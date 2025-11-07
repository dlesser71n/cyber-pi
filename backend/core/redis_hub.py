"""
Redis-First Architecture
Redis as the central hub - everything flows through Redis
"""

import redis.asyncio as redis
import json
from typing import Dict, Any, List
from datetime import datetime, timezone
import structlog

logger = structlog.get_logger(__name__)


class RedisHub:
    """
    Central hub - all data flows through Redis first
    Redis decides where data goes next
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        
        # Stream names for different processing stages
        self.THREAT_INTAKE_STREAM = "threats:intake"      # Raw threats come here
        self.THREAT_PARSED_STREAM = "threats:parsed"      # Parsed threats
        self.THREAT_STIX_STREAM = "threats:stix"          # STIX-converted
        self.THREAT_STORED_STREAM = "threats:stored"      # Successfully stored
        
        # Queues for processing
        self.WEAVIATE_QUEUE = "queue:weaviate"
        self.NEO4J_QUEUE = "queue:neo4j"
        self.STIX_EXPORT_QUEUE = "queue:stix_export"
    
    async def ingest_raw_threat(self, threat: Dict[str, Any]) -> str:
        """
        Step 1: Ingest raw threat into Redis
        Everything starts here!
        """
        threat_id = threat.get('threatId') or threat.get('id')
        
        # Store raw threat with 24h TTL
        await self.redis.setex(
            f"threat:raw:{threat_id}",
            86400,  # 24 hours
            json.dumps(threat)
        )
        
        # Add to intake stream
        await self.redis.xadd(
            self.THREAT_INTAKE_STREAM,
            {"threat_id": threat_id, "data": json.dumps(threat)}
        )
        
        logger.info("Threat ingested to Redis", threat_id=threat_id)
        return threat_id
    
    async def mark_parsed(self, threat_id: str, parsed_data: Dict):
        """
        Step 2: Mark threat as parsed
        Store parsed version
        """
        # Store parsed data
        await self.redis.setex(
            f"threat:parsed:{threat_id}",
            86400,
            json.dumps(parsed_data)
        )
        
        # Add to parsed stream
        await self.redis.xadd(
            self.THREAT_PARSED_STREAM,
            {"threat_id": threat_id, "severity": parsed_data.get('severity', 'unknown')}
        )
        
        # Route to appropriate queues based on parsed data
        await self._route_threat(threat_id, parsed_data)
    
    async def _route_threat(self, threat_id: str, parsed_data: Dict):
        """
        Redis decides where this threat should go
        Based on severity, type, etc.
        """
        severity = parsed_data.get('severity', 'medium')
        threat_types = parsed_data.get('threatType', [])
        
        # All threats go to Weaviate (vector storage)
        await self.redis.lpush(self.WEAVIATE_QUEUE, threat_id)
        
        # High/Critical threats go to Neo4j for graph analysis
        if severity in ['high', 'critical']:
            await self.redis.lpush(self.NEO4J_QUEUE, threat_id)
        
        # Threats with CVEs or threat actors go to Neo4j
        if parsed_data.get('cves') or parsed_data.get('threatActors'):
            await self.redis.lpush(self.NEO4J_QUEUE, threat_id)
        
        # APT/Ransomware/Zero-day go to STIX export
        if any(t in ['apt', 'ransomware', 'zero-day'] for t in threat_types):
            await self.redis.lpush(self.STIX_EXPORT_QUEUE, threat_id)
        
        logger.info("Threat routed", threat_id=threat_id, 
                   weaviate=True, 
                   neo4j=(severity in ['high', 'critical']),
                   stix_export=any(t in ['apt', 'ransomware'] for t in threat_types))
    
    async def mark_stix_converted(self, threat_id: str, stix_bundle: str):
        """
        Step 3: Store STIX conversion
        """
        await self.redis.setex(
            f"threat:stix:{threat_id}",
            86400,
            stix_bundle
        )
        
        await self.redis.xadd(
            self.THREAT_STIX_STREAM,
            {"threat_id": threat_id}
        )
    
    async def mark_stored(self, threat_id: str, locations: List[str]):
        """
        Step 4: Mark as successfully stored
        """
        await self.redis.setex(
            f"threat:stored:{threat_id}",
            86400,
            json.dumps({
                "threat_id": threat_id,
                "stored_at": datetime.now(timezone.utc).isoformat(),
                "locations": locations
            })
        )
        
        await self.redis.xadd(
            self.THREAT_STORED_STREAM,
            {"threat_id": threat_id, "locations": ",".join(locations)}
        )
    
    async def get_threat_status(self, threat_id: str) -> Dict:
        """
        Get complete status of a threat through the pipeline
        """
        raw = await self.redis.get(f"threat:raw:{threat_id}")
        parsed = await self.redis.get(f"threat:parsed:{threat_id}")
        stix = await self.redis.get(f"threat:stix:{threat_id}")
        stored = await self.redis.get(f"threat:stored:{threat_id}")
        
        return {
            "threat_id": threat_id,
            "has_raw": raw is not None,
            "has_parsed": parsed is not None,
            "has_stix": stix is not None,
            "has_stored": stored is not None,
            "stored_info": json.loads(stored) if stored else None
        }
    
    async def get_queue_stats(self) -> Dict:
        """
        Get statistics on all queues
        """
        return {
            "weaviate_queue": await self.redis.llen(self.WEAVIATE_QUEUE),
            "neo4j_queue": await self.redis.llen(self.NEO4J_QUEUE),
            "stix_export_queue": await self.redis.llen(self.STIX_EXPORT_QUEUE),
            "intake_stream_length": await self._get_stream_length(self.THREAT_INTAKE_STREAM),
            "parsed_stream_length": await self._get_stream_length(self.THREAT_PARSED_STREAM)
        }
    
    async def _get_stream_length(self, stream_name: str) -> int:
        """Get length of a Redis stream"""
        try:
            info = await self.redis.xinfo_stream(stream_name)
            return info.get('length', 0)
        except:
            return 0
    
    # Worker methods - pull from queues and process
    
    async def get_next_for_weaviate(self) -> str:
        """Worker: Get next threat to store in Weaviate"""
        result = await self.redis.brpop(self.WEAVIATE_QUEUE, timeout=1)
        return result[1].decode() if result else None
    
    async def get_next_for_neo4j(self) -> str:
        """Worker: Get next threat to store in Neo4j"""
        result = await self.redis.brpop(self.NEO4J_QUEUE, timeout=1)
        return result[1].decode() if result else None
    
    async def get_next_for_stix_export(self) -> str:
        """Worker: Get next threat to export as STIX"""
        result = await self.redis.brpop(self.STIX_EXPORT_QUEUE, timeout=1)
        return result[1].decode() if result else None
    
    async def get_parsed_threat(self, threat_id: str) -> Dict:
        """Get parsed threat data"""
        data = await self.redis.get(f"threat:parsed:{threat_id}")
        return json.loads(data) if data else None


# Simplified ingestion using Redis Hub
async def ingest_via_redis_hub(hub: RedisHub, threats: List[Dict]):
    """
    Simple ingestion - just push everything to Redis
    Workers handle the rest
    """
    ingested = []
    
    for threat in threats:
        threat_id = await hub.ingest_raw_threat(threat)
        ingested.append(threat_id)
    
    return ingested
