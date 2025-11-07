#!/usr/bin/env python3
"""
Quick test of RSS collector
Tests with just a few sources to verify functionality
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from collectors.rss_collector import RSSCollector

async def quick_test():
    """Quick test with minimal sources"""
    print("🧪 Testing RSS Collector")
    print("=" * 60)
    
    async with RSSCollector(max_workers=8) as collector:
        # Load news and technical sources (excluding government/vulnerabilities)
        print("\n📥 Loading sources...")
        collector.load_sources(categories=['news_research', 'technical', 'nexum_vendors'])
        
        print(f"✓ Loaded {len(collector.sources)} sources")
        
        # Collect
        print("\n🔄 Starting collection...")
        items = await collector.collect_parallel(batch_size=8)
        
        # Results
        print("\n" + "=" * 60)
        print("✅ RESULTS")
        print("=" * 60)
        stats = collector.get_stats()
        print(f"Feeds processed: {stats['successful_feeds']}/{stats['total_feeds']}")
        print(f"Items collected: {stats['total_items']}")
        
        if items:
            print(f"\n📰 Sample items:")
            for i, item in enumerate(items[:3], 1):
                print(f"\n{i}. {item['title'][:80]}...")
                print(f"   Source: {item['source']['name']}")
                print(f"   Link: {item['link']}")
        
        return len(items) > 0

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)
