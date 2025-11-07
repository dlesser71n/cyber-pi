#!/bin/bash
# Port forwarding for Cyber-PI databases in MicroK8s
# Uses alternative ports to avoid conflicts

echo "🚀 Starting port forwarding for Cyber-PI databases..."

# Kill any existing port forwards
pkill -f "kubectl port-forward.*cyber-pi-intel"

# Neo4j (using ports 17474 and 17687 instead of 7474/7687)
echo "Starting Neo4j port forward: localhost:17474 (HTTP) and localhost:17687 (Bolt)"
microk8s kubectl port-forward -n cyber-pi-intel svc/neo4j 17474:7474 17687:7687 > /dev/null 2>&1 &
NEO4J_PID=$!

# Redis (using port 16379 instead of 6379)
echo "Starting Redis port forward: localhost:16379"
microk8s kubectl port-forward -n cyber-pi-intel svc/redis 16379:6379 > /dev/null 2>&1 &
REDIS_PID=$!

# Weaviate (using port 18080 instead of 8080)
echo "Starting Weaviate port forward: localhost:18080"
microk8s kubectl port-forward -n cyber-pi-intel svc/weaviate 18080:8080 > /dev/null 2>&1 &
WEAVIATE_PID=$!

# Wait a moment for port forwards to establish
sleep 2

echo ""
echo "✅ Port forwarding active:"
echo "   Neo4j HTTP:  http://localhost:17474"
echo "   Neo4j Bolt:  bolt://localhost:17687"
echo "   Redis:       localhost:16379"
echo "   Weaviate:    http://localhost:18080"
echo ""
echo "PIDs: Neo4j=$NEO4J_PID Redis=$REDIS_PID Weaviate=$WEAVIATE_PID"
echo ""
echo "To stop: pkill -f 'kubectl port-forward.*cyber-pi-intel'"
echo "Or kill specific: kill $NEO4J_PID $REDIS_PID $WEAVIATE_PID"
