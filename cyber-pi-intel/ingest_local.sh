#!/bin/bash
#
# Ingest Real Data with Port Forwarding
# Sets up port forwards then runs ingestion
#

set -e

echo "======================================"
echo "Real Data Ingestion (Local Mode)"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Start port forwards in background
echo "Setting up port forwards..."

microk8s kubectl port-forward -n cyber-pi-intel svc/redis 6379:6379 &
PF_REDIS=$!
echo "✓ Redis: localhost:6379"

microk8s kubectl port-forward -n cyber-pi-intel svc/weaviate 8080:8080 50051:50051 &
PF_WEAVIATE=$!
echo "✓ Weaviate: localhost:8080"

microk8s kubectl port-forward -n cyber-pi-intel svc/neo4j 7474:7474 7687:7687 &
PF_NEO4J=$!
echo "✓ Neo4j: localhost:7687"

echo ""
echo -e "${GREEN}Port forwards active${NC}"
echo "Waiting for connections to stabilize..."
sleep 5

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping port forwards..."
    kill $PF_REDIS $PF_WEAVIATE $PF_NEO4J 2>/dev/null || true
    echo "✓ Cleanup complete"
}

trap cleanup EXIT

# Run ingestion with local connections
echo ""
echo "Starting ingestion..."
echo ""

USE_LOCALHOST=true python3 ingest_real_data.py

echo ""
echo -e "${GREEN}✓ Ingestion complete!${NC}"
