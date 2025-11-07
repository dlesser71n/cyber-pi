# TQAKB-v3.3 Integration Specification - NO SHORTCUTS

**Date:** October 31, 2025  
**Principle:** Solve problems properly, don't work around them  
**Approach:** Thorough, documented, production-quality

---

## Pre-Integration Assessment

### Phase 0: COMPLETE SYSTEM AUDIT (Do First)

**Why this matters:** We need to know EXACTLY what exists, what doesn't, and what needs to be fixed BEFORE we start integrating.

#### 1. TQAKB Infrastructure Inventory

**Questions to answer:**
- [ ] Is TQAKB-v3.3 actually deployed on this system?
- [ ] Which namespace? (tqakb, tqakb-v3, qakb-system, other?)
- [ ] Are all three databases running? (Redis, Weaviate, Neo4j)
- [ ] What are the actual ports and endpoints?
- [ ] Are there authentication credentials we need?
- [ ] Is the GPU accessible to TQAKB pods?
- [ ] What's the actual storage usage vs capacity?

**How to verify:**
```bash
# 1. List all namespaces
microk8s kubectl get namespaces

# 2. Check each namespace for TQAKB-related pods
microk8s kubectl get pods --all-namespaces | grep -i tqakb
microk8s kubectl get pods --all-namespaces | grep -i qakb

# 3. Check for Redis
microk8s kubectl get pods --all-namespaces | grep redis

# 4. Check for Weaviate
microk8s kubectl get pods --all-namespaces | grep weaviate

# 5. Check for Neo4j
microk8s kubectl get pods --all-namespaces | grep neo4j

# 6. Check services and their endpoints
microk8s kubectl get services --all-namespaces

# 7. Check persistent volume claims (data storage)
microk8s kubectl get pvc --all-namespaces

# 8. Check GPU availability
nvidia-smi
```

**Success Criteria:**
- Complete inventory of what exists
- Documentation of all endpoints and credentials
- Understanding of any gaps or issues

---

#### 2. cyber-pi Current State Assessment

**Questions to answer:**
- [ ] What version of Python is cyber-pi using?
- [ ] What dependencies are currently installed?
- [ ] Where is the data collection happening?
- [ ] Where is the filtering logic?
- [ ] Where is the enrichment happening?
- [ ] What's the current data flow architecture?
- [ ] Are there any existing database connections?

**How to verify:**
```bash
# 1. Check Python version
python3 --version

# 2. Check installed packages
cd /home/david/projects/cyber-pi
uv pip list | grep -E "(redis|neo4j|weaviate|torch|transformers)"

# 3. Review code structure
find src/ -name "*.py" | head -20
tree src/ -L 2

# 4. Check for existing database configs
grep -r "redis" src/ config/ 2>/dev/null | head -10
grep -r "neo4j" src/ config/ 2>/dev/null | head -10
grep -r "weaviate" src/ config/ 2>/dev/null | head -10
```

**Success Criteria:**
- Complete understanding of cyber-pi architecture
- Identification of integration points
- List of dependencies that need to be added

---

#### 3. Integration Dependencies Audit

**Required Python packages for TQAKB integration:**

**Vector/Embedding Libraries:**
- [ ] `torch` (PyTorch for GPU operations)
- [ ] `sentence-transformers` (for embeddings)
- [ ] `transformers` (HuggingFace models)

**Database Clients:**
- [ ] `redis` (async Redis client)
- [ ] `weaviate-client` (Weaviate Python SDK)
- [ ] `neo4j` (Neo4j Python driver)

**Supporting Libraries:**
- [ ] `numpy` (vector operations)
- [ ] `asyncio` (async operations)
- [ ] `pydantic` (data validation)

**Check what's missing:**
```bash
cd /home/david/projects/cyber-pi

# Create dependency check script
cat > check_dependencies.py << 'EOF'
import sys

required = {
    'torch': 'PyTorch (GPU operations)',
    'sentence_transformers': 'Sentence embeddings',
    'transformers': 'HuggingFace transformers',
    'redis': 'Redis client',
    'weaviate': 'Weaviate client',
    'neo4j': 'Neo4j driver',
    'numpy': 'Vector operations',
    'asyncio': 'Async operations (stdlib)',
    'pydantic': 'Data validation'
}

missing = []
installed = []

for package, description in required.items():
    try:
        __import__(package)
        installed.append(f"✅ {package}: {description}")
    except ImportError:
        missing.append(f"❌ {package}: {description}")

print("\n=== INSTALLED ===")
for item in installed:
    print(item)

print("\n=== MISSING ===")
for item in missing:
    print(item)

print(f"\nTotal: {len(installed)}/{len(required)} packages installed")
sys.exit(0 if not missing else 1)
EOF

python3 check_dependencies.py
```

**Success Criteria:**
- Know exactly what needs to be installed
- No guessing about dependencies

---

#### 4. Network Connectivity Testing

**Test each database endpoint:**

**Redis Test:**
```python
# test_redis.py
import redis
import asyncio

async def test_redis():
    try:
        # Test Docker Redis (localhost:6379)
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis (6379): Connected")
        
        # Test MicroK8s Redis if exists (localhost:6380 or 30379)
        try:
            r2 = redis.Redis(host='localhost', port=30379, decode_responses=True)
            r2.ping()
            print("✅ Redis (30379): Connected")
        except:
            print("⚠️  Redis (30379): Not available")
            
    except Exception as e:
        print(f"❌ Redis Error: {e}")
        return False
    return True

if __name__ == "__main__":
    asyncio.run(test_redis())
```

**Weaviate Test:**
```python
# test_weaviate.py
import weaviate

def test_weaviate():
    try:
        client = weaviate.Client("http://localhost:30883")
        schema = client.schema.get()
        print(f"✅ Weaviate: Connected (collections: {len(schema.get('classes', []))})")
        return True
    except Exception as e:
        print(f"❌ Weaviate Error: {e}")
        return False

if __name__ == "__main__":
    test_weaviate()
```

**Neo4j Test:**
```python
# test_neo4j.py
from neo4j import GraphDatabase

def test_neo4j():
    try:
        # Try common credentials
        credentials = [
            ("neo4j", "tqakb-neo4j-2024"),
            ("neo4j", "dev-neo4j-password"),
            ("neo4j", "neo4j")
        ]
        
        for user, password in credentials:
            try:
                driver = GraphDatabase.driver(
                    "bolt://localhost:30687",
                    auth=(user, password)
                )
                with driver.session() as session:
                    result = session.run("RETURN 1 as num")
                    print(f"✅ Neo4j: Connected (user: {user})")
                    driver.close()
                    return True
            except:
                continue
                
        print("❌ Neo4j: Could not connect with any known credentials")
        return False
        
    except Exception as e:
        print(f"❌ Neo4j Error: {e}")
        return False

if __name__ == "__main__":
    test_neo4j()
```

**Success Criteria:**
- All three databases accessible
- Credentials documented
- Any connectivity issues identified and FIXED

---

## Integration Architecture (Proper Design)

### Design Principles

**1. Separation of Concerns**
- cyber-pi: Data collection and delivery
- TQAKB: Intelligence processing and storage
- Clear interfaces between them

**2. No Tight Coupling**
- cyber-pi should work WITHOUT TQAKB (degraded mode)
- TQAKB should work WITHOUT cyber-pi (standalone)
- Integration is an enhancement, not a dependency

**3. Fail Gracefully**
- If TQAKB is down, fall back to keyword filtering
- If Redis is slow, don't block the entire system
- Log all errors properly, don't hide them

**4. Production Quality**
- Proper error handling (no bare `except:` statements)
- Logging at appropriate levels
- Metrics and monitoring
- Health checks for all components

---

### Integration Points (Specific)

**Point 1: Data Ingestion**

**Current (cyber-pi):**
```python
# src/collection/unified_collector.py
def collect_all():
    rss_items = collect_rss()
    social_items = collect_social()
    return rss_items + social_items
```

**Enhanced (with TQAKB):**
```python
# src/collection/intelligent_collector.py
async def collect_and_ingest():
    # Collect as before
    items = collect_all()
    
    # NEW: Send to TQAKB for processing
    if tqakb_available():
        for item in items:
            try:
                threat_id = await tqakb.ingest_threat(item)
                item['tqakb_id'] = threat_id
            except TQAKBError as e:
                logger.error(f"TQAKB ingestion failed: {e}")
                # Continue without TQAKB enhancement
                pass
    
    return items
```

**PROBLEM TO SOLVE:** What if TQAKB is slow? Don't block collection.
**SOLUTION:** Async ingestion with timeout, queue for retry

---

**Point 2: Threat Filtering**

**Current (cyber-pi):**
```python
# src/filtering/client_filter.py
def filter_for_industry(items, industry):
    keywords = load_keywords(industry)
    return [item for item in items if matches_keywords(item, keywords)]
```

**Enhanced (with TQAKB):**
```python
# src/filtering/intelligent_filter.py
async def filter_for_industry(items, industry):
    # Try TQAKB semantic search first
    if tqakb_available():
        try:
            semantic_results = await tqakb.semantic_search(
                query=f"threats targeting {industry}",
                items=items,
                threshold=0.7
            )
            # Merge with keyword results for safety
            keyword_results = keyword_filter(items, industry)
            return merge_results(semantic_results, keyword_results)
        except TQAKBError as e:
            logger.warning(f"TQAKB search failed, falling back: {e}")
    
    # Fallback to keyword filtering
    return keyword_filter(items, industry)
```

**PROBLEM TO SOLVE:** What if semantic search returns irrelevant results?
**SOLUTION:** Hybrid approach - combine semantic + keyword, validate results

---

**Point 3: Enrichment Enhancement**

**Current (cyber-pi):**
```python
# src/intelligence/report_enrichment.py
def get_enrichment(industry):
    # Load from YAML
    intel_db = load_yaml('industry_intelligence_db.yaml')
    return intel_db.get(industry, {})
```

**Enhanced (with TQAKB):**
```python
# src/intelligence/intelligent_enrichment.py
async def get_enrichment(industry, threats):
    # Get base enrichment from YAML
    base = load_yaml_enrichment(industry)
    
    # Enhance with TQAKB graph intelligence
    if tqakb_available() and threats:
        try:
            # Get threat actor intelligence
            actors = await tqakb.get_threat_actors(threats)
            base['threat_actors'] = enrich_actors(base.get('threat_actors'), actors)
            
            # Get attack chains
            chains = await tqakb.get_attack_chains(threats)
            base['attack_chains'] = chains
            
            # Get historical trends
            trends = await tqakb.get_trends(industry, days=90)
            base['trends'] = trends
            
        except TQAKBError as e:
            logger.warning(f"TQAKB enrichment failed: {e}")
            # Continue with base enrichment only
    
    return base
```

**PROBLEM TO SOLVE:** How to merge YAML data with TQAKB data without conflicts?
**SOLUTION:** Clear precedence rules, validate data quality, log discrepancies

---

## Implementation Phases (Proper)

### Phase 0: Pre-Integration (COMPLETE THIS FIRST)

**Do NOT start Phase 1 until ALL of Phase 0 is complete**

**Tasks:**
1. [ ] Complete infrastructure audit (know what exists)
2. [ ] Test all database connectivity (fix any issues)
3. [ ] Install missing dependencies (document versions)
4. [ ] Create integration test suite (validate assumptions)
5. [ ] Document current cyber-pi data flow (understand baseline)
6. [ ] Create rollback plan (if integration fails)

**Deliverables:**
- Infrastructure inventory document
- Connectivity test results
- Dependency installation log
- Integration test suite (passing)
- Data flow diagrams (before/after)
- Rollback procedure

**Exit Criteria:**
- All databases accessible ✅
- All dependencies installed ✅
- All tests passing ✅
- Team understands architecture ✅

---

### Phase 1: Minimal Integration (Prove It Works)

**Goal:** Get ONE threat flowing through TQAKB pipeline end-to-end

**Steps:**
1. Create TQAKB client wrapper (proper error handling)
2. Ingest 1 threat into Weaviate (verify storage)
3. Query that threat back (verify retrieval)
4. Extract entities from threat (verify NLP works)
5. Create graph relationships (verify Neo4j works)
6. Test semantic search (verify vectors work)
7. Measure performance (baseline for optimization)

**Success Criteria:**
- 1 threat flows through entire pipeline
- All data persists correctly
- All queries return expected results
- Performance is acceptable (<1 sec per threat)

**If ANYTHING fails:**
- STOP and FIX the root cause
- Don't proceed until it's working properly
- Document the issue and solution

---

### Phase 2: Batch Integration (Scale Testing)

**Goal:** Process 100 threats, find and fix scaling issues

**Steps:**
1. Ingest 100 threats from cyber-pi
2. Monitor resource usage (CPU, memory, GPU)
3. Check for errors or warnings
4. Verify data quality (no corruption)
5. Test deduplication (are duplicates merged correctly?)
6. Measure performance (is it still acceptable?)
7. Test concurrent access (what if 2 requests at once?)

**Things That Will Probably Break:**
- Memory issues (vectors are large)
- GPU out of memory (batch size too big)
- Neo4j connection pooling (too many connections)
- Redis cache eviction (not enough space)

**Fix Each Problem:**
- Memory: Implement batching, stream processing
- GPU: Reduce batch size, add queuing
- Neo4j: Connection pooling with limits
- Redis: LRU eviction policy, larger cache

---

### Phase 3: Integration with cyber-pi Pipeline

**Goal:** cyber-pi uses TQAKB automatically, falls back gracefully

**Steps:**
1. Modify collection to call TQAKB ingestion
2. Modify filtering to use semantic search
3. Modify enrichment to use graph data
4. Add health checks (is TQAKB available?)
5. Add fallback logic (what if TQAKB is down?)
6. Add metrics (how often is TQAKB used?)
7. Add logging (debug integration issues)

**Edge Cases to Handle:**
- TQAKB is down → Fall back to keywords
- TQAKB is slow (>5 sec) → Timeout and fallback
- TQAKB returns empty results → Use keywords
- TQAKB returns errors → Log and continue
- Database is full → Alert and stop ingestion

---

### Phase 4: Production Hardening

**Goal:** Make it bulletproof for production use

**Tasks:**
1. Add comprehensive error handling
2. Implement retry logic with exponential backoff
3. Add circuit breakers (stop hitting failing service)
4. Implement rate limiting (don't overwhelm TQAKB)
5. Add monitoring and alerting
6. Create health check endpoints
7. Write operational runbook
8. Load testing (can it handle 1000 threats/hour?)
9. Failure testing (what if Neo4j crashes?)
10. Recovery testing (what if we need to rebuild?)

**Production Checklist:**
- [ ] Error handling: Comprehensive
- [ ] Retry logic: Exponential backoff
- [ ] Circuit breakers: Implemented
- [ ] Rate limiting: Configured
- [ ] Monitoring: Prometheus metrics
- [ ] Alerting: Alert rules defined
- [ ] Health checks: All components
- [ ] Documentation: Complete
- [ ] Runbook: Operational procedures
- [ ] Load tested: 10x expected load
- [ ] Failure tested: All failure modes
- [ ] Recovery tested: Can rebuild from zero

---

## Quality Gates (Must Pass)

### Gate 1: Infrastructure Ready
- All databases accessible
- All credentials documented
- All dependencies installed
- All tests passing

**Do NOT proceed to integration until this passes**

### Gate 2: Minimal Integration Works
- 1 threat processes successfully
- Data persists correctly
- Queries return correct results
- Performance acceptable

**Do NOT proceed to batch until this passes**

### Gate 3: Batch Processing Works
- 100 threats process without errors
- No data corruption
- Resource usage acceptable
- Performance scales linearly

**Do NOT proceed to pipeline integration until this passes**

### Gate 4: Pipeline Integration Works
- cyber-pi uses TQAKB successfully
- Fallback works when TQAKB unavailable
- No degradation of existing functionality
- Metrics show improvement

**Do NOT deploy to production until this passes**

### Gate 5: Production Ready
- All error handling in place
- All monitoring in place
- All documentation complete
- Load tested and passing
- Failure modes tested
- Team trained on operations

**Do NOT deploy until ALL gates pass**

---

## Problem-Solving Approach

### When Something Breaks (It Will)

**1. STOP**
- Don't try to work around it
- Don't ignore it
- Don't hope it goes away

**2. REPRODUCE**
- Can you make it happen again?
- What are the exact steps?
- What's the error message?

**3. UNDERSTAND**
- What's the root cause?
- Why is this happening?
- What assumptions were wrong?

**4. FIX PROPERLY**
- Fix the root cause, not the symptom
- Don't add workarounds or hacks
- Write a test to prevent regression

**5. DOCUMENT**
- What was the problem?
- What was the solution?
- How can we prevent it in the future?

---

## Rollback Plan (If Integration Fails)

### Conditions for Rollback

Rollback if:
- Integration introduces bugs in cyber-pi
- Performance degrades significantly
- Data quality decreases
- Can't meet deadlines with integration
- Team can't maintain integrated system

### Rollback Procedure

**1. Stop TQAKB Integration**
```bash
# Disable TQAKB calls in code
export USE_TQAKB=false

# Restart services
systemctl restart cyber-pi
```

**2. Revert Code Changes**
```bash
git revert <integration-commits>
git push
```

**3. Verify Baseline Functionality**
- Run all cyber-pi tests
- Generate sample reports
- Verify quality is same as before

**4. Document What Went Wrong**
- What failed?
- Why did it fail?
- What would we do differently?

---

## Success Metrics (How We Know It's Working)

### Technical Metrics

**Performance:**
- Threat ingestion: <500ms per threat
- Semantic search: <100ms
- Graph query: <200ms
- End-to-end: <1 second per threat

**Quality:**
- Deduplication rate: >85% duplicates merged
- Semantic relevance: >90% relevant results
- Entity extraction accuracy: >95%
- Graph relationship accuracy: >90%

**Reliability:**
- Uptime: >99.9%
- Error rate: <0.1%
- Fallback rate: <5% (TQAKB should work 95%+ of time)

### Business Metrics

**Value Delivered:**
- Report quality: Measurably better (user survey)
- Threat coverage: +30-50% more relevant threats
- False positives: -50% reduction
- Time to insight: -80% (5ms vs 30s)

**Market Impact:**
- Pricing power: Can charge 3-5x more
- Competitive position: Unique capabilities
- Customer satisfaction: NPS score +20 points

---

## Next Steps

**IMMEDIATE:**
1. Run Phase 0 assessment (complete audit)
2. Fix any infrastructure issues found
3. Install missing dependencies
4. Create test suite

**THEN:**
5. Start Phase 1 (minimal integration)
6. Don't skip steps
7. Fix problems properly
8. Document everything

---

**NO SHORTCUTS. SOLVE PROBLEMS. BUILD IT RIGHT.**

---

**End of Specification**
