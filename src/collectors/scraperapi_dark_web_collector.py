"""
ScraperAPI Master Dark Web Intelligence Collector
Professional-grade dark web intelligence collection using ScraperAPI
"""

import asyncio
import aiohttp
import logging
import json
import hashlib
import re
import time
import random
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import base64
import os

# Import configuration
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class DarkWebThreatItem:
    """Enhanced dark web threat intelligence item"""
    # Basic fields
    source: str
    source_type: str
    title: str
    content: str
    url: str
    timestamp: datetime
    
    # Dark web specific fields
    threat_type: str
    credibility_score: float
    urgency_level: str
    actor_mentioned: Optional[str]
    target_industry: Optional[str]
    asking_price: Optional[str]
    data_type: Optional[str]
    access_method: str
    verification_status: str
    
    # Extracted intelligence
    iocs: List[str] = None
    contact_info: List[str] = None
    cryptocurrency_addresses: List[str] = None
    affected_platforms: List[str] = None
    tags: List[str] = None
    
    # ScraperAPI metadata
    proxy_country: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    def __post_init__(self):
        if self.iocs is None:
            self.iocs = []
        if self.contact_info is None:
            self.contact_info = []
        if self.cryptocurrency_addresses is None:
            self.cryptocurrency_addresses = []
        if self.affected_platforms is None:
            self.affected_platforms = []
        if self.tags is None:
            self.tags = []

class ScraperAPIClient:
    """
    Master ScraperAPI client for dark web intelligence collection
    Handles proxy rotation, geotargeting, JavaScript rendering, and error handling
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.scraperapi.com"
        self.session = None
        
        # ScraperAPI configuration
        self.config = {
            'render': False,  # Enable for JavaScript-heavy sites
            'premium': True,  # Use premium proxies for better success
            'country_code': 'us',  # Default country
            'device_type': 'desktop',
            'keep_headers': True,
            'follow_redirect': True,
            'timeout': 30,
            'retry_404': False
        }
        
        # Rate limiting
        self.requests_per_second = 10  # Adjust based on plan
        self.last_request_time = 0
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'credits_used': 0,
            'countries_used': {},
            'render_requests': 0,
            'premium_requests': 0
        }
        
        logger.info("🚀 ScraperAPI client initialized")
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            limit=20,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=60, connect=30)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent for stealth"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
        ]
        return random.choice(user_agents)
    
    async def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        min_interval = 1.0 / self.requests_per_second
        
        if time_since_last_request < min_interval:
            sleep_time = min_interval - time_since_last_request
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _configure_request(self, url: str, **kwargs) -> Dict[str, Any]:
        """Configure ScraperAPI request parameters"""
        params = {
            'api_key': self.api_key,
            'url': url
        }
        
        # Apply configuration (convert bool to string for ScraperAPI)
        for key, value in self.config.items():
            if isinstance(value, bool):
                params[key] = str(value).lower()
            else:
                params[key] = value
        
        # Override with request-specific parameters
        for key, value in kwargs.items():
            if key in ['render', 'country_code', 'device_type', 'premium', 'ultra_premium']:
                if isinstance(value, bool):
                    params[key] = str(value).lower()
                else:
                    params[key] = value
        
        return params
    
    async def get(self, url: str, **kwargs) -> Optional[str]:
        """
        Make GET request through ScraperAPI
        Returns HTML content or None if failed
        """
        await self._rate_limit()
        
        try:
            params = self._configure_request(url, **kwargs)
            
            # Track statistics
            self.stats['total_requests'] += 1
            if params.get('render'):
                self.stats['render_requests'] += 1
            if params.get('premium'):
                self.stats['premium_requests'] += 1
            
            country = params.get('country_code', 'unknown')
            self.stats['countries_used'][country] = self.stats['countries_used'].get(country, 0) + 1
            
            logger.info(f"🌐 ScraperAPI request: {url[:50]}... (country: {country}, render: {params.get('render')})")
            
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    self.stats['successful_requests'] += 1
                    self.stats['credits_used'] += 1
                    
                    logger.info(f"✅ ScraperAPI success: {len(content)} characters")
                    return content
                else:
                    logger.warning(f"⚠️ ScraperAPI HTTP {response.status}: {url}")
                    self.stats['failed_requests'] += 1
                    return None
                    
        except Exception as e:
            logger.error(f"❌ ScraperAPI error: {e}")
            self.stats['failed_requests'] += 1
            return None
    
    async def get_with_retries(self, url: str, max_retries: int = 3, **kwargs) -> Optional[str]:
        """
        Make GET request with retry logic and different configurations
        """
        retry_configs = [
            {'country_code': 'us', 'render': False, 'premium': True},
            {'country_code': 'de', 'render': False, 'premium': True},
            {'country_code': 'gb', 'render': False, 'premium': True},
            {'country_code': 'us', 'render': True, 'premium': True},  # Try with JS rendering
            {'country_code': 'us', 'render': False, 'ultra_premium': True},  # Try ultra premium
        ]
        
        for attempt in range(min(max_retries, len(retry_configs))):
            config = retry_configs[attempt]
            
            try:
                content = await self.get(url, **config, **kwargs)
                if content:
                    return content
                    
            except Exception as e:
                logger.warning(f"⚠️ Retry {attempt + 1} failed for {url}: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error(f"❌ All retries failed for {url}")
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ScraperAPI usage statistics"""
        return {
            'scraperapi_stats': self.stats.copy(),
            'success_rate': self.stats['successful_requests'] / max(1, self.stats['total_requests']),
            'credits_remaining': 'Check dashboard',
            'most_used_country': max(self.stats['countries_used'].items(), key=lambda x: x[1])[0] if self.stats['countries_used'] else None
        }

class ScraperAPIDarkWebCollector:
    """
    Professional dark web intelligence collector powered by ScraperAPI
    Monitors underground forums, marketplaces, paste sites, and threat intelligence sources
    """
    
    def __init__(self, api_key: str, max_workers: int = 8):
        self.api_key = api_key
        self.max_workers = max_workers
        self.scraperapi_client = ScraperAPIClient(api_key)
        self.collected_items: List[DarkWebThreatItem] = []
        self.stats = {
            'total_sources': 0,
            'successful_sources': 0,
            'failed_sources': 0,
            'total_items': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Enhanced dark web sources with ScraperAPI optimization
        self.dark_web_sources = {
            # High-Priority Hacker Forums
            'hackernews': {
                'url': 'https://hackernews.io/',
                'type': 'forum',
                'priority': 'high',
                'scraperapi_config': {
                    'country_code': 'us',
                    'render': False,
                    'premium': True
                }
            },
            'nulled': {
                'url': 'https://nulled.to/',
                'type': 'forum',
                'priority': 'high',
                'scraperapi_config': {
                    'country_code': 'de',
                    'render': True,  # JavaScript heavy
                    'premium': True
                }
            },
            'cracked': {
                'url': 'https://cracked.io/',
                'type': 'forum',
                'priority': 'high',
                'scraperapi_config': {
                    'country_code': 'gb',
                    'render': True,
                    'premium': True
                }
            },
            
            # Security Research Forums
            'exploit_in': {
                'url': 'https://exploit.in/',
                'type': 'forum',
                'priority': 'medium',
                'scraperapi_config': {
                    'country_code': 'us',
                    'render': False,
                    'premium': True
                }
            },
            
            # Reddit Underground Communities
            'reddit_netsec': {
                'url': 'https://www.reddit.com/r/netsec/',
                'type': 'forum',
                'priority': 'medium',
                'scraperapi_config': {
                    'country_code': 'us',
                    'render': True,  # Reddit needs JS
                    'premium': True
                }
            },
            'reddit_hacking': {
                'url': 'https://www.reddit.com/r/hacking/',
                'type': 'forum',
                'priority': 'medium',
                'scraperapi_config': {
                    'country_code': 'us',
                    'render': True,
                    'premium': True
                }
            },
            'reddit_darknet': {
                'url': 'https://www.reddit.com/r/darknet/',
                'type': 'forum',
                'priority': 'high',
                'scraperapi_config': {
                    'country_code': 'nl',
                    'render': True,
                    'premium': True
                }
            },
            'reddit_cybercrime': {
                'url': 'https://www.reddit.com/r/cybercrime/',
                'type': 'forum',
                'priority': 'high',
                'scraperapi_config': {
                    'country_code': 'us',
                    'render': True,
                    'premium': True
                }
            },
            
            # Paste Sites (Leaked Data)
            'pastebin': {
                'url': 'https://pastebin.com/archive',
                'type': 'paste',
                'priority': 'high',
                'scraperapi_config': {
                    'country_code': 'us',
                    'render': False,
                    'premium': True
                }
            },
            'justpaste': {
                'url': 'https://justpaste.it/',
                'type': 'paste',
                'priority': 'medium',
                'scraperapi_config': {
                    'country_code': 'de',
                    'render': True,
                    'premium': True
                }
            },
            
            # Threat Intelligence Blogs
            'malware_traffic': {
                'url': 'https://www.malware-traffic-analysis.net/',
                'type': 'blog',
                'priority': 'high',
                'scraperapi_config': {
                    'country_code': 'us',
                    'render': False,
                    'premium': True
                }
            },
            'abuse_ch': {
                'url': 'https://feodotracker.abuse.ch/',
                'type': 'blog',
                'priority': 'high',
                'scraperapi_config': {
                    'country_code': 'ch',
                    'render': False,
                    'premium': True
                }
            },
            
            # Exploit Repositories
            'github_exploits': {
                'url': 'https://github.com/search?q=exploit+CVE&type=repositories',
                'type': 'repository',
                'priority': 'high',
                'scraperapi_config': {
                    'country_code': 'us',
                    'render': True,  # GitHub needs JS
                    'premium': True
                }
            },
            'exploit_db': {
                'url': 'https://www.exploit-db.com/',
                'type': 'repository',
                'priority': 'high',
                'scraperapi_config': {
                    'country_code': 'us',
                    'render': True,
                    'premium': True
                }
            },
            'packet_storm': {
                'url': 'https://packetstormsecurity.com/',
                'type': 'repository',
                'priority': 'medium',
                'scraperapi_config': {
                    'country_code': 'us',
                    'render': False,
                    'premium': True
                }
            },
            
            # Underground Marketplaces (Public Access)
            'empire_market': {
                'url': 'https://empire-market.org/',
                'type': 'marketplace',
                'priority': 'high',
                'scraperapi_config': {
                    'country_code': 'nl',
                    'render': True,
                    'ultra_premium': True
                }
            }
        }
        
        self.stats['total_sources'] = len(self.dark_web_sources)
        logger.info(f"🌑 ScraperAPI Dark Web Collector initialized with {len(self.dark_web_sources)} sources")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.scraperapi_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.scraperapi_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def collect_from_source(self, source_name: str, source_config: Dict) -> List[DarkWebThreatItem]:
        """Collect intelligence from a dark web source using ScraperAPI"""
        items = []
        
        try:
            url = source_config['url']
            scraperapi_config = source_config.get('scraperapi_config', {})
            
            logger.info(f"🌑 Collecting from {source_name} via ScraperAPI")
            
            # Make request through ScraperAPI with retries
            content = await self.scraperapi_client.get_with_retries(
                url, 
                max_retries=3,
                **scraperapi_config
            )
            
            if content:
                # Parse content based on source type
                if source_config['type'] == 'forum':
                    items = await self.parse_forum_content(content, source_name, source_config)
                elif source_config['type'] == 'paste':
                    items = await self.parse_paste_content(content, source_name, source_config)
                elif source_config['type'] == 'marketplace':
                    items = await self.parse_marketplace_content(content, source_name, source_config)
                elif source_config['type'] == 'blog':
                    items = await self.parse_blog_content(content, source_name, source_config)
                elif source_config['type'] == 'repository':
                    items = await self.parse_repository_content(content, source_name, source_config)
                
                # Add ScraperAPI metadata
                for item in items:
                    item.proxy_country = scraperapi_config.get('country_code')
                    item.session_id = f"session_{int(time.time())}"
                    item.request_id = hashlib.md5(f"{source_name}{time.time()}".encode()).hexdigest()[:8]
                
                logger.info(f"✅ {source_name}: {len(items)} items collected via ScraperAPI")
                self.stats['successful_sources'] += 1
            else:
                logger.warning(f"⚠️ {source_name}: No content retrieved via ScraperAPI")
                self.stats['failed_sources'] += 1
                
        except Exception as e:
            logger.error(f"❌ {source_name}: {str(e)}")
            self.stats['failed_sources'] += 1
        
        return items
    
    async def parse_forum_content(self, content: str, source_name: str, source_config: Dict) -> List[DarkWebThreatItem]:
        """Parse forum content for threat intelligence"""
        items = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for thread titles and content
            threads = soup.find_all(['h1', 'h2', 'h3', 'h4', 'a'], limit=25)
            
            for thread in threads:
                if thread.text.strip() and len(thread.text.strip()) > 10:
                    title = thread.text.strip()
                    
                    # Get associated content
                    content_elem = thread.find_next(['p', 'div', 'span'])
                    thread_content = content_elem.text.strip() if content_elem else ""
                    
                    # Enhanced analysis for dark web intelligence
                    threat_type, urgency, credibility = self.analyze_dark_web_content(title, thread_content)
                    actor = self.extract_threat_actor(title, thread_content)
                    target = self.extract_target_industry(title, thread_content)
                    price = self.extract_asking_price(title, thread_content)
                    data_type = self.extract_data_type(title, thread_content)
                    
                    # Extract comprehensive intelligence
                    full_text = title + " " + thread_content
                    iocs = self.extract_dark_web_iocs(full_text)
                    contacts = self.extract_contact_info(full_text)
                    crypto = self.extract_cryptocurrency_addresses(full_text)
                    platforms = self.extract_affected_platforms(full_text)
                    
                    # Only include items with threat intelligence value
                    if self.is_threat_intelligence(title, thread_content, threat_type):
                        item = DarkWebThreatItem(
                            source=source_name,
                            source_type='forum',
                            title=title,
                            content=thread_content[:500],
                            url=source_config['url'],
                            timestamp=datetime.now(timezone.utc),
                            threat_type=threat_type,
                            credibility_score=credibility,
                            urgency_level=urgency,
                            actor_mentioned=actor,
                            target_industry=target,
                            asking_price=price,
                            data_type=data_type,
                            access_method='scraperapi',
                            verification_status='unverified',
                            iocs=iocs,
                            contact_info=contacts,
                            cryptocurrency_addresses=crypto,
                            affected_platforms=platforms,
                            tags=self.generate_dark_web_tags(title, thread_content, threat_type)
                        )
                        
                        items.append(item)
                    
        except Exception as e:
            logger.error(f"Error parsing forum content from {source_name}: {e}")
        
        return items
    
    async def parse_paste_content(self, content: str, source_name: str, source_config: Dict) -> List[DarkWebThreatItem]:
        """Parse paste site content for leaked data"""
        items = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for paste links/titles
            paste_links = soup.find_all('a', limit=30)
            
            for link in paste_links:
                if link.text.strip() and len(link.text.strip()) > 5:
                    title = link.text.strip()
                    
                    # Check if it's likely threat intelligence
                    if self.is_threat_intelligence(title, "", 'data_breach'):
                        threat_type = 'data_breach'
                        urgency = 'high' if any(keyword in title.lower() for keyword in ['breach', 'leak', 'dump']) else 'medium'
                        credibility = 0.6  # Paste sites moderate credibility
                        data_type = self.extract_data_type(title, "")
                        
                        iocs = self.extract_dark_web_iocs(title)
                        contacts = self.extract_contact_info(title)
                        
                        item = DarkWebThreatItem(
                            source=source_name,
                            source_type='paste',
                            title=title,
                            content="",
                            url=link.get('href', ''),
                            timestamp=datetime.now(timezone.utc),
                            threat_type=threat_type,
                            credibility_score=credibility,
                            urgency_level=urgency,
                            actor_mentioned=None,
                            target_industry=None,
                            asking_price=None,
                            data_type=data_type,
                            access_method='scraperapi',
                            verification_status='unverified',
                            iocs=iocs,
                            contact_info=contacts,
                            cryptocurrency_addresses=[],
                            affected_platforms=[],
                            tags=self.generate_dark_web_tags(title, "", threat_type) + ['paste']
                        )
                        
                        items.append(item)
                    
        except Exception as e:
            logger.error(f"Error parsing paste content from {source_name}: {e}")
        
        return items
    
    async def parse_marketplace_content(self, content: str, source_name: str, source_config: Dict) -> List[DarkWebThreatItem]:
        """Parse marketplace content for illicit goods/services"""
        items = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for product listings
            products = soup.find_all(['div', 'article', 'tr'], limit=20)
            
            for product in products:
                title_elem = product.find(['h1', 'h2', 'h3', 'h4', 'a', 'span'])
                if title_elem and title_elem.text.strip() and len(title_elem.text.strip()) > 10:
                    title = title_elem.text.strip()
                    
                    # Get description
                    desc_elem = product.find(['p', 'div', 'span'])
                    description = desc_elem.text.strip() if desc_elem else ""
                    
                    # Extract marketplace intelligence
                    if self.is_marketplace_intelligence(title, description):
                        threat_type, urgency, credibility = self.analyze_dark_web_content(title, description)
                        price = self.extract_asking_price(title, description)
                        data_type = self.extract_data_type(title, description)
                        
                        full_text = title + " " + description
                        iocs = self.extract_dark_web_iocs(full_text)
                        contacts = self.extract_contact_info(full_text)
                        crypto = self.extract_cryptocurrency_addresses(full_text)
                        
                        item = DarkWebThreatItem(
                            source=source_name,
                            source_type='marketplace',
                            title=title,
                            content=description[:300],
                            url=source_config['url'],
                            timestamp=datetime.now(timezone.utc),
                            threat_type=threat_type or 'illicit_goods',
                            credibility_score=credibility,
                            urgency_level=urgency,
                            actor_mentioned=None,
                            target_industry=None,
                            asking_price=price,
                            data_type=data_type,
                            access_method='scraperapi',
                            verification_status='unverified',
                            iocs=iocs,
                            contact_info=contacts,
                            cryptocurrency_addresses=crypto,
                            affected_platforms=[],
                            tags=self.generate_dark_web_tags(title, description, threat_type) + ['marketplace']
                        )
                        
                        items.append(item)
                    
        except Exception as e:
            logger.error(f"Error parsing marketplace content from {source_name}: {e}")
        
        return items
    
    async def parse_blog_content(self, content: str, source_name: str, source_config: Dict) -> List[DarkWebThreatItem]:
        """Parse blog content for threat intelligence"""
        items = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for article titles
            articles = soup.find_all(['h1', 'h2', 'h3', 'a'], limit=20)
            
            for article in articles:
                if article.text.strip() and len(article.text.strip()) > 10:
                    title = article.text.strip()
                    
                    # Get article content
                    content_elem = article.find_next(['p', 'div', 'span'])
                    article_content = content_elem.text.strip() if content_elem else ""
                    
                    # Analyze for threat intelligence
                    if self.is_threat_intelligence(title, article_content, 'threat_research'):
                        threat_type, urgency, credibility = self.analyze_dark_web_content(title, article_content)
                        actor = self.extract_threat_actor(title, article_content)
                        platforms = self.extract_affected_platforms(title + " " + article_content)
                        
                        full_text = title + " " + article_content
                        iocs = self.extract_dark_web_iocs(full_text)
                        
                        item = DarkWebThreatItem(
                            source=source_name,
                            source_type='blog',
                            title=title,
                            content=article_content[:400],
                            url=source_config['url'],
                            timestamp=datetime.now(timezone.utc),
                            threat_type=threat_type or 'threat_research',
                            credibility_score=credibility + 0.1,  # Blogs slightly more credible
                            urgency_level=urgency,
                            actor_mentioned=actor,
                            target_industry=None,
                            asking_price=None,
                            data_type=None,
                            access_method='scraperapi',
                            verification_status='research',
                            iocs=iocs,
                            contact_info=[],
                            cryptocurrency_addresses=[],
                            affected_platforms=platforms,
                            tags=self.generate_dark_web_tags(title, article_content, threat_type) + ['research']
                        )
                        
                        items.append(item)
                    
        except Exception as e:
            logger.error(f"Error parsing blog content from {source_name}: {e}")
        
        return items
    
    async def parse_repository_content(self, content: str, source_name: str, source_config: Dict) -> List[DarkWebThreatItem]:
        """Parse repository content for exploit code"""
        items = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for repository links
            repos = soup.find_all('a', limit=25)
            
            for repo in repos:
                if repo.text.strip() and len(repo.text.strip()) > 5:
                    title = repo.text.strip()
                    
                    # Check if it's exploit-related
                    if any(keyword in title.lower() for keyword in ['exploit', 'cve', 'payload', 'shell', 'backdoor', '0day']):
                        threat_type = 'exploit_code'
                        urgency = 'high' if any(keyword in title.lower() for keyword in ['cve', '0day', 'zero']) else 'medium'
                        credibility = 0.7  # Public repos moderately credible
                        
                        platforms = self.extract_affected_platforms(title)
                        iocs = self.extract_dark_web_iocs(title)
                        
                        item = DarkWebThreatItem(
                            source=source_name,
                            source_type='repository',
                            title=title,
                            content="",
                            url=repo.get('href', ''),
                            timestamp=datetime.now(timezone.utc),
                            threat_type=threat_type,
                            credibility_score=credibility,
                            urgency_level=urgency,
                            actor_mentioned=None,
                            target_industry=None,
                            asking_price=None,
                            data_type='exploit',
                            access_method='scraperapi',
                            verification_status='public',
                            iocs=iocs,
                            contact_info=[],
                            cryptocurrency_addresses=[],
                            affected_platforms=platforms,
                            tags=['exploit', 'code', 'public']
                        )
                        
                        items.append(item)
                    
        except Exception as e:
            logger.error(f"Error parsing repository content from {source_name}: {e}")
        
        return items
    
    def is_threat_intelligence(self, title: str, content: str, threat_type: str) -> bool:
        """Determine if content is actual threat intelligence"""
        text = (title + " " + content).lower()
        
        # Threat intelligence keywords
        ti_keywords = [
            'ransomware', 'malware', 'exploit', 'cve', 'vulnerability',
            'leak', 'breach', 'dump', 'hack', 'attack', 'backdoor',
            'trojan', 'botnet', 'phishing', 'ddos', '0day', 'zero day',
            'apt', 'cyber', 'security', 'threat', 'intel', 'credential',
            'password', 'database', 'inject', 'shell', 'payload'
        ]
        
        # Check for threat intelligence indicators
        has_ti_keywords = any(keyword in text for keyword in ti_keywords)
        has_technical_terms = any(term in text for term in ['code', 'script', 'tool', 'software', 'system'])
        has_malicious_indicators = any(indicator in text for indicator in ['malicious', 'attack', 'exploit', 'breach'])
        
        return has_ti_keywords or (has_technical_terms and has_malicious_indicators)
    
    def is_marketplace_intelligence(self, title: str, content: str) -> bool:
        """Determine if marketplace listing is threat intelligence related"""
        text = (title + " " + content).lower()
        
        # Marketplace threat intelligence keywords
        marketplace_keywords = [
            'ransomware', 'malware', 'exploit', 'botnet', 'ddos',
            'access', 'credentials', 'database', 'leak', 'breach',
            'shell', 'backdoor', 'trojan', 'stealer', 'logger',
            'crypter', 'packer', 'builder', 'kit'
        ]
        
        # Price indicators
        price_indicators = ['$', 'btc', 'bitcoin', 'monero', 'xmr', 'eth', 'ethereum', 'usd', 'eur']
        
        has_threat_keywords = any(keyword in text for keyword in marketplace_keywords)
        has_price_indicators = any(indicator in text for indicator in price_indicators)
        
        return has_threat_keywords and has_price_indicators
    
    def analyze_dark_web_content(self, title: str, content: str) -> tuple:
        """Analyze content for threat intelligence parameters"""
        text = (title + " " + content).lower()
        
        # Enhanced threat type classification
        threat_type = "general"
        if any(keyword in text for keyword in ['ransomware', 'encrypt', 'decrypt', 'payment', 'lock']):
            threat_type = "ransomware"
        elif any(keyword in text for keyword in ['leak', 'breach', 'dump', 'database', 'credentials', 'stolen']):
            threat_type = "data_breach"
        elif any(keyword in text for keyword in ['exploit', 'cve', '0day', 'vulnerability', 'payload']):
            threat_type = "exploit"
        elif any(keyword in text for keyword in ['malware', 'trojan', 'backdoor', 'botnet', 'stealer']):
            threat_type = "malware"
        elif any(keyword in text for keyword in ['ddos', 'booter', 'stresser', 'amplification', 'flood']):
            threat_type = "ddos_service"
        elif any(keyword in text for keyword in ['phishing', 'credential', 'login', 'password', 'account']):
            threat_type = "phishing_kit"
        elif any(keyword in text for keyword in ['card', 'cvv', 'dumps', 'stripe', 'paypal', 'bank']):
            threat_type = "financial_fraud"
        elif any(keyword in text for keyword in ['access', 'rdp', 'ssh', 'cpanel', 'admin']):
            threat_type = "access_broker"
        
        # Enhanced urgency assessment
        urgency = "medium"
        high_urgency_keywords = ['critical', 'urgent', 'immediate', '0day', 'active', 'fresh', 'new', 'latest']
        low_urgency_keywords = ['old', 'archive', 'past', 'previous']
        
        if any(keyword in text for keyword in high_urgency_keywords):
            urgency = "high"
        elif any(keyword in text for keyword in low_urgency_keywords):
            urgency = "low"
        
        # Enhanced credibility scoring
        credibility = 0.5  # Base credibility for dark web sources
        
        # Boost for specific indicators
        if any(keyword in text for keyword in ['proof', 'screenshot', 'sample', 'demo', 'test']):
            credibility += 0.1
        if any(keyword in text for keyword in ['verified', 'trusted', 'reputation', 'vouch']):
            credibility += 0.1
        if len(content) > 200:
            credibility += 0.1
        if any(keyword in text for keyword in ['bitcoin', 'monero', 'crypto', 'blockchain']):
            credibility += 0.1
        if any(keyword in text for keyword in ['tutorial', 'guide', 'howto', 'method']):
            credibility += 0.1
        if any(keyword in text for keyword in ['private', 'exclusive', 'unique']):
            credibility += 0.05
        
        credibility = min(credibility, 1.0)
        
        return threat_type, urgency, credibility
    
    def extract_threat_actor(self, title: str, content: str) -> Optional[str]:
        """Extract threat actor mentions"""
        text = (title + " " + content).lower()
        
        # Enhanced threat actor database
        threat_actors = {
            # Ransomware Groups
            'lockbit': 'LockBit',
            'conti': 'Conti',
            'revil': 'REvil',
            'sodinokibi': 'REvil',
            'darkside': 'DarkSide',
            'cl0p': 'CL0P',
            'clop': 'CL0P',
            'babuk': 'Babuk',
            'avaddon': 'Avaddon',
            'pysa': 'Pysa',
            'maze': 'Maze',
            'netwalker': 'NetWalker',
            'ryuk': 'Ryuk',
            'wannacry': 'WannaCry',
            'notpetya': 'NotPetya',
            
            # APT Groups
            'apt28': 'APT28',
            'apt29': 'APT29',
            'apt41': 'APT41',
            'lazarus': 'Lazarus Group',
            'fancy bear': 'Fancy Bear',
            'cozy bear': 'Cozy Bear',
            'equation group': 'Equation Group',
            'carbanak': 'Carbanak',
            'fin7': 'FIN7',
            'ta505': 'TA505',
            
            # Cybercrime Groups
            'wizard spider': 'Wizard Spider',
            'trickbot': 'TrickBot',
            'emotet': 'Emotet',
            'qakbot': 'Qakbot',
            'iceid': 'IceID',
            'dridex': 'Dridex'
        }
        
        for actor_key, actor_name in threat_actors.items():
            if actor_key in text:
                return actor_name
        
        return None
    
    def extract_target_industry(self, title: str, content: str) -> Optional[str]:
        """Extract targeted industry"""
        text = (title + " " + content).lower()
        
        industries = {
            'healthcare': ['hospital', 'medical', 'healthcare', 'pharma', 'clinic', 'health'],
            'financial': ['bank', 'finance', 'payment', 'credit', 'card', 'atm', 'swift'],
            'government': ['government', 'military', 'agency', 'federal', 'defense', 'state'],
            'technology': ['software', 'tech', 'saas', 'cloud', 'isp', 'hosting'],
            'retail': ['retail', 'ecommerce', 'shop', 'store', 'merchant'],
            'education': ['university', 'school', 'education', 'college', 'student'],
            'manufacturing': ['manufacturing', 'factory', 'industrial', 'production'],
            'telecommunications': ['telecom', 'communications', 'isp', 'mobile', 'wireless']
        }
        
        for industry, keywords in industries.items():
            if any(keyword in text for keyword in keywords):
                return industry
        
        return None
    
    def extract_asking_price(self, title: str, content: str) -> Optional[str]:
        """Extract asking price from marketplace listings"""
        text = (title + " " + content).lower()
        
        # Enhanced price patterns
        price_patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $1,000.00
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:usd|dollars?)',  # 1,000 USD
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:eur|euros?)',  # 1,000 EUR
            r'(\d+)\s*bitcoin',  # 5 bitcoin
            r'(\d+)\s*btc',  # 5 BTC
            r'(\d+(?:\.\d+)?)\s*monero',  # 10.5 monero
            r'(\d+(?:\.\d+)?)\s*xmr',  # 10.5 XMR
            r'(\d+(?:\.\d+)?)\s*ethereum',  # 2 ethereum
            r'(\d+(?:\.\d+)?)\s*eth',  # 2 ETH
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    def extract_data_type(self, title: str, content: str) -> Optional[str]:
        """Extract type of data being offered/leaked"""
        text = (title + " " + content).lower()
        
        data_types = {
            'credentials': ['password', 'credential', 'login', 'account', 'auth'],
            'database': ['database', 'db', 'sql', 'dump', 'table'],
            'personal_info': ['pii', 'personal', 'identity', 'ssn', 'social security', 'id'],
            'financial': ['credit card', 'cvv', 'bank', 'payment', 'transaction'],
            'source_code': ['source code', 'code', 'github', 'git', 'repository'],
            'exploit': ['exploit', '0day', 'vulnerability', 'cve', 'payload'],
            'malware': ['malware', 'trojan', 'ransomware', 'backdoor', 'builder'],
            'access': ['access', 'rdp', 'ssh', 'cpanel', 'admin', 'shell'],
            'logs': ['logs', 'traffic', 'network', 'capture', 'pcap']
        }
        
        for data_type, keywords in data_types.items():
            if any(keyword in text for keyword in keywords):
                return data_type
        
        return None
    
    def extract_dark_web_iocs(self, text: str) -> List[str]:
        """Extract indicators of compromise from dark web content"""
        iocs = []
        
        # IP addresses
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = re.findall(ip_pattern, text)
        # Filter out common false positives
        valid_ips = [ip for ip in ips if not (ip.startswith('127.') or ip.startswith('192.168.') or ip.startswith('10.') or ip.endswith('.0'))]
        iocs.extend(valid_ips)
        
        # Domains
        domain_pattern = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
        domains = re.findall(domain_pattern, text)
        # Filter out common false positives
        valid_domains = [domain for domain in domains if len(domain) > 3 and not any(ext in domain for ext in ['.jpg', '.png', '.gif', '.css', '.js'])]
        iocs.extend(valid_domains)
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        iocs.extend(emails)
        
        # Hash patterns
        hash_patterns = [
            r'\b[a-f0-9]{32}\b',  # MD5
            r'\b[a-f0-9]{40}\b',  # SHA1
            r'\b[a-f0-9]{64}\b'   # SHA256
        ]
        
        for pattern in hash_patterns:
            hashes = re.findall(pattern, text)
            iocs.extend(hashes)
        
        # URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        iocs.extend(urls)
        
        return list(set(iocs))  # Remove duplicates
    
    def extract_contact_info(self, text: str) -> List[str]:
        """Extract contact information"""
        contacts = []
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        contacts.extend(emails)
        
        # Phone numbers (basic pattern)
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
        phones = re.findall(phone_pattern, text)
        contacts.extend(phones)
        
        # Telegram handles
        telegram_pattern = r'@([a-zA-Z0-9_]{5,})'
        telegram = re.findall(telegram_pattern, text)
        contacts.extend(['@' + handle for handle in telegram])
        
        # Discord handles
        discord_pattern = r'([a-zA-Z0-9]{2,32})#([0-9]{4})'
        discord = re.findall(discord_pattern, text)
        contacts.extend([f"{username}#{discriminator}" for username, discriminator in discord])
        
        return list(set(contacts))
    
    def extract_cryptocurrency_addresses(self, text: str) -> List[str]:
        """Extract cryptocurrency addresses"""
        crypto_addresses = []
        
        # Bitcoin addresses
        btc_pattern = r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'
        btc = re.findall(btc_pattern, text)
        crypto_addresses.extend(btc)
        
        # Bitcoin Cash addresses
        bch_pattern = r'\b(q|Q)[a-km-zA-HJ-NP-Z1-9]{41}\b'
        bch = re.findall(bch_pattern, text)
        crypto_addresses.extend(bch)
        
        # Monero addresses
        xmr_pattern = r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b'
        xmr = re.findall(xmr_pattern, text)
        crypto_addresses.extend(xmr)
        
        # Ethereum addresses
        eth_pattern = r'\b0x[a-fA-F0-9]{40}\b'
        eth = re.findall(eth_pattern, text)
        crypto_addresses.extend(eth)
        
        # Litecoin addresses
        ltc_pattern = r'\b[L][a-km-zA-HJ-NP-Z1-9]{32,33}\b'
        ltc = re.findall(ltc_pattern, text)
        crypto_addresses.extend(ltc)
        
        return list(set(crypto_addresses))
    
    def extract_affected_platforms(self, text: str) -> List[str]:
        """Extract affected platforms"""
        platforms = []
        
        platform_keywords = {
            'Windows': ['windows', 'win', 'microsoft', '.exe'],
            'Linux': ['linux', 'ubuntu', 'debian', 'centos', 'redhat', 'rpm', 'deb'],
            'macOS': ['macos', 'mac', 'osx', 'apple', '.dmg'],
            'Android': ['android', 'google', '.apk'],
            'iOS': ['ios', 'iphone', 'ipad', 'apple', '.ipa'],
            'Web': ['web', 'website', 'http', 'https', 'html', 'javascript'],
            'Database': ['mysql', 'postgresql', 'oracle', 'sql server', 'mongodb', 'redis'],
            'Cloud': ['aws', 'azure', 'gcp', 'cloud', 'ec2', 's3'],
            'Network': ['router', 'switch', 'firewall', 'cisco', 'juniper'],
            'IoT': ['iot', 'embedded', 'firmware', 'arduino', 'raspberry']
        }
        
        for platform, keywords in platform_keywords.items():
            if any(keyword in text.lower() for keyword in keywords):
                platforms.append(platform)
        
        return list(set(platforms))
    
    def generate_dark_web_tags(self, title: str, content: str, threat_type: str) -> List[str]:
        """Generate relevant tags for dark web intelligence"""
        text = (title + " " + content).lower()
        tags = []
        
        # Source type tags
        tags.append('dark_web')
        tags.append('underground')
        tags.append('scraperapi')
        
        # Content-based tags
        if threat_type:
            tags.append(threat_type)
        
        # Specific threat tags
        threat_tags = {
            'ransomware': ['ransomware', 'encryption', 'payment'],
            'data_breach': ['data_leak', 'breach', 'dump'],
            'exploit': ['exploit', 'vulnerability', 'cve'],
            'malware': ['malware', 'trojan', 'backdoor'],
            'ddos_service': ['ddos', 'booter', 'stresser'],
            'phishing_kit': ['phishing', 'credential', 'login'],
            'financial_fraud': ['financial_crime', 'carding', 'fraud'],
            'access_broker': ['access', 'initial_access']
        }
        
        if threat_type in threat_tags:
            tags.extend(threat_tags[threat_type])
        
        # Additional context tags
        if any(keyword in text for keyword in ['cryptocurrency', 'bitcoin', 'monero']):
            tags.append('crypto')
        if any(keyword in text for keyword in ['tutorial', 'guide', 'howto']):
            tags.append('tutorial')
        if any(keyword in text for keyword in ['private', 'exclusive', 'unique']):
            tags.append('exclusive')
        if any(keyword in text for keyword in ['verified', 'proof', 'demo']):
            tags.append('verified')
        
        return list(set(tags))
    
    async def collect_all_dark_web_intelligence(self) -> List[DarkWebThreatItem]:
        """Collect from all dark web intelligence sources using ScraperAPI"""
        self.stats['start_time'] = datetime.now(timezone.utc)
        self.collected_items.clear()
        
        logger.info("🌑 Starting ScraperAPI Dark Web Intelligence Collection")
        logger.info(f"📊 Total sources: {self.stats['total_sources']}")
        logger.info(f"🚀 Using ScraperAPI with premium proxies")
        
        # Create tasks for parallel collection
        tasks = []
        for source_name, source_config in self.dark_web_sources.items():
            task = asyncio.create_task(self.collect_from_source(source_name, source_config))
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect all items
        for result in results:
            if isinstance(result, list):
                self.collected_items.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Collection error: {result}")
        
        self.stats['end_time'] = datetime.now(timezone.utc)
        self.stats['total_items'] = len(self.collected_items)
        
        # Sort by timestamp (most recent first)
        self.collected_items.sort(key=lambda x: x.timestamp, reverse=True)
        
        return self.collected_items
    
    def get_collection_summary(self) -> Dict[str, Any]:
        """Get comprehensive dark web collection summary"""
        duration = None
        if self.stats['start_time'] and self.stats['end_time']:
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        # Analyze collected items
        threat_types = {}
        source_types = {}
        urgency_levels = {}
        actors_mentioned = {}
        countries_used = {}
        
        total_iocs = 0
        total_crypto_addresses = 0
        total_contact_info = 0
        avg_credibility = 0
        
        for item in self.collected_items:
            # Count threat types
            threat_types[item.threat_type] = threat_types.get(item.threat_type, 0) + 1
            
            # Count source types
            source_types[item.source_type] = source_types.get(item.source_type, 0) + 1
            
            # Count urgency levels
            urgency_levels[item.urgency_level] = urgency_levels.get(item.urgency_level, 0) + 1
            
            # Count actors
            if item.actor_mentioned:
                actors_mentioned[item.actor_mentioned] = actors_mentioned.get(item.actor_mentioned, 0) + 1
            
            # Count countries
            if item.proxy_country:
                countries_used[item.proxy_country] = countries_used.get(item.proxy_country, 0) + 1
            
            # Count intelligence
            total_iocs += len(item.iocs)
            total_crypto_addresses += len(item.cryptocurrency_addresses)
            total_contact_info += len(item.contact_info)
            avg_credibility += item.credibility_score
        
        avg_credibility = avg_credibility / len(self.collected_items) if self.collected_items else 0
        
        # Get ScraperAPI stats
        scraperapi_stats = self.scraperapi_client.get_stats()
        
        return {
            'collection_stats': {
                'total_sources': self.stats['total_sources'],
                'successful_sources': self.stats['successful_sources'],
                'failed_sources': self.stats['failed_sources'],
                'total_items': self.stats['total_items'],
                'start_time': self.stats['start_time'].isoformat() if self.stats.get('start_time') else None,
                'end_time': self.stats['end_time'].isoformat() if self.stats.get('end_time') else None
            },
            'duration_seconds': duration,
            'items_per_second': len(self.collected_items) / duration if duration else 0,
            'threat_analysis': {
                'threat_types': threat_types,
                'source_types': source_types,
                'urgency_levels': urgency_levels,
                'top_actors': dict(sorted(actors_mentioned.items(), key=lambda x: x[1], reverse=True)[:5])
            },
            'intelligence_metrics': {
                'total_iocs_extracted': total_iocs,
                'total_crypto_addresses': total_crypto_addresses,
                'total_contact_info': total_contact_info,
                'average_credibility': avg_credibility,
                'high_urgency_items': urgency_levels.get('high', 0) + urgency_levels.get('critical', 0)
            },
            'geographic_analysis': {
                'countries_used': countries_used,
                'most_used_country': max(countries_used.items(), key=lambda x: x[1])[0] if countries_used else None
            },
            'scraperapi_performance': scraperapi_stats
        }
    
    def save_dark_web_results(self, output_file: str):
        """Save dark web collection results with ScraperAPI metadata"""
        # Convert items to dictionaries
        items_data = []
        for item in self.collected_items:
            item_dict = {
                'source': item.source,
                'source_type': item.source_type,
                'title': item.title,
                'content': item.content,
                'url': item.url,
                'timestamp': item.timestamp.isoformat(),
                'threat_type': item.threat_type,
                'credibility_score': item.credibility_score,
                'urgency_level': item.urgency_level,
                'actor_mentioned': item.actor_mentioned,
                'target_industry': item.target_industry,
                'asking_price': item.asking_price,
                'data_type': item.data_type,
                'access_method': item.access_method,
                'verification_status': item.verification_status,
                'iocs': item.iocs,
                'contact_info': item.contact_info,
                'cryptocurrency_addresses': item.cryptocurrency_addresses,
                'affected_platforms': item.affected_platforms,
                'tags': item.tags,
                # ScraperAPI metadata
                'proxy_country': item.proxy_country,
                'session_id': item.session_id,
                'request_id': item.request_id
            }
            items_data.append(item_dict)
        
        output = {
            'collection_metadata': {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'collector_version': 'scraperapi_dark_web_v1.0',
                'total_items': len(self.collected_items),
                'collection_type': 'scraperapi_dark_web_intelligence',
                'powered_by': 'ScraperAPI'
            },
            'collection_summary': self.get_collection_summary(),
            'dark_web_intelligence': items_data
        }
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"💾 ScraperAPI dark web intelligence saved to {output_file}")

async def main():
    """Main function for ScraperAPI dark web intelligence collection"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Get ScraperAPI key from environment or settings
    api_key = os.getenv('SCRAPERAPI_KEY') or getattr(settings, 'scraperapi_key', None)
    
    if not api_key:
        logger.error("❌ ScraperAPI key not found. Set SCRAPERAPI_KEY environment variable or add to settings.")
        return
    
    async with ScraperAPIDarkWebCollector(api_key=api_key, max_workers=8) as collector:
        # Collect dark web intelligence
        items = await collector.collect_all_dark_web_intelligence()
        
        # Get summary
        summary = collector.get_collection_summary()
        
        # Print results
        print("\n" + "="*80)
        print("🌑 SCRAPERAPI DARK WEB INTELLIGENCE COLLECTION RESULTS")
        print("="*80)
        print(f"Total Items Collected: {summary['collection_stats']['total_items']}")
        print(f"Successful Sources: {summary['collection_stats']['successful_sources']}/{summary['collection_stats']['total_sources']}")
        print(f"Collection Duration: {summary['duration_seconds']:.2f} seconds")
        print(f"Collection Rate: {summary['items_per_second']:.2f} items/second")
        
        print(f"\n📊 Threat Types:")
        for threat_type, count in summary['threat_analysis']['threat_types'].items():
            print(f"  {threat_type}: {count}")
        
        print(f"\n⚠️ Urgency Levels:")
        for urgency, count in summary['threat_analysis']['urgency_levels'].items():
            print(f"  {urgency}: {count}")
        
        print(f"\n🎯 Intelligence Metrics:")
        print(f"  Total IOCs Extracted: {summary['intelligence_metrics']['total_iocs_extracted']}")
        print(f"  Crypto Addresses: {summary['intelligence_metrics']['total_crypto_addresses']}")
        print(f"  Contact Info: {summary['intelligence_metrics']['total_contact_info']}")
        print(f"  Average Credibility: {summary['intelligence_metrics']['average_credibility']:.2f}")
        print(f"  High Urgency Items: {summary['intelligence_metrics']['high_urgency_items']}")
        
        print(f"\n🌍 Geographic Analysis:")
        print(f"  Countries Used: {summary['geographic_analysis']['countries_used']}")
        print(f"  Most Used Country: {summary['geographic_analysis']['most_used_country']}")
        
        print(f"\n🚀 ScraperAPI Performance:")
        scraperapi_stats = summary['scraperapi_performance']['scraperapi_stats']
        print(f"  Total Requests: {scraperapi_stats['total_requests']}")
        print(f"  Success Rate: {summary['scraperapi_performance']['success_rate']:.1%}")
        print(f"  Credits Used: {scraperapi_stats['credits_used']}")
        print(f"  Premium Requests: {scraperapi_stats['premium_requests']}")
        print(f"  Render Requests: {scraperapi_stats['render_requests']}")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"data/raw/scraperapi_dark_web_intelligence_{timestamp}.json"
        collector.save_dark_web_results(output_file)
        
        print(f"\n✅ ScraperAPI dark web intelligence collection complete!")
        print(f"📁 Results saved to: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
