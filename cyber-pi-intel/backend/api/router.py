"""
Router API endpoints for testing intelligent routing
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
import structlog

from backend.core.intelligent_router import IntelligentRouter, DataPattern, WriteStrategy
from backend.core.connections import connection_manager

logger = structlog.get_logger(__name__)
router = APIRouter()

# Initialize router (would be done in app startup)
intelligent_router: Optional[IntelligentRouter] = None

@router.on_event("startup")
async def initialize_router():
    """Initialize the intelligent router"""
    global intelligent_router
    
    config = {
        "size_threshold": 1_000_000,  # 1MB
        "batch_threshold": 100,
        "ttl_threshold": 3600
    }
    
    intelligent_router = IntelligentRouter(
        redis_client=connection_manager.redis,
        kafka_producer=connection_manager.kafka_producer,
        config=config
    )
    
    # Start background Kafka processor
    import asyncio
    asyncio.create_task(intelligent_router.process_kafka_queue())
    
    logger.info("Intelligent router initialized with Redis-first strategy")

@router.post("/write")
async def route_write(
    key: str,
    data: Dict[str, Any] = Body(...),
    metadata: Optional[Dict[str, Any]] = Body(default=None)
) -> Dict[str, Any]:
    """
    Route a write operation through intelligent router
    
    Examples:
    - Small operational data: Goes to Redis first, async to Kafka
    - Critical transaction: Dual synchronous write
    - Large analytics: Kafka first
    - Temporary cache: Redis only
    """
    if not intelligent_router:
        raise HTTPException(500, "Router not initialized")
    
    result = await intelligent_router.route_write(key, data, metadata or {})
    
    return {
        "success": len(result.get("errors", [])) == 0,
        "result": result
    }

@router.get("/read/{key}")
async def route_read(
    key: str,
    check_kafka: bool = True,
    rehydrate_cache: bool = True
) -> Dict[str, Any]:
    """
    Route a read operation - always Redis first
    
    If not in Redis and check_kafka=True, will check Kafka
    If found in Kafka and rehydrate_cache=True, will cache in Redis
    """
    if not intelligent_router:
        raise HTTPException(500, "Router not initialized")
    
    metadata = {
        "check_kafka": check_kafka,
        "rehydrate_cache": rehydrate_cache
    }
    
    data, source = await intelligent_router.route_read(key, metadata)
    
    if data is None:
        raise HTTPException(404, f"Key not found: {key}")
    
    return {
        "key": key,
        "data": data,
        "source": source
    }

@router.post("/test-patterns")
async def test_routing_patterns() -> Dict[str, Any]:
    """
    Test different routing patterns with sample data
    """
    if not intelligent_router:
        raise HTTPException(500, "Router not initialized")
    
    results = []
    
    # Test 1: Cache-only (Redis only)
    result1 = await intelligent_router.route_write(
        "test:cache:1",
        {"type": "session", "user": "test", "temp": True},
        {"ttl": 60}  # 1 minute TTL
    )
    results.append({"test": "cache_only", **result1})
    
    # Test 2: Operational (Redis first, async Kafka)
    result2 = await intelligent_router.route_write(
        "test:operational:1",
        {"type": "user_action", "action": "click", "target": "button1"},
        {}
    )
    results.append({"test": "operational", **result2})
    
    # Test 3: Immutable (Dual sync write)
    result3 = await intelligent_router.route_write(
        "test:transaction:1",
        {"transaction_id": "tx123", "amount": 100, "status": "completed"},
        {"immutable": True}
    )
    results.append({"test": "immutable", **result3})
    
    # Test 4: Analytical (Kafka first)
    large_data = {
        "type": "analytics",
        "records": [{"id": i, "value": i*10} for i in range(100)]
    }
    result4 = await intelligent_router.route_write(
        "test:analytics:1",
        large_data,
        {"type": "analytics"}
    )
    results.append({"test": "analytical", **result4})
    
    return {
        "message": "Routing pattern tests completed",
        "results": results,
        "summary": {
            "redis_first": sum(1 for r in results if r["strategy"] == "redis_first"),
            "kafka_first": sum(1 for r in results if r["strategy"] == "kafka_first"),
            "dual_sync": sum(1 for r in results if r["strategy"] == "dual_sync"),
            "redis_only": sum(1 for r in results if r["strategy"] == "redis_only")
        }
    }

@router.get("/metrics")
async def get_routing_metrics() -> Dict[str, Any]:
    """
    Get routing system metrics
    """
    if not intelligent_router:
        raise HTTPException(500, "Router not initialized")
    
    metrics = intelligent_router.get_metrics()
    
    return {
        "metrics": metrics,
        "analysis": {
            "redis_dominant": metrics.get("redis_first_percentage", 0) > 70,
            "cache_effective": metrics.get("cache_hit_rate", 0) > 0.8,
            "queue_healthy": metrics.get("kafka_queue_size", 0) < 1000
        }
    }

@router.post("/classify")
async def classify_data(
    data: Dict[str, Any] = Body(...),
    metadata: Optional[Dict[str, Any]] = Body(default=None)
) -> Dict[str, Any]:
    """
    Classify data and determine routing strategy without writing
    """
    if not intelligent_router:
        raise HTTPException(500, "Router not initialized")
    
    pattern = intelligent_router.classify_data(data, metadata or {})
    strategy = intelligent_router.determine_strategy(pattern, metadata or {})
    
    return {
        "pattern": pattern.value,
        "strategy": strategy.value,
        "explanation": _explain_strategy(pattern, strategy)
    }

def _explain_strategy(pattern: DataPattern, strategy: WriteStrategy) -> str:
    """Explain why a strategy was chosen"""
    explanations = {
        (DataPattern.CACHE_ONLY, WriteStrategy.REDIS_ONLY): 
            "Temporary data with short TTL - Redis only for speed",
        
        (DataPattern.TRANSIENT, WriteStrategy.REDIS_ONLY):
            "Transient data - Redis with longer TTL, no persistence needed",
        
        (DataPattern.OPERATIONAL, WriteStrategy.REDIS_FIRST):
            "Operational data - Redis for speed, async Kafka for durability",
        
        (DataPattern.IMMUTABLE, WriteStrategy.DUAL_SYNC):
            "Critical/immutable data - Synchronous writes to both for consistency",
        
        (DataPattern.ANALYTICAL, WriteStrategy.KAFKA_FIRST):
            "Large/analytical data - Kafka for streaming, optional Redis metadata"
    }
    
    return explanations.get(
        (pattern, strategy),
        f"Pattern {pattern.value} mapped to strategy {strategy.value}"
    )