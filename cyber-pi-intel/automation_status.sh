#!/bin/bash

echo "======================================================================="
echo "🤖 AUTOMATION STATUS DASHBOARD"
echo "======================================================================="
echo

echo "📅 Collection Schedule:"
echo "   CISA KEV:      Every 15 minutes (CronJob ready)"
echo "   RSS Feeds:     Hourly (CronJob ready)"
echo "   GitHub:        Hourly (CronJob ready)"
echo

echo "📊 Current Collection Stats:"
CISA_COUNT=$(microk8s kubectl exec -n cyber-pi-intel neo4j-0 -- cypher-shell -u neo4j -p cyber-pi-neo4j-2025 "MATCH (t:CyberThreat) WHERE t.source CONTAINS 'CISA KEV' RETURN count(t) as total;" 2>/dev/null | tail -1)
echo "   CISA KEV Threats in DB: $CISA_COUNT"
echo "   Total KEV Available: 1,453"
echo

echo "🔄 Redis Queue Status:"
WEAVIATE_Q=$(microk8s kubectl exec -n cyber-pi-intel redis-0 -- redis-cli -a cyber-pi-redis-2025 --no-auth-warning LLEN queue:weaviate 2>/dev/null)
NEO4J_Q=$(microk8s kubectl exec -n cyber-pi-intel redis-0 -- redis-cli -a cyber-pi-redis-2025 --no-auth-warning LLEN queue:neo4j 2>/dev/null)
echo "   queue:weaviate: $WEAVIATE_Q items"
echo "   queue:neo4j: $NEO4J_Q items"
echo

echo "⚙️  Storage Workers:"
RUNNING_WORKERS=$(microk8s kubectl get pods -n cyber-pi-intel 2>/dev/null | grep -E "weaviate-worker|neo4j-worker" | grep "Running" | wc -l)
COMPLETED_WORKERS=$(microk8s kubectl get pods -n cyber-pi-intel 2>/dev/null | grep -E "weaviate-worker|neo4j-worker" | grep "Completed" | wc -l)
echo "   Running: $RUNNING_WORKERS"
echo "   Completed: $COMPLETED_WORKERS"
echo

echo "📋 CronJobs:"
microk8s kubectl get cronjobs -n cyber-pi-intel 2>/dev/null | grep -v NAME | awk '{print "   "$1": "$5}' || echo "   None deployed yet"
echo

echo "🎯 Sample CISA KEV Threats:"
microk8s kubectl exec -n cyber-pi-intel neo4j-0 -- cypher-shell -u neo4j -p cyber-pi-neo4j-2025 "
MATCH (t:CyberThreat)
WHERE t.source CONTAINS 'CISA KEV'
RETURN t.title
LIMIT 5;
" 2>/dev/null | tail -n +2 | head -5 | awk '{print "   "$0}'
echo

echo "======================================================================="
echo "📈 Automation Capabilities:"
echo "======================================================================="
echo
echo "✅ Automated Collection:"
echo "   • CISA KEV (1,453 vulnerabilities)"
echo "   • RSS feeds (5+ security news sources)"
echo "   • GitHub advisories (supply chain)"
echo
echo "✅ Automated Processing:"
echo "   • Redis data highway"
echo "   • Parallel storage workers"
echo "   • Vector + Graph databases"
echo
echo "⏳ Coming Soon:"
echo "   • Enrichment (CVE/Actor extraction)"
echo "   • Deduplication engine"
echo "   • Automated threat hunting"
echo "   • Alert generation (Slack/Email)"
echo
echo "======================================================================="
echo "🚀 Deployment Commands:"
echo "======================================================================="
echo
echo "Deploy Full Automation:"
echo "  kubectl apply -f deployment/automation/collection-cronjobs.yaml"
echo
echo "Run Manual Collection:"
echo "  kubectl apply -f deployment/automation/test-cisa-collector.yaml"
echo
echo "Deploy Storage Workers:"
echo "  kubectl apply -f deployment/cyber-pi-simplified/worker-jobs.yaml"
echo
echo "Check Logs:"
echo "  kubectl logs -n cyber-pi-intel <pod-name>"
echo
echo "======================================================================="
