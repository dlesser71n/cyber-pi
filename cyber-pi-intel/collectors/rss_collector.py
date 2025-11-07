#!/usr/bin/env python3
"""
RSS Feed Collector
Automated collection from security RSS feeds
"""

import asyncio
import json
import os
import hashlib
from datetime import datetime, timezone
import feedparser
import redis.asyncio as redis

# RSS Feed Sources
RSS_FEEDS = [
    {
        "name": "Krebs on Security",
        "url": "https://krebsonsecurity.com/feed/",
        "category": "news_research",
        "priority": "high"
    },
    {
        "name": "The Hacker News",
        "url": "https://feeds.feedburner.com/TheHackersNews",
        "category": "news",
        "priority": "high"
    },
    {
        "name": "Bleeping Computer",
        "url": "https://www.bleepingcomputer.com/feed/",
        "category": "news",
        "priority": "medium"
    },
    {
        "name": "Threatpost",
        "url": "https://threatpost.com/feed/",
        "category": "news",
        "priority": "medium"
    },
    {
        "name": "US-CERT Current Activity",
        "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml",
        "category": "government",
        "priority": "critical"
    }
]

async def collect_rss():
    """Collect from RSS feeds"""
    print("="*60)
    print("📰 RSS FEED COLLECTOR")
    print("="*60)
    print()

    # Connect to Redis (from Kubernetes secrets)
    redis_password = os.getenv('REDIS_PASSWORD', '')
    redis_host = os.getenv('REDIS_HOST', 'redis.cyber-pi-intel.svc.cluster.local')
    redis_port = os.getenv('REDIS_PORT', '6379')
    redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"

    redis_client = await redis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    await redis_client.ping()
    print("✅ Connected to Redis")
    print()

    total_collected = 0
    total_new = 0

    for feed_config in RSS_FEEDS:
        print(f"📡 Fetching: {feed_config['name']}")

        try:
            # Parse RSS feed
            feed = feedparser.parse(feed_config['url'])

            if not feed.entries:
                print(f"   ⚠️  No entries found")
                continue

            print(f"   Found {len(feed.entries)} entries")

            new_items = 0
            for entry in feed.entries:
                # Generate threat ID from title + link
                id_str = entry.get('title', '') + entry.get('link', '')
                threat_id = f"threat_{hashlib.sha256(id_str.encode()).hexdigest()[:16]}"

                # Check if already exists
                existing = await redis_client.get(f"threat:parsed:{threat_id}")
                if existing:
                    continue

                # Extract published date
                published = entry.get('published_parsed')
                if published:
                    published_date = datetime(*published[:6], tzinfo=timezone.utc).isoformat()
                else:
                    published_date = datetime.now(timezone.utc).isoformat()

                # Build threat data
                threat_data = {
                    "threatId": threat_id,
                    "title": entry.get('title', 'Unknown')[:500],
                    "content": entry.get('summary', entry.get('description', ''))[:10000],
                    "source": feed_config['name'],
                    "sourceUrl": entry.get('link', ''),
                    "industry": [feed_config['category']],
                    "severity": "medium",  # Default, can be enriched later
                    "threatType": [],
                    "threatActors": [],
                    "cves": [],
                    "publishedDate": published_date,
                    "ingestedDate": datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "feed_priority": feed_config['priority'],
                        "source_type": "rss",
                        "category": feed_config['category']
                    }
                }

                # Store in Redis
                await redis_client.setex(
                    f"threat:parsed:{threat_id}",
                    86400 * 3,  # 3 day TTL for RSS
                    json.dumps(threat_data)
                )

                # Queue for storage workers
                await redis_client.lpush("queue:weaviate", threat_id)
                await redis_client.lpush("queue:neo4j", threat_id)

                new_items += 1
                total_new += 1

            print(f"   ✅ Collected {new_items} new items")
            total_collected += len(feed.entries)

        except Exception as e:
            print(f"   ❌ Error: {e}")

        print()

    print(f"✅ RSS collection complete!")
    print(f"   Total items processed: {total_collected}")
    print(f"   New threats collected: {total_new}")

    await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(collect_rss())
