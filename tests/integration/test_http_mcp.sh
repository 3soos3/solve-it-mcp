#!/bin/bash
# Integration test for MCP HTTP transport
# Tests the full SOLVE-IT MCP server over HTTP/SSE

set -e

echo "=========================================="
echo "MCP HTTP Transport Integration Test"
echo "=========================================="
echo ""

# Configuration
SERVER_HOST="localhost"
SERVER_PORT="8000"
BASE_URL="http://${SERVER_HOST}:${SERVER_PORT}"
MCP_ENDPOINT="${BASE_URL}/mcp/v1/messages"
SERVER_PID=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

cleanup() {
    if [ -n "$SERVER_PID" ]; then
        log_info "Stopping server (PID: $SERVER_PID)"
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    fi
}

trap cleanup EXIT

# Start server
log_info "Starting SOLVE-IT MCP server..."
cd "$PROJECT_ROOT"
python3 src/server.py --transport http > /tmp/mcp_integration_test.log 2>&1 &
SERVER_PID=$!

log_info "Server PID: $SERVER_PID"
log_info "Waiting for server to start..."
sleep 8

# Check if server is running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    log_error "Server failed to start!"
    log_error "Check logs at /tmp/mcp_integration_test.log"
    tail -50 /tmp/mcp_integration_test.log
    exit 1
fi

log_info "Server started successfully"
echo ""

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    echo "----------------------------------------"
    echo "Test $TESTS_RUN: $test_name"
    echo "----------------------------------------"
    
    if eval "$test_command"; then
        log_info "✅ PASSED"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "❌ FAILED"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

# Test 1: Health check
run_test "Health Check (/healthz)" \
    "curl -s -f $BASE_URL/healthz | jq -e '.status == \"healthy\"' > /dev/null"

# Test 2: Readiness check
run_test "Readiness Check (/readyz)" \
    "curl -s -f $BASE_URL/readyz | jq -e '.status == \"ready\"' > /dev/null"

# Test 3: Initialize (requires Accept header)
run_test "MCP Initialize" \
    "curl -s -X POST $MCP_ENDPOINT \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json, text/event-stream' \
        -d '{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"initialize\", \"params\": {\"protocolVersion\": \"2025-11-25\", \"capabilities\": {}, \"clientInfo\": {\"name\": \"test\", \"version\": \"1.0\"}}}' \
        | grep -q 'serverInfo'"

# Test 4: Tools list
run_test "MCP Tools List" \
    "curl -s -X POST $MCP_ENDPOINT \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json, text/event-stream' \
        -d '{\"jsonrpc\": \"2.0\", \"id\": 2, \"method\": \"tools/list\", \"params\": {}}' \
        | grep -q 'get_database_description'"

# Test 5: Count tools (should have 20)
run_test "Tool Count (20 tools)" \
    "curl -s -X POST $MCP_ENDPOINT \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json, text/event-stream' \
        -d '{\"jsonrpc\": \"2.0\", \"id\": 3, \"method\": \"tools/list\", \"params\": {}}' \
        | grep -o '\"name\"' | wc -l | grep -q '20'"

# Test 6: Search tool exists
run_test "Search Tool Present" \
    "curl -s -X POST $MCP_ENDPOINT \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json, text/event-stream' \
        -d '{\"jsonrpc\": \"2.0\", \"id\": 4, \"method\": \"tools/list\", \"params\": {}}' \
        | grep -q '\"search\"'"

# Test 7: Tool call - get_database_description
run_test "Tool Call - get_database_description" \
    "curl -s -X POST $MCP_ENDPOINT \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json, text/event-stream' \
        -d '{\"jsonrpc\": \"2.0\", \"id\": 5, \"method\": \"tools/call\", \"params\": {\"name\": \"get_database_description\", \"arguments\": {}}}' \
        | grep -q 'SOLVE-IT'"

# Test 8: SSE format check (should have 'event:' and 'data:' fields)
run_test "SSE Format Compliance" \
    "curl -s -X POST $MCP_ENDPOINT \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json, text/event-stream' \
        -d '{\"jsonrpc\": \"2.0\", \"id\": 6, \"method\": \"tools/list\", \"params\": {}}' \
        | grep -E '(event: |data: )' > /dev/null"

# Test 9: Check Content-Type is SSE
run_test "SSE Content-Type Header" \
    "curl -s -I -X POST $MCP_ENDPOINT \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json, text/event-stream' \
        -d '{\"jsonrpc\": \"2.0\", \"id\": 7, \"method\": \"tools/list\", \"params\": {}}' \
        | grep -i 'content-type.*text/event-stream' > /dev/null"

# Test 10: Error without Accept header
run_test "Requires Accept Header" \
    "curl -s -X POST $MCP_ENDPOINT \
        -H 'Content-Type: application/json' \
        -d '{\"jsonrpc\": \"2.0\", \"id\": 8, \"method\": \"initialize\", \"params\": {}}' \
        | grep -q 'error'"

# Print summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Total Tests:  $TESTS_RUN"
echo -e "Passed:       ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed:       ${RED}$TESTS_FAILED${NC}"
echo "=========================================="

if [ $TESTS_FAILED -eq 0 ]; then
    log_info "✅ All tests passed!"
    exit 0
else
    log_error "❌ Some tests failed"
    log_info "Server logs at: /tmp/mcp_integration_test.log"
    exit 1
fi
