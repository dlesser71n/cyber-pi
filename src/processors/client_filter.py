"""
Client-Specific Intelligence Filtering
Scores and filters threat intelligence based on client industry
"""

import yaml
import re
from typing import List, Dict, Set
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ClientFilter:
    """Filter and score threat intelligence for specific client industries"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "client_filters.yaml"
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.filter_settings = self.config.get('filter_settings', {})
        self.scoring = self.filter_settings.get('scoring', {})
        self.thresholds = self.filter_settings.get('thresholds', {})
        
        logger.info(f"✅ Client filters loaded: {len(self.config) - 1} industries")
    
    def get_available_industries(self) -> List[str]:
        """Get list of available industry filters"""
        return [k for k in self.config.keys() if k != 'filter_settings']
    
    def score_item(self, item: Dict, industry: str) -> Dict:
        """
        Score intelligence item for specific industry
        
        Args:
            item: Intelligence item with title, description, tags
            industry: Industry key (aviation, energy, healthcare, etc.)
        
        Returns:
            Item with added 'relevance_score' and 'match_reasons'
        """
        if industry not in self.config:
            logger.warning(f"Unknown industry: {industry}")
            return item
        
        profile = self.config[industry]
        score = 0
        reasons = []
        
        # Combine text for analysis
        text = f"{item.get('title', '')} {item.get('description', '')}".lower()
        tags = [t.lower() for t in item.get('tags', [])]
        
        # Score keyword matches
        for level in ['critical', 'high', 'medium']:
            keywords = profile.get('keywords', {}).get(level, [])
            weight = self.scoring.get(f'keyword_match_{level}', 0)
            
            for keyword in keywords:
                if keyword.lower() in text:
                    score += weight
                    if level == 'critical':
                        reasons.append(f"Critical keyword: '{keyword}'")
        
        # Score threat type matches
        threat_types = profile.get('threat_types', {})
        for level in ['critical', 'high', 'medium']:
            types = threat_types.get(level, [])
            weight = self.scoring.get(f'threat_type_match_{level}', 0)
            
            for threat_type in types:
                if threat_type.lower() in text:
                    score += weight
                    if level == 'critical':
                        reasons.append(f"Critical threat: '{threat_type}'")
        
        # Score vendor matches
        vendors = profile.get('watch_vendors', [])
        vendor_weight = self.scoring.get('vendor_match', 0)
        
        for vendor in vendors:
            if vendor.lower() in text:
                score += vendor_weight
                reasons.append(f"Vendor mention: '{vendor}'")
        
        # Score compliance matches
        compliance = profile.get('compliance', [])
        compliance_weight = self.scoring.get('compliance_match', 0)
        
        for comp in compliance:
            if comp.lower() in text:
                score += compliance_weight
                reasons.append(f"Compliance: '{comp}'")
        
        # Add scoring to item
        item['relevance_score'] = score
        item['match_reasons'] = reasons
        item['industry'] = industry
        item['is_critical'] = score >= self.thresholds.get('flag_as_critical', 30)
        
        return item
    
    def filter_for_client(self, items: List[Dict], industry: str, 
                         min_score: int = None) -> List[Dict]:
        """
        Filter intelligence items for specific client
        
        Args:
            items: List of intelligence items
            industry: Industry key
            min_score: Minimum relevance score (default from config)
        
        Returns:
            Filtered and scored items, sorted by relevance
        """
        if min_score is None:
            min_score = self.thresholds.get('include_in_report', 10)
        
        logger.info(f"📊 Filtering {len(items)} items for {industry}")
        
        # Score all items
        scored_items = [self.score_item(item.copy(), industry) for item in items]
        
        # Filter by minimum score
        filtered_items = [i for i in scored_items if i['relevance_score'] >= min_score]
        
        # Sort by relevance (highest first)
        filtered_items.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"✅ {len(filtered_items)} items relevant for {industry}")
        logger.info(f"   Critical items: {sum(1 for i in filtered_items if i['is_critical'])}")
        
        return filtered_items
    
    def generate_client_report(self, items: List[Dict], industry: str) -> Dict:
        """
        Generate industry-specific report
        
        Args:
            items: Raw intelligence items
            industry: Industry key
        
        Returns:
            Structured report with sections
        """
        filtered_items = self.filter_for_client(items, industry)
        
        if industry not in self.config:
            return {'error': f'Unknown industry: {industry}'}
        
        profile = self.config[industry]
        
        # Categorize items
        critical_items = [i for i in filtered_items if i['is_critical']]
        high_items = [i for i in filtered_items if 20 <= i['relevance_score'] < 30]
        medium_items = [i for i in filtered_items if 10 <= i['relevance_score'] < 20]
        
        # Generate report
        report = {
            'industry': industry,
            'industry_name': profile.get('name', industry),
            'generated_at': self._get_timestamp(),
            'summary': {
                'total_threats': len(filtered_items),
                'critical_threats': len(critical_items),
                'high_priority': len(high_items),
                'medium_priority': len(medium_items)
            },
            'critical_threats': critical_items[:10],  # Top 10 critical
            'high_priority_threats': high_items[:15],  # Top 15 high
            'medium_priority_threats': medium_items[:20],  # Top 20 medium
            'vendor_alerts': self._extract_vendor_alerts(filtered_items, profile),
            'compliance_updates': self._extract_compliance(filtered_items, profile),
            'all_threats': filtered_items
        }
        
        return report
    
    def _extract_vendor_alerts(self, items: List[Dict], profile: Dict) -> List[Dict]:
        """Extract items mentioning watched vendors"""
        vendors = profile.get('watch_vendors', [])
        alerts = []
        
        for item in items:
            text = f"{item.get('title', '')} {item.get('description', '')}".lower()
            for vendor in vendors:
                if vendor.lower() in text:
                    alerts.append({
                        'vendor': vendor,
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'relevance_score': item.get('relevance_score', 0)
                    })
        
        return sorted(alerts, key=lambda x: x['relevance_score'], reverse=True)[:10]
    
    def _extract_compliance(self, items: List[Dict], profile: Dict) -> List[Dict]:
        """Extract compliance-related items"""
        compliance_terms = profile.get('compliance', [])
        updates = []
        
        for item in items:
            text = f"{item.get('title', '')} {item.get('description', '')}".lower()
            for term in compliance_terms:
                if term.lower() in text:
                    updates.append({
                        'compliance_framework': term,
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'relevance_score': item.get('relevance_score', 0)
                    })
        
        return sorted(updates, key=lambda x: x['relevance_score'], reverse=True)[:10]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()


# Convenience function
def filter_for_industry(items: List[Dict], industry: str) -> List[Dict]:
    """Quick filter for specific industry"""
    filter_engine = ClientFilter()
    return filter_engine.filter_for_client(items, industry)


if __name__ == "__main__":
    # Test the filter
    logging.basicConfig(level=logging.INFO)
    
    # Sample items
    test_items = [
        {
            'title': 'Ransomware Hits Major Hospital System',
            'description': 'Healthcare ransomware attack affects Epic EHR system, PHI exposed',
            'tags': ['ransomware', 'healthcare']
        },
        {
            'title': 'New Vulnerability in Aviation Booking System',
            'description': 'Critical flaw found in Amadeus flight reservation platform',
            'tags': ['vulnerability', 'aviation']
        },
        {
            'title': 'SCADA System Exploit Targeting Power Grid',
            'description': 'ICS malware discovered targeting Siemens control systems',
            'tags': ['ICS', 'malware', 'energy']
        }
    ]
    
    filter_engine = ClientFilter()
    
    print("\nTesting industry filters:\n")
    
    for industry in ['healthcare', 'aviation', 'energy']:
        print(f"\n{'='*60}")
        print(f"Industry: {industry}")
        print('='*60)
        
        filtered = filter_engine.filter_for_client(test_items, industry)
        
        for item in filtered:
            print(f"\nScore: {item['relevance_score']}")
            print(f"Title: {item['title']}")
            print(f"Reasons: {', '.join(item['match_reasons'][:3])}")
