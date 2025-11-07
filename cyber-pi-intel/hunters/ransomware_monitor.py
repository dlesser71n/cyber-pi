#!/usr/bin/env python3
"""
Automated Ransomware Monitor
Detects ransomware campaigns and generates immediate alerts
"""

import asyncio
import json
from datetime import datetime, timezone
import redis.asyncio as redis
from neo4j import GraphDatabase

# Ransomware families to track
RANSOMWARE_FAMILIES = [
    'lockbit', 'qilin', 'alphv', 'blackcat', 'royal',
    'play', 'cl0p', 'akira', 'black basta', 'bianlian'
]

async def monitor_ransomware():
    """Monitor for ransomware threats"""
    print("="*60)
    print("🔒 RANSOMWARE MONITOR")
    print("="*60)
    print()

    # Connect to Neo4j
    driver = GraphDatabase.driver(
        "bolt://neo4j.cyber-pi-intel.svc.cluster.local:7687",
        auth=("neo4j", "cyber-pi-neo4j-2025")
    )

    # Connect to Redis
    redis_client = await redis.from_url(
        "redis://:cyber-pi-redis-2025@redis.cyber-pi-intel.svc.cluster.local:6379",
        encoding="utf-8",
        decode_responses=True
    )

    print("✅ Connected to databases")
    print()

    # Query for ransomware threats
    query = """
    MATCH (t:CyberThreat)
    WHERE toLower(t.title) CONTAINS 'ransomware'
       OR toLower(t.title) CONTAINS 'lockbit'
       OR toLower(t.title) CONTAINS 'encryption'
    RETURN
        t.threatId as id,
        t.title as title,
        t.source as source,
        t.severity as severity,
        t.publishedDate as published
    ORDER BY t.publishedDate DESC
    LIMIT 50
    """

    with driver.session() as session:
        result = session.run(query)
        threats = [dict(record) for record in result]

    print(f"📊 Found {len(threats)} ransomware-related threats\n")

    # Alert on new ransomware campaigns
    new_campaigns = []

    for threat in threats:
        threat_id = threat['id']

        # Check if already alerted
        alerted = await redis_client.get(f"ransomware:alerted:{threat_id}")
        if alerted:
            continue

        # New ransomware campaign!
        new_campaigns.append(threat)

        # Mark as alerted
        await redis_client.setex(
            f"ransomware:alerted:{threat_id}",
            86400 * 30,
            json.dumps({
                "threat_id": threat_id,
                "alerted_at": datetime.now(timezone.utc).isoformat(),
                "category": "ransomware"
            })
        )

        # Generate high-priority alert
        alert = {
            "type": "ransomware_campaign",
            "severity": "critical",
            "threat_id": threat_id,
            "title": threat['title'],
            "source": threat['source'],
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "recommendations": [
                "Verify offline backups are current",
                "Check for indicators of compromise",
                "Review network segmentation",
                "Enable MFA on admin accounts",
                "Update EDR signatures"
            ]
        }

        await redis_client.lpush("queue:alerts", json.dumps(alert))

    print(f"🚨 NEW RANSOMWARE CAMPAIGNS: {len(new_campaigns)}")
    print()

    for i, threat in enumerate(new_campaigns, 1):
        print(f"{i}. {threat['title'][:70]}")
        print(f"   Source: {threat['source']}")
        print()

    if not new_campaigns:
        print("✅ No new ransomware campaigns detected")
        print()

    # Trend analysis
    print("📈 Ransomware Trend Analysis...")
    trend_query = """
    MATCH (t:CyberThreat)
    WHERE toLower(t.title) CONTAINS 'ransomware'
    RETURN
        count(t) as total,
        collect(DISTINCT t.source)[..5] as top_sources
    """

    with driver.session() as session:
        result = session.run(trend_query)
        trends = result.single()

    if trends:
        print(f"\n   Total ransomware threats: {trends['total']}")
        print(f"   Top sources: {', '.join(trends['top_sources'])}")

    print()
    print(f"📊 Summary:")
    print(f"   Ransomware threats tracked: {len(threats)}")
    print(f"   New alerts generated: {len(new_campaigns)}")
    print(f"   Alert queue: queue:alerts")

    driver.close()
    await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(monitor_ransomware())
