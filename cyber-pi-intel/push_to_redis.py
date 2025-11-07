#!/usr/bin/env python3
"""
Push threats directly to Redis highway for worker processing
Bypasses collection workers by using pre-processed data
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
import hashlib
import redis.asyncio as redis
from pathlib import Path

async def main():
    print("="*60)
    print("🚀 DIRECT REDIS PUSH")
    print("Loading threats → Redis → Workers → Databases")
    print("="*60)

    # Connect to Redis (via port-forward or direct K8s service)
    print("\n📡 Connecting to Redis...")

    # Try localhost first (if port-forward active), fallback to K8s exec
    try:
        redis_client = await redis.from_url(
            "redis://:cyber-pi-redis-2025@localhost:6379",
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        print("✅ Connected via localhost:6379")
    except:
        print("⚠️  localhost:6379 not available")
        print("Use: microk8s kubectl port-forward -n cyber-pi-intel svc/redis 6379:6379")
        return 1

    # Load source data
    data_file = Path("/home/david/projects/cyber-pi/data/raw/master_collection_20251031_014039.json")
    print(f"\n📁 Loading: {data_file}")

    with open(data_file) as f:
        data = json.load(f)

    items = data.get('items', [])
    print(f"📊 Found {len(items)} threat items")

    # Process and queue to Redis
    print("\n🔄 Pushing to Redis highway...")
    queued_weaviate = 0
    queued_neo4j = 0

    for i, item in enumerate(items):
        if i % 100 == 0 and i > 0:
            print(f"  Progress: {i}/{len(items)} ({i*100//len(items)}%)")

        # Generate threat ID
        threat_id = f"threat_{hashlib.sha256((item.get('title', '') + item.get('link', '')).encode()).hexdigest()[:16]}"

        # Parse threat data
        threat_data = {
            "threatId": threat_id,
            "title": item.get('title', 'Unknown')[:500],
            "content": item.get('content', '')[:10000],
            "source": item.get('source', 'cyber-pi'),
            "sourceUrl": item.get('link', ''),
            "industry": [item.get('category', 'General')],
            "severity": "medium",  # Default, can be enhanced
            "threatType": [],
            "threatActors": [],
            "cves": [],  # Extract from content if needed
            "publishedDate": item.get('published', datetime.now(timezone.utc).isoformat()),
            "ingestedDate": datetime.now(timezone.utc).isoformat()
        }

        try:
            # Store parsed threat in Redis (for workers to retrieve)
            await redis_client.setex(
                f"threat:parsed:{threat_id}",
                86400,  # 24 hour TTL
                json.dumps(threat_data)
            )

            # Queue for Weaviate worker
            await redis_client.lpush("queue:weaviate", threat_id)
            queued_weaviate += 1

            # Queue for Neo4j worker
            await redis_client.lpush("queue:neo4j", threat_id)
            queued_neo4j += 1

        except Exception as e:
            print(f"  Error queuing {threat_id}: {e}")

    print(f"\n✅ Complete!")
    print(f"  Queued for Weaviate: {queued_weaviate}")
    print(f"  Queued for Neo4j: {queued_neo4j}")
    print(f"  Total threats in Redis: {queued_weaviate}")

    # Check queue lengths
    weaviate_len = await redis_client.llen("queue:weaviate")
    neo4j_len = await redis_client.llen("queue:neo4j")

    print(f"\n📊 Redis Queue Status:")
    print(f"  queue:weaviate = {weaviate_len} items")
    print(f"  queue:neo4j = {neo4j_len} items")

    await redis_client.close()

    print("\n🎯 Next step: Deploy storage workers")
    print("   kubectl apply -f deployment/cyber-pi-simplified/worker-jobs.yaml")

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
