"""
Database Connection Manager for TQAKB V4
Manages connections to Redis, Neo4j, and Weaviate
"""

import asyncio
from typing import Optional, Dict, Any
import structlog
import redis.asyncio as redis
from neo4j import AsyncGraphDatabase, AsyncDriver
import weaviate
from weaviate import WeaviateClient
import httpx

from backend.core.config import settings

logger = structlog.get_logger(__name__)

class ConnectionManager:
    """Manages all database connections"""

    def __init__(self) -> None:
        self.redis_client: Optional[redis.Redis] = None
        self.neo4j_driver: Optional[AsyncDriver] = None
        self.weaviate_client: Optional[WeaviateClient] = None
        self.ollama_client: Optional[httpx.AsyncClient] = None
        self._initialized: bool = False
    
    async def initialize(self) -> None:
        """Initialize all database connections"""
        if self._initialized:
            return

        logger.info("Initializing database connections")
        
        # Initialize Redis
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password.get_secret_value() if settings.redis_password else None,
                decode_responses=True,
                max_connections=settings.redis_pool_max_connections
            )
            await self.redis_client.ping()
            logger.info("Redis connection established", 
                       host=settings.redis_host, 
                       port=settings.redis_port)
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            self.redis_client = None
        
        # Initialize Neo4j
        try:
            self.neo4j_driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password.get_secret_value()),
                max_connection_pool_size=settings.neo4j_connection_pool_size
            )
            # Verify connection
            async with self.neo4j_driver.session() as session:
                await session.run("RETURN 1")
            logger.info("Neo4j connection established", uri=settings.neo4j_uri)
        except Exception as e:
            logger.error("Failed to connect to Neo4j", error=str(e))
            self.neo4j_driver = None
        
        # Initialize Weaviate
        try:
            auth_config = None
            if settings.weaviate_api_key:
                auth_config = weaviate.auth.AuthApiKey(
                    api_key=settings.weaviate_api_key.get_secret_value()
                )
            
            self.weaviate_client = weaviate.Client(
                url=settings.weaviate_url,
                auth_client_secret=auth_config,
                timeout_config=(settings.weaviate_timeout, settings.weaviate_timeout)
            )
            
            # Verify connection
            if self.weaviate_client.is_ready():
                logger.info("Weaviate connection established", url=settings.weaviate_url)
            else:
                raise Exception("Weaviate is not ready")
        except Exception as e:
            logger.error("Failed to connect to Weaviate", error=str(e))
            self.weaviate_client = None
        
        # Initialize Ollama client
        try:
            self.ollama_client = httpx.AsyncClient(
                base_url=settings.ollama_host,
                timeout=settings.ollama_timeout
            )
            # Verify connection
            response = await self.ollama_client.get("/api/tags")
            if response.status_code == 200:
                logger.info("Ollama connection established", host=settings.ollama_host)
            else:
                raise Exception(f"Ollama returned status {response.status_code}")
        except Exception as e:
            logger.error("Failed to connect to Ollama", error=str(e))
            self.ollama_client = None
        
        self._initialized = True
        logger.info("Database connections initialized")
    
    async def close(self) -> None:
        """Close all database connections"""
        logger.info("Closing database connections")
        
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
        
        if self.neo4j_driver:
            await self.neo4j_driver.close()
            logger.info("Neo4j connection closed")
        
        if self.weaviate_client:
            # Weaviate client doesn't have async close
            logger.info("Weaviate connection closed")
        
        if self.ollama_client:
            await self.ollama_client.aclose()
            logger.info("Ollama connection closed")
        
        self._initialized = False
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all connections"""
        health = {}
        
        # Check Redis
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health["redis"] = True
            except Exception:
                health["redis"] = False
        else:
            health["redis"] = False
        
        # Check Neo4j
        if self.neo4j_driver:
            try:
                async with self.neo4j_driver.session() as session:
                    await session.run("RETURN 1")
                health["neo4j"] = True
            except Exception:
                health["neo4j"] = False
        else:
            health["neo4j"] = False
        
        # Check Weaviate
        if self.weaviate_client:
            try:
                health["weaviate"] = self.weaviate_client.is_ready()
            except Exception:
                health["weaviate"] = False
        else:
            health["weaviate"] = False
        
        # Check Ollama
        if self.ollama_client:
            try:
                response = await self.ollama_client.get("/api/tags")
                health["ollama"] = response.status_code == 200
            except Exception:
                health["ollama"] = False
        else:
            health["ollama"] = False
        
        return health
    
    def get_redis(self) -> Optional[redis.Redis]:
        """Get Redis client"""
        return self.redis_client
    
    def get_neo4j(self) -> Optional[AsyncDriver]:
        """Get Neo4j driver"""
        return self.neo4j_driver
    
    def get_weaviate(self) -> Optional[WeaviateClient]:
        """Get Weaviate client"""
        return self.weaviate_client
    
    def get_ollama(self) -> Optional[httpx.AsyncClient]:
        """Get Ollama client"""
        return self.ollama_client

# Singleton instance
connection_manager = ConnectionManager()