"""
Enhanced Intelligence Collector
Expands data collection with additional threat intelligence sources
"""

import asyncio
import aiohttp
import logging
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

# Import configuration
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class EnhancedThreatItem:
    """Enhanced threat intelligence item with additional metadata"""
    # Base fields
    source: str
    title: str
    description: str
    url: str
    timestamp: datetime
    
    # Enhanced fields
    threat_type: str  # malware, phishing, vulnerability, etc.
    severity: str  # low, medium, high, critical
    confidence: float  # 0.0 to 1.0
    industry_sector: Optional[str] = None
    affected_products: List[str] = None
    iocs: List[str] = None  # Indicators of Compromise
    attribution: Optional[str] = None  # Threat actor/group
    tags: List[str] = None
    
    def __post_init__(self):
        if self.affected_products is None:
            self.affected_products = []
        if self.iocs is None:
            self.iocs = []
        if self.tags is None:
            self.tags = []

class EnhancedIntelligenceCollector:
    """
    Enhanced threat intelligence collector with additional sources:
    - Government alerts (CISA, FBI, NSA)
    - Vendor security feeds (Microsoft, Cisco, etc.)
    - International CERT feeds
    - Specialized industry intelligence
    """
    
    def __init__(self, max_workers: int = 16):
        self.max_workers = max_workers
        self.session: Optional[aiohttp.ClientSession] = None
        self.collected_items: List[EnhancedThreatItem] = []
        self.stats = {
            'total_sources': 0,
            'successful_sources': 0,
            'failed_sources': 0,
            'total_items': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Enhanced intelligence sources
        self.sources = {
            # Government Intelligence
            'cisa_alerts': {
                'url': 'https://www.cisa.gov/news-events/cybersecurity-advisories',
                'type': 'government',
                'update_frequency': 'daily',
                'priority': 'high'
            },
            'fbi_cyber': {
                'url': 'https://www.fbi.gov/news/press-releases/press-releases-cyber',
                'type': 'government',
                'update_frequency': 'weekly',
                'priority': 'high'
            },
            'nsa_cybersecurity': {
                'url': 'https://www.nsa.gov/Research/Programs-Initiatives/',
                'type': 'government',
                'update_frequency': 'monthly',
                'priority': 'high'
            },
            
            # International CERTs
            'ncsc_uk': {
                'url': 'https://www.ncsc.gov.uk/news',
                'type': 'international',
                'update_frequency': 'daily',
                'priority': 'medium'
            },
            'bsi_germany': {
                'url': 'https://www.bsi.bund.de/DE/Service-Navi/Presse/Presse/presse_node.html',
                'type': 'international',
                'update_frequency': 'weekly',
                'priority': 'medium'
            },
            'cert_eu': {
                'url': 'https://cert.europa.eu/news/',
                'type': 'international',
                'update_frequency': 'daily',
                'priority': 'medium'
            },
            
            # Vendor Intelligence
            'microsoft_security': {
                'url': 'https://msrc.microsoft.com/blog/feed',
                'type': 'vendor',
                'update_frequency': 'daily',
                'priority': 'high'
            },
            'cisco_talos': {
                'url': 'https://blog.talosintelligence.com/rss/',
                'type': 'vendor',
                'update_frequency': 'daily',
                'priority': 'high'
            },
            'fireeye_threat': {
                'url': 'https://www.fireeye.com/blog/threat-research.xml',
                'type': 'vendor',
                'update_frequency': 'daily',
                'priority': 'high'
            },
            'palo_alto_unit42': {
                'url': 'https://unit42.paloaltonetworks.com/feed/',
                'type': 'vendor',
                'update_frequency': 'daily',
                'priority': 'high'
            },
            
            # Specialized Intelligence
            'ics_cve': {
                'url': 'https://www.cisa.gov/uscert/ncas/alerts',
                'type': 'industrial',
                'update_frequency': 'weekly',
                'priority': 'high'
            },
            'healthcare_cyber': {
                'url': 'https://www.hhs.gov/about/news/index.html',
                'type': 'healthcare',
                'update_frequency': 'weekly',
                'priority': 'medium'
            },
            'financial_cyber': {
                'url': 'https://www.fincen.gov/news/news-releases',
                'type': 'financial',
                'update_frequency': 'weekly',
                'priority': 'medium'
            },
            
            # Emerging Threat Sources
            'zero_day_initiative': {
                'url': 'https://www.zerodayinitiative.com/blog',
                'type': 'vulnerability',
                'update_frequency': 'daily',
                'priority': 'high'
            },
            'exploit_db': {
                'url': 'https://www.exploit-db.com/rss.xml',
                'type': 'exploit',
                'update_frequency': 'daily',
                'priority': 'high'
            },
            'packet_storm': {
                'url': 'https://packetstormsecurity.com/feeds/news.xml',
                'type': 'exploit',
                'update_frequency': 'daily',
                'priority': 'medium'
            }
        }
        
        self.stats['total_sources'] = len(self.sources)
        logger.info(f"🚀 Enhanced Intelligence Collector initialized with {len(self.sources)} sources")
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            limit=self.max_workers,
            limit_per_host=8,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Cyber-Pi-Intelligence/1.0 (Threat Intelligence Collector)',
                'Accept': 'application/rss+xml, application/xml, text/xml, application/json'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def collect_from_source(self, source_name: str, source_config: Dict) -> List[EnhancedThreatItem]:
        """Collect intelligence from a single source"""
        items = []
        
        try:
            logger.info(f"🔍 Collecting from {source_name}")
            
            async with self.session.get(source_config['url']) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Parse based on source type
                    if source_config['url'].endswith('.xml') or 'rss' in source_config['url']:
                        items = await self.parse_rss_feed(content, source_name, source_config)
                    else:
                        items = await self.parse_web_content(content, source_name, source_config)
                    
                    logger.info(f"✅ {source_name}: {len(items)} items collected")
                    self.stats['successful_sources'] += 1
                    
                else:
                    logger.warning(f"⚠️ {source_name}: HTTP {response.status}")
                    self.stats['failed_sources'] += 1
                    
        except Exception as e:
            logger.error(f"❌ {source_name}: {str(e)}")
            self.stats['failed_sources'] += 1
        
        return items
    
    async def parse_rss_feed(self, content: str, source_name: str, source_config: Dict) -> List[EnhancedThreatItem]:
        """Parse RSS/XML feed content"""
        items = []
        
        try:
            root = ET.fromstring(content)
            
            # Handle both RSS and Atom formats
            if root.tag == 'rss':
                entries = root.findall('.//item')
            else:  # Atom or other XML format
                entries = root.findall('.//entry') or root.findall('.//item')
            
            for entry in entries:  # Collect ALL items - filter by intelligence, not arbitrary limits
                try:
                    # Extract basic fields
                    title_elem = entry.find('title') or entry.find('.//title')
                    desc_elem = entry.find('description') or entry.find('.//description') or entry.find('summary')
                    link_elem = entry.find('link') or entry.find('.//link')
                    date_elem = entry.find('pubDate') or entry.find('published') or entry.find('updated')
                    
                    if title_elem is not None and title_elem.text:
                        title = title_elem.text.strip()
                        description = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""
                        url = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                        
                        # Parse timestamp
                        timestamp = datetime.now(timezone.utc)
                        if date_elem is not None and date_elem.text:
                            try:
                                from dateutil import parser
                                timestamp = parser.parse(date_elem.text)
                            except:
                                pass
                        
                        # Enhanced analysis
                        threat_type, severity, confidence = self.analyze_threat_content(title, description)
                        industry_sector = self.identify_industry_sector(title, description, source_config['type'])
                        affected_products = self.extract_affected_products(title, description)
                        iocs = self.extract_iocs(description)
                        attribution = self.extract_attribution(title, description)
                        tags = self.generate_tags(title, description, source_config)
                        
                        item = EnhancedThreatItem(
                            source=source_name,
                            title=title,
                            description=description,
                            url=url,
                            timestamp=timestamp,
                            threat_type=threat_type,
                            severity=severity,
                            confidence=confidence,
                            industry_sector=industry_sector,
                            affected_products=affected_products,
                            iocs=iocs,
                            attribution=attribution,
                            tags=tags
                        )
                        
                        items.append(item)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing entry from {source_name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error parsing RSS from {source_name}: {e}")
        
        return items
    
    async def parse_web_content(self, content: str, source_name: str, source_config: Dict) -> List[EnhancedThreatItem]:
        """Parse web page content (non-RSS)"""
        items = []
        
        try:
            # Simple HTML parsing for basic information
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for headlines/links that might be threat intelligence
            headlines = soup.find_all(['h1', 'h2', 'h3'], limit=20)
            
            for headline in headlines:
                if headline.text.strip():
                    title = headline.text.strip()
                    
                    # Get associated link if available
                    link = headline.find('a')
                    url = link.get('href', '') if link else ''
                    
                    # Get description from following paragraph
                    description = ""
                    next_elem = headline.find_next(['p', 'div'])
                    if next_elem and next_elem.text.strip():
                        description = next_elem.text.strip()[:500]  # Limit length
                    
                    # Enhanced analysis
                    threat_type, severity, confidence = self.analyze_threat_content(title, description)
                    industry_sector = self.identify_industry_sector(title, description, source_config['type'])
                    affected_products = self.extract_affected_products(title, description)
                    iocs = self.extract_iocs(description)
                    attribution = self.extract_attribution(title, description)
                    tags = self.generate_tags(title, description, source_config)
                    
                    item = EnhancedThreatItem(
                        source=source_name,
                        title=title,
                        description=description,
                        url=url,
                        timestamp=datetime.now(timezone.utc),
                        threat_type=threat_type,
                        severity=severity,
                        confidence=confidence,
                        industry_sector=industry_sector,
                        affected_products=affected_products,
                        iocs=iocs,
                        attribution=attribution,
                        tags=tags
                    )
                    
                    items.append(item)
                    
        except Exception as e:
            logger.error(f"❌ Error parsing web content from {source_name}: {e}")
        
        return items
    
    def analyze_threat_content(self, title: str, description: str) -> tuple:
        """Analyze content to determine threat type, severity, and confidence"""
        title_lower = title.lower()
        desc_lower = description.lower()
        content = (title + " " + description).lower()
        
        # Threat type classification
        threat_type = "general"
        if any(keyword in content for keyword in ['vulnerability', 'cve', 'exploit']):
            threat_type = "vulnerability"
        elif any(keyword in content for keyword in ['malware', 'trojan', 'ransomware', 'virus']):
            threat_type = "malware"
        elif any(keyword in content for keyword in ['phishing', 'social engineering', 'fraud']):
            threat_type = "phishing"
        elif any(keyword in content for keyword in ['apt', 'advanced persistent', 'state-sponsored']):
            threat_type = "apt"
        elif any(keyword in content for keyword in ['ddos', 'denial of service']):
            threat_type = "ddos"
        elif any(keyword in content for keyword in ['data breach', 'leak', 'exposure']):
            threat_type = "breach"
        
        # Severity assessment
        severity = "medium"
        high_severity_keywords = ['critical', 'severe', 'urgent', 'zero-day', 'active', 'widespread']
        low_severity_keywords = ['informational', 'advisory', 'guidance', 'best practice']
        
        if any(keyword in content for keyword in high_severity_keywords):
            severity = "high"
        elif any(keyword in content for keyword in low_severity_keywords):
            severity = "low"
        
        # Confidence scoring
        confidence = 0.7  # Base confidence
        if len(description) > 200:
            confidence += 0.1
        if any(keyword in content for keyword in ['confirmed', 'verified', 'observed']):
            confidence += 0.1
        if 'cve-' in content:
            confidence += 0.1
        
        confidence = min(confidence, 1.0)
        
        return threat_type, severity, confidence
    
    def identify_industry_sector(self, title: str, description: str, source_type: str) -> Optional[str]:
        """Identify the industry sector based on content"""
        content = (title + " " + description).lower()
        
        industry_mapping = {
            'healthcare': ['healthcare', 'medical', 'hospital', 'hipaa', 'phi'],
            'financial': ['bank', 'financial', 'payment', 'atm', 'swift', 'pci'],
            'industrial': ['ics', 'scada', 'industrial', 'operational', 'ot'],
            'government': ['government', 'federal', 'agency', 'military', 'defense'],
            'technology': ['software', 'hardware', 'cloud', 'saas', 'api'],
            'retail': ['retail', 'ecommerce', 'point of sale', 'pos']
        }
        
        for sector, keywords in industry_mapping.items():
            if any(keyword in content for keyword in keywords):
                return sector
        
        # Use source type as fallback
        type_mapping = {
            'industrial': 'industrial',
            'healthcare': 'healthcare',
            'financial': 'financial'
        }
        
        return type_mapping.get(source_type)
    
    def extract_affected_products(self, title: str, description: str) -> List[str]:
        """Extract affected products from content"""
        content = (title + " " + description).lower()
        products = []
        
        # Common product patterns
        product_patterns = [
            'windows', 'linux', 'macos', 'android', 'ios',
            'microsoft office', 'adobe', 'chrome', 'firefox',
            'apache', 'nginx', 'openssl', 'cisco', 'juniper',
            'vmware', 'oracle', 'sap', 'sharepoint', 'exchange'
        ]
        
        for product in product_patterns:
            if product in content:
                products.append(product.title())
        
        return list(set(products))  # Remove duplicates
    
    def extract_iocs(self, description: str) -> List[str]:
        """Extract potential indicators of compromise"""
        import re
        
        iocs = []
        
        # IPv4 addresses
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = re.findall(ip_pattern, description)
        iocs.extend(ips)
        
        # Hash patterns (MD5, SHA1, SHA256)
        hash_patterns = [
            r'\b[a-f0-9]{32}\b',  # MD5
            r'\b[a-f0-9]{40}\b',  # SHA1
            r'\b[a-f0-9]{64}\b'   # SHA256
        ]
        
        for pattern in hash_patterns:
            hashes = re.findall(pattern, description)
            iocs.extend(hashes)
        
        # Domain names
        domain_pattern = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
        domains = re.findall(domain_pattern, description)
        iocs.extend(domains)
        
        return list(set(iocs))  # Remove duplicates
    
    def extract_attribution(self, title: str, description: str) -> Optional[str]:
        """Extract potential threat actor attribution"""
        content = (title + " " + description).lower()
        
        # Known threat actor groups
        threat_actors = [
            'apt28', 'apt29', 'fancy bear', 'cozy bear', 'lazarus group',
            'carbanak', 'fin7', 'equation group', 'solarstorm', 'darkside',
            'conti', 'revil', 'lockbit', 'cl0p', 'wannacry'
        ]
        
        for actor in threat_actors:
            if actor in content:
                return actor.title()
        
        return None
    
    def generate_tags(self, title: str, description: str, source_config: Dict) -> List[str]:
        """Generate relevant tags for the threat intelligence"""
        content = (title + " " + description).lower()
        tags = []
        
        # Source type tag
        tags.append(source_config['type'])
        
        # Content-based tags
        tag_keywords = {
            'ransomware': ['ransomware', 'encryption', 'bitcoin', 'monero'],
            'malware': ['malware', 'trojan', 'backdoor', 'botnet'],
            'vulnerability': ['cve', 'vulnerability', 'patch', 'update'],
            'phishing': ['phishing', 'credential', 'login', 'password'],
            'data_breach': ['breach', 'leak', 'exposed', 'stolen'],
            'apt': ['apt', 'advanced persistent', 'state-sponsored'],
            'ddos': ['ddos', 'denial of service', 'amplification']
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in content for keyword in keywords):
                tags.append(tag)
        
        # Severity tag
        if 'critical' in content or 'severe' in content:
            tags.append('high_priority')
        
        return list(set(tags))  # Remove duplicates
    
    async def collect_all_enhanced(self) -> List[EnhancedThreatItem]:
        """Collect from all enhanced intelligence sources"""
        self.stats['start_time'] = datetime.now(timezone.utc)
        self.collected_items.clear()
        
        logger.info("🚀 Starting Enhanced Intelligence Collection")
        logger.info(f"📊 Total sources: {self.stats['total_sources']}")
        
        # Create tasks for parallel collection
        tasks = []
        for source_name, source_config in self.sources.items():
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
        """Get comprehensive collection summary"""
        duration = None
        if self.stats['start_time'] and self.stats['end_time']:
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        # Analyze collected items
        threat_types = {}
        severities = {}
        sources = {}
        
        for item in self.collected_items:
            # Count threat types
            threat_types[item.threat_type] = threat_types.get(item.threat_type, 0) + 1
            
            # Count severities
            severities[item.severity] = severities.get(item.severity, 0) + 1
            
            # Count sources
            sources[item.source] = sources.get(item.source, 0) + 1
        
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
                'severities': severities,
                'top_sources': dict(sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10])
            },
            'enhancement_metrics': {
                'total_iocs_extracted': sum(len(item.iocs) for item in self.collected_items),
                'items_with_attribution': sum(1 for item in self.collected_items if item.attribution),
                'items_with_products': sum(1 for item in self.collected_items if item.affected_products),
                'average_confidence': sum(item.confidence for item in self.collected_items) / len(self.collected_items) if self.collected_items else 0
            }
        }
    
    def save_enhanced_results(self, output_file: str):
        """Save enhanced collection results"""
        # Convert items to dictionaries
        items_data = []
        for item in self.collected_items:
            item_dict = {
                'source': item.source,
                'title': item.title,
                'description': item.description[:500],  # Limit description length
                'url': item.url,
                'timestamp': item.timestamp.isoformat() if item.timestamp else None,
                'threat_type': item.threat_type,
                'severity': item.severity,
                'confidence': item.confidence,
                'industry_sector': item.industry_sector,
                'affected_products': item.affected_products,
                'iocs': item.iocs,
                'attribution': item.attribution,
                'tags': item.tags
            }
            items_data.append(item_dict)
        
        output = {
            'collection_metadata': {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'collector_version': 'enhanced_v1.0',
                'total_items': len(self.collected_items)
            },
            'collection_summary': self.get_collection_summary(),
            'threat_intelligence': items_data
        }
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"💾 Enhanced intelligence saved to {output_file}")

async def main():
    """Main function for enhanced intelligence collection"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    async with EnhancedIntelligenceCollector(max_workers=16) as collector:
        # Collect enhanced intelligence
        items = await collector.collect_all_enhanced()
        
        # Get summary
        summary = collector.get_collection_summary()
        
        # Print results
        print("\n" + "="*80)
        print("🚀 ENHANCED INTELLIGENCE COLLECTION RESULTS")
        print("="*80)
        print(f"Total Items Collected: {summary['collection_stats']['total_items']}")
        print(f"Successful Sources: {summary['collection_stats']['successful_sources']}/{summary['collection_stats']['total_sources']}")
        print(f"Collection Duration: {summary['duration_seconds']:.2f} seconds")
        print(f"Collection Rate: {summary['items_per_second']:.2f} items/second")
        
        print(f"\n📊 Threat Types:")
        for threat_type, count in summary['threat_analysis']['threat_types'].items():
            print(f"  {threat_type}: {count}")
        
        print(f"\n⚠️ Severity Distribution:")
        for severity, count in summary['threat_analysis']['severities'].items():
            print(f"  {severity}: {count}")
        
        print(f"\n🎯 Enhancement Metrics:")
        print(f"  Total IOCs Extracted: {summary['enhancement_metrics']['total_iocs_extracted']}")
        print(f"  Items with Attribution: {summary['enhancement_metrics']['items_with_attribution']}")
        print(f"  Items with Affected Products: {summary['enhancement_metrics']['items_with_products']}")
        print(f"  Average Confidence: {summary['enhancement_metrics']['average_confidence']:.2f}")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"data/raw/enhanced_intelligence_{timestamp}.json"
        collector.save_enhanced_results(output_file)
        
        print(f"\n✅ Enhanced intelligence collection complete!")
        print(f"📁 Results saved to: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
