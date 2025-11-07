"""
Automated Newsletter Generation
Creates industry-specific threat intelligence reports and sends via email
"""

from jinja2 import Template
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import logging
import sys
import os

sys.path.append(str(Path(__file__).parent.parent))

from processors.client_filter import ClientFilter
from delivery.email_sender import EmailSender

logger = logging.getLogger(__name__)


class NewsletterGenerator:
    """Generate and send industry-specific threat intelligence newsletters"""
    
    def __init__(self):
        self.client_filter = ClientFilter()
        self.email_sender = EmailSender(method='smtp')
        
        template_path = Path(__file__).parent.parent / 'templates' / 'email_report_template.html'
        with open(template_path, 'r') as f:
            self.template = Template(f.read())
        
        logger.info("✅ Newsletter generator initialized")
    
    def generate_newsletter(self, items: List[Dict], industry: str) -> str:
        """
        Generate HTML newsletter for specific industry
        
        Args:
            items: Raw intelligence items
            industry: Industry key (aviation, energy, healthcare, etc.)
        
        Returns:
            HTML newsletter content
        """
        # Generate client report
        report = self.client_filter.generate_client_report(items, industry)
        
        if 'error' in report:
            logger.error(f"Error generating report: {report['error']}")
            return ""
        
        # Prepare executive summary
        exec_summary = self._generate_executive_summary(report)
        
        # Render template
        html = self.template.render(
            industry_name=report['industry_name'],
            date=datetime.utcnow().strftime('%B %d, %Y'),
            critical_count=report['summary']['critical_threats'],
            high_count=report['summary']['high_priority'],
            medium_count=report['summary']['medium_priority'],
            total_count=report['summary']['total_threats'],
            executive_summary=exec_summary,
            critical_threats=report['critical_threats'],
            high_priority_threats=report['high_priority_threats'],
            vendor_alerts=report['vendor_alerts'],
            compliance_updates=report['compliance_updates']
        )
        
        return html
    
    def _generate_executive_summary(self, report: Dict) -> str:
        """Generate executive summary text"""
        summary = report['summary']
        
        if summary['critical_threats'] > 0:
            tone = f"⚠️ <strong>CRITICAL:</strong> {summary['critical_threats']} critical threats require immediate attention."
        elif summary['high_priority'] > 5:
            tone = f"⚠️ <strong>ELEVATED:</strong> {summary['high_priority']} high-priority threats detected."
        else:
            tone = "✅ Threat landscape is relatively calm with no critical threats."
        
        text = f"""
        {tone} This report analyzes {summary['total_threats']} threat intelligence items 
        relevant to the {report['industry_name']} industry. Key findings include vendor-specific 
        advisories, compliance updates, and emerging threats targeting your sector.
        """
        
        return text.strip()
    
    def send_newsletter(self, items: List[Dict], industry: str, 
                       to_emails: List[str]) -> bool:
        """
        Generate and send newsletter
        
        Args:
            items: Raw intelligence items
            industry: Industry key
            to_emails: List of recipient emails
        
        Returns:
            True if sent successfully
        """
        logger.info(f"📧 Generating newsletter for {industry}")
        
        html = self.generate_newsletter(items, industry)
        
        if not html:
            logger.error("Failed to generate newsletter")
            return False
        
        # Get industry name for subject
        profile = self.client_filter.config.get(industry, {})
        industry_name = profile.get('name', industry)
        
        subject = f"🛡️ {industry_name} Threat Intelligence - {datetime.utcnow().strftime('%B %d, %Y')}"
        
        return self.email_sender.send_report(to_emails, subject, html)
    
    def send_daily_briefings(self, items: List[Dict], client_config: Dict) -> int:
        """
        Send daily briefings to all configured clients
        
        Args:
            items: Raw intelligence items
            client_config: Dict mapping industry -> email list
            
        Example:
            {
                'aviation': ['airline1@example.com', 'airline2@example.com'],
                'healthcare': ['hospital1@example.com'],
                'energy': ['power1@example.com', 'power2@example.com']
            }
        
        Returns:
            Number of successfully sent newsletters
        """
        sent_count = 0
        
        logger.info("=" * 80)
        logger.info("📬 SENDING DAILY BRIEFINGS")
        logger.info("=" * 80)
        
        for industry, emails in client_config.items():
            logger.info(f"\n📨 Industry: {industry}")
            logger.info(f"   Recipients: {len(emails)}")
            
            success = self.send_newsletter(items, industry, emails)
            
            if success:
                sent_count += 1
                logger.info(f"   ✅ Sent successfully")
            else:
                logger.error(f"   ❌ Failed to send")
        
        logger.info("\n" + "=" * 80)
        logger.info(f"📊 SUMMARY: {sent_count}/{len(client_config)} newsletters sent")
        logger.info("=" * 80)
        
        return sent_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test newsletter generation
    test_items = [
        {
            'title': 'Critical Ransomware Campaign Targets Healthcare',
            'description': 'New ransomware variant specifically targeting Epic EHR systems',
            'link': 'https://example.com/threat1',
            'published': '2025-10-31T14:00:00',
            'source': {'name': 'Cyber Threat Alliance', 'type': 'vendor'},
            'tags': ['ransomware', 'healthcare', 'EHR']
        },
        {
            'title': 'Aviation Booking System Vulnerability Disclosed',
            'description': 'Critical SQL injection in Amadeus reservation platform',
            'link': 'https://example.com/threat2',
            'published': '2025-10-31T12:00:00',
            'source': {'name': 'Security Week', 'type': 'news'},
            'tags': ['vulnerability', 'aviation', 'SQL injection']
        }
    ]
    
    generator = NewsletterGenerator()
    
    # Generate sample for each industry
    for industry in ['aviation', 'healthcare', 'energy']:
        print(f"\n{'='*60}")
        print(f"Generating {industry} newsletter...")
        print('='*60)
        
        html = generator.generate_newsletter(test_items, industry)
        
        # Save to file
        output_dir = Path('data/reports/newsletters')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"test_{industry}_newsletter.html"
        with open(output_file, 'w') as f:
            f.write(html)
        
        print(f"✅ Saved to: {output_file}")
    
    print("\n✅ Newsletter generation test complete!")
