"""
Simplified Router for cyber-pi Integration
Redis + Weaviate + Neo4j (No Kafka)

Architecture:
- Redis: Hot cache (0.22ms reads)
- Weaviate: Permanent vector storage (semantic search)
- Neo4j: Relationship graphs (attack chains)
"""

from typing import Dict, Any, Optional, List
import asyncio
import json
from datetime import datetime, timedelta
import structlog
import hashlib

from backend.core.stix_converter import STIXConverter, convert_threat_to_stix

logger = structlog.get_logger(__name__)

class SimplifiedRouter:
    """
    Simplified routing without Kafka complexity
    Direct writes to all databases for durability
    Redis-first reads for performance
    """
    
    def __init__(self, redis_client, weaviate_client, neo4j_driver, ollama_client):
        self.redis = redis_client
        self.weaviate = weaviate_client
        self.neo4j = neo4j_driver
        self.ollama = ollama_client
        
        # STIX converter for industry-standard format
        try:
            self.stix_converter = STIXConverter()
            self.stix_enabled = True
        except ImportError:
            logger.warning("STIX converter not available - install stix2 library")
            self.stix_converter = None
            self.stix_enabled = False
        
        # Performance metrics
        self.metrics = {
            "redis_writes": 0,
            "weaviate_writes": 0,
            "neo4j_writes": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_queries": 0,
            "stix_conversions": 0
        }
    
    async def ingest_threat(self, 
                           threat: Dict[str, Any],
                           generate_embedding: bool = True) -> str:
        """
        Ingest threat into tri-modal storage
        
        Flow:
        1. Generate embedding (if needed)
        2. Store in Weaviate (permanent)
        3. Cache in Redis (fast access)
        4. Build graph (if entities present)
        
        Returns: threat_id
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Generate unique threat ID
            threat_id = self._generate_threat_id(threat)
            
            # Convert to STIX 2.1 format (industry standard)
            stix_bundle = None
            stix_id = None
            stix_type = None
            if self.stix_enabled:
                try:
                    stix_bundle = self.stix_converter.threat_to_stix_bundle(threat)
                    # Extract primary object ID and type
                    if stix_bundle.objects:
                        primary_obj = stix_bundle.objects[0]
                        stix_id = primary_obj.id
                        stix_type = primary_obj.type
                    self.metrics["stix_conversions"] += 1
                    logger.info("Converted threat to STIX 2.1", 
                               threat_id=threat_id, 
                               stix_id=stix_id,
                               stix_type=stix_type)
                except Exception as e:
                    logger.warning(f"STIX conversion failed: {e}")
            
            # 1. Generate embedding for semantic search
            embedding = None
            if generate_embedding and threat.get('content'):
                try:
                    # Use Ollama to generate embedding
                    embedding = await self._generate_embedding(threat['content'])
                except Exception as e:
                    logger.warning(f"Failed to generate embedding: {e}")
            
            # 2. Store in Weaviate (permanent storage with STIX)
            weaviate_success = await self._store_in_weaviate(
                threat_id=threat_id,
                threat=threat,
                embedding=embedding,
                stix_bundle=stix_bundle,
                stix_id=stix_id,
                stix_type=stix_type
            )
            if weaviate_success:
                self.metrics["weaviate_writes"] += 1
            
            # 3. Cache in Redis (hot cache, 1 hour TTL)
            redis_success = await self._cache_in_redis(
                threat_id=threat_id,
                threat=threat,
                ttl=3600
            )
            if redis_success:
                self.metrics["redis_writes"] += 1
            
            # 4. Build graph relationships (if entities present)
            if threat.get('entities') or threat.get('threat_actor'):
                neo4j_success = await self._build_graph_relationships(
                    threat_id=threat_id,
                    threat=threat
                )
                if neo4j_success:
                    self.metrics["neo4j_writes"] += 1
            
            # Log performance
            latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.info("Threat ingested",
                       threat_id=threat_id,
                       latency_ms=latency_ms,
                       weaviate=weaviate_success,
                       redis=redis_success)
            
            return threat_id
            
        except Exception as e:
            logger.error(f"Threat ingestion failed: {e}", exc_info=True)
            raise
    
    async def query_threats(self,
                           query: str,
                           industry: Optional[str] = None,
                           limit: int = 50,
                           use_cache: bool = True) -> List[Dict]:
        """
        Query threats with Redis-first strategy
        
        Flow:
        1. Check Redis cache (0.22ms)
        2. If miss, semantic search in Weaviate (2-5ms)
        3. Cache results for future queries
        """
        self.metrics["total_queries"] += 1
        cache_key = self._generate_cache_key(query, industry, limit)
        
        # 1. Try Redis cache first (if enabled)
        if use_cache:
            cached = await self._read_from_cache(cache_key)
            if cached:
                self.metrics["cache_hits"] += 1
                logger.debug("Cache hit", query=query, cache_key=cache_key)
                return cached
        
        self.metrics["cache_misses"] += 1
        
        # 2. Cache miss - perform semantic search
        results = await self._semantic_search_weaviate(
            query=query,
            industry=industry,
            limit=limit
        )
        
        # 3. Cache results for next time
        if use_cache and results:
            await self._write_to_cache(cache_key, results, ttl=3600)
        
        return results
    
    async def get_threat_by_id(self, threat_id: str) -> Optional[Dict]:
        """Get single threat by ID (Redis-first)"""
        
        # Try cache first
        cached = await self.redis.get(f"threat:{threat_id}")
        if cached:
            self.metrics["cache_hits"] += 1
            return json.loads(cached)
        
        self.metrics["cache_misses"] += 1
        
        # Fallback to Weaviate
        threat = await self._get_from_weaviate(threat_id)
        
        # Re-hydrate cache
        if threat:
            await self._cache_in_redis(threat_id, threat, ttl=3600)
        
        return threat
    
    async def get_related_threats(self,
                                 threat_id: str,
                                 relationship_type: Optional[str] = None,
                                 max_depth: int = 2) -> List[Dict]:
        """
        Get related threats using Neo4j graph
        
        Example: Find threats from same actor, or using same TTP
        """
        if not self.neo4j:
            return []
        
        try:
            async with self.neo4j.session() as session:
                # Cypher query to find related threats
                query = """
                MATCH (t:Threat {id: $threat_id})-[r*1..{max_depth}]-(related:Threat)
                {relationship_filter}
                RETURN DISTINCT related
                LIMIT 20
                """.format(
                    max_depth=max_depth,
                    relationship_filter=f"WHERE type(r) = '{relationship_type}'" if relationship_type else ""
                )
                
                result = await session.run(query, threat_id=threat_id)
                records = await result.data()
                
                related = [record['related'] for record in records]
                return related
                
        except Exception as e:
            logger.error(f"Failed to get related threats: {e}")
            return []
    
    # Private helper methods
    
    def _generate_threat_id(self, threat: Dict) -> str:
        """Generate unique threat ID from content hash"""
        content = threat.get('title', '') + threat.get('content', '')
        hash_obj = hashlib.sha256(content.encode())
        return f"threat_{hash_obj.hexdigest()[:16]}"
    
    def _generate_cache_key(self, query: str, industry: Optional[str], limit: int) -> str:
        """Generate cache key for query"""
        key_parts = [query, industry or "all", str(limit)]
        key_string = ":".join(key_parts)
        hash_obj = hashlib.md5(key_string.encode())
        return f"query:{hash_obj.hexdigest()}"
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama"""
        if not self.ollama:
            raise Exception("Ollama client not available")
        
        try:
            response = await self.ollama.post(
                "/api/embeddings",
                json={
                    "model": "nomic-embed-text:latest",
                    "prompt": text
                }
            )
            data = response.json()
            return data.get('embedding', [])
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    async def _store_in_weaviate(self,
                                threat_id: str,
                                threat: Dict,
                                embedding: Optional[List[float]],
                                stix_bundle=None,
                                stix_id: Optional[str] = None,
                                stix_type: Optional[str] = None) -> bool:
        """Store threat in Weaviate with STIX 2.1 data"""
        if not self.weaviate:
            return False
        
        try:
            # Prepare data object with STIX fields
            data_object = {
                "threatId": threat_id,
                "stixId": stix_id or "",
                "stixType": stix_type or "unknown",
                "stixVersion": "2.1" if stix_bundle else "",
                "stixObject": stix_bundle.serialize() if stix_bundle else "",
                "title": threat.get('title', ''),
                "content": threat.get('content', ''),
                "source": threat.get('source', ''),
                "industry": threat.get('industry', ''),
                "severity": threat.get('severity', 'medium'),
                "publishedDate": threat.get('published_date', datetime.utcnow().isoformat()),
                "ingestedAt": datetime.utcnow().isoformat()
            }
            
            # Store with or without embedding
            if embedding:
                self.weaviate.data_object.create(
                    data_object=data_object,
                    class_name="Threat",
                    vector=embedding
                )
            else:
                self.weaviate.data_object.create(
                    data_object=data_object,
                    class_name="Threat"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Weaviate storage failed: {e}")
            return False
    
    async def _cache_in_redis(self,
                             threat_id: str,
                             threat: Dict,
                             ttl: int) -> bool:
        """Cache threat in Redis"""
        if not self.redis:
            return False
        
        try:
            await self.redis.setex(
                f"threat:{threat_id}",
                ttl,
                json.dumps(threat)
            )
            return True
        except Exception as e:
            logger.error(f"Redis caching failed: {e}")
            return False
    
    async def _build_graph_relationships(self,
                                        threat_id: str,
                                        threat: Dict) -> bool:
        """Build graph relationships in Neo4j"""
        if not self.neo4j:
            return False
        
        try:
            async with self.neo4j.session() as session:
                # Create threat node
                await session.run(
                    """
                    MERGE (t:Threat {id: $id})
                    SET t.title = $title,
                        t.severity = $severity,
                        t.timestamp = datetime($timestamp)
                    """,
                    id=threat_id,
                    title=threat.get('title', ''),
                    severity=threat.get('severity', 'medium'),
                    timestamp=datetime.utcnow().isoformat()
                )
                
                # Create relationships to threat actor (if present)
                if threat.get('threat_actor'):
                    await session.run(
                        """
                        MATCH (t:Threat {id: $threat_id})
                        MERGE (actor:ThreatActor {name: $actor_name})
                        MERGE (actor)-[:RESPONSIBLE_FOR]->(t)
                        """,
                        threat_id=threat_id,
                        actor_name=threat['threat_actor']
                    )
                
                # Create relationships to industry (if present)
                if threat.get('industry'):
                    await session.run(
                        """
                        MATCH (t:Threat {id: $threat_id})
                        MERGE (i:Industry {name: $industry_name})
                        MERGE (t)-[:TARGETS]->(i)
                        """,
                        threat_id=threat_id,
                        industry_name=threat['industry']
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Neo4j relationship building failed: {e}")
            return False
    
    async def _read_from_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """Read from Redis cache"""
        if not self.redis:
            return None
        
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.debug(f"Cache read failed: {e}")
        
        return None
    
    async def _write_to_cache(self,
                             cache_key: str,
                             data: List[Dict],
                             ttl: int) -> bool:
        """Write to Redis cache"""
        if not self.redis:
            return False
        
        try:
            await self.redis.setex(
                cache_key,
                ttl,
                json.dumps(data)
            )
            return True
        except Exception as e:
            logger.error(f"Cache write failed: {e}")
            return False
    
    async def _semantic_search_weaviate(self,
                                       query: str,
                                       industry: Optional[str],
                                       limit: int) -> List[Dict]:
        """Perform semantic search in Weaviate"""
        if not self.weaviate:
            return []
        
        try:
            # Build Weaviate query
            where_filter = None
            if industry:
                where_filter = {
                    "path": ["industry"],
                    "operator": "Equal",
                    "valueString": industry
                }
            
            # Execute semantic search
            result = self.weaviate.query.get(
                "Threat",
                ["threatId", "title", "content", "source", "industry", "severity", "publishedDate"]
            ).with_near_text({
                "concepts": [query]
            })
            
            if where_filter:
                result = result.with_where(where_filter)
            
            result = result.with_limit(limit).do()
            
            # Extract threats from result
            threats = result.get('data', {}).get('Get', {}).get('Threat', [])
            return threats
            
        except Exception as e:
            logger.error(f"Weaviate search failed: {e}")
            return []
    
    async def _get_from_weaviate(self, threat_id: str) -> Optional[Dict]:
        """Get single threat from Weaviate by ID"""
        if not self.weaviate:
            return None
        
        try:
            result = self.weaviate.query.get(
                "Threat",
                ["threatId", "title", "content", "source", "industry", "severity", "publishedDate"]
            ).with_where({
                "path": ["threatId"],
                "operator": "Equal",
                "valueString": threat_id
            }).with_limit(1).do()
            
            threats = result.get('data', {}).get('Get', {}).get('Threat', [])
            return threats[0] if threats else None
            
        except Exception as e:
            logger.error(f"Weaviate retrieval failed: {e}")
            return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        total_cache_ops = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_hit_rate = (
            self.metrics["cache_hits"] / max(1, total_cache_ops)
        ) * 100
        
        return {
            **self.metrics,
            "cache_hit_rate": cache_hit_rate,
            "total_cache_operations": total_cache_ops
        }
