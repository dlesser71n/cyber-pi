#!/usr/bin/env python3
"""
IBKR Financial Intelligence Client Collector

This collector calls the standalone IBKR Financial Intelligence microservice
and pushes cyber-relevant financial news to the Redis highway.

Architecture:
  IBKR Service (REST API) → This Collector → Redis → Workers → Neo4j/Weaviate

Rickover Principle: Separation of concerns - this is just a client, IBKR service handles complexity.
"""

import asyncio
import json
import os
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any
import httpx
import redis.asyncio as redis


# IBKR Service Configuration
IBKR_SERVICE_URL = os.getenv('IBKR_SERVICE_URL', 'http://localhost:8000')
IBKR_API_KEY = os.getenv('IBKR_API_KEY', 'dev-key-change-in-production')

# Redis Configuration (from K8s secrets)
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis.cyber-pi-intel.svc.cluster.local')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"

# Cyber-security keywords for filtering
CYBER_KEYWORDS = [
    'breach', 'hacked', 'ransomware', 'cyberattack', 'cyber attack',
    'data leak', 'vulnerability', 'zero-day', 'exploit', 'malware',
    'phishing', 'ddos', 'denial of service', 'security incident',
    'unauthorized access', 'data theft', 'compromised', 'intrusion',
    'data breach', 'security breach', 'hack', 'stolen data'
]


async def collect_ibkr_financial_intel():
    """
    Collect financial intelligence from IBKR service.

    Rickover Principle: Simple, focused, single-purpose function.
    """
    print("="*60)
    print("💰 IBKR FINANCIAL INTELLIGENCE CLIENT COLLECTOR")
    print("="*60)
    print()

    # Connect to Redis
    try:
        redis_client = await redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        print("✅ Connected to Redis highway")
        print()
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        return

    # Create HTTP client
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Check IBKR service health
            print(f"🔍 Checking IBKR service: {IBKR_SERVICE_URL}")
            health_response = await client.get(
                f"{IBKR_SERVICE_URL}/health"
            )

            if health_response.status_code != 200:
                print(f"❌ IBKR service unhealthy: {health_response.status_code}")
                return

            health = health_response.json()
            print(f"✅ IBKR service: {health['status']}")
            print(f"   Connected to Gateway: {health['ibkr_connected']}")
            print(f"   News providers: {health['news_providers_count']}")
            print()

            # Collect cyber-relevant news
            print("📰 Collecting cyber-relevant financial news...")
            news_response = await client.post(
                f"{IBKR_SERVICE_URL}/api/v1/news/filter",
                json={
                    "keywords": CYBER_KEYWORDS,
                    "providers": None,  # Use default providers (BRFG, BRFUPDN, DJNL)
                    "time_range_hours": 1,  # Last hour (called frequently)
                    "limit": 100
                },
                headers={"X-API-Key": IBKR_API_KEY}
            )

            if news_response.status_code != 200:
                print(f"❌ Failed to get news: {news_response.status_code}")
                print(f"   Error: {news_response.text}")
                return

            news_data = news_response.json()
            articles = news_data["articles"]
            print(f"✅ Received {len(articles)} cyber-relevant articles")
            print()

            # Convert to standard threat format and push to Redis
            if articles:
                print("🚀 Pushing to Redis highway...")
                queued_count = 0

                for article in articles:
                    threat_data = await convert_to_threat_format(article)

                    # Check if already exists
                    threat_id = threat_data["threatId"]
                    existing = await redis_client.get(f"threat:parsed:{threat_id}")
                    if existing:
                        continue

                    # Store in Redis (threat:parsed key)
                    await redis_client.setex(
                        f"threat:parsed:{threat_id}",
                        86400 * 7,  # 7 day TTL
                        json.dumps(threat_data)
                    )

                    # Queue for Weaviate
                    await redis_client.lpush("queue:weaviate", threat_id)

                    # Queue for Neo4j
                    await redis_client.lpush("queue:neo4j", threat_id)

                    queued_count += 1
                    print(f"   ✓ {article['headline'][:80]}...")

                print()
                print(f"✅ Queued {queued_count} new items to Redis highway")
                print()

            else:
                print("ℹ️  No cyber-relevant financial news in the last hour")
                print("   (This is normal - security incidents are rare)")
                print()

        except httpx.ConnectError:
            print(f"❌ Cannot connect to IBKR service at {IBKR_SERVICE_URL}")
            print("   Is the IBKR service running?")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await redis_client.aclose()

    print("="*60)
    print("✅ Collection complete")
    print("="*60)


async def convert_to_threat_format(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert IBKR article to standard Cyber-PI threat format.

    Rickover Principle: Data standardization is critical for integration.

    Args:
        article: Article from IBKR service

    Returns:
        Threat data in standard format
    """
    # Generate consistent threat ID
    id_str = f"ibkr_{article['provider_code']}_{article['article_id']}"
    threat_id = f"threat_{hashlib.sha256(id_str.encode()).hexdigest()[:16]}"

    # Determine severity based on content
    severity = "medium"
    headline_lower = article['headline'].lower()
    if any(word in headline_lower for word in ['breach', 'ransomware', 'compromised']):
        severity = "high"
    if any(word in headline_lower for word in ['zero-day', 'critical', 'emergency']):
        severity = "critical"

    # Build threat data
    threat_data = {
        "threatId": threat_id,
        "title": f"IBKR Financial Alert: {article['headline'][:200]}",
        "content": article.get('body', article['headline']),
        "source": f"IBKR - {article['provider_code']}",
        "sourceUrl": f"{IBKR_SERVICE_URL}/api/v1/news/providers",  # Service endpoint
        "industry": ["financial", "technology"],
        "severity": severity,
        "threatType": ["financial_indicator"],
        "threatActors": [],
        "cves": [],
        "publishedDate": article['timestamp'],
        "ingestedDate": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "source_type": "ibkr_financial",
            "provider_code": article['provider_code'],
            "article_id": article['article_id'],
            "symbols": article.get('symbols', []),
            "sentiment": article.get('sentiment')
        }
    }

    return threat_data


if __name__ == "__main__":
    asyncio.run(collect_ibkr_financial_intel())
