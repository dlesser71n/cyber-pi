#!/usr/bin/env python3
"""
Cyber-PI-Intel Backend API
Complete threat intelligence platform with multi-source collection
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import redis
import weaviate
from neo4j import GraphDatabase
import logging
import os

# Import validators and security
from backend.core.validators import (
    InputValidator,
    ValidatedThreatQuery,
    ValidatedCollectionRequest,
    ValidatedActorName,
    validate_limit_param,
    validate_offset_param,
    validate_severity_param,
    validate_industry_param
)
from backend.core.security import SecurityHeaders

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Cyber-PI-Intel API",
    description="Multi-Source Threat Intelligence Platform",
    version="1.0.0"
)

# Load CORS origins from environment
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

# CORS - Restricted to specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses"""
    return await SecurityHeaders.add_security_headers(request, call_next)

# Database connection globals (initialized on startup)
redis_client: Optional[redis.Redis] = None
weaviate_client: Optional[weaviate.WeaviateClient] = None
neo4j_driver: Optional[GraphDatabase.driver] = None


# ============================================================================
# MODELS (Use validated models from validators.py)
# ============================================================================
# Removed - now using ValidatedThreatQuery and ValidatedCollectionRequest from validators.py


# ============================================================================
# HEALTH & STATUS
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Cyber-PI-Intel API",
        "version": "1.0.0",
        "status": "operational",
        "sources": ["technical", "social", "ot_ics", "dark_web", "geopolitical"],
        "databases": ["redis", "weaviate", "neo4j"],
        "endpoints": {
            "collection": "/collect",
            "search": "/search",
            "threats": "/threats",
            "analytics": "/analytics",
            "actors": "/actors",
            "cves": "/cves",
            "campaigns": "/campaigns"
        }
    }


@app.get("/health")
async def health_check():
    """Health check for all services"""
    status = {
        "api": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {}
    }

    # Check Redis
    try:
        if redis_client:
            redis_client.ping()
            status["services"]["redis"] = "healthy"
        else:
            status["services"]["redis"] = "not initialized"
    except Exception as e:
        status["services"]["redis"] = f"unhealthy: {str(e)}"

    # Check Weaviate
    try:
        if weaviate_client:
            weaviate_client.is_ready()
            status["services"]["weaviate"] = "healthy"
        else:
            status["services"]["weaviate"] = "not initialized"
    except Exception as e:
        status["services"]["weaviate"] = f"unhealthy: {str(e)}"

    # Check Neo4j
    try:
        if neo4j_driver:
            with neo4j_driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            status["services"]["neo4j"] = "healthy"
        else:
            status["services"]["neo4j"] = "not initialized"
    except Exception as e:
        status["services"]["neo4j"] = f"unhealthy: {str(e)}"

    return status


# ============================================================================
# COLLECTION ENDPOINTS
# ============================================================================

@app.post("/collect")
async def collect_threats(request: ValidatedCollectionRequest):
    """
    Trigger threat collection from multiple sources
    NOTE: Collection is typically run via separate ingestion pipeline
    This endpoint queues collection jobs in Redis
    """
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sources_requested": request.sources,
        "industry_filter": request.industry,
        "status": "queued",
        "message": "Collection jobs queued in Redis. Workers will process them.",
        "queue_keys": []
    }

    try:
        # Queue collection jobs in Redis
        for source in request.sources:
            queue_key = f"collection:queue:{source}"
            job_data = {
                "source": source,
                "industry": request.industry,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            redis_client.rpush(queue_key, str(job_data))
            results["queue_keys"].append(queue_key)
            logger.info(f"Queued collection job for {source}")
        
        results["status"] = "success"
        
    except Exception as e:
        logger.error(f"Collection queueing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return results


# ============================================================================
# SEARCH & QUERY
# ============================================================================

@app.post("/search")
async def search_threats(query: ValidatedThreatQuery):
    """
    Semantic search across all threats using Weaviate
    """
    try:
        collection = weaviate_client.collections.get("CyberThreatIntelligence")
        
        # Build filters
        filters = []
        if query.severity:
            # Weaviate filter for severity
            pass  # Add filter logic
        
        # Semantic search
        response = collection.query.near_text(
            query=query.query,
            limit=query.limit
        )
        
        threats = []
        for item in response.objects:
            threats.append({
                "threat_id": item.properties.get("threatId"),
                "title": item.properties.get("title"),
                "severity": item.properties.get("severity"),
                "source": item.properties.get("source"),
                "published": item.properties.get("publishedDate"),
                "cves": item.properties.get("cves", []),
                "threat_actors": item.properties.get("threatActors", [])
            })
        
        return {
            "query": query.query,
            "results_count": len(threats),
            "threats": threats
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/threats")
async def get_threats(
    severity: Optional[str] = Depends(validate_severity_param),
    industry: Optional[str] = Depends(validate_industry_param),
    source_type: Optional[str] = None,
    limit: int = Depends(validate_limit_param),
    offset: int = Depends(validate_offset_param)
):
    """
    Get recent threats with filters
    """
    try:
        collection = weaviate_client.collections.get("CyberThreatIntelligence")
        
        # Query threats
        response = collection.query.fetch_objects(
            limit=limit,
            offset=offset
        )
        
        threats = []
        for item in response.objects:
            # Apply filters
            if severity and item.properties.get("severity") != severity:
                continue
            
            threats.append({
                "threat_id": item.properties.get("threatId"),
                "title": item.properties.get("title"),
                "severity": item.properties.get("severity"),
                "source": item.properties.get("source"),
                "published": item.properties.get("publishedDate"),
                "url": item.properties.get("sourceUrl")
            })
        
        return {
            "total": len(threats),
            "limit": limit,
            "offset": offset,
            "threats": threats
        }
        
    except Exception as e:
        logger.error(f"Get threats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/analytics/summary")
async def analytics_summary():
    """
    Get threat landscape summary
    """
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (threat:CyberThreat)
                OPTIONAL MATCH (threat)-[:EXPLOITS]->(cve:CVE)
                OPTIONAL MATCH (threat)-[:ATTRIBUTED_TO]->(actor:ThreatActor)
                RETURN 
                  count(DISTINCT threat) as totalThreats,
                  count(DISTINCT cve) as uniqueCVEs,
                  count(DISTINCT actor) as activeActors,
                  count(DISTINCT CASE WHEN threat.severity = 'critical' THEN threat END) as criticalThreats,
                  count(DISTINCT CASE WHEN threat.severity = 'high' THEN threat END) as highThreats
            """)
            
            record = result.single()
            
            return {
                "threat_landscape": {
                    "total_threats": record["totalThreats"],
                    "unique_cves": record["uniqueCVEs"],
                    "active_actors": record["activeActors"],
                    "critical_threats": record["criticalThreats"],
                    "high_threats": record["highThreats"]
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
    except Exception as e:
        logger.error(f"Analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/top-cves")
async def top_cves(limit: int = Depends(validate_limit_param)):
    """
    Get most exploited CVEs
    """
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (cve:CVE)<-[:EXPLOITS]-(threat:CyberThreat)
                WITH cve, count(threat) as exploitCount
                WHERE exploitCount > 1
                RETURN 
                  cve.cveId as cve,
                  exploitCount as timesExploited
                ORDER BY exploitCount DESC
                LIMIT $limit
            """, limit=limit)
            
            cves = [
                {
                    "cve": record["cve"],
                    "exploit_count": record["timesExploited"]
                }
                for record in result
            ]
            
            return {
                "top_cves": cves,
                "count": len(cves)
            }
            
    except Exception as e:
        logger.error(f"Top CVEs failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# THREAT ACTOR ENDPOINTS
# ============================================================================

@app.get("/actors")
async def get_threat_actors():
    """
    Get all threat actors and their campaigns
    """
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (actor:ThreatActor)<-[:ATTRIBUTED_TO]-(threat:CyberThreat)
                WITH actor, count(threat) as threatCount
                RETURN 
                  actor.actorName as actor,
                  threatCount as campaigns
                ORDER BY threatCount DESC
            """)
            
            actors = [
                {
                    "actor": record["actor"],
                    "campaign_count": record["campaigns"]
                }
                for record in result
            ]
            
            return {
                "threat_actors": actors,
                "total": len(actors)
            }
            
    except Exception as e:
        logger.error(f"Get actors failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/actors/{actor_name}")
async def get_actor_profile(actor_name: str):
    """
    Get detailed threat actor profile
    """
    # Sanitize actor name to prevent injection
    actor_name = InputValidator.sanitize_neo4j_parameter(actor_name, 100)

    try:
        with neo4j_driver.session() as session:
            # Get actor's campaigns
            campaigns_result = session.run("""
                MATCH (actor:ThreatActor {actorName: $actor})<-[:ATTRIBUTED_TO]-(threat:CyberThreat)
                RETURN collect(threat.title) as campaigns
            """, actor=actor_name)
            
            campaigns = campaigns_result.single()["campaigns"]
            
            # Get actor's CVEs
            cves_result = session.run("""
                MATCH (actor:ThreatActor {actorName: $actor})<-[:ATTRIBUTED_TO]-(threat:CyberThreat)-[:EXPLOITS]->(cve:CVE)
                RETURN collect(DISTINCT cve.cveId) as cves
            """, actor=actor_name)
            
            cves = cves_result.single()["cves"]
            
            return {
                "actor": actor_name,
                "campaigns": campaigns,
                "campaign_count": len(campaigns),
                "cves_used": cves,
                "cve_count": len(cves)
            }
            
    except Exception as e:
        logger.error(f"Get actor profile failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CAMPAIGN DETECTION
# ============================================================================

@app.get("/campaigns")
async def detect_campaigns(min_shared_cves: int = 2):
    """
    Detect potential threat campaigns by analyzing similar threats
    """
    # Validate integer range
    min_shared_cves = InputValidator.validate_integer_range(min_shared_cves, 1, 10, "min_shared_cves")

    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (t1:CyberThreat)-[:EXPLOITS]->(cve:CVE)<-[:EXPLOITS]-(t2:CyberThreat)
                WHERE id(t1) < id(t2)
                WITH t1, t2, collect(cve.cveId) as sharedCVEs, count(cve) as commonality
                WHERE commonality >= $min_shared
                RETURN 
                  t1.title as threat1,
                  t2.title as threat2,
                  commonality as sharedVulnerabilities,
                  sharedCVEs[0..5] as sampleCVEs
                ORDER BY commonality DESC
                LIMIT 20
            """, min_shared=min_shared_cves)
            
            campaigns = [
                {
                    "threat1": record["threat1"],
                    "threat2": record["threat2"],
                    "shared_cves": record["sharedVulnerabilities"],
                    "sample_cves": record["sampleCVEs"],
                    "confidence": "high" if record["sharedVulnerabilities"] >= 5 else "medium"
                }
                for record in result
            ]
            
            return {
                "detected_campaigns": campaigns,
                "count": len(campaigns),
                "min_shared_cves": min_shared_cves
            }
            
    except Exception as e:
        logger.error(f"Campaign detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CVE PRIORITIZATION
# ============================================================================

@app.get("/cves/priority")
async def cve_priority_list(limit: int = Depends(validate_limit_param)):
    """
    Get CVE priority list based on exploitation and criticality
    """
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (threat:CyberThreat)-[:EXPLOITS]->(cve:CVE)
                WITH cve, 
                     count(threat) as exploitCount,
                     count(CASE WHEN threat.severity = 'critical' THEN 1 END) as criticalThreats,
                     count(CASE WHEN threat.severity = 'high' THEN 1 END) as highThreats
                WITH cve, exploitCount, criticalThreats, highThreats,
                     (criticalThreats * 3 + highThreats * 2 + exploitCount) as priorityScore
                RETURN 
                  cve.cveId as cve,
                  exploitCount,
                  criticalThreats,
                  highThreats,
                  priorityScore
                ORDER BY priorityScore DESC
                LIMIT $limit
            """, limit=limit)
            
            priorities = [
                {
                    "cve": record["cve"],
                    "priority_score": record["priorityScore"],
                    "exploit_count": record["exploitCount"],
                    "critical_threats": record["criticalThreats"],
                    "high_threats": record["highThreats"],
                    "recommendation": "PATCH IMMEDIATELY" if record["priorityScore"] > 20 else "HIGH PRIORITY"
                }
                for record in result
            ]
            
            return {
                "priority_list": priorities,
                "total": len(priorities)
            }
            
    except Exception as e:
        logger.error(f"CVE prioritization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SOURCE-SPECIFIC ENDPOINTS
# ============================================================================

@app.get("/sources/ot-ics")
async def get_ot_ics_threats(limit: int = Depends(validate_limit_param)):
    """
    Get OT/ICS specific threats (SCADA, Industrial Control Systems)
    """
    try:
        collection = weaviate_client.collections.get("CyberThreatIntelligence")
        
        response = collection.query.fetch_objects(limit=200)  # Get more to filter
        
        ot_threats = []
        ot_keywords = ["ics", "scada", "plc", "hmi", "industrial", "ot", "siemens", 
                       "schneider", "rockwell", "modbus", "profinet"]
        
        for item in response.objects:
            title = item.properties.get("title", "").lower()
            source = item.properties.get("source", "").lower()
            tags = str(item.properties.get("tags", [])).lower()
            content = item.properties.get("content", "").lower()
            
            # Check if it's OT/ICS related
            if any(keyword in title + source + tags + content for keyword in ot_keywords):
                ot_threats.append({
                    "title": item.properties.get("title"),
                    "severity": item.properties.get("severity"),
                    "source": item.properties.get("source"),
                    "published": item.properties.get("publishedDate"),
                    "url": item.properties.get("sourceUrl")
                })
                
                if len(ot_threats) >= limit:
                    break
        
        return {
            "ot_ics_threats": ot_threats,
            "count": len(ot_threats),
            "keywords_matched": ot_keywords
        }
        
    except Exception as e:
        logger.error(f"OT/ICS threats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sources/dark-web")
async def get_dark_web_intel():
    """
    Get recent dark web intelligence (ransomware, breaches)
    Query from Weaviate for dark-web tagged threats
    """
    try:
        collection = weaviate_client.collections.get("CyberThreatIntelligence")
        
        # Query for dark web threats
        response = collection.query.fetch_objects(limit=50)
        
        dark_web_items = []
        for item in response.objects:
            source = item.properties.get("source", "")
            tags = str(item.properties.get("tags", []))
            
            # Filter for dark web sources
            if any(keyword in source.lower() for keyword in ["ransomware", "breach", "leak", "dark"]) or \
               any(keyword in tags.lower() for keyword in ["ransomware", "breach", "dark_web"]):
                dark_web_items.append({
                    "title": item.properties.get("title"),
                    "severity": item.properties.get("severity"),
                    "source": source,
                    "published": item.properties.get("publishedDate"),
                    "url": item.properties.get("sourceUrl")
                })
        
        return {
            "dark_web_intelligence": dark_web_items[:20],
            "total": len(dark_web_items),
            "sources": ["Ransomware.live", "Have I Been Pwned", "Threat Intel Feeds"]
        }
        
    except Exception as e:
        logger.error(f"Dark web intel failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ML ENDPOINTS INTEGRATION
# ============================================================================

# Import ML router
try:
    from backend.api.ml_endpoints import ml_router
    app.include_router(ml_router)
    logger.info("✅ ML endpoints integrated")
except ImportError as e:
    logger.warning(f"⚠️ ML endpoints not available: {e}")


# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database connections from environment variables"""
    global redis_client, weaviate_client, neo4j_driver

    logger.info("🚀 Cyber-PI-Intel API starting...")

    # Initialize Redis
    try:
        redis_host = os.getenv("REDIS_HOST", "redis.cyber-pi-intel.svc.cluster.local")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD")

        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True
        )
        redis_client.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        redis_client = None

    # Initialize Weaviate
    try:
        weaviate_host = os.getenv("WEAVIATE_HOST", "weaviate.cyber-pi-intel.svc.cluster.local")
        weaviate_port = int(os.getenv("WEAVIATE_PORT", "8080"))
        weaviate_grpc_port = int(os.getenv("WEAVIATE_GRPC_PORT", "50051"))

        weaviate_client = weaviate.connect_to_custom(
            http_host=weaviate_host,
            http_port=weaviate_port,
            http_secure=False,
            grpc_host=weaviate_host,
            grpc_port=weaviate_grpc_port,
            grpc_secure=False
        )
        logger.info("✅ Weaviate connected")
    except Exception as e:
        logger.error(f"❌ Weaviate connection failed: {e}")
        weaviate_client = None

    # Initialize Neo4j
    try:
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j.cyber-pi-intel.svc.cluster.local:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD")

        if not neo4j_password:
            raise ValueError("NEO4J_PASSWORD environment variable is required")

        neo4j_driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )
        # Verify connection
        with neo4j_driver.session() as session:
            session.run("RETURN 1")
        logger.info("✅ Neo4j connected")
    except Exception as e:
        logger.error(f"❌ Neo4j connection failed: {e}")
        neo4j_driver = None

    logger.info("✅ ML endpoints ready")
    logger.info("🎉 API ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections"""
    logger.info("👋 Shutting down...")

    if weaviate_client:
        try:
            weaviate_client.close()
            logger.info("✅ Weaviate closed")
        except Exception as e:
            logger.error(f"Error closing Weaviate: {e}")

    if neo4j_driver:
        try:
            neo4j_driver.close()
            logger.info("✅ Neo4j closed")
        except Exception as e:
            logger.error(f"Error closing Neo4j: {e}")

    if redis_client:
        try:
            redis_client.close()
            logger.info("✅ Redis closed")
        except Exception as e:
            logger.error(f"Error closing Redis: {e}")

    # Clean up ML predictor
    try:
        from backend.api.ml_endpoints import predictor
        if predictor:
            predictor.close()
    except Exception as e:
        logger.error(f"Error closing ML predictor: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
