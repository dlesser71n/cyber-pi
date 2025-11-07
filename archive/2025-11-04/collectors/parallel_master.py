"""
cyber-pi Parallel Master Orchestrator
Coordinates all collection mediums in massive parallel operation
RSS + Web Scraping + Public APIs running simultaneously
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
import json
from pathlib import Path

# Import all collectors
from rss_collector import RSSCollector
from web_scraper import create_scraper
from api_collector import PublicAPICollector

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


class ParallelMasterOrchestrator:
    """
    Master orchestrator for all intelligence collection
    Runs RSS, Web Scraping, and APIs in parallel
    """
    
    def __init__(self):
        self.stats = {
            'start_time': None,
            'end_time': None,
            'rss': {'items': 0, 'sources': 0, 'success': 0, 'failed': 0},
            'web_scraping': {'items': 0, 'sources': 0, 'success': 0, 'failed': 0},
            'apis': {'items': 0, 'sources': 0, 'success': 0, 'failed': 0},
            'total_items': 0,
            'total_sources': 0
        }
        self.all_items = []
        
    async def collect_rss(self, categories: List[str] = None) -> List[Dict[str, Any]]:
        """
        Collect from RSS feeds
        
        Args:
            categories: Categories to collect from
            
        Returns:
            List of collected items
        """
        logger.info("🔄 Starting RSS collection...")
        
        try:
            async with RSSCollector(max_workers=32) as collector:
                # Load sources
                collector.load_sources(categories=categories)
                self.stats['rss']['sources'] = len(collector.sources)
                
                # Collect in parallel
                items = await collector.collect_parallel(batch_size=32)
                
                # Update stats
                stats = collector.get_stats()
                self.stats['rss']['items'] = len(items)
                self.stats['rss']['success'] = stats['successful_feeds']
                self.stats['rss']['failed'] = stats['failed_feeds']
                
                logger.info(f"✓ RSS: {len(items)} items from {stats['successful_feeds']} sources")
                return items
                
        except Exception as e:
            logger.error(f"RSS collection failed: {e}")
            return []
    
    async def collect_web_scraping(self, urls: List[str] = None) -> List[Dict[str, Any]]:
        """
        Collect from web scraping
        
        Args:
            urls: URLs to scrape (if None, uses configured sources)
            
        Returns:
            List of collected items
        """
        logger.info("🔄 Starting web scraping...")
        
        try:
            # Default URLs if none provided
            if not urls:
                urls = [
                    "https://krebsonsecurity.com/",
                    "https://thehackernews.com/",
                    "https://www.bleepingcomputer.com/",
                    "https://www.darkreading.com/",
                    "https://threatpost.com/"
                ]
            
            scraper = create_scraper("trafilatura")
            results = await scraper.batch_scrape(urls, max_concurrent=8)
            
            # Convert to standard format
            items = []
            for result in results:
                if result.success:
                    item = {
                        'id': result.url,
                        'title': result.title,
                        'content': result.content,
                        'url': result.url,
                        'author': result.author,
                        'published': result.publish_date.isoformat() if result.publish_date else None,
                        'collected': result.extraction_time.isoformat(),
                        'source': {
                            'name': result.scraper_used,
                            'type': 'web_scrape',
                            'credibility': 0.75
                        },
                        'tags': ['web_scrape', 'article']
                    }
                    items.append(item)
            
            # Update stats
            self.stats['web_scraping']['sources'] = len(urls)
            self.stats['web_scraping']['items'] = len(items)
            self.stats['web_scraping']['success'] = len(items)
            self.stats['web_scraping']['failed'] = len(urls) - len(items)
            
            logger.info(f"✓ Web Scraping: {len(items)} items from {len(urls)} sources")
            return items
            
        except Exception as e:
            logger.error(f"Web scraping failed: {e}")
            return []
    
    async def collect_apis(self) -> List[Dict[str, Any]]:
        """
        Collect from public APIs
        
        Returns:
            List of collected items
        """
        logger.info("🔄 Starting API collection...")
        
        try:
            async with PublicAPICollector(max_workers=8) as collector:
                items = await collector.collect_all()
                
                # Update stats
                stats = collector.get_stats()
                self.stats['apis']['sources'] = 3  # NIST, MITRE, CVE Details
                self.stats['apis']['items'] = len(items)
                self.stats['apis']['success'] = stats['successful_apis']
                self.stats['apis']['failed'] = stats['failed_apis']
                
                logger.info(f"✓ APIs: {len(items)} items from {stats['successful_apis']} sources")
                return items
                
        except Exception as e:
            logger.error(f"API collection failed: {e}")
            return []
    
    async def collect_all(self, 
                         rss_categories: List[str] = None,
                         web_urls: List[str] = None) -> Dict[str, Any]:
        """
        Collect from all sources in parallel
        
        Args:
            rss_categories: RSS categories to collect
            web_urls: URLs to scrape
            
        Returns:
            Dictionary with all collected data and statistics
        """
        self.stats['start_time'] = datetime.now(timezone.utc)
        
        logger.info("=" * 80)
        logger.info("🚀 CYBER-PI PARALLEL MASTER ORCHESTRATOR")
        logger.info("=" * 80)
        logger.info("Starting massive parallel intelligence collection...")
        logger.info(f"Hardware: {settings.cpu_cores} cores, {settings.total_ram}GB RAM")
        logger.info(f"Max workers: {settings.max_workers}")
        logger.info("")
        
        # Run all collectors in parallel
        logger.info("⚡ Launching parallel collection tasks...")
        tasks = [
            self.collect_rss(categories=rss_categories),
            self.collect_web_scraping(urls=web_urls),
            self.collect_apis()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Collection task {i} failed: {result}")
            elif result:
                self.all_items.extend(result)
        
        self.stats['end_time'] = datetime.now(timezone.utc)
        self.stats['total_items'] = len(self.all_items)
        self.stats['total_sources'] = (
            self.stats['rss']['sources'] + 
            self.stats['web_scraping']['sources'] + 
            self.stats['apis']['sources']
        )
        
        return {
            'items': self.all_items,
            'stats': self.stats
        }
    
    def save_results(self, filepath: str = None) -> str:
        """
        Save all collected intelligence to JSON
        
        Args:
            filepath: Output file path
            
        Returns:
            Path to saved file
        """
        if not filepath:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            filepath = f"{settings.raw_data_dir}/master_collection_{timestamp}.json"
        
        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare data
        data = {
            'metadata': {
                'collected_at': datetime.now(timezone.utc).isoformat(),
                'collection_system': 'cyber-pi Parallel Master',
                'version': '1.0.0',
                'stats': self.stats
            },
            'items': self.all_items
        }
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"💾 Saved {len(self.all_items)} items to {filepath}")
        return filepath
    
    def print_summary(self):
        """Print collection summary"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("📊 COLLECTION SUMMARY")
        logger.info("=" * 80)
        
        # Overall stats
        logger.info(f"Duration: {duration:.2f}s")
        logger.info(f"Total Sources: {self.stats['total_sources']}")
        logger.info(f"Total Items: {self.stats['total_items']}")
        logger.info(f"Collection Rate: {self.stats['total_items']/duration:.1f} items/sec")
        logger.info("")
        
        # RSS stats
        logger.info("📰 RSS Feeds:")
        logger.info(f"  Sources: {self.stats['rss']['sources']}")
        logger.info(f"  Success: {self.stats['rss']['success']}")
        logger.info(f"  Failed: {self.stats['rss']['failed']}")
        logger.info(f"  Items: {self.stats['rss']['items']}")
        logger.info("")
        
        # Web scraping stats
        logger.info("🌐 Web Scraping:")
        logger.info(f"  Sources: {self.stats['web_scraping']['sources']}")
        logger.info(f"  Success: {self.stats['web_scraping']['success']}")
        logger.info(f"  Failed: {self.stats['web_scraping']['failed']}")
        logger.info(f"  Items: {self.stats['web_scraping']['items']}")
        logger.info("")
        
        # API stats
        logger.info("🔌 Public APIs:")
        logger.info(f"  Sources: {self.stats['apis']['sources']}")
        logger.info(f"  Success: {self.stats['apis']['success']}")
        logger.info(f"  Failed: {self.stats['apis']['failed']}")
        logger.info(f"  Items: {self.stats['apis']['items']}")
        logger.info("")
        
        logger.info("=" * 80)
        logger.info("✅ COLLECTION COMPLETE")
        logger.info("=" * 80)


async def main():
    """
    Main function - runs full parallel collection
    """
    # Create orchestrator
    orchestrator = ParallelMasterOrchestrator()
    
    # Run collection (use specific categories to avoid overwhelming on first run)
    result = await orchestrator.collect_all(
        rss_categories=['news_research', 'nexum_vendors', 'technical'],
        web_urls=None  # Use defaults
    )
    
    # Save results
    filepath = orchestrator.save_results()
    
    # Print summary
    orchestrator.print_summary()
    
    # Show sample items
    if result['items']:
        logger.info("")
        logger.info("=" * 80)
        logger.info("📋 SAMPLE INTELLIGENCE (First 5 items)")
        logger.info("=" * 80)
        
        for i, item in enumerate(result['items'][:5], 1):
            logger.info(f"\n{i}. {item.get('title', 'No title')[:80]}")
            logger.info(f"   Source: {item['source'].get('name', 'Unknown')}")
            logger.info(f"   Type: {item['source'].get('type', 'Unknown')}")
            logger.info(f"   Credibility: {item['source'].get('credibility', 0.0)}")


if __name__ == "__main__":
    asyncio.run(main())
