#!/usr/bin/env python3
"""
Automated Zero-Day Hunter
Continuously scans for zero-day vulnerabilities and active exploits
"""

import asyncio
import json
from datetime import datetime, timezone
import redis.asyncio as redis
from neo4j import GraphDatabase

# Detection keywords for zero-days
ZERO_DAY_KEYWORDS = [
    'zero-day', '0-day', 'zero day',
    'actively exploited', 'active exploitation',
    'in the wild', 'under attack',
    'emergency patch', 'urgent update'
]

async def hunt_zero_days():
    """Hunt for zero-day threats"""
    print("="*60)
    print("🔍 ZERO-DAY HUNTER")
    print("="*60)
    print()

    # Connect to Neo4j
    driver = GraphDatabase.driver(
        "bolt://neo4j.cyber-pi-intel.svc.cluster.local:7687",
        auth=("neo4j", "cyber-pi-neo4j-2025")
    )

    # Connect to Redis for alerting
    redis_client = await redis.from_url(
        "redis://:cyber-pi-redis-2025@redis.cyber-pi-intel.svc.cluster.local:6379",
        encoding="utf-8",
        decode_responses=True
    )

    print("✅ Connected to databases")
    print()

    # Query for zero-days
    query = """
    MATCH (t:CyberThreat)
    WHERE toLower(t.title) CONTAINS 'zero-day'
       OR toLower(t.title) CONTAINS '0-day'
       OR toLower(t.title) CONTAINS 'actively exploited'
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

    print(f"📊 Found {len(threats)} potential zero-days\n")

    # Check which are new (not alerted before)
    alerts_to_send = []

    for threat in threats:
        threat_id = threat['id']

        # Check if already alerted
        alerted = await redis_client.get(f"alert:sent:{threat_id}")
        if alerted:
            continue

        # New zero-day detected!
        alerts_to_send.append(threat)

        # Mark as alerted
        await redis_client.setex(
            f"alert:sent:{threat_id}",
            86400 * 30,  # 30 day TTL
            json.dumps({
                "threat_id": threat_id,
                "alerted_at": datetime.now(timezone.utc).isoformat(),
                "alert_type": "zero_day"
            })
        )

        # Queue alert
        alert = {
            "type": "zero_day",
            "severity": "critical",
            "threat_id": threat_id,
            "title": threat['title'],
            "source": threat['source'],
            "detected_at": datetime.now(timezone.utc).isoformat()
        }

        await redis_client.lpush("queue:alerts", json.dumps(alert))

    print(f"🚨 NEW ZERO-DAYS DETECTED: {len(alerts_to_send)}")
    print()

    for i, threat in enumerate(alerts_to_send, 1):
        print(f"{i}. {threat['title'][:70]}")
        print(f"   Source: {threat['source']}")
        print(f"   Severity: {threat['severity']}")
        print()

    if not alerts_to_send:
        print("✅ No new zero-days detected (all previously seen)")
        print()

    # Summary
    print(f"📈 Summary:")
    print(f"   Total zero-days tracked: {len(threats)}")
    print(f"   New alerts generated: {len(alerts_to_send)}")
    print(f"   Alerts queued: queue:alerts")

    driver.close()
    await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(hunt_zero_days())
