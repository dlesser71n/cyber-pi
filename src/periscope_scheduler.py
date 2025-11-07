#!/usr/bin/env python3
"""
Periscope Automated Scheduler
See threats before they surface.

Continuously collects and ingests threat intelligence into Periscope.
Runs on configurable schedule with health monitoring and auto-recovery.

Built on Rickover's nuclear submarine principles:
- Continuous operation (24/7)
- Auto-recovery from failures
- Health monitoring and alerting
- Audit logging
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
import json
import signal
import sys

from src.periscope_intelligence_integration import PeriscopeIntelligenceIntegration

# Configure logging
Path('logs').mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/periscope_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PeriscopeScheduler:
    """
    Automated threat intelligence collection scheduler.
    
    Features:
    - Configurable collection intervals
    - Health monitoring
    - Auto-recovery from failures
    - Graceful shutdown
    - Statistics tracking
    - Alert generation
    """
    
    def __init__(
        self,
        interval_minutes: int = 60,
        min_score: float = 60.0,
        critical_threshold: float = 80.0,
        max_failures: int = 3,
        alert_on_critical: bool = True
    ):
        """
        Initialize scheduler.
        
        Args:
            interval_minutes: Collection interval in minutes (default: 60)
            min_score: Minimum threat score for ingestion (default: 60.0)
            critical_threshold: Score for auto-escalation (default: 80.0)
            max_failures: Max consecutive failures before alert (default: 3)
            alert_on_critical: Alert on critical threats (default: True)
        """
        self.interval_minutes = interval_minutes
        self.min_score = min_score
        self.critical_threshold = critical_threshold
        self.max_failures = max_failures
        self.alert_on_critical = alert_on_critical
        
        self.integration = PeriscopeIntelligenceIntegration(
            min_score=min_score,
            critical_threshold=critical_threshold,
            auto_escalate=True
        )
        
        self.running = False
        self.consecutive_failures = 0
        self.total_cycles = 0
        self.successful_cycles = 0
        self.failed_cycles = 0
        
        self.stats = {
            'start_time': None,
            'last_collection': None,
            'next_collection': None,
            'total_threats_collected': 0,
            'total_threats_ingested': 0,
            'total_critical_threats': 0,
            'uptime_seconds': 0
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Periscope Scheduler initialized")
        logger.info(f"  Collection interval: {interval_minutes} minutes")
        logger.info(f"  Min score: {min_score}")
        logger.info(f"  Critical threshold: {critical_threshold}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    async def start(self):
        """Start the scheduler."""
        self.running = True
        self.stats['start_time'] = datetime.now(timezone.utc)
        
        logger.info("=" * 80)
        logger.info("🔭 PERISCOPE SCHEDULER STARTED")
        logger.info("=" * 80)
        logger.info("See threats before they surface.")
        logger.info(f"Collection interval: Every {self.interval_minutes} minutes")
        logger.info("")
        
        try:
            while self.running:
                cycle_start = datetime.now(timezone.utc)
                self.total_cycles += 1
                
                logger.info(f"🔄 Starting collection cycle #{self.total_cycles}")
                logger.info(f"Time: {cycle_start.isoformat()}")
                
                try:
                    # Run collection cycle
                    results = await self.integration.run_collection_cycle(save_reports=True)
                    
                    if results['success']:
                        self.successful_cycles += 1
                        self.consecutive_failures = 0
                        
                        # Update stats
                        stats = results['stats']
                        self.stats['last_collection'] = cycle_start.isoformat()
                        self.stats['total_threats_collected'] += stats['collected']
                        self.stats['total_threats_ingested'] += stats['ingested']
                        self.stats['total_critical_threats'] += stats['critical']
                        
                        # Check for critical threats
                        if self.alert_on_critical and stats['critical'] > 0:
                            await self._alert_critical_threats(results)
                        
                        logger.info(f"✅ Cycle #{self.total_cycles} completed successfully")
                        
                    else:
                        self.failed_cycles += 1
                        self.consecutive_failures += 1
                        logger.error(f"❌ Cycle #{self.total_cycles} failed: {results.get('error', 'Unknown')}")
                        
                        # Check failure threshold
                        if self.consecutive_failures >= self.max_failures:
                            await self._alert_system_failure()
                
                except Exception as e:
                    self.failed_cycles += 1
                    self.consecutive_failures += 1
                    logger.error(f"❌ Cycle #{self.total_cycles} exception: {e}", exc_info=True)
                    
                    if self.consecutive_failures >= self.max_failures:
                        await self._alert_system_failure()
                
                # Calculate next collection time
                cycle_duration = (datetime.now(timezone.utc) - cycle_start).total_seconds()
                sleep_seconds = max(0, (self.interval_minutes * 60) - cycle_duration)
                
                next_collection = datetime.now(timezone.utc) + timedelta(seconds=sleep_seconds)
                self.stats['next_collection'] = next_collection.isoformat()
                
                logger.info(f"⏰ Next collection: {next_collection.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                logger.info(f"💤 Sleeping for {sleep_seconds/60:.1f} minutes...")
                logger.info("")
                
                # Sleep until next cycle (with periodic checks for shutdown)
                sleep_interval = 10  # Check every 10 seconds
                slept = 0
                while slept < sleep_seconds and self.running:
                    await asyncio.sleep(min(sleep_interval, sleep_seconds - slept))
                    slept += sleep_interval
        
        finally:
            await self._shutdown()
    
    async def _alert_critical_threats(self, results: Dict[str, Any]):
        """Alert on critical threats detected."""
        stats = results['stats']
        critical_count = stats['critical']
        
        logger.warning("=" * 80)
        logger.warning(f"🚨 CRITICAL THREAT ALERT")
        logger.warning("=" * 80)
        logger.warning(f"Detected {critical_count} CRITICAL threats")
        logger.warning(f"Auto-escalated: {stats['escalated']} threats")
        logger.warning("")
        
        # Show top 3 critical threats
        actionable = results.get('actionable_threats', [])
        critical = [t for t in actionable if t['_scoring']['severity'] == 'CRITICAL'][:3]
        
        for i, threat in enumerate(critical, 1):
            scoring = threat['_scoring']
            logger.warning(f"{i}. [{scoring['severity']}] Score: {scoring['score']:.1f}/100")
            logger.warning(f"   {threat['title'][:70]}")
            logger.warning(f"   Source: {threat['source']['name']}")
        
        logger.warning("=" * 80)
        
        # TODO: Send email/Slack/PagerDuty alert
    
    async def _alert_system_failure(self):
        """Alert on system failure."""
        logger.critical("=" * 80)
        logger.critical(f"🚨 SYSTEM FAILURE ALERT")
        logger.critical("=" * 80)
        logger.critical(f"Consecutive failures: {self.consecutive_failures}/{self.max_failures}")
        logger.critical(f"Total cycles: {self.total_cycles}")
        logger.critical(f"Success rate: {self.successful_cycles/self.total_cycles*100:.1f}%")
        logger.critical("System requires attention!")
        logger.critical("=" * 80)
        
        # TODO: Send critical alert to ops team
    
    async def _shutdown(self):
        """Graceful shutdown."""
        logger.info("")
        logger.info("=" * 80)
        logger.info("🛑 PERISCOPE SCHEDULER SHUTDOWN")
        logger.info("=" * 80)
        
        # Calculate uptime
        if self.stats['start_time']:
            uptime = (datetime.now(timezone.utc) - self.stats['start_time']).total_seconds()
            self.stats['uptime_seconds'] = uptime
            
            logger.info(f"Uptime: {uptime/3600:.2f} hours")
        
        logger.info(f"Total cycles: {self.total_cycles}")
        logger.info(f"Successful: {self.successful_cycles}")
        logger.info(f"Failed: {self.failed_cycles}")
        logger.info(f"Success rate: {self.successful_cycles/self.total_cycles*100:.1f}%")
        logger.info("")
        logger.info(f"Total threats collected: {self.stats['total_threats_collected']:,}")
        logger.info(f"Total threats ingested: {self.stats['total_threats_ingested']:,}")
        logger.info(f"Total critical threats: {self.stats['total_critical_threats']:,}")
        logger.info("")
        
        # Save final stats
        stats_file = Path('logs/scheduler_stats.json')
        stats_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2, default=str)
        
        logger.info(f"Stats saved to {stats_file}")
        logger.info("=" * 80)
        logger.info("🔭 See threats before they surface.")
        logger.info("=" * 80)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        return {
            'running': self.running,
            'total_cycles': self.total_cycles,
            'successful_cycles': self.successful_cycles,
            'failed_cycles': self.failed_cycles,
            'consecutive_failures': self.consecutive_failures,
            'success_rate': self.successful_cycles / self.total_cycles if self.total_cycles > 0 else 0,
            'stats': self.stats
        }


async def main():
    """Main entry point."""
    
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    # Initialize scheduler
    scheduler = PeriscopeScheduler(
        interval_minutes=60,  # Collect every hour
        min_score=60.0,
        critical_threshold=80.0,
        max_failures=3,
        alert_on_critical=True
    )
    
    # Start scheduler
    await scheduler.start()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
