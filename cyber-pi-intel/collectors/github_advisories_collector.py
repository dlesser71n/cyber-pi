#!/usr/bin/env python3
"""
GitHub Security Advisories Collector
Automated collection from GitHub's security advisory database
"""

import asyncio
import json
import hashlib
from datetime import datetime, timezone
import httpx
import redis.asyncio as redis

# GitHub GraphQL API
GITHUB_API = "https://api.github.com/graphql"

# GraphQL query for security advisories
ADVISORIES_QUERY = """
query {
  securityAdvisories(first: 100, orderBy: {field: PUBLISHED_AT, direction: DESC}) {
    nodes {
      ghsaId
      summary
      description
      severity
      publishedAt
      updatedAt
      withdrawnAt
      permalink
      cvss {
        score
        vectorString
      }
      cwes(first: 5) {
        nodes {
          cweId
          description
        }
      }
      identifiers {
        type
        value
      }
      references {
        url
      }
      vulnerabilities(first: 10) {
        nodes {
          package {
            name
            ecosystem
          }
          vulnerableVersionRange
          firstPatchedVersion {
            identifier
          }
        }
      }
    }
  }
}
"""

async def collect_github_advisories():
    """Collect from GitHub Security Advisories"""
    print("="*60)
    print("🐙 GITHUB SECURITY ADVISORIES COLLECTOR")
    print("="*60)
    print()

    # Note: In production, use GitHub token from secrets
    # For now, using unauthenticated (rate limited to 60/hour)
    headers = {
        "Content-Type": "application/json"
        # "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
    }

    # Connect to Redis
    redis_client = await redis.from_url(
        "redis://:cyber-pi-redis-2025@redis.cyber-pi-intel.svc.cluster.local:6379",
        encoding="utf-8",
        decode_responses=True
    )
    await redis_client.ping()
    print("✅ Connected to Redis")

    # Fetch advisories
    print(f"📡 Fetching from GitHub GraphQL API...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GITHUB_API,
                headers=headers,
                json={"query": ADVISORIES_QUERY},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

        if 'errors' in data:
            print(f"❌ API Error: {data['errors']}")
            print("   Note: GitHub requires authentication token for full access")
            print("   Using authenticated API recommended for production")
            return

        advisories = data.get('data', {}).get('securityAdvisories', {}).get('nodes', [])
        print(f"📊 Found {len(advisories)} advisories")
        print()

        queued = 0
        updated = 0

        for advisory in advisories:
            ghsa_id = advisory.get('ghsaId', '')
            if not ghsa_id:
                continue

            # Create threat ID
            threat_id = f"threat_{hashlib.sha256(ghsa_id.encode()).hexdigest()[:16]}"

            # Check if already processed
            existing = await redis_client.get(f"threat:parsed:{threat_id}")
            if existing:
                updated += 1
                continue

            # Extract CVEs
            cves = [
                ident['value']
                for ident in advisory.get('identifiers', [])
                if ident.get('type') == 'CVE'
            ]

            # Extract CWEs
            cwes = [
                cwe.get('cweId')
                for cwe in advisory.get('cwes', {}).get('nodes', [])
            ]

            # Extract affected packages
            packages = []
            for vuln in advisory.get('vulnerabilities', {}).get('nodes', []):
                pkg = vuln.get('package', {})
                packages.append(f"{pkg.get('ecosystem')}/{pkg.get('name')}")

            # Map GitHub severity to our scale
            severity_map = {
                'LOW': 'low',
                'MODERATE': 'medium',
                'HIGH': 'high',
                'CRITICAL': 'critical'
            }
            severity = severity_map.get(advisory.get('severity', 'MODERATE'), 'medium')

            # Build content
            content = f"""
{advisory.get('summary', 'Unknown')}

{advisory.get('description', '')}

Severity: {advisory.get('severity', 'Unknown')}
CVSS Score: {advisory.get('cvss', {}).get('score', 'N/A')}

Affected Packages:
{chr(10).join(f'  - {pkg}' for pkg in packages)}

References:
{chr(10).join(f'  - {ref.get("url")}' for ref in advisory.get('references', []))}
            """.strip()

            # Build threat data
            threat_data = {
                "threatId": threat_id,
                "title": f"GitHub Advisory: {ghsa_id} - {advisory.get('summary', 'Unknown')[:200]}",
                "content": content[:10000],
                "source": "GitHub Security Advisories",
                "sourceUrl": advisory.get('permalink', ''),
                "industry": ["Technology", "Software Development"],
                "severity": severity,
                "threatType": ["vulnerability"],
                "threatActors": [],
                "cves": cves,
                "publishedDate": advisory.get('publishedAt', datetime.now(timezone.utc).isoformat()),
                "ingestedDate": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "ghsa_id": ghsa_id,
                    "cvss_score": advisory.get('cvss', {}).get('score'),
                    "cvss_vector": advisory.get('cvss', {}).get('vectorString'),
                    "cwes": cwes,
                    "affected_packages": packages,
                    "source": "github_advisories"
                }
            }

            # Store in Redis
            await redis_client.setex(
                f"threat:parsed:{threat_id}",
                86400 * 7,  # 7 day TTL
                json.dumps(threat_data)
            )

            # Queue for storage workers
            await redis_client.lpush("queue:weaviate", threat_id)
            await redis_client.lpush("queue:neo4j", threat_id)

            queued += 1

        print(f"✅ Collection complete!")
        print(f"   New advisories: {queued}")
        print(f"   Already tracked: {updated}")
        print(f"   Total processed: {len(advisories)}")

    except Exception as e:
        print(f"❌ Error: {e}")

    await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(collect_github_advisories())
