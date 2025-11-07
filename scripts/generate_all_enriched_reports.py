#!/usr/bin/env python3
"""
Generate Enriched Reports for All 18 Industries
Demonstrates the power of the enrichment system
"""

import sys
import os
from pathlib import Path
import logging

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from collectors.unified_collector import UnifiedCollector
from delivery.enriched_newsletter_generator import EnrichedNewsletterGenerator
from processors.client_filter import ClientFilter

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 80)
    logger.info("🚀 GENERATING ENRICHED REPORTS FOR ALL 18 INDUSTRIES")
    logger.info("=" * 80)
    logger.info("")
    
    # Step 1: Collect intelligence
    logger.info("📡 Step 1: Collecting Intelligence...")
    collector = UnifiedCollector()
    results = collector.collect_all()
    items = results['total']
    
    logger.info(f"✅ Collected {len(items)} intelligence items")
    logger.info("")
    
    # Step 2: Get all industries
    client_filter = ClientFilter()
    industries = client_filter.get_available_industries()
    
    logger.info(f"📊 Step 2: Generating Enriched Reports for {len(industries)} Industries...")
    logger.info("")
    
    # Step 3: Generate enriched newsletters
    generator = EnrichedNewsletterGenerator()
    output_dir = Path('data/reports/newsletters/enriched_all')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_reports = []
    
    for i, industry in enumerate(industries, 1):
        try:
            logger.info(f"[{i}/{len(industries)}] Generating: {industry}")
            
            # Generate enriched newsletter
            html = generator.generate_enriched_newsletter(items, industry)
            
            # Save to file
            output_file = output_dir / f"{industry}_enriched.html"
            with open(output_file, 'w') as f:
                f.write(html)
            
            size_kb = len(html) / 1024
            logger.info(f"   ✅ Generated: {output_file.name} ({size_kb:.1f} KB)")
            
            generated_reports.append({
                'industry': industry,
                'file': output_file,
                'size': len(html)
            })
            
        except Exception as e:
            logger.error(f"   ❌ Failed: {str(e)[:100]}")
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 GENERATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Reports Generated: {len(generated_reports)}/{len(industries)}")
    logger.info(f"Total Size: {sum(r['size'] for r in generated_reports) / 1024:.1f} KB")
    logger.info(f"Average Size: {sum(r['size'] for r in generated_reports) / len(generated_reports) / 1024:.1f} KB")
    logger.info(f"Output Directory: {output_dir}")
    logger.info("")
    
    # Create index
    create_enriched_index(generated_reports, output_dir)
    
    logger.info("=" * 80)
    logger.info("✅ ALL ENRICHED REPORTS GENERATED!")
    logger.info("=" * 80)
    logger.info(f"")
    logger.info(f"📂 View reports: file://{output_dir.absolute()}/index.html")
    logger.info("")
    
    return 0


def create_enriched_index(reports, output_dir):
    """Create index page for enriched reports"""
    
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Enriched Threat Intelligence Reports - All 18 Industries</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container {
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        h1 {
            color: #333;
            margin: 0 0 10px 0;
            font-size: 36px;
        }
        .subtitle {
            color: #666;
            font-size: 18px;
        }
        .badge {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            margin: 20px 0;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 40px;
        }
        .card {
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 24px;
            transition: all 0.3s;
            cursor: pointer;
            background: white;
        }
        .card:hover {
            border-color: #667eea;
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
            transform: translateY(-4px);
        }
        .card h3 {
            margin: 0 0 12px 0;
            color: #333;
            font-size: 20px;
        }
        .card .meta {
            color: #666;
            font-size: 14px;
            margin-bottom: 16px;
        }
        .card .enrichment-badge {
            display: inline-block;
            background: #4caf50;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 12px;
        }
        .btn {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
        }
        .btn:hover {
            background: #5568d3;
        }
        .feature-list {
            background: #f5f5f5;
            border-radius: 8px;
            padding: 24px;
            margin: 30px 0;
        }
        .feature-list h3 {
            color: #333;
            margin: 0 0 16px 0;
        }
        .feature-list ul {
            margin: 0;
            padding-left: 20px;
        }
        .feature-list li {
            margin: 8px 0;
            color: #555;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Enriched Threat Intelligence Reports</h1>
            <p class="subtitle">Expert Analysis + Real-Time Threats • All 18 Fortune 1000 Industries</p>
            <span class="badge">✨ ENRICHED WITH 10 EXPERT SECTIONS</span>
        </div>
        
        <div class="feature-list">
            <h3>🎯 What's Included in Every Enriched Report:</h3>
            <ul>
                <li>✅ Real-time threat intelligence (RSS + Social Media)</li>
                <li>✅ Threat Landscape Analysis (current state of your industry)</li>
                <li>✅ Active Threat Actor Spotlight (who's targeting you)</li>
                <li>✅ Critical Vulnerabilities (CVEs in your vendor stack)</li>
                <li>✅ Recommended Security Controls (actionable checklist)</li>
                <li>✅ Compliance Updates (deadlines and requirements)</li>
                <li>✅ Industry Statistics (breach costs and trends)</li>
                <li>✅ Expert Analysis (not just data aggregation)</li>
            </ul>
        </div>
        
        <div class="grid">
"""
    
    # Add cards for each industry
    for report in sorted(reports, key=lambda x: x['industry']):
        industry = report['industry']
        size_kb = report['size'] / 1024
        
        # Map industry to emoji and name
        industry_map = {
            'aviation': ('✈️', 'Aviation & Airlines'),
            'energy': ('⚡', 'Energy & Utilities'),
            'healthcare': ('🏥', 'Healthcare & Hospitals'),
            'government': ('🏛️', 'Government'),
            'financial': ('💰', 'Financial Services'),
            'education': ('🎓', 'Education'),
            'manufacturing': ('🏭', 'Manufacturing'),
            'retail': ('🛒', 'Retail'),
            'technology': ('💻', 'Technology'),
            'telecommunications': ('📡', 'Telecommunications'),
            'pharmaceuticals': ('💊', 'Pharmaceuticals'),
            'insurance': ('🏢', 'Insurance'),
            'automotive': ('🚗', 'Automotive'),
            'media': ('📺', 'Media'),
            'hospitality': ('🏨', 'Hospitality'),
            'professional_services': ('⚖️', 'Professional Services'),
            'transportation': ('🚚', 'Transportation'),
            'real_estate': ('🏢', 'Real Estate')
        }
        
        emoji, name = industry_map.get(industry, ('📊', industry.title()))
        
        html += f"""
            <div class="card" onclick="window.open('{industry}_enriched.html', '_blank')">
                <div class="enrichment-badge">✨ ENRICHED</div>
                <h3>{emoji} {name}</h3>
                <div class="meta">{size_kb:.1f} KB • 10 Expert Sections</div>
                <a href="{industry}_enriched.html" class="btn" target="_blank">View Enriched Report →</a>
            </div>
        """
    
    html += """
        </div>
        
        <div style="margin-top: 60px; text-align: center; color: #666;">
            <p><strong>cyber-pi Enriched Threat Intelligence Platform</strong></p>
            <p>Transform any report into comprehensive expert analysis • Powered by Nexum</p>
        </div>
    </div>
</body>
</html>
"""
    
    index_file = output_dir / 'index.html'
    with open(index_file, 'w') as f:
        f.write(html)
    
    logger.info(f"📄 Index page created: {index_file}")


if __name__ == "__main__":
    sys.exit(main())
