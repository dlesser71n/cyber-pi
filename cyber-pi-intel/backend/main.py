"""
TQAKB V4 - Main FastAPI Application
Event-driven knowledge management system with AI capabilities
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge
import structlog
import time
import uuid
from typing import Dict, Any
import os

from backend.core.config import settings
from backend.core.schemas import HealthStatus

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.CallsiteParameterAdder(
            parameters=[structlog.processors.CallsiteParameter.FILENAME,
                        structlog.processors.CallsiteParameter.LINENO,
                        structlog.processors.CallsiteParameter.FUNC_NAME]
        ),
        structlog.processors.dict_tracebacks,
        structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics - handle reload gracefully
from prometheus_client import CollectorRegistry, REGISTRY

# Use a custom registry to avoid conflicts during reload
if settings.api_reload:
    # Clear existing collectors during reload
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass

request_count = Counter('tqakb_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('tqakb_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
active_connections = Gauge('tqakb_active_connections', 'Active connections')
kafka_events_produced = Counter('tqakb_kafka_events_produced', 'Kafka events produced', ['topic'])
kafka_events_consumed = Counter('tqakb_kafka_events_consumed', 'Kafka events consumed', ['topic'])
db_operations = Counter('tqakb_db_operations', 'Database operations', ['db', 'operation'])

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""

    # Startup
    logger.info("Starting TQAKB V4 (Simplified)",
                environment=settings.environment,
                debug=settings.debug)

    # Validate security settings (will raise ValueError if issues found)
    try:
        settings.validate_security_settings()
        logger.info("Security settings validated")
    except ValueError as e:
        logger.critical(f"Security validation failed: {e}")
        raise

    # Initialize database connections
    from backend.core.connections import connection_manager
    await connection_manager.initialize()

    logger.info("TQAKB V4 started successfully (simplified: no Kafka)")

    yield

    # Shutdown
    logger.info("Shutting down TQAKB V4")
    
    # Close database connections
    await connection_manager.close()
    
    logger.info("TQAKB V4 shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="TQAKB V4 - The Question Answer Knowledge Base",
    description="Next Generation Event-Driven Knowledge Management System",
    version="4.0.0-alpha",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Middleware for correlation ID
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to all requests"""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    
    # Add to logging context
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
    
    # Process request
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Add headers
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log request
    logger.info("Request processed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time=process_time)
    
    # Update metrics
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(process_time)
    
    # Clear context
    structlog.contextvars.unbind_contextvars("correlation_id")
    
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount Prometheus metrics
if settings.prometheus_enabled:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Import and include routers
from backend.api.health import router as health_router
from backend.api.knowledge import router as knowledge_router
from backend.api.search import router as search_router
from backend.api.admin import router as admin_router

app.include_router(health_router, prefix="/api/health", tags=["Health"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["Knowledge"])
app.include_router(search_router, prefix="/api/search", tags=["Search"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])

# Root endpoint
@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with service information"""
    return {
        "name": "TQAKB V4",
        "version": "4.0.0-alpha",
        "description": "Next Generation Event-Driven Knowledge Management System",
        "status": "running",
        "environment": settings.environment,
        "endpoints": {
            "health": "/api/health",
            "docs": "/api/docs",
            "redoc": "/api/redoc",
            "metrics": "/metrics" if settings.prometheus_enabled else None,
            "knowledge": "/api/knowledge",
            "search": "/api/search",
            "admin": "/api/admin"
        }
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    logger.error("Unhandled exception",
                 correlation_id=correlation_id,
                 method=request.method,
                 path=request.url.path,
                 exception=str(exc),
                 exc_info=exc)
    
    # Don't expose internal errors in production
    if settings.is_production():
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "correlation_id": correlation_id
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": str(exc),
                "type": exc.__class__.__name__,
                "correlation_id": correlation_id
            }
        )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload and settings.is_development(),
        workers=1 if settings.api_reload else settings.api_workers,
        log_level=settings.log_level.lower()
    )