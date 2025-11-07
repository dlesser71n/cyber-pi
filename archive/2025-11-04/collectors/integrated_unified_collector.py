"""
Integrated Unified Intelligence Collector
Combines existing RSS/social collection with enhanced intelligence sources
"""

import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import existing collectors
sys.path.append(os.path.dirname(__file__))
from rss_collector import RSSCollector
from social_intelligence import SocialIntelligenceCollector
from enhanced_intelligence_collector import EnhancedIntelligenceCollector

logger = logging.getLogger(__name__)

class IntegratedUnifiedCollector:
    """
    Integrated collector combining all intelligence sources:
    - Original RSS feeds (65+ sources)
    - Social intelligence (Reddit, Twitter)
    - Enhanced government/vendor intelligence (16+ sources)
    - Future: Commercial feeds, dark web monitoring
    """
    
    def __init__(self):
        self.rss_collector = None
        self.social_collector = None
        self.enhanced_collector = None
        self.collection_results = {}
        
        logger.info("🚀 Integrated Unified Intelligence Collector initialized")
    
    async def collect_all_intelligence(self) -> Dict[str, Any]:
        """
        Collect from all intelligence sources in parallel
        """
        logger.info("=" * 80)
        logger.info("🌐 INTEGRATED INTELLIGENCE COLLECTION")
        logger.info("=" * 80)
        
        start_time = datetime.now(timezone.utc)
        
        # Collection tasks
        collection_tasks = []
        source_types = []
        
        # RSS Collector (existing)
        async def collect_rss():
            try:
                self.rss_collector = RSSCollector(max_workers=32)
                return self.rss_collector.collect_all_feeds()
            except Exception as e:
                logger.error(f"❌ RSS collector failed: {e}")
                return []
        
        # Social Intelligence Collector (existing)
        async def collect_social():
            try:
                self.social_collector = SocialIntelligenceCollector()
                return self.social_collector.collect_all()
            except ValueError as e:
                logger.warning(f"⚠️ Social collector: {e}")
                return []
            except Exception as e:
                logger.error(f"❌ Social collector failed: {e}")
                return []
        
        # Enhanced Intelligence Collector (new)
        async def collect_enhanced():
            try:
                async with EnhancedIntelligenceCollector(max_workers=16) as enhanced:
                    return await enhanced.collect_all_enhanced()
            except Exception as e:
                logger.error(f"❌ Enhanced collector failed: {e}")
                return []
        
        # Add all collection tasks
        collection_tasks.append(collect_rss())
        source_types.append('rss')
        
        collection_tasks.append(collect_social())
        source_types.append('social')
        
        collection_tasks.append(collect_enhanced())
        source_types.append('enhanced')
        
        # Execute all collections in parallel
        results = await asyncio.gather(*collection_tasks, return_exceptions=True)
        
        # Process results
        processed_results = {}
        total_items = 0
        
        for source_type, result in zip(source_types, results):
            if isinstance(result, list):
                processed_results[source_type] = result
                total_items += len(result)
                logger.info(f"✅ {source_type.upper()}: {len(result)} items collected")
            elif isinstance(result, Exception):
                logger.error(f"❌ {source_type.upper()}: {result}")
                processed_results[source_type] = []
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        # Create comprehensive summary
        self.collection_results = {
            'collection_metadata': {
                'timestamp': end_time.isoformat(),
                'collector_version': 'integrated_v1.0',
                'total_sources': self._count_total_sources(),
                'collection_duration_seconds': duration,
                'total_items_collected': total_items
            },
            'source_breakdown': {
                'rss_feeds': {
                    'items_count': len(processed_results.get('rss', [])),
                    'description': '65+ cybersecurity RSS feeds'
                },
                'social_intelligence': {
                    'items_count': len(processed_results.get('social', [])),
                    'description': 'Reddit, Twitter social monitoring'
                },
                'enhanced_intelligence': {
                    'items_count': len(processed_results.get('enhanced', [])),
                    'description': 'Government, vendor, exploit intelligence'
                }
            },
            'performance_metrics': {
                'items_per_second': total_items / duration if duration > 0 else 0,
                'collection_efficiency': f"{total_items/duration:.1f}" if duration > 0 else "0"
            },
            'threat_analysis': self._analyze_threats(processed_results),
            'enhancement_metrics': self._calculate_enhancement_metrics(processed_results),
            'all_intelligence': self._merge_all_intelligence(processed_results)
        }
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 INTEGRATED COLLECTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Sources: {self._count_total_sources()}")
        logger.info(f"Total Items: {total_items:,}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Rate: {total_items/duration:.1f} items/second" if duration > 0 else "Rate: 0 items/second")
        
        for source_type, data in self.collection_results['source_breakdown'].items():
            logger.info(f"  {source_type}: {data['items_count']} items ({data['description']})")
        
        logger.info("=" * 80)
        
        return self.collection_results
    
    def _count_total_sources(self) -> int:
        """Count total number of sources across all collectors"""
        # RSS: ~65 sources
        # Social: Reddit + Twitter
        # Enhanced: 16 sources
        return 65 + 2 + 16  # Approximate total
    
    def _analyze_threats(self, results: Dict[str, List]) -> Dict[str, Any]:
        """Analyze threats across all collected intelligence"""
        threat_types = {}
        severities = {}
        sources = {}
        
        # Analyze enhanced intelligence (has structured data)
        for item in results.get('enhanced', []):
            if hasattr(item, 'threat_type'):
                threat_types[item.threat_type] = threat_types.get(item.threat_type, 0) + 1
            if hasattr(item, 'severity'):
                severities[item.severity] = severities.get(item.severity, 0) + 1
            if hasattr(item, 'source'):
                sources[item.source] = sources.get(item.source, 0) + 1
        
        # Count other sources
        for source_type in ['rss', 'social']:
            sources[source_type] = len(results.get(source_type, []))
        
        return {
            'threat_types': threat_types,
            'severities': severities,
            'top_sources': dict(sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def _calculate_enhancement_metrics(self, results: Dict[str, List]) -> Dict[str, Any]:
        """Calculate enhancement metrics from collected data"""
        enhanced_items = results.get('enhanced', [])
        
        total_iocs = 0
        items_with_attribution = 0
        items_with_products = 0
        avg_confidence = 0.0
        
        for item in enhanced_items:
            if hasattr(item, 'iocs') and item.iocs:
                total_iocs += len(item.iocs)
            if hasattr(item, 'attribution') and item.attribution:
                items_with_attribution += 1
            if hasattr(item, 'affected_products') and item.affected_products:
                items_with_products += 1
            if hasattr(item, 'confidence'):
                avg_confidence += item.confidence
        
        if enhanced_items:
            avg_confidence = avg_confidence / len(enhanced_items)
        
        return {
            'total_iocs_extracted': total_iocs,
            'items_with_attribution': items_with_attribution,
            'items_with_products': items_with_products,
            'average_confidence': avg_confidence,
            'enhanced_coverage_percentage': (len(enhanced_items) / sum(len(r) for r in results.values())) * 100 if results else 0
        }
    
    def _merge_all_intelligence(self, results: Dict[str, List]) -> List[Dict]:
        """Merge all intelligence into unified format"""
        all_items = []
        
        # Process RSS items
        for item in results.get('rss', []):
            unified_item = {
                'source_type': 'rss',
                'source': item.get('source', 'unknown'),
                'title': item.get('title', ''),
                'description': item.get('description', ''),
                'url': item.get('url', ''),
                'timestamp': item.get('timestamp', datetime.now(timezone.utc).isoformat()),
                'threat_type': 'general',
                'severity': 'medium',
                'confidence': 0.5,
                'industry_sector': None,
                'affected_products': [],
                'iocs': [],
                'attribution': None,
                'tags': ['rss']
            }
            all_items.append(unified_item)
        
        # Process Social items
        for item in results.get('social', []):
            unified_item = {
                'source_type': 'social',
                'source': item.get('source', 'social'),
                'title': item.get('title', ''),
                'description': item.get('description', ''),
                'url': item.get('url', ''),
                'timestamp': item.get('timestamp', datetime.now(timezone.utc).isoformat()),
                'threat_type': 'social_threat',
                'severity': 'medium',
                'confidence': 0.6,
                'industry_sector': None,
                'affected_products': [],
                'iocs': [],
                'attribution': None,
                'tags': ['social', 'reddit', 'twitter']
            }
            all_items.append(unified_item)
        
        # Process Enhanced items
        for item in results.get('enhanced', []):
            if hasattr(item, 'source'):
                unified_item = {
                    'source_type': 'enhanced',
                    'source': item.source,
                    'title': item.title,
                    'description': item.description,
                    'url': item.url,
                    'timestamp': item.timestamp.isoformat() if item.timestamp else None,
                    'threat_type': item.threat_type,
                    'severity': item.severity,
                    'confidence': item.confidence,
                    'industry_sector': item.industry_sector,
                    'affected_products': item.affected_products,
                    'iocs': item.iocs,
                    'attribution': item.attribution,
                    'tags': item.tags + ['enhanced'] if item.tags else ['enhanced']
                }
                all_items.append(unified_item)
        
        # Sort by timestamp (most recent first)
        all_items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return all_items
    
    def save_integrated_results(self, output_file: str):
        """Save integrated collection results"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.collection_results, f, indent=2)
        
        logger.info(f"💾 Integrated intelligence saved to {output_file}")
    
    def get_collection_summary(self) -> Dict[str, Any]:
        """Get comprehensive collection summary"""
        if not self.collection_results:
            return {'status': 'No collection performed yet'}
        
        return {
            'status': 'Collection completed successfully',
            'total_sources': self.collection_results['collection_metadata']['total_sources'],
            'total_items': self.collection_results['collection_metadata']['total_items_collected'],
            'collection_rate': self.collection_results['performance_metrics']['items_per_second'],
            'enhancement_coverage': self.collection_results['enhancement_metrics']['enhanced_coverage_percentage'],
            'ioc_extraction_rate': self.collection_results['enhancement_metrics']['total_iocs_extracted'],
            'attribution_success_rate': (self.collection_results['enhancement_metrics']['items_with_attribution'] / 
                                       max(1, len(self.collection_results['all_intelligence']))) * 100
        }

async def main():
    """Main function for integrated intelligence collection"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    collector = IntegratedUnifiedCollector()
    
    # Collect all intelligence
    results = await collector.collect_all_intelligence()
    
    # Get summary
    summary = collector.get_collection_summary()
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"data/raw/integrated_intelligence_{timestamp}.json"
    collector.save_integrated_results(output_file)
    
    # Print final summary
    print("\n" + "=" * 80)
    print("🎯 INTEGRATED INTELLIGENCE COLLECTION COMPLETE")
    print("=" * 80)
    print(f"📊 Total Sources: {summary['total_sources']}")
    print(f"📈 Total Items: {summary['total_items']:,}")
    print(f"⚡ Collection Rate: {summary['collection_rate']:.1f} items/second")
    print(f"🎯 Enhanced Coverage: {summary['enhancement_coverage']:.1f}%")
    print(f"🔍 IOCs Extracted: {summary['ioc_extraction_rate']}")
    print(f"🎪 Attribution Rate: {summary['attribution_success_rate']:.1f}%")
    print(f"📁 Results: {output_file}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
