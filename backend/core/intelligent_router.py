"""
Intelligent Routing System - Redis-First Architecture
Prioritizes Redis for speed with async Kafka propagation for immutability
"""

from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import asyncio
import hashlib
import json
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

class DataPattern(Enum):
    """Data access patterns"""
    TRANSIENT = "transient"          # Temporary data (Redis only)
    OPERATIONAL = "operational"       # Working data (Redis first, Kafka async)
    IMMUTABLE = "immutable"          # Permanent record (Dual write)
    ANALYTICAL = "analytical"        # Batch/streaming (Kafka first)
    CACHE_ONLY = "cache_only"        # Pure cache (Redis only, no persistence)

class WriteStrategy(Enum):
    """Write strategies for data persistence"""
    REDIS_ONLY = "redis_only"
    REDIS_FIRST = "redis_first"      # Default strategy
    DUAL_SYNC = "dual_sync"          # Critical paths
    KAFKA_FIRST = "kafka_first"      # Analytics/audit
    KAFKA_ONLY = "kafka_only"        # Pure streaming

class IntelligentRouter:
    """
    Redis-First Intelligent Routing System
    
    Philosophy:
    - Redis handles all real-time operations for speed
    - Kafka ensures immutability and durability
    - Async propagation minimizes latency
    - Critical paths use dual-sync for consistency
    """
    
    def __init__(self, redis_client, kafka_producer, config: Dict[str, Any]):
        self.redis = redis_client
        self.kafka = kafka_producer
        self.config = config
        
        # Performance thresholds
        self.size_threshold = config.get("size_threshold", 1_000_000)  # 1MB
        self.batch_threshold = config.get("batch_threshold", 100)
        self.ttl_threshold = config.get("ttl_threshold", 3600)  # 1 hour
        
        # Async queue for Kafka propagation
        self.kafka_queue = asyncio.Queue(maxsize=10000)
        self.kafka_batch = []
        
        # Metrics
        self.metrics = {
            "redis_writes": 0,
            "kafka_writes": 0,
            "dual_writes": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "kafka_queue_size": 0
        }

    def classify_data(self, 
                     data: Dict[str, Any], 
                     metadata: Optional[Dict] = None) -> DataPattern:
        """
        Classify data to determine routing strategy
        
        Redis-first bias: Most data goes to Redis first
        """
        metadata = metadata or {}
        
        # Explicit classification
        if pattern := metadata.get("pattern"):
            return DataPattern(pattern)
        
        # Size-based classification
        data_size = len(json.dumps(data))
        
        # Cache-only patterns (never persist)
        if any([
            metadata.get("ttl", float('inf')) < 300,  # < 5 min TTL
            metadata.get("type") == "session",
            metadata.get("type") == "temp",
            data.get("_temp", False)
        ]):
            return DataPattern.CACHE_ONLY
        
        # Transient patterns (Redis with longer TTL, no Kafka)
        if any([
            metadata.get("ttl", float('inf')) < self.ttl_threshold,
            metadata.get("type") == "status",
            metadata.get("type") == "metric",
            data_size < 1000  # Small ephemeral data
        ]):
            return DataPattern.TRANSIENT
        
        # Immutable patterns (critical data needing guarantees)
        if any([
            metadata.get("immutable", False),
            metadata.get("audit", False),
            metadata.get("type") == "transaction",
            metadata.get("type") == "event",
            "transaction_id" in data,
            "audit_trail" in data
        ]):
            return DataPattern.IMMUTABLE
        
        # Analytical patterns (large batch/streaming)
        if any([
            data_size > self.size_threshold,
            metadata.get("batch_size", 0) > self.batch_threshold,
            metadata.get("type") == "analytics",
            metadata.get("type") == "log",
            isinstance(data.get("records"), list) and len(data.get("records", [])) > 50
        ]):
            return DataPattern.ANALYTICAL
        
        # Default: Operational (Redis-first with async Kafka)
        return DataPattern.OPERATIONAL

    def determine_strategy(self, 
                          pattern: DataPattern,
                          metadata: Optional[Dict] = None) -> WriteStrategy:
        """
        Determine write strategy based on data pattern
        
        Redis-first approach: Optimize for speed, ensure durability
        """
        metadata = metadata or {}
        
        # Override strategy if specified
        if strategy := metadata.get("strategy"):
            return WriteStrategy(strategy)
        
        # Pattern-based strategy (Redis-first bias)
        strategy_map = {
            DataPattern.CACHE_ONLY: WriteStrategy.REDIS_ONLY,
            DataPattern.TRANSIENT: WriteStrategy.REDIS_ONLY,
            DataPattern.OPERATIONAL: WriteStrategy.REDIS_FIRST,  # Default
            DataPattern.IMMUTABLE: WriteStrategy.DUAL_SYNC,      # Critical
            DataPattern.ANALYTICAL: WriteStrategy.KAFKA_FIRST    # Large/batch
        }
        
        return strategy_map.get(pattern, WriteStrategy.REDIS_FIRST)

    async def route_write(self, 
                         key: str,
                         data: Dict[str, Any],
                         metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Route write operation using Redis-first strategy
        """
        metadata = metadata or {}
        start_time = asyncio.get_event_loop().time()
        
        # Classify and determine strategy
        pattern = self.classify_data(data, metadata)
        strategy = self.determine_strategy(pattern, metadata)
        
        logger.debug("Routing write",
                    key=key,
                    pattern=pattern.value,
                    strategy=strategy.value,
                    size=len(json.dumps(data)))
        
        result = {
            "key": key,
            "pattern": pattern.value,
            "strategy": strategy.value,
            "redis": False,
            "kafka": False,
            "queued": False,
            "errors": []
        }
        
        try:
            if strategy == WriteStrategy.REDIS_ONLY:
                # Pure Redis (cache/transient)
                await self._write_redis(key, data, metadata)
                result["redis"] = True
                self.metrics["redis_writes"] += 1
                
            elif strategy == WriteStrategy.REDIS_FIRST:
                # Redis first, queue for Kafka (default operational)
                await self._write_redis(key, data, metadata)
                result["redis"] = True
                
                # Queue for async Kafka write
                await self._queue_kafka(key, data, metadata)
                result["queued"] = True
                
                self.metrics["redis_writes"] += 1
                
            elif strategy == WriteStrategy.DUAL_SYNC:
                # Synchronous dual write (critical paths)
                redis_task = asyncio.create_task(
                    self._write_redis(key, data, metadata)
                )
                kafka_task = asyncio.create_task(
                    self._write_kafka(key, data, metadata)
                )
                
                # Wait for both
                redis_result, kafka_result = await asyncio.gather(
                    redis_task, kafka_task,
                    return_exceptions=True
                )
                
                if not isinstance(redis_result, Exception):
                    result["redis"] = True
                    self.metrics["redis_writes"] += 1
                else:
                    result["errors"].append(f"Redis: {redis_result}")
                
                if not isinstance(kafka_result, Exception):
                    result["kafka"] = True
                    self.metrics["kafka_writes"] += 1
                else:
                    result["errors"].append(f"Kafka: {kafka_result}")
                
                self.metrics["dual_writes"] += 1
                
            elif strategy == WriteStrategy.KAFKA_FIRST:
                # Kafka first (analytics/large data)
                await self._write_kafka(key, data, metadata)
                result["kafka"] = True
                self.metrics["kafka_writes"] += 1
                
                # Optionally cache metadata in Redis
                if metadata.get("cache_metadata", True):
                    cache_data = {
                        "key": key,
                        "size": len(json.dumps(data)),
                        "timestamp": datetime.utcnow().isoformat(),
                        "location": "kafka"
                    }
                    await self._write_redis(f"{key}:meta", cache_data, {"ttl": 3600})
                    
            elif strategy == WriteStrategy.KAFKA_ONLY:
                # Pure Kafka (streaming only)
                await self._write_kafka(key, data, metadata)
                result["kafka"] = True
                self.metrics["kafka_writes"] += 1
                
        except Exception as e:
            logger.error("Route write failed",
                        key=key,
                        strategy=strategy.value,
                        error=str(e))
            result["errors"].append(str(e))
        
        # Record latency
        result["latency_ms"] = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return result

    async def route_read(self,
                        key: str,
                        metadata: Optional[Dict] = None) -> Tuple[Optional[Any], str]:
        """
        Route read operation - always Redis first for speed
        """
        metadata = metadata or {}
        
        # Always try Redis first (speed priority)
        try:
            data = await self._read_redis(key)
            if data is not None:
                self.metrics["cache_hits"] += 1
                return data, "redis"
        except Exception as e:
            logger.debug(f"Redis read failed: {e}")
        
        self.metrics["cache_misses"] += 1
        
        # Check if we should look in Kafka
        if metadata.get("check_kafka", True):
            try:
                # Check Redis for metadata about Kafka location
                meta_key = f"{key}:meta"
                meta = await self._read_redis(meta_key)
                
                if meta and meta.get("location") == "kafka":
                    # Fetch from Kafka
                    data = await self._read_kafka(key, metadata)
                    
                    if data is not None:
                        # Re-hydrate Redis cache for next time
                        if metadata.get("rehydrate_cache", True):
                            await self._write_redis(key, data, {"ttl": 3600})
                        
                        return data, "kafka"
                        
            except Exception as e:
                logger.error(f"Kafka read failed: {e}")
        
        return None, "not_found"

    async def _write_redis(self, key: str, data: Any, metadata: Dict):
        """Write to Redis with optional TTL"""
        ttl = metadata.get("ttl")
        
        if isinstance(data, dict):
            data = json.dumps(data)
        
        if ttl:
            await self.redis.setex(key, ttl, data)
        else:
            await self.redis.set(key, data)

    async def _write_kafka(self, key: str, data: Any, metadata: Dict):
        """Write to Kafka topic"""
        topic = metadata.get("topic", "tqakb.events")
        
        message = {
            "key": key,
            "data": data,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.kafka.send(
            topic,
            key=key.encode() if isinstance(key, str) else key,
            value=json.dumps(message)  # Don't encode here, let serializer handle it
        )

    async def _queue_kafka(self, key: str, data: Any, metadata: Dict):
        """Queue for async Kafka write"""
        item = (key, data, metadata, datetime.utcnow())
        
        # Non-blocking put
        try:
            self.kafka_queue.put_nowait(item)
            self.metrics["kafka_queue_size"] = self.kafka_queue.qsize()
        except asyncio.QueueFull:
            # Fallback to sync write if queue full
            logger.warning("Kafka queue full, falling back to sync write")
            await self._write_kafka(key, data, metadata)

    async def _read_redis(self, key: str) -> Optional[Any]:
        """Read from Redis"""
        data = await self.redis.get(key)
        
        if data:
            try:
                return json.loads(data)
            except:
                return data
        
        return None

    async def _read_kafka(self, key: str, metadata: Dict) -> Optional[Any]:
        """Read from Kafka (last value for key)"""
        # This would typically use Kafka Streams or ksqlDB
        # For now, return None (implement based on your Kafka setup)
        logger.warning(f"Kafka read not implemented for key: {key}")
        return None

    async def process_kafka_queue(self):
        """
        Background task to process Kafka queue
        Batches writes for efficiency
        """
        while True:
            try:
                # Collect batch
                batch = []
                deadline = asyncio.get_event_loop().time() + 0.1  # 100ms window
                
                while len(batch) < self.batch_threshold:
                    timeout = max(0, deadline - asyncio.get_event_loop().time())
                    
                    try:
                        item = await asyncio.wait_for(
                            self.kafka_queue.get(),
                            timeout=timeout
                        )
                        batch.append(item)
                    except asyncio.TimeoutError:
                        break
                
                # Process batch
                if batch:
                    for key, data, metadata, timestamp in batch:
                        try:
                            await self._write_kafka(key, data, metadata)
                            self.metrics["kafka_writes"] += 1
                        except Exception as e:
                            logger.error(f"Kafka batch write failed: {e}")
                    
                    logger.debug(f"Processed Kafka batch: {len(batch)} items")
                    self.metrics["kafka_queue_size"] = self.kafka_queue.qsize()
                
                # Brief pause if queue empty
                if not batch:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Kafka queue processor error: {e}")
                await asyncio.sleep(1)

    def get_metrics(self) -> Dict[str, Any]:
        """Get routing metrics"""
        total_writes = (
            self.metrics["redis_writes"] + 
            self.metrics["kafka_writes"] + 
            self.metrics["dual_writes"]
        )
        
        return {
            **self.metrics,
            "total_writes": total_writes,
            "cache_hit_rate": (
                self.metrics["cache_hits"] / 
                max(1, self.metrics["cache_hits"] + self.metrics["cache_misses"])
            ),
            "redis_first_percentage": (
                self.metrics["redis_writes"] / max(1, total_writes)
            ) * 100
        }