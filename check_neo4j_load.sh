#!/bin/bash
# Quick Neo4j Load Status Checker

echo "🔍 NEO4J HIGHWAY LOAD STATUS"
echo "=============================="

# Check if process is running
PID=$(pgrep -f "neo4j_highway_loader.py")
if [ -n "$PID" ]; then
    echo "✅ Process Running: PID $PID"
else
    echo "❌ Process Not Running"
fi

# Show latest progress
echo ""
echo "📊 Latest Progress:"
tail -30 /tmp/neo4j_highway_load.log | grep -E "(Loading|✅|Creating|relationships)" | tail -10

# Check Neo4j node counts
echo ""
echo "💾 Neo4j Node Counts:"
microk8s kubectl exec -n cyber-pi-intel neo4j-0 -- cypher-shell -u neo4j -p cyber-pi-neo4j-2025 \
  "MATCH (n) RETURN labels(n)[0] as type, count(n) as count ORDER BY count DESC" 2>/dev/null || echo "Neo4j query skipped"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Run: tail -f /tmp/neo4j_highway_load.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
