#!/usr/bin/env python3
"""
CISA KEV Critical Monitor
Monitors CISA Known Exploited Vulnerabilities for new additions
These are federally-mandated patches - immediate action required
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
import redis.asyncio as redis
from neo4j import GraphDatabase

async def monitor_cisa_kev():
    """Monitor CISA KEV for new critical vulnerabilities"""
    print("="*60)
    print("🔒 CISA KEV CRITICAL MONITOR")
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

    # Query for CISA KEV threats
    query = """
    MATCH (t:CyberThreat)
    WHERE t.source CONTAINS 'CISA KEV'
    RETURN
        t.threatId as id,
        t.title as title,
        t.content as content,
        t.severity as severity,
        t.publishedDate as published,
        t.ingestedDate as ingested
    ORDER BY t.ingestedDate DESC
    """

    with driver.session() as session:
        result = session.run(query)
        threats = [dict(record) for record in result]

    print(f"📊 Total CISA KEV vulnerabilities tracked: {len(threats)}\n")

    # Find new KEV entries (added in last 24 hours)
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    new_kevs = [t for t in threats if t['ingested'] and t['ingested'] > cutoff]

    print(f"🆕 KEV entries added in last 24h: {len(new_kevs)}")
    print()

    # Generate critical alerts for new KEVs
    alerts_generated = 0

    for threat in new_kevs:
        threat_id = threat['id']

        # Check if already alerted
        alerted = await redis_client.get(f"kev:alerted:{threat_id}")
        if alerted:
            continue

        # Extract CVE from title
        cve = "Unknown"
        if "CVE-" in threat['title']:
            cve = threat['title'].split("CVE-")[1].split()[0]
            cve = f"CVE-{cve}"

        # Generate CRITICAL alert
        alert = {
            "type": "cisa_kev",
            "severity": "critical",
            "priority": "P1",
            "threat_id": threat_id,
            "cve": cve,
            "title": threat['title'],
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "federal_mandate": True,
            "action_required": "IMMEDIATE PATCHING REQUIRED",
            "recommendations": [
                f"Patch {cve} IMMEDIATELY",
                "This is a federally-mandated patch (BOD 22-01)",
                "Known to be actively exploited",
                "Review systems for indicators of compromise",
                "Report patching status to leadership"
            ]
        }

        await redis_client.lpush("queue:alerts", json.dumps(alert))

        # Mark as alerted
        await redis_client.setex(
            f"kev:alerted:{threat_id}",
            86400 * 90,  # 90 day TTL for KEV
            json.dumps({
                "threat_id": threat_id,
                "cve": cve,
                "alerted_at": datetime.now(timezone.utc).isoformat()
            })
        )

        alerts_generated += 1

        print(f"🚨 CRITICAL ALERT: {cve}")
        print(f"   {threat['title'][:80]}")
        print()

    if alerts_generated == 0:
        print("✅ No new KEV entries requiring alerts")
        print()

    # Show oldest unpatched KEVs (high risk)
    print("⚠️  Oldest KEV Entries (Highest Risk):")
    oldest_query = """
    MATCH (t:CyberThreat)
    WHERE t.source CONTAINS 'CISA KEV'
    RETURN t.title as title, t.publishedDate as published
    ORDER BY t.publishedDate ASC
    LIMIT 5
    """

    with driver.session() as session:
        result = session.run(oldest_query)
        oldest = [dict(record) for record in result]

    for threat in oldest:
        print(f"   {threat['title'][:70]}")
        print(f"   Published: {threat['published']}")
        print()

    print(f"📊 Summary:")
    print(f"   Total KEV tracked: {len(threats)}")
    print(f"   New KEV (24h): {len(new_kevs)}")
    print(f"   Critical alerts generated: {alerts_generated}")
    print(f"   Federal mandate compliance: Required")

    driver.close()
    await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(monitor_cisa_kev())
