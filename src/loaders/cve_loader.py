#!/usr/bin/env python3
"""
CVE Loader - NVD API Integration
Loads CVE data from National Vulnerability Database into Neo4j

Built to Rickover standards: Production-ready, type-safe, resilient
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from models.ontology import CVE, Product, Vendor, SeverityLevel, Relationship, RelationType
from graph.neo4j_schema import Neo4jSchemaManager

logger = logging.getLogger(__name__)


class CVELoader:
    """
    Load CVE data from NVD API into Neo4j
    
    Features:
    - Async batch loading
    - Rate limiting (NVD: 5 requests/30 seconds)
    - Retry logic with exponential backoff
    - Incremental updates
    - Relationship inference
    """
    
    # NVD API Configuration
    NVD_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    RATE_LIMIT_DELAY = 6  # seconds between requests (5 req/30s = 6s delay)
    BATCH_SIZE = 2000  # NVD max results per page
    
    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        api_key: Optional[str] = None
    ):
        """
        Initialize CVE loader
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            api_key: NVD API key (optional, increases rate limit to 50 req/30s)
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.api_key = api_key
        
        self.schema_manager: Optional[Neo4jSchemaManager] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Statistics
        self.stats = {
            "cves_loaded": 0,
            "products_created": 0,
            "vendors_created": 0,
            "relationships_created": 0,
            "errors": 0
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def connect(self) -> None:
        """Establish connections"""
        # Neo4j connection
        self.schema_manager = Neo4jSchemaManager(
            self.neo4j_uri,
            self.neo4j_user,
            self.neo4j_password
        )
        await self.schema_manager.connect()
        
        # HTTP session
        headers = {}
        if self.api_key:
            headers["apiKey"] = self.api_key
        
        self.session = aiohttp.ClientSession(headers=headers)
        
        logger.info("✓ Connected to Neo4j and NVD API")
    
    async def close(self) -> None:
        """Close connections"""
        if self.schema_manager:
            await self.schema_manager.close()
        if self.session:
            await self.session.close()
        
        logger.info("✓ Closed connections")
    
    # ========================================================================
    # NVD API METHODS
    # ========================================================================
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def fetch_cves(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        start_index: int = 0
    ) -> Dict[str, Any]:
        """
        Fetch CVEs from NVD API
        
        Args:
            start_date: Filter by published date (start)
            end_date: Filter by published date (end)
            start_index: Pagination offset
            
        Returns:
            NVD API response
        """
        params = {
            "resultsPerPage": self.BATCH_SIZE,
            "startIndex": start_index
        }
        
        if start_date:
            params["pubStartDate"] = start_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        if end_date:
            params["pubEndDate"] = end_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        
        try:
            async with self.session.get(self.NVD_BASE_URL, params=params, timeout=30) as resp:
                resp.raise_for_status()
                data = await resp.json()
                
                logger.debug(f"Fetched {len(data.get('vulnerabilities', []))} CVEs from NVD")
                return data
                
        except aiohttp.ClientError as e:
            logger.error(f"NVD API request failed: {e}")
            raise
        except asyncio.TimeoutError:
            logger.error("NVD API request timed out")
            raise
    
    async def fetch_all_cves(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_cves: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all CVEs with pagination
        
        Args:
            start_date: Filter by published date (start)
            end_date: Filter by published date (end)
            max_cves: Maximum number of CVEs to fetch
            
        Returns:
            List of CVE records
        """
        all_cves = []
        start_index = 0
        
        logger.info(f"Fetching CVEs from NVD (start_date={start_date}, end_date={end_date})")
        
        while True:
            # Rate limiting
            await asyncio.sleep(self.RATE_LIMIT_DELAY)
            
            # Fetch batch
            data = await self.fetch_cves(start_date, end_date, start_index)
            
            vulnerabilities = data.get("vulnerabilities", [])
            if not vulnerabilities:
                break
            
            all_cves.extend(vulnerabilities)
            
            # Check if we've reached max
            if max_cves and len(all_cves) >= max_cves:
                all_cves = all_cves[:max_cves]
                break
            
            # Check if there are more results
            total_results = data.get("totalResults", 0)
            if start_index + len(vulnerabilities) >= total_results:
                break
            
            start_index += len(vulnerabilities)
            logger.info(f"Fetched {len(all_cves)}/{total_results} CVEs...")
        
        logger.info(f"✓ Fetched {len(all_cves)} CVEs from NVD")
        return all_cves
    
    # ========================================================================
    # DATA TRANSFORMATION
    # ========================================================================
    
    def transform_cve(self, nvd_cve: Dict[str, Any]) -> CVE:
        """
        Transform NVD CVE format to our ontology model
        
        Args:
            nvd_cve: CVE data from NVD API
            
        Returns:
            CVE entity
        """
        cve_data = nvd_cve.get("cve", {})
        
        # Extract CVE ID
        cve_id = cve_data.get("id", "")
        
        # Extract description
        descriptions = cve_data.get("descriptions", [])
        description = next(
            (d["value"] for d in descriptions if d.get("lang") == "en"),
            "No description available"
        )
        
        # Extract CVSS scores
        metrics = cve_data.get("metrics", {})
        cvss_v3_score = None
        cvss_v2_score = None
        
        # CVSS v3.x
        cvss_v3_data = (
            metrics.get("cvssMetricV31", []) or
            metrics.get("cvssMetricV30", [])
        )
        if cvss_v3_data:
            cvss_v3_score = cvss_v3_data[0].get("cvssData", {}).get("baseScore")
        
        # CVSS v2
        cvss_v2_data = metrics.get("cvssMetricV2", [])
        if cvss_v2_data:
            cvss_v2_score = cvss_v2_data[0].get("cvssData", {}).get("baseScore")
        
        # Determine severity
        score = cvss_v3_score or cvss_v2_score or 0.0
        if score >= 9.0:
            severity = SeverityLevel.CRITICAL
        elif score >= 7.0:
            severity = SeverityLevel.HIGH
        elif score >= 4.0:
            severity = SeverityLevel.MEDIUM
        elif score > 0.0:
            severity = SeverityLevel.LOW
        else:
            severity = SeverityLevel.NONE
        
        # Extract dates
        published = cve_data.get("published")
        modified = cve_data.get("lastModified")
        
        if published:
            published = datetime.fromisoformat(published.replace("Z", "+00:00"))
        if modified:
            modified = datetime.fromisoformat(modified.replace("Z", "+00:00"))
        
        # Extract affected vendors/products
        configurations = cve_data.get("configurations", [])
        affected_vendors = set()
        affected_products = set()
        
        for config in configurations:
            for node in config.get("nodes", []):
                for cpe_match in node.get("cpeMatch", []):
                    cpe = cpe_match.get("criteria", "")
                    # Parse CPE: cpe:2.3:a:vendor:product:version:...
                    parts = cpe.split(":")
                    if len(parts) >= 5:
                        vendor = parts[3]
                        product = parts[4]
                        if vendor != "*":
                            affected_vendors.add(vendor)
                        if product != "*":
                            affected_products.add(product)
        
        # Extract CWEs
        weaknesses = cve_data.get("weaknesses", [])
        cwes = []
        for weakness in weaknesses:
            for desc in weakness.get("description", []):
                cwe_id = desc.get("value", "")
                if cwe_id.startswith("CWE-") or cwe_id.startswith("NVD-CWE-"):
                    cwes.append(cwe_id)
        
        # Extract references
        references = cve_data.get("references", [])
        reference_urls = [ref.get("url") for ref in references if ref.get("url")]
        
        # Create CVE entity
        return CVE(
            cve_id=cve_id,
            description=description,
            cvss_v3_score=cvss_v3_score,
            cvss_v2_score=cvss_v2_score,
            severity=severity,
            published=published,
            modified_date=modified,
            affected_vendors=list(affected_vendors),
            affected_products=list(affected_products),
            cwes=cwes,
            references=reference_urls[:10],  # Limit to 10 references
            source="NVD",
            confidence=100  # NVD is authoritative
        )
    
    # ========================================================================
    # NEO4J LOADING
    # ========================================================================
    
    async def load_cve(self, cve: CVE) -> None:
        """
        Load CVE into Neo4j
        
        Args:
            cve: CVE entity to load
        """
        async with self.schema_manager.driver.session() as session:
            # Create CVE node
            query = """
            MERGE (c:CVE {cve_id: $cve_id})
            SET c.id = $id,
                c.type = $type,
                c.description = $description,
                c.cvss_v3_score = $cvss_v3_score,
                c.cvss_v2_score = $cvss_v2_score,
                c.severity = $severity,
                c.published = $published,
                c.modified = $modified,
                c.cwes = $cwes,
                c.references = $references,
                c.source = $source,
                c.confidence = $confidence,
                c.created = $created,
                c.tags = $tags
            RETURN c
            """
            
            await session.run(query, {
                "cve_id": cve.cve_id,
                "id": cve.id,
                "type": cve.type,
                "description": cve.description,
                "cvss_v3_score": cve.cvss_v3_score,
                "cvss_v2_score": cve.cvss_v2_score,
                "severity": cve.severity.value,
                "published": cve.published.isoformat() if cve.published else None,
                "modified": cve.modified_date.isoformat() if cve.modified_date else None,
                "cwes": cve.cwes,
                "references": cve.references,
                "source": cve.source,
                "confidence": cve.confidence,
                "created": cve.created.isoformat(),
                "tags": cve.tags
            })
            
            self.stats["cves_loaded"] += 1
    
    async def load_vendor_product_relationships(self, cve: CVE) -> None:
        """
        Create vendor/product nodes and relationships
        
        Args:
            cve: CVE entity with affected vendors/products
        """
        async with self.schema_manager.driver.session() as session:
            # Create vendors
            for vendor_name in cve.affected_vendors:
                query = """
                MERGE (v:Vendor {name: $name})
                ON CREATE SET v.id = randomUUID(),
                              v.type = 'vendor',
                              v.created = datetime(),
                              v.modified = datetime()
                RETURN v
                """
                await session.run(query, {"name": vendor_name.lower()})
                self.stats["vendors_created"] += 1
            
            # Create products and link to vendors
            for product_name in cve.affected_products:
                # Try to infer vendor from product name or CVE data
                vendor_name = cve.affected_vendors[0] if cve.affected_vendors else "unknown"
                
                query = """
                MERGE (p:Product {name: $product_name})
                ON CREATE SET p.id = randomUUID(),
                              p.type = 'product',
                              p.vendor_id = $vendor_name,
                              p.created = datetime(),
                              p.modified = datetime()
                
                WITH p
                MATCH (v:Vendor {name: $vendor_name})
                MERGE (p)-[:MANUFACTURED_BY]->(v)
                
                WITH p
                MATCH (c:CVE {cve_id: $cve_id})
                MERGE (c)-[:AFFECTS]->(p)
                
                RETURN p
                """
                
                await session.run(query, {
                    "product_name": product_name.lower(),
                    "vendor_name": vendor_name.lower(),
                    "cve_id": cve.cve_id
                })
                
                self.stats["products_created"] += 1
                self.stats["relationships_created"] += 2  # MANUFACTURED_BY + AFFECTS
    
    # ========================================================================
    # BATCH LOADING
    # ========================================================================
    
    async def load_cves_batch(self, cves: List[CVE]) -> None:
        """
        Load multiple CVEs in batch
        
        Args:
            cves: List of CVE entities
        """
        logger.info(f"Loading {len(cves)} CVEs into Neo4j...")
        
        for i, cve in enumerate(cves, 1):
            try:
                await self.load_cve(cve)
                await self.load_vendor_product_relationships(cve)
                
                if i % 100 == 0:
                    logger.info(f"Loaded {i}/{len(cves)} CVEs...")
                    
            except Exception as e:
                logger.error(f"Failed to load CVE {cve.cve_id}: {e}")
                self.stats["errors"] += 1
        
        logger.info(f"✓ Loaded {len(cves)} CVEs into Neo4j")
    
    # ========================================================================
    # HIGH-LEVEL OPERATIONS
    # ========================================================================
    
    async def load_recent_cves(self, days: int = 30, max_cves: Optional[int] = None) -> None:
        """
        Load recent CVEs from NVD
        
        Args:
            days: Number of days to look back
            max_cves: Maximum number of CVEs to load
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        logger.info(f"Loading CVEs from last {days} days...")
        
        # Fetch from NVD
        nvd_cves = await self.fetch_all_cves(start_date, end_date, max_cves)
        
        # Transform to our model
        cves = [self.transform_cve(nvd_cve) for nvd_cve in nvd_cves]
        
        # Load into Neo4j
        await self.load_cves_batch(cves)
        
        logger.info(f"✓ Loaded {len(cves)} recent CVEs")
    
    async def load_all_cves(self, max_cves: Optional[int] = None) -> None:
        """
        Load all CVEs from NVD (WARNING: This is a LOT of data)
        
        Args:
            max_cves: Maximum number of CVEs to load
        """
        logger.warning("Loading ALL CVEs from NVD - this will take hours!")
        
        # Fetch from NVD (no date filter)
        nvd_cves = await self.fetch_all_cves(max_cves=max_cves)
        
        # Transform to our model
        cves = [self.transform_cve(nvd_cve) for nvd_cve in nvd_cves]
        
        # Load into Neo4j
        await self.load_cves_batch(cves)
        
        logger.info(f"✓ Loaded {len(cves)} CVEs")
    
    def print_stats(self) -> None:
        """Print loading statistics"""
        print("\n" + "="*60)
        print("CVE Loader Statistics")
        print("="*60)
        print(f"CVEs loaded:          {self.stats['cves_loaded']:,}")
        print(f"Vendors created:      {self.stats['vendors_created']:,}")
        print(f"Products created:     {self.stats['products_created']:,}")
        print(f"Relationships:        {self.stats['relationships_created']:,}")
        print(f"Errors:               {self.stats['errors']:,}")
        print("="*60)


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """CLI for CVE loader"""
    import os
    import sys
    
    # Get credentials from environment
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    nvd_api_key = os.getenv("NVD_API_KEY")  # Optional
    
    if not neo4j_password:
        print("❌ NEO4J_PASSWORD environment variable not set")
        sys.exit(1)
    
    # Parse command
    command = sys.argv[1] if len(sys.argv) > 1 else "recent"
    
    async with CVELoader(neo4j_uri, neo4j_user, neo4j_password, nvd_api_key) as loader:
        if command == "recent":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            await loader.load_recent_cves(days=days)
        
        elif command == "all":
            max_cves = int(sys.argv[2]) if len(sys.argv) > 2 else None
            await loader.load_all_cves(max_cves=max_cves)
        
        elif command == "test":
            # Load just 10 CVEs for testing
            await loader.load_recent_cves(days=7, max_cves=10)
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands:")
            print("  recent [days]  - Load recent CVEs (default: 30 days)")
            print("  all [max]      - Load all CVEs (optional max limit)")
            print("  test           - Load 10 CVEs for testing")
            sys.exit(1)
        
        # Print statistics
        loader.print_stats()


if __name__ == "__main__":
    asyncio.run(main())
