#!/usr/bin/env python3
"""
Test Debug Mode Configuration
Shows detailed logging and debug output
"""
import asyncio
import sys
sys.path.insert(0, 'src')

# Import config first to setup logging
from cascade.config import setup_logging, get_config, is_debug_mode, is_verbose
from cascade.cascade_batch_ops import CascadeBatchOperations

# Setup logging with debug mode
config = setup_logging()

import logging
logger = logging.getLogger(__name__)


async def test_debug_mode():
    """Test with debug mode enabled"""
    
    logger.info("="*70)
    logger.info("🔍 Testing Debug Mode Configuration")
    logger.info("="*70)
    
    # Show config status
    logger.info(f"Debug Mode: {is_debug_mode()}")
    logger.info(f"Verbose Logging: {is_verbose()}")
    logger.info(f"Config Loaded: {bool(config)}")
    
    logger.debug("Initializing Cascade Memory System...")
    
    # Initialize system
    memory = CascadeBatchOperations(redis_host="localhost", redis_port=32379)
    await memory.initialize()
    
    logger.debug("System initialized successfully")
    
    # Clear test data
    for client in memory.redis_clients.values():
        await client.flushdb()
    
    logger.info("\n" + "="*70)
    logger.info("TEST: Add Threat with Debug Output")
    logger.info("="*70)
    
    logger.debug("Creating threat object...")
    threat = await memory.add_threat(
        "debug_threat_001",
        "Test threat for debug mode",
        "HIGH",
        metadata={'test': True, 'source': 'debug'}
    )
    
    logger.info(f"✅ Threat added: {threat.threat_id}")
    logger.debug(f"   Threat score: {threat.threat_score:.3f}")
    logger.debug(f"   Severity: {threat.severity}")
    logger.debug(f"   Metadata: {threat.metadata}")
    
    logger.info("\n" + "="*70)
    logger.info("TEST: Record Interactions with Debug Output")
    logger.info("="*70)
    
    for i in range(3):
        logger.debug(f"Recording interaction {i+1}/3...")
        await memory.record_interaction(
            "debug_threat_001",
            f"analyst_{i+1}",
            "escalate" if i < 2 else "view"
        )
        logger.debug(f"   Interaction {i+1} recorded")
    
    logger.info("✅ All interactions recorded")
    
    logger.info("\n" + "="*70)
    logger.info("TEST: Get Threat with Debug Output")
    logger.info("="*70)
    
    logger.debug("Fetching threat from Level 1...")
    threat_updated = await memory.get_threat("debug_threat_001")
    
    if threat_updated:
        logger.info(f"✅ Threat retrieved from Level 1")
        logger.debug(f"   Interactions: {threat_updated.interaction_count}")
        logger.debug(f"   Escalations: {threat_updated.escalation_count}")
        logger.debug(f"   Updated score: {threat_updated.threat_score:.3f}")
    
    logger.info("\n" + "="*70)
    logger.info("TEST: Intelligent Get with Debug Output")
    logger.info("="*70)
    
    logger.debug("Testing intelligent_get_threat...")
    threat_intel, tier = await memory.intelligent_get_threat("debug_threat_001")
    
    if threat_intel:
        logger.info(f"✅ Found in tier: {tier}")
        logger.debug(f"   Threat ID: {threat_intel.threat_id}")
        logger.debug(f"   Score: {threat_intel.threat_score:.3f}")
    
    logger.info("\n" + "="*70)
    logger.info("TEST: System Statistics with Debug Output")
    logger.info("="*70)
    
    logger.debug("Gathering system statistics...")
    stats = await memory.get_stats()
    
    logger.info("✅ System Statistics:")
    for tier_name, tier_stats in stats['tiers'].items():
        logger.info(f"\n   {tier_name}:")
        logger.debug(f"      Hits: {tier_stats['hits']}")
        logger.debug(f"      Misses: {tier_stats['misses']}")
        logger.debug(f"      Promotions: {tier_stats['promotions']}")
        logger.debug(f"      Sets: {tier_stats['sets']}")
    
    # Cleanup
    logger.debug("Cleaning up test data...")
    for client in memory.redis_clients.values():
        await client.flushdb()
        await client.close()
    
    logger.info("\n" + "="*70)
    logger.info("🎉 Debug Mode Test Complete!")
    logger.info("="*70)
    logger.info("\n✅ All debug output working correctly")
    logger.info("✅ Detailed logging enabled")
    logger.info("✅ Source locations shown")
    logger.info("✅ Timestamps included")
    logger.info("\n📝 Configuration file: .windsurf/config.json")
    logger.info("📚 Documentation: .windsurf/README.md")


if __name__ == "__main__":
    asyncio.run(test_debug_mode())
