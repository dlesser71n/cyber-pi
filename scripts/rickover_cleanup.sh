#!/bin/bash
#
# Rickover-Level Cleanup Script
# Executes Phase 1: File Organization
#
# Date: November 4, 2025
# Standard: Production-ready, maintainable
#

set -e  # Exit on error

echo "=========================================="
echo "🔧 RICKOVER-LEVEL CLEANUP"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ROOT="/home/david/projects/cyber-pi"
ARCHIVE_DIR="$PROJECT_ROOT/archive/2025-11-04"

cd "$PROJECT_ROOT"

echo "Phase 1: Archive Duplicate Collectors"
echo "--------------------------------------"

# Archive duplicate collectors
DUPLICATE_COLLECTORS=(
    "enhanced_collector.py"
    "enhanced_intelligence_collector.py"
    "comprehensive_intelligence_collection.py"
    "focused_intelligence_collection.py"
    "integrated_unified_collector.py"
    "parallel_master.py"
)

for file in "${DUPLICATE_COLLECTORS[@]}"; do
    if [ -f "src/collectors/$file" ]; then
        echo -e "${YELLOW}Archiving${NC} src/collectors/$file"
        mv "src/collectors/$file" "$ARCHIVE_DIR/collectors/"
    fi
done

echo ""
echo "Phase 2: Archive Experimental Financial Code"
echo "--------------------------------------"

# Archive experimental financial intelligence code
FINANCIAL_FILES=(
    "src/collectors/financial_threat_collector.py"
    "src/intelligence/options_threat_analyzer.py"
    "src/intelligence/options_threat_analyzer_fast.py"
    "src/intelligence/financial_options_database.py"
    "src/intelligence/ibkr_financial_integration.py"
    "src/intelligence/financial_threat_analyzer.py"
)

for file in "${FINANCIAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${YELLOW}Archiving${NC} $file"
        mv "$file" "$ARCHIVE_DIR/intelligence/"
    fi
done

echo ""
echo "Phase 3: Move Test Files"
echo "--------------------------------------"

# Move test files to tests/validation/
TEST_FILES=(
    "test_financial_collector.py"
    "test_two_stage_financial.py"
    "test_optimized_batch.py"
    "test_ibkr_200_tickers.py"
    "check_ibkr_subscriptions.py"
)

for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${YELLOW}Moving${NC} $file → tests/validation/"
        mv "$file" "tests/validation/"
    fi
done

echo ""
echo "Phase 4: Archive Session Documentation"
echo "--------------------------------------"

# Archive old session summaries
DOC_FILES=(
    "SESSION_COMPLETE_FINANCIAL_INTEGRATION.md"
    "SESSION_SUMMARY_SECURITY_METHODOLOGY.md"
    "TASKS_FOLLOWUP.md"
)

for file in "${DOC_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${YELLOW}Archiving${NC} $file"
        mv "$file" "$ARCHIVE_DIR/docs/"
    fi
done

echo ""
echo "Phase 5: Create Directory READMEs"
echo "--------------------------------------"

# Create README for tests/
cat > tests/README.md << 'EOF'
# Tests

## Structure

- `unit/` - Unit tests for individual functions
- `integration/` - Integration tests for complete workflows
- `validation/` - Validation and experimental test scripts

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
```

## Adding Tests

1. Unit tests go in `unit/`
2. Integration tests go in `integration/`
3. Validation scripts go in `validation/`
EOF

echo -e "${GREEN}Created${NC} tests/README.md"

# Create README for archive/
cat > archive/README.md << 'EOF'
# Archive

This directory contains old, experimental, or superseded code.

## Structure

- `2025-11-04/` - Rickover cleanup archive
  - `collectors/` - Old collector implementations
  - `intelligence/` - Experimental intelligence modules
  - `tests/` - Old test files
  - `docs/` - Superseded documentation

## Policy

- Code is archived, not deleted
- Can be restored if needed
- Organized by date for easy reference
EOF

echo -e "${GREEN}Created${NC} archive/README.md"

echo ""
echo "=========================================="
echo "✅ CLEANUP COMPLETE"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - Archived ${#DUPLICATE_COLLECTORS[@]} duplicate collectors"
echo "  - Archived ${#FINANCIAL_FILES[@]} experimental financial files"
echo "  - Moved ${#TEST_FILES[@]} test files to tests/validation/"
echo "  - Archived ${#DOC_FILES[@]} old documentation files"
echo "  - Created directory READMEs"
echo ""
echo "Next steps:"
echo "  1. Review archived files in archive/2025-11-04/"
echo "  2. Proceed with Phase 2: Code Quality"
echo "  3. See RICKOVER_CLEANUP_PLAN.md for details"
echo ""
