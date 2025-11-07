# Existing TQAKB Systems - What's Already Built

**Discovery:** You're absolutely right - this has already been built in previous TQAKB projects!

---

## What I Found

### 1. **Multi-Tier Cache System** (tqakb-research)
**File:** `/home/david/projects/tqakb-research/docs/archive/2025-10-04/scripts/multi_tier_cache.py`

**Architecture:**
```python
L1_hot:       50GB  - 300s TTL   - 95% hit target
L2_warm:      200GB - 3600s TTL  - 85% hit target
L3_cold:      250GB - 86400s TTL - 75% hit target
gpu_vectors:  50GB  - 7200s TTL  - 95% hit target
```

**Features:**
- ✅ Confidence-based tier assignment
- ✅ Automatic promotion on access
- ✅ Sorted sets for ranking
- ✅ Memory tracking per tier
- ✅ LRU eviction
- ✅ Prefetching (sequential, temporal, semantic)

---

### 2. **Confidence Decay Worker** (tqakb-data-processor)
**File:** `/home/david/projects/tqakb-data-processor/src/confidence_decay_worker.py`

**Key Features:**
```python
# CRITICAL PRINCIPLE: FACTS DO NOT DECAY
if is_fact:
    return initial_confidence  # No decay!

# Context decays exponentially
decayed = initial_confidence * ((1 - decay_rate) ** days_elapsed)

# Floor at 0.5 (don't decay below 50%)
return max(0.5, decayed)
```

**Tier Determination:**
```python
if confidence >= 0.9 and days_old < 7:
    return 'hot'
elif confidence >= 0.7 or days_old < 30:
    return 'warm'
else:
    return 'cold'
```

**Background Worker:**
- Runs every N hours
- Processes chunks in batches (100 at a time)
- Updates confidence scores
- Moves between tiers
- Tracks statistics:
  - Facts protected
  - Context decayed
  - Tier changes
  - Confidence updates

---

### 3. **Production System** (tqakb-enterprise)
**File:** `/home/david/projects/tqakb-enterprise/src/ui/enhanced_redis_native_ui_v4_auth.py`

**3-Tier Cache:**
```python
cache_tiers = {
    "L1_hot": CacheTier("L1 Hot", 64, 300, 0.95, db=1),
    "L2_warm": CacheTier("L2 Warm", 256, 3600, 0.85, db=2),
    "L3_cold": CacheTier("L3 Cold", 384, 86400, 0.75, db=3),
}
```

**Query Flow:**
```python
async def query(query_text):
    # 1. Check L1_hot
    if cached := await redis_db1.get(query_hash):
        return cached  # Sub-millisecond
    
    # 2. Check L2_warm
    if cached := await redis_db2.get(query_hash):
        await promote_to_l1(cached)  # Auto-promote!
        return cached
    
    # 3. Check L3_cold
    if cached := await redis_db3.get(query_hash):
        await promote_to_l2(cached)  # Auto-promote!
        await promote_to_l1(cached)
        return cached
    
    # 4. Query knowledge base
    result = await search_knowledge(query_text)
    await cache_in_appropriate_tier(result)
    return result
```

**Prometheus Metrics:**
- Query counter by tier
- Cache hits/misses per tier
- Query duration
- Active connections
- Redis keys per tier

---

## What This Means for Cascade

### ✅ **Already Solved Problems:**

1. **Multi-tier architecture** - Fully implemented
2. **Confidence decay** - Production-ready worker
3. **Auto-promotion** - Working in tqakb-enterprise
4. **Tier determination** - Clear rules based on confidence + age
5. **Background maintenance** - Decay worker runs continuously
6. **Metrics & monitoring** - Prometheus integration
7. **Facts vs Context** - Critical distinction (facts don't decay!)

### 🎯 **What to Reuse:**

#### From `multi_tier_cache.py`:
```python
# Tier determination logic
def _determine_tier(confidence, access_pattern, data_type):
    if confidence >= 0.9 and access_pattern == "frequent":
        return "L1_hot"
    if confidence >= 0.7 and data_type == "vector":
        return "gpu_vectors"
    if confidence >= 0.6 and access_pattern == "regular":
        return "L2_warm"
    return "L3_cold"

# Auto-promotion on access
async def intelligent_get(key):
    # Try L1
    if data := await l1.get(key):
        return data, "L1_hot"
    
    # Try L2 → promote to L1
    if data := await l2.get(key):
        await l1.set(key, data)  # Promote!
        return data, "L2_warm"
    
    # Try L3 → promote to L2 + L1
    if data := await l3.get(key):
        await l2.set(key, data)  # Promote!
        await l1.set(key, data)  # Promote!
        return data, "L3_cold"
    
    return None, None
```

#### From `confidence_decay_worker.py`:
```python
# Decay calculation
def calculate_decay(initial_confidence, decay_rate, days_elapsed, is_fact=False):
    # FACTS DO NOT DECAY
    if is_fact:
        return initial_confidence
    
    if days_elapsed <= 0:
        return initial_confidence
    
    decayed = initial_confidence * ((1 - decay_rate) ** days_elapsed)
    return max(0.5, decayed)  # Floor at 50%

# Batch processing
async def run_decay_cycle():
    batch_size = 100
    offset = 0
    
    while True:
        batch = await get_batch(offset, batch_size)
        if not batch:
            break
        
        for item in batch:
            new_confidence = calculate_decay(...)
            new_tier = determine_tier(new_confidence, age)
            await update(item, new_confidence, new_tier)
        
        offset += batch_size
```

#### From `enhanced_redis_native_ui_v4_auth.py`:
```python
# Separate Redis DBs per tier
cache_tiers = {
    "L1_hot": CacheTier(..., db=1),
    "L2_warm": CacheTier(..., db=2),
    "L3_cold": CacheTier(..., db=3),
}

# Prometheus metrics
query_counter = Counter('queries_total', ['cache_tier', 'user'])
cache_hits = Counter('cache_hits_total', ['tier'])
redis_keys = Gauge('redis_keys', ['tier'])
```

---

## Adaptation for Cascade Threats

### Key Differences:

| TQAKB | Cascade |
|-------|---------|
| Knowledge chunks | Threats |
| Query caching | Threat tracking |
| Confidence = relevance | Confidence = threat score |
| Facts don't decay | Validated threats don't decay |
| Context decays | Unvalidated threats decay |

### Cascade-Specific Adaptations:

```python
# 1. Threat is like a "fact" - validated threats don't decay
def calculate_threat_decay(threat, days_elapsed):
    # Validated threats = facts (don't decay)
    if threat.validated or threat.escalation_count >= 3:
        return threat.confidence
    
    # Unvalidated threats decay
    decay_rate = 0.02  # 2% per day
    decayed = threat.confidence * ((1 - decay_rate) ** days_elapsed)
    return max(0.3, decayed)  # Floor at 30%

# 2. Tier determination for threats
def determine_threat_tier(threat):
    confidence = calculate_threat_score(threat)
    age_days = (now - threat.created_at).days
    
    # Hot: Active investigation
    if confidence >= 0.9 and age_days < 1:
        return "Level_1_Working"
    
    # Warm: Recent validated
    if confidence >= 0.7 or age_days < 7:
        return "Level_2_ShortTerm"
    
    # Cold: Historical
    return "Level_3_LongTerm"

# 3. Auto-promotion on access (exactly like TQAKB)
async def get_threat(threat_id):
    # Try Level 1
    if threat := await level1.get(threat_id):
        return threat
    
    # Try Level 2 → promote to Level 1
    if threat := await level2.get(threat_id):
        await level1.add(threat)  # Promote!
        return threat
    
    # Try Level 3 → promote to Level 2 + Level 1
    if threat := await level3.get(threat_id):
        await level2.add(threat)  # Promote!
        await level1.add(threat)  # Promote!
        return threat
    
    return None
```

---

## Implementation Plan (Revised)

### Phase 1: Copy & Adapt (2-3 hours)

**Copy these files:**
1. `multi_tier_cache.py` → `cascade_memory_tiers.py`
2. `confidence_decay_worker.py` → `threat_decay_worker.py`
3. Cache tier logic from `enhanced_redis_native_ui_v4_auth.py`

**Adapt for threats:**
- Replace "chunks" with "threats"
- Replace "confidence" (relevance) with "threat_score"
- Replace "facts" with "validated_threats"
- Add threat-specific metadata (severity, analyst_count, etc.)

### Phase 2: Test (1 hour)

**Use existing test patterns:**
- Batch processing tests
- Decay calculation tests
- Tier transition tests
- Auto-promotion tests

### Phase 3: Integrate (1 hour)

**Connect to Level 1:**
- Level 1 uses existing code
- Add decay worker
- Add tier management
- Add auto-promotion

**Total: ~5 hours instead of 1 week!**

---

## Key Insights

### 1. **Facts Don't Decay** (Critical!)
```python
# From TQAKB: Facts are eternal truths
if is_fact:
    return initial_confidence  # NO DECAY

# For Cascade: Validated threats are "facts"
if threat.validated or threat.escalation_count >= 3:
    return threat.confidence  # NO DECAY
```

### 2. **Separate Redis DBs Per Tier**
```python
# TQAKB uses different Redis DBs
L1_hot: db=1
L2_warm: db=2
L3_cold: db=3

# Better than different key prefixes
# Easier to manage memory per tier
# Cleaner separation
```

### 3. **Background Worker Pattern**
```python
# Run continuously
async def run_forever():
    while True:
        await run_decay_cycle()
        await asyncio.sleep(3600)  # Every hour

# Or run once for testing
if args.once:
    run_decay_cycle()
    exit()
```

### 4. **Batch Processing**
```python
# Don't process one at a time
# Process in batches of 100
batch_size = 100
offset = 0

while True:
    batch = get_batch(offset, batch_size)
    if not batch:
        break
    
    process_batch(batch)
    offset += batch_size
```

---

## Recommendation

**Don't rebuild - ADAPT!**

1. **Copy** the working TQAKB code
2. **Adapt** for threats instead of knowledge chunks
3. **Test** with existing test patterns
4. **Deploy** in ~5 hours instead of 1 week

**Files to copy:**
- `/home/david/projects/tqakb-research/docs/archive/2025-10-04/scripts/multi_tier_cache.py`
- `/home/david/projects/tqakb-data-processor/src/confidence_decay_worker.py`
- Cache tier logic from `/home/david/projects/tqakb-enterprise/src/ui/enhanced_redis_native_ui_v4_auth.py`

**Changes needed:**
- Rename classes (ThreatMemory instead of Chunk)
- Adapt confidence calculation (threat scoring)
- Add threat-specific fields (severity, analyst_count, escalations)
- Keep the architecture identical

---

## Next Steps

**Want me to:**
1. Copy the TQAKB code and adapt it for Cascade?
2. Create a unified `cascade_memory_complete.py` based on proven patterns?
3. Set up the decay worker for threats?

**This is ~5 hours of work, not 1 week.**

The hard problems are already solved. We just need to adapt for threats.
