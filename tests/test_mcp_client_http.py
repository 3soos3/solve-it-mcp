"""Integration tests for MCP HTTP transport using the official MCP SDK client.

These tests verify that the HTTP/SSE transport implementation works correctly
with the official MCP Python SDK client. Unlike the bash integration tests,
these use the same client libraries that real MCP clients would use.

Usage:
    # Run all SDK client tests
    pytest tests/test_mcp_client_http.py -v

    # Run specific test
    pytest tests/test_mcp_client_http.py::test_initialize -v

    # Skip slow tests
    pytest tests/test_mcp_client_http.py -v -m "not slow"

    # Skip integration tests in CI (they're run separately)
    pytest tests/ -m "not integration"
"""

import asyncio
import subprocess
import time

import pytest
import pytest_asyncio
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import TextContent


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


# Configuration
DEFAULT_SERVER_URL = "http://localhost:8000/mcp/v1"
SERVER_STARTUP_TIMEOUT = 10  # seconds
SERVER_SHUTDOWN_TIMEOUT = 5  # seconds


@pytest.fixture(scope="module")
def server_process(request):
    """Start MCP server for testing."""
    # Start a new server process
    print("\n[Fixture] Starting MCP server...")
    process = subprocess.Popen(
        ["python3", "src/server.py", "--transport", "http"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for server to start
    print(f"[Fixture] Waiting up to {SERVER_STARTUP_TIMEOUT}s for server startup...")
    time.sleep(SERVER_STARTUP_TIMEOUT)

    # Check if process is still running
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        pytest.fail(f"Server failed to start!\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}")

    print("[Fixture] Server started successfully")

    yield process

    # Cleanup
    print("\n[Fixture] Stopping server...")
    process.terminate()
    try:
        process.wait(timeout=SERVER_SHUTDOWN_TIMEOUT)
        print("[Fixture] Server stopped gracefully")
    except subprocess.TimeoutExpired:
        print("[Fixture] Server didn't stop gracefully, killing...")
        process.kill()
        process.wait()


@pytest.fixture(scope="module")
def server_url() -> str:
    """Get server URL."""
    return DEFAULT_SERVER_URL


@pytest.mark.asyncio
async def test_initialize(server_process, server_url):
    """Test MCP initialize handshake."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            result = await session.initialize()

            # Verify server info
            assert result.serverInfo is not None
            assert result.serverInfo.name == "solveit_mcp_server"
            assert result.serverInfo.version is not None

            # Verify protocol version (SDK may use different version)
            assert result.protocolVersion in ["2025-11-25", "2025-06-18"]

            # Verify capabilities
            assert result.capabilities is not None


@pytest.mark.asyncio
async def test_list_tools(server_process, server_url):
    """Test listing all available tools."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            # Initialize first
            await session.initialize()

            # List tools
            result = await session.list_tools()

            # Verify we have exactly 20 SOLVE-IT tools
            assert len(result.tools) == 20

            # Verify some expected tools are present
            tool_names = {tool.name for tool in result.tools}
            expected_tools = {
                "get_database_description",
                "search",
                "get_technique_details",
                "get_weakness_details",
                "get_mitigation_details",
            }
            assert expected_tools.issubset(tool_names), (
                f"Missing tools: {expected_tools - tool_names}"
            )

            # Verify each tool has required fields
            for tool in result.tools:
                assert tool.name
                assert tool.description
                assert tool.inputSchema is not None


@pytest.mark.asyncio
async def test_call_tool_get_database_description(server_process, server_url):
    """Test calling the get_database_description tool."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            # Initialize first
            await session.initialize()

            # Call tool
            result = await session.call_tool("get_database_description", {})

            # Verify result structure
            assert result.content is not None
            assert len(result.content) > 0

            # Verify content type and content
            first_content = result.content[0]
            assert isinstance(first_content, TextContent)
            assert "SOLVE-IT" in first_content.text
            assert "techniques" in first_content.text.lower()
            assert "weaknesses" in first_content.text.lower()
            assert "mitigations" in first_content.text.lower()


@pytest.mark.asyncio
async def test_call_tool_search(server_process, server_url):
    """Test calling the search tool."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            # Initialize first
            await session.initialize()

            # Search for "SQL injection"
            result = await session.call_tool(
                "search", {"query": "SQL injection", "category": "all", "limit": 5}
            )

            # Verify result
            assert result.content is not None
            assert len(result.content) > 0

            first_content = result.content[0]
            assert isinstance(first_content, TextContent)
            # Should find CWE-89 or similar SQL injection related items
            assert len(first_content.text) > 0


@pytest.mark.asyncio
async def test_call_tool_with_invalid_name(server_process, server_url):
    """Test calling a non-existent tool returns an error."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            # Initialize first
            await session.initialize()

            # Call non-existent tool - SDK returns CallToolResult with isError=True
            result = await session.call_tool("nonexistent_tool", {})

            # The SDK wraps errors in the result
            assert result.isError is True
            assert len(result.content) > 0
            error_text = result.content[0].text.lower()
            assert "nonexistent_tool" in error_text or "unknown" in error_text


@pytest.mark.asyncio
async def test_call_tool_with_invalid_arguments(server_process, server_url):
    """Test calling a tool with invalid arguments returns an error."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            # Initialize first
            await session.initialize()

            # Call search tool with invalid limit - SDK returns CallToolResult with isError=True
            result = await session.call_tool(
                "search",
                {"query": "test", "limit": -1},  # Invalid: negative limit
            )

            # Should get validation error in result
            assert result.isError is True
            assert len(result.content) > 0
            error_text = result.content[0].text.lower()
            assert "limit" in error_text or "validation" in error_text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool_name,arguments",
    [
        ("get_technique_details", {"technique_id": "T1059"}),
        ("get_weakness_details", {"weakness_id": "CWE-79"}),
        ("get_mitigation_details", {"mitigation_id": "M1038"}),
        ("list_objectives", {}),
    ],
)
async def test_call_multiple_tools(server_process, server_url, tool_name: str, arguments: dict):
    """Test calling various tools with valid arguments."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            # Initialize first
            await session.initialize()

            # Call tool
            result = await session.call_tool(tool_name, arguments)

            # Verify basic structure
            assert result.content is not None
            assert len(result.content) > 0
            assert isinstance(result.content[0], TextContent)
            assert len(result.content[0].text) > 0


@pytest.mark.asyncio
async def test_concurrent_tool_calls(server_process, server_url):
    """Test that multiple concurrent tool calls work correctly."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            # Initialize first
            await session.initialize()

            # Make multiple concurrent calls
            tasks = [
                session.call_tool("get_database_description", {}),
                session.call_tool(
                    "search", {"query": "authentication", "category": "all", "limit": 3}
                ),
                session.call_tool("list_objectives", {}),
            ]

            results = await asyncio.gather(*tasks)

            # Verify all calls succeeded
            assert len(results) == 3
            for result in results:
                assert result.content is not None
                assert len(result.content) > 0


# Performance test (optional, can be skipped with -m "not slow")
@pytest.mark.asyncio
@pytest.mark.slow
async def test_tool_call_performance(server_process, server_url):
    """Test that tool calls complete within reasonable time."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            # Initialize first
            await session.initialize()

            # Time a simple tool call
            start = time.time()
            await session.call_tool("get_database_description", {})
            elapsed = time.time() - start

            # Should complete in under 2 seconds
            assert elapsed < 2.0, f"Tool call took {elapsed:.2f}s (expected < 2.0s)"
