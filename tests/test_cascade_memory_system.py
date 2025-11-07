"""
Comprehensive tests for ThreatMemorySystem

Tests ALL functionality - as many tests as needed for confidence.
Following nuclear-grade engineering: test everything thoroughly.
"""

import pytest
import asyncio
import json
from datetime import datetime
from src.cascade.memory_system import (
    ThreatMemorySystem,
    MemoryType,
    MemoryFormationDecision,
    ThreatMemory
)


@pytest.fixture
async def memory_system():
    """Create memory system for testing"""
    system = ThreatMemorySystem(redis_url="redis://localhost:32379")
    await system.connect()
    yield system
    
    # Cleanup - remove all test memories
    try:
        all_memories = await system._redis_client.smembers("cascade:memory:all")
        for mem_id in all_memories:
            await system._redis_client.delete(f"cascade:memory:{mem_id}")
        await system._redis_client.delete("cascade:memory:all")
        await system._redis_client.delete("cascade:memory:export:pending")
        # Clean up industry indexes
        for industry in ['aviation', 'healthcare', 'finance', 'unknown']:
            await system._redis_client.delete(f"cascade:memory:industry:{industry}")
        for mem_type in ['campaign', 'evolution', 'pattern', 'validated']:
            await system._redis_client.delete(f"cascade:memory:type:{mem_type}")
    except:
        pass
    
    await system.disconnect()


# ============================================================================
# CONNECTION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_redis_connection():
    """Test 1: Can we connect to Redis?"""
    system = ThreatMemorySystem(redis_url="redis://localhost:32379")
    await system.connect()
    assert system._redis_client is not None
    await system.disconnect()


@pytest.mark.asyncio
async def test_disconnect_cleanup():
    """Test 2: Does disconnect clean up properly?"""
    system = ThreatMemorySystem(redis_url="redis://localhost:32379")
    await system.connect()
    await system.disconnect()
    assert system._redis_client is None


# ============================================================================
# MEMORY FORMATION DECISION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_formation_decision_low_engagement(memory_system):
    """Test 3: Low engagement = no memory formation"""
    threat_data = {
        'severity': 'LOW',
        'confidence': 0.3,
        'sources': ['single_source']
    }
    analyst_actions = [
        {'analyst_id': 'analyst_1', 'action_type': 'view', 'time_spent_seconds': 10}
    ]
    
    decision = await memory_system.should_form_memory(
        'threat_low', analyst_actions, threat_data
    )
    
    assert decision.should_form == False
    assert decision.confidence < 0.7


@pytest.mark.asyncio
async def test_formation_decision_high_engagement(memory_system):
    """Test 4: High engagement = memory formation"""
    threat_data = {
        'severity': 'CRITICAL',
        'confidence': 1.0,
        'source_reliability': 0.95,
        'sources': ['s1', 's2', 's3', 's4', 's5', 's6']
    }
    analyst_actions = [
        {'analyst_id': f'analyst_{i}', 'action_type': 'escalate', 'time_spent_seconds': 300}
        for i in range(5)
    ]
    
    decision = await memory_system.should_form_memory(
        'threat_high', analyst_actions, threat_data
    )
    
    assert decision.should_form == True
    assert decision.confidence >= 0.7


@pytest.mark.asyncio
async def test_engagement_score_calculation(memory_system):
    """Test 5: Engagement score calculated correctly"""
    # 5 analysts, 3 escalations, 600 seconds = should score high
    analyst_actions = [
        {'analyst_id': 'a1', 'action_type': 'escalate', 'time_spent_seconds': 200},
        {'analyst_id': 'a2', 'action_type': 'escalate', 'time_spent_seconds': 200},
        {'analyst_id': 'a3', 'action_type': 'escalate', 'time_spent_seconds': 200},
        {'analyst_id': 'a4', 'action_type': 'view', 'time_spent_seconds': 0},
        {'analyst_id': 'a5', 'action_type': 'view', 'time_spent_seconds': 0},
    ]
    
    score = memory_system._calculate_engagement_score(analyst_actions)
    
    # 5 analysts (1.0) * 0.4 + 3 escalations (1.0) * 0.4 + 600s (1.0) * 0.2 = 1.0
    assert score >= 0.8  # Should be very high


@pytest.mark.asyncio
async def test_source_score_calculation(memory_system):
    """Test 6: Source score calculated correctly"""
    threat_data = {
        'sources': ['s1', 's2', 's3', 's4', 's5'],  # 5 sources
        'source_reliability': 0.9
    }
    
    score = memory_system._calculate_source_score(threat_data)
    
    # 5 sources (1.0) * 0.6 + 0.9 reliability * 0.4 = 0.96
    assert score > 0.9


@pytest.mark.asyncio
async def test_impact_score_calculation(memory_system):
    """Test 7: Impact score calculated correctly"""
    threat_data = {
        'severity': 'CRITICAL',
        'confidence': 0.9
    }
    
    score = memory_system._calculate_impact_score(threat_data)
    
    # CRITICAL (1.0) * 0.9 confidence = 0.9
    assert score == 0.9


@pytest.mark.asyncio
async def test_memory_type_validated(memory_system):
    """Test 8: Validated memory type detection"""
    analyst_actions = [
        {'action_type': 'escalate'},
        {'action_type': 'escalate'},
        {'action_type': 'escalate'}
    ]
    
    mem_type = memory_system._determine_memory_type(
        analyst_actions, {}, 0.5
    )
    
    assert mem_type == MemoryType.VALIDATED


@pytest.mark.asyncio
async def test_formation_threshold(memory_system):
    """Test 9: Threshold exactly at 0.7"""
    # Engineer data to get exactly 0.7 confidence
    threat_data = {
        'severity': 'HIGH',
        'confidence': 0.7,
        'sources': ['s1', 's2', 's3'],
        'source_reliability': 0.7
    }
    analyst_actions = [
        {'analyst_id': f'a{i}', 'action_type': 'view', 'time_spent_seconds': 100}
        for i in range(3)
    ]
    
    decision = await memory_system.should_form_memory(
        'threat_threshold', analyst_actions, threat_data
    )
    
    # Should form if >= 0.7
    if decision.confidence >= 0.7:
        assert decision.should_form == True
    else:
        assert decision.should_form == False


# ============================================================================
# REDIS STORAGE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_form_memory_writes_to_redis(memory_system):
    """Test 10: Memory formation writes to Redis Hash"""
    threat_data = {
        'threat_id': 'test_threat',
        'title': 'Test Threat',
        'description': 'Testing Redis storage',
        'severity': 'CRITICAL',
        'confidence': 1.0,
        'industry': 'aviation',
        'sources': ['s1', 's2', 's3', 's4', 's5', 's6']
    }
    analyst_actions = [
        {'analyst_id': f'a{i}', 'action_type': 'escalate', 'time_spent_seconds': 300}
        for i in range(5)
    ]
    
    decision = await memory_system.should_form_memory(
        'test_threat', analyst_actions, threat_data
    )
    
    memory = await memory_system.form_memory(
        'test_threat', analyst_actions, threat_data, decision
    )
    
    # Verify it exists in Redis
    exists = await memory_system._redis_client.exists(f"cascade:memory:{memory.id}")
    assert exists == 1


@pytest.mark.asyncio
async def test_form_memory_adds_to_index_sets(memory_system):
    """Test 11: Memory added to all index Sets"""
    threat_data = {
        'severity': 'CRITICAL',
        'confidence': 1.0,
        'industry': 'aviation',
        'sources': ['s1', 's2', 's3', 's4', 's5', 's6']
    }
    analyst_actions = [
        {'analyst_id': f'a{i}', 'action_type': 'escalate', 'time_spent_seconds': 300}
        for i in range(5)
    ]
    
    decision = await memory_system.should_form_memory(
        'test_threat', analyst_actions, threat_data
    )
    memory = await memory_system.form_memory(
        'test_threat', analyst_actions, threat_data, decision
    )
    
    # Check all index sets
    in_all = await memory_system._redis_client.sismember("cascade:memory:all", memory.id)
    in_industry = await memory_system._redis_client.sismember(
        f"cascade:memory:industry:{memory.industry}", memory.id
    )
    in_type = await memory_system._redis_client.sismember(
        f"cascade:memory:type:{memory.memory_type}", memory.id
    )
    
    assert in_all == 1
    assert in_industry == 1
    assert in_type == 1


@pytest.mark.asyncio
async def test_form_memory_adds_to_export_queue(memory_system):
    """Test 12: Memory queued for Neo4j export"""
    threat_data = {
        'severity': 'CRITICAL',
        'confidence': 1.0,
        'industry': 'aviation',
        'sources': ['s1', 's2', 's3', 's4', 's5', 's6']
    }
    analyst_actions = [
        {'analyst_id': f'a{i}', 'action_type': 'escalate', 'time_spent_seconds': 300}
        for i in range(5)
    ]
    
    decision = await memory_system.should_form_memory(
        'test_threat', analyst_actions, threat_data
    )
    memory = await memory_system.form_memory(
        'test_threat', analyst_actions, threat_data, decision
    )
    
    # Check export queue
    in_queue = await memory_system._redis_client.sismember(
        "cascade:memory:export:pending", memory.id
    )
    assert in_queue == 1


@pytest.mark.asyncio
async def test_get_memory_retrieval(memory_system):
    """Test 13: Can retrieve memory from Redis"""
    threat_data = {
        'severity': 'CRITICAL',
        'confidence': 1.0,
        'industry': 'healthcare',
        'sources': ['s1', 's2', 's3', 's4', 's5', 's6']
    }
    analyst_actions = [
        {'analyst_id': f'a{i}', 'action_type': 'escalate', 'time_spent_seconds': 300}
        for i in range(5)
    ]
    
    decision = await memory_system.should_form_memory(
        'test_threat', analyst_actions, threat_data
    )
    memory = await memory_system.form_memory(
        'test_threat', analyst_actions, threat_data, decision
    )
    
    # Retrieve it
    retrieved = await memory_system.get_memory(memory.id)
    
    assert retrieved is not None
    assert retrieved.id == memory.id
    assert retrieved.confidence == memory.confidence
    assert retrieved.industry == 'healthcare'


@pytest.mark.asyncio
async def test_get_nonexistent_memory(memory_system):
    """Test 14: Getting non-existent memory returns None"""
    retrieved = await memory_system.get_memory("nonexistent_memory_id")
    assert retrieved is None


@pytest.mark.asyncio
async def test_memory_data_integrity(memory_system):
    """Test 15: All memory fields preserved in Redis"""
    threat_data = {
        'threat_id': 'integrity_test',
        'title': 'Integrity Test',
        'description': 'Testing data integrity',
        'severity': 'HIGH',
        'confidence': 0.85,
        'industry': 'finance',
        'sources': ['s1', 's2', 's3', 's4', 's5']
    }
    analyst_actions = [
        {'analyst_id': f'a{i}', 'action_type': 'escalate', 'time_spent_seconds': 200}
        for i in range(4)
    ]
    
    decision = await memory_system.should_form_memory(
        'integrity_test', analyst_actions, threat_data
    )
    original = await memory_system.form_memory(
        'integrity_test', analyst_actions, threat_data, decision
    )
    
    # Retrieve and verify all fields
    retrieved = await memory_system.get_memory(original.id)
    
    assert retrieved.threat_id == 'integrity_test'
    assert retrieved.content == 'Testing data integrity'
    assert retrieved.severity == 'HIGH'
    assert retrieved.confidence == decision.confidence
    assert retrieved.industry == 'finance'
    assert retrieved.memory_type == decision.memory_type.value
    assert retrieved.analyst_interactions == 4
    assert retrieved.neo4j_exported == False


# ============================================================================
# QUERY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_memories_by_industry(memory_system):
    """Test 16: Can query memories by industry"""
    # Create memories in different industries
    for industry in ['aviation', 'healthcare', 'aviation']:
        threat_data = {
            'severity': 'CRITICAL',
            'confidence': 1.0,
            'industry': industry,
            'sources': ['s1', 's2', 's3', 's4', 's5', 's6']
        }
        analyst_actions = [
            {'analyst_id': f'a{i}', 'action_type': 'escalate', 'time_spent_seconds': 300}
            for i in range(5)
        ]
        
        decision = await memory_system.should_form_memory(
            f'threat_{industry}', analyst_actions, threat_data
        )
        await memory_system.form_memory(
            f'threat_{industry}', analyst_actions, threat_data, decision
        )
    
    # Query aviation memories
    aviation_memories = await memory_system.get_memories_by_industry('aviation')
    
    assert len(aviation_memories) == 2
    assert all(m.industry == 'aviation' for m in aviation_memories)


@pytest.mark.asyncio
async def test_count_memories(memory_system):
    """Test 17: Memory counting works"""
    initial_count = await memory_system.count_memories()
    
    # Create 3 memories
    for i in range(3):
        threat_data = {
            'severity': 'CRITICAL',
            'confidence': 1.0,
            'industry': 'aviation',
            'sources': ['s1', 's2', 's3', 's4', 's5', 's6']
        }
        analyst_actions = [
            {'analyst_id': f'a{j}', 'action_type': 'escalate', 'time_spent_seconds': 300}
            for j in range(5)
        ]
        
        decision = await memory_system.should_form_memory(
            f'threat_{i}', analyst_actions, threat_data
        )
        await memory_system.form_memory(
            f'threat_{i}', analyst_actions, threat_data, decision
        )
    
    final_count = await memory_system.count_memories()
    assert final_count == initial_count + 3


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_empty_analyst_actions(memory_system):
    """Test 18: Handles empty analyst actions"""
    threat_data = {
        'severity': 'CRITICAL',
        'confidence': 1.0,
        'sources': ['s1', 's2', 's3']
    }
    
    decision = await memory_system.should_form_memory(
        'threat_empty', [], threat_data
    )
    
    assert decision.should_form == False  # No engagement


@pytest.mark.asyncio
async def test_missing_threat_fields(memory_system):
    """Test 19: Handles missing threat data fields"""
    threat_data = {}  # Minimal data
    analyst_actions = [
        {'analyst_id': 'a1', 'action_type': 'escalate', 'time_spent_seconds': 100}
    ]
    
    decision = await memory_system.should_form_memory(
        'threat_minimal', analyst_actions, threat_data
    )
    
    # Should not crash, but probably won't form memory
    assert isinstance(decision, MemoryFormationDecision)


@pytest.mark.asyncio
async def test_invalid_severity_level(memory_system):
    """Test 20: Handles invalid severity levels"""
    threat_data = {
        'severity': 'INVALID_SEVERITY',
        'confidence': 0.8,
        'sources': ['s1', 's2']
    }
    analyst_actions = [
        {'analyst_id': 'a1', 'action_type': 'view', 'time_spent_seconds': 100}
    ]
    
    score = memory_system._calculate_impact_score(threat_data)
    
    # Should default to 0.5 for unknown severity
    assert score > 0


@pytest.mark.asyncio
async def test_concurrent_memory_formation(memory_system):
    """Test 21: Can handle concurrent memory formation"""
    async def create_memory(index):
        threat_data = {
            'threat_id': f'concurrent_{index}',
            'severity': 'CRITICAL',
            'confidence': 1.0,
            'industry': 'aviation',
            'sources': ['s1', 's2', 's3', 's4', 's5', 's6']
        }
        analyst_actions = [
            {'analyst_id': f'a{i}', 'action_type': 'escalate', 'time_spent_seconds': 300}
            for i in range(5)
        ]
        
        decision = await memory_system.should_form_memory(
            f'concurrent_{index}', analyst_actions, threat_data
        )
        return await memory_system.form_memory(
            f'concurrent_{index}', analyst_actions, threat_data, decision
        )
    
    # Create 5 memories concurrently
    memories = await asyncio.gather(*[create_memory(i) for i in range(5)])
    
    assert len(memories) == 5
    assert len(set(m.id for m in memories)) == 5  # All unique IDs


# ============================================================================
# DATACLASS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_threat_memory_to_dict():
    """Test 22: ThreatMemory serialization to dict"""
    memory = ThreatMemory(
        id="test_id",
        threat_id="threat_123",
        content="Test content",
        confidence=0.85,
        formed_at="2025-11-03T19:30:00Z",
        last_updated="2025-11-03T19:30:00Z",
        evidence_count=5,
        analyst_interactions=3,
        industry="aviation",
        severity="HIGH",
        memory_type="validated",
        metadata={'key': 'value'},
        neo4j_exported=False
    )
    
    data = memory.to_dict()
    
    assert data['id'] == "test_id"
    assert data['confidence'] == 0.85
    assert data['metadata'] == {'key': 'value'}


@pytest.mark.asyncio
async def test_threat_memory_from_dict():
    """Test 23: ThreatMemory deserialization from dict"""
    data = {
        'id': "test_id",
        'threat_id': "threat_123",
        'content': "Test content",
        'confidence': 0.85,
        'formed_at': "2025-11-03T19:30:00Z",
        'last_updated': "2025-11-03T19:30:00Z",
        'evidence_count': 5,
        'analyst_interactions': 3,
        'industry': "aviation",
        'severity': "HIGH",
        'memory_type': "validated",
        'metadata': {'key': 'value'},
        'neo4j_exported': False
    }
    
    memory = ThreatMemory.from_dict(data)
    
    assert memory.id == "test_id"
    assert memory.confidence == 0.85
    assert memory.metadata == {'key': 'value'}


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_redis_write_performance(memory_system):
    """Test 24: Redis write performance (<10ms target)"""
    import time
    
    threat_data = {
        'severity': 'CRITICAL',
        'confidence': 1.0,
        'industry': 'aviation',
        'sources': ['s1', 's2', 's3', 's4', 's5', 's6']
    }
    analyst_actions = [
        {'analyst_id': f'a{i}', 'action_type': 'escalate', 'time_spent_seconds': 300}
        for i in range(5)
    ]
    
    decision = await memory_system.should_form_memory(
        'perf_test', analyst_actions, threat_data
    )
    
    start = time.time()
    memory = await memory_system.form_memory(
        'perf_test', analyst_actions, threat_data, decision
    )
    duration = time.time() - start
    
    print(f"\nRedis write took: {duration*1000:.2f}ms")
    # Target: <10ms, but allow 50ms for test environment
    assert duration < 0.05


@pytest.mark.asyncio
async def test_high_volume_memory_formation(memory_system):
    """Test 25: Can handle 100 memory formations"""
    import time
    
    start = time.time()
    
    for i in range(100):
        threat_data = {
            'severity': 'CRITICAL',
            'confidence': 1.0,
            'industry': 'aviation',
            'sources': ['s1', 's2', 's3', 's4', 's5', 's6']
        }
        analyst_actions = [
            {'analyst_id': f'a{j}', 'action_type': 'escalate', 'time_spent_seconds': 300}
            for j in range(5)
        ]
        
        decision = await memory_system.should_form_memory(
            f'volume_{i}', analyst_actions, threat_data
        )
        await memory_system.form_memory(
            f'volume_{i}', analyst_actions, threat_data, decision
        )
    
    duration = time.time() - start
    print(f"\n100 memories formed in: {duration:.2f}s ({duration*10:.0f}ms avg)")
    
    count = await memory_system.count_memories()
    assert count >= 100


# ============================================================================
# REASON GENERATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_reason_generation(memory_system):
    """Test 26: Formation reason includes relevant factors"""
    threat_data = {
        'severity': 'CRITICAL',
        'confidence': 1.0,
        'source_reliability': 0.95,
        'industry': 'aviation',
        'sources': ['s1', 's2', 's3', 's4', 's5', 's6']
    }
    analyst_actions = [
        {'analyst_id': f'a{i}', 'action_type': 'escalate', 'time_spent_seconds': 300}
        for i in range(5)
    ]
    
    decision = await memory_system.should_form_memory(
        'reason_test', analyst_actions, threat_data
    )
    
    # Reason should mention key factors
    assert 'engagement' in decision.reason.lower() or 'validated' in decision.reason.lower()
    assert decision.memory_type in [MemoryType.VALIDATED, MemoryType.CAMPAIGN]


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
