#!/usr/bin/env python3
"""
cyber-pi Master Automation Script
Complete end-to-end threat intelligence collection, filtering, and delivery
"""

import sys
import logging
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

logger = logging.getLogger(__name__)


class CyberPiMaster:
    """
    Master orchestration for cyber-pi platform
    
    Pipeline:
    1. Collect intelligence (RSS + Social)
    2. Filter for each client industry
    3. Send critical alerts immediately
    4. Generate and send daily newsletters
    5. Archive results
    """
    
    def __init__(self, config_path: str = None):
        """Initialize master system"""
        logger.info("=" * 80)
        logger.info("🚀 CYBER-PI MASTER SYSTEM INITIALIZING")
        logger.info("=" * 80)
        
        # Initialize components
        self.collector = UnifiedCollector()
        self.client_filter = ClientFilter()
        self.newsletter_gen = NewsletterGenerator()
        self.alert_system = AlertSystem()
        
        # Load client configuration
        if config_path:
            self.client_config = self._load_config(config_path)
        else:
            self.client_config = self._get_default_config()
        
        logger.info(f"✅ Configured for {len(self.client_config)} industries")
        logger.info("=" * 80)
    
    def run_full_cycle(self, mode: str = 'all'):
        """
        Run complete intelligence cycle
        
        Args:
            mode: 'all', 'collect', 'alert', 'newsletter'
        """
        logger.info(f"\n🔄 Running cycle: {mode}")
        logger.info(f"⏰ Time: {datetime.utcnow().isoformat()}")
        
        # Step 1: Collect intelligence
        if mode in ['all', 'collect', 'alert']:
            logger.info("\n📡 Step 1: Collecting intelligence...")
            results = self.collector.collect_all()
            items = results['total']
            logger.info(f"✅ Collected {len(items)} intelligence items")
        else:
            # Load from cache for newsletter-only mode
            items = self._load_latest_collection()
        
        # Step 2: Check for critical threats and send alerts
        if mode in ['all', 'alert']:
            logger.info("\n🚨 Step 2: Checking for critical threats...")
            alert_count = 0
            
            for industry, config in self.client_config.items():
                emails = config.get('alert_emails', [])
                count = self.alert_system.check_and_alert(items, industry, emails)
                alert_count += count
            
            logger.info(f"✅ Sent {alert_count} critical alerts")
        
        # Step 3: Generate and send newsletters
        if mode in ['all', 'newsletter']:
            logger.info("\n📧 Step 3: Generating newsletters...")
            newsletter_count = 0
            
            for industry, config in self.client_config.items():
                emails = config.get('newsletter_emails', [])
                if emails:
                    success = self.newsletter_gen.send_newsletter(items, industry, emails)
                    if success:
                        newsletter_count += 1
            
            logger.info(f"✅ Sent {newsletter_count} newsletters")
        
        # Step 4: Archive results
        if mode in ['all', 'collect']:
            self._archive_results(items)
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ CYCLE COMPLETE")
        logger.info("=" * 80)
    
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
    
    def _load_config(self, config_path: str) -> Dict:
        """Load client configuration from file"""
        import yaml
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _get_default_config(self) -> Dict:
        """Get default client configuration"""
        return {
            'aviation': {
                'newsletter_emails': [],  # Add client emails
                'alert_emails': [],       # Add critical alert emails
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
        
        # Find most recent file
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


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='cyber-pi Master System')
    parser.add_argument('--mode', default='all', 
                       choices=['all', 'collect', 'alert', 'newsletter', 'report'],
                       help='Execution mode')
    parser.add_argument('--config', help='Client configuration file')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run system
    try:
        master = CyberPiMaster(config_path=args.config)
        
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
