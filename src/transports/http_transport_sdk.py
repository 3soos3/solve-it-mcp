"""HTTP transport using official MCP SDK StreamableHTTPSessionManager.

This is the CORRECT way to implement HTTP/SSE transport for MCP servers,
using the official SDK provided by https://github.com/modelcontextprotocol/python-sdk

The SDK provides:
- StreamableHTTPSessionManager: Session management, resumability, lifecycle
- StreamableHTTPServerTransport: MCP 2025-11-25 spec-compliant transport
- Full SSE support with event IDs, Last-Event-ID resumption
- Stateless and stateful modes
- Proper error handling and security

Why use the SDK instead of custom implementation:
- Spec-compliant (MCP 2025-11-25)
- Battle-tested and maintained
- Handles edge cases properly
- Gets updates when spec changes
- Less code to maintain

Typical usage:
    >>> from mcp.server.lowlevel import Server
    >>> from config import HTTPConfig
    >>> from transports.http_transport_sdk import create_mcp_http_app
    >>>
    >>> mcp_server = Server("my-server")
    >>> # Register tools...
    >>> app = create_mcp_http_app(mcp_server, config)
    >>> # Run with uvicorn
"""

import contextlib
from collections.abc import AsyncIterator

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
import uvicorn

from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from config import HTTPConfig
from utils.logging import get_logger

logger = get_logger(__name__)


def create_mcp_http_app(mcp_server: Server, config: HTTPConfig) -> Starlette:
    """Create a Starlette ASGI app with MCP HTTP transport.

    This uses the official MCP SDK's StreamableHTTPSessionManager for
    proper MCP 2025-11-25 spec compliance.

    Args:
        mcp_server: MCP server instance with tools/resources registered
        config: HTTP configuration

    Returns:
        Starlette ASGI application ready for Uvicorn

    Examples:
        >>> server = Server("solveit")
        >>> # Register tools...
        >>> app = create_mcp_http_app(server, HTTPConfig())
        >>> uvicorn.run(app, host="0.0.0.0", port=8000)
    """
    # Create session manager (stateless mode for MVP)
    session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        event_store=None,  # No resumability for MVP (can add later)
        json_response=False,  # Use SSE streams (spec-compliant)
        stateless=config.stateless,  # Stateless for horizontal scaling
    )

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Lifespan context manager for the app.

        This starts and stops the session manager properly.
        """
        logger.info("Starting MCP HTTP session manager")
        async with session_manager.run():
            logger.info("MCP HTTP session manager ready")
            yield
        logger.info("MCP HTTP session manager stopped")

    # Health check endpoint
    async def health_check(request: Request) -> JSONResponse:
        """Health check for Kubernetes liveness probe."""
        return JSONResponse({"status": "healthy", "service": "solveit-mcp-server"})

    async def readiness_check(request: Request) -> JSONResponse:
        """Readiness check for Kubernetes readiness probe."""
        return JSONResponse({"status": "ready", "service": "solveit-mcp-server"})

    # CORS middleware
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=config.cors.allowed_origins,
            allow_methods=config.cors.allowed_methods,
            allow_headers=config.cors.allowed_headers,
            expose_headers=config.cors.expose_headers,
            max_age=config.cors.max_age,
        )
    ]

    # Create Starlette app
    app = Starlette(
        debug=False,
        routes=[
            # Health checks (Kubernetes standard)
            Route("/healthz", health_check, methods=["GET"]),
            Route("/readyz", readiness_check, methods=["GET"]),
            # Legacy health checks (backward compatibility)
            Route("/health", health_check, methods=["GET"]),
            Route("/ready", readiness_check, methods=["GET"]),
            # MCP endpoint - mount the session manager at base path
            # The SDK handles GET and POST automatically
            Mount(config.base_path, app=session_manager.handle_request),
        ],
        middleware=middleware,
        lifespan=lifespan,
    )

    logger.info(
        f"MCP HTTP app created: base_path={config.base_path}, "
        f"stateless={config.stateless}, cors_origins={config.cors.allowed_origins}"
    )

    return app


async def run_http_server(mcp_server: Server, config: HTTPConfig) -> None:
    """Run the MCP HTTP server.

    This is a convenience function that creates the app and runs it with Uvicorn.

    Args:
        mcp_server: MCP server instance
        config: HTTP configuration

    Examples:
        >>> server = Server("solveit")
        >>> # Register tools...
        >>> await run_http_server(server, HTTPConfig())
    """
    app = create_mcp_http_app(mcp_server, config)

    logger.info(f"Starting HTTP server on {config.host}:{config.port}")
    logger.info(f"MCP endpoint: http://{config.host}:{config.port}{config.base_path}/messages")
    logger.info(f"Health check: http://{config.host}:{config.port}/healthz")

    # Run with Uvicorn
    uvicorn_config = uvicorn.Config(
        app,
        host=config.host,
        port=config.port,
        workers=config.workers,
        log_level="info",
    )
    server_instance = uvicorn.Server(uvicorn_config)
    await server_instance.serve()
