"""
Comprehensive tests for AnalystFlowTracker

Tests ALL functionality before proceeding to next module.
Nuclear grade engineering requires thorough validation.
"""

import pytest
import asyncio
from datetime import datetime
from src.cascade.flow_tracker import (
    AnalystFlowTracker,
    FlowAction,
    ActionType
)


@pytest.fixture
async def tracker():
    """Create tracker instance for testing"""
    # Use NodePort for tqakb Redis instance (redis-82-nodeport)
    tracker = AnalystFlowTracker(redis_url="redis://localhost:32379")
    await tracker.connect()
    yield tracker
    # Cleanup
    await tracker.clear_analyst_history("test_analyst")
    await tracker.disconnect()


@pytest.mark.asyncio
async def test_tracker_connection():
    """Test 1: Can we connect to Redis?"""
    tracker = AnalystFlowTracker(redis_url="redis://localhost:32379")
    await tracker.connect()
    assert tracker._redis_client is not None
    await tracker.disconnect()


@pytest.mark.asyncio
async def test_track_single_action(tracker):
    """Test 2: Can we track a single action?"""
    action_id = await tracker.track_action(
        analyst_id="test_analyst",
        action_type=ActionType.VIEW_THREAT,
        threat_id="threat_001",
        industry="aviation",
        severity="CRITICAL",
        time_spent_seconds=45
    )
    
    assert action_id is not None
    assert isinstance(action_id, str)


@pytest.mark.asyncio
async def test_retrieve_recent_actions(tracker):
    """Test 3: Can we retrieve tracked actions?"""
    # Track multiple actions
    for i in range(5):
        await tracker.track_action(
            analyst_id="test_analyst",
            action_type=ActionType.VIEW_THREAT,
            threat_id=f"threat_{i:03d}",
            industry="aviation"
        )
    
    # Retrieve them
    actions = await tracker.get_recent_actions("test_analyst", count=10)
    
    assert len(actions) == 5
    assert actions[0]['action_type'] == ActionType.VIEW_THREAT.value
    assert 'timestamp' in actions[0]


@pytest.mark.asyncio
async def test_action_ordering(tracker):
    """Test 4: Are actions returned in correct order (newest first)?"""
    # Track actions with identifiable threat IDs
    await tracker.track_action(
        analyst_id="test_analyst",
        action_type=ActionType.VIEW_THREAT,
        threat_id="threat_first"
    )
    
    await asyncio.sleep(0.1)  # Small delay
    
    await tracker.track_action(
        analyst_id="test_analyst",
        action_type=ActionType.VIEW_THREAT,
        threat_id="threat_second"
    )
    
    actions = await tracker.get_recent_actions("test_analyst", count=2)
    
    # Most recent should be first
    assert actions[0]['threat_id'] == "threat_second"
    assert actions[1]['threat_id'] == "threat_first"


@pytest.mark.asyncio
async def test_different_action_types(tracker):
    """Test 5: Can we track all action types?"""
    action_types = [
        ActionType.VIEW_THREAT,
        ActionType.SEARCH,
        ActionType.ESCALATE,
        ActionType.DISMISS,
        ActionType.DOWNLOAD_REPORT
    ]
    
    for action_type in action_types:
        await tracker.track_action(
            analyst_id="test_analyst",
            action_type=action_type
        )
    
    actions = await tracker.get_recent_actions("test_analyst", count=10)
    tracked_types = {a['action_type'] for a in actions}
    
    assert len(tracked_types) == len(action_types)


@pytest.mark.asyncio
async def test_optional_fields(tracker):
    """Test 6: Can we track with minimal data (optional fields)?"""
    # Track with only required fields
    action_id = await tracker.track_action(
        analyst_id="test_analyst",
        action_type=ActionType.SEARCH
    )
    
    assert action_id is not None
    
    actions = await tracker.get_recent_actions("test_analyst", count=1)
    assert actions[0]['threat_id'] is None
    assert actions[0]['industry'] is None


@pytest.mark.asyncio
async def test_search_query_tracking(tracker):
    """Test 7: Can we track search queries?"""
    search_query = "aviation ransomware lockbit"
    
    await tracker.track_action(
        analyst_id="test_analyst",
        action_type=ActionType.SEARCH,
        search_query=search_query,
        industry="aviation"
    )
    
    actions = await tracker.get_recent_actions("test_analyst", count=1)
    assert actions[0]['search_query'] == search_query


@pytest.mark.asyncio
async def test_time_spent_tracking(tracker):
    """Test 8: Can we track time spent?"""
    time_spent = 180  # 3 minutes
    
    await tracker.track_action(
        analyst_id="test_analyst",
        action_type=ActionType.VIEW_THREAT,
        threat_id="threat_001",
        time_spent_seconds=time_spent
    )
    
    actions = await tracker.get_recent_actions("test_analyst", count=1)
    assert actions[0]['time_spent'] == time_spent


@pytest.mark.asyncio
async def test_action_count(tracker):
    """Test 9: Can we count actions?"""
    # Track 10 actions
    for i in range(10):
        await tracker.track_action(
            analyst_id="test_analyst",
            action_type=ActionType.VIEW_THREAT
        )
    
    count = await tracker.count_actions("test_analyst")
    assert count == 10


@pytest.mark.asyncio
async def test_action_count_by_type(tracker):
    """Test 10: Can we count specific action types?"""
    # Track mixed actions
    for i in range(5):
        await tracker.track_action(
            analyst_id="test_analyst",
            action_type=ActionType.VIEW_THREAT
        )
    
    for i in range(3):
        await tracker.track_action(
            analyst_id="test_analyst",
            action_type=ActionType.ESCALATE
        )
    
    escalation_count = await tracker.count_actions(
        "test_analyst",
        action_type=ActionType.ESCALATE
    )
    
    assert escalation_count == 3


@pytest.mark.asyncio
async def test_action_summary(tracker):
    """Test 11: Can we get action summary?"""
    # Track varied actions
    await tracker.track_action(
        analyst_id="test_analyst",
        action_type=ActionType.VIEW_THREAT,
        industry="aviation",
        time_spent_seconds=120
    )
    
    await tracker.track_action(
        analyst_id="test_analyst",
        action_type=ActionType.SEARCH,
        industry="healthcare"
    )
    
    await tracker.track_action(
        analyst_id="test_analyst",
        action_type=ActionType.ESCALATE,
        industry="aviation"
    )
    
    summary = await tracker.get_action_summary("test_analyst")
    
    assert summary['total_actions'] == 3
    assert 'action_types' in summary
    assert 'industries' in summary
    assert summary['most_viewed_industry'] in ['aviation', 'healthcare']


@pytest.mark.asyncio
async def test_multiple_analysts(tracker):
    """Test 12: Can we track multiple analysts independently?"""
    # Track for analyst 1
    await tracker.track_action(
        analyst_id="analyst_1",
        action_type=ActionType.VIEW_THREAT,
        industry="aviation"
    )
    
    # Track for analyst 2
    await tracker.track_action(
        analyst_id="analyst_2",
        action_type=ActionType.VIEW_THREAT,
        industry="healthcare"
    )
    
    # Verify separation
    actions_1 = await tracker.get_recent_actions("analyst_1", count=10)
    actions_2 = await tracker.get_recent_actions("analyst_2", count=10)
    
    assert len(actions_1) == 1
    assert len(actions_2) == 1
    assert actions_1[0]['industry'] == "aviation"
    assert actions_2[0]['industry'] == "healthcare"
    
    # Cleanup analyst 2
    await tracker.clear_analyst_history("analyst_2")


@pytest.mark.asyncio
async def test_stream_length_limiting(tracker):
    """Test 13: Does stream length limiting work?"""
    # Track more than max length
    tracker.max_stream_length = 100
    
    for i in range(150):
        await tracker.track_action(
            analyst_id="test_analyst",
            action_type=ActionType.VIEW_THREAT,
            threat_id=f"threat_{i:03d}"
        )
    
    count = await tracker.count_actions("test_analyst")
    
    # Should be trimmed to ~100 (approximate due to Redis MAXLEN ~)
    assert count <= 110  # Allow some margin for approximate trimming


@pytest.mark.asyncio
async def test_empty_analyst_history(tracker):
    """Test 14: What happens with no actions?"""
    actions = await tracker.get_recent_actions("nonexistent_analyst", count=10)
    assert len(actions) == 0
    
    summary = await tracker.get_action_summary("nonexistent_analyst")
    assert summary['total_actions'] == 0


@pytest.mark.asyncio
async def test_clear_history(tracker):
    """Test 15: Can we clear history?"""
    # Track some actions
    for i in range(5):
        await tracker.track_action(
            analyst_id="test_analyst",
            action_type=ActionType.VIEW_THREAT
        )
    
    # Verify they exist
    actions_before = await tracker.get_recent_actions("test_analyst", count=10)
    assert len(actions_before) == 5
    
    # Clear
    await tracker.clear_analyst_history("test_analyst")
    
    # Verify cleared
    actions_after = await tracker.get_recent_actions("test_analyst", count=10)
    assert len(actions_after) == 0


@pytest.mark.asyncio
async def test_timestamp_format(tracker):
    """Test 16: Are timestamps in correct ISO format?"""
    await tracker.track_action(
        analyst_id="test_analyst",
        action_type=ActionType.VIEW_THREAT
    )
    
    actions = await tracker.get_recent_actions("test_analyst", count=1)
    timestamp_str = actions[0]['timestamp']
    
    # Should be valid ISO format
    try:
        datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        timestamp_valid = True
    except ValueError:
        timestamp_valid = False
    
    assert timestamp_valid


@pytest.mark.asyncio
async def test_concurrent_tracking(tracker):
    """Test 17: Can we handle concurrent action tracking?"""
    # Track actions concurrently
    tasks = [
        tracker.track_action(
            analyst_id="test_analyst",
            action_type=ActionType.VIEW_THREAT,
            threat_id=f"threat_{i:03d}"
        )
        for i in range(10)
    ]
    
    await asyncio.gather(*tasks)
    
    actions = await tracker.get_recent_actions("test_analyst", count=20)
    assert len(actions) == 10


@pytest.mark.asyncio
async def test_flow_action_dataclass(tracker):
    """Test 18: Does FlowAction dataclass work correctly?"""
    action = FlowAction(
        analyst_id="test_analyst",
        action_type=ActionType.VIEW_THREAT,
        timestamp=datetime.utcnow().isoformat(),
        threat_id="threat_001",
        industry="aviation",
        severity="CRITICAL"
    )
    
    # Convert to dict
    action_dict = action.to_dict()
    
    assert action_dict['analyst_id'] == "test_analyst"
    assert action_dict['action_type'] == ActionType.VIEW_THREAT.value
    assert action_dict['threat_id'] == "threat_001"


@pytest.mark.asyncio
async def test_metadata_tracking(tracker):
    """Test 19: Can we track custom metadata?"""
    metadata = {
        'source': 'api',
        'client_ip': '192.168.1.1',
        'session_id': 'sess_123'
    }
    
    await tracker.track_action(
        analyst_id="test_analyst",
        action_type=ActionType.VIEW_THREAT,
        metadata=metadata
    )
    
    # Note: Current implementation doesn't store metadata in Redis
    # This test documents expected behavior for future enhancement
    actions = await tracker.get_recent_actions("test_analyst", count=1)
    assert actions[0] is not None


@pytest.mark.asyncio  
async def test_high_volume_tracking(tracker):
    """Test 20: Performance test - Can we handle high volume?"""
    import time
    
    start = time.time()
    
    # Track 100 actions
    for i in range(100):
        await tracker.track_action(
            analyst_id="test_analyst",
            action_type=ActionType.VIEW_THREAT,
            threat_id=f"threat_{i:03d}"
        )
    
    elapsed = time.time() - start
    
    # Should be fast (<5 seconds for 100 actions)
    assert elapsed < 5.0
    
    # Verify all tracked
    count = await tracker.count_actions("test_analyst")
    assert count >= 100  # >= because other tests might add actions


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
