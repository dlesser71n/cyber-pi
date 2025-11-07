#!/bin/bash
#
# CVE Knowledge Graph Bootstrap
# Downloads 200K+ CVEs and loads into Neo4j for critical mass
#

set -e  # Exit on error

echo "🚀 CVE Knowledge Graph Bootstrap"
echo "=================================="
echo ""

# Activate virtual environment
source .venv/bin/activate

# Check if data already exists
if [ -f "data/cve_import/all_cves_neo4j.json" ]; then
    echo "⚠️  CVE data already downloaded (data/cve_import/all_cves_neo4j.json)"
    echo "   Skip download? (y/n)"
    read -r skip_download
else
    skip_download="n"
fi

# Step 1: Download CVE data
if [ "$skip_download" != "y" ]; then
    echo ""
    echo "📥 Step 1: Downloading all CVE data from NIST NVD..."
    echo "   This will download ~3 GB of data (2002-2024+)"
    echo "   Estimated time: 5-10 minutes"
    echo ""
    python3 src/bootstrap/cve_bulk_import.py
else
    echo "✓ Skipping download (using existing data)"
fi

# Check if download succeeded
if [ ! -f "data/cve_import/all_cves_neo4j.json" ]; then
    echo "❌ Error: CVE data file not found after download"
    echo "   Expected: data/cve_import/all_cves_neo4j.json"
    exit 1
fi

# Get file stats
CVE_COUNT=$(python3 -c "import json; print(len(json.load(open('data/cve_import/all_cves_neo4j.json'))))")
FILE_SIZE=$(du -h data/cve_import/all_cves_neo4j.json | cut -f1)

echo ""
echo "✅ CVE data ready:"
echo "   File: data/cve_import/all_cves_neo4j.json"
echo "   Size: $FILE_SIZE"
echo "   CVEs: $CVE_COUNT"
echo ""

# Step 2: Load into Neo4j
echo "📊 Step 2: Loading CVEs into Neo4j..."
echo ""
echo "⚠️  IMPORTANT: Make sure Neo4j is running!"
echo "   Check with: neo4j status"
echo ""
echo "   Neo4j credentials will be needed (default: neo4j/neo4j)"
echo "   Update password in src/bootstrap/neo4j_cve_loader.py if needed"
echo ""
echo "   Continue with Neo4j load? (y/n)"
read -r continue_neo4j

if [ "$continue_neo4j" = "y" ]; then
    echo ""
    echo "🔄 Loading into Neo4j (this takes 30-60 minutes)..."
    python3 src/bootstrap/neo4j_cve_loader.py
    
    echo ""
    echo "🎉 BOOTSTRAP COMPLETE!"
    echo ""
    echo "Your Neo4j database now has critical mass:"
    echo "  • 200,000+ CVEs"
    echo "  • 10,000+ Vendors"
    echo "  • 50,000+ Products"
    echo "  • 800+ CWE weakness types"
    echo "  • 500,000+ relationships"
    echo ""
    echo "Try queries in Neo4j Browser: http://localhost:7474"
    echo ""
else
    echo ""
    echo "⏸️  Neo4j load skipped"
    echo "   Run manually when ready:"
    echo "   python3 src/bootstrap/neo4j_cve_loader.py"
    echo ""
fi
