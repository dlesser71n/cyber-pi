#!/usr/bin/env python3
"""
Dark Web & Underground Threat Intelligence
OPSEC CRITICAL: Use with proper legal authorization and security measures
"""

import requests
from typing import List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DarkWebMonitor:
    """
    Monitor dark web and underground sources for threat intelligence
    
    WARNING: This requires:
    1. Proper legal authorization
    2. Security measures (VPN, Tor, compartmentalization)
    3. OPSEC training
    4. Incident response plan
    
    Use at your own risk. Designed for licensed security professionals only.
    """
    
    def __init__(self, use_tor=False):
        self.use_tor = use_tor
        
        # Ransomware leak sites (clearnet mirrors)
        self.ransomware_sites = {
            'Lockbit': 'http://lockbit-clearnet-mirror.onion',  # Example - NOT real
            'BlackCat/ALPHV': 'http://alphv-clearnet.onion',
            'BlackBasta': 'http://blackbasta-clearnet.onion',
            # NOTE: These are examples. Real sites change frequently.
            # Use threat intel feeds for current URLs.
        }
        
        # Threat intelligence feeds that monitor dark web
        self.clearnet_feeds = {
            'DarkFeed': 'https://darkfeed.io/api/v1/ransomware',  # Paid service
            'Ransomware.live': 'https://api.ransomware.live/recentvictims',  # Free
            'DarkTracer': 'https://darktracer.com/api/victims',  # Paid service
        }
        
        # Initial Access Broker forums (CLEARNET monitoring only!)
        self.iab_monitors = [
            'breach_forums_monitor',
            'raid_forums_monitor',
            'exploit_in_monitor'
        ]
    
    def collect_ransomware_victims(self) -> List[Dict]:
        """
        Collect recent ransomware victims from leak sites
        Uses CLEARNET mirrors/monitoring services ONLY
        """
        items = []
        
        try:
            # Use ransomware.live (free, clearnet, aggregator)
            response = requests.get(
                'https://api.ransomware.live/recentvictims',
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for victim in data[:50]:  # Last 50 victims
                    items.append({
                        'title': f"Ransomware Victim: {victim.get('company', 'Unknown')}",
                        'content': f"Group: {victim.get('group', 'Unknown')}\n"
                                 f"Industry: {victim.get('activity', 'Unknown')}\n"
                                 f"Country: {victim.get('country', 'Unknown')}\n"
                                 f"Posted: {victim.get('published', 'Unknown')}",
                        'link': victim.get('link', ''),
                        'published': victim.get('published', datetime.utcnow().isoformat()),
                        'source': {
                            'name': 'Ransomware.live',
                            'type': 'aggregator',
                            'credibility': 0.90,
                            'category': 'ransomware-victims'
                        },
                        'tags': ['ransomware', 'breach', 'victim', victim.get('group', 'unknown').lower()],
                        'metadata': {
                            'group': victim.get('group'),
                            'industry': victim.get('activity'),
                            'country': victim.get('country')
                        }
                    })
                    
                logger.info(f"✅ Ransomware Victims: {len(items)} collected")
                
        except Exception as e:
            logger.error(f"Ransomware victim collection failed: {e}")
        
        return items
    
    def collect_breach_databases(self) -> List[Dict]:
        """
        Monitor breach database announcements
        Uses Have I Been Pwned API (legitimate service)
        """
        items = []
        
        try:
            # HIBP API - get latest breaches
            response = requests.get(
                'https://haveibeenpwned.com/api/v3/breaches',
                headers={'User-Agent': 'cyber-pi-intel'},
                timeout=10
            )
            
            if response.status_code == 200:
                breaches = response.json()
                
                # Get recent breaches (last 30 days)
                recent_breaches = [
                    b for b in breaches 
                    if self._is_recent(b.get('AddedDate', ''))
                ]
                
                for breach in recent_breaches[:20]:
                    items.append({
                        'title': f"Data Breach: {breach.get('Name', 'Unknown')}",
                        'content': f"Domain: {breach.get('Domain', 'N/A')}\n"
                                 f"Compromised Accounts: {breach.get('PwnCount', 0):,}\n"
                                 f"Breach Date: {breach.get('BreachDate', 'Unknown')}\n"
                                 f"Data Classes: {', '.join(breach.get('DataClasses', []))}",
                        'link': f"https://haveibeenpwned.com/PwnedWebsites#{breach.get('Name', '')}",
                        'published': breach.get('AddedDate', datetime.utcnow().isoformat()),
                        'source': {
                            'name': 'Have I Been Pwned',
                            'type': 'breach-database',
                            'credibility': 0.95,
                            'category': 'data-breach'
                        },
                        'tags': ['breach', 'database', 'credentials'],
                        'metadata': {
                            'accounts_compromised': breach.get('PwnCount', 0),
                            'breach_date': breach.get('BreachDate'),
                            'data_classes': breach.get('DataClasses', [])
                        }
                    })
                    
                logger.info(f"✅ Breaches: {len(items)} recent")
                
        except Exception as e:
            logger.error(f"Breach database collection failed: {e}")
        
        return items
    
    def collect_paste_sites(self) -> List[Dict]:
        """
        Monitor paste sites for credential dumps
        Uses HIBP Pastes API
        """
        # Requires HIBP API key for paste monitoring
        logger.warning("Paste monitoring requires HIBP API key")
        return []
    
    def collect_telegram_breach_channels(self) -> List[Dict]:
        """
        Monitor Telegram channels known for breach announcements
        REQUIRES: Telegram API access and proper OPSEC
        """
        logger.warning("Telegram breach monitoring requires API setup and OPSEC measures")
        
        # Known breach announcement channels (examples):
        # - Various "Combolist" channels
        # - Database leak channels
        # - Credential marketplace channels
        
        # DO NOT ACCESS WITHOUT PROPER AUTHORIZATION AND SECURITY
        
        return []
    
    def monitor_exploit_forums(self) -> List[Dict]:
        """
        Monitor exploit forums for initial access broker (IAB) listings
        REQUIRES: Proper authorization and OPSEC
        """
        logger.warning("Forum monitoring requires authorization and OPSEC measures")
        
        # Forums to monitor (through legitimate threat intel feeds):
        # - Breach Forums
        # - Exploit.in
        # - XSS.is
        # - Various Russian-language forums
        
        # Use commercial threat intel feeds instead:
        # - Intel 471
        # - Flashpoint
        # - Recorded Future
        # - Cyberint
        
        return []
    
    def _is_recent(self, date_string: str, days=30) -> bool:
        """Check if date is within last N days"""
        try:
            date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            age = (datetime.now(date.tzinfo) - date).days
            return age <= days
        except:
            return False
    
    def collect_all(self) -> List[Dict]:
        """
        Collect from all CLEARNET/LEGITIMATE sources
        
        NOTE: This ONLY collects from legitimate, clearnet sources:
        - Ransomware.live (aggregator)
        - Have I Been Pwned (breach database)
        - Other legitimate threat intel feeds
        
        NO direct dark web access is performed.
        """
        all_items = []
        
        # Safe, clearnet sources
        all_items.extend(self.collect_ransomware_victims())
        all_items.extend(self.collect_breach_databases())
        
        # Requires additional setup/authorization:
        # - self.collect_paste_sites()
        # - self.collect_telegram_breach_channels()
        # - self.monitor_exploit_forums()
        
        logger.info(f"📊 Total Dark Web Intel: {len(all_items)} items")
        return all_items


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("⚠️  WARNING: Dark Web Monitoring")
    print("This collector ONLY uses clearnet, legitimate sources:")
    print("- Ransomware.live (aggregator)")
    print("- Have I Been Pwned (breach database)")
    print("\nNO direct dark web access is performed.\n")
    
    collector = DarkWebMonitor()
    items = collector.collect_all()
    
    print(f"\n{'='*60}")
    print(f"DARK WEB & UNDERGROUND INTELLIGENCE")
    print(f"{'='*60}")
    print(f"Total Items: {len(items)}")
    
    # Show samples
    for item in items[:5]:
        print(f"\n{item['source']['name']}: {item['title']}")
