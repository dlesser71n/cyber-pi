#!/bin/bash
#
# Initialize All Databases with Self-Descriptive Schemas
# Weaviate: CyberThreatIntelligence class
# Neo4j: Cyber threat intelligence graph with proper node labels
#

set -e

echo "========================================"
echo "Cyber-PI Database Initialization"
echo "Creating Self-Descriptive Schemas"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: python3 not found${NC}"
    exit 1
fi

# Check if dependencies are installed
echo "Checking dependencies..."
python3 -c "import weaviate" 2>/dev/null || {
    echo -e "${YELLOW}Installing weaviate-client...${NC}"
    pip install weaviate-client
}

python3 -c "import neo4j" 2>/dev/null || {
    echo -e "${YELLOW}Installing neo4j driver...${NC}"
    pip install neo4j
}

echo -e "${GREEN}✓ Dependencies ready${NC}"
echo ""

# Initialize Weaviate
echo "========================================"
echo "1. Initializing Weaviate"
echo "========================================"
python3 initialize-weaviate.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Weaviate initialized${NC}"
else
    echo -e "${RED}✗ Weaviate initialization failed${NC}"
    exit 1
fi
echo ""

# Initialize Neo4j
echo "========================================"
echo "2. Initializing Neo4j"
echo "========================================"
python3 initialize-neo4j.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Neo4j initialized${NC}"
else
    echo -e "${RED}✗ Neo4j initialization failed${NC}"
    exit 1
fi
echo ""

# Summary
echo "========================================"
echo -e "${GREEN}Database Initialization Complete!${NC}"
echo "========================================"
echo ""
echo "Weaviate Schema:"
echo "  Class: CyberThreatIntelligence"
echo "  Properties: 25 comprehensive fields"
echo "  URL: http://localhost:30883/v1/schema"
echo ""
echo "Neo4j Graph:"
echo "  Node Labels: CyberThreat, ThreatActor, Industry, CVE, TTP, IOC, etc."
echo "  Industries: 18 verticals initialized"
echo "  Constraints: Unique IDs for all node types"
echo "  Indexes: Performance indexes on key properties"
echo "  URL: http://localhost:30474"
echo ""
echo "Next Steps:"
echo "  1. Test threat ingestion with sample data"
echo "  2. Deploy TQAKB backend"
echo "  3. Integrate with cyber-pi collection"
echo ""
