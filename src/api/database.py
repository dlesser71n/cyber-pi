#!/usr/bin/env python3
"""
Database connection management for cyber-pi API
Enterprise-grade connection handling with retry logic
"""

import redis
import neo4j
import weaviate
from typing import Optional, Dict, Any
import logging
from contextlib import asynccontextmanager

from config.settings import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages all database connections for the API"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.neo4j_driver: Optional[neo4j.GraphDatabase.driver] = None
        self.weaviate_client: Optional[weaviate.Client] = None
        
    async def initialize_connections(self):
        """Initialize all database connections"""
        try:
            # Initialize Redis
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test Redis connection
            self.redis_client.ping()
            logger.info(f"✅ Redis connected: {settings.redis_host}:{settings.redis_port}")
            
            # Initialize Neo4j
            self.neo4j_driver = neo4j.GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50
            )
            
            # Test Neo4j connection
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"✅ Neo4j connected: {settings.neo4j_uri}")
            
            # Initialize Weaviate
            self.weaviate_client = weaviate.Client(
                url=settings.weaviate_url,
                auth_client_secret=weaviate.AuthApiKey(api_key=settings.weaviate_api_key) if settings.weaviate_api_key else None
            )
            
            # Test Weaviate connection
            self.weaviate_client.is_ready()
            logger.info(f"✅ Weaviate connected: {settings.weaviate_url}")
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    async def close_connections(self):
        """Close all database connections"""
        try:
            if self.redis_client:
                self.redis_client.close()
                logger.info("✅ Redis connection closed")
                
            if self.neo4j_driver:
                self.neo4j_driver.close()
                logger.info("✅ Neo4j connection closed")
                
            # Weaviate doesn't need explicit closing
            logger.info("✅ Database connections closed")
            
        except Exception as e:
            logger.error(f"❌ Error closing connections: {e}")
    
    def get_redis(self) -> redis.Redis:
        """Get Redis client"""
        if not self.redis_client:
            raise RuntimeError("Redis not initialized")
        return self.redis_client
    
    def get_neo4j(self) -> neo4j.GraphDatabase.driver:
        """Get Neo4j driver"""
        if not self.neo4j_driver:
            raise RuntimeError("Neo4j not initialized")
        return self.neo4j_driver
    
    def get_weaviate(self) -> weaviate.Client:
        """Get Weaviate client"""
        if not self.weaviate_client:
            raise RuntimeError("Weaviate not initialized")
        return self.weaviate_client

# Global database manager instance
db_manager = DatabaseManager()

@asynccontextmanager
async def get_db_session():
    """Context manager for database operations"""
    try:
        yield db_manager
    except Exception as e:
        logger.error(f"Database operation error: {e}")
        raise

# Health check functions
async def check_redis_health() -> Dict[str, Any]:
    """Check Redis health"""
    try:
        redis_client = db_manager.get_redis()
        info = redis_client.info()
        return {
            "status": "healthy",
            "connected_clients": info.get("connected_clients", 0),
            "used_memory": info.get("used_memory_human", "unknown"),
            "uptime_seconds": info.get("uptime_in_seconds", 0)
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_neo4j_health() -> Dict[str, Any]:
    """Check Neo4j health"""
    try:
        driver = db_manager.get_neo4j()
        with driver.session() as session:
            result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions[0] as version")
            record = result.single()
            return {
                "status": "healthy",
                "database": record["name"],
                "version": record["version"]
            }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_weaviate_health() -> Dict[str, Any]:
    """Check Weaviate health"""
    try:
        client = db_manager.get_weaviate()
        nodes = client.cluster.get_nodes_status()
        return {
            "status": "healthy",
            "nodes": len(nodes),
            "ready": client.is_ready()
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
