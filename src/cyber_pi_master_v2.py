#!/usr/bin/env python3
"""
cyber-pi Master v2 - With Cyber Periscope Triage Integration
Complete end-to-end threat intelligence with multi-level memory and analyst triage
"""

import sys
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import json

# Add src to path
sys.path.append(str(Path(__file__).parent))

from collectors.unified_collector import UnifiedCollector
from processors.client_filter import ClientFilter
from delivery.newsletter_generator import NewsletterGenerator
from delivery.alert_system import AlertSystem
from cyber_pi_periscope_integration import CyberPiPeriscopeIntegration

logger = logging.getLogger(__name__)


class CyberPiMasterV2:
    """
    Master orchestration for cyber-pi platform with Periscope Triage
    
    Pipeline:
    1. Collect intelligence (RSS + Social)
    2. **NEW: Ingest into Periscope Triage (3-level memory)**
    3. Filter for each client industry
    4. **NEW: Track analyst triage and interactions**
    5. Send critical alerts immediately
    6. Generate and send daily newsletters
    7. **NEW: Auto-promote validated threats**
    8. Archive results
    """
    
    def __init__(self, config_path: str = None, enable_periscope: bool = True):
        """Initialize master system with Periscope"""
        logger.info("=" * 80)
        logger.info("🚀 CYBER-PI MASTER V2 - WITH PERISCOPE TRIAGE")
        logger.info("=" * 80)
        
        # Initialize components
        self.collector = UnifiedCollector()
        self.client_filter = ClientFilter()
        self.newsletter_gen = NewsletterGenerator()
        self.alert_system = AlertSystem()
        
        # Initialize Periscope Triage
        self.enable_periscope = enable_periscope
        if enable_periscope:
            self.periscope = CyberPiPeriscopeIntegration()
            logger.info("🧠 Periscope Triage enabled")
        else:
            self.periscope = None
            logger.info("⚠️  Periscope Triage disabled")
        
        # Load client configuration
        if config_path:
            self.client_config = self._load_config(config_path)
        else:
            self.client_config = self._get_default_config()
        
        logger.info(f"✅ Configured for {len(self.client_config)} industries")
        logger.info("=" * 80)
    
    async def run_full_cycle_async(self, mode: str = 'all'):
        """
        Run complete intelligence cycle with Periscope integration
        
        Args:
            mode: 'all', 'collect', 'alert', 'newsletter', 'triage'
        """
        logger.info(f"\n🔄 Running cycle: {mode}")
        logger.info(f"⏰ Time: {datetime.utcnow().isoformat()}")
        
        # Step 1: Collect intelligence
        if mode in ['all', 'collect', 'alert', 'triage']:
            logger.info("\n📡 Step 1: Collecting intelligence...")
            results = self.collector.collect_all()
            items = results['total']
            logger.info(f"✅ Collected {len(items)} intelligence items")
        else:
            # Load from cache for newsletter-only mode
            items = self._load_latest_collection()
        
        # Step 2: Ingest into Periscope Triage
        if self.enable_periscope and mode in ['all', 'collect', 'triage']:
            logger.info("\n🧠 Step 2: Ingesting into Periscope Triage...")
            stats = await self.periscope.ingest_cyber_pi_threats(items)
            logger.info(f"✅ Periscope: {stats['added']} threats added to memory")
        
        # Step 3: Check for critical threats and send alerts
        if mode in ['all', 'alert']:
            logger.info("\n🚨 Step 3: Checking for critical threats...")
            alert_count = 0
            
            for industry, config in self.client_config.items():
                emails = config.get('alert_emails', [])
                count = self.alert_system.check_and_alert(items, industry, emails)
                alert_count += count
            
            logger.info(f"✅ Sent {alert_count} critical alerts")
        
        # Step 4: Auto-promote validated threats in Periscope
        if self.enable_periscope and mode in ['all', 'triage']:
            logger.info("\n⬆️  Step 4: Auto-promoting validated threats...")
            promo_stats = await self.periscope.auto_promote_validated()
            logger.info(f"✅ Promoted {promo_stats['promoted']} threats to Level 2")
        
        # Step 5: Generate and send newsletters
        if mode in ['all', 'newsletter']:
            logger.info("\n📧 Step 5: Generating newsletters...")
            newsletter_count = 0
            
            for industry, config in self.client_config.items():
                emails = config.get('newsletter_emails', [])
                if emails:
                    success = self.newsletter_gen.send_newsletter(items, industry, emails)
                    if success:
                        newsletter_count += 1
            
            logger.info(f"✅ Sent {newsletter_count} newsletters")
        
        # Step 6: Archive results
        if mode in ['all', 'collect']:
            self._archive_results(items)
        
        # Step 7: Show Periscope dashboard
        if self.enable_periscope and mode in ['all', 'triage']:
            logger.info("\n📊 Periscope Triage Dashboard:")
            dashboard = await self.periscope.get_triage_dashboard()
            self._print_dashboard(dashboard)
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ CYCLE COMPLETE")
        logger.info("=" * 80)
    
    def run_full_cycle(self, mode: str = 'all'):
        """Sync wrapper for async cycle"""
        asyncio.run(self.run_full_cycle_async(mode))
    
    async def get_priority_threats_async(self, min_score: float = 0.7):
        """Get priority threats from Periscope"""
        if not self.enable_periscope:
            logger.warning("Periscope not enabled")
            return []
        
        threats = await self.periscope.get_priority_threats(min_score=min_score)
        
        logger.info(f"\n🎯 Priority Threats (score >= {min_score}):")
        for threat in threats:
            logger.info(f"  - {threat.threat_id}: {threat.content[:80]}...")
            logger.info(f"    Severity: {threat.severity}, Score: {threat.threat_score:.2f}")
        
        return threats
    
    async def record_analyst_action_async(
        self,
        threat_id: str,
        analyst_id: str,
        action: str = "view"
    ):
        """Record analyst interaction with threat"""
        if not self.enable_periscope:
            logger.warning("Periscope not enabled")
            return None
        
        threat = await self.periscope.record_analyst_triage(threat_id, analyst_id, action)
        
        if threat:
            logger.info(f"✅ Recorded {action} by {analyst_id} on {threat_id}")
            logger.info(f"   New score: {threat.threat_score:.2f}, Interactions: {threat.interaction_count}")
        
        return threat
    
    def generate_reports(self, items: List[Dict] = None):
        """Generate reports without sending"""
        if items is None:
            items = self._load_latest_collection()
        
        logger.info("📊 Generating reports for all industries...")
        
        for industry in self.client_config.keys():
            report = self.client_filter.generate_client_report(items, industry)
            
            # Save report
            self._save_report(industry, report)
            
            logger.info(f"✅ {industry}: {report['summary']['total_threats']} threats")
    
    def _print_dashboard(self, dashboard: Dict):
        """Print Periscope dashboard"""
        stats = dashboard['system_stats']
        
        logger.info(f"  Total Active (L1): {stats['total_active']}")
        logger.info(f"  Total Short-Term (L2): {stats['total_short_term']}")
        logger.info(f"  Total Long-Term (L3): {stats['total_long_term']}")
        
        logger.info(f"\n  Priority Threats: {len(dashboard['priority_threats'])}")
        for threat in dashboard['priority_threats'][:3]:
            logger.info(f"    - {threat['id']}: {threat['severity']} (score: {threat['score']:.2f})")
        
        logger.info(f"\n  Hot Threats: {len(dashboard['hot_threats'])}")
        for threat in dashboard['hot_threats'][:3]:
            logger.info(f"    - {threat['id']}: {threat['interactions']} interactions")
        
        logger.info(f"\n  Severity Breakdown:")
        logger.info(f"    Critical: {dashboard['severity_breakdown']['critical']}")
        logger.info(f"    High: {dashboard['severity_breakdown']['high']}")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load client configuration from file"""
        import yaml
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _get_default_config(self) -> Dict:
        """Get default client configuration"""
        return {
            'aviation': {
                'newsletter_emails': [],
                'alert_emails': [],
                'slack_channel': '#aviation-security'
            },
            'healthcare': {
                'newsletter_emails': [],
                'alert_emails': [],
                'slack_channel': '#healthcare-security'
            },
            'energy': {
                'newsletter_emails': [],
                'alert_emails': [],
                'slack_channel': '#energy-security'
            }
        }
    
    def _load_latest_collection(self) -> List[Dict]:
        """Load most recent collection from disk"""
        data_dir = Path('data/raw')
        
        files = sorted(data_dir.glob('unified_collection_*.json'), reverse=True)
        
        if not files:
            logger.warning("No previous collections found")
            return []
        
        with open(files[0], 'r') as f:
            data = json.load(f)
            return data.get('items', [])
    
    def _archive_results(self, items: List[Dict]):
        """Archive collection results"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_dir = Path('data/archive')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f'collection_{timestamp}.json'
        
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'item_count': len(items),
                'items': items
            }, f, indent=2)
        
        logger.info(f"💾 Archived to: {output_file}")
    
    def _save_report(self, industry: str, report: Dict):
        """Save industry report"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_dir = Path('data/reports/industry')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f'{industry}_{timestamp}.json'
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
    
    async def cleanup_async(self):
        """Cleanup resources"""
        if self.periscope:
            await self.periscope.cleanup()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='cyber-pi Master V2 with Periscope Triage')
    parser.add_argument('--mode', default='all', 
                       choices=['all', 'collect', 'alert', 'newsletter', 'report', 'triage'],
                       help='Execution mode')
    parser.add_argument('--config', help='Client configuration file')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('--no-periscope', action='store_true', help='Disable Periscope Triage')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run system
    try:
        master = CyberPiMasterV2(
            config_path=args.config,
            enable_periscope=not args.no_periscope
        )
        
        if args.mode == 'report':
            master.generate_reports()
        else:
            master.run_full_cycle(mode=args.mode)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopped by user")
        return 1
    except Exception as e:
        logger.error(f"\n❌ Error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
