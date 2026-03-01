"""MCP transport layer implementations.

This package provides different transport implementations for the MCP server:

- stdio_transport: Standard input/output transport for local/CLI usage
- http_transport_sdk: HTTP/SSE transport using official MCP SDK (recommended)

The transport layer abstracts the communication protocol from the core MCP
server logic, enabling the same server to work over different transports.

Typical usage:
    >>> from transports import run_stdio_server, run_http_server
    >>> from config import load_config
    >>>
    >>> config = load_config()
    >>> if config.transport == "stdio":
    ...     await run_stdio_server(server)
    ... elif config.transport == "http":
    ...     await run_http_server(server, config.http)
"""

from .stdio_transport import run_stdio_server

# HTTP transport import is conditional to avoid dependency issues
try:
    from .http_transport_sdk import run_http_server, create_mcp_http_app

    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False
    run_http_server = None
    create_mcp_http_app = None


__all__ = [
    "HTTP_AVAILABLE",
    "run_stdio_server",
    "run_http_server",
    "create_mcp_http_app",
]
