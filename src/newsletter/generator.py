"""
cyber-pi Newsletter Generator
Transforms 1000+ intelligence items into actionable reports
Uses prioritization, deduplication, and intelligent summarization
"""

import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
from collections import defaultdict
import hashlib

# Import configuration
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsletterGenerator:
    """
    Generates actionable intelligence reports from massive data
    Prioritizes, deduplicates, and organizes for readability
    """
    
    def __init__(self):
        self.items = []
        self.stats = {
            'total_items': 0,
            'after_dedup': 0,
            'high_priority': 0,
            'medium_priority': 0,
            'low_priority': 0
        }
        
    def load_collection(self, filepath: str) -> None:
        """
        Load intelligence collection from JSON
        
        Args:
            filepath: Path to collection JSON file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.items = data.get('items', [])
        self.stats['total_items'] = len(self.items)
        
        logger.info(f"Loaded {len(self.items)} intelligence items")
    
    def deduplicate(self) -> List[Dict[str, Any]]:
        """
        Remove duplicate items based on title similarity
        
        Returns:
            Deduplicated list of items
        """
        seen_titles = set()
        unique_items = []
        
        for item in self.items:
            title = item.get('title', '')
            # Create a normalized hash of the title
            title_hash = hashlib.md5(title.lower().strip().encode()).hexdigest()
            
            if title_hash not in seen_titles:
                seen_titles.add(title_hash)
                unique_items.append(item)
        
        self.stats['after_dedup'] = len(unique_items)
        logger.info(f"Deduplication: {len(self.items)} → {len(unique_items)} items")
        
        return unique_items
    
    def calculate_priority(self, item: Dict[str, Any]) -> tuple[int, str]:
        """
        Calculate priority score for an item
        
        Args:
            item: Intelligence item
            
        Returns:
            Tuple of (score, priority_level)
        """
        score = 0
        
        # Source credibility (0-50 points)
        credibility = item.get('source', {}).get('credibility', 0.5)
        score += int(credibility * 50)
        
        # CVE/Vulnerability items get high priority (30 points)
        tags = item.get('tags', [])
        if any(tag in ['cve', 'vulnerability', 'exploit'] for tag in tags):
            score += 30
        
        # Critical keywords in title (20 points)
        title = item.get('title', '').lower()
        critical_keywords = ['zero-day', 'critical', 'ransomware', 'breach', 'exploit', 
                            'nation-state', 'apt', 'vulnerability', 'rce', 'authentication bypass']
        if any(keyword in title for keyword in critical_keywords):
            score += 20
        
        # CVSS score for CVEs (0-20 points)
        cvss_score = item.get('cvss_score', 0)
        if cvss_score > 0:
            score += int((cvss_score / 10) * 20)
        
        # Recency (0-10 points)
        published = item.get('published', '')
        if published:
            try:
                pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                days_old = (datetime.now(timezone.utc) - pub_date).days
                if days_old <= 1:
                    score += 10
                elif days_old <= 3:
                    score += 5
            except:
                pass
        
        # Determine priority level
        if score >= 80:
            priority = 'critical'
        elif score >= 60:
            priority = 'high'
        elif score >= 40:
            priority = 'medium'
        else:
            priority = 'low'
        
        return score, priority
    
    def prioritize_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add priority scores and sort by priority
        
        Args:
            items: List of intelligence items
            
        Returns:
            Sorted list with priority scores
        """
        for item in items:
            score, priority = self.calculate_priority(item)
            item['priority_score'] = score
            item['priority_level'] = priority
            
            # Update stats
            if priority == 'critical':
                self.stats['high_priority'] += 1
            elif priority == 'high':
                self.stats['high_priority'] += 1
            elif priority == 'medium':
                self.stats['medium_priority'] += 1
            else:
                self.stats['low_priority'] += 1
        
        # Sort by priority score (highest first)
        items.sort(key=lambda x: x['priority_score'], reverse=True)
        
        logger.info(f"Prioritization complete:")
        logger.info(f"  Critical/High: {self.stats['high_priority']}")
        logger.info(f"  Medium: {self.stats['medium_priority']}")
        logger.info(f"  Low: {self.stats['low_priority']}")
        
        return items
    
    def categorize_items(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Organize items into categories
        
        Args:
            items: List of intelligence items
            
        Returns:
            Dictionary of categorized items
        """
        categories = {
            'vulnerabilities': [],
            'threat_actors': [],
            'malware': [],
            'breaches': [],
            'vendor_advisories': [],
            'news': [],
            'other': []
        }
        
        for item in items:
            title = item.get('title', '').lower()
            tags = item.get('tags', [])
            
            # Categorize based on tags and keywords
            if any(tag in ['cve', 'vulnerability'] for tag in tags) or 'cve-' in title:
                categories['vulnerabilities'].append(item)
            elif any(keyword in title for keyword in ['apt', 'nation-state', 'threat actor']):
                categories['threat_actors'].append(item)
            elif any(keyword in title for keyword in ['malware', 'ransomware', 'trojan', 'botnet']):
                categories['malware'].append(item)
            elif any(keyword in title for keyword in ['breach', 'leak', 'exposed', 'compromised']):
                categories['breaches'].append(item)
            elif item.get('source', {}).get('type') == 'rss' and 'vendor' in str(tags):
                categories['vendor_advisories'].append(item)
            elif item.get('source', {}).get('type') in ['rss', 'web_scrape']:
                categories['news'].append(item)
            else:
                categories['other'].append(item)
        
        return categories
    
    def generate_executive_summary(self, items: List[Dict[str, Any]]) -> str:
        """
        Generate executive summary (top 10 items)
        
        Args:
            items: Prioritized list of items
            
        Returns:
            Formatted executive summary
        """
        summary = []
        summary.append("=" * 80)
        summary.append("EXECUTIVE SUMMARY - TOP 10 CRITICAL THREATS")
        summary.append("=" * 80)
        summary.append("")
        
        for i, item in enumerate(items[:10], 1):
            title = item.get('title', 'No title')
            source = item.get('source', {}).get('name', 'Unknown')
            priority = item.get('priority_level', 'unknown').upper()
            score = item.get('priority_score', 0)
            
            summary.append(f"{i}. [{priority}] {title[:70]}")
            summary.append(f"   Source: {source} | Priority Score: {score}")
            
            # Add CVSS if available
            if 'cvss_score' in item:
                summary.append(f"   CVSS: {item['cvss_score']} | Severity: {item.get('severity', 'N/A')}")
            
            summary.append("")
        
        return "\n".join(summary)
    
    def generate_category_report(self, 
                                 category_name: str, 
                                 items: List[Dict[str, Any]], 
                                 limit: int = 20) -> str:
        """
        Generate report for a specific category
        
        Args:
            category_name: Name of the category
            items: Items in this category
            limit: Maximum items to include
            
        Returns:
            Formatted category report
        """
        if not items:
            return ""
        
        report = []
        report.append("")
        report.append("=" * 80)
        report.append(f"{category_name.upper().replace('_', ' ')} ({len(items)} items)")
        report.append("=" * 80)
        report.append("")
        
        for i, item in enumerate(items[:limit], 1):
            title = item.get('title', 'No title')
            source = item.get('source', {}).get('name', 'Unknown')
            priority = item.get('priority_level', 'unknown')
            
            report.append(f"{i}. [{priority.upper()}] {title[:70]}")
            report.append(f"   Source: {source}")
            
            # Add URL if available
            if 'link' in item:
                report.append(f"   Link: {item['link']}")
            elif 'url' in item:
                report.append(f"   Link: {item['url']}")
            
            report.append("")
        
        if len(items) > limit:
            report.append(f"... and {len(items) - limit} more items in this category")
            report.append("")
        
        return "\n".join(report)
    
    def generate_full_report(self, output_file: str = None) -> str:
        """
        Generate complete intelligence report
        
        Args:
            output_file: Optional file to save report
            
        Returns:
            Full report text
        """
        logger.info("Generating intelligence report...")
        
        # Step 1: Deduplicate
        unique_items = self.deduplicate()
        
        # Step 2: Prioritize
        prioritized_items = self.prioritize_items(unique_items)
        
        # Step 3: Categorize
        categories = self.categorize_items(prioritized_items)
        
        # Step 4: Build report
        report = []
        
        # Header
        report.append("=" * 80)
        report.append("CYBER-PI THREAT INTELLIGENCE REPORT")
        report.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append("=" * 80)
        report.append("")
        
        # Statistics
        report.append("COLLECTION STATISTICS")
        report.append("-" * 80)
        report.append(f"Total Items Collected: {self.stats['total_items']}")
        report.append(f"After Deduplication: {self.stats['after_dedup']}")
        report.append(f"Critical/High Priority: {self.stats['high_priority']}")
        report.append(f"Medium Priority: {self.stats['medium_priority']}")
        report.append(f"Low Priority: {self.stats['low_priority']}")
        report.append("")
        
        # Executive Summary
        report.append(self.generate_executive_summary(prioritized_items))
        
        # Category Reports (top items only)
        report.append(self.generate_category_report("Vulnerabilities & CVEs", 
                                                    categories['vulnerabilities'], limit=15))
        report.append(self.generate_category_report("Threat Actors & APTs", 
                                                    categories['threat_actors'], limit=10))
        report.append(self.generate_category_report("Malware & Ransomware", 
                                                    categories['malware'], limit=10))
        report.append(self.generate_category_report("Data Breaches", 
                                                    categories['breaches'], limit=10))
        report.append(self.generate_category_report("Vendor Security Advisories", 
                                                    categories['vendor_advisories'], limit=15))
        report.append(self.generate_category_report("Security News", 
                                                    categories['news'], limit=10))
        
        # Footer
        report.append("")
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        full_report = "\n".join(report)
        
        # Save to file if specified
        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(full_report)
            logger.info(f"Report saved to: {output_file}")
        
        return full_report


def main():
    """Generate report from latest collection"""
    # Find latest collection file
    data_dir = Path(settings.raw_data_dir)
    collection_files = sorted(data_dir.glob("master_collection_*.json"), reverse=True)
    
    if not collection_files:
        logger.error("No collection files found!")
        return
    
    latest_file = collection_files[0]
    logger.info(f"Processing: {latest_file}")
    
    # Generate report
    generator = NewsletterGenerator()
    generator.load_collection(str(latest_file))
    
    # Generate and save report
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    output_file = f"{settings.reports_dir}/intelligence_report_{timestamp}.txt"
    
    report = generator.generate_full_report(output_file)
    
    # Print to console (first 100 lines)
    lines = report.split('\n')
    print('\n'.join(lines[:100]))
    
    if len(lines) > 100:
        print(f"\n... ({len(lines) - 100} more lines)")
        print(f"\nFull report saved to: {output_file}")


if __name__ == "__main__":
    main()
