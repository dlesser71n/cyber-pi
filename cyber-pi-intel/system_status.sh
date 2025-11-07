#!/bin/bash
#
# Cyber-PI-Intel System Status Dashboard
# Real-time view of threat intelligence platform
#

echo "======================================================================="
echo "🔒 CYBER-PI-INTEL SYSTEM STATUS"
echo "======================================================================="
echo

# API Health
echo "📡 API Status:"
API_STATUS=$(curl -s http://localhost:30888/health 2>/dev/null)
if [ "$API_STATUS" = "healthy" ]; then
    echo "   ✅ API Gateway: Healthy (http://localhost:30888)"
else
    echo "   ❌ API Gateway: Not responding"
fi
echo

# Database Counts
echo "💾 Database Statistics:"
echo

# Weaviate
ANALYTICS=$(curl -s http://localhost:30888/api/analytics/summary 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data['threat_landscape']['total_threats']}\")" 2>/dev/null)
if [ -n "$ANALYTICS" ]; then
    echo "   Weaviate (Vector DB):"
    echo "   └─ Total Threats: $ANALYTICS"
else
    echo "   ⚠️  Weaviate: Unable to query"
fi
echo

# Neo4j
NEO4J_COUNT=$(microk8s kubectl exec -n cyber-pi-intel neo4j-0 -- cypher-shell -u neo4j -p cyber-pi-neo4j-2025 "MATCH (t:CyberThreat) RETURN count(t) as total;" 2>/dev/null | tail -1)
if [ -n "$NEO4J_COUNT" ]; then
    echo "   Neo4j (Graph DB):"
    echo "   ├─ Threat Nodes: $NEO4J_COUNT"

    # Get node types
    LABELS=$(microk8s kubectl exec -n cyber-pi-intel neo4j-0 -- cypher-shell -u neo4j -p cyber-pi-neo4j-2025 "CALL db.labels();" 2>/dev/null | tail -n +2 | wc -l)
    echo "   └─ Node Types: $LABELS"
else
    echo "   ⚠️  Neo4j: Unable to query"
fi
echo

# Redis Queue Status
echo "🛣️  Redis Highway:"
WEAVIATE_Q=$(microk8s kubectl exec -n cyber-pi-intel redis-0 -- redis-cli -a cyber-pi-redis-2025 --no-auth-warning LLEN queue:weaviate 2>/dev/null)
NEO4J_Q=$(microk8s kubectl exec -n cyber-pi-intel redis-0 -- redis-cli -a cyber-pi-redis-2025 --no-auth-warning LLEN queue:neo4j 2>/dev/null)
echo "   ├─ queue:weaviate: $WEAVIATE_Q items"
echo "   └─ queue:neo4j: $NEO4J_Q items"
echo

# Kubernetes Pods
echo "☸️  Kubernetes Pods:"
PODS=$(microk8s kubectl get pods -n cyber-pi-intel --no-headers 2>/dev/null)
RUNNING=$(echo "$PODS" | grep "Running" | wc -l)
COMPLETED=$(echo "$PODS" | grep "Completed" | wc -l)
TOTAL=$(echo "$PODS" | wc -l)
echo "   ├─ Running: $RUNNING"
echo "   ├─ Completed: $COMPLETED"
echo "   └─ Total: $TOTAL"
echo

# Sample Recent Threats
echo "🎯 Sample Threats (Latest 3):"
curl -s "http://localhost:30888/api/threats?limit=3" 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
for i, threat in enumerate(data.get('threats', []), 1):
    title = threat.get('title', 'Unknown')
    if len(title) > 60:
        title = title[:60] + '...'
    source = threat.get('source', 'Unknown')
    severity = threat.get('severity', 'unknown')
    print(f\"   {i}. [{severity.upper()}] {title}\")
    print(f\"      Source: {source}\")
" 2>/dev/null
echo

# Test Results
echo "🧪 Latest Test Results:"
if [ -f "E2E_TEST_RESULTS.md" ]; then
    PASS_RATE=$(grep -oP '\*\*\d+\.\d+%\*\* PASS' E2E_TEST_RESULTS.md | head -1 | grep -oP '\d+\.\d+')
    if [ -n "$PASS_RATE" ]; then
        echo "   ✅ E2E Tests: $PASS_RATE% pass rate"
    fi
fi

if [ -f "SECURITY_ENHANCEMENTS_COMPLETE.md" ]; then
    SECURITY_RATING=$(grep -oP 'Rating: \*\*\d+\.\d+/10' SECURITY_ENHANCEMENTS_COMPLETE.md | head -1 | grep -oP '\d+\.\d+')
    if [ -n "$SECURITY_RATING" ]; then
        echo "   🔒 Security: $SECURITY_RATING/10 rating"
    fi
fi
echo

echo "======================================================================="
echo "System Operational: $(date)"
echo "======================================================================="
