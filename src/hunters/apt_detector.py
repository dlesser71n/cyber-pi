#!/usr/bin/env python3
"""
Automated APT Detector
Detects Advanced Persistent Threat group activity
"""

import asyncio
import json
from datetime import datetime, timezone
import redis.asyncio as redis
from neo4j import GraphDatabase

# Known APT groups and indicators
APT_INDICATORS = {
    'apt_groups': [
        'apt', 'lazarus', 'apt28', 'apt29', 'apt36',
        'cozy bear', 'fancy bear', 'bluenoroff',
        'passivenuron', 'thewizards'
    ],
    'techniques': [
        'spear phishing', 'watering hole', 'supply chain',
        'living off the land', 'lateral movement',
        'credential dumping', 'persistence mechanism'
    ]
}

async def detect_apt():
    """Detect APT activity"""
    print("="*60)
    print("🎯 APT DETECTOR")
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

    # Query for APT activity
    query = """
    MATCH (t:CyberThreat)
    WHERE toLower(t.title) CONTAINS 'apt'
       OR toLower(t.title) CONTAINS 'lazarus'
       OR toLower(t.title) CONTAINS 'advanced persistent'
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

    print(f"📊 Found {len(threats)} APT-related threats\n")

    # Analyze and alert on new APT activity
    new_apt_activity = []

    for threat in threats:
        threat_id = threat['id']

        # Check if already analyzed
        analyzed = await redis_client.get(f"apt:analyzed:{threat_id}")
        if analyzed:
            continue

        # New APT activity!
        new_apt_activity.append(threat)

        # Mark as analyzed
        await redis_client.setex(
            f"apt:analyzed:{threat_id}",
            86400 * 30,
            json.dumps({
                "threat_id": threat_id,
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
                "category": "apt"
            })
        )

        # Generate alert
        alert = {
            "type": "apt_activity",
            "severity": "high",
            "threat_id": threat_id,
            "title": threat['title'],
            "source": threat['source'],
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "recommendation": "Review network logs for indicators of compromise"
        }

        await redis_client.lpush("queue:alerts", json.dumps(alert))

    print(f"🚨 NEW APT ACTIVITY: {len(new_apt_activity)}")
    print()

    for i, threat in enumerate(new_apt_activity, 1):
        print(f"{i}. {threat['title'][:70]}")
        print(f"   Source: {threat['source']}")
        print()

    if not new_apt_activity:
        print("✅ No new APT activity detected")
        print()

    # Campaign correlation
    print("🔗 Correlating APT campaigns...")
    campaign_query = """
    MATCH (t:CyberThreat)
    WHERE toLower(t.title) CONTAINS 'apt'
    WITH t.source as source, count(t) as threat_count
    WHERE threat_count > 1
    RETURN source, threat_count
    ORDER BY threat_count DESC
    LIMIT 10
    """

    with driver.session() as session:
        result = session.run(campaign_query)
        campaigns = [dict(record) for record in result]

    if campaigns:
        print("\n📈 APT Campaign Sources:")
        for camp in campaigns:
            print(f"   {camp['source']}: {camp['threat_count']} related threats")

    print()
    print(f"📊 Summary:")
    print(f"   Total APT threats tracked: {len(threats)}")
    print(f"   New alerts generated: {len(new_apt_activity)}")

    driver.close()
    await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(detect_apt())
