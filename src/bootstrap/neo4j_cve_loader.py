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
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

import redis
from neo4j import GraphDatabase
from tqdm import tqdm
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.cve_models import CVE, CVEVendor, CVEProduct

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Neo4jHighwayLoader:
    """
    Load CVEs from Redis Highway into Neo4j Knowledge Graph
    
    Source: Redis Highway (validated, indexed, embedded)
    Schema: Pydantic CVE models (single source of truth)
    Destination: Neo4j (graph analytics, ML features)
    
    Graph Structure:
    - (CVE) nodes with all properties from Pydantic model
    - (Vendor) nodes from affected_vendors
    - (Product) nodes from affected_products
    - (CWE) nodes from weakness enumeration
    - Relationships:
      * (CVE)-[:AFFECTS_VENDOR]->(Vendor)
      * (CVE)-[:AFFECTS_PRODUCT]->(Product)
      * (CVE)-[:HAS_CWE]->(CWE)
      * (CVE)-[:SIMILAR_TO {score}]->(CVE) [from embeddings]
      * (Product)-[:FROM_VENDOR]->(Vendor)
    """
    
    def __init__(
        self,
        redis_host: str = "10.152.183.253",
        redis_port: int = 6379,
        redis_password: Optional[str] = None,
        neo4j_uri: str = "bolt://10.152.183.77:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: Optional[str] = None,
        use_embeddings: bool = True,
        similarity_threshold: float = 0.85
    ):
        """Initialize connections to Redis and Neo4j"""
        logger.info("="*80)
        logger.info("🚀 NEO4J CVE LOADER - REDIS TO NEO4J WITH EMBEDDINGS")
        logger.info("="*80)
        
        # Get passwords from environment
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
        
        self.use_embeddings = use_embeddings
        self.similarity_threshold = similarity_threshold
        
        # Stats
        self.stats = {
            'cves_loaded': 0,
            'vendors_loaded': 0,
            'products_loaded': 0,
            'cwes_loaded': 0,
            'relationships_created': 0,
            'similarity_edges': 0
        }
        
    def close(self):
        self.driver.close()
    
    def create_indexes(self):
        """Create indexes for fast lookups"""
        logger.info("📇 Creating Neo4j indexes...")
        
        with self.driver.session() as session:
            # CVE index
            session.run("CREATE INDEX cve_id_index IF NOT EXISTS FOR (c:CVE) ON (c.id)")
            
            # Vendor index  
            session.run("CREATE INDEX vendor_name_index IF NOT EXISTS FOR (v:Vendor) ON (v.name)")
            
            # Product index
            session.run("CREATE INDEX product_name_index IF NOT EXISTS FOR (p:Product) ON (p.name)")
            
            # CWE index
            session.run("CREATE INDEX cwe_id_index IF NOT EXISTS FOR (w:CWE) ON (w.id)")
            
            logger.info("✓ Indexes created")
    
    def create_constraints(self):
        """Create uniqueness constraints"""
        logger.info("🔒 Creating uniqueness constraints...")
        
        with self.driver.session() as session:
            try:
                session.run("CREATE CONSTRAINT cve_id_unique IF NOT EXISTS FOR (c:CVE) REQUIRE c.id IS UNIQUE")
                session.run("CREATE CONSTRAINT vendor_name_unique IF NOT EXISTS FOR (v:Vendor) REQUIRE v.name IS UNIQUE")
                session.run("CREATE CONSTRAINT cwe_id_unique IF NOT EXISTS FOR (w:CWE) REQUIRE w.id IS UNIQUE")
                logger.info("✓ Constraints created")
            except Exception as e:
                logger.warning(f"Constraint creation warning: {e}")
    
    def load_cves_from_redis(self, batch_size: int = 1000) -> List[CVE]:
        """Load CVEs from Redis and reconstruct as Pydantic objects"""
        logger.info("📚 Loading CVEs from Redis...")
        
        # Get all CVE keys (exclude embedding keys)
        cve_keys = [
            k for k in self.redis.keys("cve:CVE-*")
            if not k.endswith(":embedding")
        ]
        
        logger.info(f"Found {len(cve_keys):,} CVEs in Redis")
        
        cves = []
        for key in tqdm(cve_keys, desc="Loading from Redis"):
            try:
                # Get hash data
                cve_data = self.redis.hgetall(key)
                
                # Reconstruct Pydantic CVE
                # Convert Redis string data back to proper types
                cve = self._redis_hash_to_cve(cve_data)
                cves.append(cve)
            except Exception as e:
                logger.warning(f"⚠️  Failed to load {key}: {e}")
        
        logger.info(f"✅ Loaded {len(cves):,} CVEs from Redis")
        return cves
    
    def _redis_hash_to_cve(self, redis_data: Dict[str, str]) -> CVE:
        """Convert Redis hash back to Pydantic CVE object"""
        # Redis stores everything as strings, need to convert back
        data = {}
        
        for key, value in redis_data.items():
            if key in ['cvss_v3', 'cvss_v2']:
                data[f'{key}_score'] = float(value) if value else None
            elif key in ['vendors', 'products', 'cwes']:
                data[f'affected_{key}' if key in ['vendors', 'products'] else key] = [
                    v.strip() for v in value.split(',') if v.strip()
                ]
            elif key in ['references']:
                data[key] = [r.strip() for r in value.split(',') if r.strip()]
            else:
                data[key] = value
        
        # Create CVE using Pydantic validation
        return CVE(**data)
    
    def load_cve_batch(self, cves: List[CVE]):
        """Load batch of CVEs using Pydantic to_neo4j_node() method"""
        with self.driver.session() as session:
            # Convert each CVE using its built-in method
            nodes = [cve.to_neo4j_node() for cve in cves]
            
            # Batch insert CVEs
            session.run("""
                UNWIND $nodes AS node
                MERGE (c:CVE {id: node.id})
                SET c = node
            """, nodes=nodes)
            
            self.stats['cves_loaded'] += len(cves)
    
    def load_vendors_batch(self, cves: List[CVE]):
        """Load vendors from CVEs using Pydantic vendor_names property"""
        with self.driver.session() as session:
            # Extract unique vendors using Pydantic computed property
            all_vendors = []
            for cve in cves:
                for vendor in cve.vendor_names:  # Pydantic computed property
                    all_vendors.append({'name': vendor})
            
            if all_vendors:
                session.run("""
                    UNWIND $vendors AS vendor
                    MERGE (v:Vendor {name: vendor.name})
                """, vendors=all_vendors)
                
            self.stats['vendors_loaded'] += len(set(v['name'] for v in all_vendors))
    
    def load_products_and_relationships(self, cves: List[Dict]):
        """Load products and create CVE->Product, Product->Vendor relationships"""
        with self.driver.session() as session:
            for cve in cves:
                cve_id = cve['cve_id']
                
                for product_info in cve.get('affected_products', []):
                    vendor = product_info['vendor']
                    product = product_info['product']
                    version = product_info.get('version', '*')
                    cpe = product_info.get('cpe', '')
                    
                    # Create Product and relationships
                    session.run("""
                        MATCH (c:CVE {id: $cve_id})
                        MERGE (v:Vendor {name: $vendor})
                        MERGE (p:Product {name: $product, vendor: $vendor})
                        SET p.cpe = $cpe
                        MERGE (c)-[:AFFECTS {version: $version}]->(p)
                        MERGE (p)-[:MADE_BY]->(v)
                    """, cve_id=cve_id, vendor=vendor, product=product, version=version, cpe=cpe)
    
    def load_cwes_and_relationships(self, cves: List[Dict]):
        """Load CWEs (Common Weakness Enumeration) and link to CVEs"""
        with self.driver.session() as session:
            for cve in cves:
                cve_id = cve['cve_id']
                
                for cwe_id in cve.get('cwes', []):
                    session.run("""
                        MATCH (c:CVE {id: $cve_id})
                        MERGE (w:CWE {id: $cwe_id})
                        MERGE (c)-[:HAS_WEAKNESS]->(w)
                    """, cve_id=cve_id, cwe_id=cwe_id)
    
    def create_similarity_relationships(self):
        """
        Create SIMILAR_TO relationships between CVEs
        Based on:
        - Same CWE (weakness type)
        - Same vendor/product
        - Similar CVSS scores
        """
        logger.info("🔗 Creating similarity relationships...")
        
        with self.driver.session() as session:
            # Link CVEs with same CWE
            session.run("""
                MATCH (c1:CVE)-[:HAS_WEAKNESS]->(w:CWE)<-[:HAS_WEAKNESS]-(c2:CVE)
                WHERE c1.id < c2.id
                MERGE (c1)-[:SIMILAR_WEAKNESS]->(c2)
            """)
            
            # Link CVEs affecting same product
            session.run("""
                MATCH (c1:CVE)-[:AFFECTS]->(p:Product)<-[:AFFECTS]-(c2:CVE)
                WHERE c1.id < c2.id
                MERGE (c1)-[:SIMILAR_TARGET]->(c2)
            """)
            
            logger.info("✓ Similarity relationships created")
    
    def get_graph_stats(self):
        """Get statistics about the knowledge graph"""
        logger.info("\n" + "="*80)
        logger.info("📊 NEO4J KNOWLEDGE GRAPH STATISTICS")
        logger.info("="*80)
        
        with self.driver.session() as session:
            # Node counts
            cve_count = session.run("MATCH (c:CVE) RETURN count(c) as count").single()['count']
            vendor_count = session.run("MATCH (v:Vendor) RETURN count(v) as count").single()['count']
            product_count = session.run("MATCH (p:Product) RETURN count(p) as count").single()['count']
            cwe_count = session.run("MATCH (w:CWE) RETURN count(w) as count").single()['count']
            
            logger.info(f"Nodes:")
            logger.info(f"  CVEs:     {cve_count:,}")
            logger.info(f"  Vendors:  {vendor_count:,}")
            logger.info(f"  Products: {product_count:,}")
            logger.info(f"  CWEs:     {cwe_count:,}")
            logger.info(f"  TOTAL:    {cve_count + vendor_count + product_count + cwe_count:,}")
            
            # Relationship counts
            affects_count = session.run("MATCH ()-[r:AFFECTS]->() RETURN count(r) as count").single()['count']
            weakness_count = session.run("MATCH ()-[r:HAS_WEAKNESS]->() RETURN count(r) as count").single()['count']
            made_by_count = session.run("MATCH ()-[r:MADE_BY]->() RETURN count(r) as count").single()['count']
            
            logger.info(f"\nRelationships:")
            logger.info(f"  AFFECTS:       {affects_count:,}")
            logger.info(f"  HAS_WEAKNESS:  {weakness_count:,}")
            logger.info(f"  MADE_BY:       {made_by_count:,}")
            
            # Top vendors by CVE count
            top_vendors = session.run("""
                MATCH (v:Vendor)<-[:MADE_BY]-(p:Product)<-[:AFFECTS]-(c:CVE)
                RETURN v.name as vendor, count(DISTINCT c) as cve_count
                ORDER BY cve_count DESC
                LIMIT 10
            """).values()
            
            logger.info(f"\nTop 10 Vendors by CVE Count:")
            for vendor, count in top_vendors:
                logger.info(f"  {vendor:30s} {count:,}")
            
            # Top CWEs
            top_cwes = session.run("""
                MATCH (w:CWE)<-[:HAS_WEAKNESS]-(c:CVE)
                RETURN w.id as cwe, count(c) as cve_count
                ORDER BY cve_count DESC
                LIMIT 10
            """).values()
            
            logger.info(f"\nTop 10 CWEs (Weakness Types):")
            for cwe, count in top_cwes:
                logger.info(f"  {cwe:30s} {count:,}")
            
            logger.info("="*80 + "\n")
    
    def load_all_cves(self, cves: List[Dict], batch_size=1000):
        """Load all CVEs into Neo4j with progress tracking"""
        logger.info(f"📥 Loading {len(cves):,} CVEs into Neo4j...")
        logger.info(f"Batch size: {batch_size}")
        
        start_time = time.time()
        
        # Step 1: Create indexes and constraints
        self.create_indexes()
        self.create_constraints()
        
        # Step 2: Load CVEs in batches
        logger.info("\n1️⃣  Loading CVE nodes...")
        for i in tqdm(range(0, len(cves), batch_size), desc="CVE batches"):
            batch = cves[i:i+batch_size]
            self.load_cve_batch(batch)
        
        # Step 3: Load vendors
        logger.info("\n2️⃣  Loading Vendor nodes...")
        for i in tqdm(range(0, len(cves), batch_size), desc="Vendor batches"):
            batch = cves[i:i+batch_size]
            self.load_vendors_batch(batch)
        
        # Step 4: Load products and create CVE->Product, Product->Vendor relationships
        logger.info("\n3️⃣  Loading Products and relationships...")
        for i in tqdm(range(0, len(cves), batch_size), desc="Product batches"):
            batch = cves[i:i+batch_size]
            self.load_products_and_relationships(batch)
        
        # Step 5: Load CWEs and create CVE->CWE relationships
        logger.info("\n4️⃣  Loading CWEs and weakness relationships...")
        for i in tqdm(range(0, len(cves), batch_size), desc="CWE batches"):
            batch = cves[i:i+batch_size]
            self.load_cwes_and_relationships(batch)
        
        # Step 6: Create similarity relationships
        logger.info("\n5️⃣  Creating CVE similarity relationships...")
        self.create_similarity_relationships()
        
        elapsed = time.time() - start_time
        logger.info(f"\n✅ Neo4j load complete in {elapsed/60:.1f} minutes")
        
        # Step 7: Show statistics
        self.get_graph_stats()


def main():
    """Main execution"""
    # Load CVE data
    data_file = Path("data/cve_import/all_cves_neo4j.json")
    
    if not data_file.exists():
        logger.error(f"CVE data file not found: {data_file}")
        logger.error("Run cve_bulk_import.py first!")
        return
    
    logger.info(f"📖 Loading CVE data from {data_file}...")
    with open(data_file) as f:
        cves = json.load(f)
    
    logger.info(f"✓ Loaded {len(cves):,} CVEs")
    
    # Load Neo4j credentials from environment or settings
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    
    # Load .env from project root
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
    
    loader = Neo4jCVELoader(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "dev-neo4j-password")
    )
    
    try:
        loader.load_all_cves(cves, batch_size=1000)
    finally:
        loader.close()


if __name__ == "__main__":
    main()
