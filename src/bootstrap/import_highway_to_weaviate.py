#!/usr/bin/env python3
"""
Import CVEs from Redis Highway to Weaviate
Creates vector embeddings for semantic search
"""

import redis
import os
import sys
import json
from pathlib import Path
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from tqdm import tqdm
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.cve_models import CVE

print("=" * 80)
print("🔍 IMPORTING CVEs FROM REDIS HIGHWAY TO WEAVIATE")
print("=" * 80)
print()

# Connect to Redis
redis_host = os.getenv('REDIS_HOST', 'redis.cyber-pi.svc.cluster.local')
redis_password = os.getenv('REDIS_PASSWORD', 'cyber-pi-redis-2025')

print(f"🔌 Connecting to Redis...")
r = redis.Redis(host=redis_host, port=6379, password=redis_password, decode_responses=True)
r.ping()
print("✅ Redis connected")

# Connect to Weaviate
weaviate_url = os.getenv('WEAVIATE_URL', 'http://weaviate.cyber-pi.svc.cluster.local:8080')

print(f"🔌 Connecting to Weaviate at {weaviate_url}...")
client = weaviate.connect_to_custom(
    http_host=weaviate_url.replace('http://', '').replace('https://', '').split(':')[0],
    http_port=8080,
    http_secure=False,
    grpc_host=weaviate_url.replace('http://', '').replace('https://', '').split(':')[0],
    grpc_port=50051,
    grpc_secure=False
)
print("✅ Weaviate connected")
print()

# Create CVE collection if it doesn't exist
print("🔧 Setting up Weaviate CVE collection...")
try:
    # Check if collection exists
    collections = client.collections.list_all()
    if 'CVE' not in [c.name for c in collections]:
        print("   Creating CVE collection...")
        client.collections.create(
            name="CVE",
            vectorizer_config=Configure.Vectorizer.text2vec_transformers(),
            properties=[
                Property(name="cve_id", data_type=DataType.TEXT),
                Property(name="description", data_type=DataType.TEXT),
                Property(name="cvss_v3_score", data_type=DataType.NUMBER),
                Property(name="cvss_v3_severity", data_type=DataType.TEXT),
                Property(name="published", data_type=DataType.DATE),
                Property(name="modified", data_type=DataType.DATE),
                Property(name="vendors", data_type=DataType.TEXT_ARRAY),
                Property(name="cwes", data_type=DataType.TEXT_ARRAY),
                Property(name="source", data_type=DataType.TEXT)
            ]
        )
        print("   ✅ CVE collection created")
    else:
        print("   ✅ CVE collection exists")
except Exception as e:
    print(f"   Note: {e}")
print()

# Get CVE collection
cve_collection = client.collections.get("CVE")

# Get all CVE keys from Redis Highway
print("📋 Fetching CVE keys from Redis Highway...")
cve_keys = r.keys('cve:highway:*')
print(f"✅ Found {len(cve_keys):,} CVE keys")
print()

# Import to Weaviate
print("📥 Importing CVEs to Weaviate...")
print("   Creating vector embeddings for semantic search...")
print()

imported = 0
errors = 0
batch_size = 100

with cve_collection.batch.dynamic() as batch:
    for key in tqdm(cve_keys, desc="Vectorizing CVEs"):
        try:
            # Load Pydantic model from Redis
            cve_json = r.get(key)
            if not cve_json:
                continue
            
            cve_model = CVE.model_validate_json(cve_json)
            
            # Prepare data for Weaviate
            properties = {
                "cve_id": cve_model.cve_id,
                "description": cve_model.description[:5000],  # Truncate very long descriptions
                "cvss_v3_score": cve_model.cvss_v3_score if cve_model.cvss_v3_score else 0.0,
                "cvss_v3_severity": str(cve_model.cvss_v3_score) if cve_model.cvss_v3_score else "unknown",
                "published": cve_model.published.isoformat() if cve_model.published else None,
                "modified": cve_model.modified.isoformat() if cve_model.modified else None,
                "vendors": [v.name if hasattr(v, 'name') else str(v) for v in cve_model.affected_vendors][:50],
                "cwes": cve_model.cwes[:20],
                "source": "nvd_highway"
            }
            
            # Add to batch
            batch.add_object(properties=properties)
            imported += 1
            
        except Exception as e:
            errors += 1
            if errors <= 10:
                print(f"\n⚠️  Error: {e}")

print()
print("=" * 80)
print("✅ WEAVIATE IMPORT COMPLETE")
print("=" * 80)
print(f"   Imported: {imported:,} CVEs")
print(f"   Errors: {errors:,}")
print()

# Verify
try:
    result = cve_collection.aggregate.over_all(total_count=True)
    count = result.total_count
    print(f"🔍 Verification: {count:,} CVEs in Weaviate")
except Exception as e:
    print(f"⚠️  Could not verify count: {e}")

print()
client.close()
r.close()
print("✅ Done! CVEs ready for semantic search")
