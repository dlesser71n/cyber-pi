#!/usr/bin/env python3
"""
Redis-First Ingestion
Everything goes to Redis first, then workers process
"""

import json
import sys
import asyncio
from pathlib import Path
import redis.asyncio as redis
import hashlib
import re
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

from backend.core.redis_hub import RedisHub


def parse_cyber_pi_threat(item: dict) -> dict:
    """Parse cyber-pi threat format with proper flattening"""
    threat_id = item.get('id', hashlib.sha256(
        (item.get('title', '') + item.get('link', '')).encode()
    ).hexdigest()[:16])
    
    content = item.get('content', '')
    title = item.get('title', 'Unknown Threat')
    text_lower = (title + ' ' + content).lower()
    
    # Extract threat types
    threat_types = []
    for keyword in ['ransomware', 'phishing', 'malware', 'ddos', 'botnet', 'apt', 'zero-day']:
        if keyword in text_lower:
            threat_types.append(keyword)
    
    # Extract CVEs
    cves = list(set(re.findall(r'CVE-\d{4}-\d{4,7}', content, re.IGNORECASE)))
    
    # Determine severity
    if any(k in text_lower for k in ['critical', 'severe', 'zero-day']):
        severity = 'critical'
    elif any(k in text_lower for k in ['high', 'important']):
        severity = 'high'
    else:
        severity = 'medium'
    
    # Extract threat actors
    actors = []
    for actor in ['Lockbit', 'BlackCat', 'Lazarus', 'APT28', 'APT29']:
        if actor.lower() in text_lower:
            actors.append(actor)
    
    # Flatten source (handle both string and dict)
    source = item.get('source', 'cyber-pi')
    if isinstance(source, dict):
        source = source.get('name', 'cyber-pi')
    
    # Fix date format to RFC3339 with Z suffix (Weaviate format)
    published = item.get('published', datetime.now(timezone.utc).isoformat())
    if isinstance(published, str):
        # Replace +00:00 with Z for UTC
        published = published.replace('+00:00', 'Z')
        # Add Z if missing
        if not published.endswith('Z'):
            published = published + 'Z'
    
    # Get current time in proper format (NO microseconds for Weaviate date type)
    ingested = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    
    return {
        "threatId": f"threat_{threat_id}",
        "title": title,
        "content": content[:5000],  # Limit size
        "source": source,  # Now always a string
        "sourceUrl": item.get('link', ''),
        "severity": severity,
        "threatType": threat_types or ['unknown'],
        "threatActors": actors,
        "cves": cves,
        "publishedDate": published,  # RFC3339 format with Z
        "ingestedDate": ingested,  # RFC3339 format with Z
        "tags": item.get('tags', [])
    }


async def main():
    print("="*60)
    print("🔥 REDIS-FIRST INGESTION")
    print("All threats → Redis Hub → Workers decide routing")
    print("="*60)
    print()
    
    # Connect to Redis (using alternate port 6380 to avoid conflicts)
    print("📡 Connecting to Redis...")
    redis_port = 6380  # Using 6380 to avoid conflict with other Redis instances
    redis_client = await redis.from_url(
        f"redis://localhost:{redis_port}",
        password="cyber-pi-redis-2025",
        encoding="utf-8",
        decode_responses=True
    )
    
    try:
        await redis_client.ping()
        print("✅ Connected to Redis")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("\nStart port forward:")
        print("  microk8s kubectl port-forward -n cyber-pi-intel svc/redis 6379:6379")
        return 1
    
    print()
    
    # Initialize Redis Hub
    hub = RedisHub(redis_client)
    
    # Load threats
    filepath = "/home/david/projects/cyber-pi/data/raw/master_collection_20251031_014039.json"
    print(f"📁 Loading: {filepath}")
    
    with open(filepath) as f:
        data = json.load(f)
    
    items = data['items']
    print(f"📊 Found {len(items)} threats")
    print()
    
    # Ingest to Redis
    print("🚀 Ingesting to Redis Hub...")
    success = 0
    failed = 0
    
    for i, item in enumerate(items):
        if (i + 1) % 100 == 0:
            print(f"  Progress: {i+1}/{len(items)} ({(i+1)/len(items)*100:.1f}%)")
        
        try:
            # Parse
            parsed = parse_cyber_pi_threat(item)
            
            # Ingest raw to Redis
            threat_id = await hub.ingest_raw_threat(parsed)
            
            # Mark as parsed (triggers routing)
            await hub.mark_parsed(threat_id, parsed)
            
            success += 1
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            failed += 1
    
    print()
    
    # Get queue stats
    stats = await hub.get_queue_stats()
    
    print("="*60)
    print("📊 INGESTION COMPLETE")
    print("="*60)
    print(f"Total threats:    {len(items)}")
    print(f"Success:          {success}")
    print(f"Failed:           {failed}")
    print(f"Success rate:     {success/len(items)*100:.1f}%")
    print()
    print("📋 Queue Status:")
    print(f"  Weaviate queue:   {stats['weaviate_queue']} threats")
    print(f"  Neo4j queue:      {stats['neo4j_queue']} threats (high/critical)")
    print(f"  STIX export:      {stats['stix_export_queue']} threats (APT/ransomware)")
    print(f"  Intake stream:    {stats['intake_stream_length']} events")
    print(f"  Parsed stream:    {stats['parsed_stream_length']} events")
    print()
    print("✅ All threats in Redis!")
    print()
    print("Next steps:")
    print("  1. Run Weaviate worker to process weaviate_queue")
    print("  2. Run Neo4j worker to process neo4j_queue")
    print("  3. Run STIX worker to process stix_export_queue")
    print()
    
    await redis_client.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
