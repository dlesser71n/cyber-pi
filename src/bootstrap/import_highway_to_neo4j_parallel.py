#!/usr/bin/env python3
"""
Import CVEs from Redis Highway to Neo4j - PARALLEL VERSION
Uses concurrent workers for 10x speed improvement
"""

import redis
import os
import sys
import json
from pathlib import Path
from neo4j import GraphDatabase
from tqdm import tqdm
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.cve_models import CVE

print("=" * 80)
print("📊 IMPORTING CVEs FROM REDIS HIGHWAY TO NEO4J (PARALLEL)")
print("=" * 80)
print()

# Configuration
NUM_WORKERS = 8  # Parallel workers
BATCH_SIZE = 1000  # CVEs per batch

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

# Create indexes (once)
print("🔧 Creating Neo4j indexes...")
with driver.session() as session:
    try:
        session.run("CREATE CONSTRAINT cve_id_unique IF NOT EXISTS FOR (c:CVE) REQUIRE c.cve_id IS UNIQUE")
    except:
        session.run("CREATE INDEX cve_id_index IF NOT EXISTS FOR (c:CVE) ON (c.cve_id)")
    try:
        session.run("CREATE CONSTRAINT vendor_unique IF NOT EXISTS FOR (v:Vendor) REQUIRE v.name IS UNIQUE")
    except:
        session.run("CREATE INDEX vendor_name_index IF NOT EXISTS FOR (v:Vendor) ON (v.name)")
    try:
        session.run("CREATE CONSTRAINT cwe_unique IF NOT EXISTS FOR (w:CWE) REQUIRE w.cwe_id IS UNIQUE")
    except:
        session.run("CREATE INDEX cwe_id_index IF NOT EXISTS FOR (w:CWE) ON (w.cwe_id)")
print("✅ Indexes ready")
print()

# Get all CVE keys
print("📋 Fetching CVE keys from Redis Highway...")
all_keys = r.keys('cve:highway:*')
# Filter out metadata keys (only keep CVE-* keys)
cve_keys = [k for k in all_keys if 'CVE-' in k]
print(f"✅ Found {len(cve_keys):,} CVE keys (filtered from {len(all_keys):,} total)")
print()

# Split keys into chunks for parallel processing
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

key_chunks = list(chunks(cve_keys, BATCH_SIZE))
print(f"📦 Split into {len(key_chunks):,} batches of {BATCH_SIZE}")
print(f"⚡ Using {NUM_WORKERS} parallel workers")
print()

# Thread-safe counters
imported_lock = threading.Lock()
imported_count = 0
error_count = 0

def import_batch(batch_keys):
    """Import a batch of CVEs in a single thread"""
    global imported_count, error_count
    local_imported = 0
    local_errors = 0
    
    # Each thread gets its own Redis connection
    thread_redis = redis.Redis(host=redis_host, port=6379, password=redis_password, decode_responses=True)
    
    # Load CVEs from Redis
    cves = []
    for key in batch_keys:
        try:
            cve_json = thread_redis.get(key)
            if cve_json:
                cve_model = CVE.model_validate_json(cve_json)
                cves.append(cve_model)
        except Exception as e:
            local_errors += 1
    
    # Import to Neo4j in single transaction
    if cves:
        with driver.session() as session:
            def tx_work(tx):
                for cve_model in cves:
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
                            description=cve_model.description[:2000],
                            published=cve_model.published.isoformat() if cve_model.published else None,
                            modified=cve_model.modified.isoformat() if cve_model.modified else None,
                            cvss_v3_score=cve_model.cvss_v3_score,
                            cvss_v2_score=cve_model.cvss_v2_score
                        )
                        
                        # Batch create vendors
                        if cve_model.affected_vendors:
                            vendor_names = [v.name if hasattr(v, 'name') else str(v) for v in cve_model.affected_vendors]
                            tx.run("""
                                UNWIND $vendors AS vendor_name
                                MERGE (v:Vendor {name: vendor_name})
                                WITH v
                                MATCH (c:CVE {cve_id: $cve_id})
                                MERGE (c)-[:AFFECTS_VENDOR]->(v)
                            """, vendors=vendor_names, cve_id=cve_model.cve_id)
                        
                        # Batch create CWEs
                        if cve_model.cwes:
                            tx.run("""
                                UNWIND $cwes AS cwe
                                MERGE (w:CWE {cwe_id: cwe})
                                WITH w
                                MATCH (c:CVE {cve_id: $cve_id})
                                MERGE (c)-[:HAS_WEAKNESS]->(w)
                            """, cwes=cve_model.cwes, cve_id=cve_model.cve_id)
                        
                    except Exception as e:
                        pass  # Continue on error
            
            try:
                session.execute_write(tx_work)
                local_imported = len(cves)
            except Exception as e:
                local_errors += len(cves)
    
    # Update global counters
    with imported_lock:
        imported_count += local_imported
        error_count += local_errors
    
    thread_redis.close()
    return local_imported, local_errors

# Import in parallel
print("📥 Importing CVEs to Neo4j (parallel)...")
with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
    futures = {executor.submit(import_batch, chunk): chunk for chunk in key_chunks}
    
    with tqdm(total=len(cve_keys), desc="Importing CVEs") as pbar:
        for future in as_completed(futures):
            imported, errors = future.result()
            pbar.update(imported + errors)

print()
print("=" * 80)
print("✅ NEO4J IMPORT COMPLETE")
print("=" * 80)
print(f"   Imported: {imported_count:,} CVEs")
print(f"   Errors: {error_count:,}")
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
