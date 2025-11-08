#!/usr/bin/env python3
"""
Quick integration test - checks if monitored integration can initialize
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from cyber_pi_periscope_integration_monitored import MonitoredCyberPiPeriscopeIntegration


async def test_integration():
    """Test monitored integration initialization"""
    print("🧪 Testing MonitoredCyberPiPeriscopeIntegration...")
    
    # Create integration (monitoring enabled but won't connect to Redis yet)
    integration = MonitoredCyberPiPeriscopeIntegration(
        redis_host="localhost",
        redis_port=32379,
        enable_monitoring=True
    )
    
    print("✅ Integration created")
    
    # Test threat conversion (doesn't need Redis)
    test_item = {
        'source': 'test',
        'title': 'Critical Zero-Day Exploit',
        'description': 'Test threat',
        'tags': ['critical', 'exploit'],
        'url': 'https://example.com/test'
    }
    
    threat = integration._convert_to_periscope_threat(test_item)
    
    assert threat is not None
    assert threat['severity'] == 'CRITICAL'
    assert 'threat_id' in threat
    
    print("✅ Threat conversion works")
    
    # Test threat ID generation
    threat_id = integration._generate_threat_id(test_item)
    assert threat_id.startswith('threat_')
    assert len(threat_id) == 19  # threat_ + 12 char hash
    
    print("✅ Threat ID generation works")
    
    # Test severity determination
    assert integration._determine_severity({'title': '0-day exploit', 'tags': []}) == 'CRITICAL'
    assert integration._determine_severity({'title': 'vulnerability found', 'tags': []}) == 'HIGH'
    assert integration._determine_severity({'title': 'security advisory', 'tags': []}) == 'MEDIUM'
    assert integration._determine_severity({'title': 'general news', 'tags': []}) == 'LOW'
    
    print("✅ Severity determination works")
    
    # Check monitoring is enabled
    assert integration.monitor is not None
    print("✅ Monitoring is enabled")
    
    print("\n✅ ALL INTEGRATION TESTS PASSED!")
    return True


if __name__ == "__main__":
    try:
        asyncio.run(test_integration())
        print("\n🎯 MonitoredCyberPiPeriscopeIntegration is working correctly!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
