"""
Social Intelligence Layer - Real-time threat monitoring from Twitter/Reddit
Uses ScraperAPI for reliable access
"""

import requests
import os
import re
from typing import List, Dict
from datetime import datetime
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class SocialIntelligenceCollector:
    """Collect real-time threat intelligence from social media"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('SCRAPERAPI_KEY')
        if not self.api_key:
            raise ValueError("ScraperAPI key required")
        
        self.base_url = "http://api.scraperapi.com"
        logger.info("✅ Social Intelligence initialized")
    
    def scrape(self, url: str, render_js: bool = True) -> str:
        """Scrape URL via ScraperAPI"""
        params = {'api_key': self.api_key, 'url': url}
        if render_js:
            params['render'] = 'true'
        
        try:
            r = requests.get(self.base_url, params=params, timeout=60)
            return r.text if r.status_code == 200 else None
        except Exception as e:
            logger.error(f"Scrape failed: {str(e)[:50]}")
            return None
    
    def monitor_reddit(self, subreddit: str, limit: int = 25) -> List[Dict]:
        """Monitor Reddit subreddit for threats"""
        url = f"https://old.reddit.com/r/{subreddit}/new/"
        logger.info(f"🔴 Monitoring r/{subreddit}")
        
        html = self.scrape(url, render_js=False)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        items = []
        
        for post in soup.find_all('div', class_='thing', limit=limit):
            try:
                title_elem = post.find('a', class_='title')
                if not title_elem:
                    continue
                
                title = title_elem.get_text()
                link = title_elem.get('href', '')
                
                if link.startswith('/r/'):
                    link = f"https://reddit.com{link}"
                
                # Filter threat-related
                if not self._is_threat(title):
                    continue
                
                items.append({
                    'title': title,
                    'link': link,
                    'source': {
                        'name': f'Reddit r/{subreddit}',
                        'type': 'social',
                        'credibility': 0.65
                    },
                    'published': datetime.utcnow().isoformat(),
                    'tags': ['reddit', 'social', subreddit.lower()]
                })
            except Exception:
                continue
        
        logger.info(f"✅ Collected {len(items)} from r/{subreddit}")
        return items
    
    def collect_all(self) -> List[Dict]:
        """Collect from all priority sources"""
        items = []
        
        # Priority subreddits
        for sub in ['netsec', 'cybersecurity', 'blueteamsec']:
            items.extend(self.monitor_reddit(sub, limit=15))
        
        logger.info(f"📊 Total: {len(items)} social intelligence items")
        return items
    
    def _is_threat(self, text: str) -> bool:
        """Check if threat-related"""
        keywords = ['breach', 'hack', 'vulnerab', 'exploit', 'ransomware',
                   'malware', 'cve-', 'zero-day', '0day', 'attack']
        return any(k in text.lower() for k in keywords)
