"""
TQAKB V4 - Simple FastAPI Application (for testing)
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import uuid
from typing import Dict, Any
import os

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting TQAKB V4 Simple")
    yield
    logger.info("Shutting down TQAKB V4 Simple")

# Create FastAPI app
app = FastAPI(
    title="TQAKB V4 - Simple",
    description="Simplified version for testing",
    version="4.0.0-test",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "name": "TQAKB V4",
        "version": "4.0.0-test",
        "status": "running",
        "message": "Simple version without Prometheus"
    }

@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check"""
    return {"status": "healthy"}

@app.get("/api/test-v3-services")
async def test_v3_services() -> Dict[str, Any]:
    """Test connections to V3 services"""
    import httpx
    import redis.asyncio as redis
    
    results = {}
    
    # Test Redis (V3's NodePort)
    try:
        r = redis.Redis(host='localhost', port=30379, db=1, decode_responses=True)
        await r.ping()
        results["redis"] = "✅ Connected via NodePort 30379"
        await r.close()
    except Exception as e:
        results["redis"] = f"❌ Failed: {str(e)}"
    
    # Test Neo4j HTTP (V3's NodePort)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:30474", timeout=2.0)
            results["neo4j_http"] = f"✅ Reachable via NodePort 30474 (status: {response.status_code})"
    except Exception as e:
        results["neo4j_http"] = f"❌ Failed: {str(e)}"
    
    # Test Weaviate (V3's NodePort)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:30082/v1/.well-known/ready", timeout=2.0)
            results["weaviate"] = f"✅ Reachable via NodePort 30082 (status: {response.status_code})"
    except Exception as e:
        results["weaviate"] = f"❌ Failed: {str(e)}"
    
    # Test Ollama (local, not K8s)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=2.0)
            results["ollama"] = f"✅ Local Ollama reachable (status: {response.status_code})"
    except Exception as e:
        results["ollama"] = f"❌ Failed: {str(e)}"
    
    # Test Kafka (V3's NodePort)
    results["kafka"] = "📝 Kafka test requires aiokafka (port 30092 available)"
    
    return {
        "message": "Testing connections to V3 services via NodePorts",
        "results": results
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", "8001"))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )