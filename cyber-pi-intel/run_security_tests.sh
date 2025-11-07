#!/bin/bash
#
# Security Testing Script for Cyber-PI-Intel
# Runs multiple security scanners and generates reports
#

set -e

echo "🔒 Running Security Tests for Cyber-PI-Intel"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Warning: Virtual environment not activated${NC}"
    echo "Consider running: source venv/bin/activate"
    echo ""
fi

# Install security tools if not present
echo "📦 Checking security tools..."
pip install -q bandit safety pip-audit ruff 2>/dev/null || true

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Running Bandit (Python Security Linter)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if bandit -r backend/ -c .bandit -f screen; then
    echo -e "${GREEN}✅ Bandit: No high-severity issues found${NC}"
else
    echo -e "${RED}❌ Bandit: Security issues detected!${NC}"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Running Safety (Dependency Vulnerability Scanner)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if safety check --json > safety-report.json 2>/dev/null; then
    echo -e "${GREEN}✅ Safety: No known vulnerabilities in dependencies${NC}"
else
    echo -e "${YELLOW}⚠️  Safety: Vulnerabilities found in dependencies${NC}"
    echo "See safety-report.json for details"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Running pip-audit (Python Package Auditor)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if pip-audit --format json > pip-audit-report.json 2>/dev/null; then
    echo -e "${GREEN}✅ pip-audit: No vulnerabilities found${NC}"
else
    echo -e "${YELLOW}⚠️  pip-audit: Vulnerabilities found${NC}"
    echo "See pip-audit-report.json for details"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  Running Ruff (Code Quality & Security Linter)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if ruff check backend/ --select=S; then  # S = flake8-bandit security rules
    echo -e "${GREEN}✅ Ruff: No security issues found${NC}"
else
    echo -e "${YELLOW}⚠️  Ruff: Security warnings detected${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Security Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Reports generated:"
echo "  - safety-report.json"
echo "  - pip-audit-report.json"
echo ""
echo -e "${GREEN}✅ Security testing complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review any warnings in the reports"
echo "  2. Update vulnerable dependencies"
echo "  3. Fix any security issues identified by Bandit"
echo "  4. Re-run tests after fixes"
echo ""
