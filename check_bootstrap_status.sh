#!/bin/bash
#
# Check CVE Bootstrap Status
#

echo "🔍 CVE Bootstrap Status Check"
echo "=============================="
echo ""

# Check if download is running
if pgrep -f "cve_bulk_import_v2.py" > /dev/null; then
    echo "✅ Download process: RUNNING"
    echo ""
    
    # Show recent log lines
    if [ -f "data/cve_import/bootstrap.log" ]; then
        echo "Recent progress:"
        tail -5 data/cve_import/bootstrap.log
    fi
else
    echo "⏸️  Download process: NOT RUNNING"
fi

echo ""
echo "---"
echo ""

# Check downloaded data
if [ -f "data/cve_import/all_cves_neo4j.json" ]; then
    echo "✅ CVE data file: EXISTS"
    FILE_SIZE=$(du -h data/cve_import/all_cves_neo4j.json | cut -f1)
    echo "   Size: $FILE_SIZE"
    
    # Count CVEs
    CVE_COUNT=$(python3 -c "import json; print(len(json.load(open('data/cve_import/all_cves_neo4j.json'))))" 2>/dev/null || echo "?")
    echo "   CVEs: $CVE_COUNT"
else
    echo "❌ CVE data file: NOT YET CREATED"
fi

echo ""
echo "---"
echo ""

# Check Neo4j status
if curl -s http://localhost:7474/ > /dev/null 2>&1; then
    echo "✅ Neo4j: RUNNING"
    echo "   URL: http://localhost:7474"
else
    echo "❌ Neo4j: NOT ACCESSIBLE"
fi

echo ""
echo "To monitor live progress:"
echo "  watch -n 5 ./check_bootstrap_status.sh"
