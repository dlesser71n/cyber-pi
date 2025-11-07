#!/usr/bin/env python3
"""
OT/ICS/SCADA Threat Intelligence Collector
Monitors industrial control systems, SCADA, critical infrastructure
"""

import feedparser
import requests
from typing import List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OT_ICS_Collector:
    """Collect threats specific to Operational Technology & Industrial Control Systems"""
    
    def __init__(self):
        self.sources = {
            # US Government
            "ICS-CERT": "https://www.cisa.gov/news-events/cybersecurity-advisories/rss.xml",
            
            # Industry Organizations  
            "Dragos": "https://www.dragos.com/feed/",
            "Claroty": "https://claroty.com/team82/research/rss",
            
            # Vendor Specific
            "Siemens Security": "https://new.siemens.com/global/en/products/services/cert.html",  # Web scrape
            "Rockwell Automation": "https://www.rockwellautomation.com/en-us/support/product-security-advisories.html",
            
            # Research
            "SANS ICS": "https://ics.sans.org/blog/rss.xml",
        }
        
        self.keywords = [
            # OT/ICS Systems
            'scada', 'ics', 'plc', 'hmi', 'dcs', 'rtu', 'iiot',
            'industrial control', 'operational technology',
            
            # Vendors
            'siemens', 'schneider', 'rockwell', 'abb', 'ge digital',
            'honeywell', 'emerson', 'yokogawa',
            
            # Protocols
            'modbus', 'dnp3', 'profinet', 'ethercat', 'opcua',
            'bacnet', 'profibus', 's7comm',
            
            # Sectors
            'critical infrastructure', 'power grid', 'oil and gas',
            'water treatment', 'manufacturing', 'energy sector',
            'pipeline', 'refinery', 'nuclear'
        ]
        
    def collect_ics_cert(self) -> List[Dict]:
        """Collect from ICS-CERT advisories"""
        items = []
        
        try:
            feed = feedparser.parse(self.sources["ICS-CERT"])
            
            for entry in feed.entries[:50]:  # Last 50 advisories
                # Filter for OT/ICS relevance
                text = (entry.title + ' ' + entry.get('summary', '')).lower()
                
                if not any(kw in text for kw in self.keywords):
                    continue
                
                items.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.get('published', datetime.utcnow().isoformat()),
                    'content': entry.get('summary', ''),
                    'source': {
                        'name': 'ICS-CERT',
                        'type': 'government',
                        'credibility': 0.95,
                        'category': 'OT/ICS'
                    },
                    'tags': ['ics', 'scada', 'critical-infrastructure', 'government']
                })
                
            logger.info(f"✅ ICS-CERT: {len(items)} advisories")
            
        except Exception as e:
            logger.error(f"ICS-CERT collection failed: {e}")
            
        return items
    
    def collect_dragos(self) -> List[Dict]:
        """Collect from Dragos OT threat intelligence"""
        items = []
        
        try:
            feed = feedparser.parse(self.sources["Dragos"])
            
            for entry in feed.entries[:20]:
                items.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.get('published', datetime.utcnow().isoformat()),
                    'content': entry.get('summary', ''),
                    'source': {
                        'name': 'Dragos',
                        'type': 'vendor',
                        'credibility': 0.90,
                        'category': 'OT/ICS'
                    },
                    'tags': ['ics', 'ot', 'dragos', 'threat-intelligence']
                })
                
            logger.info(f"✅ Dragos: {len(items)} reports")
            
        except Exception as e:
            logger.error(f"Dragos collection failed: {e}")
            
        return items
    
    def collect_claroty(self) -> List[Dict]:
        """Collect from Claroty Team82 research"""
        items = []
        
        try:
            feed = feedparser.parse(self.sources["Claroty"])
            
            for entry in feed.entries[:20]:
                items.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.get('published', datetime.utcnow().isoformat()),
                    'content': entry.get('summary', ''),
                    'source': {
                        'name': 'Claroty Team82',
                        'type': 'research',
                        'credibility': 0.90,
                        'category': 'OT/ICS'
                    },
                    'tags': ['ics', 'ot', 'research', 'vulnerabilities']
                })
                
            logger.info(f"✅ Claroty: {len(items)} research")
            
        except Exception as e:
            logger.error(f"Claroty collection failed: {e}")
            
        return items
    
    def collect_all(self) -> List[Dict]:
        """Collect from all OT/ICS sources"""
        all_items = []
        
        all_items.extend(self.collect_ics_cert())
        all_items.extend(self.collect_dragos())
        all_items.extend(self.collect_claroty())
        
        logger.info(f"📊 Total OT/ICS: {len(all_items)} items")
        return all_items
    
    def filter_by_industry(self, items: List[Dict], industry: str) -> List[Dict]:
        """Filter OT/ICS threats by specific industry"""
        industry_keywords = {
            'energy': ['power', 'grid', 'electric', 'utility', 'generation'],
            'oil_gas': ['oil', 'gas', 'pipeline', 'refinery', 'petrochemical'],
            'water': ['water', 'wastewater', 'treatment plant', 'municipal'],
            'manufacturing': ['factory', 'assembly', 'production line', 'plant'],
            'transportation': ['railway', 'metro', 'traffic', 'aviation'],
            'healthcare': ['hospital', 'medical device', 'patient', 'clinical']
        }
        
        keywords = industry_keywords.get(industry.lower(), [])
        if not keywords:
            return items
        
        filtered = []
        for item in items:
            text = (item['title'] + ' ' + item.get('content', '')).lower()
            if any(kw in text for kw in keywords):
                filtered.append(item)
        
        return filtered


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    collector = OT_ICS_Collector()
    items = collector.collect_all()
    
    print(f"\n{'='*60}")
    print(f"OT/ICS THREAT INTELLIGENCE COLLECTION")
    print(f"{'='*60}")
    print(f"Total Items: {len(items)}")
    
    # Show samples
    for item in items[:5]:
        print(f"\n{item['source']['name']}: {item['title'][:60]}...")
