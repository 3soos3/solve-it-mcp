#!/bin/bash
# Cleanup script for SOLVE-IT MCP Server
# Removes temporary files, caches, and build artifacts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Cleaning SOLVE-IT MCP Server..."
echo "Project root: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Python cache files
echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

# Build artifacts
echo "Removing build artifacts..."
rm -rf build/ dist/ *.egg-info 2>/dev/null || true

# Test artifacts
echo "Removing test artifacts..."
rm -rf .coverage htmlcov/ .pytest_cache/ 2>/dev/null || true
find . -type f -name ".coverage.*" -delete 2>/dev/null || true

# Temporary files
echo "Removing temporary files..."
find . -type f -name "*.log" -not -path "./.git/*" -delete 2>/dev/null || true
find . -type f -name "*~" -delete 2>/dev/null || true
find . -type f -name "*.bak" -delete 2>/dev/null || true
find . -type f -name "*.swp" -delete 2>/dev/null || true

# MkDocs build
echo "Removing MkDocs build artifacts..."
rm -rf site/ 2>/dev/null || true

# Docker volumes (optional - commented out for safety)
# echo "Removing Docker volumes..."
# docker-compose down -v 2>/dev/null || true

echo "✅ Cleanup complete!"
echo ""
echo "To rebuild:"
echo "  pip install -e ."
echo "  mkdocs build"
