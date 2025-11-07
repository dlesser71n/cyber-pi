"""
Health check endpoints for TQAKB V4
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import structlog

from backend.core.schemas import HealthStatus
from backend.core.connections import connection_manager
from backend.core.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """Basic health check endpoint"""
    return HealthStatus(
        service="TQAKB V4",
        status="healthy",
        timestamp=datetime.utcnow(),
        details={
            "version": "4.0.0-alpha",
            "environment": settings.environment
        }
    )

@router.get("/live")
async def liveness_probe() -> Dict[str, str]:
    """Kubernetes liveness probe"""
    return {"status": "alive"}

@router.get("/ready")
async def readiness_probe() -> Dict[str, Any]:
    """Kubernetes readiness probe - checks all dependencies"""
    try:
        health = await connection_manager.health_check()
        
        # Service is ready if at least Redis and one other service is up
        redis_ok = health.get("redis", False)
        any_other_ok = any([
            health.get("neo4j", False),
            health.get("weaviate", False)
        ])
        
        if redis_ok and any_other_ok:
            return {
                "status": "ready",
                "services": health
            }
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "not_ready",
                    "services": health
                }
            )
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "message": str(e)}
        )

@router.get("/services")
async def service_health() -> Dict[str, Any]:
    """Detailed health check of all services"""
    try:
        health = await connection_manager.health_check()
        
        services = []
        for service_name, is_healthy in health.items():
            services.append({
                "name": service_name,
                "status": "healthy" if is_healthy else "unhealthy",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        overall = "healthy" if all(health.values()) else "degraded"
        
        return {
            "overall_status": overall,
            "services": services,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Service health check failed", error=str(e))
        return {
            "overall_status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }