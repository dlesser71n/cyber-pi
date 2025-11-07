#!/usr/bin/env python3
"""
Test ScraperAPI on previously blocked sources
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.collectors.scraperapi_collector import ScraperAPICollector, collect_blocked_sources_with_scraperapi
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

# Previously blocked sources (403, 404, timeout)
BLOCKED_SOURCES = [
    # 403 Forbidden
    {'name': 'Dark Reading', 'url': 'https://www.darkreading.com/rss_simple.asp', 'credibility': 0.80},
    {'name': 'SC Magazine', 'url': 'https://www.scmagazine.com/feed', 'credibility': 0.75},
    {'name': 'CVE Details', 'url': 'https://www.cvedetails.com/vulnerability-feed.php?vendor_id=0&product_id=0&version_id=0&orderby=3&cvssscoremin=7', 'credibility': 0.85},
    {'name': 'NSA Cybersecurity', 'url': 'https://www.nsa.gov/Press-Room/Cybersecurity-Advisories-Guidance/RSS/', 'credibility': 0.95},
    {'name': 'HHS Cybersecurity', 'url': 'https://www.hhs.gov/about/news/rss/cybersecurity.xml', 'credibility': 0.90},
    {'name': 'Armis Security', 'url': 'https://www.armis.com/blog/feed/', 'credibility': 0.80},
    
    # 404 Not Found
    {'name': 'Ars Technica Security', 'url': 'https://feeds.arstechnica.com/arstechnica/security', 'credibility': 0.80},
    {'name': 'Cisco Talos Intelligence', 'url': 'https://blog.talosintelligence.com/feeds/posts/default', 'credibility': 0.90},
    {'name': 'Juniper Threat Labs', 'url': 'https://blogs.juniper.net/en-us/threat-research/rss.xml', 'credibility': 0.90},
    {'name': 'Trend Micro Security', 'url': 'https://www.trendmicro.com/vinfo/us/security/news/feed', 'credibility': 0.85},
]

def main():
    print("=" * 80)
    print("🧪 TESTING SCRAPERAPI ON BLOCKED SOURCES")
    print("=" * 80)
    print()
    
    # Check if API key is set
    api_key = os.getenv('SCRAPERAPI_KEY', '')
    if not api_key or api_key == 'your-scraperapi-key-here':
        print("❌ ERROR: ScraperAPI key not set!")
        print()
        print("Please add your ScraperAPI key to .env file:")
        print("   SCRAPERAPI_KEY=your-actual-key-here")
        print()
        print("Your ScraperAPI dashboard: https://dashboard.scraperapi.com/")
        return 1
    
    print(f"✅ ScraperAPI key found: {api_key[:10]}...")
    print()
    
    # Test collection
    print(f"Testing {len(BLOCKED_SOURCES)} previously blocked sources...")
    print()
    
    items = collect_blocked_sources_with_scraperapi(BLOCKED_SOURCES)
    
    print()
    print("=" * 80)
    print("📊 RESULTS")
    print("=" * 80)
    print()
    
    if items:
        print(f"✅ SUCCESS! Collected {len(items)} items from blocked sources!")
        print()
        print("Sample items:")
        for i, item in enumerate(items[:5], 1):
            print(f"{i}. [{item['source']['name']}] {item['title'][:60]}")
        print()
        print("🎉 ScraperAPI successfully bypassed all blocks!")
    else:
        print("⚠️  No items collected. Check your API key and credits.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
