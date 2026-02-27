#!/bin/bash

# Pre-Push Check Script
# Runs all CI checks locally before pushing to GitHub
# Usage: bash scripts/pre-push-check.sh

set -e  # Exit on first error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILED_CHECKS=()

echo "=================================================="
echo "  Running Local CI Checks Before Push"
echo "=================================================="
echo ""

# Function to run check and track failures
run_check() {
    local check_name=$1
    shift
    echo "=== ${check_name} ==="
    if "$@"; then
        echo -e "${GREEN}✅ ${check_name} PASSED${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}❌ ${check_name} FAILED${NC}"
        FAILED_CHECKS+=("${check_name}")
        echo ""
        return 1
    fi
}

# 1. YAML Linting
run_check "YAML Linting" yamllint .github/workflows/ || true

# 2. Ruff Linting
run_check "Ruff Linting" ruff check src/ tests/ || true

# 3. Black Formatting
run_check "Black Formatting" black --check src/ tests/ || true

# 4. Type Checking (non-blocking)
echo "=== Type Checking (non-blocking) ==="
if mypy src/; then
    echo -e "${GREEN}✅ Type Checking PASSED${NC}"
else
    echo -e "${YELLOW}⚠️  Type checking had errors (non-blocking)${NC}"
fi
echo ""

# 5. Unit Tests
echo "=== Unit Tests ==="
if pytest tests/ -q --tb=short; then
    echo -e "${GREEN}✅ Unit Tests PASSED${NC}"
else
    echo -e "${RED}❌ Unit Tests FAILED${NC}"
    FAILED_CHECKS+=("Unit Tests")
fi
echo ""

# Summary
echo "=================================================="
echo "  Check Summary"
echo "=================================================="
echo ""

if [ ${#FAILED_CHECKS[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Safe to push.${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ ${#FAILED_CHECKS[@]} check(s) failed:${NC}"
    for check in "${FAILED_CHECKS[@]}"; do
        echo "  - $check"
    done
    echo ""
    echo "Fix issues before pushing:"
    echo "  - Ruff:  ruff check --fix src/ tests/"
    echo "  - Black: black src/ tests/"
    echo "  - YAML:  sed -i 's/[[:space:]]*$//' .github/workflows/*.yml"
    echo ""
    exit 1
fi
