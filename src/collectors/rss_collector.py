"""
cyber-pi RSS Feed Collector
Massive parallel RSS feed collection with 32-worker architecture
"""

import asyncio
import aiohttp
import feedparser
import yaml
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
import json

# Import configuration
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RSSCollector:
    """
    High-performance RSS feed collector with massive parallelization
    Collects from 100+ cybersecurity intelligence sources
    """
    
    def __init__(self, max_workers: int = 32):
        self.max_workers = max_workers
        self.sources = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.collected_items = []
        self.stats = {
            'total_feeds': 0,
            'successful_feeds': 0,
            'failed_feeds': 0,
            'total_items': 0,
            'start_time': None,
            'end_time': None
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.rss_timeout),
            headers={'User-Agent': 'cyber-pi/1.0 (Enterprise Threat Intelligence)'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def load_sources(self, categories: List[str] = None) -> None:
        """
        Load RSS sources from configuration
        
        Args:
            categories: List of categories to load (None = all)
        """
        config_path = Path(__file__).parent.parent.parent / 'config' / 'sources.yaml'
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Loaded configuration from {config_path}")
            
            # Extract RSS sources from all categories
            for category_name, category_data in config.items():
                if category_name == 'collection_settings':
                    continue
                    
                if categories and category_name not in categories:
                    continue
                
                if not isinstance(category_data, dict) or 'sources' not in category_data:
                    continue
                
                for source in category_data['sources']:
                    if source.get('type') == 'rss':
                        self.sources.append({
                            'name': source['name'],
                            'url': source['url'],
                            'category': category_name,
                            'credibility': source.get('credibility', 0.7),
                            'tags': source.get('tags', []),
                            'priority': category_data.get('priority', 'medium')
                        })
            
            self.stats['total_feeds'] = len(self.sources)
            logger.info(f"Loaded {len(self.sources)} RSS sources")
            
            # Log sources by category
            categories_count = {}
            for source in self.sources:
                cat = source['category']
                categories_count[cat] = categories_count.get(cat, 0) + 1
            
            for cat, count in categories_count.items():
                logger.info(f"  {cat}: {count} sources")
                
        except Exception as e:
            logger.error(f"Failed to load sources: {e}")
            raise
    
    async def fetch_feed(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch and parse a single RSS feed
        
        Args:
            source: Source configuration dictionary
            
        Returns:
            Dictionary with feed data and metadata
        """
        try:
            logger.debug(f"Fetching: {source['name']}")
            
            async with self.session.get(source['url']) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {source['name']}")
                    return {
                        'source': source,
                        'success': False,
                        'error': f"HTTP {response.status}",
                        'items': []
                    }
                
                content = await response.text()
                
                # Parse RSS feed
                feed = feedparser.parse(content)
                
                if feed.bozo:
                    logger.warning(f"Feed parsing warning for {source['name']}: {feed.bozo_exception}")
                
                # Extract items
                items = []
                for entry in feed.entries:
                    item = self._parse_entry(entry, source)
                    if item:
                        items.append(item)
                
                logger.info(f"✓ {source['name']}: {len(items)} items")
                
                return {
                    'source': source,
                    'success': True,
                    'items': items,
                    'feed_title': feed.feed.get('title', source['name']),
                    'feed_updated': feed.feed.get('updated', None)
                }
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {source['name']}")
            return {
                'source': source,
                'success': False,
                'error': 'Timeout',
                'items': []
            }
        except Exception as e:
            logger.error(f"Error fetching {source['name']}: {e}")
            return {
                'source': source,
                'success': False,
                'error': str(e),
                'items': []
            }
    
    def _parse_entry(self, entry: Any, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a single RSS entry into standardized format
        
        Args:
            entry: feedparser entry object
            source: Source configuration
            
        Returns:
            Standardized item dictionary or None
        """
        try:
            # Extract basic fields
            title = entry.get('title', '').strip()
            link = entry.get('link', '').strip()
            
            if not title or not link:
                return None
            
            # Generate unique ID
            item_id = hashlib.sha256(f"{link}{title}".encode()).hexdigest()[:16]
            
            # Extract content
            content = ''
            if hasattr(entry, 'content'):
                content = entry.content[0].value
            elif hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description
            
            # Extract published date
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            else:
                published = datetime.now(timezone.utc)
            
            # Extract tags/categories
            tags = source.get('tags', []).copy()
            if hasattr(entry, 'tags'):
                tags.extend([tag.term for tag in entry.tags])
            
            # Build standardized item
            item = {
                'id': item_id,
                'title': title,
                'link': link,
                'content': content,
                'published': published.isoformat(),
                'collected': datetime.now(timezone.utc).isoformat(),
                'source': {
                    'name': source['name'],
                    'url': source['url'],
                    'category': source['category'],
                    'credibility': source['credibility'],
                    'priority': source['priority']
                },
                'tags': list(set(tags)),  # Deduplicate
                'metadata': {
                    'author': entry.get('author', ''),
                    'language': entry.get('language', 'en')
                }
            }
            
            return item
            
        except Exception as e:
            logger.error(f"Error parsing entry: {e}")
            return None
    
    async def collect_parallel(self, batch_size: int = None) -> List[Dict[str, Any]]:
        """
        Collect from all sources in parallel with worker pool
        
        Args:
            batch_size: Number of concurrent requests (default: max_workers)
            
        Returns:
            List of all collected items
        """
        if not self.sources:
            logger.warning("No sources loaded")
            return []
        
        batch_size = batch_size or self.max_workers
        self.stats['start_time'] = datetime.now(timezone.utc)
        
        logger.info(f"Starting parallel collection from {len(self.sources)} sources")
        logger.info(f"Using {batch_size} concurrent workers")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(batch_size)
        
        async def fetch_with_semaphore(source):
            async with semaphore:
                return await self.fetch_feed(source)
        
        # Fetch all feeds in parallel
        tasks = [fetch_with_semaphore(source) for source in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        all_items = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed with exception: {result}")
                self.stats['failed_feeds'] += 1
                continue
            
            if result['success']:
                self.stats['successful_feeds'] += 1
                all_items.extend(result['items'])
            else:
                self.stats['failed_feeds'] += 1
        
        self.stats['total_items'] = len(all_items)
        self.stats['end_time'] = datetime.now(timezone.utc)
        
        # Calculate duration
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        logger.info(f"Collection complete in {duration:.2f}s")
        logger.info(f"  Successful: {self.stats['successful_feeds']}/{self.stats['total_feeds']}")
        logger.info(f"  Failed: {self.stats['failed_feeds']}")
        logger.info(f"  Total items: {self.stats['total_items']}")
        logger.info(f"  Rate: {self.stats['total_items']/duration:.1f} items/sec")
        
        self.collected_items = all_items
        return all_items
    
    def save_to_json(self, filepath: str = None) -> str:
        """
        Save collected items to JSON file
        
        Args:
            filepath: Output file path (default: data/raw/rss_TIMESTAMP.json)
            
        Returns:
            Path to saved file
        """
        if not filepath:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            filepath = f"{settings.raw_data_dir}/rss_{timestamp}.json"
        
        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare data
        data = {
            'metadata': {
                'collected_at': datetime.now(timezone.utc).isoformat(),
                'total_items': len(self.collected_items),
                'stats': self.stats
            },
            'items': self.collected_items
        }
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Saved {len(self.collected_items)} items to {filepath}")
        return filepath
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        return self.stats.copy()


async def main():
    """
    Main function for testing RSS collector
    """
    logger.info("🚀 cyber-pi RSS Collector")
    logger.info("=" * 60)
    
    # Create collector
    async with RSSCollector(max_workers=32) as collector:
        # Load sources (start with just a few categories for testing)
        logger.info("Loading sources...")
        collector.load_sources(categories=['government', 'technical', 'news_research'])
        
        # Collect in parallel
        logger.info("Starting parallel collection...")
        items = await collector.collect_parallel()
        
        # Save results
        if items:
            filepath = collector.save_to_json()
            logger.info(f"✓ Results saved to: {filepath}")
        
        # Display stats
        stats = collector.get_stats()
        logger.info("\n" + "=" * 60)
        logger.info("COLLECTION STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total Feeds: {stats['total_feeds']}")
        logger.info(f"Successful: {stats['successful_feeds']}")
        logger.info(f"Failed: {stats['failed_feeds']}")
        logger.info(f"Total Items: {stats['total_items']}")
        
        if stats['start_time'] and stats['end_time']:
            duration = (stats['end_time'] - stats['start_time']).total_seconds()
            logger.info(f"Duration: {duration:.2f}s")
            logger.info(f"Rate: {stats['total_items']/duration:.1f} items/sec")
        
        # Show sample items
        if items:
            logger.info("\n" + "=" * 60)
            logger.info("SAMPLE ITEMS (first 3)")
            logger.info("=" * 60)
            for i, item in enumerate(items[:3], 1):
                logger.info(f"\n{i}. {item['title']}")
                logger.info(f"   Source: {item['source']['name']}")
                logger.info(f"   Category: {item['source']['category']}")
                logger.info(f"   Published: {item['published']}")
                logger.info(f"   Link: {item['link']}")
                logger.info(f"   Tags: {', '.join(item['tags'][:5])}")


if __name__ == "__main__":
    asyncio.run(main())
