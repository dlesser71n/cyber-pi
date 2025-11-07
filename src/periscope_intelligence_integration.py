#!/usr/bin/env python3
"""
Periscope Intelligence Integration
See threats before they surface.

Integrates intelligent collection pipeline with Periscope triage system.
Creates end-to-end threat intelligence flow:
  Collection → Scoring → Periscope L1 → Analyst Assistant → Action

Built on Rickover's nuclear submarine principles.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

from src.collectors.intelligent_collection_pipeline import IntelligentCollectionPipeline
from src.periscope.periscope_batch_ops import PeriscopeTriageBatch
from src.intelligence.threat_scoring_engine import ThreatScoringEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PeriscopeIntelligenceIntegration:
    """
    Integrates intelligent collection with Periscope triage.
    
    Flow:
    1. Collect threats from all sources (no limits)
    2. Score threats using multi-factor analysis
    3. Filter for actionable intelligence (score >= threshold)
    4. Ingest into Periscope L1 memory
    5. Generate analyst recommendations
    6. Track and report statistics
    """
    
    def __init__(
        self,
        min_score: float = 60.0,
        critical_threshold: float = 80.0,
        auto_escalate: bool = True
    ):
        """
        Initialize integration.
        
        Args:
            min_score: Minimum score for Periscope ingestion (default: 60.0)
            critical_threshold: Score threshold for auto-escalation (default: 80.0)
            auto_escalate: Automatically escalate critical threats (default: True)
        """
        self.min_score = min_score
        self.critical_threshold = critical_threshold
        self.auto_escalate = auto_escalate
        
        self.collection_pipeline = IntelligentCollectionPipeline()
        self.scoring_engine = ThreatScoringEngine()
        
        self.stats = {
            'collected': 0,
            'scored': 0,
            'ingested': 0,
            'critical': 0,
            'high': 0,
            'escalated': 0,
            'start_time': None,
            'end_time': None
        }
        
        logger.info("Periscope Intelligence Integration initialized")
        logger.info(f"  Min score: {min_score}")
        logger.info(f"  Critical threshold: {critical_threshold}")
        logger.info(f"  Auto-escalate: {auto_escalate}")
    
    async def run_collection_cycle(self, save_reports: bool = True) -> Dict[str, Any]:
        """
        Run complete collection and ingestion cycle.
        
        Args:
            save_reports: Save collection reports to disk (default: True)
            
        Returns:
            Statistics and results dictionary
        """
        self.stats['start_time'] = datetime.now(timezone.utc)
        
        logger.info("=" * 80)
        logger.info("🔭 PERISCOPE INTELLIGENCE INTEGRATION - COLLECTION CYCLE")
        logger.info("=" * 80)
        logger.info("See threats before they surface.")
        logger.info("")
        
        try:
            # Step 1: Collect and score threats
            logger.info("📡 Step 1: Collecting and scoring threats...")
            collection_results = await self.collection_pipeline.collect_and_prioritize(
                min_score=self.min_score,
                save_all=save_reports
            )
            
            self.stats['collected'] = collection_results['stats']['total_collected']
            self.stats['scored'] = collection_results['stats']['total_collected']
            
            actionable_threats = collection_results['actionable_threats']
            logger.info(f"✅ Found {len(actionable_threats)} actionable threats")
            
            # Step 2: Ingest into Periscope
            logger.info("")
            logger.info("🔭 Step 2: Ingesting into Periscope triage...")
            ingestion_results = await self._ingest_to_periscope(actionable_threats)
            
            self.stats['ingested'] = ingestion_results['ingested']
            self.stats['critical'] = ingestion_results['critical']
            self.stats['high'] = ingestion_results['high']
            self.stats['escalated'] = ingestion_results['escalated']
            
            # Step 3: Generate summary
            self.stats['end_time'] = datetime.now(timezone.utc)
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            
            logger.info("")
            logger.info("=" * 80)
            logger.info("📊 COLLECTION CYCLE SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Duration: {duration:.2f}s")
            logger.info(f"Collected: {self.stats['collected']:,} threats")
            logger.info(f"Actionable: {len(actionable_threats):,} threats")
            logger.info(f"Ingested to Periscope: {self.stats['ingested']:,} threats")
            logger.info("")
            logger.info("Severity Breakdown:")
            logger.info(f"  🔴 CRITICAL: {self.stats['critical']} threats")
            logger.info(f"  🟠 HIGH: {self.stats['high']} threats")
            if self.auto_escalate:
                logger.info(f"  ⚡ Auto-escalated: {self.stats['escalated']} threats")
            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ COLLECTION CYCLE COMPLETE")
            logger.info("=" * 80)
            
            return {
                'success': True,
                'stats': self.stats,
                'actionable_threats': actionable_threats,
                'ingestion_results': ingestion_results,
                'collection_results': collection_results
            }
            
        except Exception as e:
            logger.error(f"Collection cycle failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats
            }
    
    async def _ingest_to_periscope(
        self,
        threats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Ingest threats into Periscope L1 memory.
        
        Args:
            threats: List of scored threats to ingest
            
        Returns:
            Ingestion statistics
        """
        results = {
            'ingested': 0,
            'critical': 0,
            'high': 0,
            'escalated': 0,
            'errors': []
        }
        
        periscope = PeriscopeTriageBatch()
        await periscope.initialize()
        
        for threat in threats:
            try:
                # Extract threat data
                threat_id = self._generate_threat_id(threat)
                scoring = threat.get('_scoring', {})
                score = scoring.get('score', 0) / 100  # Convert to 0-1 scale
                severity = scoring.get('severity', 'MEDIUM')
                
                # Prepare threat content
                content = self._format_threat_content(threat)
                
                # Ingest to Periscope
                await periscope.add_threat(
                    threat_id=threat_id,
                    content=content,
                    severity=severity,
                    metadata={
                        'source': threat.get('source', {}).get('name', 'Unknown'),
                        'published': threat.get('published', ''),
                        'category': scoring.get('category', 'general'),
                        'confidence': scoring.get('confidence', 0),
                        'intelligence_score': score,  # Store our score in metadata
                        'url': threat.get('link', ''),
                        'collection_time': datetime.now(timezone.utc).isoformat()
                    }
                )
                
                results['ingested'] += 1
                
                # Track severity
                if severity == 'CRITICAL':
                    results['critical'] += 1
                elif severity == 'HIGH':
                    results['high'] += 1
                
                # Auto-escalate critical threats
                if self.auto_escalate and score >= (self.critical_threshold / 100):
                    await periscope.record_interaction(
                        threat_id=threat_id,
                        analyst_id="system_auto_escalate",
                        action_type="escalate"
                    )
                    results['escalated'] += 1
                    logger.info(f"⚡ Auto-escalated: {threat.get('title', 'Unknown')[:60]}")
                
            except Exception as e:
                logger.error(f"Failed to ingest threat: {e}")
                results['errors'].append({
                    'threat_id': threat.get('id', 'unknown'),
                    'error': str(e)
                })
        
        logger.info(f"✅ Ingested {results['ingested']} threats to Periscope")
        if results['errors']:
            logger.warning(f"⚠️  {len(results['errors'])} ingestion errors")
        
        return results
    
    def _generate_threat_id(self, threat: Dict[str, Any]) -> str:
        """Generate unique threat ID."""
        import hashlib
        
        # Use title + source + published as unique identifier
        unique_str = f"{threat.get('title', '')}{threat.get('source', {}).get('name', '')}{threat.get('published', '')}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]
    
    def _format_threat_content(self, threat: Dict[str, Any]) -> str:
        """Format threat content for Periscope."""
        scoring = threat.get('_scoring', {})
        
        content_parts = [
            f"Title: {threat.get('title', 'Unknown')}",
            f"Source: {threat.get('source', {}).get('name', 'Unknown')}",
            f"Score: {scoring.get('score', 0):.1f}/100",
            f"Severity: {scoring.get('severity', 'UNKNOWN')}",
            f"Category: {scoring.get('category', 'general')}",
        ]
        
        # Add summary if available
        summary = threat.get('summary', '')
        if summary:
            content_parts.append(f"\nSummary: {summary[:500]}")
        
        # Add reasoning
        reasoning = scoring.get('reasoning', [])
        if reasoning:
            content_parts.append(f"\nKey Indicators:")
            for reason in reasoning[:3]:  # Top 3 reasons
                content_parts.append(f"  • {reason}")
        
        return "\n".join(content_parts)
    
    async def get_periscope_status(self) -> Dict[str, Any]:
        """Get current Periscope triage status."""
        periscope = PeriscopeTriageBatch()
        await periscope.initialize()
        
        # Get system stats
        stats = await periscope.get_stats()
        
        return {
            'l1_threats': stats.get('Level_1_Working', {}).get('total_items', 0),
            'l2_threats': stats.get('Level_2_ShortTerm', {}).get('total_items', 0),
            'l3_threats': stats.get('Level_3_LongTerm', {}).get('total_items', 0),
            'last_update': datetime.now(timezone.utc).isoformat()
        }


async def main():
    """Main entry point for integration testing."""
    
    # Initialize integration
    integration = PeriscopeIntelligenceIntegration(
        min_score=60.0,
        critical_threshold=80.0,
        auto_escalate=True
    )
    
    # Run collection cycle
    results = await integration.run_collection_cycle(save_reports=True)
    
    if results['success']:
        # Show Periscope status
        logger.info("")
        logger.info("🔭 Periscope Status:")
        status = await integration.get_periscope_status()
        logger.info(f"  L1 Memory: {status['l1_threats']} threats")
        logger.info(f"  Critical: {status['critical_threats']}")
        logger.info(f"  High: {status['high_threats']}")
        
        # Show top 5 critical threats
        logger.info("")
        logger.info("🔥 Top 5 Critical Threats in Periscope:")
        actionable = results['actionable_threats']
        critical = [t for t in actionable if t['_scoring']['severity'] == 'CRITICAL'][:5]
        
        for i, threat in enumerate(critical, 1):
            scoring = threat['_scoring']
            logger.info(f"\n{i}. [{scoring['severity']}] Score: {scoring['score']:.1f}/100")
            logger.info(f"   {threat['title'][:70]}")
            logger.info(f"   Source: {threat['source']['name']}")
            logger.info(f"   Category: {scoring['category']}")
    else:
        logger.error(f"Collection cycle failed: {results.get('error', 'Unknown error')}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
