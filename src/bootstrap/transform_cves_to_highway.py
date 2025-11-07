#!/usr/bin/env python3
"""
Transform CVEs to Redis Highway Format
Converts raw JSON CVEs to Pydantic-validated models and stores in Redis Highway

Pipeline:
  JSON → Pydantic CVE Model → Redis Highway → Neo4j/Weaviate
"""

import json
import redis
import os
import sys
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.cve_models import CVE, CVEVendor, CVEProduct, CVEReference, CVSSMetrics

print("=" * 80)
print("🔄 TRANSFORMING CVEs TO REDIS HIGHWAY FORMAT")
print("=" * 80)
print()

# Connect to Redis
redis_host = os.getenv('REDIS_HOST', 'redis.cyber-pi.svc.cluster.local')
redis_password = os.getenv('REDIS_PASSWORD', 'cyber-pi-redis-2025')

print(f"🔌 Connecting to Redis...")
r = redis.Redis(host=redis_host, port=6379, password=redis_password, decode_responses=False)
r.ping()
print("✅ Redis connected")
print()

# Load CVE JSON
data_file = Path(__file__).parent.parent.parent / 'data' / 'cve_import' / 'all_cves_neo4j.json'
print(f"📂 Loading CVE data from: {data_file}")

with open(data_file) as f:
    cves_json = json.load(f)

print(f"✅ Loaded {len(cves_json):,} CVEs")
print()

# Transform and store in Redis Highway
print("🔄 Transforming to Pydantic models and storing in Redis Highway...")
print("   Format: cve:highway:{cve_id} → Pydantic JSON")
print()

transformed = 0
validation_errors = 0
storage_errors = 0

for cve_json in tqdm(cves_json, desc="Transforming"):
    try:
        # Parse dates
        published = None
        modified = None
        if cve_json.get('published'):
            try:
                published = datetime.fromisoformat(cve_json['published'].replace('Z', '+00:00'))
            except:
                pass
        if cve_json.get('modified'):
            try:
                modified = datetime.fromisoformat(cve_json['modified'].replace('Z', '+00:00'))
            except:
                pass
        
        # Build Pydantic model
        cve_model = CVE(
            cve_id=cve_json['cve_id'],
            description=cve_json.get('description', 'No description available'),
            cvss_v3_score=cve_json.get('cvss_v3_score'),
            cvss_v2_score=cve_json.get('cvss_v2_score'),
            published=published,
            modified=modified,
            affected_vendors=[CVEVendor(name=v) for v in cve_json.get('affected_vendors', []) if v],
            affected_products=[
                CVEProduct(
                    product=p.get('product', p.get('name', 'unknown')),
                    version=p.get('version'),
                    vendor=p.get('vendor'),
                    cpe=p.get('cpe')
                ) if isinstance(p, dict) else CVEProduct(product=str(p))
                for p in cve_json.get('affected_products', [])
            ],
            cwes=cve_json.get('cwes', []),
            references=[
                CVEReference(
                    url=r.get('url', ''),
                    source=r.get('source'),
                    tags=r.get('tags', [])
                ) if isinstance(r, dict) else CVEReference(url=str(r), tags=[])
                for r in cve_json.get('references', [])
            ]
        )
        
        # Store in Redis Highway format
        key = f"cve:highway:{cve_model.cve_id}"
        value = cve_model.model_dump_json()
        r.set(key, value)
        
        transformed += 1
        
    except Exception as e:
        validation_errors += 1
        if validation_errors <= 10:  # Only print first 10 errors
            print(f"\n⚠️  Validation error for {cve_json.get('cve_id', 'unknown')}: {e}")

print()
print("=" * 80)
print("✅ TRANSFORMATION COMPLETE")
print("=" * 80)
print(f"   Transformed: {transformed:,} CVEs")
print(f"   Validation errors: {validation_errors:,}")
print(f"   Storage errors: {storage_errors:,}")
print()

# Verify
highway_keys = r.keys('cve:highway:*')
print(f"🔍 Verification: {len(highway_keys):,} CVEs in Redis Highway")
print()

# Store metadata
r.set('cve:highway:total', transformed)
r.set('cve:highway:timestamp', datetime.utcnow().isoformat())
r.set('cve:highway:version', '1.0')

r.close()
print("✅ Done! CVEs ready for Neo4j and Weaviate import")
