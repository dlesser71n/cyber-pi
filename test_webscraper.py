#!/usr/bin/env python3
"""
Quick test of Web Scraper
Tests with a few cybersecurity news sites
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from collectors.web_scraper import create_scraper, ScraperType

async def quick_test():
    """Quick test with a few URLs"""
    print("🧪 Testing Web Scraper")
    print("=" * 60)
    
    # Test URLs from cybersecurity sites
    test_urls = [
        "https://krebsonsecurity.com/",
        "https://thehackernews.com/",
        "https://www.bleepingcomputer.com/"
    ]
    
    # Create scraper (trafilatura is best for most cases)
    scraper = create_scraper("trafilatura")
    
    print(f"\n📥 Scraping {len(test_urls)} URLs...")
    print(f"Using scraper: trafilatura")
    
    # Batch scrape
    results = await scraper.batch_scrape(test_urls, max_concurrent=3)
    
    # Results
    print("\n" + "=" * 60)
    print("✅ RESULTS")
    print("=" * 60)
    
    successful = sum(1 for r in results if r.success)
    print(f"Successful: {successful}/{len(results)}")
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.title[:80]}")
        print(f"   URL: {result.url}")
        print(f"   Success: {result.success}")
        print(f"   Scraper: {result.scraper_used}")
        print(f"   Content length: {len(result.content)} chars")
        if result.author:
            print(f"   Author: {result.author}")
        if result.publish_date:
            print(f"   Published: {result.publish_date}")
    
    return successful > 0

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)
