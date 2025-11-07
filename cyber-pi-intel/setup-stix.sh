#!/bin/bash
#
# Setup STIX 2.1 Support for cyber-pi
# Install all required libraries for industry-standard threat intelligence
#

set -e

echo "========================================"
echo "STIX 2.1 Setup for cyber-pi"
echo "Industry-Standard Threat Intelligence"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Python version
echo "Checking Python version..."
python3 --version
echo ""

# Install STIX libraries
echo "Installing STIX 2.1 libraries..."
pip install stix2==3.0.1
pip install stix2-patterns==2.0.0
pip install taxii2-client==2.3.0

echo -e "${GREEN}✓ STIX libraries installed${NC}"
echo ""

# Verify installation
echo "Verifying STIX installation..."
python3 -c "import stix2; print(f'✓ stix2 {stix2.__version__}')"
python3 -c "import stix2.patterns; print('✓ stix2-patterns installed')"
python3 -c "import taxii2client; print('✓ taxii2-client installed')"
echo ""

# Test STIX converter
echo "Testing STIX converter..."
python3 -c "
from backend.core.stix_converter import STIXConverter
converter = STIXConverter()
print('✓ STIXConverter initialized successfully')
"
echo ""

echo "========================================"
echo -e "${GREEN}STIX 2.1 Setup Complete!${NC}"
echo "========================================"
echo ""
echo "Installed Libraries:"
echo "  - stix2: Official STIX 2.1 library"
echo "  - stix2-patterns: Pattern matching"
echo "  - taxii2-client: Feed sharing (TAXII protocol)"
echo ""
echo "Next Steps:"
echo "  1. Initialize databases: ./initialize-all.sh"
echo "  2. Test STIX conversion with sample data"
echo "  3. Import external STIX feed (optional)"
echo ""
echo "Example Usage:"
echo "  from backend.core.stix_converter import convert_threat_to_stix"
echo "  bundle = convert_threat_to_stix(threat_dict)"
echo ""
