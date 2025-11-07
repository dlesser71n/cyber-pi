"""
cyber-pi Public API Collector
Collects from public cybersecurity APIs (no authentication required)
Includes: NIST NVD, MITRE ATT&CK, CVE Details, AlienVault OTX
"""

import asyncio
import aiohttp
import yaml
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
import json

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


class PublicAPICollector:
    """
    Collects threat intelligence from public APIs
    No authentication required for these sources
    """
    
    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.sources = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.collected_items = []
        self.stats = {
            'total_apis': 0,
            'successful_apis': 0,
            'failed_apis': 0,
            'total_items': 0,
            'start_time': None,
            'end_time': None
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),  # APIs can be slow
            headers={'User-Agent': 'cyber-pi/1.0 (Enterprise Threat Intelligence)'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def load_sources(self, categories: List[str] = None) -> None:
        """
        Load API sources from configuration
        
        Args:
            categories: List of categories to load (None = all)
        """
        config_path = Path(__file__).parent.parent.parent / 'config' / 'sources.yaml'
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Loaded configuration from {config_path}")
            
            # Extract API sources from all categories
            for category_name, category_data in config.items():
                if category_name == 'collection_settings':
                    continue
                    
                if categories and category_name not in categories:
                    continue
                
                if not isinstance(category_data, dict) or 'sources' not in category_data:
                    continue
                
                for source in category_data['sources']:
                    if source.get('type') == 'api':
                        self.sources.append({
                            'name': source['name'],
                            'url': source['url'],
                            'category': category_name,
                            'credibility': source.get('credibility', 0.7),
                            'tags': source.get('tags', []),
                            'priority': category_data.get('priority', 'medium')
                        })
            
            self.stats['total_apis'] = len(self.sources)
            logger.info(f"Loaded {len(self.sources)} API sources")
            
        except Exception as e:
            logger.error(f"Failed to load sources: {e}")
            raise
    
    async def fetch_nist_nvd(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch recent CVEs from NIST National Vulnerability Database
        Public API, no authentication required
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of CVE items
        """
        try:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days_back)
            
            # NIST NVD API v2.0
            url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
            params = {
                'pubStartDate': start_date.strftime('%Y-%m-%dT%H:%M:%S.000'),
                'pubEndDate': end_date.strftime('%Y-%m-%dT%H:%M:%S.000'),
                'resultsPerPage': 100
            }
            
            logger.debug(f"Fetching NIST NVD CVEs from {start_date.date()} to {end_date.date()}")
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"NIST NVD returned status {response.status}")
                    return []
                
                data = await response.json()
                
                items = []
                for vuln in data.get('vulnerabilities', []):
                    cve = vuln.get('cve', {})
                    cve_id = cve.get('id', 'Unknown')
                    
                    # Extract description
                    descriptions = cve.get('descriptions', [])
                    description = next((d['value'] for d in descriptions if d.get('lang') == 'en'), '')
                    
                    # Extract CVSS scores
                    metrics = cve.get('metrics', {})
                    cvss_v3 = metrics.get('cvssMetricV31', [{}])[0] if metrics.get('cvssMetricV31') else {}
                    cvss_score = cvss_v3.get('cvssData', {}).get('baseScore', 0.0)
                    severity = cvss_v3.get('cvssData', {}).get('baseSeverity', 'UNKNOWN')
                    
                    # Extract references
                    references = [ref.get('url') for ref in cve.get('references', [])]
                    
                    item = {
                        'id': hashlib.sha256(cve_id.encode()).hexdigest()[:16],
                        'title': f"{cve_id}: {description[:100]}...",
                        'cve_id': cve_id,
                        'description': description,
                        'cvss_score': cvss_score,
                        'severity': severity,
                        'published': cve.get('published', ''),
                        'last_modified': cve.get('lastModified', ''),
                        'references': references,
                        'collected': datetime.now(timezone.utc).isoformat(),
                        'source': {
                            'name': 'NIST NVD',
                            'type': 'api',
                            'credibility': 0.95
                        },
                        'tags': ['cve', 'vulnerability', 'nist']
                    }
                    items.append(item)
                
                logger.info(f"✓ NIST NVD: {len(items)} CVEs")
                return items
                
        except Exception as e:
            logger.error(f"Error fetching NIST NVD: {e}")
            return []
    
    async def fetch_mitre_attack(self) -> List[Dict[str, Any]]:
        """
        Fetch MITRE ATT&CK techniques
        Public data, no authentication required
        
        Returns:
            List of ATT&CK technique items
        """
        try:
            # MITRE ATT&CK STIX data (public)
            url = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
            
            logger.debug("Fetching MITRE ATT&CK techniques")
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"MITRE ATT&CK returned status {response.status}")
                    return []
                
                data = await response.json()
                
                items = []
                for obj in data.get('objects', []):
                    if obj.get('type') == 'attack-pattern':
                        technique_id = obj.get('external_references', [{}])[0].get('external_id', 'Unknown')
                        name = obj.get('name', 'Unknown')
                        description = obj.get('description', '')
                        
                        # Extract tactics
                        kill_chain_phases = obj.get('kill_chain_phases', [])
                        tactics = [phase.get('phase_name') for phase in kill_chain_phases]
                        
                        item = {
                            'id': hashlib.sha256(technique_id.encode()).hexdigest()[:16],
                            'title': f"{technique_id}: {name}",
                            'technique_id': technique_id,
                            'name': name,
                            'description': description,
                            'tactics': tactics,
                            'created': obj.get('created', ''),
                            'modified': obj.get('modified', ''),
                            'collected': datetime.now(timezone.utc).isoformat(),
                            'source': {
                                'name': 'MITRE ATT&CK',
                                'type': 'api',
                                'credibility': 0.95
                            },
                            'tags': ['mitre', 'attack', 'technique', 'ttp']
                        }
                        items.append(item)
                
                logger.info(f"✓ MITRE ATT&CK: {len(items)} techniques")
                return items
                
        except Exception as e:
            logger.error(f"Error fetching MITRE ATT&CK: {e}")
            return []
    
    async def fetch_cve_details_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch recent CVEs from CVE Details
        Public data, no authentication required
        
        Args:
            limit: Maximum number of CVEs to fetch
            
        Returns:
            List of CVE items
        """
        try:
            # CVE Details RSS feed (public)
            url = "https://www.cvedetails.com/json-feed.php"
            params = {
                'numrows': limit,
                'vendor_id': 0,
                'product_id': 0,
                'version_id': 0,
                'hasexp': 0,
                'opec': 0,
                'opov': 0,
                'opcsrf': 0,
                'opfileinc': 0,
                'opgpriv': 0,
                'opsqli': 0,
                'opxss': 0,
                'opdirt': 0,
                'opmemc': 0,
                'ophttprs': 0,
                'opbyp': 0,
                'opginf': 0,
                'opdos': 0,
                'orderby': 3,
                'cvssscoremin': 0
            }
            
            logger.debug(f"Fetching CVE Details (limit: {limit})")
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"CVE Details returned status {response.status}")
                    return []
                
                data = await response.json()
                
                items = []
                for cve in data:
                    cve_id = cve.get('cve_id', 'Unknown')
                    
                    item = {
                        'id': hashlib.sha256(cve_id.encode()).hexdigest()[:16],
                        'title': f"{cve_id}: {cve.get('summary', '')[:100]}...",
                        'cve_id': cve_id,
                        'summary': cve.get('summary', ''),
                        'cvss_score': float(cve.get('cvss_score', 0)),
                        'published_date': cve.get('publish_date', ''),
                        'update_date': cve.get('update_date', ''),
                        'collected': datetime.now(timezone.utc).isoformat(),
                        'source': {
                            'name': 'CVE Details',
                            'type': 'api',
                            'credibility': 0.85
                        },
                        'tags': ['cve', 'vulnerability']
                    }
                    items.append(item)
                
                logger.info(f"✓ CVE Details: {len(items)} CVEs")
                return items
                
        except Exception as e:
            logger.error(f"Error fetching CVE Details: {e}")
            return []
    
    async def collect_all(self) -> List[Dict[str, Any]]:
        """
        Collect from all available public APIs
        
        Returns:
            List of all collected items
        """
        self.stats['start_time'] = datetime.now(timezone.utc)
        
        logger.info("Starting public API collection")
        
        # Collect from all APIs in parallel
        tasks = [
            self.fetch_nist_nvd(days_back=7),
            self.fetch_mitre_attack(),
            self.fetch_cve_details_recent(limit=50)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all results
        all_items = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"API task {i} failed: {result}")
                self.stats['failed_apis'] += 1
            elif result:
                all_items.extend(result)
                self.stats['successful_apis'] += 1
            else:
                self.stats['failed_apis'] += 1
        
        self.stats['total_items'] = len(all_items)
        self.stats['end_time'] = datetime.now(timezone.utc)
        
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        logger.info(f"API collection complete in {duration:.2f}s")
        logger.info(f"  Successful APIs: {self.stats['successful_apis']}/3")
        logger.info(f"  Total items: {self.stats['total_items']}")
        
        self.collected_items = all_items
        return all_items
    
    def save_to_json(self, filepath: str = None) -> str:
        """
        Save collected items to JSON file
        
        Args:
            filepath: Output file path
            
        Returns:
            Path to saved file
        """
        if not filepath:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            filepath = f"{settings.raw_data_dir}/api_{timestamp}.json"
        
        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare data
        data = {
            'metadata': {
                'collected_at': datetime.now(timezone.utc).isoformat(),
                'total_items': len(self.collected_items),
                'stats': self.stats
            },
            'items': self.collected_items
        }
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Saved {len(self.collected_items)} items to {filepath}")
        return filepath
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        return self.stats.copy()


async def main():
    """
    Main function for testing API collector
    """
    logger.info("🚀 cyber-pi Public API Collector")
    logger.info("=" * 60)
    
    async with PublicAPICollector(max_workers=8) as collector:
        # Collect from all public APIs
        logger.info("Starting collection from public APIs...")
        items = await collector.collect_all()
        
        # Save results
        if items:
            filepath = collector.save_to_json()
            logger.info(f"✓ Results saved to: {filepath}")
        
        # Display stats
        stats = collector.get_stats()
        logger.info("\n" + "=" * 60)
        logger.info("COLLECTION STATISTICS")
        logger.info("=" * 60)
        logger.info(f"APIs Queried: 3")
        logger.info(f"Successful: {stats['successful_apis']}")
        logger.info(f"Failed: {stats['failed_apis']}")
        logger.info(f"Total Items: {stats['total_items']}")
        
        if stats['start_time'] and stats['end_time']:
            duration = (stats['end_time'] - stats['start_time']).total_seconds()
            logger.info(f"Duration: {duration:.2f}s")
        
        # Show sample items by type
        if items:
            logger.info("\n" + "=" * 60)
            logger.info("SAMPLE ITEMS BY SOURCE")
            logger.info("=" * 60)
            
            # Group by source
            by_source = {}
            for item in items:
                source_name = item['source']['name']
                if source_name not in by_source:
                    by_source[source_name] = []
                by_source[source_name].append(item)
            
            for source_name, source_items in by_source.items():
                logger.info(f"\n{source_name}: {len(source_items)} items")
                for item in source_items[:2]:  # Show first 2 from each source
                    logger.info(f"  - {item['title'][:80]}")


if __name__ == "__main__":
    asyncio.run(main())
