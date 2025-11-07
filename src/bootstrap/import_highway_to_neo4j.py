#!/usr/bin/env python3
"""
Import CVEs from Redis Highway to Neo4j
Uses Pydantic-validated models from Redis Highway format
"""

import redis
import os
import sys
import json
from pathlib import Path
from neo4j import GraphDatabase
from tqdm import tqdm
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.cve_models import CVE

print("=" * 80)
print("📊 IMPORTING CVEs FROM REDIS HIGHWAY TO NEO4J")
print("=" * 80)
print()

# Connect to Redis
redis_host = os.getenv('REDIS_HOST', 'redis.cyber-pi.svc.cluster.local')
redis_password = os.getenv('REDIS_PASSWORD', 'cyber-pi-redis-2025')

print(f"🔌 Connecting to Redis...")
r = redis.Redis(host=redis_host, port=6379, password=redis_password, decode_responses=True)
r.ping()
print("✅ Redis connected")

# Connect to Neo4j
neo4j_uri = os.getenv('NEO4J_URI', 'bolt://neo4j.cyber-pi.svc.cluster.local:7687')
neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
neo4j_password = os.getenv('NEO4J_PASSWORD', 'cyber-pi-neo4j-2025')

print(f"🔌 Connecting to Neo4j...")
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
driver.verify_connectivity()
print("✅ Neo4j connected")
print()

# Create indexes
print("🔧 Creating Neo4j indexes and constraints...")
with driver.session() as session:
    try:
        session.run("CREATE CONSTRAINT cve_id_unique IF NOT EXISTS FOR (c:CVE) REQUIRE c.cve_id IS UNIQUE")
    except Exception as e:
        print(f"   Note: CVE constraint: {e}")
        session.run("CREATE INDEX cve_id_index IF NOT EXISTS FOR (c:CVE) ON (c.cve_id)")
    
    try:
        session.run("CREATE CONSTRAINT vendor_unique IF NOT EXISTS FOR (v:Vendor) REQUIRE v.name IS UNIQUE")
    except Exception as e:
        print(f"   Note: Vendor constraint: {e}")
        session.run("CREATE INDEX vendor_name_index IF NOT EXISTS FOR (v:Vendor) ON (v.name)")
    
    try:
        session.run("CREATE CONSTRAINT cwe_unique IF NOT EXISTS FOR (w:CWE) REQUIRE w.cwe_id IS UNIQUE")
    except Exception as e:
        print(f"   Note: CWE constraint: {e}")
        session.run("CREATE INDEX cwe_id_index IF NOT EXISTS FOR (w:CWE) ON (w.cwe_id)")
print("✅ Indexes/constraints ready")
print()

# Get all CVE keys from Redis Highway
print("📋 Fetching CVE keys from Redis Highway...")
all_keys = r.keys('cve:highway:*')
# Filter out metadata keys (only keep CVE-* keys)
cve_keys = [k for k in all_keys if 'CVE-' in k]
print(f"✅ Found {len(cve_keys):,} CVE keys (filtered from {len(all_keys):,} total)")
print()

# Import to Neo4j
print("📥 Importing CVEs to Neo4j...")
print("   Creating: CVE nodes, Vendor nodes, CWE nodes, Relationships")
print()

imported = 0
errors = 0
batch_size = 500
batch = []

def import_batch(tx, cves_batch):
    """Import a batch of CVEs"""
    for cve_model in cves_batch:
        try:
            # Create CVE node
            tx.run("""
                MERGE (c:CVE {cve_id: $cve_id})
                SET c.description = $description,
                    c.published = datetime($published),
                    c.modified = datetime($modified),
                    c.cvss_v3_score = $cvss_v3_score,
                    c.cvss_v2_score = $cvss_v2_score,
                    c.source = 'nvd_highway',
                    c.imported_at = datetime()
            """,
                cve_id=cve_model.cve_id,
                description=cve_model.description[:2000],  # Truncate long descriptions
                published=cve_model.published.isoformat() if cve_model.published else None,
                modified=cve_model.modified.isoformat() if cve_model.modified else None,
                cvss_v3_score=cve_model.cvss_v3_score,
                cvss_v2_score=cve_model.cvss_v2_score
            )
            
            # Create Vendor nodes and relationships
            for vendor in cve_model.affected_vendors:
                vendor_name = vendor.name if hasattr(vendor, 'name') else str(vendor)
                tx.run("""
                    MERGE (v:Vendor {name: $vendor_name})
                    WITH v
                    MATCH (c:CVE {cve_id: $cve_id})
                    MERGE (c)-[:AFFECTS_VENDOR]->(v)
                """, vendor_name=vendor_name, cve_id=cve_model.cve_id)
            
            # Create CWE nodes and relationships
            for cwe in cve_model.cwes:
                tx.run("""
                    MERGE (w:CWE {cwe_id: $cwe})
                    WITH w
                    MATCH (c:CVE {cve_id: $cve_id})
                    MERGE (c)-[:HAS_WEAKNESS]->(w)
                """, cwe=cwe, cve_id=cve_model.cve_id)
        
        except Exception as e:
            raise Exception(f"Error importing {cve_model.cve_id}: {e}")

for key in tqdm(cve_keys, desc="Importing CVEs"):
    try:
        # Load Pydantic model from Redis
        cve_json = r.get(key)
        if not cve_json:
            continue
        
        cve_model = CVE.model_validate_json(cve_json)
        batch.append(cve_model)
        
        # Import batch when full
        if len(batch) >= batch_size:
            with driver.session() as session:
                session.execute_write(import_batch, batch)
            imported += len(batch)
            batch = []
    
    except Exception as e:
        errors += 1
        if errors <= 10:
            print(f"\n⚠️  Error: {e}")

# Import remaining batch
if batch:
    with driver.session() as session:
        session.execute_write(import_batch, batch)
    imported += len(batch)

print()
print("=" * 80)
print("✅ NEO4J IMPORT COMPLETE")
print("=" * 80)
print(f"   Imported: {imported:,} CVEs")
print(f"   Errors: {errors:,}")
print()

# Verify
with driver.session() as session:
    result = session.run("MATCH (c:CVE) RETURN count(c) as count")
    cve_count = result.single()['count']
    
    result = session.run("MATCH (v:Vendor) RETURN count(v) as count")
    vendor_count = result.single()['count']
    
    result = session.run("MATCH (w:CWE) RETURN count(w) as count")
    cwe_count = result.single()['count']
    
    result = session.run("MATCH ()-[r:AFFECTS_VENDOR]->() RETURN count(r) as count")
    vendor_rels = result.single()['count']
    
    result = session.run("MATCH ()-[r:HAS_WEAKNESS]->() RETURN count(r) as count")
    cwe_rels = result.single()['count']

print(f"🔍 Verification:")
print(f"   CVE nodes: {cve_count:,}")
print(f"   Vendor nodes: {vendor_count:,}")
print(f"   CWE nodes: {cwe_count:,}")
print(f"   AFFECTS_VENDOR relationships: {vendor_rels:,}")
print(f"   HAS_WEAKNESS relationships: {cwe_rels:,}")
print()

driver.close()
r.close()
print("✅ Done!")
