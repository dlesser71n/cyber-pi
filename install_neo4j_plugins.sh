#!/bin/bash
#
# Install Neo4j Plugins: APOC + GDS
# Unlock 90% of Neo4j's capabilities
#

set -e

echo "🚀 Neo4j Plugin Installation"
echo "============================="
echo ""
echo "This will install:"
echo "  • APOC (Awesome Procedures on Cypher)"
echo "  • GDS (Graph Data Science)"
echo ""
echo "Neo4j will restart during installation."
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 1
fi

# Neo4j version
NEO4J_VERSION="5.13.0"
NEO4J_POD="neo4j-0"
NEO4J_NAMESPACE="cyber-pi-intel"

echo ""
echo "📥 Step 1: Downloading APOC..."
cd /tmp
if [ ! -f "apoc-${NEO4J_VERSION}-core.jar" ]; then
    wget -q --show-progress \
        https://github.com/neo4j/apoc/releases/download/${NEO4J_VERSION}/apoc-${NEO4J_VERSION}-core.jar
    echo "✓ APOC downloaded"
else
    echo "✓ APOC already downloaded"
fi

echo ""
echo "📥 Step 2: Downloading GDS..."
if [ ! -f "neo4j-graph-data-science-2.5.0.jar" ]; then
    wget -q --show-progress \
        https://s3-eu-west-1.amazonaws.com/com.neo4j.graphalgorithms.dist/graph-data-science/neo4j-graph-data-science-2.5.0.jar
    echo "✓ GDS downloaded"
else
    echo "✓ GDS already downloaded"
fi

echo ""
echo "📦 Step 3: Copying APOC to Neo4j..."
microk8s kubectl cp /tmp/apoc-${NEO4J_VERSION}-core.jar \
    ${NEO4J_NAMESPACE}/${NEO4J_POD}:/var/lib/neo4j/plugins/apoc-${NEO4J_VERSION}-core.jar
echo "✓ APOC installed"

echo ""
echo "📦 Step 4: Copying GDS to Neo4j..."
microk8s kubectl cp /tmp/neo4j-graph-data-science-2.5.0.jar \
    ${NEO4J_NAMESPACE}/${NEO4J_POD}:/var/lib/neo4j/plugins/neo4j-graph-data-science-2.5.0.jar
echo "✓ GDS installed"

echo ""
echo "⚙️  Step 5: Configuring Neo4j..."
microk8s kubectl exec -n ${NEO4J_NAMESPACE} ${NEO4J_POD} -- sh -c \
    'echo "dbms.security.procedures.unrestricted=gds.*,apoc.*" >> /var/lib/neo4j/conf/neo4j.conf'
microk8s kubectl exec -n ${NEO4J_NAMESPACE} ${NEO4J_POD} -- sh -c \
    'echo "dbms.security.procedures.allowlist=gds.*,apoc.*" >> /var/lib/neo4j/conf/neo4j.conf'
echo "✓ Configuration updated"

echo ""
echo "🔄 Step 6: Restarting Neo4j..."
microk8s kubectl rollout restart statefulset/neo4j -n ${NEO4J_NAMESPACE}
echo "✓ Restart initiated"

echo ""
echo "⏳ Waiting for Neo4j to come back online (60 seconds)..."
sleep 60

# Check if Neo4j is ready
echo ""
echo "🔍 Step 7: Verifying installation..."
sleep 5  # Extra buffer

# Test APOC
APOC_TEST=$(curl -s -u neo4j:dev-neo4j-password \
    -H "Content-Type: application/json" \
    -d '{"statements":[{"statement":"RETURN apoc.version() AS version"}]}' \
    http://localhost:7474/db/neo4j/tx/commit | grep -o '"version":"[^"]*"' || echo "")

# Test GDS
GDS_TEST=$(curl -s -u neo4j:dev-neo4j-password \
    -H "Content-Type: application/json" \
    -d '{"statements":[{"statement":"RETURN gds.version() AS version"}]}' \
    http://localhost:7474/db/neo4j/tx/commit | grep -o '"version":"[^"]*"' || echo "")

echo ""
echo "================================"
echo "📊 INSTALLATION RESULTS"
echo "================================"
echo ""

if [ -n "$APOC_TEST" ]; then
    echo "✅ APOC: INSTALLED"
    echo "   $APOC_TEST"
else
    echo "❌ APOC: VERIFICATION FAILED"
    echo "   Try again in 30 seconds or check logs"
fi

if [ -n "$GDS_TEST" ]; then
    echo "✅ GDS: INSTALLED"
    echo "   $GDS_TEST"
else
    echo "❌ GDS: VERIFICATION FAILED"
    echo "   Try again in 30 seconds or check logs"
fi

echo ""
echo "================================"
echo ""

if [ -n "$APOC_TEST" ] && [ -n "$GDS_TEST" ]; then
    echo "🎉 SUCCESS! Neo4j is now running with APOC + GDS"
    echo ""
    echo "Test with:"
    echo "  • APOC: RETURN apoc.version()"
    echo "  • GDS:  RETURN gds.version()"
    echo ""
    echo "Next steps:"
    echo "  1. Load 316K CVEs into Neo4j (run neo4j_cve_loader.py)"
    echo "  2. Try graph algorithms (PageRank, community detection)"
    echo "  3. Generate ML embeddings with Node2Vec"
else
    echo "⚠️  Verification incomplete. Neo4j may still be starting."
    echo ""
    echo "Wait 30 seconds and verify manually:"
    echo "  curl -u neo4j:dev-neo4j-password \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"statements\":[{\"statement\":\"RETURN apoc.version(), gds.version()\"}]}' \\"
    echo "    http://localhost:7474/db/neo4j/tx/commit"
fi

echo ""
echo "Installation complete!"
