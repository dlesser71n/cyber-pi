"""
Pytest configuration and fixtures for Cyber-PI tests
"""

import pytest
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


@pytest.fixture
def test_env():
    """Set up test environment variables"""
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ['REDIS_PASSWORD'] = 'test-redis-password'
    os.environ['NEO4J_PASSWORD'] = 'test-neo4j-password'
    os.environ['ENVIRONMENT'] = 'test'
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_rss_feed() -> str:
    """Mock RSS feed XML for testing"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Test Security Feed</title>
        <link>https://example.com</link>
        <description>Test feed for unit tests</description>
        <item>
            <title>Critical Vulnerability in Test Software</title>
            <link>https://example.com/vuln-001</link>
            <description>A critical vulnerability has been discovered</description>
            <pubDate>Mon, 04 Nov 2025 12:00:00 GMT</pubDate>
            <category>vulnerability</category>
        </item>
        <item>
            <title>New Threat Actor Identified</title>
            <link>https://example.com/threat-001</link>
            <description>Security researchers have identified a new threat actor</description>
            <pubDate>Mon, 04 Nov 2025 13:00:00 GMT</pubDate>
            <category>threat-intelligence</category>
        </item>
    </channel>
</rss>"""


@pytest.fixture
def mock_rss_source() -> Dict[str, Any]:
    """Mock RSS source configuration"""
    return {
        'name': 'Test Security Feed',
        'url': 'https://example.com/feed.xml',
        'category': 'test',
        'credibility': 0.9,
        'tags': ['test', 'security'],
        'priority': 'high'
    }


@pytest.fixture
def mock_threat_data() -> Dict[str, Any]:
    """Mock threat intelligence data"""
    return {
        'id': 'test-threat-001',
        'title': 'Test Threat',
        'description': 'This is a test threat for unit testing',
        'severity': 'high',
        'confidence': 0.85,
        'indicators': ['192.168.1.1', 'malware.example.com'],
        'tags': ['malware', 'apt', 'test']
    }


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory"""
    config_dir = tmp_path / 'config'
    config_dir.mkdir()
    return config_dir
