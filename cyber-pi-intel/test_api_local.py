#!/usr/bin/env python3
"""
Test the Backend API locally before K8s deployment
"""

import sys
import os

# Set environment for external access
os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6380'
os.environ['WEAVIATE_HOST'] = 'localhost'
os.environ['WEAVIATE_PORT'] = '8080'
os.environ['NEO4J_URI'] = 'bolt://localhost:7687'

# Override connections for local testing
import redis
import weaviate
from neo4j import GraphDatabase

# Test connections
print("🔍 Testing database connections...")

# Redis
try:
    redis_client = redis.Redis(
        host='localhost',
        port=6380,
        password='cyber-pi-redis-2025',
        decode_responses=True
    )
    redis_client.ping()
    print("✅ Redis: Connected")
except Exception as e:
    print(f"❌ Redis: Failed - {e}")

# Weaviate
try:
    weaviate_client = weaviate.connect_to_custom(
        http_host="localhost",
        http_port=8080,
        http_secure=False,
        grpc_host="localhost",
        grpc_port=50051,
        grpc_secure=False
    )
    weaviate_client.is_ready()
    print("✅ Weaviate: Connected")
    weaviate_client.close()
except Exception as e:
    print(f"❌ Weaviate: Failed - {e}")

# Neo4j
try:
    neo4j_driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "cyber-pi-neo4j-2025")
    )
    with neo4j_driver.session() as session:
        result = session.run("RETURN 1")
        result.single()
    print("✅ Neo4j: Connected")
    neo4j_driver.close()
except Exception as e:
    print(f"❌ Neo4j: Failed - {e}")

print("\n🚀 Starting API server...")
print("📍 API will be available at: http://localhost:8000")
print("📍 Docs available at: http://localhost:8000/docs")
print("\nPress Ctrl+C to stop\n")

# Patch the API to use localhost connections
import backend.api.threat_intel_api as api_module

# Override database connections for local testing
api_module.redis_client = redis.Redis(
    host='localhost',
    port=6380,
    password='cyber-pi-redis-2025',
    decode_responses=True
)

api_module.weaviate_client = weaviate.connect_to_custom(
    http_host="localhost",
    http_port=8080,
    http_secure=False,
    grpc_host="localhost",
    grpc_port=50051,
    grpc_secure=False
)

api_module.neo4j_driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "cyber-pi-neo4j-2025")
)

# Start the API
import uvicorn
uvicorn.run(api_module.app, host="0.0.0.0", port=8000, log_level="info")
