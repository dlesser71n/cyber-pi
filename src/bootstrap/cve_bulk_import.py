#!/usr/bin/env python3
"""
CVE Bulk Import - Bootstrap Neo4j Knowledge Graph
Download and import all CVEs from NIST NVD to establish critical mass
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import logging
from tqdm import tqdm
import gzip
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CVEBulkImporter:
    """
    Download entire NVD CVE database and prepare for Neo4j import
    
    NIST NVD provides:
    - CVE JSON feeds (all CVEs, updated daily)
    - ~200,000+ CVEs total
    - Full metadata (CVSS, CWE, CPE, references)
    """
    
    def __init__(self, data_dir: str = "data/cve_import"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # NVD JSON feed URLs (all years)
        self.base_url = "https://nvd.nist.gov/feeds/json/cve/1.1"
        
        # Years available (1999-2024+)
        current_year = datetime.now().year
        self.years = list(range(2002, current_year + 1))  # NVD structured data starts 2002
        
        self.session = None
        
    async def download_year(self, year: int) -> Path:
        """Download CVE feed for a specific year"""
        filename = f"nvdcve-1.1-{year}.json.gz"
        url = f"{self.base_url}/{filename}"
        output_path = self.data_dir / filename
        
        # Skip if already downloaded
        if output_path.exists():
            logger.info(f"✓ {year}: Already downloaded ({output_path.stat().st_size / 1024 / 1024:.1f} MB)")
            return output_path
        
        logger.info(f"⬇️  Downloading {year}...")
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    output_path.write_bytes(content)
                    size_mb = len(content) / 1024 / 1024
                    logger.info(f"✓ {year}: Downloaded ({size_mb:.1f} MB)")
                    return output_path
                else:
                    logger.error(f"✗ {year}: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"✗ {year}: {e}")
            return None
    
    async def download_all_feeds(self):
        """Download all yearly CVE feeds"""
        logger.info(f"📥 Downloading CVE feeds for {len(self.years)} years...")
        logger.info(f"Years: {self.years[0]} - {self.years[-1]}")
        
        connector = aiohttp.TCPConnector(limit=5)  # Limit concurrent downloads
        timeout = aiohttp.ClientTimeout(total=600)  # 10 minute timeout
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            self.session = session
            
            tasks = [self.download_year(year) for year in self.years]
            results = []
            
            # Download with progress bar
            for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Downloading"):
                result = await coro
                if result:
                    results.append(result)
            
            logger.info(f"✓ Downloaded {len(results)}/{len(self.years)} feeds")
            return results
    
    def extract_and_parse(self, gz_path: Path) -> Dict:
        """Extract and parse gzipped JSON feed"""
        try:
            with gzip.open(gz_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Error parsing {gz_path}: {e}")
            return None
    
    def transform_cve_to_neo4j(self, cve_item: Dict) -> Dict:
        """
        Transform NVD CVE format to Neo4j-friendly structure
        
        Creates nodes and relationships:
        - CVE node (ID, description, CVSS scores, dates)
        - Vendor nodes
        - Product nodes
        - CWE nodes (weakness types)
        - CVE -> affects -> Product
        - Product -> made_by -> Vendor
        - CVE -> has_weakness -> CWE
        """
        cve = cve_item.get('cve', {})
        cve_id = cve.get('CVE_data_meta', {}).get('ID')
        
        # Extract description
        descriptions = cve.get('description', {}).get('description_data', [])
        description = descriptions[0].get('value', '') if descriptions else ''
        
        # Extract CVSS scores (v2, v3)
        impact = cve_item.get('impact', {})
        cvss_v3 = impact.get('baseMetricV3', {}).get('cvssV3', {})
        cvss_v2 = impact.get('baseMetricV2', {}).get('cvssV2', {})
        
        # Extract CPE data (affected products/vendors)
        configurations = cve_item.get('configurations', {})
        nodes = configurations.get('nodes', [])
        
        affected_products = []
        affected_vendors = set()
        
        for node in nodes:
            for cpe_match in node.get('cpe_match', []):
                cpe23 = cpe_match.get('cpe23Uri', '')
                if cpe23:
                    # Parse CPE: cpe:2.3:a:vendor:product:version:...
                    parts = cpe23.split(':')
                    if len(parts) >= 5:
                        vendor = parts[3]
                        product = parts[4]
                        version = parts[5] if len(parts) > 5 else '*'
                        
                        affected_vendors.add(vendor)
                        affected_products.append({
                            'vendor': vendor,
                            'product': product,
                            'version': version,
                            'cpe': cpe23
                        })
        
        # Extract CWE (weakness) data
        problemtype_data = cve.get('problemtype', {}).get('problemtype_data', [])
        cwes = []
        for pt in problemtype_data:
            for desc in pt.get('description', []):
                cwe_value = desc.get('value', '')
                if cwe_value.startswith('CWE-'):
                    cwes.append(cwe_value)
        
        # Extract references
        references = []
        ref_data = cve.get('references', {}).get('reference_data', [])
        for ref in ref_data:
            references.append({
                'url': ref.get('url'),
                'name': ref.get('name'),
                'tags': ref.get('tags', [])
            })
        
        # Published and modified dates
        published = cve_item.get('publishedDate')
        modified = cve_item.get('lastModifiedDate')
        
        return {
            'cve_id': cve_id,
            'description': description,
            'published': published,
            'modified': modified,
            'cvss_v3_score': cvss_v3.get('baseScore'),
            'cvss_v3_severity': cvss_v3.get('baseSeverity'),
            'cvss_v3_vector': cvss_v3.get('vectorString'),
            'cvss_v2_score': cvss_v2.get('baseScore'),
            'cvss_v2_severity': cvss_v2.get('severity'),
            'cvss_v2_vector': cvss_v2.get('vectorString'),
            'affected_products': affected_products,
            'affected_vendors': list(affected_vendors),
            'cwes': cwes,
            'references': references,
            'reference_count': len(references),
            'exploitability': cvss_v3.get('exploitabilityScore'),
            'impact_score': cvss_v3.get('impactScore')
        }
    
    def process_all_feeds(self):
        """Process all downloaded feeds and prepare for Neo4j"""
        logger.info("📊 Processing CVE feeds...")
        
        all_cves = []
        total_cves = 0
        
        # Find all downloaded .gz files
        gz_files = sorted(self.data_dir.glob("nvdcve-1.1-*.json.gz"))
        
        if not gz_files:
            logger.error("No CVE feeds found! Run download first.")
            return None
        
        logger.info(f"Found {len(gz_files)} feed files")
        
        for gz_file in tqdm(gz_files, desc="Processing feeds"):
            logger.info(f"Processing {gz_file.name}...")
            
            # Parse feed
            feed_data = self.extract_and_parse(gz_file)
            if not feed_data:
                continue
            
            # Extract CVE items
            cve_items = feed_data.get('CVE_Items', [])
            logger.info(f"  Found {len(cve_items)} CVEs")
            
            # Transform each CVE
            for cve_item in cve_items:
                transformed = self.transform_cve_to_neo4j(cve_item)
                if transformed and transformed['cve_id']:
                    all_cves.append(transformed)
            
            total_cves += len(cve_items)
        
        logger.info(f"\n✓ Processed {total_cves} CVEs from {len(gz_files)} feeds")
        
        # Save consolidated CVE data
        output_file = self.data_dir / "all_cves_neo4j.json"
        with open(output_file, 'w') as f:
            json.dump(all_cves, f, indent=2)
        
        logger.info(f"💾 Saved {len(all_cves)} CVEs to {output_file}")
        logger.info(f"📦 File size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")
        
        # Generate statistics
        self.generate_stats(all_cves)
        
        return all_cves
    
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
        logger.info("🚀 Starting CVE Bulk Import...")
        logger.info(f"Target: {len(self.years)} years of CVE data")
        logger.info(f"Output: {self.data_dir}\n")
        
        start_time = time.time()
        
        # Step 1: Download all feeds
        await self.download_all_feeds()
        
        # Step 2: Process and transform
        cves = self.process_all_feeds()
        
        elapsed = time.time() - start_time
        logger.info(f"\n✅ Import complete in {elapsed:.1f} seconds")
        logger.info(f"📁 Data ready for Neo4j at: {self.data_dir}/all_cves_neo4j.json")
        
        return cves


async def main():
    """Main execution"""
    importer = CVEBulkImporter()
    await importer.run_full_import()


if __name__ == "__main__":
    asyncio.run(main())
