#!/usr/bin/env python3
"""
STIX Worker  
Processes threats from Redis queue → Exports STIX bundles
Can run multiple instances in parallel
"""

import asyncio
import sys
from pathlib import Path
import redis.asyncio as redis
from datetime import datetime, timezone
import json
import structlog

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.core.redis_hub import RedisHub
from backend.core.stix_converter import STIXConverter

logger = structlog.get_logger(__name__)


class STIXWorker:
    """Worker that drains STIX export queue and creates STIX bundles"""
    
    def __init__(self, worker_id: int = 1, output_dir: str = "/tmp/stix_export"):
        self.worker_id = worker_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        self.redis_client = None
        self.hub = None
        self.stix_converter = STIXConverter()
        
        self.stats = {
            "processed": 0,
            "failed": 0,
            "start_time": datetime.now(timezone.utc)
        }
    
    async def connect(self):
        """Connect to Redis"""
        logger.info("Connecting to Redis", worker_id=self.worker_id)
        
        self.redis_client = await redis.from_url(
            "redis://localhost:6380",
            password="cyber-pi-redis-2025",
            encoding="utf-8",
            decode_responses=True
        )
        await self.redis_client.ping()
        self.hub = RedisHub(self.redis_client)
        logger.info("Connected to Redis", worker_id=self.worker_id)
    
    async def process_one(self) -> bool:
        """Process one threat from queue"""
        try:
            # Get next threat from queue
            threat_id = await self.hub.get_next_for_stix_export()
            
            if not threat_id:
                return False  # Queue empty
            
            # Get parsed threat data
            threat = await self.hub.get_parsed_threat(threat_id)
            
            if not threat:
                logger.warning("Threat data not found", threat_id=threat_id)
                return False
            
            # Convert to STIX bundle
            try:
                stix_bundle = self.stix_converter.threat_to_stix_bundle(threat)
                
                # Save to file
                filename = self.output_dir / f"{threat_id}.json"
                with open(filename, 'w') as f:
                    f.write(stix_bundle.serialize(pretty=True))
                
                # Store in Redis
                await self.hub.mark_stix_converted(threat_id, stix_bundle.serialize())
                
                logger.debug("STIX bundle created",
                            threat_id=threat_id,
                            objects=len(stix_bundle.objects),
                            file=str(filename))
                
            except Exception as e:
                logger.warning("STIX conversion failed",
                              threat_id=threat_id,
                              error=str(e))
                # Still mark as processed even if STIX fails
            
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
        logger.info("Worker starting", 
                   worker_id=self.worker_id,
                   output_dir=str(self.output_dir))
        
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
        if self.redis_client:
            await self.redis_client.close()


async def main():
    """Run STIX worker"""
    import sys
    
    worker_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/stix_export"
    
    worker = STIXWorker(worker_id=worker_id, output_dir=output_dir)
    
    try:
        await worker.run()
    finally:
        await worker.close()


if __name__ == "__main__":
    asyncio.run(main())
