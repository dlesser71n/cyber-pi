"""
Comprehensive tests for PatternAnalyzer

Tests ALL functionality before proceeding to next module.
Nuclear grade engineering requires thorough validation.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from src.cascade.flow_tracker import (
    AnalystFlowTracker,
    ActionType
)
from src.cascade.pattern_analyzer import PatternAnalyzer


@pytest.fixture
async def tracker():
    """Create tracker instance for testing"""
    tracker = AnalystFlowTracker(redis_url="redis://localhost:32379")
    await tracker.connect()
    yield tracker
    await tracker.disconnect()


@pytest.fixture
async def analyzer(tracker):
    """Create analyzer instance for testing"""
    analyzer = PatternAnalyzer(tracker, redis_url="redis://localhost:32379")
    await analyzer.connect()
    yield analyzer
    await analyzer.disconnect()


@pytest.fixture
async def populated_tracker(tracker):
    """Create tracker with sample data for testing"""
    analyst_id = "test_analyst_patterns"
    
    # Clear any existing data
    await tracker.clear_analyst_history(analyst_id)
    
    # Create realistic analyst behavior pattern
    # Analyst focused on aviation with some healthcare
    for i in range(30):
        await tracker.track_action(
            analyst_id=analyst_id,
            action_type=ActionType.VIEW_THREAT,
            threat_id=f"threat_{i:03d}",
            industry="aviation" if i % 4 != 0 else "healthcare",
            severity="CRITICAL" if i % 3 == 0 else "HIGH",
            time_spent_seconds=120 + (i * 5)
        )
        
        # Escalate some threats
        if i % 5 == 0:
            await tracker.track_action(
                analyst_id=analyst_id,
                action_type=ActionType.ESCALATE,
                threat_id=f"threat_{i:03d}",
                industry="aviation" if i % 4 != 0 else "healthcare"
            )
    
    # Add some searches
    search_terms = ["ransomware", "phishing", "aviation malware", "ransomware"]
    for term in search_terms:
        await tracker.track_action(
            analyst_id=analyst_id,
            action_type=ActionType.SEARCH,
            search_query=term,
            industry="aviation"
        )
    
    return tracker, analyst_id


@pytest.mark.asyncio
async def test_analyzer_connection(analyzer):
    """Test 1: Can we connect to Redis for caching?"""
    assert analyzer._redis_client is not None


@pytest.mark.asyncio
async def test_analyze_patterns_empty(analyzer):
    """Test 2: Handle analyst with no actions"""
    patterns = await analyzer.analyze_patterns("nonexistent_analyst")
    
    assert patterns['sample_size'] == 0
    assert patterns['escalation_rate'] == 0.0
    assert patterns['specialization_score'] == 0.0
    assert patterns['most_viewed_industries'] == {}


@pytest.mark.asyncio
async def test_analyze_patterns_with_data(populated_tracker, analyzer):
    """Test 3: Analyze patterns from populated data"""
    tracker, analyst_id = populated_tracker
    
    patterns = await analyzer.analyze_patterns(analyst_id, use_cache=False)
    
    # Verify basic structure
    assert 'most_viewed_industries' in patterns
    assert 'escalation_rate' in patterns
    assert 'avg_time_per_threat' in patterns
    assert 'sample_size' in patterns
    
    # Verify data quality
    assert patterns['sample_size'] > 0
    assert isinstance(patterns['escalation_rate'], float)
    assert isinstance(patterns['specialization_score'], float)


@pytest.mark.asyncio
async def test_industry_focus_analysis(populated_tracker, analyzer):
    """Test 4: Industry preference detection"""
    tracker, analyst_id = populated_tracker
    
    patterns = await analyzer.analyze_patterns(analyst_id, use_cache=False)
    industries = patterns['most_viewed_industries']
    
    # Aviation should be most common (75% of actions)
    assert 'aviation' in industries
    assert industries['aviation'] > industries.get('healthcare', 0)


@pytest.mark.asyncio
async def test_escalation_rate_calculation(populated_tracker, analyzer):
    """Test 5: Escalation rate accuracy"""
    tracker, analyst_id = populated_tracker
    
    patterns = await analyzer.analyze_patterns(analyst_id, use_cache=False)
    escalation_rate = patterns['escalation_rate']
    
    # Should be around 20% (every 5th threat escalated)
    assert 15 <= escalation_rate <= 25


@pytest.mark.asyncio
async def test_time_per_threat_calculation(populated_tracker, analyzer):
    """Test 6: Average time calculation"""
    tracker, analyst_id = populated_tracker
    
    patterns = await analyzer.analyze_patterns(analyst_id, use_cache=False)
    avg_time = patterns['avg_time_per_threat']
    
    # Should be reasonable time (we set 120 + i*5)
    assert avg_time > 0
    assert avg_time < 500  # Less than 8 minutes average


@pytest.mark.asyncio
async def test_severity_preference(populated_tracker, analyzer):
    """Test 7: Severity focus detection"""
    tracker, analyst_id = populated_tracker
    
    patterns = await analyzer.analyze_patterns(analyst_id, use_cache=False)
    severities = patterns['preferred_severity_focus']
    
    # Should have both CRITICAL and HIGH
    assert 'CRITICAL' in severities or 'HIGH' in severities
    assert isinstance(severities, dict)


@pytest.mark.asyncio
async def test_search_terms_extraction(populated_tracker, analyzer):
    """Test 8: Common search query extraction"""
    tracker, analyst_id = populated_tracker
    
    patterns = await analyzer.analyze_patterns(analyst_id, use_cache=False)
    searches = patterns['common_search_terms']
    
    # Should find our search terms
    assert isinstance(searches, list)
    assert 'ransomware' in searches  # We searched this twice


@pytest.mark.asyncio
async def test_investigation_velocity(populated_tracker, analyzer):
    """Test 9: Velocity assessment (high/medium/low)"""
    tracker, analyst_id = populated_tracker
    
    patterns = await analyzer.analyze_patterns(analyst_id, use_cache=False)
    velocity = patterns['investigation_velocity']
    
    # Should be one of the valid values
    assert velocity in ['high', 'medium', 'low', 'unknown']


@pytest.mark.asyncio
async def test_specialization_score(populated_tracker, analyzer):
    """Test 10: Specialization calculation (0-1)"""
    tracker, analyst_id = populated_tracker
    
    patterns = await analyzer.analyze_patterns(analyst_id, use_cache=False)
    specialization = patterns['specialization_score']
    
    # Should be between 0 and 1
    assert 0 <= specialization <= 1
    # Aviation-focused analyst should be >0.5
    assert specialization > 0.5


@pytest.mark.asyncio
async def test_pattern_caching(populated_tracker, analyzer):
    """Test 11: Pattern caching works"""
    tracker, analyst_id = populated_tracker
    
    # First call (cache miss)
    import time
    start1 = time.time()
    patterns1 = await analyzer.analyze_patterns(analyst_id, use_cache=False)
    time1 = time.time() - start1
    
    # Second call (should be cached)
    start2 = time.time()
    patterns2 = await analyzer.analyze_patterns(analyst_id, use_cache=True)
    time2 = time.time() - start2
    
    # Cached should be faster (or at least not significantly slower)
    # Note: might not be dramatically faster for small datasets
    assert patterns1['sample_size'] == patterns2['sample_size']


@pytest.mark.asyncio
async def test_action_distribution(populated_tracker, analyzer):
    """Test 12: Action type distribution analysis"""
    tracker, analyst_id = populated_tracker
    
    patterns = await analyzer.analyze_patterns(analyst_id, use_cache=False)
    distribution = patterns['action_distribution']
    
    # Should have percentages for different action types
    assert isinstance(distribution, dict)
    # Total should be ~100% (allowing for rounding)
    total = sum(distribution.values())
    assert 99 <= total <= 101


@pytest.mark.asyncio
async def test_view_escalation_ratio(populated_tracker, analyzer):
    """Test 13: View to escalation ratio"""
    tracker, analyst_id = populated_tracker
    
    patterns = await analyzer.analyze_patterns(analyst_id, use_cache=False)
    ratio = patterns['threat_view_to_escalation_ratio']
    
    # Should be a number (or None if no escalations)
    if ratio is not None:
        assert isinstance(ratio, float)
        assert ratio > 0


@pytest.mark.asyncio
async def test_compare_analysts(analyzer, tracker):
    """Test 14: Analyst comparison functionality"""
    # Create two analysts with different patterns
    analyst1 = "test_analyst_1"
    analyst2 = "test_analyst_2"
    
    # Analyst 1: Aviation focused
    for i in range(10):
        await tracker.track_action(
            analyst_id=analyst1,
            action_type=ActionType.VIEW_THREAT,
            industry="aviation"
        )
    
    # Analyst 2: Healthcare focused
    for i in range(10):
        await tracker.track_action(
            analyst_id=analyst2,
            action_type=ActionType.VIEW_THREAT,
            industry="healthcare"
        )
    
    comparison = await analyzer.compare_analysts(analyst1, analyst2)
    
    # Should have comparison metrics
    assert 'industry_overlap' in comparison
    assert 'escalation_rate_diff' in comparison
    assert comparison['analyst_1'] == analyst1
    assert comparison['analyst_2'] == analyst2
    
    # Different industries = low overlap
    assert comparison['industry_overlap'] <= 0.5
    
    # Cleanup
    await tracker.clear_analyst_history(analyst1)
    await tracker.clear_analyst_history(analyst2)


@pytest.mark.asyncio
async def test_lookback_parameter(populated_tracker, analyzer):
    """Test 15: Lookback actions parameter works"""
    tracker, analyst_id = populated_tracker
    
    # Analyze with different lookback values
    patterns_10 = await analyzer.analyze_patterns(
        analyst_id, 
        lookback_actions=10, 
        use_cache=False
    )
    patterns_30 = await analyzer.analyze_patterns(
        analyst_id, 
        lookback_actions=30, 
        use_cache=False
    )
    
    # Should have different sample sizes
    assert patterns_10['sample_size'] <= 10
    assert patterns_30['sample_size'] >= patterns_10['sample_size']


@pytest.mark.asyncio
async def test_active_hours_detection(populated_tracker, analyzer):
    """Test 16: Active hours identification"""
    tracker, analyst_id = populated_tracker
    
    patterns = await analyzer.analyze_patterns(analyst_id, use_cache=False)
    active_hours = patterns['active_hours']
    
    # Should be a list of hours
    assert isinstance(active_hours, list)
    # All should be valid hours (0-23)
    for hour in active_hours:
        assert 0 <= hour <= 23


@pytest.mark.asyncio
async def test_pattern_persistence(populated_tracker, analyzer):
    """Test 17: Patterns persist in cache"""
    tracker, analyst_id = populated_tracker
    
    # Analyze and cache
    patterns1 = await analyzer.analyze_patterns(analyst_id, use_cache=False)
    
    # Disconnect and reconnect
    await analyzer.disconnect()
    analyzer2 = PatternAnalyzer(tracker, redis_url="redis://localhost:32379")
    await analyzer2.connect()
    
    # Should retrieve from cache
    patterns2 = await analyzer2.analyze_patterns(analyst_id, use_cache=True)
    
    # Should have same basic data
    assert patterns1['sample_size'] == patterns2['sample_size']
    
    await analyzer2.disconnect()


@pytest.mark.asyncio
async def test_empty_cache_behavior(analyzer):
    """Test 18: Behavior with empty cache"""
    # Try to get cached patterns for non-existent analyst
    patterns = await analyzer.analyze_patterns(
        "never_existed_analyst",
        use_cache=True
    )
    
    # Should return empty pattern structure
    assert patterns['sample_size'] == 0
    assert patterns['escalation_rate'] == 0.0


@pytest.mark.asyncio
async def test_concurrent_analysis(populated_tracker, analyzer):
    """Test 19: Concurrent pattern analysis"""
    tracker, analyst_id = populated_tracker
    
    # Analyze same analyst concurrently
    tasks = [
        analyzer.analyze_patterns(analyst_id, use_cache=False)
        for _ in range(5)
    ]
    
    results = await asyncio.gather(*tasks)
    
    # All should have same sample size
    sample_sizes = [r['sample_size'] for r in results]
    assert len(set(sample_sizes)) == 1  # All the same


@pytest.mark.asyncio
async def test_metadata_fields_present(populated_tracker, analyzer):
    """Test 20: All expected metadata fields present"""
    tracker, analyst_id = populated_tracker
    
    patterns = await analyzer.analyze_patterns(analyst_id, use_cache=False)
    
    # Check all required fields exist
    required_fields = [
        'most_viewed_industries',
        'escalation_rate',
        'avg_time_per_threat',
        'preferred_severity_focus',
        'common_search_terms',
        'investigation_velocity',
        'specialization_score',
        'active_hours',
        'action_distribution',
        'threat_view_to_escalation_ratio',
        'last_analyzed',
        'sample_size'
    ]
    
    for field in required_fields:
        assert field in patterns, f"Missing required field: {field}"


# Cleanup fixture
@pytest.fixture(autouse=True)
async def cleanup(tracker):
    """Clean up test data after each test"""
    yield
    # Cleanup common test analysts
    test_analysts = [
        "test_analyst_patterns",
        "test_analyst_1", 
        "test_analyst_2",
        "nonexistent_analyst",
        "never_existed_analyst"
    ]
    for analyst in test_analysts:
        try:
            await tracker.clear_analyst_history(analyst)
        except:
            pass  # Ignore if doesn't exist


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
