"""
Tests for Level 1 Memory System

Focus: Master the basics
- Add threats
- Record interactions
- Retrieve threats
- Simple queries
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from src.cascade.level1_memory import Level1Memory, WorkingMemory


@pytest.fixture
async def memory():
    """Create clean memory system for testing"""
    mem = Level1Memory(redis_url="redis://localhost:32379")
    await mem.connect()
    await mem.clear_all()  # Start fresh
    yield mem
    await mem.clear_all()  # Clean up
    await mem.disconnect()


# ============================================================================
# BASIC OPERATIONS
# ============================================================================

@pytest.mark.asyncio
async def test_add_threat(memory):
    """Test 1: Can add threat to working memory"""
    threat = await memory.add_threat(
        threat_id="test_001",
        content="Test threat",
        severity="HIGH",
        metadata={'source': 'test'}
    )
    
    assert threat.threat_id == "test_001"
    assert threat.severity == "HIGH"
    assert threat.interaction_count == 0


@pytest.mark.asyncio
async def test_get_threat(memory):
    """Test 2: Can retrieve threat"""
    await memory.add_threat(
        threat_id="test_002",
        content="Test threat 2",
        severity="CRITICAL"
    )
    
    retrieved = await memory.get_threat("test_002")
    
    assert retrieved is not None
    assert retrieved.threat_id == "test_002"
    assert retrieved.severity == "CRITICAL"


@pytest.mark.asyncio
async def test_get_nonexistent_threat(memory):
    """Test 3: Getting non-existent threat returns None"""
    retrieved = await memory.get_threat("does_not_exist")
    assert retrieved is None


@pytest.mark.asyncio
async def test_record_interaction(memory):
    """Test 4: Can record analyst interaction"""
    await memory.add_threat(
        threat_id="test_003",
        content="Test threat 3",
        severity="MEDIUM"
    )
    
    # Record interaction
    updated = await memory.record_interaction(
        threat_id="test_003",
        analyst_id="analyst_1",
        action_type="view"
    )
    
    assert updated.interaction_count == 1
    assert updated.analyst_count == 1


@pytest.mark.asyncio
async def test_multiple_interactions(memory):
    """Test 5: Multiple interactions increment counters"""
    await memory.add_threat(
        threat_id="test_004",
        content="Test threat 4",
        severity="HIGH"
    )
    
    # Record 3 interactions
    await memory.record_interaction("test_004", "analyst_1", "view")
    await memory.record_interaction("test_004", "analyst_2", "view")
    updated = await memory.record_interaction("test_004", "analyst_3", "escalate")
    
    assert updated.interaction_count == 3
    assert updated.analyst_count == 3


@pytest.mark.asyncio
async def test_remove_threat(memory):
    """Test 6: Can remove threat"""
    await memory.add_threat(
        threat_id="test_005",
        content="Test threat 5",
        severity="LOW"
    )
    
    # Remove it
    removed = await memory.remove_threat("test_005")
    assert removed is True
    
    # Verify it's gone
    retrieved = await memory.get_threat("test_005")
    assert retrieved is None


# ============================================================================
# QUERY OPERATIONS
# ============================================================================

@pytest.mark.asyncio
async def test_get_all_active(memory):
    """Test 7: Can get all active threat IDs"""
    await memory.add_threat("threat_1", "Content 1", "HIGH")
    await memory.add_threat("threat_2", "Content 2", "MEDIUM")
    await memory.add_threat("threat_3", "Content 3", "CRITICAL")
    
    active = await memory.get_all_active()
    
    assert len(active) == 3
    assert "threat_1" in active
    assert "threat_2" in active
    assert "threat_3" in active


@pytest.mark.asyncio
async def test_get_all_threats(memory):
    """Test 8: Can get all threats with details"""
    await memory.add_threat("threat_a", "Content A", "HIGH")
    await memory.add_threat("threat_b", "Content B", "LOW")
    
    threats = await memory.get_all_threats()
    
    assert len(threats) == 2
    assert all(isinstance(t, WorkingMemory) for t in threats)


@pytest.mark.asyncio
async def test_count_active(memory):
    """Test 9: Can count active threats"""
    initial = await memory.count_active()
    
    await memory.add_threat("threat_x", "Content X", "MEDIUM")
    await memory.add_threat("threat_y", "Content Y", "HIGH")
    
    count = await memory.count_active()
    assert count == initial + 2


@pytest.mark.asyncio
async def test_get_hot_threats(memory):
    """Test 10: Can identify hot threats"""
    # Add threats
    await memory.add_threat("hot_threat", "Hot content", "CRITICAL")
    await memory.add_threat("cold_threat", "Cold content", "LOW")
    
    # Make one hot (4 interactions)
    await memory.record_interaction("hot_threat", "analyst_1")
    await memory.record_interaction("hot_threat", "analyst_2")
    await memory.record_interaction("hot_threat", "analyst_3")
    await memory.record_interaction("hot_threat", "analyst_4")
    
    # Get hot threats (3+ interactions)
    hot = await memory.get_hot_threats(min_interactions=3)
    
    assert len(hot) == 1
    assert hot[0].threat_id == "hot_threat"
    assert hot[0].interaction_count >= 3


@pytest.mark.asyncio
async def test_get_stats(memory):
    """Test 11: Can get statistics"""
    await memory.add_threat("stat_1", "Content 1", "CRITICAL")
    await memory.add_threat("stat_2", "Content 2", "HIGH")
    await memory.add_threat("stat_3", "Content 3", "MEDIUM")
    
    await memory.record_interaction("stat_1", "analyst_1")
    await memory.record_interaction("stat_1", "analyst_2")
    
    stats = await memory.get_stats()
    
    assert stats['total_active'] == 3
    assert stats['total_interactions'] == 2
    assert stats['critical_count'] == 1
    assert stats['high_count'] == 1


# ============================================================================
# EDGE CASES
# ============================================================================

@pytest.mark.asyncio
async def test_interaction_on_nonexistent_threat(memory):
    """Test 12: Recording interaction on non-existent threat returns None"""
    result = await memory.record_interaction("does_not_exist", "analyst_1")
    assert result is None


@pytest.mark.asyncio
async def test_clear_all(memory):
    """Test 13: Can clear all threats"""
    await memory.add_threat("clear_1", "Content 1", "HIGH")
    await memory.add_threat("clear_2", "Content 2", "LOW")
    
    await memory.clear_all()
    
    count = await memory.count_active()
    assert count == 0


@pytest.mark.asyncio
async def test_metadata_preserved(memory):
    """Test 14: Metadata is preserved"""
    metadata = {
        'source': 'EDR',
        'host': 'server-01',
        'user': 'admin'
    }
    
    await memory.add_threat(
        threat_id="meta_test",
        content="Test content",
        severity="HIGH",
        metadata=metadata
    )
    
    retrieved = await memory.get_threat("meta_test")
    
    assert retrieved.metadata == metadata
    assert retrieved.metadata['source'] == 'EDR'


@pytest.mark.asyncio
async def test_concurrent_interactions(memory):
    """Test 15: Can handle concurrent interactions"""
    await memory.add_threat("concurrent", "Content", "HIGH")
    
    # Simulate 5 analysts interacting simultaneously
    tasks = [
        memory.record_interaction("concurrent", f"analyst_{i}")
        for i in range(5)
    ]
    
    await asyncio.gather(*tasks)
    
    threat = await memory.get_threat("concurrent")
    assert threat.interaction_count == 5


# ============================================================================
# INTUITION FEATURES
# ============================================================================

@pytest.mark.asyncio
async def test_hot_threats_sorted(memory):
    """Test 16: Hot threats sorted by interaction count"""
    await memory.add_threat("hot_1", "Content 1", "HIGH")
    await memory.add_threat("hot_2", "Content 2", "HIGH")
    await memory.add_threat("hot_3", "Content 3", "HIGH")
    
    # Different interaction counts
    for _ in range(5):
        await memory.record_interaction("hot_1", f"analyst_{_}")
    for _ in range(3):
        await memory.record_interaction("hot_2", f"analyst_{_}")
    for _ in range(7):
        await memory.record_interaction("hot_3", f"analyst_{_}")
    
    hot = await memory.get_hot_threats(min_interactions=3)
    
    # Should be sorted: hot_3 (7), hot_1 (5), hot_2 (3)
    assert len(hot) == 3
    assert hot[0].threat_id == "hot_3"
    assert hot[1].threat_id == "hot_1"
    assert hot[2].threat_id == "hot_2"


@pytest.mark.asyncio
async def test_empty_stats(memory):
    """Test 17: Stats work with no threats"""
    stats = await memory.get_stats()
    
    assert stats['total_active'] == 0
    assert stats['total_interactions'] == 0
    assert stats['avg_interactions'] == 0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
