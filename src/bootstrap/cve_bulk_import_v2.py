#!/usr/bin/env python3
"""
CVE Bulk Import V2 - Using NIST NVD API 2.0
Download and import all CVEs from NIST NVD API 2.0
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import logging
from tqdm import tqdm
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CVEBulkImporterV2:
    """
    Download entire NVD CVE database using NVD API 2.0
    
    NVD API 2.0:
    - REST API with pagination
    - Rate limit: 50 requests per 30 seconds (without API key)
    - Rate limit: 50 requests per 30 seconds (with API key)
    - Max results per page: 2000
    """
    
    def __init__(self, data_dir: str = "data/cve_import", api_key: str = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # NVD API 2.0 endpoint
        self.base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        
        # API key (optional, increases rate limit)
        self.api_key = api_key
        
        # Rate limiting
        self.requests_per_30s = 5  # Conservative to avoid 403
        self.request_delay = 30.0 / self.requests_per_30s  # 6 seconds between requests
        
        self.session = None
        
    async def fetch_cves_page(self, start_index: int = 0, results_per_page: int = 2000) -> Dict:
        """Fetch a single page of CVEs from NVD API"""
        
        params = {
            'startIndex': start_index,
            'resultsPerPage': results_per_page
        }
        
        headers = {}
        if self.api_key:
            headers['apiKey'] = self.api_key
        
        try:
            await asyncio.sleep(self.request_delay)  # Rate limiting
            
            async with self.session.get(self.base_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"HTTP {response.status} at index {start_index}")
                    return None
        except Exception as e:
            logger.error(f"Error at index {start_index}: {e}")
            return None
    
    async def download_all_cves(self):
        """Download all CVEs using pagination"""
        logger.info("📥 Downloading all CVEs from NVD API 2.0...")
        logger.info(f"Rate limit: 1 request every {self.request_delay:.1f} seconds")
        
        all_cves = []
        start_index = 0
        results_per_page = 2000
        total_results = None
        
        connector = aiohttp.TCPConnector(limit=1)  # Single connection
        timeout = aiohttp.ClientTimeout(total=60)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            self.session = session
            
            # First request to get total count
            logger.info("🔍 Getting total CVE count...")
            first_page = await self.fetch_cves_page(0, results_per_page)
            
            if not first_page:
                logger.error("Failed to fetch first page")
                return []
            
            total_results = first_page.get('totalResults', 0)
            logger.info(f"📊 Total CVEs available: {total_results:,}")
            
            # Add first page vulnerabilities
            vulnerabilities = first_page.get('vulnerabilities', [])
            all_cves.extend(vulnerabilities)
            logger.info(f"✓ Downloaded {len(all_cves):,}/{total_results:,} CVEs")
            
            # Calculate remaining pages
            remaining = total_results - len(all_cves)
            num_pages = (remaining + results_per_page - 1) // results_per_page
            
            logger.info(f"📄 Fetching {num_pages} more pages...")
            
            estimated_time = num_pages * self.request_delay / 60
            logger.info(f"⏱️  Estimated time: {estimated_time:.1f} minutes")
            
            # Fetch remaining pages with progress bar
            for page_num in tqdm(range(1, num_pages + 1), desc="Downloading pages"):
                start_index = page_num * results_per_page
                
                page_data = await self.fetch_cves_page(start_index, results_per_page)
                
                if page_data:
                    vulnerabilities = page_data.get('vulnerabilities', [])
                    all_cves.extend(vulnerabilities)
                    
                    if page_num % 10 == 0:  # Progress update every 10 pages
                        logger.info(f"Progress: {len(all_cves):,}/{total_results:,} CVEs downloaded")
                else:
                    logger.warning(f"Failed to fetch page at index {start_index}")
        
        logger.info(f"✓ Downloaded {len(all_cves):,} CVEs total")
        return all_cves
    
    def transform_cve_to_neo4j(self, vuln_item: Dict) -> Dict:
        """Transform NVD API 2.0 CVE format to Neo4j-friendly structure"""
        
        cve_data = vuln_item.get('cve', {})
        cve_id = cve_data.get('id')
        
        # Extract descriptions
        descriptions = cve_data.get('descriptions', [])
        description = next((d['value'] for d in descriptions if d['lang'] == 'en'), '')
        
        # Extract CVSS metrics
        metrics = cve_data.get('metrics', {})
        
        # CVSS v3.1 (preferred)
        cvss_v31 = metrics.get('cvssMetricV31', [])
        cvss_v3_data = cvss_v31[0]['cvssData'] if cvss_v31 else {}
        
        # CVSS v3.0 (fallback)
        if not cvss_v3_data:
            cvss_v30 = metrics.get('cvssMetricV30', [])
            cvss_v3_data = cvss_v30[0]['cvssData'] if cvss_v30 else {}
        
        # CVSS v2 (legacy)
        cvss_v2 = metrics.get('cvssMetricV2', [])
        cvss_v2_data = cvss_v2[0]['cvssData'] if cvss_v2 else {}
        
        # Extract CPE configurations (affected products)
        configurations = cve_data.get('configurations', [])
        affected_products = []
        affected_vendors = set()
        
        for config in configurations:
            for node in config.get('nodes', []):
                for cpe_match in node.get('cpeMatch', []):
                    if cpe_match.get('vulnerable', True):
                        criteria = cpe_match.get('criteria', '')
                        if criteria.startswith('cpe:2.3:'):
                            parts = criteria.split(':')
                            if len(parts) >= 5:
                                vendor = parts[3]
                                product = parts[4]
                                version = parts[5] if len(parts) > 5 else '*'
                                
                                affected_vendors.add(vendor)
                                affected_products.append({
                                    'vendor': vendor,
                                    'product': product,
                                    'version': version,
                                    'cpe': criteria
                                })
        
        # Extract CWE (weakness) data
        weaknesses = cve_data.get('weaknesses', [])
        cwes = []
        for weakness in weaknesses:
            for desc in weakness.get('description', []):
                cwe_value = desc.get('value', '')
                if cwe_value.startswith('CWE-'):
                    cwes.append(cwe_value)
        
        # Extract references
        references = []
        ref_list = cve_data.get('references', [])
        for ref in ref_list:
            references.append({
                'url': ref.get('url'),
                'source': ref.get('source'),
                'tags': ref.get('tags', [])
            })
        
        # Dates
        published = cve_data.get('published')
        modified = cve_data.get('lastModified')
        
        return {
            'cve_id': cve_id,
            'description': description,
            'published': published,
            'modified': modified,
            'cvss_v3_score': cvss_v3_data.get('baseScore'),
            'cvss_v3_severity': cvss_v3_data.get('baseSeverity'),
            'cvss_v3_vector': cvss_v3_data.get('vectorString'),
            'cvss_v2_score': cvss_v2_data.get('baseScore'),
            'cvss_v2_severity': cvss_v2_data.get('baseSeverity'),
            'cvss_v2_vector': cvss_v2_data.get('vectorString'),
            'affected_products': affected_products,
            'affected_vendors': list(affected_vendors),
            'cwes': cwes,
            'references': references,
            'reference_count': len(references),
            'exploitability': cvss_v31[0].get('exploitabilityScore') if cvss_v31 else None,
            'impact_score': cvss_v31[0].get('impactScore') if cvss_v31 else None
        }
    
    def process_and_save(self, cves: List[Dict]):
        """Process CVEs and save to file"""
        logger.info("📊 Processing CVEs...")
        
        transformed_cves = []
        for vuln_item in tqdm(cves, desc="Transforming"):
            try:
                transformed = self.transform_cve_to_neo4j(vuln_item)
                if transformed and transformed['cve_id']:
                    transformed_cves.append(transformed)
            except Exception as e:
                logger.error(f"Error transforming CVE: {e}")
        
        logger.info(f"✓ Processed {len(transformed_cves):,} CVEs")
        
        # Save to file
        output_file = self.data_dir / "all_cves_neo4j.json"
        with open(output_file, 'w') as f:
            json.dump(transformed_cves, f, indent=2)
        
        logger.info(f"💾 Saved to {output_file}")
        logger.info(f"📦 File size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")
        
        # Generate statistics
        self.generate_stats(transformed_cves)
        
        return transformed_cves
    
    def generate_stats(self, cves: List[Dict]):
        """Generate statistics about the CVE dataset"""
        logger.info("\n" + "="*80)
        logger.info("📊 CVE DATASET STATISTICS")
        logger.info("="*80)
        
        total = len(cves)
        logger.info(f"Total CVEs: {total:,}")
        
        # CVSS distribution
        critical = sum(1 for c in cves if c.get('cvss_v3_score', 0) >= 9.0)
        high = sum(1 for c in cves if 7.0 <= c.get('cvss_v3_score', 0) < 9.0)
        medium = sum(1 for c in cves if 4.0 <= c.get('cvss_v3_score', 0) < 7.0)
        low = sum(1 for c in cves if 0 < c.get('cvss_v3_score', 0) < 4.0)
        
        logger.info(f"\nCVSS v3 Distribution:")
        logger.info(f"  Critical (9.0-10.0): {critical:,} ({critical/total*100:.1f}%)")
        logger.info(f"  High (7.0-8.9):      {high:,} ({high/total*100:.1f}%)")
        logger.info(f"  Medium (4.0-6.9):    {medium:,} ({medium/total*100:.1f}%)")
        logger.info(f"  Low (0.1-3.9):       {low:,} ({low/total*100:.1f}%)")
        
        # Vendor analysis
        all_vendors = set()
        for cve in cves:
            all_vendors.update(cve.get('affected_vendors', []))
        
        logger.info(f"\nAffected Vendors: {len(all_vendors):,}")
        
        # Products analysis
        total_products = sum(len(cve.get('affected_products', [])) for cve in cves)
        logger.info(f"Affected Products: {total_products:,}")
        
        # CWE analysis
        all_cwes = set()
        for cve in cves:
            all_cwes.update(cve.get('cwes', []))
        
        logger.info(f"Unique CWEs: {len(all_cwes):,}")
        
        # References
        total_refs = sum(cve.get('reference_count', 0) for cve in cves)
        logger.info(f"Total References: {total_refs:,}")
        
        logger.info("="*80 + "\n")
    
    async def run_full_import(self):
        """Execute full CVE import pipeline"""
        logger.info("🚀 Starting CVE Bulk Import (NVD API 2.0)...")
        logger.info(f"Output: {self.data_dir}\n")
        
        start_time = time.time()
        
        # Step 1: Download all CVEs
        cves = await self.download_all_cves()
        
        if not cves:
            logger.error("❌ No CVEs downloaded")
            return None
        
        # Step 2: Process and transform
        transformed = self.process_and_save(cves)
        
        elapsed = time.time() - start_time
        logger.info(f"\n✅ Import complete in {elapsed/60:.1f} minutes")
        logger.info(f"📁 Data ready for Neo4j at: {self.data_dir}/all_cves_neo4j.json")
        
        return transformed


async def main():
    """Main execution"""
    # Optional: Set API key for higher rate limit
    # api_key = "your-nvd-api-key-here"
    api_key = None
    
    importer = CVEBulkImporterV2(api_key=api_key)
    await importer.run_full_import()


if __name__ == "__main__":
    asyncio.run(main())
