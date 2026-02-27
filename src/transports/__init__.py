"""MCP transport layer implementations.

This package provides different transport implementations for the MCP server:

- stdio_transport: Standard input/output transport for local/CLI usage
- http_transport: HTTP/SSE transport for web clients and Kubernetes deployment

The transport layer abstracts the communication protocol from the core MCP
server logic, enabling the same server to work over different transports.

Typical usage:
    >>> from transports import run_stdio_server, HTTPTransportManager
    >>> from config import load_config
    >>>
    >>> config = load_config()
    >>> if config.transport == "stdio":
    ...     await run_stdio_server(server)
    ... elif config.transport == "http":
    ...     http_manager = HTTPTransportManager(server, config.http)
    ...     await http_manager.run()
"""

from .stdio_transport import run_stdio_server

# HTTP transport import is conditional to avoid dependency issues
try:
    from .http_transport import HTTPTransportManager

    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False
    HTTPTransportManager = None


__all__ = [
    "HTTP_AVAILABLE",
    "HTTPTransportManager",
    "run_stdio_server",
]
