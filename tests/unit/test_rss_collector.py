"""
Unit tests for RSS Collector
Tests RSS feed collection, parsing, and error handling
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

# Import the collector
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from collectors.rss_collector import RSSCollector


class TestRSSCollector:
    """Test suite for RSSCollector"""
    
    def test_init(self):
        """Test collector initialization"""
        collector = RSSCollector(max_workers=16)
        
        assert collector.max_workers == 16
        assert collector.sources == []
        assert collector.session is None
        assert collector.collected_items == []
        assert collector.stats['total_feeds'] == 0
    
    def test_init_default_workers(self):
        """Test default worker count"""
        collector = RSSCollector()
        assert collector.max_workers == 32
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager"""
        async with RSSCollector() as collector:
            assert collector.session is not None
            assert not collector.session.closed
        
        # Session should be closed after exit
        assert collector.session.closed
    
    def test_parse_entry_valid(self, mock_rss_source):
        """Test parsing valid RSS entry"""
        collector = RSSCollector()
        
        # Mock entry
        entry = Mock()
        entry.title = "Test Vulnerability"
        entry.link = "https://example.com/test"
        entry.summary = "Test description"
        entry.published_parsed = (2025, 11, 4, 12, 0, 0, 0, 0, 0)
        entry.tags = []
        entry.author = "Test Author"
        entry.language = "en"
        
        item = collector._parse_entry(entry, mock_rss_source)
        
        assert item is not None
        assert item['title'] == "Test Vulnerability"
        assert item['link'] == "https://example.com/test"
        assert item['content'] == "Test description"
        assert 'id' in item
        assert item['source']['name'] == 'Test Security Feed'
        assert item['source']['credibility'] == 0.9
    
    def test_parse_entry_missing_title(self, mock_rss_source):
        """Test parsing entry with missing title"""
        collector = RSSCollector()
        
        entry = Mock()
        entry.title = ""
        entry.link = "https://example.com/test"
        
        item = collector._parse_entry(entry, mock_rss_source)
        assert item is None
    
    def test_parse_entry_missing_link(self, mock_rss_source):
        """Test parsing entry with missing link"""
        collector = RSSCollector()
        
        entry = Mock()
        entry.title = "Test"
        entry.link = ""
        
        item = collector._parse_entry(entry, mock_rss_source)
        assert item is None
    
    def test_parse_entry_with_tags(self, mock_rss_source):
        """Test parsing entry with tags"""
        collector = RSSCollector()
        
        entry = Mock()
        entry.title = "Test"
        entry.link = "https://example.com/test"
        entry.summary = "Test"
        entry.published_parsed = (2025, 11, 4, 12, 0, 0, 0, 0, 0)
        
        # Mock tags
        tag1 = Mock()
        tag1.term = "vulnerability"
        tag2 = Mock()
        tag2.term = "critical"
        entry.tags = [tag1, tag2]
        entry.author = ""
        entry.language = "en"
        
        item = collector._parse_entry(entry, mock_rss_source)
        
        assert 'vulnerability' in item['tags']
        assert 'critical' in item['tags']
        assert 'test' in item['tags']  # From source
    
    @pytest.mark.asyncio
    async def test_fetch_feed_success(self, mock_rss_source, mock_rss_feed):
        """Test successful feed fetch"""
        collector = RSSCollector()
        
        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=mock_rss_feed)
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        collector.session = mock_session
        
        result = await collector.fetch_feed(mock_rss_source)
        
        assert result['success'] is True
        assert len(result['items']) > 0
        assert result['source'] == mock_rss_source
    
    @pytest.mark.asyncio
    async def test_fetch_feed_http_error(self, mock_rss_source):
        """Test feed fetch with HTTP error"""
        collector = RSSCollector()
        
        # Mock 404 response
        mock_response = AsyncMock()
        mock_response.status = 404
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        collector.session = mock_session
        
        result = await collector.fetch_feed(mock_rss_source)
        
        assert result['success'] is False
        assert result['error'] == "HTTP 404"
        assert len(result['items']) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_feed_timeout(self, mock_rss_source):
        """Test feed fetch timeout"""
        collector = RSSCollector()
        
        # Mock timeout
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(side_effect=asyncio.TimeoutError())
        
        collector.session = mock_session
        
        result = await collector.fetch_feed(mock_rss_source)
        
        assert result['success'] is False
        assert result['error'] == 'Timeout'
        assert len(result['items']) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_feed_exception(self, mock_rss_source):
        """Test feed fetch with general exception"""
        collector = RSSCollector()
        
        # Mock exception
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(side_effect=Exception("Network error"))
        
        collector.session = mock_session
        
        result = await collector.fetch_feed(mock_rss_source)
        
        assert result['success'] is False
        assert 'Network error' in result['error']
        assert len(result['items']) == 0
    
    def test_stats_initialization(self):
        """Test stats are properly initialized"""
        collector = RSSCollector()
        
        assert 'total_feeds' in collector.stats
        assert 'successful_feeds' in collector.stats
        assert 'failed_feeds' in collector.stats
        assert 'total_items' in collector.stats
        assert 'start_time' in collector.stats
        assert 'end_time' in collector.stats
        
        assert collector.stats['total_feeds'] == 0
        assert collector.stats['successful_feeds'] == 0
        assert collector.stats['failed_feeds'] == 0
        assert collector.stats['total_items'] == 0


class TestRSSCollectorIntegration:
    """Integration tests for RSS Collector"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_collection_cycle(self, tmp_path):
        """Test complete collection cycle"""
        # This would test with real feeds in integration environment
        # Skipped in unit tests
        pass
    
    @pytest.mark.integration
    def test_load_sources_from_config(self, temp_config_dir):
        """Test loading sources from actual config file"""
        # This would test with real config file
        # Skipped in unit tests
        pass
