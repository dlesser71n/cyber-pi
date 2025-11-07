"""
Unified Intelligence Collector
Combines RSS feeds + Social Intelligence for comprehensive coverage
"""

import logging
import sys
import os
from datetime import datetime
from typing import List, Dict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from collectors.social_intelligence import SocialIntelligenceCollector

logger = logging.getLogger(__name__)


class UnifiedCollector:
    """
    Unified intelligence collection combining:
    - Layer 1: RSS feeds (65 sources, free)
    - Layer 2: Social intelligence (Reddit, real-time)
    - Layer 3: (Future) Dark web, IOC extraction
    """
    
    def __init__(self):
        self.social_collector = None
        
        # Try to initialize social collector if API key available
        try:
            self.social_collector = SocialIntelligenceCollector()
            logger.info("✅ Social Intelligence enabled")
        except ValueError:
            logger.warning("⚠️  ScraperAPI key not found - social intelligence disabled")
    
    def collect_all(self) -> Dict[str, List[Dict]]:
        """
        Collect from all intelligence layers
        
        Returns:
            Dict with keys: 'rss', 'social', 'total'
        """
        results = {
            'rss': [],
            'social': [],
            'total': []
        }
        
        logger.info("=" * 80)
        logger.info("🌐 UNIFIED INTELLIGENCE COLLECTION")
        logger.info("=" * 80)
        
        # Layer 1: RSS feeds (handled by existing parallel_master.py)
        # We'll integrate that separately
        
        # Layer 2: Social Intelligence
        if self.social_collector:
            logger.info("\n📱 Layer 2: Social Intelligence")
            social_items = self.social_collector.collect_all()
            results['social'] = social_items
            results['total'].extend(social_items)
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 COLLECTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"   RSS items: {len(results['rss'])}")
        logger.info(f"   Social items: {len(results['social'])}")
        logger.info(f"   Total items: {len(results['total'])}")
        logger.info("=" * 80)
        
        return results
    
    def save_results(self, results: Dict, output_file: str):
        """Save collection results to JSON"""
        import json
        
        output = {
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'rss_count': len(results['rss']),
                'social_count': len(results['social']),
                'total_count': len(results['total'])
            },
            'items': results['total']
        }
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"💾 Saved {len(results['total'])} items to {output_file}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    collector = UnifiedCollector()
    results = collector.collect_all()
    
    # Save results
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    output_file = f"data/raw/unified_collection_{timestamp}.json"
    collector.save_results(results, output_file)
    
    print(f"\n✅ Unified collection complete!")
    print(f"📊 Total threats captured: {len(results['total'])}")
