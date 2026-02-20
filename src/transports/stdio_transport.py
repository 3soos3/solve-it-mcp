"""STDIO transport implementation for MCP server.

This module provides the standard input/output transport for the MCP server,
enabling local process communication. This is the traditional transport used
for CLI tools and desktop applications like Claude Desktop.

The STDIO transport:
- Reads JSON-RPC requests from stdin
- Writes JSON-RPC responses to stdout
- Logs to stderr to avoid polluting the protocol stream
- Supports single client per process

Typical usage:
    >>> from mcp.server.lowlevel import Server
    >>> from transports import run_stdio_server
    >>> 
    >>> server = create_server()
    >>> await run_stdio_server(server)

Integration:
    Works with MCP clients that spawn server processes:
    - Claude Desktop
    - MCP CLI tools
    - Custom process-based integrations
"""

import logging
import traceback
from typing import Any

# MCP SDK imports
try:
    import mcp.server.stdio
    from mcp.server.lowlevel import NotificationOptions, Server
    from mcp.server.models import InitializationOptions
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = Any

from utils.logging import get_logger


# Module-level logger
logger = get_logger(__name__)


async def run_stdio_server(server: Server) -> None:
    """Run MCP server with STDIO transport.
    
    This function encapsulates the STDIO transport logic, handling the
    complete lifecycle of the server communication including:
    - STDIO stream establishment
    - Server initialization with capabilities
    - Request/response loop
    - Error handling and logging
    - Graceful shutdown
    
    The function runs until interrupted (Ctrl+C) or a fatal error occurs.
    All protocol communication happens via stdin/stdout, while logs go
    to stderr.
    
    Args:
        server: Configured MCP server instance ready to run. The server
            should have all tools registered and handlers configured.
    
    Raises:
        RuntimeError: If MCP SDK is not available (missing dependency)
        Exception: If server encounters unrecoverable errors
    
    Examples:
        Basic usage:
        
        >>> from mcp.server.lowlevel import Server
        >>> from transports import run_stdio_server
        >>> 
        >>> server = Server("my-mcp-server")
        >>> # ... register tools and handlers ...
        >>> await run_stdio_server(server)
        
        With error handling:
        
        >>> try:
        ...     await run_stdio_server(server)
        ... except KeyboardInterrupt:
        ...     logger.info("Server interrupted by user")
        ... except Exception as e:
        ...     logger.error(f"Server failed: {e}")
        
        In asyncio context:
        
        >>> async def main():
        ...     server = create_configured_server()
        ...     await run_stdio_server(server)
        >>> 
        >>> asyncio.run(main())
    
    Protocol Details:
        The STDIO transport uses JSON-RPC 2.0 protocol:
        - Requests are read from stdin line-by-line
        - Responses are written to stdout line-by-line
        - Each line is a complete JSON-RPC message
        - Stderr is used for logging (not part of protocol)
    
    Lifecycle:
        1. Establish STDIO streams
        2. Wait for initialize request from client
        3. Send capabilities in initialize response
        4. Process tool calls and other requests
        5. Handle shutdown request
        6. Clean up and exit
    
    Error Handling:
        - KeyboardInterrupt (Ctrl+C): Graceful shutdown
        - ExceptionGroup: Logs all exceptions in group
        - Other exceptions: Logged with full traceback, then re-raised
    
    Note:
        This function blocks until the server shuts down. It should be
        the last call in your main() function for STDIO mode.
    
    Integration:
        For Claude Desktop configuration:
        ```json
        {
          "mcpServers": {
            "solveit": {
              "command": "python",
              "args": ["/path/to/server.py"],
              "cwd": "/path/to/directory"
            }
          }
        }
        ```
    """
    if not MCP_AVAILABLE:
        raise RuntimeError(
            "MCP SDK not available. Install with: pip install mcp>=1.0.0"
        )
    
    logger.info("Starting STDIO transport server")
    logger.info("Ready to accept MCP connections via STDIO")
    
    try:
        # Establish STDIO transport
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.info("STDIO transport established, starting server run loop")
            
            # Run the server with initialization options
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="solveit_mcp_server",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt (Ctrl+C), shutting down gracefully")
        # Graceful shutdown - no need to re-raise
    
    except Exception as e:
        # Check if this is an ExceptionGroup (from asyncio.TaskGroup)
        # ExceptionGroup is a Python 3.11+ feature for grouping multiple exceptions
        if hasattr(e, 'exceptions') and hasattr(e, '__class__') and 'ExceptionGroup' in str(type(e)):
            logger.critical(
                f"Server run loop failed with ExceptionGroup containing "
                f"{len(e.exceptions)} exception(s):"
            )
            
            # Log each exception in the group
            for i, exc in enumerate(e.exceptions):
                logger.critical(f"  Exception {i+1}: {type(exc).__name__}: {exc}")
                logger.critical(
                    f"  Traceback: "
                    f"{''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))}"
                )
        else:
            # Handle regular exceptions
            logger.critical(f"Server run loop failed: {type(e).__name__}: {e}")
            logger.critical(
                f"Full traceback: "
                f"{''.join(traceback.format_exception(type(e), e, e.__traceback__))}"
            )
        
        logger.critical("Server terminating due to critical error")
        raise  # Re-raise to propagate error to caller
    
    finally:
        logger.info("STDIO transport shutdown completed")
