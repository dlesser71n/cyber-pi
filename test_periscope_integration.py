#!/usr/bin/env python3
"""
Test Periscope Integration
See threats before they surface.

Comprehensive test of end-to-end threat intelligence pipeline.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Configure DEBUG logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.periscope_intelligence_integration import PeriscopeIntelligenceIntegration


async def test_integration():
    """Test end-to-end integration."""
    
    logger.info("=" * 80)
    logger.info("🔭 PERISCOPE INTEGRATION TEST")
    logger.info("=" * 80)
    logger.info("See threats before they surface.")
    logger.info("")
    
    try:
        # Initialize integration
        logger.info("📋 Step 1: Initializing integration...")
        integration = PeriscopeIntelligenceIntegration(
            min_score=60.0,
            critical_threshold=80.0,
            auto_escalate=True
        )
        logger.info("✅ Integration initialized")
        logger.info("")
        
        # Run collection cycle
        logger.info("🚀 Step 2: Running collection cycle...")
        results = await integration.run_collection_cycle(save_reports=True)
        logger.info("")
        
        if not results['success']:
            logger.error(f"❌ Collection cycle failed: {results.get('error', 'Unknown')}")
            return False
        
        # Display results
        logger.info("=" * 80)
        logger.info("📊 TEST RESULTS")
        logger.info("=" * 80)
        
        stats = results['stats']
        logger.info(f"✅ Collection successful")
        logger.info(f"   Collected: {stats['collected']:,} threats")
        logger.info(f"   Scored: {stats['scored']:,} threats")
        logger.info(f"   Ingested: {stats['ingested']:,} threats")
        logger.info(f"   Critical: {stats['critical']} threats")
        logger.info(f"   High: {stats['high']} threats")
        logger.info(f"   Auto-escalated: {stats['escalated']} threats")
        logger.info("")
        
        # Check Periscope status
        logger.info("🔭 Step 3: Checking Periscope status...")
        status = await integration.get_periscope_status()
        logger.info(f"   L1 Memory: {status['l1_threats']} threats")
        logger.info(f"   L2 Memory: {status['l2_threats']} threats")
        logger.info(f"   L3 Memory: {status['l3_threats']} threats")
        logger.info("")
        
        # Show top critical threats
        logger.info("🔥 Step 4: Top 5 Critical Threats:")
        actionable = results['actionable_threats']
        critical = [t for t in actionable if t['_scoring']['severity'] == 'CRITICAL'][:5]
        
        for i, threat in enumerate(critical, 1):
            scoring = threat['_scoring']
            logger.info(f"\n{i}. [{scoring['severity']}] Score: {scoring['score']:.1f}/100")
            logger.info(f"   {threat['title'][:70]}")
            logger.info(f"   Source: {threat['source']['name']}")
            logger.info(f"   Category: {scoring['category']}")
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ INTEGRATION TEST PASSED")
        logger.info("=" * 80)
        logger.info("🔭 See threats before they surface.")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}", exc_info=True)
        return False


async def main():
    """Main entry point."""
    
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    
    # Run test
    success = await test_integration()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
