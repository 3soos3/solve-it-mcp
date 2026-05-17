"""Integration tests for MCP HTTP transport using the official MCP SDK client.

These tests verify that the HTTP/SSE transport implementation works correctly
with the official MCP Python SDK client. Unlike the bash integration tests,
these use the same client libraries that real MCP clients would use.

Usage:
    # Run against a locally spawned server (default)
    pytest tests/test_mcp_client_http.py -v

    # Run against an already-running server or container
    pytest tests/test_mcp_client_http.py -v --server-url http://localhost:8000/mcp/v1

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
SERVER_STARTUP_TIMEOUT = 15  # seconds to wait for local server to start
SERVER_SHUTDOWN_TIMEOUT = 5  # seconds


@pytest.fixture(scope="module")
def server_url(request) -> str:
    """Return the MCP server URL to test against."""
    url = request.config.getoption("--server-url")
    return url if url else DEFAULT_SERVER_URL


@pytest.fixture(scope="module")
def server_process(request, server_url):
    """Start a local MCP server if no --server-url was provided.

    When --server-url is given the server is assumed to already be running
    (e.g. a Docker container) and this fixture is a no-op.
    """
    external_url = request.config.getoption("--server-url")

    if external_url:
        # Nothing to start — the caller is responsible for the server
        print(f"\n[Fixture] Using external server at {external_url}")
        yield None
        return

    # Spawn a local server process
    print("\n[Fixture] Starting local MCP server...")
    process = subprocess.Popen(
        ["python3", "src/server.py", "--transport", "http"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    print(f"[Fixture] Waiting up to {SERVER_STARTUP_TIMEOUT}s for server startup...")
    time.sleep(SERVER_STARTUP_TIMEOUT)

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


@pytest.mark.asyncio
async def test_initialize(server_process, server_url):
    """Test MCP initialize handshake."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            result = await session.initialize()

            assert result.serverInfo is not None
            assert result.serverInfo.name == "solveit_mcp_server"
            assert result.serverInfo.version is not None
            assert result.protocolVersion in ["2025-11-25", "2025-06-18"]
            assert result.capabilities is not None


@pytest.mark.asyncio
async def test_list_tools(server_process, server_url):
    """Test listing all available tools."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()

            # 20 original + get_citation + get_objectives_for_technique + resolve_inline_citations + get_mitigations_for_technique = 24
            assert len(result.tools) == 24, (
                f"Expected 24 tools, got {len(result.tools)}: "
                f"{[t.name for t in result.tools]}"
            )

            tool_names = {tool.name for tool in result.tools}
            expected_tools = {
                "get_database_description",
                "search",
                "get_technique_details",
                "get_weakness_details",
                "get_mitigation_details",
                "get_citation",
                "get_objectives_for_technique",
            }
            assert expected_tools.issubset(tool_names), (
                f"Missing tools: {expected_tools - tool_names}"
            )

            for tool in result.tools:
                assert tool.name
                assert tool.description
                assert tool.inputSchema is not None


@pytest.mark.asyncio
async def test_call_tool_get_database_description(server_process, server_url):
    """Test calling the get_database_description tool."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_database_description", {})

            assert result.content is not None
            assert len(result.content) > 0
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
            await session.initialize()
            result = await session.call_tool(
                "search", {"keywords": "memory acquisition", "limit": 5}
            )

            assert result.content is not None
            assert len(result.content) > 0
            first_content = result.content[0]
            assert isinstance(first_content, TextContent)
            assert len(first_content.text) > 0


@pytest.mark.asyncio
async def test_call_tool_list_objectives(server_process, server_url):
    """Test that list_objectives returns objectives."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("list_objectives", {})

            assert result.content is not None
            assert len(result.content) > 0
            first_content = result.content[0]
            assert isinstance(first_content, TextContent)
            assert len(first_content.text) > 0


@pytest.mark.asyncio
async def test_call_tool_with_invalid_name(server_process, server_url):
    """Test calling a non-existent tool returns an error."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("nonexistent_tool", {})

            assert result.isError is True
            assert len(result.content) > 0
            error_text = result.content[0].text.lower()
            assert "nonexistent_tool" in error_text or "unknown" in error_text


@pytest.mark.asyncio
async def test_call_tool_with_invalid_arguments(server_process, server_url):
    """Test calling a tool with missing required arguments returns a validation error."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # search requires 'keywords' — omitting it should fail validation
            result = await session.call_tool(
                "search",
                {},  # missing required 'keywords' field
            )

            assert result.isError is True
            assert len(result.content) > 0
            error_text = result.content[0].text.lower()
            assert "keyword" in error_text or "validation" in error_text or "required" in error_text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool_name,arguments",
    [
        # Use SOLVE-IT DFT/DFW/DFM ID format (not MITRE ATT&CK or CWE)
        ("get_technique_details", {"technique_id": "DFT-1001"}),
        ("get_weakness_details", {"weakness_id": "DFW-1001"}),
        ("get_mitigation_details", {"mitigation_id": "DFM-1001"}),
        ("list_objectives", {}),
        ("get_all_techniques_with_name_and_id", {}),
    ],
)
async def test_call_multiple_tools(server_process, server_url, tool_name: str, arguments: dict):
    """Test calling various tools with valid arguments."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)

            assert result.content is not None
            assert len(result.content) > 0
            assert isinstance(result.content[0], TextContent)
            assert len(result.content[0].text) > 0


@pytest.mark.asyncio
async def test_concurrent_tool_calls(server_process, server_url):
    """Test that multiple concurrent tool calls work correctly."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tasks = [
                session.call_tool("get_database_description", {}),
                session.call_tool("search", {"keywords": "volatile memory", "limit": 3}),
                session.call_tool("list_objectives", {}),
            ]

            results = await asyncio.gather(*tasks)

            assert len(results) == 3
            for result in results:
                assert result.content is not None
                assert len(result.content) > 0


@pytest.mark.asyncio
@pytest.mark.slow
async def test_tool_call_performance(server_process, server_url):
    """Test that tool calls complete within reasonable time."""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()

            start = time.time()
            await session.call_tool("get_database_description", {})
            elapsed = time.time() - start

            assert elapsed < 2.0, f"Tool call took {elapsed:.2f}s (expected < 2.0s)"
