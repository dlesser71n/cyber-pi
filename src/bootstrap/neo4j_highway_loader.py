#!/usr/bin/env python3
"""
Neo4j Highway Loader - Redis to Neo4j Knowledge Graph

Loads CVEs from Redis Highway into Neo4j using Pydantic schema.
Maintains data consistency through single source of truth (Pydantic models).

Architecture:
  Redis (fast queries) → Pydantic (validation) → Neo4j (graph analytics)
  
Enterprise Standard: Production-grade data quality, schema consistency
"""

import sys
import os
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

import redis
from neo4j import GraphDatabase
from tqdm import tqdm
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.cve_models import CVE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Neo4jHighwayLoader:
    """
    Load CVEs from Redis Highway into Neo4j Knowledge Graph
    
    PHASE 1: SIMPLE CVE GRAPH
    
    Schema (from existing neo4j_cve_loader.py):
      (CVE)-[:AFFECTS]->(Product)-[:MADE_BY]->(Vendor)
      (CVE)-[:HAS_WEAKNESS]->(CWE)
    
    Source: Redis Highway (validated, indexed, embedded)
    Models: Pydantic CVE (single source of truth)
    """
    
    def __init__(
        self,
        redis_host: str = "10.152.183.253",
        redis_port: int = 6379,
        redis_password: Optional[str] = None,
        neo4j_uri: str = "bolt://10.152.183.169:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: Optional[str] = None
    ):
        """Initialize connections to Redis and Neo4j"""
        logger.info("="*80)
        logger.info("🚀 NEO4J HIGHWAY LOADER - REDIS TO NEO4J")
        logger.info("="*80)
        
        # Get passwords from environment variables
        redis_password = redis_password or os.getenv('REDIS_PASSWORD')
        if not redis_password:
            raise ValueError("REDIS_PASSWORD must be set in environment or passed as parameter")
        
        neo4j_password = neo4j_password or os.getenv('NEO4J_PASSWORD')
        if not neo4j_password:
            raise ValueError("NEO4J_PASSWORD must be set in environment or passed as parameter")
        
        # Redis connection (source)
        logger.info(f"📡 Connecting to Redis: {redis_host}:{redis_port}")
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True
        )
        self.redis.ping()
        logger.info("✅ Redis connection established")
        
        # Neo4j connection (destination)
        logger.info(f"📡 Connecting to Neo4j: {neo4j_uri}")
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.driver.verify_connectivity()
        logger.info("✅ Neo4j connection established")
        
        # Stats
        self.stats = {
            'cves_loaded': 0,
            'vendors_loaded': 0,
            'products_loaded': 0,
            'cwes_loaded': 0,
            'relationships_created': 0
        }
        
    def close(self):
        """Close connections"""
        self.driver.close()
        self.redis.close()
    
    def create_schema(self):
        """Create Neo4j schema: indexes and constraints"""
        logger.info("\n🏗️  Creating Neo4j schema...")
        
        with self.driver.session() as session:
            # Constraints (uniqueness)
            try:
                session.run("CREATE CONSTRAINT cve_id_unique IF NOT EXISTS FOR (c:CVE) REQUIRE c.id IS UNIQUE")
                session.run("CREATE CONSTRAINT vendor_name_unique IF NOT EXISTS FOR (v:Vendor) REQUIRE v.name IS UNIQUE")
                session.run("CREATE CONSTRAINT cwe_id_unique IF NOT EXISTS FOR (w:CWE) REQUIRE w.id IS UNIQUE")
                session.run("CREATE CONSTRAINT product_name_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.name IS UNIQUE")
                logger.info("  ✅ Constraints created")
            except Exception as e:
                logger.warning(f"  ⚠️  Constraint warning: {e}")
            
            # Indexes (performance)
            session.run("CREATE INDEX cve_severity_idx IF NOT EXISTS FOR (c:CVE) ON (c.severity)")
            session.run("CREATE INDEX cve_cvss_idx IF NOT EXISTS FOR (c:CVE) ON (c.cvss_score)")
            session.run("CREATE INDEX cve_published_idx IF NOT EXISTS FOR (c:CVE) ON (c.published)")
            logger.info("  ✅ Indexes created")
    
    def load_cves_from_redis(self) -> List[CVE]:
        """Load all CVEs from Redis and reconstruct as Pydantic objects"""
        logger.info("\n📚 Loading CVEs from Redis...")
        
        # Get all CVE keys (exclude embedding keys)
        cve_keys = [
            k for k in self.redis.keys("cve:CVE-*")
            if not k.endswith(":embedding")
        ]
        
        logger.info(f"  Found {len(cve_keys):,} CVE keys in Redis")
        
        cves = []
        failed = 0
        
        for key in tqdm(cve_keys, desc="  Loading from Redis"):
            try:
                # Get hash data from Redis
                cve_data = self.redis.hgetall(key)
                
                # Convert Redis strings back to proper Pydantic format
                cve_dict = self._redis_to_pydantic_dict(cve_data)
                
                # Create Pydantic CVE (validation happens here)
                cve = CVE(**cve_dict)
                cves.append(cve)
                
            except Exception as e:
                failed += 1
                if failed <= 5:  # Log first few failures
                    logger.warning(f"  ⚠️  Failed to load {key}: {e}")
        
        if failed > 0:
            logger.warning(f"  ⚠️  {failed:,} CVEs failed to load")
        
        logger.info(f"  ✅ Loaded {len(cves):,} CVEs successfully")
        return cves
    
    def _redis_to_pydantic_dict(self, redis_data: Dict[str, str]) -> Dict:
        """Convert Redis hash data to Pydantic-compatible dict"""
        # Redis stores everything as strings, need to convert types
        result = {}
        
        for key, value in redis_data.items():
            if key in ['cvss_v3', 'cvss_v2']:
                # Convert to float scores
                result[f'{key}_score'] = float(value) if value and value != '0' else None
            elif key in ['vendors', 'products', 'cwes']:
                # Convert comma-separated to list
                field_name = f'affected_{key}' if key != 'cwes' else key
                result[field_name] = [v.strip() for v in value.split(',') if v.strip()]
            elif key in ['references']:
                # Convert to list
                result[key] = [r.strip() for r in value.split(',') if r.strip()]
            elif key == 'id':
                # Rename to cve_id for Pydantic
                result['cve_id'] = value
            else:
                result[key] = value
        
        return result
    
    def load_cve_batch_to_neo4j(self, cves: List[CVE]):
        """Load batch of CVEs using Pydantic to_neo4j_node() method"""
        with self.driver.session() as session:
            # Convert each CVE using built-in Pydantic method
            nodes = [cve.to_neo4j_node() for cve in cves]
            
            # Batch insert
            session.run("""
                UNWIND $nodes AS node
                MERGE (c:CVE {id: node.id})
                SET c = node
            """, nodes=nodes)
            
            self.stats['cves_loaded'] += len(cves)
    
    def load_vendors_from_cves(self, cves: List[CVE]):
        """Extract and load unique vendors"""
        logger.info("\n🏢 Loading Vendor nodes...")
        
        # Collect unique vendors using Pydantic property
        vendors = set()
        for cve in cves:
            vendors.update(cve.vendor_names)
        
        logger.info(f"  Found {len(vendors):,} unique vendors")
        
        # Batch load
        with self.driver.session() as session:
            vendor_list = [{'name': v} for v in vendors]
            session.run("""
                UNWIND $vendors AS vendor
                MERGE (v:Vendor {name: vendor.name})
            """, vendors=vendor_list)
        
        self.stats['vendors_loaded'] = len(vendors)
        logger.info(f"  ✅ {len(vendors):,} vendors loaded")
    
    def load_products_from_cves(self, cves: List[CVE]):
        """Extract and load unique products"""
        logger.info("\n📦 Loading Product nodes...")
        
        # Collect unique products using Pydantic property
        products = set()
        for cve in cves:
            products.update(cve.product_names)
        
        logger.info(f"  Found {len(products):,} unique products")
        
        # Batch load
        with self.driver.session() as session:
            product_list = [{'name': p} for p in products]
            session.run("""
                UNWIND $products AS product
                MERGE (p:Product {name: product.name})
            """, products=product_list)
        
        self.stats['products_loaded'] = len(products)
        logger.info(f"  ✅ {len(products):,} products loaded")
    
    def load_cwes_from_cves(self, cves: List[CVE]):
        """Extract and load unique CWEs"""
        logger.info("\n🔍 Loading CWE nodes...")
        
        # Collect unique CWEs
        cwes = set()
        for cve in cves:
            cwes.update(cve.cwes)
        
        logger.info(f"  Found {len(cwes):,} unique CWEs")
        
        # Batch load
        with self.driver.session() as session:
            cwe_list = [{'id': c} for c in cwes]
            session.run("""
                UNWIND $cwes AS cwe
                MERGE (w:CWE {id: cwe.id})
            """, cwes=cwe_list)
        
        self.stats['cwes_loaded'] = len(cwes)
        logger.info(f"  ✅ {len(cwes):,} CWEs loaded")
    
    def create_cve_vendor_relationships(self, cves: List[CVE], batch_size: int = 1000):
        """Create CVE-[:AFFECTS_VENDOR]->Vendor relationships"""
        logger.info("\n🔗 Creating CVE-[:AFFECTS_VENDOR]->Vendor relationships...")
        
        with self.driver.session() as session:
            for i in tqdm(range(0, len(cves), batch_size), desc="  AFFECTS_VENDOR"):
                batch = cves[i:i+batch_size]
                
                # Prepare relationship data
                rels = []
                for cve in batch:
                    for vendor in cve.vendor_names:
                        rels.append({'cve_id': cve.cve_id, 'vendor': vendor})
                
                if rels:
                    session.run("""
                        UNWIND $rels AS rel
                        MATCH (c:CVE {id: rel.cve_id})
                        MATCH (v:Vendor {name: rel.vendor})
                        MERGE (c)-[:AFFECTS_VENDOR]->(v)
                    """, rels=rels)
                    
                    self.stats['relationships_created'] += len(rels)
        
        logger.info(f"  ✅ AFFECTS_VENDOR relationships created")
    
    def create_cve_product_relationships(self, cves: List[CVE], batch_size: int = 1000):
        """Create CVE → Product relationships"""
        logger.info("\n🔗 Creating CVE → Product relationships...")
        
        with self.driver.session() as session:
            for i in tqdm(range(0, len(cves), batch_size), desc="  CVE→Product"):
                batch = cves[i:i+batch_size]
                
                # Prepare relationship data
                rels = []
                for cve in batch:
                    for product in cve.product_names:
                        rels.append({'cve_id': cve.cve_id, 'product': product})
                
                if rels:
                    session.run("""
                        UNWIND $rels AS rel
                        MATCH (c:CVE {id: rel.cve_id})
                        MATCH (p:Product {name: rel.product})
                        MERGE (c)-[:AFFECTS_PRODUCT]->(p)
                    """, rels=rels)
                    
                    self.stats['relationships_created'] += len(rels)
        
        logger.info(f"  ✅ CVE→Product relationships created")
    
    def create_cve_cwe_relationships(self, cves: List[CVE], batch_size: int = 1000):
        """Create CVE → CWE relationships"""
        logger.info("\n🔗 Creating CVE → CWE relationships...")
        
        with self.driver.session() as session:
            for i in tqdm(range(0, len(cves), batch_size), desc="  CVE→CWE"):
                batch = cves[i:i+batch_size]
                
                # Prepare relationship data
                rels = []
                for cve in batch:
                    for cwe in cve.cwes:
                        rels.append({'cve_id': cve.cve_id, 'cwe': cwe})
                
                if rels:
                    session.run("""
                        UNWIND $rels AS rel
                        MATCH (c:CVE {id: rel.cve_id})
                        MATCH (w:CWE {id: rel.cwe})
                        MERGE (c)-[:HAS_CWE]->(w)
                    """, rels=rels)
                    
                    self.stats['relationships_created'] += len(rels)
        
        logger.info(f"  ✅ CVE→CWE relationships created")
    
    def get_stats(self):
        """Get Neo4j graph statistics"""
        logger.info("\n" + "="*80)
        logger.info("📊 NEO4J KNOWLEDGE GRAPH STATISTICS")
        logger.info("="*80)
        
        with self.driver.session() as session:
            # Node counts
            cve_count = session.run("MATCH (c:CVE) RETURN count(c) as count").single()['count']
            vendor_count = session.run("MATCH (v:Vendor) RETURN count(v) as count").single()['count']
            product_count = session.run("MATCH (p:Product) RETURN count(p) as count").single()['count']
            cwe_count = session.run("MATCH (w:CWE) RETURN count(w) as count").single()['count']
            
            logger.info(f"\nNodes:")
            logger.info(f"  CVEs:     {cve_count:,}")
            logger.info(f"  Vendors:  {vendor_count:,}")
            logger.info(f"  Products: {product_count:,}")
            logger.info(f"  CWEs:     {cwe_count:,}")
            logger.info(f"  TOTAL:    {cve_count + vendor_count + product_count + cwe_count:,}")
            
            # Relationship counts
            affects_vendor = session.run("MATCH ()-[r:AFFECTS_VENDOR]->() RETURN count(r) as count").single()['count']
            affects_product = session.run("MATCH ()-[r:AFFECTS_PRODUCT]->() RETURN count(r) as count").single()['count']
            has_cwe = session.run("MATCH ()-[r:HAS_CWE]->() RETURN count(r) as count").single()['count']
            
            logger.info(f"\nRelationships:")
            logger.info(f"  AFFECTS_VENDOR:  {affects_vendor:,}")
            logger.info(f"  AFFECTS_PRODUCT: {affects_product:,}")
            logger.info(f"  HAS_CWE:         {has_cwe:,}")
            logger.info(f"  TOTAL:           {affects_vendor + affects_product + has_cwe:,}")
            
            # Top vendors
            logger.info(f"\n🏢 Top 10 Vendors by CVE Count:")
            top_vendors = session.run("""
                MATCH (v:Vendor)<-[:AFFECTS_VENDOR]-(c:CVE)
                RETURN v.name as vendor, count(c) as cve_count
                ORDER BY cve_count DESC
                LIMIT 10
            """).values()
            
            for vendor, count in top_vendors:
                logger.info(f"  {vendor:30s} {count:,}")
            
            # Top CWEs
            logger.info(f"\n🔍 Top 10 CWEs by CVE Count:")
            top_cwes = session.run("""
                MATCH (w:CWE)<-[:HAS_CWE]-(c:CVE)
                RETURN w.id as cwe, count(c) as cve_count
                ORDER BY cve_count DESC
                LIMIT 10
            """).values()
            
            for cwe, count in top_cwes:
                logger.info(f"  {cwe:20s} {count:,}")
            
            logger.info("="*80)
    
    def load_all(self, batch_size: int = 1000):
        """Main pipeline: Load everything from Redis to Neo4j"""
        start_time = time.time()
        
        # Step 1: Create schema
        self.create_schema()
        
        # Step 2: Load CVEs from Redis (Pydantic validation)
        cves = self.load_cves_from_redis()
        
        if not cves:
            logger.error("❌ No CVEs loaded from Redis!")
            return
        
        # Step 3: Load CVE nodes to Neo4j (batch)
        logger.info(f"\n💾 Loading {len(cves):,} CVE nodes to Neo4j...")
        for i in tqdm(range(0, len(cves), batch_size), desc="  CVE nodes"):
            batch = cves[i:i+batch_size]
            self.load_cve_batch_to_neo4j(batch)
        logger.info(f"  ✅ {len(cves):,} CVE nodes loaded")
        
        # Step 4: Load entity nodes
        self.load_vendors_from_cves(cves)
        self.load_products_from_cves(cves)
        self.load_cwes_from_cves(cves)
        
        # Step 5: Create relationships
        self.create_cve_vendor_relationships(cves, batch_size)
        self.create_cve_product_relationships(cves, batch_size)
        self.create_cve_cwe_relationships(cves, batch_size)
        
        # Step 6: Stats
        elapsed = time.time() - start_time
        logger.info(f"\n⏱️  Total load time: {elapsed/60:.1f} minutes")
        self.get_stats()
        
        logger.info("\n✅ NEO4J HIGHWAY LOAD COMPLETE!")


def main():
    """Main execution"""
    loader = Neo4jHighwayLoader()
    
    try:
        loader.load_all(batch_size=1000)
    finally:
        loader.close()


if __name__ == "__main__":
    main()
