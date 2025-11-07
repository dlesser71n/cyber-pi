#!/usr/bin/env python3
"""
Unified Threat Intelligence Collector
Integrates ALL collection sources:
- Technical (CVEs, RSS)
- Social Media (Twitter, Reddit, GitHub)
- OT/ICS (SCADA, Industrial)
- Dark Web (Ransomware, Breaches)
- Geopolitical
"""

import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import logging

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class UnifiedThreatCollector:
    """Master collector that integrates all intelligence sources"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.stats = {
            'technical': 0,
            'social': 0,
            'ot_ics': 0,
            'dark_web': 0,
            'total': 0
        }
        
    def collect_technical_threats(self) -> List[Dict]:
        """
        Collect technical threats (CVEs, Advisories, RSS)
        Uses existing cyber-pi RSS collectors
        """
        items = []
        
        try:
            # Import existing cyber-pi collector
            from src.collectors.unified_collector import UnifiedCollector
            
            collector = UnifiedCollector()
            items = collector.collect_all()
            
            self.stats['technical'] = len(items)
            logger.info(f"✅ Technical: {len(items)} items")
            
        except Exception as e:
            logger.error(f"Technical collection failed: {e}")
        
        return items
    
    def collect_social_intelligence(self) -> List[Dict]:
        """
        Collect from social media platforms
        Twitter, Reddit, LinkedIn, GitHub
        """
        items = []
        
        try:
            # Reddit (existing)
            from src.collectors.social_intelligence import SocialIntelligenceCollector
            reddit_collector = SocialIntelligenceCollector()
            items.extend(reddit_collector.collect_all())
            
            # Expanded social (new)
            from src.collectors.social_media_expansion import SocialMediaExpanded
            social_collector = SocialMediaExpanded()
            items.extend(social_collector.collect_all())
            
            self.stats['social'] = len(items)
            logger.info(f"✅ Social Media: {len(items)} items")
            
        except Exception as e:
            logger.error(f"Social collection failed: {e}")
        
        return items
    
    def collect_ot_ics_threats(self) -> List[Dict]:
        """
        Collect OT/ICS/SCADA specific threats
        Industrial control systems, critical infrastructure
        """
        items = []
        
        try:
            from src.collectors.ot_ics_collector import OT_ICS_Collector
            
            collector = OT_ICS_Collector()
            items = collector.collect_all()
            
            self.stats['ot_ics'] = len(items)
            logger.info(f"✅ OT/ICS: {len(items)} items")
            
        except Exception as e:
            logger.error(f"OT/ICS collection failed: {e}")
        
        return items
    
    def collect_dark_web_intel(self) -> List[Dict]:
        """
        Collect from dark web monitoring (clearnet sources only)
        Ransomware victims, breaches, credential dumps
        """
        items = []
        
        try:
            from src.collectors.dark_web_monitor import DarkWebMonitor
            
            collector = DarkWebMonitor()
            items = collector.collect_all()
            
            self.stats['dark_web'] = len(items)
            logger.info(f"✅ Dark Web: {len(items)} items")
            
        except Exception as e:
            logger.error(f"Dark web collection failed: {e}")
        
        return items
    
    def collect_all(self) -> List[Dict]:
        """Collect from ALL sources"""
        print("\n" + "="*60)
        print("🔥 UNIFIED THREAT INTELLIGENCE COLLECTION")
        print("="*60)
        print()
        
        all_items = []
        
        # 1. Technical Threats (RSS, CVEs, Advisories)
        print("📡 Collecting Technical Threats...")
        all_items.extend(self.collect_technical_threats())
        
        # 2. Social Media Intelligence
        print("📱 Collecting Social Media Intelligence...")
        all_items.extend(self.collect_social_intelligence())
        
        # 3. OT/ICS Threats
        print("🏭 Collecting OT/ICS Threats...")
        all_items.extend(self.collect_ot_ics_threats())
        
        # 4. Dark Web Intelligence
        print("🕵️  Collecting Dark Web Intelligence...")
        all_items.extend(self.collect_dark_web_intel())
        
        self.stats['total'] = len(all_items)
        
        # Print summary
        self.print_stats()
        
        return all_items
    
    def filter_by_industry(self, items: List[Dict], industry: str) -> List[Dict]:
        """Filter threats by industry"""
        # Use existing client_filter from cyber-pi
        try:
            from src.processors.client_filter import ClientFilter
            
            filter_processor = ClientFilter()
            filtered = filter_processor.filter_for_client(items, industry)
            
            logger.info(f"Filtered for {industry}: {len(filtered)} items")
            return filtered
            
        except Exception as e:
            logger.error(f"Industry filtering failed: {e}")
            return items
    
    def print_stats(self):
        """Print collection statistics"""
        print("\n" + "="*60)
        print("📊 COLLECTION STATISTICS")
        print("="*60)
        print(f"Technical Threats:  {self.stats['technical']:>6} items")
        print(f"Social Intelligence: {self.stats['social']:>6} items")
        print(f"OT/ICS Threats:     {self.stats['ot_ics']:>6} items")
        print(f"Dark Web Intel:     {self.stats['dark_web']:>6} items")
        print("-" * 60)
        print(f"TOTAL:              {self.stats['total']:>6} items")
        print("="*60)
        print()
        
        # Show breakdown percentages
        if self.stats['total'] > 0:
            print("Source Distribution:")
            for source, count in self.stats.items():
                if source != 'total' and count > 0:
                    pct = (count / self.stats['total']) * 100
                    print(f"  {source:20} {pct:>5.1f}%")
            print()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    collector = UnifiedThreatCollector()
    
    # Collect everything
    all_threats = collector.collect_all()
    
    # Show samples from each category
    print("\n" + "="*60)
    print("🔍 SAMPLE THREATS BY CATEGORY")
    print("="*60)
    
    categories = {}
    for item in all_threats:
        cat = item.get('source', {}).get('category', 'other')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    for category, items in categories.items():
        print(f"\n{category.upper()} ({len(items)} total):")
        for item in items[:2]:  # Show 2 samples
            print(f"  - {item['title'][:70]}...")
    
    print("\n" + "="*60)
    print("✅ COLLECTION COMPLETE")
    print("="*60)
