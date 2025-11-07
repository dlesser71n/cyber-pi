"""
Real-time Alert System for Critical Threats
Monitors intelligence feed and sends immediate alerts via Slack/Email
"""

import os
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from processors.client_filter import ClientFilter
from delivery.email_sender import EmailSender

logger = logging.getLogger(__name__)


class AlertSystem:
    """
    Real-time alerting for critical threats
    
    Features:
    - Monitors intelligence feed in real-time
    - Scores threats by relevance
    - Sends immediate alerts for critical threats
    - Multiple delivery channels (Slack, Email, SMS)
    - Deduplication to prevent alert fatigue
    """
    
    def __init__(self):
        self.client_filter = ClientFilter()
        self.email_sender = EmailSender()
        
        # Slack configuration
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL', '')
        self.slack_enabled = bool(self.slack_webhook)
        
        # Alert thresholds
        self.critical_threshold = 30  # Relevance score for critical alerts
        self.high_threshold = 20      # Relevance score for high alerts
        
        # Tracking to prevent duplicates
        self.alerted_threats = set()
        
        logger.info(f"✅ Alert system initialized")
        logger.info(f"   Slack: {'enabled' if self.slack_enabled else 'disabled'}")
        logger.info(f"   Email: enabled")
    
    def check_and_alert(self, items: List[Dict], industry: str, 
                       alert_emails: List[str] = None) -> int:
        """
        Check intelligence items and send alerts for critical threats
        
        Args:
            items: Intelligence items to check
            industry: Client industry
            alert_emails: List of emails for critical alerts
        
        Returns:
            Number of alerts sent
        """
        # Filter and score for industry
        filtered = self.client_filter.filter_for_client(items, industry)
        
        # Find critical threats
        critical_threats = [
            item for item in filtered 
            if item['relevance_score'] >= self.critical_threshold 
            and self._is_new_threat(item)
        ]
        
        if not critical_threats:
            logger.info(f"✅ No critical threats for {industry}")
            return 0
        
        logger.warning(f"🚨 {len(critical_threats)} CRITICAL THREATS for {industry}!")
        
        # Send alerts
        alert_count = 0
        for threat in critical_threats:
            if self._send_alert(threat, industry, alert_emails):
                alert_count += 1
                self._mark_alerted(threat)
        
        return alert_count
    
    def _send_alert(self, threat: Dict, industry: str, 
                    alert_emails: List[str] = None) -> bool:
        """Send alert via all enabled channels"""
        success = False
        
        # Send via Slack
        if self.slack_enabled:
            if self._send_slack_alert(threat, industry):
                success = True
        
        # Send via Email
        if alert_emails:
            if self.email_sender.send_alert(alert_emails, threat):
                success = True
        
        return success
    
    def _send_slack_alert(self, threat: Dict, industry: str) -> bool:
        """Send alert to Slack"""
        try:
            # Build Slack message
            message = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"🚨 CRITICAL THREAT ALERT - {industry.upper()}",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{threat.get('title', 'Unknown Threat')}*"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Relevance Score:*\n{threat.get('relevance_score', 0)}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Source:*\n{threat.get('source', {}).get('name', 'Unknown')}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Match Reasons:*\n" + "\n".join([f"• {r}" for r in threat.get('match_reasons', [])[:5]])
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "View Details"
                                },
                                "url": threat.get('link', '#'),
                                "style": "danger"
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(
                self.slack_webhook,
                data=json.dumps(message),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Slack alert sent")
                return True
            else:
                logger.error(f"❌ Slack alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Slack alert error: {str(e)}")
            return False
    
    def _is_new_threat(self, threat: Dict) -> bool:
        """Check if threat has already been alerted"""
        threat_id = self._get_threat_id(threat)
        return threat_id not in self.alerted_threats
    
    def _mark_alerted(self, threat: Dict):
        """Mark threat as alerted"""
        threat_id = self._get_threat_id(threat)
        self.alerted_threats.add(threat_id)
    
    def _get_threat_id(self, threat: Dict) -> str:
        """Generate unique ID for threat"""
        # Use title + link as unique identifier
        return f"{threat.get('title', '')[:50]}_{threat.get('link', '')}"
    
    def monitor_continuous(self, get_items_func, client_config: Dict, 
                          check_interval: int = 300):
        """
        Continuously monitor for threats (for daemon mode)
        
        Args:
            get_items_func: Function that returns new intelligence items
            client_config: Dict of {industry: alert_emails}
            check_interval: Seconds between checks
        """
        import time
        
        logger.info("🔄 Starting continuous monitoring...")
        
        while True:
            try:
                # Get new items
                items = get_items_func()
                
                # Check for each industry
                for industry, emails in client_config.items():
                    self.check_and_alert(items, industry, emails)
                
                # Wait before next check
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitoring error: {str(e)}")
                time.sleep(60)  # Wait a minute before retry


class AlertConfig:
    """Configuration for alert system"""
    
    @staticmethod
    def load_from_file(filepath: str) -> Dict:
        """Load alert configuration from YAML"""
        import yaml
        
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def get_example_config() -> Dict:
        """Get example alert configuration"""
        return {
            'aviation': {
                'emails': ['security@airline.com', 'it@airline.com'],
                'slack_channel': '#aviation-security',
                'critical_threshold': 30,
                'high_threshold': 20
            },
            'healthcare': {
                'emails': ['security@hospital.com'],
                'slack_channel': '#healthcare-security',
                'critical_threshold': 35,  # Higher threshold for healthcare
                'high_threshold': 25
            },
            'energy': {
                'emails': ['security@power.com', 'ciso@power.com'],
                'slack_channel': '#energy-security',
                'critical_threshold': 40,  # Even higher for critical infrastructure
                'high_threshold': 30
            }
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test alert system
    alert_system = AlertSystem()
    
    # Test threat
    test_threat = {
        'title': 'Critical Ransomware Campaign Targeting Healthcare Epic EHR Systems',
        'description': 'New ransomware variant specifically targeting healthcare organizations using Epic EHR',
        'link': 'https://example.com/threat',
        'published': datetime.utcnow().isoformat(),
        'source': {'name': 'CISA', 'type': 'government'},
        'tags': ['ransomware', 'healthcare', 'EHR', 'epic']
    }
    
    # Score the threat
    filter_engine = ClientFilter()
    scored_threat = filter_engine.score_item(test_threat, 'healthcare')
    
    print("\n" + "=" * 80)
    print("🧪 TESTING ALERT SYSTEM")
    print("=" * 80)
    print(f"\nThreat: {scored_threat['title']}")
    print(f"Relevance Score: {scored_threat['relevance_score']}")
    print(f"Is Critical: {scored_threat['is_critical']}")
    print(f"Match Reasons: {', '.join(scored_threat['match_reasons'][:3])}")
    
    # Test alert (will only work if Slack webhook configured)
    if scored_threat['is_critical']:
        print("\n🚨 This would trigger a critical alert!")
        
        # Uncomment to actually send test alert:
        # alert_system._send_slack_alert(scored_threat, 'healthcare')
        
    print("\n✅ Alert system test complete!")
