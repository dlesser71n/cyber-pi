#!/usr/bin/env python3
"""
CISA Known Exploited Vulnerabilities (KEV) Collector
Automated collection from CISA's KEV catalog
"""

import asyncio
import json
import os
import httpx
from datetime import datetime, timezone
import hashlib
import redis.asyncio as redis

# CISA KEV API
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

async def collect_kev():
    """Collect from CISA KEV catalog"""
    print("="*60)
    print("🔒 CISA KEV COLLECTOR")
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

    # Fetch KEV catalog
    print(f"📡 Fetching from: {KEV_URL}")
    async with httpx.AsyncClient() as client:
        response = await client.get(KEV_URL, timeout=30.0)
        response.raise_for_status()
        data = response.json()

    vulnerabilities = data.get('vulnerabilities', [])
    print(f"📊 Found {len(vulnerabilities)} KEV entries")

    # Process each vulnerability
    queued = 0
    updated = 0

    for vuln in vulnerabilities:
        cve_id = vuln.get('cveID', '')
        if not cve_id:
            continue

        # Create threat ID
        threat_id = f"threat_{hashlib.sha256(cve_id.encode()).hexdigest()[:16]}"

        # Check if already processed recently
        existing = await redis_client.get(f"threat:parsed:{threat_id}")
        if existing:
            updated += 1
            continue

        # Build threat data
        threat_data = {
            "threatId": threat_id,
            "title": f"CISA KEV: {cve_id} - {vuln.get('vulnerabilityName', 'Unknown')}",
            "content": f"""
CISA Known Exploited Vulnerability

CVE: {cve_id}
Vendor: {vuln.get('vendorProject', 'Unknown')}
Product: {vuln.get('product', 'Unknown')}
Vulnerability: {vuln.get('vulnerabilityName', 'Unknown')}
Date Added: {vuln.get('dateAdded', '')}
Due Date: {vuln.get('dueDate', '')}

Required Action: {vuln.get('requiredAction', 'Unknown')}

Known Ransomware: {vuln.get('knownRansomwareCampaignUse', 'Unknown')}

Notes: {vuln.get('notes', 'None')}
            """.strip(),
            "source": "CISA KEV Catalog",
            "sourceUrl": f"https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
            "industry": ["Critical Infrastructure", "Government"],
            "severity": "critical",  # All KEV are critical by definition
            "threatType": ["vulnerability", "exploit"],
            "threatActors": [],
            "cves": [cve_id],
            "publishedDate": vuln.get('dateAdded', datetime.now(timezone.utc).isoformat()),
            "ingestedDate": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "vendor": vuln.get('vendorProject'),
                "product": vuln.get('product'),
                "ransomware_used": vuln.get('knownRansomwareCampaignUse'),
                "due_date": vuln.get('dueDate'),
                "source": "cisa_kev"
            }
        }

        # Store in Redis
        await redis_client.setex(
            f"threat:parsed:{threat_id}",
            86400 * 7,  # 7 day TTL for KEV
            json.dumps(threat_data)
        )

        # Queue for storage workers
        await redis_client.lpush("queue:weaviate", threat_id)
        await redis_client.lpush("queue:neo4j", threat_id)

        queued += 1

        if queued % 100 == 0:
            print(f"  Progress: {queued}/{len(vulnerabilities)}")

    print()
    print(f"✅ Collection complete!")
    print(f"   New threats: {queued}")
    print(f"   Already tracked: {updated}")
    print(f"   Total in KEV: {len(vulnerabilities)}")

    await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(collect_kev())
