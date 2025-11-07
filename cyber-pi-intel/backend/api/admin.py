"""
Admin endpoints for TQAKB V4
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import structlog
from datetime import datetime

from backend.core.connections import connection_manager
from backend.core.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/config")
async def get_configuration() -> Dict[str, Any]:
    """Get current system configuration (non-sensitive)"""
    return {
        "environment": settings.environment,
        "debug": settings.debug,
        "kafka": {
            "bootstrap_servers": settings.kafka_bootstrap_servers,
            "group_id": settings.kafka_group_id
        },
        "redis": {
            "host": settings.redis_host,
            "port": settings.redis_port,
            "db": settings.redis_db
        },
        "neo4j": {
            "uri": settings.neo4j_uri,
            "database": settings.neo4j_database
        },
        "weaviate": {
            "url": settings.weaviate_url
        },
        "ollama": {
            "host": settings.ollama_host,
            "model": settings.ollama_model,
            "embedding_model": settings.ollama_embedding_model
        }
    }

@router.post("/clear-cache")
async def clear_cache() -> Dict[str, str]:
    """Clear Redis cache (development only)"""
    if settings.is_production():
        raise HTTPException(status_code=403, detail="Not allowed in production")
    
    try:
        redis = connection_manager.get_redis()
        if not redis:
            raise HTTPException(status_code=503, detail="Redis not available")
        
        await redis.flushdb()
        return {"status": "success", "message": "Cache cleared"}
    except Exception as e:
        logger.error("Failed to clear cache", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get system metrics"""
    try:
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "connections": await connection_manager.health_check()
        }
        
        # Add Redis metrics if available
        redis = connection_manager.get_redis()
        if redis:
            info = await redis.info()
            metrics["redis"] = {
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0)
            }
        
        return metrics
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reload")
async def reload_configuration() -> Dict[str, str]:
    """Reload configuration (development only)"""
    if settings.is_production():
        raise HTTPException(status_code=403, detail="Not allowed in production")
    
    return {"status": "success", "message": "Configuration reloaded"}

@router.get("/logs")
async def get_recent_logs(lines: int = 100) -> Dict[str, Any]:
    """Get recent application logs (development only)"""
    if settings.is_production():
        raise HTTPException(status_code=403, detail="Not allowed in production")
    
    return {
        "message": "Log retrieval not yet implemented",
        "requested_lines": lines
    }