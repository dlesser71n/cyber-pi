#!/usr/bin/env python3
"""
Expanded Social Media Intelligence
Twitter, LinkedIn, Discord, Telegram, GitHub
"""

import requests
import os
from typing import List, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SocialMediaExpanded:
    """Multi-platform social media threat intelligence"""
    
    def __init__(self, twitter_bearer_token=None, github_token=None):
        self.twitter_token = twitter_bearer_token or os.getenv('TWITTER_BEARER_TOKEN')
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        
        # Threat hunter Twitter accounts to monitor
        self.twitter_hunters = [
            'vxunderground',      # Malware research
            'bad_packets',        # Network threats
            'malwarhunterteam',   # Malware samples
            'pancak3lullz',       # Threat intel
            'Cyber_H4shut0sh1',   # Security researcher
            'GossiTheDog',        # Microsoft security
            'John_Hultquist',     # Mandiant
            'threatintel',        # General threat intel
            'CERT_USCFAA',        # Aviation security
            'ICSRansomware'       # OT/ICS threats
        ]
        
        # LinkedIn security groups to monitor
        self.linkedin_groups = [
            'Cyber Security News',
            'Information Security Community',
            'CISO Network',
            'Industrial Cybersecurity'
        ]
        
        # GitHub security advisory repos
        self.github_repos = [
            'advisories/GHSA',           # GitHub Security Advisories
            'CVEProject/cvelistV5',       # CVE List
            'cisagov/vulnrichment'        # CISA enrichment
        ]
    
    def collect_twitter_timeline(self, username: str, max_results=10) -> List[Dict]:
        """Collect from a Twitter account timeline"""
        if not self.twitter_token:
            logger.warning("Twitter API token not configured")
            return []
        
        items = []
        
        try:
            # Twitter API v2
            url = f"https://api.twitter.com/2/tweets/search/recent"
            headers = {"Authorization": f"Bearer {self.twitter_token}"}
            
            params = {
                "query": f"from:{username} -is:retweet",
                "max_results": max_results,
                "tweet.fields": "created_at,author_id,public_metrics",
                "expansions": "author_id"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for tweet in data.get('data', []):
                    # Filter for threat-related content
                    text = tweet['text']
                    if not self._is_threat_related(text):
                        continue
                    
                    items.append({
                        'title': text[:200],  # First 200 chars
                        'content': text,
                        'link': f"https://twitter.com/{username}/status/{tweet['id']}",
                        'published': tweet['created_at'],
                        'source': {
                            'name': f'Twitter @{username}',
                            'type': 'social',
                            'credibility': 0.70,
                            'platform': 'twitter'
                        },
                        'tags': ['twitter', 'social', 'threat-hunter'],
                        'metadata': {
                            'likes': tweet.get('public_metrics', {}).get('like_count', 0),
                            'retweets': tweet.get('public_metrics', {}).get('retweet_count', 0)
                        }
                    })
                    
                logger.info(f"✅ Twitter @{username}: {len(items)} tweets")
                
        except Exception as e:
            logger.error(f"Twitter collection failed for @{username}: {e}")
        
        return items
    
    def collect_all_twitter_hunters(self) -> List[Dict]:
        """Collect from all threat hunter accounts"""
        all_items = []
        
        for hunter in self.twitter_hunters:
            items = self.collect_twitter_timeline(hunter, max_results=5)
            all_items.extend(items)
        
        logger.info(f"📊 Total Twitter: {len(all_items)} threat tweets")
        return all_items
    
    def collect_github_security_advisories(self) -> List[Dict]:
        """Collect from GitHub Security Advisories"""
        if not self.github_token:
            logger.warning("GitHub token not configured")
            return []
        
        items = []
        
        try:
            # GraphQL query for security advisories
            url = "https://api.github.com/graphql"
            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Content-Type": "application/json"
            }
            
            # Get recent advisories (last 7 days)
            query = """
            query {
              securityAdvisories(first: 50, orderBy: {field: PUBLISHED_AT, direction: DESC}) {
                nodes {
                  id
                  summary
                  description
                  severity
                  publishedAt
                  permalink
                  identifiers {
                    type
                    value
                  }
                }
              }
            }
            """
            
            response = requests.post(
                url, 
                headers=headers, 
                json={"query": query},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for advisory in data.get('data', {}).get('securityAdvisories', {}).get('nodes', []):
                    # Extract CVE if present
                    cves = [
                        id_item['value'] 
                        for id_item in advisory.get('identifiers', []) 
                        if id_item['type'] == 'CVE'
                    ]
                    
                    items.append({
                        'title': advisory['summary'],
                        'content': advisory['description'],
                        'link': advisory['permalink'],
                        'published': advisory['publishedAt'],
                        'source': {
                            'name': 'GitHub Security Advisories',
                            'type': 'platform',
                            'credibility': 0.95,
                            'category': 'GHSA'
                        },
                        'severity': advisory.get('severity', 'UNKNOWN'),
                        'cves': cves,
                        'tags': ['github', 'advisory', 'vulnerability']
                    })
                    
                logger.info(f"✅ GitHub: {len(items)} advisories")
                
        except Exception as e:
            logger.error(f"GitHub collection failed: {e}")
        
        return items
    
    def collect_linkedin_posts(self, group_name: str) -> List[Dict]:
        """
        Collect from LinkedIn security groups
        NOTE: LinkedIn has strict API access - may require ScraperAPI or manual monitoring
        """
        logger.warning("LinkedIn collection requires ScraperAPI or manual monitoring")
        
        # Placeholder for LinkedIn integration
        # Would use ScraperAPI to scrape group posts
        # Or LinkedIn Marketing API if access granted
        
        return []
    
    def collect_discord_channels(self) -> List[Dict]:
        """
        Monitor Discord threat intelligence channels
        NOTE: Requires Discord bot token and channel access
        """
        logger.warning("Discord monitoring requires bot setup")
        
        # Popular threat intel Discord servers:
        # - The Many Hats Club
        # - OSINT Curious
        # - Cybersecurity & Infrastructure Security Agency (CISA)
        # - BloodHound Gang
        
        return []
    
    def collect_telegram_channels(self) -> List[Dict]:
        """
        Monitor Telegram cybercrime channels
        NOTE: Requires Telegram API credentials
        """
        logger.warning("Telegram monitoring requires API setup")
        
        # Known threat intel Telegram channels:
        # - @vxunderground
        # - @malwarebazaar
        # - Various ransomware leak channels (OPSEC required!)
        
        return []
    
    def _is_threat_related(self, text: str) -> bool:
        """Check if content is threat-related"""
        keywords = [
            'breach', 'hack', 'vulnerab', 'exploit', 'ransomware',
            'malware', 'cve-', 'zero-day', '0day', 'attack', 'phish',
            'botnet', 'ddos', 'apt', 'threat actor', 'campaign'
        ]
        return any(kw in text.lower() for kw in keywords)
    
    def collect_all(self) -> List[Dict]:
        """Collect from all available social platforms"""
        all_items = []
        
        # Twitter threat hunters
        all_items.extend(self.collect_all_twitter_hunters())
        
        # GitHub security advisories
        all_items.extend(self.collect_github_security_advisories())
        
        # LinkedIn (if available)
        # Discord (if configured)
        # Telegram (if configured)
        
        logger.info(f"📊 Total Social Media: {len(all_items)} items")
        return all_items


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    collector = SocialMediaExpanded()
    items = collector.collect_all()
    
    print(f"\n{'='*60}")
    print(f"EXPANDED SOCIAL MEDIA INTELLIGENCE")
    print(f"{'='*60}")
    print(f"Total Items: {len(items)}")
    
    # Show samples by platform
    platforms = {}
    for item in items:
        platform = item['source'].get('platform', item['source'].get('name', 'other'))
        platforms[platform] = platforms.get(platform, 0) + 1
    
    print("\nBreakdown by Platform:")
    for platform, count in platforms.items():
        print(f"  {platform}: {count} items")
