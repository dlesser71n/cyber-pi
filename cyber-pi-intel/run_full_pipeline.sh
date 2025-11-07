#!/bin/bash
#
# Full Pipeline: Port Forwards + Workers
# Complete automation of data processing
#

set -e

echo "======================================"
echo "🔥 CYBER-PI INTEL FULL PIPELINE"
echo "Redis → Workers → Databases"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if Redis already has data
echo "📊 Checking Redis queue status..."
WEAVIATE_QUEUE=$(redis-cli -h localhost -p 6380 -a cyber-pi-redis-2025 --no-auth-warning LLEN queue:weaviate 2>/dev/null || echo "0")
NEO4J_QUEUE=$(redis-cli -h localhost -p 6380 -a cyber-pi-redis-2025 --no-auth-warning LLEN queue:neo4j 2>/dev/null || echo "0")
STIX_QUEUE=$(redis-cli -h localhost -p 6380 -a cyber-pi-redis-2025 --no-auth-warning LLEN queue:stix_export 2>/dev/null || echo "0")

echo -e "${GREEN}Queue Status:${NC}"
echo "  Weaviate: $WEAVIATE_QUEUE threats"
echo "  Neo4j:    $NEO4J_QUEUE threats"
echo "  STIX:     $STIX_QUEUE threats"
echo ""

if [ "$WEAVIATE_QUEUE" = "0" ]; then
    echo -e "${YELLOW}⚠️  Queues are empty. Run ingestion first:${NC}"
    echo "  python3 ingest_redis_first.py"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start port forwards in background
echo "📡 Starting port forwards..."
echo ""

# Kill existing port forwards
pkill -f "port-forward.*cyber-pi-intel" 2>/dev/null || true
sleep 2

# Redis (already forwarded on 6380)
if ! lsof -i :6380 >/dev/null 2>&1; then
    microk8s kubectl port-forward -n cyber-pi-intel svc/redis 6380:6379 >/dev/null 2>&1 &
    PF_REDIS=$!
    echo "  ✓ Redis: localhost:6380"
fi

# Weaviate
microk8s kubectl port-forward -n cyber-pi-intel svc/weaviate 8080:8080 50051:50051 >/dev/null 2>&1 &
PF_WEAVIATE=$!
echo "  ✓ Weaviate: localhost:8080"

# Neo4j
microk8s kubectl port-forward -n cyber-pi-intel svc/neo4j 7474:7474 7687:7687 >/dev/null 2>&1 &
PF_NEO4J=$!
echo "  ✓ Neo4j: localhost:7687"

echo ""
echo -e "${GREEN}Port forwards active${NC}"
echo "Waiting for connections to stabilize..."
sleep 5

# Cleanup function
cleanup() {
    echo ""
    echo "🧹 Cleaning up..."
    
    # Kill workers
    pkill -f "weaviate_worker.py" 2>/dev/null || true
    pkill -f "neo4j_worker.py" 2>/dev/null || true
    pkill -f "stix_worker.py" 2>/dev/null || true
    
    # Kill port forwards
    [ ! -z "$PF_REDIS" ] && kill $PF_REDIS 2>/dev/null || true
    [ ! -z "$PF_WEAVIATE" ] && kill $PF_WEAVIATE 2>/dev/null || true
    [ ! -z "$PF_NEO4J" ] && kill $PF_NEO4J 2>/dev/null || true
    
    echo "✓ Cleanup complete"
}

trap cleanup EXIT INT TERM

# Run workers
echo ""
echo "🚀 Starting parallel workers..."
echo ""

python3 run_workers_parallel.py \
    --weaviate 3 \
    --neo4j 2 \
    --stix 1

echo ""
echo -e "${GREEN}✅ PIPELINE COMPLETE!${NC}"
echo ""

# Show final stats
echo "📊 Final Queue Status:"
WEAVIATE_FINAL=$(redis-cli -h localhost -p 6380 -a cyber-pi-redis-2025 --no-auth-warning LLEN queue:weaviate 2>/dev/null || echo "0")
NEO4J_FINAL=$(redis-cli -h localhost -p 6380 -a cyber-pi-redis-2025 --no-auth-warning LLEN queue:neo4j 2>/dev/null || echo "0")
STIX_FINAL=$(redis-cli -h localhost -p 6380 -a cyber-pi-redis-2025 --no-auth-warning LLEN queue:stix_export 2>/dev/null || echo "0")

echo "  Weaviate: $WEAVIATE_FINAL remaining (was $WEAVIATE_QUEUE)"
echo "  Neo4j:    $NEO4J_FINAL remaining (was $NEO4J_QUEUE)"
echo "  STIX:     $STIX_FINAL remaining (was $STIX_QUEUE)"
echo ""

# Check database contents
echo "📊 Database Status:"

# Weaviate count
WEAVIATE_COUNT=$(curl -s http://localhost:8080/v1/objects 2>/dev/null | grep -o '"totalResults":[0-9]*' | cut -d: -f2 || echo "0")
echo "  Weaviate: $WEAVIATE_COUNT objects stored"

# Neo4j count
NEO4J_COUNT=$(curl -s -u neo4j:cyber-pi-neo4j-2025 \
    -H "Content-Type: application/json" \
    -d '{"statements":[{"statement":"MATCH (n:CyberThreat) RETURN count(n) as count"}]}' \
    http://localhost:7474/db/neo4j/tx/commit 2>/dev/null | grep -o '"count":[0-9]*' | head -1 | cut -d: -f2 || echo "0")
echo "  Neo4j:    $NEO4J_COUNT threats in graph"

echo ""
echo -e "${GREEN}🎉 SUCCESS!${NC}"
