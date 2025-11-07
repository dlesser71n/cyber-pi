#!/bin/bash
#
# Ingest with automatic port forward management
#

set -e

echo "======================================"
echo "🔥 REAL DATA INGESTION"
echo "All 1,525 Threats → TQAKB"
echo "======================================"
echo ""

# Start port forwards
echo "📡 Starting port forwards..."
microk8s kubectl port-forward -n cyber-pi-intel svc/redis 6379:6379 >/dev/null 2>&1 &
PF_REDIS=$!
microk8s kubectl port-forward -n cyber-pi-intel svc/weaviate 8080:8080 50051:50051 >/dev/null 2>&1 &
PF_WEAVIATE=$!
microk8s kubectl port-forward -n cyber-pi-intel svc/neo4j 7474:7474 7687:7687 >/dev/null 2>&1 &
PF_NEO4J=$!

echo "✓ Port forwards started"
echo "  Redis: $PF_REDIS"
echo "  Weaviate: $PF_WEAVIATE"
echo "  Neo4j: $PF_NEO4J"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "🧹 Cleaning up port forwards..."
    kill $PF_REDIS $PF_WEAVIATE $PF_NEO4J 2>/dev/null || true
    wait $PF_REDIS $PF_WEAVIATE $PF_NEO4J 2>/dev/null || true
    echo "✓ Cleanup complete"
}

trap cleanup EXIT INT TERM

# Wait for port forwards to be ready
echo "⏳ Waiting for connections (10 seconds)..."
sleep 10

# Test connections
echo "🔍 Testing connections..."
if redis-cli -h localhost -p 6379 -a cyber-pi-redis-2025 ping 2>/dev/null | grep -q PONG; then
    echo "  ✓ Redis connected"
else
    echo "  ✗ Redis not responding"
fi

if curl -s http://localhost:8080/v1/.well-known/ready 2>/dev/null | grep -q true; then
    echo "  ✓ Weaviate connected"
else
    echo "  ✗ Weaviate not responding"
fi

if curl -s http://localhost:7474 2>/dev/null > /dev/null; then
    echo "  ✓ Neo4j connected"
else
    echo "  ✗ Neo4j not responding"
fi

echo ""
echo "🚀 Starting ingestion..."
echo ""

# Run ingestion
USE_LOCALHOST=true python3 ingest_real_data.py

echo ""
echo "✅ COMPLETE!"
