#!/usr/bin/env python3
"""
Quick test script for TQAKB V4 API
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_api():
    """Test basic API endpoints"""
    async with httpx.AsyncClient() as client:
        print("Testing TQAKB V4 API...")
        print("-" * 50)
        
        # Test root endpoint
        print("1. Testing root endpoint...")
        response = await client.get(f"{BASE_URL}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        print()
        
        # Test health check
        print("2. Testing health check...")
        response = await client.get(f"{BASE_URL}/api/health/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        print()
        
        # Test service health
        print("3. Testing service health...")
        response = await client.get(f"{BASE_URL}/api/health/services")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        print()
        
        # Test knowledge ingestion
        print("4. Testing knowledge ingestion...")
        knowledge_event = {
            "type": "knowledge.raw",
            "source": "api",
            "content": {
                "subject": "TQAKB V4",
                "predicate": "is",
                "object": "event-driven knowledge system",
                "context": "technology"
            }
        }
        response = await client.post(
            f"{BASE_URL}/api/knowledge/ingest",
            json=knowledge_event
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        print()
        
        # Test search
        print("5. Testing search...")
        query_event = {
            "type": "knowledge.query",
            "source": "api",
            "content": {
                "query": "TQAKB",
                "limit": 5
            }
        }
        response = await client.post(
            f"{BASE_URL}/api/search/",
            json=query_event
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        print()
        
        # Test admin config
        print("6. Testing admin config...")
        response = await client.get(f"{BASE_URL}/api/admin/config")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        print()
        
        print("-" * 50)
        print("API tests completed!")

if __name__ == "__main__":
    asyncio.run(test_api())