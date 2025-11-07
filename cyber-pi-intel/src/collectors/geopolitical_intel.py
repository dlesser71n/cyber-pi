#!/usr/bin/env python3
"""
Geopolitical Intelligence Collector
Monitors nation-state activity, diplomatic incidents, sanctions, elections

Correlates geopolitical events with cyber threats:
- Diplomatic incidents → Cyber retaliation (24-48h)
- Sanctions → Targeted attacks (12-24h)
- Elections → APT campaigns (weeks)
"""

import requests
import feedparser
from typing import List, Dict
from datetime import datetime, timezone, timedelta
import logging
import re

logger = logging.getLogger(__name__)


class GeopoliticalCollector:
    """Collect geopolitical events relevant to cyber threats"""

    def __init__(self):
        # News sources focusing on cyber and geopolitics
        self.news_sources = [
            {
                "name": "Reuters Cybersecurity",
                "url": "https://www.reuters.com/arc/outboundfeeds/v3/category/cybersecurity/?outputType=xml",
                "credibility": 0.95,
                "category": "news"
            },
            {
                "name": "Reuters Technology",
                "url": "https://www.reuters.com/arc/outboundfeeds/v3/category/technology/?outputType=xml",
                "credibility": 0.95,
                "category": "news"
            },
            {
                "name": "BBC Technology",
                "url": "http://feeds.bbci.co.uk/news/technology/rss.xml",
                "credibility": 0.90,
                "category": "news"
            },
            {
                "name": "Associated Press Security",
                "url": "https://apnews.com/hub/technology",
                "credibility": 0.95,
                "category": "news"
            }
        ]

        # Sanctions and government advisories
        self.gov_sources = [
            {
                "name": "US Treasury Sanctions",
                "url": "https://home.treasury.gov/policy-issues/financial-sanctions/recent-actions",
                "credibility": 1.0,
                "category": "sanctions"
            },
            {
                "name": "State Department Travel Advisories",
                "url": "https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories.html",
                "credibility": 1.0,
                "category": "advisory"
            },
            {
                "name": "CISA Alerts",
                "url": "https://www.cisa.gov/uscert/ncas/alerts.xml",
                "credibility": 1.0,
                "category": "technical"
            }
        ]

        # Think tanks and research organizations
        self.research_sources = [
            {
                "name": "CSIS Cybersecurity",
                "url": "https://www.csis.org/programs/strategic-technologies-program/cybersecurity-and-governance/feed",
                "credibility": 0.85,
                "category": "research"
            },
            {
                "name": "Atlantic Council Cyber",
                "url": "https://www.atlanticcouncil.org/programs/scowcroft-center-for-strategy-and-security/cyber-statecraft-initiative/feed/",
                "credibility": 0.85,
                "category": "research"
            }
        ]

        # Nation-state threat actors to monitor
        self.threat_actors = {
            'russia': ['APT28', 'APT29', 'Cozy Bear', 'Fancy Bear', 'Sandworm'],
            'china': ['APT1', 'APT40', 'APT41', 'Volt Typhoon'],
            'north_korea': ['Lazarus', 'APT38', 'BlueNoroff', 'Kimsuky'],
            'iran': ['APT33', 'APT34', 'APT39', 'Charming Kitten'],
            'israel': ['NSO Group', 'Candiru'],
            'vietnam': ['APT32', 'OceanLotus']
        }

        # Keywords for geopolitical-cyber correlation
        self.correlation_keywords = [
            'cyber attack', 'hacking', 'espionage', 'disinformation',
            'election interference', 'sanctions', 'diplomatic crisis',
            'military conflict', 'trade war', 'critical infrastructure'
        ]

    def collect_news_feeds(self) -> List[Dict]:
        """Collect from news RSS feeds"""
        items = []

        for source in self.news_sources:
            try:
                feed = feedparser.parse(source['url'])

                for entry in feed.entries[:10]:  # Latest 10 per source
                    # Only include if cyber-related
                    if not self._is_cyber_relevant(entry.get('title', '') + entry.get('summary', '')):
                        continue

                    # Extract nation-states mentioned
                    nations = self._extract_nation_states(entry.get('title', '') + entry.get('summary', ''))

                    items.append({
                        'title': entry.get('title', 'Unknown'),
                        'content': entry.get('summary', ''),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', datetime.now(timezone.utc).isoformat()),
                        'source': {
                            'name': source['name'],
                            'type': 'news',
                            'credibility': source['credibility'],
                            'category': 'geopolitical'
                        },
                        'tags': ['geopolitical', 'news', 'nation-state'] + nations,
                        'metadata': {
                            'nations_mentioned': nations,
                            'threat_correlation': 'high' if len(nations) > 0 else 'medium'
                        }
                    })

                logger.info(f"✅ {source['name']}: {len([i for i in items if i['source']['name'] == source['name']])} items")

            except Exception as e:
                logger.error(f"Failed to collect from {source['name']}: {e}")

        return items

    def collect_sanctions_data(self) -> List[Dict]:
        """
        Monitor US Treasury sanctions
        Note: Requires scraping or API access for real-time data
        """
        items = []

        # Placeholder: Would scrape Treasury website or use OFAC SDN list
        # For now, we'll note this requires additional implementation

        logger.warning("Sanctions collection requires Treasury API or web scraping")

        return items

    def collect_research_feeds(self) -> List[Dict]:
        """Collect from think tank RSS feeds"""
        items = []

        for source in self.research_sources:
            try:
                feed = feedparser.parse(source['url'])

                for entry in feed.entries[:5]:  # Latest 5 per source
                    items.append({
                        'title': entry.get('title', 'Unknown'),
                        'content': entry.get('summary', ''),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', datetime.now(timezone.utc).isoformat()),
                        'source': {
                            'name': source['name'],
                            'type': 'research',
                            'credibility': source['credibility'],
                            'category': 'geopolitical'
                        },
                        'tags': ['geopolitical', 'research', 'analysis'],
                        'metadata': {
                            'analysis_depth': 'high',
                            'forward_looking': True
                        }
                    })

                logger.info(f"✅ {source['name']}: {len([i for i in items if i['source']['name'] == source['name']])} items")

            except Exception as e:
                logger.error(f"Failed to collect from {source['name']}: {e}")

        return items

    def correlate_with_apt_activity(self, items: List[Dict]) -> List[Dict]:
        """
        Correlate geopolitical events with known APT groups
        Adds threat intelligence context to geopolitical events
        """
        for item in items:
            nations = item.get('metadata', {}).get('nations_mentioned', [])

            relevant_apts = []
            for nation in nations:
                if nation.lower() in self.threat_actors:
                    relevant_apts.extend(self.threat_actors[nation.lower()])

            if relevant_apts:
                item['metadata']['related_apt_groups'] = relevant_apts
                item['metadata']['apt_correlation'] = True
                item['tags'].append('apt-relevant')

        return items

    def predict_cyber_retaliation_window(self, items: List[Dict]) -> List[Dict]:
        """
        Add predicted cyber attack windows based on event type
        """
        for item in items:
            title = item.get('title', '').lower()
            content = item.get('content', '').lower()
            combined = title + ' ' + content

            # Diplomatic incident → 24-48h cyber retaliation
            if any(kw in combined for kw in ['diplomatic', 'expel', 'ambassador', 'sanction']):
                item['metadata']['retaliation_window'] = '24-48 hours'
                item['metadata']['threat_level'] = 'high'
                item['severity'] = 'high'

            # Military action → Immediate cyber operations
            elif any(kw in combined for kw in ['military', 'strike', 'invasion', 'conflict']):
                item['metadata']['retaliation_window'] = '0-12 hours'
                item['metadata']['threat_level'] = 'critical'
                item['severity'] = 'critical'

            # Election period → Weeks of APT campaigns
            elif any(kw in combined for kw in ['election', 'voting', 'ballot', 'campaign']):
                item['metadata']['retaliation_window'] = '1-4 weeks'
                item['metadata']['threat_level'] = 'medium'
                item['severity'] = 'medium'

            # Trade/economic → 12-24h targeted attacks
            elif any(kw in combined for kw in ['trade war', 'tariff', 'embargo', 'economic']):
                item['metadata']['retaliation_window'] = '12-24 hours'
                item['metadata']['threat_level'] = 'medium'
                item['severity'] = 'medium'

        return items

    def _is_cyber_relevant(self, text: str) -> bool:
        """Check if content is cyber-relevant"""
        return any(kw in text.lower() for kw in self.correlation_keywords)

    def _extract_nation_states(self, text: str) -> List[str]:
        """Extract mentioned nation-states"""
        nations = []

        # Common nation-state mentions in cyber context
        nation_patterns = {
            'Russia': ['russia', 'russian', 'kremlin', 'moscow'],
            'China': ['china', 'chinese', 'beijing', 'prc'],
            'North Korea': ['north korea', 'dprk', 'pyongyang'],
            'Iran': ['iran', 'iranian', 'tehran'],
            'Israel': ['israel', 'israeli', 'tel aviv'],
            'USA': ['united states', 'u.s.', 'america', 'washington'],
            'Ukraine': ['ukraine', 'ukrainian', 'kyiv'],
            'Taiwan': ['taiwan', 'taiwanese', 'taipei']
        }

        text_lower = text.lower()
        for nation, patterns in nation_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                nations.append(nation)

        return nations

    def collect_all(self) -> List[Dict]:
        """Collect from all geopolitical sources"""
        all_items = []

        # Collect from news feeds
        news_items = self.collect_news_feeds()
        all_items.extend(news_items)

        # Collect from research sources
        research_items = self.collect_research_feeds()
        all_items.extend(research_items)

        # Sanctions (placeholder)
        sanctions_items = self.collect_sanctions_data()
        all_items.extend(sanctions_items)

        # Add APT correlations
        all_items = self.correlate_with_apt_activity(all_items)

        # Predict retaliation windows
        all_items = self.predict_cyber_retaliation_window(all_items)

        logger.info(f"📊 Total Geopolitical Intel: {len(all_items)} items")
        return all_items


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    collector = GeopoliticalCollector()
    items = collector.collect_all()

    print(f"\n{'='*60}")
    print(f"GEOPOLITICAL INTELLIGENCE COLLECTION")
    print(f"{'='*60}")
    print(f"Total Items: {len(items)}")

    # Show breakdown
    by_source = {}
    critical = 0
    high = 0

    for item in items:
        source = item['source']['name']
        by_source[source] = by_source.get(source, 0) + 1

        severity = item.get('severity', '')
        if severity == 'critical':
            critical += 1
        elif severity == 'high':
            high += 1

    print(f"\nBy Source:")
    for source, count in by_source.items():
        print(f"  {source}: {count}")

    print(f"\nThreat Levels:")
    print(f"  Critical: {critical}")
    print(f"  High: {high}")

    # Show samples with APT correlation
    apt_correlated = [i for i in items if i.get('metadata', {}).get('apt_correlation')]
    if apt_correlated:
        print(f"\nAPT-Correlated Events ({len(apt_correlated)}):")
        for item in apt_correlated[:3]:
            print(f"  - {item['title'][:70]}...")
            print(f"    Nations: {', '.join(item['metadata'].get('nations_mentioned', []))}")
            print(f"    APTs: {', '.join(item['metadata'].get('related_apt_groups', [])[:3])}")
            print(f"    Retaliation: {item['metadata'].get('retaliation_window', 'Unknown')}")
            print()
