# Memory System Completion Plan

**Decision:** Finish all 3 levels before integration  
**Timeline:** ~1 week focused work  
**Goal:** Production-ready 3-level memory system

---

## Phase 1: Complete Level 1 (Day 1)

### Add Critical Features

#### 1. Threat Scoring Algorithm
```python
def calculate_threat_score(threat) -> float:
    """Multi-factor threat scoring (0.0 - 1.0)"""
    
    # Severity weight
    severity_weight = {
        'CRITICAL': 1.0,
        'HIGH': 0.7,
        'MEDIUM': 0.4,
        'LOW': 0.1
    }[threat.severity]
    
    # Engagement score
    engagement = min(1.0, threat.interaction_count / 10)
    
    # Recency score (exponential decay)
    age_minutes = (now - threat.last_activity).total_seconds() / 60
    recency = math.exp(-age_minutes / 30)  # 30min half-life
    
    # Metadata intelligence
    metadata_score = extract_metadata_signals(threat.metadata)
    
    # Composite
    score = (
        severity_weight * 0.3 +
        engagement * 0.3 +
        recency * 0.2 +
        metadata_score * 0.2
    )
    
    return score
```

#### 2. Action Type Tracking
```python
@dataclass
class WorkingMemory:
    # ... existing fields ...
    escalation_count: int = 0
    view_count: int = 0
    dismiss_count: int = 0
    analyst_actions: Dict[str, str] = field(default_factory=dict)
```

#### 3. Performance Metrics
```python
@dataclass
class Level1Metrics:
    total_adds: int = 0
    total_gets: int = 0
    avg_add_time_ms: float = 0.0
    avg_get_time_ms: float = 0.0
    memory_used_mb: float = 0.0
    peak_active_threats: int = 0
```

#### 4. Promotion Criteria
```python
async def should_promote_to_level2(threat) -> bool:
    """Decide if threat warrants Level 2"""
    
    score = calculate_threat_score(threat)
    
    # Multiple validation signals
    has_validation = threat.analyst_count >= 2
    has_engagement = threat.interaction_count >= 3
    has_escalations = threat.escalation_count >= 2
    is_severe = threat.severity in ['CRITICAL', 'HIGH']
    
    return (
        score >= 0.7 and
        has_validation and
        (has_escalations or is_severe)
    )
```

**Time:** 2-3 hours  
**Test:** Update test_level1_simple.py with new features

---

## Phase 2: Build Level 2 - Short-Term Memory (Days 2-3)

### Architecture
```python
class Level2ShortTerm:
    """
    Short-term memory (7 days)
    Recently validated threats
    """
    
    # Redis keys:
    # - cascade:short:{memory_id} - Hash
    # - cascade:short:ranked - Sorted Set (by score)
    # - cascade:short:industry:{industry} - Set
    # - cascade:short:type:{type} - Set
```

### Features from TQAKB

#### 1. Confidence-Based Admission
```python
async def promote_from_level1(threat_id: str):
    """Promote from Level 1 to Level 2"""
    
    # Get from Level 1
    threat = await level1.get_threat(threat_id)
    
    # Check promotion criteria
    if not await level1.should_promote_to_level2(threat):
        return False
    
    # Calculate confidence
    confidence = calculate_threat_score(threat)
    
    # Create Level 2 memory
    memory = ShortTermMemory(
        id=f"short_{uuid.uuid4().hex[:10]}",
        threat_id=threat.threat_id,
        content=threat.content,
        confidence=confidence,
        severity=threat.severity,
        industry=threat.metadata.get('industry', 'unknown'),
        formed_at=datetime.utcnow().isoformat(),
        last_updated=datetime.utcnow().isoformat(),
        evidence_count=threat.interaction_count,
        analyst_interactions=threat.analyst_count,
        memory_type=determine_memory_type(threat),
        score=calculate_ranking_score(threat),
        metadata=threat.metadata
    )
    
    # Store in Level 2
    await level2.add(memory)
    
    # Remove from Level 1 (promoted!)
    await level1.remove_threat(threat_id)
    
    return True
```

#### 2. Sorted Sets for Ranking
```python
async def add(self, memory: ShortTermMemory):
    """Add to Level 2 with ranking"""
    
    # Store hash
    key = f"cascade:short:{memory.id}"
    await redis.hset(key, mapping=memory.to_dict())
    await redis.expire(key, self.ttl)  # 7 days
    
    # Add to ranked sorted set
    await redis.zadd("cascade:short:ranked", {
        memory.id: memory.score
    })
    
    # Add to industry index
    await redis.sadd(
        f"cascade:short:industry:{memory.industry}",
        memory.id
    )
```

#### 3. Automatic Promotion on Access
```python
async def get(self, memory_id: str) -> Optional[ShortTermMemory]:
    """Get from Level 2 with auto-promotion to Level 1"""
    
    memory = await self._get_from_redis(memory_id)
    
    if memory:
        # Promote to Level 1 for fast access
        await level1.add_threat(
            threat_id=memory.threat_id,
            content=memory.content,
            severity=memory.severity,
            metadata=memory.metadata
        )
    
    return memory
```

#### 4. Top Threats Query
```python
async def get_top_threats(self, limit: int = 10) -> List[ShortTermMemory]:
    """Get top-ranked threats"""
    
    # Get top IDs from sorted set
    memory_ids = await redis.zrevrange(
        "cascade:short:ranked", 0, limit - 1
    )
    
    # Fetch full memories
    memories = []
    for mem_id in memory_ids:
        memory = await self.get(mem_id)
        if memory:
            memories.append(memory)
    
    return memories
```

**Time:** 1 day implementation + 0.5 day testing  
**Test:** Create test_level2_memory.py

---

## Phase 3: Build Level 3 - Long-Term Memory (Days 4-5)

### Architecture
```python
class Level3LongTerm:
    """
    Long-term memory (90+ days)
    Permanent knowledge base
    """
    
    # Redis keys:
    # - cascade:long:{memory_id} - Hash
    # - cascade:long:all - Set
    # - cascade:long:industry:{industry} - Set
    # - cascade:long:type:{type} - Set
    # - cascade:long:export:pending - Set (Neo4j queue)
```

### Features from TQAKB

#### 1. Confidence Decay
```python
async def apply_confidence_decay(
    self,
    memory_id: str,
    decay_rate: float = 0.001
) -> float:
    """Apply exponential decay to confidence"""
    
    memory = await self.get(memory_id)
    
    # Calculate age
    age_days = (datetime.utcnow() - memory.formed_at).days
    
    # Exponential decay
    decay_factor = (1 - decay_rate) ** age_days
    new_confidence = memory.confidence * decay_factor
    
    # Update
    memory.confidence = new_confidence
    memory.last_updated = datetime.utcnow().isoformat()
    await self.update(memory)
    
    # Auto-demote if too low
    if new_confidence < 0.3:
        await self.archive_or_delete(memory_id)
    
    return new_confidence

async def batch_decay_update(self):
    """Apply decay to all memories (run daily)"""
    
    all_ids = await redis.smembers("cascade:long:all")
    
    for memory_id in all_ids:
        await self.apply_confidence_decay(memory_id)
```

#### 2. Consolidation Tracking
```python
@dataclass
class LongTermMemory:
    # ... existing fields ...
    consolidation_count: int = 1  # How many times reinforced
    
async def consolidate(self, memory_id: str):
    """Reinforce memory (seen again)"""
    
    await redis.hincrby(
        f"cascade:long:{memory_id}",
        "consolidation_count",
        1
    )
    
    # Refresh TTL (important memories stay longer)
    await redis.expire(
        f"cascade:long:{memory_id}",
        self.ttl
    )
```

#### 3. Neo4j Export
```python
async def export_to_neo4j(self, memory_id: str):
    """Export memory to Neo4j for graph queries"""
    
    memory = await self.get(memory_id)
    
    # Create node in Neo4j
    query = """
    CREATE (t:Threat {
        id: $id,
        threat_id: $threat_id,
        content: $content,
        confidence: $confidence,
        severity: $severity,
        industry: $industry,
        formed_at: $formed_at,
        memory_type: $memory_type
    })
    """
    
    await neo4j.run(query, **memory.to_dict())
    
    # Mark as exported
    memory.neo4j_exported = True
    await self.update(memory)
    
    # Remove from export queue
    await redis.srem("cascade:long:export:pending", memory_id)

async def background_export_worker(self):
    """Background worker for Neo4j export"""
    
    while True:
        # Get pending exports
        pending = await redis.smembers("cascade:long:export:pending")
        
        for memory_id in pending:
            try:
                await self.export_to_neo4j(memory_id)
            except Exception as e:
                print(f"Export failed for {memory_id}: {e}")
        
        await asyncio.sleep(60)  # Check every minute
```

#### 4. Temporal Validity
```python
@dataclass
class LongTermMemory:
    # ... existing fields ...
    valid_from: str  # ISO timestamp
    valid_to: Optional[str] = None  # ISO timestamp or None
    
async def get_valid_at(
    self,
    memory_id: str,
    timestamp: datetime
) -> Optional[LongTermMemory]:
    """Get memory if valid at timestamp"""
    
    memory = await self.get(memory_id)
    
    if not memory:
        return None
    
    valid_from = datetime.fromisoformat(memory.valid_from)
    valid_to = datetime.fromisoformat(memory.valid_to) if memory.valid_to else datetime.max
    
    if valid_from <= timestamp <= valid_to:
        return memory
    
    return None
```

**Time:** 1 day implementation + 0.5 day testing  
**Test:** Create test_level3_memory.py

---

## Phase 4: Integration & Multi-Level Operations (Day 6)

### Unified Memory Interface
```python
class CascadeMemory:
    """
    Unified interface for all 3 levels
    Handles promotion/demotion automatically
    """
    
    def __init__(self):
        self.level1 = Level1Memory()
        self.level2 = Level2ShortTerm()
        self.level3 = Level3LongTerm()
    
    async def intelligent_get(self, threat_id: str) -> Optional[Threat]:
        """Get threat from any level (with auto-promotion)"""
        
        # Try Level 1 (fastest)
        if threat := await self.level1.get_threat(threat_id):
            return threat
        
        # Try Level 2
        if memory := await self.level2.get_by_threat_id(threat_id):
            # Promote to Level 1
            await self.level1.add_threat(
                threat_id=memory.threat_id,
                content=memory.content,
                severity=memory.severity,
                metadata=memory.metadata
            )
            return memory
        
        # Try Level 3
        if memory := await self.level3.get_by_threat_id(threat_id):
            # Promote to Level 2 and Level 1
            await self.level2.promote_from_level3(memory)
            await self.level1.add_from_level2(memory)
            return memory
        
        return None
    
    async def add_threat(self, threat_data: Dict):
        """Add new threat (always starts at Level 1)"""
        
        await self.level1.add_threat(**threat_data)
    
    async def background_maintenance(self):
        """Run maintenance tasks"""
        
        while True:
            # Promote eligible Level 1 → Level 2
            await self._promote_level1_to_level2()
            
            # Promote eligible Level 2 → Level 3
            await self._promote_level2_to_level3()
            
            # Apply decay to Level 3
            await self.level3.batch_decay_update()
            
            # Export to Neo4j
            await self.level3.background_export_worker()
            
            await asyncio.sleep(300)  # Every 5 minutes
    
    async def _promote_level1_to_level2(self):
        """Auto-promote eligible threats"""
        
        all_threats = await self.level1.get_all_threats()
        
        for threat in all_threats:
            if await self.level1.should_promote_to_level2(threat):
                await self.level2.promote_from_level1(threat.threat_id)
    
    async def _promote_level2_to_level3(self):
        """Auto-promote validated threats"""
        
        top_threats = await self.level2.get_top_threats(limit=100)
        
        for memory in top_threats:
            if memory.confidence >= 0.8 and memory.consolidation_count >= 3:
                await self.level3.promote_from_level2(memory.id)
```

**Time:** 0.5 day implementation + 0.5 day testing

---

## Phase 5: Testing & Documentation (Day 7)

### Comprehensive Testing
```python
# test_cascade_memory_complete.py

async def test_full_lifecycle():
    """Test threat through all 3 levels"""
    
    memory = CascadeMemory()
    
    # 1. Add to Level 1
    await memory.add_threat({
        'threat_id': 'test_001',
        'content': 'Test threat',
        'severity': 'CRITICAL',
        'metadata': {'source': 'EDR'}
    })
    
    # 2. Simulate analyst activity
    for i in range(5):
        await memory.level1.record_interaction(
            'test_001', f'analyst_{i}', 'escalate'
        )
    
    # 3. Check promotion to Level 2
    await memory._promote_level1_to_level2()
    
    level2_memory = await memory.level2.get_by_threat_id('test_001')
    assert level2_memory is not None
    
    # 4. Consolidate and promote to Level 3
    for _ in range(3):
        await memory.level2.consolidate(level2_memory.id)
    
    await memory._promote_level2_to_level3()
    
    level3_memory = await memory.level3.get_by_threat_id('test_001')
    assert level3_memory is not None
    
    # 5. Test intelligent get (should promote back up)
    threat = await memory.intelligent_get('test_001')
    assert threat is not None
    
    # Should now be in Level 1 again
    level1_threat = await memory.level1.get_threat('test_001')
    assert level1_threat is not None
```

### Documentation
- Complete API documentation
- Architecture diagrams
- Usage examples
- Performance benchmarks
- Deployment guide

**Time:** 1 day

---

## Timeline Summary

| Day | Task | Hours |
|-----|------|-------|
| 1 | Complete Level 1 improvements | 3-4 |
| 2 | Build Level 2 core | 6-8 |
| 3 | Build Level 2 features + test | 6-8 |
| 4 | Build Level 3 core | 6-8 |
| 5 | Build Level 3 features + test | 6-8 |
| 6 | Integration + unified interface | 6-8 |
| 7 | Testing + documentation | 6-8 |

**Total: ~45-50 hours (~1 week focused work)**

---

## Success Criteria

### Level 1 Complete ✅
- [x] Threat scoring algorithm
- [x] Action type tracking
- [x] Performance metrics
- [x] Promotion criteria
- [x] All tests passing

### Level 2 Complete
- [ ] Confidence-based admission
- [ ] Sorted sets for ranking
- [ ] Auto-promotion on access
- [ ] Industry/type indexing
- [ ] All tests passing

### Level 3 Complete
- [ ] Confidence decay
- [ ] Consolidation tracking
- [ ] Neo4j export
- [ ] Temporal validity
- [ ] All tests passing

### Integration Complete
- [ ] Unified interface
- [ ] Auto-promotion between levels
- [ ] Background maintenance
- [ ] Full lifecycle tests
- [ ] Documentation complete

---

## Next Steps

**Ready to start?**

1. Complete Level 1 improvements (today)
2. Build Level 2 (tomorrow)
3. Build Level 3 (day after)
4. Integrate (day 6)
5. Test & document (day 7)

**Let's do this properly. 🚀**
