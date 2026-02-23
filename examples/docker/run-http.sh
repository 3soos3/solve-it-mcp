#!/usr/bin/env bash
# run-http.sh - Quick start script for running SOLVE-IT MCP in HTTP mode
# This script demonstrates how to run the Docker container with HTTP/SSE transport

set -euo pipefail

DOCKER_IMAGE="${DOCKER_IMAGE:-3soos3/solve-it-mcp:latest}"
HTTP_PORT="${HTTP_PORT:-8000}"

echo "Starting SOLVE-IT MCP Server in HTTP mode..."
echo "Image: ${DOCKER_IMAGE}"
echo "Port:  ${HTTP_PORT}"
echo ""

docker run -it --rm \
  --name solveit-mcp-http \
  -p "${HTTP_PORT}:8000" \
  -e MCP_TRANSPORT=http \
  -e HTTP_PORT=8000 \
  -e LOG_LEVEL=INFO \
  -e OTEL_ENABLED=false \
  "${DOCKER_IMAGE}"
