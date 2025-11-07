#!/bin/bash

# TQAKB V4 Deployment Script for MicroK8s
# Deploys all core components with NGINX Ingress

set -e

echo "🚀 Deploying TQAKB V4 to MicroK8s..."

# Check if MicroK8s is running
if ! microk8s status | grep -q "microk8s is running"; then
    echo "❌ MicroK8s is not running. Please start it first."
    exit 1
fi

# Enable required addons
echo "🔧 Enabling required MicroK8s addons..."
microk8s enable dns storage ingress || true

# Wait for ingress to be ready
echo "⏳ Waiting for NGINX Ingress controller..."
microk8s kubectl wait --for=condition=ready pod -l name=nginx-ingress-microk8s -n ingress --timeout=300s || true

# Create namespace first
echo "📦 Creating namespace..."
microk8s kubectl apply -f namespace.yaml

# Wait for namespace to be ready
sleep 2

# Deploy core infrastructure in order
echo "🎯 Deploying Kafka..."
microk8s kubectl apply -f kafka/kafka-statefulset.yaml

echo "🚀 Deploying Redis..."
microk8s kubectl apply -f redis/redis-deployment.yaml

echo "🕸️ Deploying Neo4j..."
microk8s kubectl apply -f neo4j/neo4j-deployment.yaml

echo "🧠 Deploying Weaviate..."
microk8s kubectl apply -f weaviate/weaviate-deployment.yaml

echo "📊 Deploying Kafka UI..."
microk8s kubectl apply -f kafka-ui/kafka-ui-deployment.yaml

echo "🌐 Configuring Ingress..."
microk8s kubectl apply -f ingress/ingress.yaml

# Configure TCP services for ingress
echo "🔌 Configuring TCP services..."
microk8s kubectl patch configmap tcp-services -n ingress --patch-file=/dev/stdin <<EOF || true
data:
  9092: "tqakb-v4/kafka:9092"
  6379: "tqakb-v4/redis:6379"
  7687: "tqakb-v4/neo4j:7687"
  50051: "tqakb-v4/weaviate:50051"
EOF

# Get node IP
NODE_IP=$(microk8s kubectl get nodes -o wide --no-headers | awk '{print $6}')

# Add hosts entry
echo "📝 Configuring local hosts file..."
if ! grep -q "tqakb.local" /etc/hosts; then
    echo "Adding tqakb.local to /etc/hosts (requires sudo)..."
    echo "$NODE_IP tqakb.local" | sudo tee -a /etc/hosts
else
    echo "tqakb.local already in /etc/hosts"
fi

# Wait for deployments
echo "⏳ Waiting for pods to be ready..."
microk8s kubectl wait --for=condition=ready pod -l app=kafka -n tqakb-v4 --timeout=300s || true
microk8s kubectl wait --for=condition=ready pod -l app=redis -n tqakb-v4 --timeout=300s || true
microk8s kubectl wait --for=condition=ready pod -l app=neo4j -n tqakb-v4 --timeout=300s || true
microk8s kubectl wait --for=condition=ready pod -l app=weaviate -n tqakb-v4 --timeout=300s || true
microk8s kubectl wait --for=condition=ready pod -l app=kafka-ui -n tqakb-v4 --timeout=300s || true

# Show status
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Pod Status:"
microk8s kubectl get pods -n tqakb-v4

echo ""
echo "🌐 Services:"
microk8s kubectl get svc -n tqakb-v4

echo ""
echo "🌍 Ingress Status:"
microk8s kubectl get ingress -n tqakb-v4

echo ""
echo "🔗 Access Points via NGINX Ingress:"
echo "  Web UIs:"
echo "    Kafka UI:      http://tqakb.local/kafka-ui"
echo "    Redis Stack:   http://tqakb.local/redis"
echo "    Neo4j Browser: http://tqakb.local/neo4j"
echo "    Weaviate:      http://tqakb.local/weaviate"
echo ""
echo "  TCP Services (via Ingress TCP):"
echo "    Kafka:    $NODE_IP:9092"
echo "    Redis:    $NODE_IP:6379"
echo "    Neo4j:    $NODE_IP:7687"
echo "    Weaviate: $NODE_IP:50051"

echo ""
echo "💡 Tips:"
echo "  - Check logs: microk8s kubectl logs -f <pod-name> -n tqakb-v4"
echo "  - Shell into pod: microk8s kubectl exec -it <pod-name> -n tqakb-v4 -- /bin/bash"
echo "  - Delete deployment: microk8s kubectl delete namespace tqakb-v4"
echo "  - Check ingress: microk8s kubectl describe ingress -n tqakb-v4"