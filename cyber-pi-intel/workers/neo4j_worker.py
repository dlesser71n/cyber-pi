#!/usr/bin/env python3
"""
Neo4j Worker
Processes threats from Redis queue → Builds graph in Neo4j
Can run multiple instances in parallel
"""

import asyncio
import sys
from pathlib import Path
import redis.asyncio as redis
from neo4j import GraphDatabase
from datetime import datetime, timezone
import structlog

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.core.redis_hub import RedisHub

logger = structlog.get_logger(__name__)


class Neo4jWorker:
    """Worker that drains Neo4j queue and builds graph"""
    
    def __init__(self, worker_id: int = 1):
        self.worker_id = worker_id
        self.redis_client = None
        self.neo4j_driver = None
        self.hub = None
        
        self.stats = {
            "processed": 0,
            "failed": 0,
            "start_time": datetime.now(timezone.utc)
        }
    
    async def connect(self):
        """Connect to Redis and Neo4j"""
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
        
        # Neo4j (using localhost with port forward)
        self.neo4j_driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "cyber-pi-neo4j-2025")
        )
        self.neo4j_driver.verify_connectivity()
        logger.info("Connected to Neo4j", worker_id=self.worker_id)
    
    async def process_one(self) -> bool:
        """Process one threat from queue"""
        try:
            # Get next threat from queue
            threat_id = await self.hub.get_next_for_neo4j()
            
            if not threat_id:
                return False  # Queue empty
            
            # Get parsed threat data
            threat = await self.hub.get_parsed_threat(threat_id)
            
            if not threat:
                logger.warning("Threat data not found", threat_id=threat_id)
                return False
            
            # Build graph in Neo4j
            with self.neo4j_driver.session() as session:
                # Create threat node
                session.run("""
                    MERGE (t:CyberThreat {threatId: $threatId})
                    SET t.title = $title,
                        t.severity = $severity,
                        t.publishedDate = $publishedDate,
                        t.source = $source,
                        t.ingestedDate = $ingestedDate
                """, 
                    threatId=threat['threatId'],
                    title=threat.get('title', ''),
                    severity=threat.get('severity', 'medium'),
                    publishedDate=threat.get('publishedDate', ''),
                    source=threat.get('source', ''),
                    ingestedDate=threat.get('ingestedDate', '')
                )
                
                # Create relationships to threat actors
                for actor in threat.get('threatActors', []):
                    session.run("""
                        MATCH (t:CyberThreat {threatId: $threatId})
                        MERGE (a:ThreatActor {actorName: $actor})
                        MERGE (t)-[:ATTRIBUTED_TO]->(a)
                    """, threatId=threat['threatId'], actor=actor)
                
                # Create relationships to CVEs
                for cve in threat.get('cves', []):
                    session.run("""
                        MATCH (t:CyberThreat {threatId: $threatId})
                        MERGE (c:CVE {cveId: $cve})
                        MERGE (t)-[:EXPLOITS]->(c)
                    """, threatId=threat['threatId'], cve=cve)
            
            # Mark as stored
            await self.hub.mark_stored(threat_id, ["neo4j"])
            
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
        if self.neo4j_driver:
            self.neo4j_driver.close()
        if self.redis_client:
            await self.redis_client.close()


async def main():
    """Run Neo4j worker"""
    import sys
    
    worker_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    worker = Neo4jWorker(worker_id=worker_id)
    
    try:
        await worker.run()
    finally:
        await worker.close()


if __name__ == "__main__":
    asyncio.run(main())
