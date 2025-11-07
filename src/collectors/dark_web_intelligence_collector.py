"""
Dark Web Intelligence Collector
Pro scraper implementation with rotating proxies for underground threat intelligence
"""

import asyncio
import aiohttp
import logging
import json
import hashlib
import re
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import random
from urllib.parse import urljoin, urlparse
import base64

# Import configuration
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class DarkWebThreatItem:
    """Dark web threat intelligence item with enhanced metadata"""
    # Basic fields
    source: str
    source_type: str  # forum, marketplace, telegram, etc.
    title: str
    content: str
    url: str
    timestamp: datetime
    
    # Dark web specific fields
    threat_type: str  # ransomware, data_breach, exploit, malware, etc.
    credibility_score: float  # 0.0-1.0 based on source reliability
    urgency_level: str  # low, medium, high, critical
    actor_mentioned: Optional[str]  # threat actor or group
    target_industry: Optional[str]  # targeted industry sector
    asking_price: Optional[str]  # for marketplace items
    data_type: Optional[str]  # credentials, databases, exploits, etc.
    access_method: str  # direct, proxy, tor, etc.
    verification_status: str  # verified, unverified, disputed
    
    # Extracted intelligence
    iocs: List[str] = None
    contact_info: List[str] = None
    cryptocurrency_addresses: List[str] = None
    affected_platforms: List[str] = None
    tags: List[str] = None
    
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

class RotatingProxyManager:
    """Manages rotating proxy pool for dark web scraping"""
    
    def __init__(self):
        # Free proxy sources (you can replace with paid proxy services)
        self.proxy_sources = [
            # Free proxy lists (update regularly)
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
            'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
            # Add your own proxy sources here
        ]
        
        self.proxies = []
        self.current_proxy_index = 0
        self.proxy_failures = {}
        self.max_failures = 3
        
    async def refresh_proxies(self):
        """Refresh proxy list from sources"""
        logger.info("🔄 Refreshing proxy pool...")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for source in self.proxy_sources:
                task = self.fetch_proxy_source(session, source)
                tasks.append(task)
            
            proxy_lists = await asyncio.gather(*tasks, return_exceptions=True)
            
            self.proxies = []
            for proxy_list in proxy_lists:
                if isinstance(proxy_list, list):
                    self.proxies.extend(proxy_list)
            
            # Remove duplicates and test connectivity
            self.proxies = list(set(self.proxies))
            logger.info(f"✅ Proxy pool refreshed: {len(self.proxies)} proxies available")
    
    async def fetch_proxy_source(self, session: aiohttp.ClientSession, url: str) -> List[str]:
        """Fetch proxies from a source URL"""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    text = await response.text()
                    # Extract IP:PORT pairs
                    proxy_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{1,5}\b'
                    proxies = re.findall(proxy_pattern, text)
                    return proxies
        except Exception as e:
            logger.warning(f"Failed to fetch proxies from {url}: {e}")
            return []
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next working proxy"""
        if not self.proxies:
            return None
        
        attempts = 0
        while attempts < len(self.proxies):
            proxy = self.proxies[self.current_proxy_index]
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
            
            # Skip failed proxies
            if self.proxy_failures.get(proxy, 0) < self.max_failures:
                return proxy
            
            attempts += 1
        
        return None
    
    def mark_proxy_failed(self, proxy: str):
        """Mark a proxy as failed"""
        self.proxy_failures[proxy] = self.proxy_failures.get(proxy, 0) + 1

class DarkWebIntelligenceCollector:
    """
    Dark web intelligence collector with pro scraping capabilities
    Monitors forums, marketplaces, Telegram channels, and underground sources
    """
    
    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.proxy_manager = RotatingProxyManager()
        self.collected_items: List[DarkWebThreatItem] = []
        self.stats = {
            'total_sources': 0,
            'successful_sources': 0,
            'failed_sources': 0,
            'total_items': 0,
            'proxies_used': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Dark web intelligence sources
        self.dark_web_sources = {
            # Hacker Forums (Clear web with underground content)
            'hackernews': {
                'url': 'https://hackernews.io/',
                'type': 'forum',
                'update_frequency': 'hourly',
                'priority': 'high',
                'content_selectors': ['.title', '.content', '.metadata']
            },
            'nulled': {
                'url': 'https://nulled.to/',
                'type': 'forum',
                'update_frequency': 'hourly',
                'priority': 'high',
                'content_selectors': ['.topic_title', '.post_content', '.post_meta']
            },
            'cracked': {
                'url': 'https://cracked.io/',
                'type': 'forum',
                'update_frequency': 'hourly',
                'priority': 'high',
                'content_selectors': ['.thread-title', '.message', '.thread-info']
            },
            
            # Security Research Forums
            'exploit_in': {
                'url': 'https://exploit.in/',
                'type': 'forum',
                'update_frequency': 'daily',
                'priority': 'medium',
                'content_selectors': ['.topic', '.post', '.meta']
            },
            
            # Reddit Underground Communities
            'reddit_netsec': {
                'url': 'https://www.reddit.com/r/netsec/',
                'type': 'forum',
                'update_frequency': 'hourly',
                'priority': 'medium',
                'content_selectors': ['._3xX726aBn29LDbsDtzr_6E', '_3cjCphgls6DH-irkVaA0GM']
            },
            'reddit_hacking': {
                'url': 'https://www.reddit.com/r/hacking/',
                'type': 'forum',
                'update_frequency': 'hourly',
                'priority': 'medium',
                'content_selectors': ['._3xX726aBn29LDbsDtzr_6E', '_3cjCphgls6DH-irkVaA0GM']
            },
            'reddit_darknet': {
                'url': 'https://www.reddit.com/r/darknet/',
                'type': 'forum',
                'update_frequency': 'daily',
                'priority': 'high',
                'content_selectors': ['._3xX726aBn29LDbsDtzr_6E', '_3cjCphgls6DH-irkVaA0GM']
            },
            
            # Paste Sites (often contain leaked data)
            'pastebin': {
                'url': 'https://pastebin.com/archive',
                'type': 'paste',
                'update_frequency': 'continuous',
                'priority': 'high',
                'content_selectors': ['.gsc-table-result', '.gs_a']
            },
            'gists': {
                'url': 'https://gist.github.com/discover',
                'type': 'paste',
                'update_frequency': 'continuous',
                'priority': 'medium',
                'content_selectors': ['.gist', '.file-box']
            },
            
            # Threat Intelligence Blogs (Monitor for TTPs)
            'malware_traffic': {
                'url': 'https://www.malware-traffic-analysis.net/',
                'type': 'blog',
                'update_frequency': 'daily',
                'priority': 'high',
                'content_selectors': ['.post-title', '.post-content', '.post-meta']
            },
            
            # Exploit Repositories
            'github_exploits': {
                'url': 'https://github.com/search?q=exploit+CVE&type=repositories',
                'type': 'repository',
                'update_frequency': 'daily',
                'priority': 'high',
                'content_selectors': ['.v-align-middle', '.mb-1']
            },
            
            # Underground Marketplaces (Public access)
            'empire_market': {
                'url': 'https://empire-market.org/',
                'type': 'marketplace',
                'update_frequency': 'daily',
                'priority': 'high',
                'content_selectors': ['.product-title', '.product-description', '.product-price']
            }
        }
        
        self.stats['total_sources'] = len(self.dark_web_sources)
        logger.info(f"🌑 Dark Web Intelligence Collector initialized with {len(self.dark_web_sources)} sources")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.proxy_manager.refresh_proxies()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass
    
    def create_session_with_proxy(self, proxy: str) -> aiohttp.ClientSession:
        """Create session with rotating proxy"""
        connector = aiohttp.TCPConnector(
            limit=self.max_workers,
            limit_per_host=4,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        if proxy:
            proxy_url = f"http://{proxy}"
            return aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers,
                proxy=proxy_url
            )
        else:
            return aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers
            )
    
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
    
    async def collect_from_source(self, source_name: str, source_config: Dict) -> List[DarkWebThreatItem]:
        """Collect intelligence from a dark web source"""
        items = []
        proxy_used = None
        
        try:
            # Get proxy for this request
            proxy = self.proxy_manager.get_next_proxy()
            if proxy:
                proxy_used = proxy
                self.stats['proxies_used'] += 1
            
            async with self.create_session_with_proxy(proxy) as session:
                logger.info(f"🌑 Collecting from {source_name} (proxy: {'yes' if proxy else 'no'})")
                
                async with session.get(source_config['url']) as response:
                    if response.status == 200:
                        content = await response.text()
                        
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
                        
                        logger.info(f"✅ {source_name}: {len(items)} items collected")
                        self.stats['successful_sources'] += 1
                        
                    else:
                        logger.warning(f"⚠️ {source_name}: HTTP {response.status}")
                        if proxy:
                            self.proxy_manager.mark_proxy_failed(proxy)
                        self.stats['failed_sources'] += 1
                        
        except Exception as e:
            logger.error(f"❌ {source_name}: {str(e)}")
            if proxy_used:
                self.proxy_manager.mark_proxy_failed(proxy_used)
            self.stats['failed_sources'] += 1
        
        return items
    
    async def parse_forum_content(self, content: str, source_name: str, source_config: Dict) -> List[DarkWebThreatItem]:
        """Parse forum content for threat intelligence"""
        items = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for thread titles and content
            threads = soup.find_all(['h1', 'h2', 'h3', 'h4'], limit=20)
            
            for thread in threads:
                if thread.text.strip():
                    title = thread.text.strip()
                    
                    # Get associated content
                    content_elem = thread.find_next(['p', 'div', 'span'])
                    thread_content = content_elem.text.strip() if content_elem else ""
                    
                    # Extract threat intelligence
                    threat_type, urgency, credibility = self.analyze_dark_web_content(title, thread_content)
                    actor = self.extract_threat_actor(title, thread_content)
                    target = self.extract_target_industry(title, thread_content)
                    price = self.extract_asking_price(title, thread_content)
                    data_type = self.extract_data_type(title, thread_content)
                    
                    # Extract IOCs and other intelligence
                    iocs = self.extract_dark_web_iocs(title + " " + thread_content)
                    contacts = self.extract_contact_info(title + " " + thread_content)
                    crypto = self.extract_cryptocurrency_addresses(title + " " + thread_content)
                    platforms = self.extract_affected_platforms(title + " " + thread_content)
                    
                    item = DarkWebThreatItem(
                        source=source_name,
                        source_type='forum',
                        title=title,
                        content=thread_content[:500],  # Limit length
                        url=source_config['url'],
                        timestamp=datetime.now(timezone.utc),
                        threat_type=threat_type,
                        credibility_score=credibility,
                        urgency_level=urgency,
                        actor_mentioned=actor,
                        target_industry=target,
                        asking_price=price,
                        data_type=data_type,
                        access_method='proxy' if self.proxy_manager.proxies else 'direct',
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
            paste_links = soup.find_all('a', limit=25)
            
            for link in paste_links:
                if link.text.strip():
                    title = link.text.strip()
                    
                    # Analyze for potential threat intelligence
                    threat_type, urgency, credibility = self.analyze_dark_web_content(title, "")
                    data_type = self.extract_data_type(title, "")
                    
                    # Check if it's likely threat intelligence
                    if any(keyword in title.lower() for keyword in ['leak', 'breach', 'dump', 'database', 'credentials', 'passwords', 'exploit']):
                        iocs = self.extract_dark_web_iocs(title)
                        contacts = self.extract_contact_info(title)
                        
                        item = DarkWebThreatItem(
                            source=source_name,
                            source_type='paste',
                            title=title,
                            content="",
                            url=link.get('href', ''),
                            timestamp=datetime.now(timezone.utc),
                            threat_type=threat_type or 'data_breach',
                            credibility_score=credibility,
                            urgency_level=urgency,
                            actor_mentioned=None,
                            target_industry=None,
                            asking_price=None,
                            data_type=data_type,
                            access_method='proxy' if self.proxy_manager.proxies else 'direct',
                            verification_status='unverified',
                            iocs=iocs,
                            contact_info=contacts,
                            cryptocurrency_addresses=[],
                            affected_platforms=[],
                            tags=self.generate_dark_web_tags(title, "", threat_type)
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
            products = soup.find_all(['div', 'article'], limit=15)
            
            for product in products:
                title_elem = product.find(['h1', 'h2', 'h3', 'h4'])
                if title_elem and title_elem.text.strip():
                    title = title_elem.text.strip()
                    
                    # Get description
                    desc_elem = product.find(['p', 'div', 'span'])
                    description = desc_elem.text.strip() if desc_elem else ""
                    
                    # Extract marketplace intelligence
                    threat_type, urgency, credibility = self.analyze_dark_web_content(title, description)
                    price = self.extract_asking_price(title, description)
                    data_type = self.extract_data_type(title, description)
                    
                    iocs = self.extract_dark_web_iocs(title + " " + description)
                    contacts = self.extract_contact_info(title + " " + description)
                    crypto = self.extract_cryptocurrency_addresses(title + " " + description)
                    
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
                        access_method='proxy' if self.proxy_manager.proxies else 'direct',
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
            articles = soup.find_all(['h1', 'h2', 'h3'], limit=20)
            
            for article in articles:
                if article.text.strip():
                    title = article.text.strip()
                    
                    # Get article content
                    content_elem = article.find_next(['p', 'div'])
                    article_content = content_elem.text.strip() if content_elem else ""
                    
                    # Analyze for threat intelligence
                    threat_type, urgency, credibility = self.analyze_dark_web_content(title, article_content)
                    actor = self.extract_threat_actor(title, article_content)
                    platforms = self.extract_affected_platforms(title + " " + article_content)
                    
                    iocs = self.extract_dark_web_iocs(title + " " + article_content)
                    
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
                        access_method='direct',
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
            repos = soup.find_all('a', limit=20)
            
            for repo in repos:
                if repo.text.strip():
                    title = repo.text.strip()
                    
                    # Check if it's exploit-related
                    if any(keyword in title.lower() for keyword in ['exploit', 'cve', 'payload', 'shell', 'backdoor']):
                        threat_type = 'exploit_code'
                        urgency = 'high' if any(keyword in title.lower() for keyword in ['cve', '0day', 'zero']) else 'medium'
                        credibility = 0.6  # Public repos moderately credible
                        
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
                            access_method='direct',
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
    
    def analyze_dark_web_content(self, title: str, content: str) -> tuple:
        """Analyze content for threat intelligence parameters"""
        text = (title + " " + content).lower()
        
        # Threat type classification
        threat_type = "general"
        if any(keyword in text for keyword in ['ransomware', 'encrypt', 'decrypt', 'payment']):
            threat_type = "ransomware"
        elif any(keyword in text for keyword in ['leak', 'breach', 'dump', 'database', 'credentials']):
            threat_type = "data_breach"
        elif any(keyword in text for keyword in ['exploit', 'cve', '0day', 'vulnerability']):
            threat_type = "exploit"
        elif any(keyword in text for keyword in ['malware', 'trojan', 'backdoor', 'botnet']):
            threat_type = "malware"
        elif any(keyword in text for keyword in ['ddos', 'booter', 'stresser', 'amplification']):
            threat_type = "ddos_service"
        elif any(keyword in text for keyword in ['phishing', 'credential', 'login', 'password']):
            threat_type = "phishing_kit"
        elif any(keyword in text for keyword in ['card', 'cvv', 'dumps', 'stripe']):
            threat_type = "financial_fraud"
        
        # Urgency assessment
        urgency = "medium"
        if any(keyword in text for keyword in ['critical', 'urgent', 'immediate', '0day', 'active']):
            urgency = "high"
        elif any(keyword in text for keyword in ['new', 'fresh', 'latest']):
            urgency = "medium"
        else:
            urgency = "low"
        
        # Credibility scoring
        credibility = 0.5  # Base credibility for dark web sources
        
        # Boost for specific indicators
        if any(keyword in text for keyword in ['proof', 'screenshot', 'sample', 'demo']):
            credibility += 0.1
        if any(keyword in text for keyword in ['verified', 'trusted', 'reputation']):
            credibility += 0.1
        if len(content) > 100:
            credibility += 0.1
        if any(keyword in text for keyword in ['bitcoin', 'monero', 'crypto']):
            credibility += 0.1
        
        credibility = min(credibility, 1.0)
        
        return threat_type, urgency, credibility
    
    def extract_threat_actor(self, title: str, content: str) -> Optional[str]:
        """Extract threat actor mentions"""
        text = (title + " " + content).lower()
        
        threat_actors = {
            'lockbit': 'LockBit',
            'conti': 'Conti',
            'revil': 'REvil',
            'darkside': 'DarkSide',
            'cl0p': 'CL0P',
            'apt28': 'APT28',
            'apt29': 'APT29',
            'lazarus': 'Lazarus Group',
            'fancy bear': 'Fancy Bear',
            'cozy bear': 'Cozy Bear'
        }
        
        for actor_key, actor_name in threat_actors.items():
            if actor_key in text:
                return actor_name
        
        return None
    
    def extract_target_industry(self, title: str, content: str) -> Optional[str]:
        """Extract targeted industry"""
        text = (title + " " + content).lower()
        
        industries = {
            'healthcare': ['hospital', 'medical', 'healthcare', 'pharma', 'clinic'],
            'financial': ['bank', 'finance', 'payment', 'credit', 'card'],
            'government': ['government', 'military', 'agency', 'federal'],
            'technology': ['software', 'tech', 'saas', 'cloud'],
            'retail': ['retail', 'ecommerce', 'shop', 'store'],
            'education': ['university', 'school', 'education', 'college']
        }
        
        for industry, keywords in industries.items():
            if any(keyword in text for keyword in keywords):
                return industry
        
        return None
    
    def extract_asking_price(self, title: str, content: str) -> Optional[str]:
        """Extract asking price from marketplace listings"""
        text = (title + " " + content).lower()
        
        # Price patterns
        price_patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $1,000.00
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:usd|dollars?)',  # 1,000 USD
            r'(\d+)\s*bitcoin',  # 5 bitcoin
            r'(\d+)\s*btc',  # 5 BTC
            r'(\d+)\s*monero',  # 10 monero
            r'(\d+)\s*xmr',  # 10 XMR
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
            'credentials': ['password', 'credential', 'login', 'account'],
            'database': ['database', 'db', 'sql', 'dump'],
            'personal_info': ['pii', 'personal', 'identity', 'ssn', 'social security'],
            'financial': ['credit card', 'cvv', 'bank', 'payment'],
            'source_code': ['source code', 'code', 'github', 'git'],
            'exploit': ['exploit', '0day', 'vulnerability', 'cve'],
            'malware': ['malware', 'trojan', 'ransomware', 'backdoor']
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
        iocs.extend(ips)
        
        # Domains
        domain_pattern = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
        domains = re.findall(domain_pattern, text)
        iocs.extend(domains)
        
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
        
        return list(set(contacts))
    
    def extract_cryptocurrency_addresses(self, text: str) -> List[str]:
        """Extract cryptocurrency addresses"""
        crypto_addresses = []
        
        # Bitcoin addresses
        btc_pattern = r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'
        btc = re.findall(btc_pattern, text)
        crypto_addresses.extend(btc)
        
        # Monero addresses
        xmr_pattern = r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b'
        xmr = re.findall(xmr_pattern, text)
        crypto_addresses.extend(xmr)
        
        # Ethereum addresses
        eth_pattern = r'\b0x[a-fA-F0-9]{40}\b'
        eth = re.findall(eth_pattern, text)
        crypto_addresses.extend(eth)
        
        return list(set(crypto_addresses))
    
    def extract_affected_platforms(self, text: str) -> List[str]:
        """Extract affected platforms"""
        platforms = []
        
        platform_keywords = {
            'Windows': ['windows', 'win', 'microsoft'],
            'Linux': ['linux', 'ubuntu', 'debian', 'centos'],
            'macOS': ['macos', 'mac', 'osx', 'apple'],
            'Android': ['android', 'google'],
            'iOS': ['ios', 'iphone', 'ipad', 'apple'],
            'Web': ['web', 'website', 'http', 'https'],
            'Database': ['mysql', 'postgresql', 'oracle', 'sql server', 'mongodb'],
            'Cloud': ['aws', 'azure', 'gcp', 'cloud']
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
        
        # Content-based tags
        if threat_type:
            tags.append(threat_type)
        
        if any(keyword in text for keyword in ['ransomware', 'encrypt']):
            tags.append('ransomware')
        if any(keyword in text for keyword in ['leak', 'breach', 'dump']):
            tags.append('data_leak')
        if any(keyword in text for keyword in ['exploit', 'cve', 'vulnerability']):
            tags.append('exploit')
        if any(keyword in text for keyword in ['malware', 'trojan', 'backdoor']):
            tags.append('malware')
        if any(keyword in text for keyword in ['financial', 'bank', 'card']):
            tags.append('financial_crime')
        if any(keyword in text for keyword in ['cryptocurrency', 'bitcoin', 'monero']):
            tags.append('crypto')
        
        return list(set(tags))
    
    async def collect_all_dark_web_intelligence(self) -> List[DarkWebThreatItem]:
        """Collect from all dark web intelligence sources"""
        self.stats['start_time'] = datetime.now(timezone.utc)
        self.collected_items.clear()
        
        logger.info("🌑 Starting Dark Web Intelligence Collection")
        logger.info(f"📊 Total sources: {self.stats['total_sources']}")
        logger.info(f"🔄 Proxies available: {len(self.proxy_manager.proxies)}")
        
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
            
            # Count IOCs and other intelligence
            total_iocs += len(item.iocs)
            total_crypto_addresses += len(item.cryptocurrency_addresses)
            total_contact_info += len(item.contact_info)
            avg_credibility += item.credibility_score
        
        avg_credibility = avg_credibility / len(self.collected_items) if self.collected_items else 0
        
        return {
            'collection_stats': self.stats,
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
            'proxy_performance': {
                'proxies_available': len(self.proxy_manager.proxies),
                'proxies_used': self.stats['proxies_used'],
                'proxy_success_rate': self.stats['successful_sources'] / max(1, self.stats['total_sources'])
            }
        }
    
    def save_dark_web_results(self, output_file: str):
        """Save dark web collection results"""
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
                'tags': item.tags
            }
            items_data.append(item_dict)
        
        output = {
            'collection_metadata': {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'collector_version': 'dark_web_v1.0',
                'total_items': len(self.collected_items),
                'collection_type': 'dark_web_intelligence'
            },
            'collection_summary': self.get_collection_summary(),
            'dark_web_intelligence': items_data
        }
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"💾 Dark web intelligence saved to {output_file}")

async def main():
    """Main function for dark web intelligence collection"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    async with DarkWebIntelligenceCollector(max_workers=8) as collector:
        # Collect dark web intelligence
        items = await collector.collect_all_dark_web_intelligence()
        
        # Get summary
        summary = collector.get_collection_summary()
        
        # Print results
        print("\n" + "="*80)
        print("🌑 DARK WEB INTELLIGENCE COLLECTION RESULTS")
        print("="*80)
        print(f"Total Items Collected: {summary['collection_stats']['total_items']}")
        print(f"Successful Sources: {summary['collection_stats']['successful_sources']}/{summary['collection_stats']['total_sources']}")
        print(f"Collection Duration: {summary['duration_seconds']:.2f} seconds")
        print(f"Collection Rate: {summary['items_per_second']:.2f} items/second")
        print(f"Proxies Used: {summary['proxy_performance']['proxies_used']}")
        
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
        
        print(f"\n🔄 Proxy Performance:")
        print(f"  Proxies Available: {summary['proxy_performance']['proxies_available']}")
        print(f"  Proxies Used: {summary['proxy_performance']['proxies_used']}")
        print(f"  Success Rate: {summary['proxy_performance']['proxy_success_rate']:.1%}")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"data/raw/dark_web_intelligence_{timestamp}.json"
        collector.save_dark_web_results(output_file)
        
        print(f"\n✅ Dark web intelligence collection complete!")
        print(f"📁 Results saved to: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
