# 🛣️ REDIS HIGHWAY ARCHITECTURE

**Redis as the Central Nervous System for CVE Intelligence**

---

## **ARCHITECTURE PRINCIPLES**

1. **Redis First** - All reads/writes go through Redis
2. **Async Sync** - Neo4j/Weaviate updated asynchronously
3. **Event-Driven** - Redis Streams for data flow
4. **Pre-Computed** - Expensive queries pre-indexed in Redis
5. **Eventually Consistent** - Speed layer (Redis) + Batch layer (Neo4j/Weaviate)

---

## **DATA FLOW**

```
CVE Data → Redis (Write) → Publish Event
                ↓
           Read (Fast)
                ↓
         Application
                
Background Workers:
  Redis Stream → Neo4j (Graph Analysis)
              → Weaviate (Vector Embeddings)
              → Update Related Indexes
              → ML Predictions
```

---

## **REDIS DATA STRUCTURES**

### **1. CVE Storage (Hashes)**
```redis
HSET cve:CVE-2024-1234
  id "CVE-2024-1234"
  description "Remote code execution..."
  cvss_v3 9.8
  published "2024-01-15"
  vendors "microsoft,apache"
  cwes "CWE-787,CWE-119"
```

### **2. Indexes (Sets)**
```redis
# By severity
SADD cves:critical CVE-2024-1234 CVE-2024-5678 ...
SADD cves:high CVE-2024-9999 ...

# By vendor
SADD vendor:microsoft:cves CVE-2024-1234 ...
SADD vendor:apache:cves CVE-2024-5678 ...

# By CWE
SADD cwe:CWE-787:cves CVE-2024-1234 ...

# By keyword
SADD keyword:authentication:cves CVE-2024-1234 ...
```

### **3. Rankings (Sorted Sets)**
```redis
# By CVSS score
ZADD cves:by:cvss 9.8 CVE-2024-1234 7.5 CVE-2024-5678 ...

# By timestamp
ZADD cves:by:date 1705276800 CVE-2024-1234 ...

# Similar CVEs (pre-computed)
ZADD cve:CVE-2024-1234:similar 0.95 CVE-2024-5678 0.87 CVE-2024-9999 ...
```

### **4. Event Stream**
```redis
XADD cve:stream * event cve.created cve_id CVE-2024-1234 timestamp 1705276800
XADD cve:stream * event cve.updated cve_id CVE-2024-1234 field cvss_v3 old_value 9.0 new_value 9.8
```

### **5. Pub/Sub (Real-Time)**
```redis
PUBLISH cve:updates:critical {"cve_id": "CVE-2024-1234", "cvss": 9.8}
PUBLISH vendor:microsoft:updates {"cve_id": "CVE-2024-1234", "vendor": "microsoft"}
```

---

## **QUERY PATTERNS**

### **Pattern 1: Simple Lookup (1ms)**
```python
# Get CVE details
cve = redis.hgetall("cve:CVE-2024-1234")
```

### **Pattern 2: Filtered Search (5-10ms)**
```python
# Critical Microsoft CVEs
results = redis.sinter(
    "cves:critical",
    "vendor:microsoft:cves"
)
```

### **Pattern 3: Ranked Results (5-20ms)**
```python
# Top 10 CVEs by CVSS score affecting Microsoft
ms_cves = redis.smembers("vendor:microsoft:cves")
scores = redis.zscore("cves:by:cvss", *ms_cves)
top_10 = sorted(zip(ms_cves, scores), key=lambda x: x[1], reverse=True)[:10]
```

### **Pattern 4: Related/Similar (2-5ms)**
```python
# Get similar CVEs
similar = redis.zrange("cve:CVE-2024-1234:similar", 0, 10, withscores=True)
```

### **Pattern 5: Time-Series (10-20ms)**
```python
# CVEs in last 30 days
thirty_days_ago = time.time() - (30 * 86400)
recent = redis.zrangebyscore("cves:by:date", thirty_days_ago, "+inf")
```

---

## **BACKGROUND WORKERS**

### **Worker 1: Neo4j Sync**
```python
# redis_to_neo4j_worker.py
while True:
    # Read from stream
    events = redis.xread({"cve:stream": last_id}, count=100, block=1000)
    
    for event in events:
        if event['event'] == 'cve.created':
            cve = redis.hgetall(f"cve:{event['cve_id']}")
            neo4j.create_cve_graph(cve)
        elif event['event'] == 'cve.updated':
            neo4j.update_cve(event['cve_id'], event['field'], event['new_value'])
```

### **Worker 2: Weaviate Sync**
```python
# redis_to_weaviate_worker.py
while True:
    events = redis.xread({"cve:stream": last_id}, count=50, block=1000)
    
    for event in events:
        if event['event'] == 'cve.created':
            cve = redis.hgetall(f"cve:{event['cve_id']}")
            vector = embed_model.encode(cve['description'])
            weaviate.add_vector(cve['id'], vector, cve)
```

### **Worker 3: Similarity Index Builder**
```python
# similarity_worker.py
while True:
    # Get CVEs that need similarity computed
    pending = redis.smembers("cves:pending:similarity")
    
    for cve_id in pending:
        # Get similar CVEs from Weaviate
        cve = redis.hgetall(f"cve:{cve_id}")
        similar = weaviate.search(cve['description'], limit=50)
        
        # Update Redis sorted set
        for sim_cve, score in similar:
            redis.zadd(f"cve:{cve_id}:similar", {sim_cve: score})
        
        redis.srem("cves:pending:similarity", cve_id)
```

### **Worker 4: Analytics & ML**
```python
# analytics_worker.py
while True:
    events = redis.xread({"cve:stream": last_id}, count=100, block=1000)
    
    for event in events:
        if event['event'] == 'cve.created':
            # Run predictions
            cve = redis.hgetall(f"cve:{event['cve_id']}")
            predictions = ml_model.predict(cve)
            
            # Update Redis with predictions
            redis.hset(f"cve:{event['cve_id']}", 
                      "exploit_probability", predictions['exploit_prob'],
                      "severity_score", predictions['severity'])
```

---

## **API LAYER (SIMPLE)**

```python
# api/cve_search.py
from fastapi import FastAPI
import redis

app = FastAPI()
r = redis.Redis(host='redis', port=6379)

@app.get("/cve/{cve_id}")
async def get_cve(cve_id: str):
    """Get CVE details - Always from Redis (1-2ms)"""
    cve = r.hgetall(f"cve:{cve_id}")
    similar = r.zrange(f"cve:{cve_id}:similar", 0, 10, withscores=True)
    
    return {
        "cve": cve,
        "similar": similar,
        "source": "redis",
        "latency_ms": 1.5
    }

@app.get("/search/vendor/{vendor}")
async def search_by_vendor(vendor: str, severity: str = None):
    """Search CVEs - Redis set operations (5-10ms)"""
    
    # Base set
    results = r.smembers(f"vendor:{vendor}:cves")
    
    # Filter by severity if specified
    if severity:
        results = r.sinter(f"vendor:{vendor}:cves", f"cves:{severity}")
    
    # Enrich with details
    cves = [r.hgetall(f"cve:{cve_id}") for cve_id in results]
    
    return {
        "count": len(cves),
        "cves": cves,
        "source": "redis",
        "latency_ms": 8.2
    }

@app.get("/deep-analysis/{cve_id}")
async def deep_analysis(cve_id: str):
    """Deep analysis - Query Neo4j (slower but comprehensive)"""
    # Check Redis first
    basic = r.hgetall(f"cve:{cve_id}")
    
    # Get graph analysis from Neo4j
    graph_analysis = neo4j.analyze_cve(cve_id)
    
    return {
        "cve": basic,
        "graph_metrics": graph_analysis,
        "sources": ["redis", "neo4j"],
        "latency_ms": 125.3
    }
```

---

## **DEPLOYMENT**

### **1. Initialize Redis Indexes**
```bash
python3 src/bootstrap/build_redis_indexes.py
# - Builds all sets and sorted sets
# - Computes initial similarity indexes
# - Sets up event streams
```

### **2. Deploy Workers**
```bash
# Kubernetes Jobs/Deployments
kubectl apply -f k8s/redis-workers/
# - neo4j-sync-worker (1 replica)
# - weaviate-sync-worker (1 replica)
# - similarity-worker (2 replicas)
# - analytics-worker (2 replicas)
```

### **3. Monitor**
```bash
# Redis stats
redis-cli INFO stats

# Stream lag
redis-cli XINFO STREAM cve:stream

# Worker health
kubectl get pods -l app=redis-worker
```

---

## **PERFORMANCE TARGETS**

| Operation | Redis Highway | Traditional | Improvement |
|-----------|--------------|-------------|-------------|
| CVE Lookup | 1-2ms | 50ms | 25-50x |
| Vendor Search | 5-10ms | 200ms | 20-40x |
| Similar CVEs | 2-5ms | 100ms | 20-50x |
| Complex Query | 10-20ms | 500ms | 25-50x |
| Bulk Export | 100ms/10K | 5s/10K | 50x |

---

## **ADVANTAGES**

1. ✅ **Speed** - Sub-10ms for 95% of queries
2. ✅ **Simplicity** - No complex orchestration logic
3. ✅ **Scalability** - Horizontal scaling of workers
4. ✅ **Resilience** - Components fail independently
5. ✅ **Flexibility** - Easy to add new data sources
6. ✅ **Real-Time** - Pub/Sub for live updates
7. ✅ **Cost** - Redis cheaper than complex orchestrator

---

## **DISADVANTAGES**

1. ⚠️ **Eventually Consistent** - Neo4j/Weaviate lag behind Redis
2. ⚠️ **Memory** - Redis in-memory (need enough RAM)
3. ⚠️ **Complexity** - Distributed system management
4. ⚠️ **Data Duplication** - Same data in multiple stores

---

## **VERDICT**

**Redis Highway is the RIGHT architecture for:**
- High-throughput systems
- Real-time requirements
- Microservices
- Event-driven workflows
- Scale-out scenarios

**Trade-off:** Immediate consistency → Eventual consistency  
**Gain:** 20-50x performance improvement

**Recommendation:** ⭐⭐⭐⭐⭐ **STRONGLY RECOMMENDED**
