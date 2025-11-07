#!/usr/bin/env python3
"""
Weaviate Worker
Processes threats from Redis queue → Stores in Weaviate
Can run multiple instances in parallel
"""

import asyncio
import sys
from pathlib import Path
import redis.asyncio as redis
import weaviate
import weaviate.classes.config as wvcc
from datetime import datetime, timezone
import json
import structlog

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.core.redis_hub import RedisHub

logger = structlog.get_logger(__name__)


class WeaviateWorker:
    """Worker that drains Weaviate queue and stores threats"""
    
    def __init__(self, worker_id: int = 1):
        self.worker_id = worker_id
        self.redis_client = None
        self.weaviate_client = None
        self.hub = None
        
        self.stats = {
            "processed": 0,
            "failed": 0,
            "start_time": datetime.now(timezone.utc)
        }
    
    async def connect(self):
        """Connect to Redis and Weaviate"""
        logger.info("Connecting to databases", worker_id=self.worker_id)
        
        # Redis
        self.redis_client = await redis.from_url(
            "redis://localhost:6380",
            password="cyber-pi-redis-2025",
            encoding="utf-8",
            decode_responses=True
        )
        await self.redis_client.ping()
        self.hub = RedisHub(self.redis_client)
        logger.info("Connected to Redis", worker_id=self.worker_id)
        
        # Weaviate (using localhost with port forward)
        self.weaviate_client = weaviate.connect_to_custom(
            http_host="localhost",
            http_port=8080,
            http_secure=False,
            grpc_host="localhost",
            grpc_port=50051,
            grpc_secure=False
        )
        logger.info("Connected to Weaviate", worker_id=self.worker_id)
    
    async def process_one(self) -> bool:
        """Process one threat from queue"""
        try:
            # Get next threat from queue (blocks for 1 second)
            threat_id = await self.hub.get_next_for_weaviate()
            
            if not threat_id:
                return False  # Queue empty
            
            # Get parsed threat data
            threat = await self.hub.get_parsed_threat(threat_id)
            
            if not threat:
                logger.warning("Threat data not found", threat_id=threat_id)
                return False
            
            # Store in Weaviate
            collection = self.weaviate_client.collections.get("CyberThreatIntelligence")
            
            data_obj = {
                "threatId": threat.get('threatId'),
                "title": threat.get('title', ''),
                "content": threat.get('content', ''),
                "summary": threat.get('content', '')[:500],
                "source": threat.get('source', ''),
                "sourceUrl": threat.get('sourceUrl', ''),
                "industry": threat.get('industry', []) if isinstance(threat.get('industry'), list) else [threat.get('industry', 'General')],
                "severity": threat.get('severity', 'medium'),
                "threatType": threat.get('threatType', []),
                "threatActors": threat.get('threatActors', []),
                "cves": threat.get('cves', []),
                "iocs": [],
                "mitreTactics": [],
                "mitreTechniques": [],
                "publishedDate": threat.get('publishedDate', datetime.now(timezone.utc).isoformat()),
                "ingestedDate": threat.get('ingestedDate', datetime.now(timezone.utc).isoformat()),
                "lastUpdated": datetime.now(timezone.utc).isoformat(),
                "confidence": 0.7,
                "verificationStatus": "unverified",
                "tags": threat.get('tags', []),
                "affectedProducts": [],
                "affectedVendors": [],
                "recommendedActions": [],
                "relatedThreats": [],
                "metadata": json.dumps({}),
                # STIX fields (empty for now)
                "stixId": "",
                "stixType": "",
                "stixVersion": "",
                "stixObject": ""
            }
            
            collection.data.insert(data_obj)
            
            # Mark as stored
            await self.hub.mark_stored(threat_id, ["weaviate"])
            
            self.stats["processed"] += 1
            
            if self.stats["processed"] % 10 == 0:
                logger.info("Progress", 
                           worker_id=self.worker_id,
                           processed=self.stats["processed"],
                           failed=self.stats["failed"])
            
            return True
            
        except Exception as e:
            logger.error("Processing failed", 
                        worker_id=self.worker_id,
                        error=str(e),
                        threat_id=threat_id if 'threat_id' in locals() else 'unknown')
            self.stats["failed"] += 1
            return False
    
    async def run(self):
        """Main worker loop"""
        logger.info("Worker starting", worker_id=self.worker_id)
        
        await self.connect()
        
        logger.info("Processing queue...", worker_id=self.worker_id)
        
        consecutive_empty = 0
        
        while True:
            processed = await self.process_one()
            
            if processed:
                consecutive_empty = 0
            else:
                consecutive_empty += 1
                
                # If queue empty for 5 checks, we're done
                if consecutive_empty >= 5:
                    logger.info("Queue empty, shutting down", worker_id=self.worker_id)
                    break
                
                await asyncio.sleep(0.5)
        
        # Final stats
        elapsed = (datetime.now(timezone.utc) - self.stats["start_time"]).total_seconds()
        logger.info("Worker complete",
                   worker_id=self.worker_id,
                   processed=self.stats["processed"],
                   failed=self.stats["failed"],
                   elapsed_seconds=elapsed,
                   rate=self.stats["processed"]/elapsed if elapsed > 0 else 0)
    
    async def close(self):
        """Cleanup"""
        if self.weaviate_client:
            self.weaviate_client.close()
        if self.redis_client:
            await self.redis_client.close()


async def main():
    """Run Weaviate worker"""
    import sys
    
    worker_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    worker = WeaviateWorker(worker_id=worker_id)
    
    try:
        await worker.run()
    finally:
        await worker.close()


if __name__ == "__main__":
    asyncio.run(main())
