#!/bin/bash

# TQAKB V4 Development Setup Script
# Sets up virtual environment and runs with different ports to avoid conflicts with V3

set -e

echo "🚀 Setting up TQAKB V4 development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip and uv
echo "📥 Installing uv for fast package management..."
pip install --upgrade pip
pip install uv

# Install dependencies
echo "📚 Installing dependencies with uv..."
uv pip install -e ".[dev]"

# Create .env file with non-conflicting ports
echo "⚙️ Creating .env file with development ports..."
cat > .env << 'EOF'
# TQAKB V4 Development Configuration
# Using different ports to avoid conflicts with V3

# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# API Configuration - Different port from V3
API_HOST=0.0.0.0
API_PORT=8001  # V3 uses 8000
API_WORKERS=1
API_RELOAD=true

# Use V3's running services via NodePort
# This way we don't need to deploy V4 infrastructure yet

# Kafka - Use V3's Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:30092
KAFKA_SECURITY_PROTOCOL=PLAINTEXT
KAFKA_GROUP_ID=tqakb-v4-dev
KAFKA_AUTO_OFFSET_RESET=earliest
KAFKA_ENABLE_AUTO_COMMIT=true

# Redis - Use V3's Redis
REDIS_HOST=localhost
REDIS_PORT=30379
REDIS_DB=1  # Use different DB to avoid conflicts
REDIS_PASSWORD=
REDIS_SSL=false
REDIS_POOL_SIZE=10
REDIS_POOL_MAX_CONNECTIONS=20

# Neo4j - Use V3's Neo4j
NEO4J_URI=bolt://localhost:30687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
NEO4J_DATABASE=neo4j
NEO4J_CONNECTION_POOL_SIZE=10

# Weaviate - Use V3's Weaviate
WEAVIATE_URL=http://localhost:30082
WEAVIATE_API_KEY=
WEAVIATE_BATCH_SIZE=100
WEAVIATE_TIMEOUT=60

# Ollama - Use local Ollama (not K8s)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest
OLLAMA_TIMEOUT=120
OLLAMA_NUM_CTX=4096

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9091  # Different from V3
OTEL_ENABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Security
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8001", "http://tqakb.local"]

# Performance
ASYNC_POOL_SIZE=10
BATCH_SIZE=100
CACHE_TTL=300
MAX_RETRIES=3
RETRY_DELAY=1.0
EOF

echo "✅ Environment configured to use V3 services"

# Create run script
cat > run_dev.sh << 'EOF'
#!/bin/bash
# Activate virtual environment and run the app
source venv/bin/activate
echo "Starting TQAKB V4 on port 8001..."
echo "Using V3 services via NodePort connections"
python backend/main.py
EOF
chmod +x run_dev.sh

# Create test script for new port
cat > test_v4_local.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for TQAKB V4 API (running on port 8001)
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"  # V4 uses 8001

async def test_api():
    """Test V4 API endpoints"""
    async with httpx.AsyncClient() as client:
        print("Testing TQAKB V4 API on port 8001...")
        print("(Using V3 infrastructure via NodePorts)")
        print("-" * 50)
        
        # Test root endpoint
        print("1. Testing root endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Version: {response.json().get('version', 'unknown')}")
        except Exception as e:
            print(f"   Error: {e}")
        print()
        
        # Test health check
        print("2. Testing health check...")
        try:
            response = await client.get(f"{BASE_URL}/api/health/")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Service: {response.json().get('service', 'unknown')}")
        except Exception as e:
            print(f"   Error: {e}")
        print()
        
        # Test service health (connections to V3 services)
        print("3. Testing connections to V3 services...")
        try:
            response = await client.get(f"{BASE_URL}/api/health/services")
            if response.status_code == 200:
                services = response.json().get('services', [])
                for service in services:
                    status_icon = "✅" if service['status'] == 'healthy' else "❌"
                    print(f"   {status_icon} {service['name']}: {service['status']}")
        except Exception as e:
            print(f"   Error: {e}")
        print()
        
        print("-" * 50)
        print("V4 API test completed!")
        print("\nNOTE: V4 is using V3's infrastructure via NodePorts")
        print("This allows testing V4 code without deploying new infrastructure")

if __name__ == "__main__":
    asyncio.run(test_api())
EOF
chmod +x test_v4_local.py

echo ""
echo "✨ Setup complete!"
echo ""
echo "📝 Configuration:"
echo "   - Virtual environment: ./venv"
echo "   - V4 API Port: 8001 (V3 uses 8000)"
echo "   - Using V3 services via NodePorts"
echo "   - Redis DB: 1 (isolated from V3)"
echo ""
echo "🎯 Next steps:"
echo "   1. Run V4 API:     ./run_dev.sh"
echo "   2. Test V4 API:    ./test_v4_local.py"
echo "   3. Access docs:    http://localhost:8001/api/docs"
echo ""
echo "💡 The V4 backend will connect to V3's running services:"
echo "   - Kafka:    localhost:30092"
echo "   - Redis:    localhost:30379 (DB 1)"
echo "   - Neo4j:    localhost:30687"
echo "   - Weaviate: localhost:30082"
echo "   - Ollama:   localhost:11434 (local)"