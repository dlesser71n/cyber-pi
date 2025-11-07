#!/bin/bash
#
# Deploy Simplified TQAKB Stack for cyber-pi
# Redis + Weaviate + Neo4j (No Kafka)
#

set -e

echo "=================================="
echo "TQAKB Simplified Deployment"
echo "cyber-pi Threat Intelligence"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if microk8s is available
if ! command -v microk8s &> /dev/null; then
    echo -e "${RED}ERROR: microk8s not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ MicroK8s found${NC}"
echo ""

# Function to wait for deployment
wait_for_deployment() {
    local namespace=$1
    local deployment=$2
    local timeout=${3:-300}
    
    echo -n "Waiting for $deployment to be ready..."
    microk8s kubectl wait --for=condition=ready pod \
        -l app=$deployment \
        -n $namespace \
        --timeout=${timeout}s 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e " ${GREEN}✓${NC}"
        return 0
    else
        echo -e " ${YELLOW}⚠ Timeout (continuing anyway)${NC}"
        return 1
    fi
}

# Step 1: Create namespace
echo "Step 1: Creating namespace..."
microk8s kubectl apply -f namespace.yaml
echo -e "${GREEN}✓ Namespace created${NC}"
echo ""

# Step 2: Deploy secrets and config
echo "Step 2: Deploying secrets and configuration..."
microk8s kubectl apply -f secrets.yaml
echo -e "${GREEN}✓ Secrets and ConfigMap created${NC}"
echo ""

# Step 3: Deploy Redis
echo "Step 3: Deploying Redis..."
microk8s kubectl apply -f redis-deployment.yaml
wait_for_deployment cyber-pi-intel redis 120
echo ""

# Step 4: Deploy Weaviate
echo "Step 4: Deploying Weaviate..."
microk8s kubectl apply -f weaviate-deployment.yaml
wait_for_deployment cyber-pi-intel weaviate 180
echo ""

# Step 5: Deploy Neo4j
echo "Step 5: Deploying Neo4j..."
microk8s kubectl apply -f neo4j-deployment.yaml
wait_for_deployment cyber-pi-intel neo4j 180
echo ""

# Step 6: Deploy NGINX Gateway
echo "Step 6: Deploying NGINX Gateway..."
microk8s kubectl apply -f nginx-gateway.yaml
wait_for_deployment cyber-pi-intel nginx-gateway 60
echo ""

# Step 6: Check status
echo "=================================="
echo "Deployment Summary"
echo "=================================="
echo ""

echo "Pods:"
microk8s kubectl get pods -n cyber-pi-intel
echo ""

echo "Services:"
microk8s kubectl get svc -n cyber-pi-intel
echo ""

echo "PVCs:"
microk8s kubectl get pvc -n cyber-pi-intel
echo ""

# Step 7: Connection information
echo "=================================="
echo "Connection Information"
echo "=================================="
echo ""
echo -e "${GREEN}🔐 Secrets:${NC}"
echo "  View: kubectl get secret cyber-pi-credentials -n cyber-pi-intel"
echo "  Decode: kubectl get secret cyber-pi-credentials -n cyber-pi-intel -o jsonpath='{.data.redis-password}' | base64 -d"
echo ""
echo -e "${GREEN}🌐 NGINX Gateway (Single Entry Point):${NC}"
echo "  Gateway:  http://localhost:30888"
echo "  Health:   http://localhost:30888/health"
echo ""
echo -e "${GREEN}📊 Service Access (via NGINX):${NC}"
echo "  Weaviate: http://localhost:30888/weaviate/v1/schema"
echo "  Neo4j:    http://localhost:30888/neo4j/"
echo ""
echo -e "${GREEN}🔒 Internal Service Access (within cluster):${NC}"
echo "  Redis:    redis.cyber-pi-intel.svc.cluster.local:6379"
echo "  Weaviate: weaviate.cyber-pi-intel.svc.cluster.local:8080"
echo "  Neo4j:    neo4j.cyber-pi-intel.svc.cluster.local:7474"
echo ""
echo -e "${GREEN}🔑 Credentials:${NC}"
echo "  Neo4j: neo4j / cyber-pi-neo4j-2025"
echo "  Redis: cyber-pi-redis-2025"
echo "  External: bolt://localhost:30687"
echo "  Web UI: http://localhost:30474"
echo "  Username: neo4j"
echo "  Password: cyber-pi-neo4j-2025 (from secret)"
echo ""

# Step 7: Health checks
echo "=================================="
echo "Health Checks"
echo "=================================="
echo ""

echo -n "Testing NGINX Gateway... "
if curl -s http://localhost:30888/health 2>/dev/null | grep -q healthy; then
    echo -e "${GREEN}✓ Gateway healthy${NC}"
else
    echo -e "${YELLOW}⚠ Gateway not ready${NC}"
fi

echo -n "Testing Weaviate (via NGINX)... "
if curl -s http://localhost:30888/weaviate/v1/.well-known/ready 2>/dev/null | grep -q true; then
    echo -e "${GREEN}✓ Ready${NC}"
else
    echo -e "${YELLOW}⚠ Not ready yet${NC}"
fi

echo -n "Testing Neo4j (via NGINX)... "
if curl -s http://localhost:30888/neo4j/ 2>/dev/null > /dev/null; then
    echo -e "${GREEN}✓ Accessible${NC}"
else
    echo -e "${YELLOW}⚠ Not accessible yet${NC}"
fi

echo ""
echo "=================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Wait for all pods to be Running (kubectl get pods -n cyber-pi-intel)"
echo "2. Review credentials in CREDENTIALS.md"
echo "3. Test connectivity to each service (with passwords)"
echo "4. Deploy TQAKB backend"
echo "5. Initialize Weaviate schema"
echo ""
echo "Credentials:"
echo "  All passwords stored in: kubectl get secret cyber-pi-credentials -n cyber-pi-intel"
echo "  Documentation: See CREDENTIALS.md"
echo ""
echo "To monitor:"
echo "  kubectl get pods -n cyber-pi-intel -w"
echo ""
echo "To access logs:"
echo "  kubectl logs -n cyber-pi-intel -l app=redis"
echo "  kubectl logs -n cyber-pi-intel -l app=weaviate"
echo "  kubectl logs -n cyber-pi-intel -l app=neo4j"
echo ""
