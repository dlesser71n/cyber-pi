#!/usr/bin/env python3
"""
Intelligence API endpoints
Functional endpoints for threat intelligence queries
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from ..database import get_db_session, check_redis_health, check_neo4j_health, check_weaviate_health
from ..auth import get_current_user, require_permission

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])

@router.get("/search")
async def search_intelligence(
    query: str = Query(..., description="Search query string"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    source_types: Optional[str] = Query(None, description="Comma-separated source types"),
    min_confidence: float = Query(0.7, ge=0.0, le=1.0, description="Minimum confidence score"),
    current_user: Dict[str, Any] = Depends(require_permission("read"))
):
    """
    Search intelligence database across all storage systems
    """
    try:
        async with get_db_session() as db:
            # Search Redis for cached results first
            redis_client = db.get_redis()
            cache_key = f"search:{hash(query)}:{limit}:{min_confidence}"
            
            # Try cache first
            cached_result = redis_client.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for query: {query}")
                import json
                return json.loads(cached_result)
            
            # Search Neo4j for structured threat intelligence
            neo4j_driver = db.get_neo4j()
            neo4j_results = []
            
            with neo4j_driver.session() as session:
                # Search for CVEs, threats, and related entities
                neo4j_query = """
                MATCH (n)
                WHERE (n:CVE OR n:ThreatIntel OR n:Product OR n:Vendor)
                AND toLower(n.description) CONTAINS toLower($query)
                RETURN n
                LIMIT $limit
                """
                result = session.run(neo4j_query, query=query.lower(), limit=limit)
                
                for record in result:
                    node = record["n"]
                    neo4j_results.append({
                        "id": node.element_id,
                        "type": list(node.labels)[0],
                        "properties": dict(node),
                        "source": "neo4j"
                    })
            
            # Search Weaviate for semantic similarity
            weaviate_client = db.get_weaviate()
            weaviate_results = []
            
            try:
                # Check if ThreatIntel class exists
                if "ThreatIntel" in weaviate_client.schema.get()['classes']:
                    weaviate_result = weaviate_client.query.get(
                        things="ThreatIntel",
                        fields=["title", "description", "severity", "source", "confidence"],
                        near_text={
                            "concepts": [query],
                            "certainty": min_confidence
                        },
                        limit=limit
                    )
                    
                    for item in weaviate_result:
                        weaviate_results.append({
                            "id": item["_additional"]["id"],
                            "type": "ThreatIntel",
                            "properties": {k: v for k, v in item.items() if not k.startswith("_")},
                            "source": "weaviate",
                            "certainty": item["_additional"]["certainty"]
                        })
            except Exception as e:
                logger.warning(f"Weaviate search failed: {e}")
            
            # Combine results
            all_results = neo4j_results + weaviate_results
            
            # Sort by relevance (simple implementation)
            all_results.sort(key=lambda x: x.get("certainty", 0.5), reverse=True)
            
            # Limit results
            all_results = all_results[:limit]
            
            # Cache the results for 5 minutes
            response_data = {
                "query": query,
                "results": all_results,
                "total": len(all_results),
                "processing_time_ms": 0,  # TODO: Add timing
                "sources": {
                    "neo4j": len(neo4j_results),
                    "weaviate": len(weaviate_results)
                }
            }
            
            import json
            redis_client.setex(cache_key, 300, json.dumps(response_data))
            
            return response_data
            
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/latest")
async def get_latest_intelligence(
    category: str = Query("all", description="Category filter"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of items")
):
    """
    Get latest intelligence items from all sources
    """
    try:
        async with get_db_session() as db:
            redis_client = db.get_redis()
            neo4j_driver = db.get_neo4j()
            
            # Get latest items from Neo4j
            latest_items = []
            
            with neo4j_driver.session() as session:
                # Get recent CVEs and threat intelligence
                neo4j_query = """
                MATCH (n)
                WHERE (n:CVE OR n:ThreatIntel)
                AND n.published IS NOT NULL
                RETURN n
                ORDER BY n.published DESC
                LIMIT $limit
                """
                result = session.run(neo4j_query, limit=limit)
                
                for record in result:
                    node = record["n"]
                    latest_items.append({
                        "id": node.element_id,
                        "type": list(node.labels)[0],
                        "properties": dict(node),
                        "source": "neo4j"
                    })
            
            return {
                "category": category,
                "items": latest_items,
                "total": len(latest_items),
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Get latest intelligence failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get latest intelligence: {str(e)}")

@router.get("/threats")
async def get_active_threats(
    severity: str = Query("all", description="Severity filter"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of threats")
):
    """
    Get active threat intelligence with severity filtering
    """
    try:
        async with get_db_session() as db:
            neo4j_driver = db.get_neo4j()
            
            threats = []
            
            with neo4j_driver.session() as session:
                # Build query based on severity filter
                if severity.lower() == "all":
                    neo4j_query = """
                    MATCH (t:ThreatIntel)
                    WHERE t.severity IS NOT NULL
                    RETURN t
                    ORDER BY t.confidence DESC, t.published DESC
                    LIMIT $limit
                    """
                    params = {"limit": limit}
                else:
                    neo4j_query = """
                    MATCH (t:ThreatIntel)
                    WHERE toLower(t.severity) = toLower($severity)
                    RETURN t
                    ORDER BY t.confidence DESC, t.published DESC
                    LIMIT $limit
                    """
                    params = {"severity": severity, "limit": limit}
                
                result = session.run(neo4j_query, **params)
                
                for record in result:
                    threat = record["t"]
                    threats.append({
                        "id": threat.element_id,
                        "type": "ThreatIntel",
                        "properties": dict(threat)
                    })
            
            return {
                "severity": severity,
                "threats": threats,
                "total": len(threats),
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Get active threats failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active threats: {str(e)}")

@router.get("/stats")
async def get_intelligence_stats():
    """
    Get intelligence database statistics
    """
    try:
        async with get_db_session() as db:
            redis_client = db.get_redis()
            neo4j_driver = db.get_neo4j()
            weaviate_client = db.get_weaviate()
            
            stats = {
                "timestamp": datetime.utcnow().isoformat(),
                "storage": {},
                "intelligence": {}
            }
            
            # Redis stats
            try:
                redis_info = redis_client.info()
                stats["storage"]["redis"] = {
                    "keys": redis_info.get("db0", {}).get("keys", 0),
                    "memory_used": redis_info.get("used_memory_human", "unknown"),
                    "connected_clients": redis_info.get("connected_clients", 0)
                }
            except Exception as e:
                stats["storage"]["redis"] = {"error": str(e)}
            
            # Neo4j stats
            try:
                with neo4j_driver.session() as session:
                    # Count nodes by type
                    node_counts = session.run("""
                    MATCH (n)
                    RETURN labels(n) as type, count(n) as count
                    """)
                    
                    neo4j_stats = {}
                    for record in node_counts:
                        node_type = record["type"][0] if record["type"] else "Unknown"
                        neo4j_stats[node_type.lower()] = record["count"]
                    
                    stats["storage"]["neo4j"] = neo4j_stats
            except Exception as e:
                stats["storage"]["neo4j"] = {"error": str(e)}
            
            # Weaviate stats
            try:
                schema = weaviate_client.schema.get()
                class_stats = {}
                
                for class_info in schema.get("classes", []):
                    class_name = class_info["class"]
                    # Get object count (simplified)
                    class_stats[class_name.lower()] = "available"
                
                stats["storage"]["weaviate"] = class_stats
            except Exception as e:
                stats["storage"]["weaviate"] = {"error": str(e)}
            
            return stats
            
    except Exception as e:
        logger.error(f"Get intelligence stats failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get intelligence stats: {str(e)}")
