"""
ScraperAPI Integration for cyber-pi
Uses your existing ScraperAPI subscription to bypass all blocks
"""

import requests
import feedparser
from typing import Dict, List, Optional
import logging
import os

logger = logging.getLogger(__name__)

# Get ScraperAPI key from environment
SCRAPERAPI_KEY = os.getenv('SCRAPERAPI_KEY', '')


class ScraperAPICollector:
    """
    RSS collector using ScraperAPI to bypass all blocks
    
    ScraperAPI handles:
    - Proxy rotation
    - Browser fingerprinting
    - CAPTCHA solving
    - Anti-bot bypass
    - Geographic targeting
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or SCRAPERAPI_KEY
        if not self.api_key:
            raise ValueError("ScraperAPI key not found! Set SCRAPERAPI_KEY environment variable")
        
        self.base_url = "http://api.scraperapi.com"
        logger.info(f"✅ ScraperAPI initialized")
    
    def fetch_with_scraperapi(self, url: str, render_js: bool = False) -> Optional[str]:
        """
        Fetch URL content using ScraperAPI
        
        Args:
            url: Target URL to scrape
            render_js: Whether to render JavaScript (costs more credits)
        
        Returns:
            HTML/RSS content as string
        """
        try:
            params = {
                'api_key': self.api_key,
                'url': url,
            }
            
            # Optional: render JavaScript (for dynamic content)
            if render_js:
                params['render'] = 'true'
            
            logger.info(f"📡 Fetching via ScraperAPI: {url}")
            response = requests.get(self.base_url, params=params, timeout=60)
            
            if response.status_code == 200:
                logger.info(f"✅ Success: {url}")
                return response.text
            else:
                logger.error(f"❌ ScraperAPI error {response.status_code}: {url}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Exception: {url} - {str(e)}")
            return None
    
    def collect_rss(self, source: Dict) -> List[Dict]:
        """
        Collect RSS feed using ScraperAPI
        
        Args:
            source: Source dict with 'name', 'url', 'credibility'
        
        Returns:
            List of parsed items
        """
        url = source['url']
        name = source['name']
        
        logger.info(f"🚀 Collecting via ScraperAPI: {name}")
        
        # Fetch RSS content via ScraperAPI
        content = self.fetch_with_scraperapi(url, render_js=False)
        
        if not content:
            logger.warning(f"⚠️  No content received: {name}")
            return []
        
        # Parse RSS/Atom feed
        feed = feedparser.parse(content)
        
        if not feed.entries:
            logger.warning(f"⚠️  No entries found: {name}")
            return []
        
        # Parse entries
        items = []
        for entry in feed.entries:  # Collect ALL items - filter by intelligence, not arbitrary limits
            try:
                items.append({
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'description': entry.get('summary', entry.get('description', ''))[:500],
                    'published': entry.get('published', entry.get('updated', '')),
                    'source': {
                        'name': source['name'],
                        'type': source.get('type', 'rss'),
                        'credibility': source.get('credibility', 0.75)
                    }
                })
            except Exception as e:
                logger.warning(f"Error parsing entry: {str(e)[:50]}")
                continue
        
        logger.info(f"✅ Collected {len(items)} items: {name}")
        return items
    
    def check_credits(self) -> Dict:
        """
        Check remaining ScraperAPI credits
        
        Returns:
            Dict with credit info
        """
        try:
            response = requests.get(
                'https://api.scraperapi.com/account',
                params={'api_key': self.api_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"💳 ScraperAPI Credits:")
                logger.info(f"   Used: {data.get('requestCount', 'N/A')}")
                logger.info(f"   Limit: {data.get('requestLimit', 'N/A')}")
                logger.info(f"   Remaining: {data.get('requestLimit', 0) - data.get('requestCount', 0)}")
                return data
            else:
                logger.error(f"❌ Could not check credits: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error checking credits: {str(e)}")
            return {}


def collect_blocked_sources_with_scraperapi(blocked_sources: List[Dict]) -> List[Dict]:
    """
    Collect from previously blocked sources using ScraperAPI
    
    Args:
        blocked_sources: List of source dicts that failed with regular requests
    
    Returns:
        Combined list of all collected items
    """
    
    collector = ScraperAPICollector()
    
    # Check credits first
    collector.check_credits()
    
    all_items = []
    success_count = 0
    
    for source in blocked_sources:
        items = collector.collect_rss(source)
        if items:
            all_items.extend(items)
            success_count += 1
    
    logger.info(f"\n📊 ScraperAPI Collection Summary:")
    logger.info(f"   Sources attempted: {len(blocked_sources)}")
    logger.info(f"   Sources successful: {success_count}")
    logger.info(f"   Total items: {len(all_items)}")
    logger.info(f"   Success rate: {success_count/len(blocked_sources)*100:.1f}%")
    
    return all_items


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test on blocked sources
    test_sources = [
        {
            'name': 'Dark Reading',
            'url': 'https://www.darkreading.com/rss_simple.asp',
            'credibility': 0.80
        },
        {
            'name': 'SC Magazine',
            'url': 'https://www.scmagazine.com/feed',
            'credibility': 0.75
        },
        {
            'name': 'NSA Cybersecurity',
            'url': 'https://www.nsa.gov/Press-Room/Cybersecurity-Advisories-Guidance/RSS/',
            'credibility': 0.95
        }
    ]
    
    items = collect_blocked_sources_with_scraperapi(test_sources)
    
    if items:
        print(f"\n✅ Successfully collected {len(items)} items!")
        print(f"\nFirst item:")
        print(f"  Title: {items[0]['title']}")
        print(f"  Source: {items[0]['source']['name']}")
