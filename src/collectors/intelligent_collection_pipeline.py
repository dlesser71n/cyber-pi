#!/usr/bin/env python3
"""
Intelligent Collection Pipeline
Implements "Collect All, Filter Smart" pattern following industry best practices
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.collectors.rss_collector import RSSCollector
from src.intelligence.threat_scoring_engine import (
    ThreatScoringEngine,
    filter_threats_by_priority,
    ThreatSeverity
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntelligentCollectionPipeline:
    """
    Industry-standard threat intelligence collection pipeline
    
    Philosophy: "Collect Everything, Filter Intelligently"
    - No arbitrary limits on collection
    - Multi-factor threat scoring
    - Intelligent prioritization
    - Actionable intelligence focus
    """
    
    def __init__(self, output_dir: str = "data/processed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.scoring_engine = ThreatScoringEngine()
        
        self.stats = {
            'total_collected': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0,
            'actionable': 0,
            'sources_processed': 0,
            'collection_time': None,
            'processing_time': None
        }
    
    async def collect_and_prioritize(
        self,
        min_score: float = 60.0,
        save_all: bool = True
    ) -> Dict[str, Any]:
        """
        Collect all threat intelligence and intelligently filter
        
        Args:
            min_score: Minimum score for actionable threats (60 = HIGH/CRITICAL)
            save_all: Save all collected data (not just actionable)
            
        Returns:
            Dictionary with collection results and statistics
        """
        logger.info("=" * 80)
        logger.info("🚀 INTELLIGENT COLLECTION PIPELINE STARTED")
        logger.info("=" * 80)
        logger.info(f"Strategy: Collect ALL items, filter by intelligence (min score: {min_score})")
        logger.info("")
        
        collection_start = datetime.now(timezone.utc)
        
        # Step 1: Collect ALL threat intelligence (no limits)
        logger.info("📡 Step 1: Collecting from all sources (NO LIMITS)...")
        all_threats = await self._collect_all_sources()
        
        collection_end = datetime.now(timezone.utc)
        self.stats['collection_time'] = (collection_end - collection_start).total_seconds()
        self.stats['total_collected'] = len(all_threats)
        
        logger.info(f"✅ Collected {len(all_threats):,} total items in {self.stats['collection_time']:.2f}s")
        logger.info("")
        
        # Step 2: Score and prioritize
        logger.info("🎯 Step 2: Scoring threats with multi-factor analysis...")
        processing_start = datetime.now(timezone.utc)
        
        scored_threats = self._score_all_threats(all_threats)
        
        processing_end = datetime.now(timezone.utc)
        self.stats['processing_time'] = (processing_end - processing_start).total_seconds()
        
        logger.info(f"✅ Scored {len(scored_threats):,} threats in {self.stats['processing_time']:.2f}s")
        logger.info("")
        
        # Step 3: Filter by priority
        logger.info(f"🔍 Step 3: Filtering for actionable intelligence (score >= {min_score})...")
        actionable_threats = [t for t in scored_threats if t['_scoring']['score'] >= min_score]
        self.stats['actionable'] = len(actionable_threats)
        
        # Count by severity
        for threat in scored_threats:
            severity = threat['_scoring']['severity']
            if severity == ThreatSeverity.CRITICAL.value:
                self.stats['critical'] += 1
            elif severity == ThreatSeverity.HIGH.value:
                self.stats['high'] += 1
            elif severity == ThreatSeverity.MEDIUM.value:
                self.stats['medium'] += 1
            elif severity == ThreatSeverity.LOW.value:
                self.stats['low'] += 1
            else:
                self.stats['info'] += 1
        
        logger.info(f"✅ Found {len(actionable_threats):,} actionable threats")
        logger.info("")
        
        # Step 4: Save results
        logger.info("💾 Step 4: Saving intelligence reports...")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        # Save actionable threats (HIGH/CRITICAL)
        actionable_file = self.output_dir / f"actionable_threats_{timestamp}.json"
        self._save_threats(actionable_threats, actionable_file, "Actionable Intelligence")
        
        # Save all threats if requested
        if save_all:
            all_file = self.output_dir / f"all_threats_{timestamp}.json"
            self._save_threats(scored_threats, all_file, "Complete Collection")
        
        # Save statistics
        stats_file = self.output_dir / f"collection_stats_{timestamp}.json"
        self._save_stats(stats_file)
        
        logger.info("")
        self._print_summary()
        
        return {
            'actionable_threats': actionable_threats,
            'all_threats': scored_threats if save_all else None,
            'stats': self.stats,
            'files': {
                'actionable': str(actionable_file),
                'all': str(all_file) if save_all else None,
                'stats': str(stats_file)
            }
        }
    
    async def _collect_all_sources(self) -> List[Dict[str, Any]]:
        """Collect from all sources with NO LIMITS"""
        # Use RSS collector (already has limits removed)
        async with RSSCollector(max_workers=32) as collector:
            collector.load_sources()
            self.stats['sources_processed'] = len(collector.sources)
            
            # Collect from all sources in parallel
            # collect_parallel() returns list of items directly
            all_items = await collector.collect_parallel()
        
        return all_items
    
    def _score_all_threats(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score all threats using multi-factor analysis"""
        scored = []
        
        for threat in threats:
            try:
                score = self.scoring_engine.score_threat(threat)
                
                # Add scoring metadata
                threat['_scoring'] = {
                    'score': score.total_score,
                    'severity': score.severity.value,
                    'category': score.category.value,
                    'factors': score.factors,
                    'confidence': score.confidence,
                    'reasoning': score.reasoning,
                    'actionable': score.actionable,
                    'priority_rank': score.priority_rank
                }
                
                scored.append(threat)
                
            except Exception as e:
                logger.warning(f"Error scoring threat: {e}")
                continue
        
        # Sort by priority rank (lower = higher priority)
        scored.sort(key=lambda x: x['_scoring']['priority_rank'])
        
        return scored
    
    def _save_threats(self, threats: List[Dict[str, Any]], filepath: Path, description: str):
        """Save threats to JSON file"""
        data = {
            'metadata': {
                'description': description,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total_items': len(threats),
                'scoring_method': 'multi-factor',
                'version': '1.0'
            },
            'threats': threats
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"  ✅ Saved {len(threats):,} items to {filepath.name}")
    
    def _save_stats(self, filepath: Path):
        """Save collection statistics"""
        with open(filepath, 'w') as f:
            json.dump(self.stats, f, indent=2)
        
        logger.info(f"  ✅ Saved statistics to {filepath.name}")
    
    def _print_summary(self):
        """Print collection summary"""
        logger.info("=" * 80)
        logger.info("📊 COLLECTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Sources Processed:     {self.stats['sources_processed']}")
        logger.info(f"Total Items Collected: {self.stats['total_collected']:,}")
        logger.info(f"Collection Time:       {self.stats['collection_time']:.2f}s")
        logger.info(f"Processing Time:       {self.stats['processing_time']:.2f}s")
        logger.info("")
        logger.info("Severity Breakdown:")
        logger.info(f"  🔴 CRITICAL:  {self.stats['critical']:,} items")
        logger.info(f"  🟠 HIGH:      {self.stats['high']:,} items")
        logger.info(f"  🟡 MEDIUM:    {self.stats['medium']:,} items")
        logger.info(f"  🟢 LOW:       {self.stats['low']:,} items")
        logger.info(f"  ⚪ INFO:      {self.stats['info']:,} items")
        logger.info("")
        logger.info(f"✅ Actionable Intelligence: {self.stats['actionable']:,} items ({self.stats['actionable']/self.stats['total_collected']*100:.1f}%)")
        logger.info("")
        
        # Calculate efficiency
        if self.stats['total_collected'] > 0:
            signal_to_noise = self.stats['actionable'] / self.stats['total_collected'] * 100
            logger.info(f"📈 Signal-to-Noise Ratio: {signal_to_noise:.1f}%")
            logger.info(f"   (Industry standard: 1-5%, Cyber-PI: {signal_to_noise:.1f}%)")
        
        logger.info("=" * 80)
        logger.info("✅ COLLECTION COMPLETE")
        logger.info("=" * 80)


async def main():
    """Main execution"""
    pipeline = IntelligentCollectionPipeline()
    
    # Collect and prioritize
    results = await pipeline.collect_and_prioritize(
        min_score=60.0,  # HIGH and CRITICAL only
        save_all=True    # Save all data for analysis
    )
    
    # Print top 10 critical threats
    actionable = results['actionable_threats']
    if actionable:
        print("\n" + "=" * 80)
        print("🔥 TOP 10 CRITICAL THREATS")
        print("=" * 80)
        
        for i, threat in enumerate(actionable[:10], 1):
            scoring = threat['_scoring']
            print(f"\n{i}. [{scoring['severity']}] Score: {scoring['score']:.1f}/100")
            print(f"   {threat['title']}")
            print(f"   Category: {scoring['category']}")
            print(f"   Source: {threat['source']['name']}")
            print(f"   Reasoning: {scoring['reasoning'][0] if scoring['reasoning'] else 'N/A'}")


if __name__ == "__main__":
    asyncio.run(main())
