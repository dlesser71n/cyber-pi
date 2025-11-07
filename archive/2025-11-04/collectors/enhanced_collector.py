"""
Enhanced RSS Collector with Multiple Fallback Strategies
Handles 403, 404, and timeout errors with browser-like requests
"""

import requests
from bs4 import BeautifulSoup
import feedparser
import time
import random
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Browser-like headers to avoid blocks
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0'
}


def respectful_delay():
    """Add random delay to be respectful to servers"""
    time.sleep(random.uniform(0.5, 2.0))


def try_rss_with_headers(url: str, timeout: int = 30) -> Optional[feedparser.FeedParserDict]:
    """Try to fetch RSS with browser-like headers"""
    try:
        respectful_delay()
        response = requests.get(url, headers=BROWSER_HEADERS, timeout=timeout)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            if feed.entries:
                logger.info(f"✅ RSS success: {url}")
                return feed
        elif response.status_code == 429:
            # Rate limited - wait and retry
            wait_time = int(response.headers.get('Retry-After', 60))
            logger.warning(f"⏳ Rate limited, waiting {wait_time}s: {url}")
            time.sleep(wait_time)
            return try_rss_with_headers(url, timeout)
        else:
            logger.warning(f"❌ HTTP {response.status_code}: {url}")
            
    except requests.exceptions.Timeout:
        logger.warning(f"⏱️  Timeout: {url}")
    except Exception as e:
        logger.warning(f"❌ Error: {url} - {str(e)[:50]}")
    
    return None


def discover_rss_feed(website_url: str) -> Optional[str]:
    """Auto-discover RSS feed from website"""
    
    # Try common RSS locations
    common_paths = [
        '/feed/',
        '/rss/',
        '/rss.xml',
        '/feed.xml',
        '/atom.xml',
        '/blog/feed/',
        '/news/rss',
        '/feeds/posts/default',
        '/feeds/rss.xml'
    ]
    
    base_url = website_url.rstrip('/')
    
    for path in common_paths:
        try_url = base_url + path
        try:
            respectful_delay()
            response = requests.get(try_url, headers=BROWSER_HEADERS, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                if feed.entries:
                    logger.info(f"🔍 Discovered RSS: {try_url}")
                    return try_url
        except:
            continue
    
    # Try parsing HTML for feed links
    try:
        respectful_delay()
        response = requests.get(base_url, headers=BROWSER_HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for RSS/Atom links in HTML
        for link in soup.find_all('link'):
            link_type = link.get('type', '')
            if 'rss' in link_type or 'atom' in link_type:
                feed_url = link.get('href')
                if feed_url:
                    # Make absolute URL if relative
                    if feed_url.startswith('/'):
                        feed_url = base_url + feed_url
                    logger.info(f"🔍 Found feed in HTML: {feed_url}")
                    return feed_url
    except:
        pass
    
    return None


def scrape_fallback(url: str) -> List[Dict]:
    """Fallback to web scraping if RSS fails"""
    try:
        # Remove /feed/ etc from URL
        base_url = url.replace('/feed/', '/').replace('/rss', '').replace('/feed', '')
        
        respectful_delay()
        response = requests.get(base_url, headers=BROWSER_HEADERS, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        items = []
        
        # Try to find articles (common patterns)
        articles = soup.find_all(['article', 'div'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['post', 'article', 'entry', 'news']
        ), limit=10)
        
        for article in articles:
            try:
                # Find title
                title_tag = article.find(['h1', 'h2', 'h3', 'h4'])
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                
                # Find link
                link_tag = article.find('a', href=True)
                if not link_tag:
                    continue
                link = link_tag['href']
                
                # Make absolute URL
                if link.startswith('/'):
                    from urllib.parse import urlparse
                    parsed = urlparse(base_url)
                    link = f"{parsed.scheme}://{parsed.netloc}{link}"
                
                # Find description (optional)
                desc_tag = article.find(['p', 'div'], class_=lambda x: x and 'excerpt' in str(x).lower())
                description = desc_tag.get_text(strip=True)[:200] if desc_tag else ""
                
                items.append({
                    'title': title,
                    'link': link,
                    'description': description,
                    'source': 'scraped'
                })
            except:
                continue
        
        if items:
            logger.info(f"🕷️  Scraped {len(items)} items: {url}")
        
        return items
        
    except Exception as e:
        logger.warning(f"❌ Scraping failed: {url} - {str(e)[:50]}")
        return []


def collect_with_fallback(source: Dict) -> List[Dict]:
    """
    Collect from source with multiple fallback strategies
    
    Strategies:
    1. Try RSS with browser headers
    2. Try discovering RSS feed
    3. Fallback to web scraping
    """
    
    url = source['url']
    name = source['name']
    
    logger.info(f"📡 Collecting: {name}")
    
    # Strategy 1: Try RSS with browser headers
    feed = try_rss_with_headers(url)
    if feed and feed.entries:
        return parse_feed_entries(feed, source)
    
    # Strategy 2: Try discovering RSS feed
    logger.info(f"🔍 Strategy 2: Discovering RSS for {name}")
    discovered_url = discover_rss_feed(url)
    if discovered_url:
        feed = try_rss_with_headers(discovered_url)
        if feed and feed.entries:
            # Update source URL for future
            logger.info(f"✅ Found working feed: {discovered_url}")
            return parse_feed_entries(feed, source)
    
    # Strategy 3: Web scraping fallback
    logger.info(f"🕷️  Strategy 3: Web scraping for {name}")
    items = scrape_fallback(url)
    if items:
        return items
    
    # All strategies failed
    logger.error(f"❌ All strategies failed for: {name}")
    return []


def parse_feed_entries(feed: feedparser.FeedParserDict, source: Dict) -> List[Dict]:
    """Parse feed entries into standard format"""
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
    
    return items


if __name__ == "__main__":
    # Test on some blocked sources
    test_sources = [
        {
            'name': 'Dark Reading',
            'url': 'https://www.darkreading.com/rss_simple.asp',
            'credibility': 0.80
        },
        {
            'name': 'Cisco Talos',
            'url': 'https://blog.talosintelligence.com/feeds/posts/default',
            'credibility': 0.90
        }
    ]
    
    logging.basicConfig(level=logging.INFO)
    
    for source in test_sources:
        items = collect_with_fallback(source)
        print(f"\n{source['name']}: {len(items)} items collected")
        if items:
            print(f"  First item: {items[0]['title'][:60]}")
