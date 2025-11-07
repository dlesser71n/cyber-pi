"""
cyber-pi Unique Report Formats
Innovative ways to present threat intelligence
"""

import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from pathlib import Path
from collections import defaultdict

# Import configuration
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import settings

logger = logging.getLogger(__name__)


class UniqueReportFormats:
    """
    Generate threat intelligence in unique, engaging formats
    """
    
    def __init__(self, items: List[Dict[str, Any]]):
        self.items = items
        
    def generate_threat_story(self) -> str:
        """
        Format 1: NARRATIVE STORY FORMAT
        Presents threats as a story/timeline
        """
        report = []
        report.append("=" * 80)
        report.append("🕵️ CYBER THREAT INTELLIGENCE BRIEFING")
        report.append("The Week in Cybersecurity: A Threat Actor's Perspective")
        report.append("=" * 80)
        report.append("")
        
        # Group by severity/type for narrative
        critical_cves = [i for i in self.items if i.get('cvss_score', 0) >= 9.0]
        malware_items = [i for i in self.items if any(k in str(i.get('title', '')).lower() 
                        for k in ['malware', 'ransomware', 'botnet'])]
        breach_items = [i for i in self.items if any(k in str(i.get('title', '')).lower() 
                       for k in ['breach', 'leak', 'exposed'])]
        
        report.append("📖 THIS WEEK'S CYBER NARRATIVE")
        report.append("-" * 80)
        report.append("")
        
        if critical_cves:
            report.append("🚨 THE CRITICAL VULNERABILITY CRISIS")
            report.append("")
            report.append(f"This week revealed {len(critical_cves)} CRITICAL vulnerabilities (CVSS 9.0+)")
            report.append("that could allow attackers to completely compromise systems.")
            report.append("")
            for i, item in enumerate(critical_cves[:3], 1):
                cve_id = item.get('cve_id', 'Unknown')
                cvss = item.get('cvss_score', 0)
                report.append(f"  {i}. {cve_id} (CVSS {cvss})")
                report.append(f"     Impact: {item.get('description', 'N/A')[:100]}...")
                report.append("")
        
        if malware_items:
            report.append("🦠 THE MALWARE LANDSCAPE")
            report.append("")
            report.append(f"Threat actors deployed {len(malware_items)} new malware campaigns,")
            report.append("targeting organizations across multiple sectors.")
            report.append("")
            for i, item in enumerate(malware_items[:3], 1):
                report.append(f"  {i}. {item.get('title', 'Unknown')[:70]}")
                report.append(f"     Source: {item.get('source', {}).get('name', 'Unknown')}")
                report.append("")
        
        if breach_items:
            report.append("💔 DATA BREACH INCIDENTS")
            report.append("")
            report.append(f"{len(breach_items)} organizations reported security incidents,")
            report.append("exposing sensitive data and compromising user trust.")
            report.append("")
            for i, item in enumerate(breach_items[:3], 1):
                report.append(f"  {i}. {item.get('title', 'Unknown')[:70]}")
                report.append("")
        
        report.append("=" * 80)
        report.append("📊 THREAT INTELLIGENCE SUMMARY")
        report.append(f"Total Threats Analyzed: {len(self.items)}")
        report.append(f"Critical Vulnerabilities: {len(critical_cves)}")
        report.append(f"Malware Campaigns: {len(malware_items)}")
        report.append(f"Breach Incidents: {len(breach_items)}")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def generate_threat_matrix(self) -> str:
        """
        Format 2: THREAT MATRIX (Visual Grid)
        Presents threats in a matrix by severity and category
        """
        report = []
        report.append("=" * 100)
        report.append("🎯 CYBER THREAT MATRIX - VISUAL INTELLIGENCE DASHBOARD")
        report.append("=" * 100)
        report.append("")
        
        # Create matrix
        categories = ['Vulnerabilities', 'Malware', 'Breaches', 'APT/Nation-State', 'Vendor Advisories']
        severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        
        # Count items in each cell
        matrix = defaultdict(lambda: defaultdict(int))
        
        for item in self.items:
            # Determine category
            title = str(item.get('title', '')).lower()
            tags = item.get('tags', [])
            
            if any(t in tags for t in ['cve', 'vulnerability']) or 'cve-' in title:
                category = 'Vulnerabilities'
            elif any(k in title for k in ['malware', 'ransomware', 'botnet']):
                category = 'Malware'
            elif any(k in title for k in ['breach', 'leak', 'exposed']):
                category = 'Breaches'
            elif any(k in title for k in ['apt', 'nation-state']):
                category = 'APT/Nation-State'
            else:
                category = 'Vendor Advisories'
            
            # Determine severity
            cvss = item.get('cvss_score', 0)
            if cvss >= 9.0:
                severity = 'CRITICAL'
            elif cvss >= 7.0:
                severity = 'HIGH'
            elif cvss >= 4.0:
                severity = 'MEDIUM'
            else:
                severity = 'LOW'
            
            matrix[category][severity] += 1
        
        # Print matrix
        report.append("┌" + "─" * 25 + "┬" + "─" * 15 + "┬" + "─" * 15 + "┬" + "─" * 15 + "┬" + "─" * 15 + "┐")
        report.append(f"│ {'CATEGORY':<23} │ {'CRITICAL':^13} │ {'HIGH':^13} │ {'MEDIUM':^13} │ {'LOW':^13} │")
        report.append("├" + "─" * 25 + "┼" + "─" * 15 + "┼" + "─" * 15 + "┼" + "─" * 15 + "┼" + "─" * 15 + "┤")
        
        for category in categories:
            critical = matrix[category]['CRITICAL']
            high = matrix[category]['HIGH']
            medium = matrix[category]['MEDIUM']
            low = matrix[category]['LOW']
            
            # Visual indicators
            crit_vis = "🔴" * min(critical, 5) if critical > 0 else "-"
            high_vis = "🟠" * min(high, 5) if high > 0 else "-"
            med_vis = "🟡" * min(medium, 5) if medium > 0 else "-"
            low_vis = "🟢" * min(low, 5) if low > 0 else "-"
            
            report.append(f"│ {category:<23} │ {critical:>3} {crit_vis:<9} │ {high:>3} {high_vis:<9} │ {medium:>3} {med_vis:<9} │ {low:>3} {low_vis:<9} │")
        
        report.append("└" + "─" * 25 + "┴" + "─" * 15 + "┴" + "─" * 15 + "┴" + "─" * 15 + "┴" + "─" * 15 + "┘")
        report.append("")
        report.append("Legend: 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low")
        report.append("Each emoji = up to 5 threats in that category")
        report.append("")
        
        return "\n".join(report)
    
    def generate_threat_scorecard(self) -> str:
        """
        Format 3: THREAT SCORECARD (Sports-style)
        Presents threats like a sports scorecard with rankings
        """
        report = []
        report.append("=" * 80)
        report.append("🏆 CYBER THREAT SCORECARD - THIS WEEK'S RANKINGS")
        report.append("=" * 80)
        report.append("")
        
        # Calculate "threat scores" for different categories
        report.append("📊 THREAT LEVEL INDEX (0-100)")
        report.append("-" * 80)
        
        # Count critical items
        critical_count = sum(1 for i in self.items if i.get('cvss_score', 0) >= 9.0)
        high_count = sum(1 for i in self.items if 7.0 <= i.get('cvss_score', 0) < 9.0)
        
        # Calculate threat index
        threat_index = min(100, (critical_count * 10) + (high_count * 5))
        
        report.append(f"Overall Threat Level: {threat_index}/100 {'🔥' * (threat_index // 20)}")
        report.append("")
        
        # Top threats leaderboard
        report.append("🥇 TOP 10 THREAT LEADERBOARD")
        report.append("-" * 80)
        
        # Sort by CVSS score
        sorted_items = sorted(self.items, key=lambda x: x.get('cvss_score', 0), reverse=True)
        
        for i, item in enumerate(sorted_items[:10], 1):
            cvss = item.get('cvss_score', 0)
            title = item.get('title', 'Unknown')[:60]
            
            # Medal emojis
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}."
            
            # Threat bar
            bar_length = int((cvss / 10) * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            report.append(f"{medal} {title}")
            report.append(f"    Score: {cvss:.1f}/10 [{bar}]")
            report.append("")
        
        return "\n".join(report)
    
    def generate_executive_dashboard(self) -> str:
        """
        Format 4: EXECUTIVE DASHBOARD (Metrics-focused)
        C-Suite friendly with KPIs and metrics
        """
        report = []
        report.append("=" * 80)
        report.append("📈 EXECUTIVE CYBER THREAT DASHBOARD")
        report.append(f"Report Date: {datetime.now(timezone.utc).strftime('%B %d, %Y')}")
        report.append("=" * 80)
        report.append("")
        
        # Key metrics
        total_threats = len(self.items)
        critical_threats = sum(1 for i in self.items if i.get('cvss_score', 0) >= 9.0)
        high_threats = sum(1 for i in self.items if 7.0 <= i.get('cvss_score', 0) < 9.0)
        
        report.append("🎯 KEY PERFORMANCE INDICATORS")
        report.append("-" * 80)
        report.append(f"Total Threats Monitored:        {total_threats:>6}")
        report.append(f"Critical Vulnerabilities:       {critical_threats:>6}  ⚠️  IMMEDIATE ACTION REQUIRED")
        report.append(f"High-Priority Threats:          {high_threats:>6}  ⚡ URGENT ATTENTION")
        report.append(f"Medium/Low Priority:            {total_threats - critical_threats - high_threats:>6}  📋 Monitor")
        report.append("")
        
        # Risk assessment
        risk_score = min(100, (critical_threats * 5) + (high_threats * 2))
        risk_level = "CRITICAL" if risk_score >= 80 else "HIGH" if risk_score >= 60 else "MODERATE" if risk_score >= 40 else "LOW"
        
        report.append("⚠️  ORGANIZATIONAL RISK ASSESSMENT")
        report.append("-" * 80)
        report.append(f"Current Risk Level: {risk_level} ({risk_score}/100)")
        report.append("")
        
        # Recommendations
        report.append("💡 EXECUTIVE RECOMMENDATIONS")
        report.append("-" * 80)
        if critical_threats > 0:
            report.append(f"1. IMMEDIATE: Patch {critical_threats} critical vulnerabilities within 24 hours")
        if high_threats > 0:
            report.append(f"2. URGENT: Address {high_threats} high-priority threats within 72 hours")
        report.append("3. ONGOING: Maintain continuous monitoring of threat landscape")
        report.append("4. STRATEGIC: Review and update incident response procedures")
        report.append("")
        
        return "\n".join(report)
    
    def generate_threat_timeline(self) -> str:
        """
        Format 5: THREAT TIMELINE (Chronological story)
        Shows threats as they emerged over time
        """
        report = []
        report.append("=" * 80)
        report.append("⏰ CYBER THREAT TIMELINE - 24 HOUR INTELLIGENCE FEED")
        report.append("=" * 80)
        report.append("")
        
        # Sort by published date
        dated_items = [i for i in self.items if i.get('published')]
        dated_items.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        report.append("📅 RECENT THREAT ACTIVITY (Last 24 Hours)")
        report.append("-" * 80)
        
        for i, item in enumerate(dated_items[:15], 1):
            published = item.get('published', 'Unknown')
            title = item.get('title', 'Unknown')[:65]
            source = item.get('source', {}).get('name', 'Unknown')
            
            # Time indicator
            try:
                pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                time_str = pub_date.strftime('%H:%M UTC')
            except:
                time_str = 'Unknown'
            
            report.append(f"[{time_str}] {title}")
            report.append(f"           Source: {source}")
            report.append("")
        
        return "\n".join(report)


def generate_all_formats(collection_file: str):
    """Generate all unique report formats"""
    
    # Load data
    with open(collection_file, 'r') as f:
        data = json.load(f)
    
    items = data.get('items', [])
    
    # Create generator
    generator = UniqueReportFormats(items)
    
    # Generate all formats
    formats = {
        'narrative_story': generator.generate_threat_story(),
        'threat_matrix': generator.generate_threat_matrix(),
        'scorecard': generator.generate_threat_scorecard(),
        'executive_dashboard': generator.generate_executive_dashboard(),
        'timeline': generator.generate_threat_timeline()
    }
    
    # Save each format
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    
    for format_name, content in formats.items():
        output_file = f"{settings.reports_dir}/{format_name}_{timestamp}.txt"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Generated: {format_name}")
        print(f"   Saved to: {output_file}")
        print()
    
    # Print one format to console
    print("\n" + "=" * 80)
    print("PREVIEW: THREAT MATRIX FORMAT")
    print("=" * 80)
    print(formats['threat_matrix'])


if __name__ == "__main__":
    # Find latest collection
    data_dir = Path(settings.raw_data_dir)
    collection_files = sorted(data_dir.glob("master_collection_*.json"), reverse=True)
    
    if collection_files:
        print(f"Processing: {collection_files[0]}")
        generate_all_formats(str(collection_files[0]))
    else:
        print("No collection files found!")
