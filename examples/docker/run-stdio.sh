#!/usr/bin/env bash
# run-stdio.sh - Quick start script for running SOLVE-IT MCP in STDIO mode
# This script demonstrates how to run the Docker container with STDIO transport
# Useful for connecting with MCP clients like Claude Desktop

set -euo pipefail

DOCKER_IMAGE="${DOCKER_IMAGE:-3soos3/solve-it-mcp:latest}"

echo "Starting SOLVE-IT MCP Server in STDIO mode..."
echo "Image: ${DOCKER_IMAGE}"
echo ""
echo "NOTE: STDIO mode requires interactive input/output"
echo "Use this with MCP clients configured to run Docker commands"
echo ""

docker run -i --rm \
  --name solveit-mcp-stdio \
  -e MCP_TRANSPORT=stdio \
  -e LOG_LEVEL=INFO \
  -e OTEL_ENABLED=false \
  "${DOCKER_IMAGE}"
