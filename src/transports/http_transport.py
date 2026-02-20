"""HTTP/SSE transport implementation for MCP server.

This module provides HTTP and Server-Sent Events (SSE) transport for the MCP
server, enabling web clients and Kubernetes deployments. The transport supports:

- Stateless HTTP with JSON responses (for REST-like clients)
- Server-Sent Events (SSE) streaming (for real-time updates)
- CORS support for web browser clients
- Health and readiness probes for Kubernetes
- Session management via headers

The HTTP transport is built on Starlette (ASGI framework) and runs via Uvicorn,
providing production-ready async HTTP serving with WebSocket support.

Architecture:
    Client → HTTP Request → Starlette App → MCP Server → Response
    
    For SSE:
    Client ← SSE Stream ← Starlette App ← MCP Server ← Events

Typical usage:
    >>> from mcp.server.lowlevel import Server
    >>> from config import HTTPConfig
    >>> from transports import HTTPTransportManager
    >>> 
    >>> config = HTTPConfig(host="0.0.0.0", port=8000)
    >>> server = create_mcp_server()
    >>> manager = HTTPTransportManager(server, config)
    >>> await manager.run()

Kubernetes Integration:
    The transport provides health check endpoints that Kubernetes uses:
    - /health: Liveness probe (is the server running?)
    - /ready: Readiness probe (is the server ready to accept traffic?)

Content Negotiation:
    Clients can request their preferred response format via Accept header:
    - Accept: application/json → JSON response (default)
    - Accept: text/event-stream → SSE streaming

Security:
    - CORS configured via HTTPConfig
    - Session IDs tracked via Mcp-Session-Id header
    - Stateless mode prevents session hijacking
    - Rate limiting can be added via middleware
"""

from typing import Any, Optional
import json
import uuid
import logging

# ASGI framework imports
try:
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    from starlette.requests import Request
    from starlette.responses import Response, StreamingResponse, JSONResponse
    import uvicorn
    STARLETTE_AVAILABLE = True
except ImportError:
    STARLETTE_AVAILABLE = False
    Starlette = None
    uvicorn = None

# MCP SDK imports
try:
    from mcp.server.lowlevel import Server
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = Any

from config import HTTPConfig
from utils.logging import get_logger


# Module-level logger
logger = get_logger(__name__)


class HTTPTransportManager:
    """Manages HTTP/SSE transport for MCP server.
    
    This class handles the complete HTTP transport layer including:
    - Starlette ASGI application setup
    - Route configuration for MCP endpoints
    - CORS middleware for web clients
    - Health/readiness endpoints for Kubernetes
    - JSON and SSE response handling
    - Uvicorn server lifecycle
    
    The manager creates a stateless transport where each request is independent,
    enabling horizontal scaling across multiple Kubernetes pods.
    
    Attributes:
        mcp_server: MCP server instance to handle requests
        config: HTTP transport configuration
        app: Starlette ASGI application instance
    
    Examples:
        Basic usage:
        
        >>> from mcp.server.lowlevel import Server
        >>> from config import HTTPConfig
        >>> 
        >>> config = HTTPConfig(host="0.0.0.0", port=8000)
        >>> mcp_server = Server("my-server")
        >>> manager = HTTPTransportManager(mcp_server, config)
        >>> await manager.run()
        
        Custom configuration:
        
        >>> config = HTTPConfig(
        ...     host="0.0.0.0",
        ...     port=8080,
        ...     workers=4,
        ...     sse_enabled=True,
        ...     cors=CORSConfig(allowed_origins=["https://app.example.com"])
        ... )
        >>> manager = HTTPTransportManager(mcp_server, config)
        >>> await manager.run()
        
        In production with Kubernetes:
        
        >>> # Environment variables set by Kubernetes
        >>> # HTTP_HOST=0.0.0.0, HTTP_PORT=8000
        >>> from config import load_config
        >>> config = load_config()
        >>> manager = HTTPTransportManager(mcp_server, config.http)
        >>> await manager.run()
    
    Kubernetes Integration:
        The manager provides health check endpoints:
        
        ```yaml
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
        ```
    
    Performance:
        - Stateless design enables horizontal scaling
        - Async I/O for high concurrency
        - Uvicorn worker processes for CPU parallelism
        - Connection pooling handled by Uvicorn
    
    Note:
        Requires starlette and uvicorn dependencies. The class gracefully
        handles missing dependencies by raising RuntimeError.
    """
    
    def __init__(self, mcp_server: Server, config: HTTPConfig):
        """Initialize HTTP transport manager.
        
        Args:
            mcp_server: Configured MCP server instance with tools registered
            config: HTTP transport configuration including host, port, CORS settings
        
        Raises:
            RuntimeError: If Starlette/Uvicorn dependencies are not available
        
        Examples:
            >>> from config import HTTPConfig
            >>> config = HTTPConfig()
            >>> manager = HTTPTransportManager(mcp_server, config)
        """
        if not STARLETTE_AVAILABLE:
            raise RuntimeError(
                "Starlette/Uvicorn not available. Install with: "
                "pip install starlette uvicorn[standard]"
            )
        
        if not MCP_AVAILABLE:
            raise RuntimeError(
                "MCP SDK not available. Install with: pip install mcp>=1.0.0"
            )
        
        self.mcp_server = mcp_server
        self.config = config
        self.app = self._create_app()
        
        logger.info(
            f"HTTP transport manager initialized: "
            f"sse_enabled={config.sse_enabled}, "
            f"stateless={config.stateless}"
        )
    
    def _create_app(self) -> Starlette:
        """Create Starlette ASGI application with routes and middleware.
        
        Configures the complete ASGI application including:
        - CORS middleware for web clients
        - Route handlers for MCP endpoints
        - Health check endpoints
        - Error handling
        
        Returns:
            Starlette: Configured ASGI application ready to serve
        
        Routes Created:
            - POST /mcp/v1/messages: JSON-based MCP requests
            - GET /mcp/v1/sse: SSE streaming (if enabled)
            - GET /health: Kubernetes liveness probe
            - GET /ready: Kubernetes readiness probe
        
        Examples:
            >>> app = manager._create_app()
            >>> # App is now ready for Uvicorn
        
        Note:
            This is an internal method called during initialization.
            The returned app is stored in self.app.
        """
        # CORS middleware configuration
        middleware = [
            Middleware(
                CORSMiddleware,
                allow_origins=self.config.cors.allowed_origins,
                allow_methods=self.config.cors.allowed_methods,
                allow_headers=self.config.cors.allowed_headers,
                expose_headers=self.config.cors.expose_headers,
                max_age=self.config.cors.max_age,
            )
        ]
        
        # Build routes list
        routes = [
            # MCP JSON endpoint (always enabled)
            Route(
                f"{self.config.base_path}/messages",
                self.handle_json_request,
                methods=["POST", "OPTIONS"]
            ),
            
            # Health check endpoints
            Route(self.config.health_path, self.health_check, methods=["GET"]),
            Route(self.config.ready_path, self.readiness_check, methods=["GET"]),
        ]
        
        # Add SSE endpoint if enabled
        if self.config.sse_enabled:
            routes.append(
                Route(
                    f"{self.config.base_path}/sse",
                    self.handle_sse_request,
                    methods=["GET"]
                )
            )
            logger.debug("SSE endpoint enabled")
        
        # Create Starlette application
        app = Starlette(
            debug=False,  # Never enable debug in production
            routes=routes,
            middleware=middleware,
        )
        
        logger.debug(
            f"Starlette app created: {len(routes)} routes, "
            f"CORS origins={self.config.cors.allowed_origins}"
        )
        
        return app
    
    async def handle_json_request(self, request: Request) -> JSONResponse:
        """Handle JSON-based MCP requests (stateless mode).
        
        This endpoint handles standard MCP JSON-RPC requests, providing
        a REST-like interface for MCP clients. Each request is independent
        (stateless), enabling horizontal scaling.
        
        Request Flow:
            1. Extract or generate session ID from headers
            2. Parse JSON-RPC request body
            3. Forward to MCP server for processing
            4. Return JSON-RPC response
        
        Args:
            request: Starlette HTTP request object containing MCP JSON-RPC
        
        Returns:
            JSONResponse: MCP JSON-RPC response with session ID header
        
        Request Headers:
            - Mcp-Session-Id (optional): Client-provided session ID
            - Content-Type: application/json
            - Accept: application/json (optional)
        
        Response Headers:
            - Mcp-Session-Id: Session ID (generated or echoed)
            - Content-Type: application/json
        
        Examples:
            Request:
            ```
            POST /mcp/v1/messages HTTP/1.1
            Content-Type: application/json
            
            {
              "jsonrpc": "2.0",
              "method": "tools/list",
              "id": 1
            }
            ```
            
            Response:
            ```
            HTTP/1.1 200 OK
            Content-Type: application/json
            Mcp-Session-Id: http_a1b2c3d4e5f6
            
            {
              "jsonrpc": "2.0",
              "result": {
                "tools": [...]
              },
              "id": 1
            }
            ```
        
        Error Handling:
            - Invalid JSON: Returns 400 Bad Request
            - MCP errors: Returns 500 with error details
            - All errors include session ID in headers
        
        Note:
            This endpoint is stateless - each request is completely independent.
            The session ID is used for request tracing and correlation, not
            for maintaining server-side state.
        """
        # Extract or generate session ID
        session_id = request.headers.get("Mcp-Session-Id")
        if not session_id:
            session_id = f"http_{uuid.uuid4().hex[:12]}"
        
        logger.info(
            f"JSON request received",
            extra={
                "session_id": session_id,
                "method": request.method,
                "path": request.url.path
            }
        )
        
        try:
            # Parse request body
            body = await request.body()
            
            # TODO: Integrate with MCP server
            # For now, return a placeholder response
            # In the full implementation, this would:
            # 1. Parse JSON-RPC from body
            # 2. Create MCP transport
            # 3. Forward to mcp_server
            # 4. Return result
            
            response_data = {
                "jsonrpc": "2.0",
                "result": {"status": "HTTP transport placeholder"},
                "id": 1
            }
            
            logger.debug(
                f"JSON request processed successfully",
                extra={"session_id": session_id}
            )
            
            return JSONResponse(
                content=response_data,
                headers={"Mcp-Session-Id": session_id}
            )
            
        except json.JSONDecodeError as e:
            logger.error(
                f"Invalid JSON in request: {e}",
                extra={"session_id": session_id}
            )
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error: Invalid JSON"
                    },
                    "id": None
                },
                status_code=400,
                headers={"Mcp-Session-Id": session_id}
            )
        
        except Exception as e:
            logger.error(
                f"JSON request failed: {e}",
                extra={"session_id": session_id},
                exc_info=True
            )
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    },
                    "id": None
                },
                status_code=500,
                headers={"Mcp-Session-Id": session_id}
            )
    
    async def handle_sse_request(self, request: Request) -> StreamingResponse:
        """Handle SSE (Server-Sent Events) streaming requests.
        
        This endpoint provides real-time event streaming using the SSE protocol.
        Clients can maintain a persistent connection to receive MCP events as
        they occur.
        
        SSE is useful for:
        - Real-time progress updates
        - Long-running operations
        - Event notifications
        
        Args:
            request: Starlette HTTP request object
        
        Returns:
            StreamingResponse: SSE event stream with appropriate headers
        
        Request Headers:
            - Accept: text/event-stream
            - Mcp-Session-Id (optional): Client-provided session ID
        
        Response Headers:
            - Content-Type: text/event-stream
            - Cache-Control: no-cache
            - Connection: keep-alive
            - Mcp-Session-Id: Session ID
        
        SSE Event Format:
            ```
            data: {"type": "event", "data": {...}}
            
            data: {"type": "message", "content": "..."}
            
            event: error
            data: {"error": "Something went wrong"}
            
            ```
        
        Examples:
            Client connection:
            ```javascript
            const eventSource = new EventSource('/mcp/v1/sse');
            eventSource.onmessage = (event) => {
              const data = JSON.parse(event.data);
              console.log('Received:', data);
            };
            ```
            
            Server events:
            ```
            GET /mcp/v1/sse HTTP/1.1
            Accept: text/event-stream
            
            HTTP/1.1 200 OK
            Content-Type: text/event-stream
            Mcp-Session-Id: sse_x1y2z3
            
            data: {"type": "connected", "session": "sse_x1y2z3"}
            
            data: {"type": "tool_result", "result": {...}}
            
            ```
        
        Error Handling:
            - Connection errors are sent as SSE error events
            - Client disconnection is detected and logged
            - Stream automatically closes on server errors
        
        Note:
            SSE is a one-way protocol (server → client only).
            For bidirectional communication, consider WebSockets.
        """
        # Extract or generate session ID
        session_id = request.headers.get("Mcp-Session-Id")
        if not session_id:
            session_id = f"sse_{uuid.uuid4().hex[:12]}"
        
        logger.info(
            f"SSE request received",
            extra={"session_id": session_id}
        )
        
        async def event_generator():
            """Generate SSE events for the client.
            
            Yields:
                str: SSE-formatted event strings
            
            Examples:
                >>> async for event in event_generator():
                ...     # event = "data: {...}\\n\\n"
            """
            try:
                # Send connection established event
                yield f"data: {json.dumps({'type': 'connected', 'session': session_id})}\n\n"
                
                # TODO: Integrate with MCP server for real event streaming
                # For now, send a placeholder message
                yield f"data: {json.dumps({'type': 'status', 'message': 'SSE transport placeholder'})}\n\n"
                
                logger.debug(
                    f"SSE stream established",
                    extra={"session_id": session_id}
                )
                
            except Exception as e:
                logger.error(
                    f"SSE streaming failed: {e}",
                    extra={"session_id": session_id},
                    exc_info=True
                )
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Mcp-Session-Id": session_id,
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )
    
    async def health_check(self, request: Request) -> JSONResponse:
        """Kubernetes liveness probe endpoint.
        
        This endpoint indicates whether the server process is alive and running.
        Kubernetes uses this to detect crashed or hung processes.
        
        Returns:
            JSONResponse: Health status (always 200 OK if reachable)
        
        Response:
            ```json
            {
              "status": "healthy",
              "service": "solveit-mcp-server"
            }
            ```
        
        Kubernetes Configuration:
            ```yaml
            livenessProbe:
              httpGet:
                path: /health
                port: 8000
              initialDelaySeconds: 10
              periodSeconds: 10
              timeoutSeconds: 3
              failureThreshold: 3
            ```
        
        Examples:
            >>> # Kubernetes performs periodic health checks
            >>> GET /health HTTP/1.1
            >>> 
            >>> HTTP/1.1 200 OK
            >>> {"status": "healthy", "service": "solveit-mcp-server"}
        
        Note:
            This check is simple and always returns 200 if the process
            is running. For more sophisticated checks, add validation
            logic (e.g., database connectivity, memory usage).
        """
        return JSONResponse({
            "status": "healthy",
            "service": "solveit-mcp-server"
        })
    
    async def readiness_check(self, request: Request) -> JSONResponse:
        """Kubernetes readiness probe endpoint.
        
        This endpoint indicates whether the server is ready to accept traffic.
        Kubernetes uses this to know when to start routing requests to the pod.
        
        Returns:
            JSONResponse: Readiness status with detailed information
        
        Response:
            ```json
            {
              "status": "ready",
              "service": "solveit-mcp-server",
              "checks": {
                "mcp_server": true,
                "knowledge_base": true
              }
            }
            ```
        
        Kubernetes Configuration:
            ```yaml
            readinessProbe:
              httpGet:
                path: /ready
                port: 8000
              initialDelaySeconds: 5
              periodSeconds: 5
              timeoutSeconds: 3
              failureThreshold: 3
            ```
        
        Examples:
            During startup (not ready):
            ```
            GET /ready HTTP/1.1
            
            HTTP/1.1 503 Service Unavailable
            {"status": "not_ready", "reason": "knowledge_base_loading"}
            ```
            
            After startup (ready):
            ```
            GET /ready HTTP/1.1
            
            HTTP/1.1 200 OK
            {"status": "ready", "service": "solveit-mcp-server"}
            ```
        
        Note:
            Currently returns ready immediately. In production, add checks for:
            - Knowledge base loaded
            - Database connections established
            - Required services available
        """
        # TODO: Add actual readiness checks
        # - Check if knowledge base is loaded
        # - Check if MCP server is initialized
        # - Check any other dependencies
        
        checks = {
            "mcp_server": True,  # Always true if we're running
            # Add more checks here
        }
        
        all_ready = all(checks.values())
        
        return JSONResponse(
            {
                "status": "ready" if all_ready else "not_ready",
                "service": "solveit-mcp-server",
                "checks": checks
            },
            status_code=200 if all_ready else 503
        )
    
    async def run(self) -> None:
        """Run the HTTP server using Uvicorn.
        
        Starts the Uvicorn ASGI server with the configured Starlette app.
        This method blocks until the server is shut down.
        
        The server runs with:
        - Async worker processes
        - Access logging
        - Graceful shutdown on SIGTERM
        - Auto-reload in development (if enabled)
        
        Raises:
            RuntimeError: If Uvicorn is not available
        
        Examples:
            Basic usage:
            
            >>> manager = HTTPTransportManager(server, config)
            >>> await manager.run()
            # Server now running, blocks until shutdown
            
            In asyncio main:
            
            >>> async def main():
            ...     manager = HTTPTransportManager(server, config)
            ...     await manager.run()
            >>> 
            >>> if __name__ == "__main__":
            ...     asyncio.run(main())
            
            With error handling:
            
            >>> try:
            ...     await manager.run()
            ... except KeyboardInterrupt:
            ...     logger.info("Server stopped by user")
        
        Uvicorn Configuration:
            - Host: From config.http.host (default: 0.0.0.0)
            - Port: From config.http.port (default: 8000)
            - Workers: From config.http.workers (default: 1)
            - Log level: From config.log_level
        
        Production Deployment:
            For production, consider:
            - Setting workers = CPU cores * 2
            - Using a reverse proxy (nginx, Traefik)
            - Enabling TLS/HTTPS
            - Configuring timeouts
        
        Note:
            This method blocks until the server shuts down. It should be
            the last call in your main() function for HTTP mode.
        """
        if uvicorn is None:
            raise RuntimeError(
                "Uvicorn not available. Install with: pip install uvicorn[standard]"
            )
        
        logger.info(
            f"Starting HTTP server on {self.config.host}:{self.config.port}",
            extra={
                "host": self.config.host,
                "port": self.config.port,
                "workers": self.config.workers,
                "sse_enabled": self.config.sse_enabled,
            }
        )
        
        # Create Uvicorn configuration
        config = uvicorn.Config(
            app=self.app,
            host=self.config.host,
            port=self.config.port,
            workers=self.config.workers,
            log_level="info",  # Uvicorn's own logging
            access_log=True,   # Log HTTP requests
            loop="asyncio",    # Use asyncio event loop
        )
        
        # Create and run server
        server = uvicorn.Server(config)
        
        logger.info(
            f"HTTP server ready: http://{self.config.host}:{self.config.port}"
        )
        logger.info(f"Health check: http://{self.config.host}:{self.config.port}/health")
        logger.info(f"MCP endpoint: http://{self.config.host}:{self.config.port}{self.config.base_path}/messages")
        
        if self.config.sse_enabled:
            logger.info(f"SSE endpoint: http://{self.config.host}:{self.config.port}{self.config.base_path}/sse")
        
        await server.serve()
