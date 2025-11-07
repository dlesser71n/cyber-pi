#!/usr/bin/env python3
"""
Import CVEs to Redis
Load all 317K CVEs from JSON into Redis for fast access
"""

import json
import redis
import os
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

print("=" * 80)
print("📥 IMPORTING CVEs TO REDIS")
print("=" * 80)
print()

# Connect to Redis
redis_host = os.getenv('REDIS_HOST', 'redis.cyber-pi.svc.cluster.local')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_password = os.getenv('REDIS_PASSWORD', 'cyber-pi-redis-2025')

print(f"🔌 Connecting to Redis at {redis_host}:{redis_port}...")
r = redis.Redis(
    host=redis_host,
    port=redis_port,
    password=redis_password,
    decode_responses=True
)

try:
    r.ping()
    print("✅ Connected to Redis")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    exit(1)

# Load CVE data
data_file = Path('/home/david/projects/cyber-pi/data/cve_import/all_cves_neo4j.json')
print(f"\n📂 Loading CVE data from: {data_file}")

if not data_file.exists():
    print(f"❌ File not found: {data_file}")
    exit(1)

print(f"📊 File size: {data_file.stat().st_size / 1024 / 1024:.1f} MB")
print("⏳ Loading JSON (this may take a minute)...")

with open(data_file) as f:
    cves = json.load(f)

print(f"✅ Loaded {len(cves):,} CVEs")
print()

# Import to Redis
print("📥 Importing to Redis...")
print(f"   Strategy: Hash per CVE (nvd:cve:CVE-XXXX)")
print()

imported = 0
skipped = 0
errors = 0

for cve in tqdm(cves, desc="Importing CVEs"):
    try:
        cve_id = cve.get('cve_id')
        if not cve_id:
            skipped += 1
            continue
        
        key = f"nvd:cve:{cve_id}"
        
        # Build Redis hash
        hash_data = {
            'cve_id': cve_id,
            'description': cve.get('description', '')[:1000],  # Truncate long descriptions
            'published': cve.get('published', ''),
            'modified': cve.get('modified', ''),
            'cvss_v3_score': str(cve.get('cvss_v3_score', '')),
            'cvss_v3_severity': cve.get('cvss_v3_severity', ''),
            'cvss_v3_vector': cve.get('cvss_v3_vector', ''),
            'cvss_v2_score': str(cve.get('cvss_v2_score', '')),
            'affected_vendors': ','.join(cve.get('affected_vendors', []))[:500],
            'cwes': ','.join(cve.get('cwes', []))[:200],
            'reference_count': str(cve.get('reference_count', 0)),
            'source': 'nvd_bulk_import',
            'imported_at': datetime.utcnow().isoformat()
        }
        
        # Remove empty values
        hash_data = {k: v for k, v in hash_data.items() if v}
        
        # Store in Redis
        r.hset(key, mapping=hash_data)
        imported += 1
        
    except Exception as e:
        errors += 1
        if errors < 10:  # Only print first 10 errors
            print(f"\n⚠️  Error importing {cve.get('cve_id', 'unknown')}: {e}")

print()
print("=" * 80)
print("✅ REDIS IMPORT COMPLETE")
print("=" * 80)
print(f"   Imported: {imported:,} CVEs")
print(f"   Skipped: {skipped:,}")
print(f"   Errors: {errors:,}")
print()

# Store metadata
r.set('nvd:import:total_cves', imported)
r.set('nvd:import:timestamp', datetime.utcnow().isoformat())
r.set('nvd:import:version', '2.0')

# Verify
total_keys = len(r.keys('nvd:cve:*'))
print(f"🔍 Verification: {total_keys:,} CVE keys in Redis")
print()

r.close()
print("✅ Done!")
