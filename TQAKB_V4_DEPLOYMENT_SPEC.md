# TQAKB V4 Golden Deployment for cyber-pi
# Using Weaviate (NOT Milvus)

**Date:** October 31, 2025  
**Source:** V4 Golden commit 4893b3b (September 5, 2025)  
**Namespace:** cyber-pi-intel (clean deployment)  
**Vector DB:** Weaviate (modern, REST API)

---

## Architecture Overview

### Three-Layer Intelligence Stack

**Layer 1: Redis 8.2.1 (Speed)**
- Purpose: Ultra-fast caching and routing
- Performance: 0.22ms latency (proven)
- Cache hit rate: 98.5%
- Event streaming: Redis Streams (not Kafka)
- Endpoint: localhost:30379 (NodePort)

**Layer 2: Weaviate (Semantic Intelligence)**
- Purpose: Vector storage and semantic search
- Technology: Modern vector database
- API: REST (http://localhost:30883)
- Storage: Persistent (10+ years)
- Features: Semantic search, entity extraction

**Layer 3: Neo4j (Relationships)**
- Purpose: Graph database for attack chains
- Protocol: Bolt (localhost:30687)
- Use cases: Threat actor tracking, IOC correlation
- Auth: neo4j / [password-to-be-set]

---

## Why This Configuration

### V4 Golden Advantages

**Proven Performance (Sep 5, 2025):**
- 75x faster than V3 (0.22ms vs 16.55ms)
- 10,000+ requests/second throughput
- 98.5% cache hit rate
- Redis-first intelligent routing

**Clean Architecture:**
- 32 focused Python files (not 169+)
- ~80 dependencies (not 150+)
- Event-driven with Redis Streams
- No over-engineering (no GPU, no service mesh)

### Weaviate Over Milvus

**Why Weaviate:**
- ✅ Modern REST API (easier integration)
- ✅ Better semantic search capabilities
- ✅ Native vector operations
- ✅ Easier deployment on MicroK8s
- ✅ Better documentation
- ✅ Active community support

**Milvus weaknesses:**
- ❌ More complex deployment
- ❌ gRPC dependencies (protobuf issues)
- ❌ Heavier resource usage
- ❌ Less intuitive API

---

## Deployment Strategy

### Phase 1: Extract V4 Golden Code

**Goal:** Get clean V4 code at commit 4893b3b

**Steps:**
```bash
# 1. Navigate to V4 golden repository
cd /home/david/archived/20251030_tqakb_final/tqakb-v4-golden

# 2. Checkout the golden commit
git checkout 4893b3b

# 3. Copy to new clean location
cp -r /home/david/archived/20251030_tqakb_final/tqakb-v4-golden \
      /home/david/projects/cyber-pi-intel

# 4. Verify it's the right code
cd /home/david/projects/cyber-pi-intel
git log --oneline -1
# Should show: 4893b3b feat: TQAKB v4.0 - Production-ready with Redis-first architecture
```

**Success criteria:**
- [ ] Clean copy created
- [ ] At correct commit (4893b3b)
- [ ] No post-Sep-5 complexity

---

### Phase 2: Configure for Weaviate

**Goal:** Replace any Milvus references with Weaviate

**Files to check:**
```bash
# Search for Milvus references
cd /home/david/projects/cyber-pi-intel
grep -r "milvus" --include="*.py" --include="*.yaml" .

# Search for vector database configs
grep -r "vector" --include="*.py" src/

# Check dependencies
cat requirements.txt | grep -i "milvus\|weaviate"
```

**Changes needed:**
1. Replace `pymilvus` with `weaviate-client` in requirements
2. Update vector database client in code
3. Change connection endpoints
4. Update schema for Weaviate format

**Weaviate client example:**
```python
# OLD (Milvus):
from pymilvus import connections, Collection
connections.connect(host="localhost", port="19530")

# NEW (Weaviate):
import weaviate
client = weaviate.Client("http://localhost:30883")
```

---

### Phase 3: Deploy Infrastructure

**Namespace creation:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cyber-pi-intel
  labels:
    purpose: threat-intelligence
    system: cyber-pi
    tqakb-version: v4-golden
```

**Redis deployment:**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: cyber-pi-intel
spec:
  serviceName: redis
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7.4.1-alpine  # Stable version
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: cyber-pi-intel
spec:
  type: NodePort
  ports:
  - port: 6379
    targetPort: 6379
    nodePort: 30379
  selector:
    app: redis
```

**Weaviate deployment:**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: weaviate
  namespace: cyber-pi-intel
spec:
  serviceName: weaviate
  replicas: 1
  selector:
    matchLabels:
      app: weaviate
  template:
    metadata:
      labels:
        app: weaviate
    spec:
      containers:
      - name: weaviate
        image: semitechnologies/weaviate:1.24.1
        ports:
        - containerPort: 8080
        env:
        - name: QUERY_DEFAULTS_LIMIT
          value: "25"
        - name: AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED
          value: "true"
        - name: PERSISTENCE_DATA_PATH
          value: "/var/lib/weaviate"
        - name: DEFAULT_VECTORIZER_MODULE
          value: "none"  # We'll provide our own vectors
        - name: ENABLE_MODULES
          value: ""
        volumeMounts:
        - name: weaviate-data
          mountPath: /var/lib/weaviate
  volumeClaimTemplates:
  - metadata:
      name: weaviate-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: weaviate
  namespace: cyber-pi-intel
spec:
  type: NodePort
  ports:
  - port: 8080
    targetPort: 8080
    nodePort: 30883
  selector:
    app: weaviate
```

**Neo4j deployment:**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
  namespace: cyber-pi-intel
spec:
  serviceName: neo4j
  replicas: 1
  selector:
    matchLabels:
      app: neo4j
  template:
    metadata:
      labels:
        app: neo4j
    spec:
      containers:
      - name: neo4j
        image: neo4j:5.13.0
        ports:
        - containerPort: 7474  # HTTP
        - containerPort: 7687  # Bolt
        env:
        - name: NEO4J_AUTH
          value: "neo4j/cyber-pi-neo4j-2025"
        - name: NEO4J_dbms_memory_pagecache_size
          value: "2G"
        - name: NEO4J_dbms_memory_heap_max__size
          value: "4G"
        volumeMounts:
        - name: neo4j-data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: neo4j-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: neo4j
  namespace: cyber-pi-intel
spec:
  type: NodePort
  ports:
  - name: http
    port: 7474
    targetPort: 7474
    nodePort: 30474
  - name: bolt
    port: 7687
    targetPort: 7687
    nodePort: 30687
  selector:
    app: neo4j
```

---

### Phase 4: Deploy TQAKB Backend

**Backend deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tqakb-backend
  namespace: cyber-pi-intel
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tqakb-backend
  template:
    metadata:
      labels:
        app: tqakb-backend
    spec:
      containers:
      - name: backend
        image: python:3.11-slim
        command: ["/bin/bash", "-c"]
        args:
          - |
            cd /app
            pip install -r requirements.txt
            uvicorn main:app --host 0.0.0.0 --port 8000
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: WEAVIATE_URL
          value: "http://weaviate:8080"
        - name: NEO4J_URI
          value: "bolt://neo4j:7687"
        - name: NEO4J_USER
          value: "neo4j"
        - name: NEO4J_PASSWORD
          value: "cyber-pi-neo4j-2025"
        volumeMounts:
        - name: code
          mountPath: /app
      volumes:
      - name: code
        hostPath:
          path: /home/david/projects/cyber-pi-intel
          type: Directory
---
apiVersion: v1
kind: Service
metadata:
  name: tqakb-backend
  namespace: cyber-pi-intel
spec:
  type: NodePort
  ports:
  - port: 8000
    targetPort: 8000
    nodePort: 30800
  selector:
    app: tqakb-backend
```

---

## Integration with cyber-pi

### Connection Configuration

**cyber-pi configuration:**
```python
# config/tqakb_config.py

TQAKB_CONFIG = {
    'enabled': True,  # Can disable for fallback
    'redis_url': 'redis://localhost:30379',
    'weaviate_url': 'http://localhost:30883',
    'neo4j_uri': 'bolt://localhost:30687',
    'neo4j_auth': ('neo4j', 'cyber-pi-neo4j-2025'),
    'timeout': 5.0,  # Seconds
    'fallback_on_error': True,  # Use keyword filtering if TQAKB fails
}
```

**Client wrapper:**
```python
# src/intelligence/tqakb_client.py

import weaviate
import redis
from neo4j import GraphDatabase
from typing import List, Dict, Optional
import asyncio

class TQAKBClient:
    """Clean wrapper for TQAKB V4 Golden services"""
    
    def __init__(self, config: dict):
        self.config = config
        self._redis = None
        self._weaviate = None
        self._neo4j = None
        
    async def connect(self):
        """Establish connections to all services"""
        try:
            # Redis
            self._redis = redis.asyncio.Redis.from_url(
                self.config['redis_url'],
                decode_responses=True
            )
            await self._redis.ping()
            
            # Weaviate
            self._weaviate = weaviate.Client(self.config['weaviate_url'])
            self._weaviate.schema.get()  # Test connection
            
            # Neo4j
            self._neo4j = GraphDatabase.driver(
                self.config['neo4j_uri'],
                auth=self.config['neo4j_auth']
            )
            self._neo4j.verify_connectivity()
            
            return True
        except Exception as e:
            print(f"TQAKB connection failed: {e}")
            return False
    
    async def ingest_threat(self, threat: Dict) -> Optional[str]:
        """Ingest threat into tri-modal system"""
        try:
            # 1. Generate vector embedding (placeholder - will use sentence-transformers)
            # embedding = await self._vectorize(threat['content'])
            
            # 2. Store in Weaviate
            threat_id = self._weaviate.data_object.create(
                data_object=threat,
                class_name="Threat"
            )
            
            # 3. Cache in Redis
            await self._redis.setex(
                f"threat:{threat_id}",
                3600,  # 1 hour TTL
                str(threat)
            )
            
            # 4. Create graph relationships (if entities present)
            # await self._create_graph_relationships(threat_id, threat)
            
            return threat_id
            
        except Exception as e:
            print(f"Ingestion failed: {e}")
            return None
    
    async def semantic_search(self, query: str, limit: int = 50) -> List[Dict]:
        """Semantic search using Weaviate"""
        try:
            # Check Redis cache first
            cache_key = f"search:{query}:{limit}"
            cached = await self._redis.get(cache_key)
            if cached:
                return eval(cached)  # In production, use json.loads
            
            # Query Weaviate
            result = self._weaviate.query.get(
                "Threat",
                ["content", "title", "source", "published_date"]
            ).with_near_text({
                "concepts": [query]
            }).with_limit(limit).do()
            
            threats = result.get('data', {}).get('Get', {}).get('Threat', [])
            
            # Cache results
            await self._redis.setex(cache_key, 3600, str(threats))
            
            return threats
            
        except Exception as e:
            print(f"Search failed: {e}")
            return []
    
    async def close(self):
        """Clean shutdown"""
        if self._redis:
            await self._redis.close()
        if self._neo4j:
            self._neo4j.close()
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] V4 Golden code extracted at commit 4893b3b
- [ ] Milvus references replaced with Weaviate
- [ ] Dependencies updated (weaviate-client installed)
- [ ] Kubernetes YAML files created
- [ ] Namespace `cyber-pi-intel` ready

### Database Deployment

- [ ] Redis deployed and accessible (localhost:30379)
- [ ] Weaviate deployed and accessible (localhost:30883)
- [ ] Neo4j deployed and accessible (localhost:30687)
- [ ] All services have persistent storage
- [ ] Health checks passing

### Backend Deployment

- [ ] TQAKB backend code mounted
- [ ] Dependencies installed
- [ ] Environment variables configured
- [ ] Backend accessible (localhost:30800)
- [ ] API endpoints responding

### Integration

- [ ] cyber-pi can connect to Redis
- [ ] cyber-pi can connect to Weaviate
- [ ] cyber-pi can connect to Neo4j
- [ ] Test threat ingestion works
- [ ] Test semantic search works
- [ ] Fallback logic tested

---

## Success Criteria

### Performance Targets

- Redis queries: <5ms
- Weaviate searches: <100ms
- Neo4j graph queries: <200ms
- End-to-end threat processing: <1 second

### Quality Targets

- Deduplication: >85% duplicates merged
- Semantic relevance: >90% results relevant
- Entity extraction: >95% accuracy
- System uptime: >99.9%

### Integration Targets

- Fallback works when TQAKB unavailable
- No degradation of cyber-pi baseline functionality
- Reports show measurable improvement
- Cache hit rate: >90%

---

## Rollback Plan

If deployment fails:

1. Stop TQAKB services
2. Set `TQAKB_CONFIG['enabled'] = False` in cyber-pi
3. cyber-pi falls back to keyword filtering
4. Investigate issues without pressure
5. Fix and redeploy when ready

---

## Next Steps

1. Extract V4 Golden code (commit 4893b3b)
2. Replace Milvus with Weaviate in code
3. Deploy infrastructure (Redis, Weaviate, Neo4j)
4. Test each service individually
5. Deploy TQAKB backend
6. Test end-to-end
7. Integrate with cyber-pi
8. Measure and validate

---

**This is the CLEAN, PROPER deployment plan using V4 Golden + Weaviate.**

No old infrastructure reuse. Fresh deployment. Proven architecture.
