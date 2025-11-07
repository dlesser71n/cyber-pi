"""
Enriched Newsletter Generator
Adds expert intelligence to create comprehensive reports
"""

import yaml
from pathlib import Path
from jinja2 import Template
from datetime import datetime
import sys

sys.path.append(str(Path(__file__).parent.parent))

from processors.client_filter import ClientFilter

class EnrichedNewsletterGenerator:
    """Generate newsletters with expert intelligence enrichment"""
    
    def __init__(self):
        # Load intelligence database
        intel_db_path = Path(__file__).parent.parent / 'intelligence' / 'industry_intelligence_db.yaml'
        with open(intel_db_path, 'r') as f:
            self.intelligence_db = yaml.safe_load(f)
        
        self.client_filter = ClientFilter()
        
        # Load enriched template
        template_path = Path(__file__).parent.parent / 'templates' / 'enriched_email_template.html'
        if template_path.exists():
            with open(template_path, 'r') as f:
                self.template = Template(f.read())
        else:
            # Fallback to basic template
            template_path = Path(__file__).parent.parent / 'templates' / 'email_report_template.html'
            with open(template_path, 'r') as f:
                self.template = Template(f.read())
    
    def generate_enriched_newsletter(self, items: list, industry: str) -> str:
        """Generate newsletter with intelligence enrichment"""
        
        # Get base report
        report = self.client_filter.generate_client_report(items, industry)
        
        # Get intelligence enrichment
        intel = self.intelligence_db.get(industry, {})
        
        # Add enrichment sections
        enrichment = {
            'threat_landscape': intel.get('threat_landscape', {}),
            'threat_actor': intel.get('threat_actors', {}).get('primary', {}),
            'vulnerabilities': intel.get('critical_vulnerabilities', [])[:3],
            'security_controls': intel.get('security_controls', {}),
            'compliance': intel.get('compliance_updates', []),
            'statistics': intel.get('industry_statistics', {})
        }
        
        # Render template with enrichment
        html = self.template.render(
            industry_name=report['industry_name'],
            date=datetime.utcnow().strftime('%B %d, %Y'),
            critical_count=report['summary']['critical_threats'],
            high_count=report['summary']['high_priority'],
            medium_count=report['summary']['medium_priority'],
            total_count=report['summary']['total_threats'],
            executive_summary=self._generate_enriched_summary(report, enrichment),
            critical_threats=report['critical_threats'],
            high_priority_threats=report['high_priority_threats'],
            vendor_alerts=report['vendor_alerts'],
            compliance_updates=report['compliance_updates'],
            # Enrichment sections
            threat_landscape=enrichment['threat_landscape'],
            threat_actor=enrichment['threat_actor'],
            vulnerabilities=enrichment['vulnerabilities'],
            security_controls=enrichment['security_controls'],
            compliance_intel=enrichment['compliance'],
            statistics=enrichment['statistics']
        )
        
        return html
    
    def _generate_enriched_summary(self, report: dict, enrichment: dict) -> str:
        """Generate executive summary with enrichment context"""
        
        summary = report['summary']
        landscape = enrichment.get('threat_landscape', {})
        
        # Base summary
        if summary['critical_threats'] > 0:
            tone = f"⚠️ <strong>CRITICAL:</strong> {summary['critical_threats']} critical threats require immediate attention."
        elif summary['high_priority'] > 5:
            tone = f"⚠️ <strong>ELEVATED:</strong> {summary['high_priority']} high-priority threats detected."
        else:
            tone = "✅ Threat landscape is relatively calm with no critical threats."
        
        # Add threat landscape context
        current_trend = landscape.get('current_trend', '')
        risk_level = landscape.get('risk_level', 'MEDIUM')
        
        text = f"""
        {tone} This report analyzes {summary['total_threats']} new threat intelligence items 
        relevant to the {report['industry_name']} industry.
        <br><br>
        <strong>Current Threat Landscape:</strong> {current_trend}
        <br>
        <strong>Industry Risk Level:</strong> <span style="color: {'#d32f2f' if risk_level == 'CRITICAL' else '#f57c00' if risk_level == 'HIGH' else '#1976d2'};">{risk_level}</span>
        """
        
        return text.strip()


if __name__ == "__main__":
    # Test enriched newsletter
    from collectors.unified_collector import UnifiedCollector
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    # Collect some data
    collector = UnifiedCollector()
    results = collector.collect_all()
    
    # Generate enriched newsletter
    generator = EnrichedNewsletterGenerator()
    
    # Test for aviation
    html = generator.generate_enriched_newsletter(results['total'], 'aviation')
    
    # Save
    output_file = Path('data/reports/newsletters/test_enriched_aviation.html')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"✅ Enriched newsletter generated: {output_file}")
    print(f"   Size: {len(html)} bytes")
