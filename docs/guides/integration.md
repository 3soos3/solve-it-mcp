# Server.py Integration Guide

This guide shows how to integrate the HTTP/SSE transport and OpenTelemetry observability into the existing `src/server.py` file.

## Overview

The server.py modifications add:
- ✅ HTTP/SSE transport support
- ✅ OpenTelemetry distributed tracing
- ✅ Prometheus metrics collection
- ✅ Correlation ID tracking
- ✅ Transport selection (STDIO or HTTP)

## Required Changes

### 1. Update Imports

**Add at the top of server.py (after existing imports):**

```python
# New imports for HTTP transport and observability
from config import load_config
from utils.telemetry import TelemetryManager
from utils.metrics import MCPMetrics
from utils.correlation import CorrelationContext
from transports import run_stdio_server, HTTPTransportManager, HTTP_AVAILABLE

# Conditional OpenTelemetry imports
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None
```

### 2. Remove Old run_stdio_server Function

**Delete lines 62-113** (the old run_stdio_server function).

The new version is in `src/transports/stdio_transport.py` and imported above.

###  3. Add Helper Function

**Add before `create_server()` function:**

```python
def _noop_context():
    """No-op context manager for when OpenTelemetry is disabled."""
    from contextlib import nullcontext
    return nullcontext()
```

### 4. Update main() Function

Replace the existing `main()` function with this enhanced version:

```python
async def main() -> None:
    """Main entry point for the MCP server with HTTP/SSE and OpenTelemetry support."""
    
    # 1. LOAD CONFIGURATION
    config = load_config()
    
    # 2. CONFIGURE LOGGING
    configure_logging()
    logger = get_logger(__name__)

    # 3. PARSE CLI ARGUMENTS
    parser = argparse.ArgumentParser(
        description="SOLVE-IT MCP Server with HTTP/SSE and OpenTelemetry"
    )
    parser.add_argument(
        "--transport", 
        choices=["stdio", "http"], 
        default=config.transport,
        help="Transport protocol (stdio for local, http for web/k8s)"
    )
    args = parser.parse_args()
    config.transport = args.transport

    # 4. LOG STARTUP INFO
    logger.info("=" * 80)
    logger.info("Starting SOLVE-IT MCP Server")
    logger.info("=" * 80)
    logger.info(f"Server: name=solveit_mcp_server, version=0.1.0")
    logger.info(f"Transport: {config.transport}")
    logger.info(f"Environment: {config.otel.environment}")
    logger.info(f"OpenTelemetry: {'enabled' if config.otel.enabled else 'disabled'}")
    if config.transport == "http":
        logger.info(f"HTTP: {config.http.host}:{config.http.port}")
        logger.info(f"SSE: {'enabled' if config.http.sse_enabled else 'disabled'}")
    
    # 5. INITIALIZE OPENTELEMETRY
    tracer = None
    metrics_recorder = None
    
    if config.otel.enabled:
        try:
            logger.info("Initializing OpenTelemetry observability")
            telemetry_manager = TelemetryManager(config.otel)
            tracer, meter = telemetry_manager.configure()
            metrics_recorder = MCPMetrics(meter)
            
            logger.info(
                f"OpenTelemetry initialized: "
                f"sample_rate={config.otel.get_sample_rate()*100}%, "
                f"endpoint={config.otel.otlp_endpoint}"
            )
        except Exception as e:
            logger.warning(
                f"Failed to initialize OpenTelemetry: {e}. "
                f"Continuing without observability."
            )
            tracer = None
            metrics_recorder = None
    else:
        logger.info("OpenTelemetry disabled by configuration")

    # 6. CREATE MCP SERVER (existing code)
    try:
        server = create_server()
        logger.info("MCP SDK server instance created successfully")
    except Exception as e:
        logger.critical(f"Failed to create MCP server instance: {e}")
        logger.critical("Server startup aborted - SDK initialization failed")
        raise

    # 7-9. INITIALIZE SECURITY AND KNOWLEDGE BASE (existing code - keep as is)
    # ... (lines 154-250 remain unchanged)
    
    # After tool registration, ADD this before @server.list_tools():
```

### 5. Update handle_call_tool() Handler

Replace the `@server.call_tool()` handler with this telemetry-integrated version:

```python
    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[types.TextContent]:
        """Handle tool calls with telemetry, security, and performance tracking."""
        
        # Generate and set correlation ID
        correlation_id = CorrelationContext.generate_id("tool")
        CorrelationContext.set_correlation_id(correlation_id)
        
        # Track active requests
        if metrics_recorder:
            metrics_recorder.active_requests.add(1, {"tool_name": name})
        
        start_time = time.time()
        
        # Start OpenTelemetry span
        span_context = None
        if tracer and OTEL_AVAILABLE:
            span_context = tracer.start_as_current_span(
                f"mcp.tool.{name}",
                kind=trace.SpanKind.SERVER,
                attributes={
                    "mcp.tool.name": name,
                    "correlation.id": correlation_id,
                }
            )
        
        # Execute with telemetry context
        async with span_context if span_context else _noop_context():
            # Get trace context for logging
            trace_ctx = CorrelationContext.get_trace_context()
            arg_count = len(arguments) if arguments else 0
            
            logger.info(
                f"Tool call request: {name}",
                extra={**trace_ctx, "tool_name": name, "arg_count": arg_count}
            )

            try:
                if arguments is None:
                    arguments = {}

                # LAYER 1 SECURITY (existing)
                await security.validate_request(name, arguments)

                # TOOL LOOKUP (existing)
                if name not in tool_registry:
                    error_msg = f"Unknown tool: {name}"
                    logger.error(error_msg, extra={**trace_ctx, "tool_name": name})
                    if span_context and OTEL_AVAILABLE:
                        trace.get_current_span().set_status(
                            Status(StatusCode.ERROR, error_msg)
                        )
                    raise ValueError(error_msg)

                tool = tool_registry[name]

                # LAYER 2 SECURITY + Validation (existing)
                validation_start = time.time()
                params = tool.validate_params(arguments)
                validation_time = time.time() - validation_start

                # Record validation metrics
                if metrics_recorder:
                    metrics_recorder.validation_duration.record(
                        validation_time * 1000,
                        {"tool_name": name}
                    )

                # EXECUTION (existing)
                tool_timeout = getattr(tool, 'execution_timeout', 
                                     shared_security_config.default_timeout)
                
                async with security.execution_timeout(tool_timeout, name):
                    execution_start = time.time()
                    result = await tool.invoke(params)
                    execution_time = time.time() - execution_start

                # RESPONSE VALIDATION (existing)
                safe_result = await security.validate_response(result, name)

                # RECORD SUCCESS METRICS
                total_time = time.time() - start_time
                
                if metrics_recorder:
                    metrics_recorder.record_tool_invocation(
                        tool_name=name,
                        duration_ms=execution_time * 1000,
                        input_size=len(str(arguments)),
                        output_size=len(safe_result),
                        attributes=trace_ctx
                    )
                
                if span_context and OTEL_AVAILABLE:
                    current_span = trace.get_current_span()
                    current_span.set_attribute("mcp.result.length", len(safe_result))
                    current_span.set_status(Status(StatusCode.OK))

                logger.info(
                    f"Tool call completed successfully: {name}",
                    extra={
                        **trace_ctx,
                        "tool_name": name,
                        "execution_time_ms": execution_time * 1000,
                        "total_time_ms": total_time * 1000,
                    }
                )

                return [types.TextContent(type="text", text=safe_result)]

            except SecurityError as e:
                # SECURITY VIOLATION HANDLING
                total_time = time.time() - start_time
                
                if metrics_recorder:
                    metrics_recorder.security_violations.add(1, {
                        "tool_name": name,
                        "violation_type": type(e).__name__
                    })
                
                if span_context and OTEL_AVAILABLE:
                    current_span = trace.get_current_span()
                    current_span.set_status(Status(StatusCode.ERROR, str(e)))
                    current_span.record_exception(e)

                logger.error(
                    f"Security violation in tool call: {name} - {e}",
                    extra={**trace_ctx, "tool_name": name, "error_type": "SecurityError"}
                )

                raise ValueError(f"Security policy violation: {str(e)}")

            except Exception as e:
                # GENERAL ERROR HANDLING
                total_time = time.time() - start_time
                
                if metrics_recorder:
                    metrics_recorder.record_tool_invocation(
                        tool_name=name,
                        duration_ms=total_time * 1000,
                        input_size=len(str(arguments)),
                        output_size=0,
                        error=True,
                        attributes=trace_ctx
                    )
                
                if span_context and OTEL_AVAILABLE:
                    current_span = trace.get_current_span()
                    current_span.set_status(Status(StatusCode.ERROR, str(e)))
                    current_span.record_exception(e)

                logger.error(
                    f"Tool call failed: {name} - {e}",
                    extra={**trace_ctx, "tool_name": name, "error_type": type(e).__name__}
                )

                raise
            
            finally:
                # Clean up active request tracking
                if metrics_recorder:
                    metrics_recorder.active_requests.add(-1, {"tool_name": name})
```

### 6. Update Transport Selection

Replace the last section before `if __name__ == "__main__"` with:

```python
    # Server initialization completed
    logger.info("Server initialization completed successfully")
    logger.info("=" * 80)
    
    # Run server with selected transport
    if config.transport == "http":
        if not HTTP_AVAILABLE:
            logger.critical("HTTP transport selected but not available")
            logger.critical("Install with: pip install starlette uvicorn[standard]")
            raise RuntimeError("HTTP transport dependencies missing")
        
        logger.info("Starting HTTP/SSE transport")
        http_manager = HTTPTransportManager(server, config.http)
        await http_manager.run()
    else:
        logger.info("Starting STDIO transport")
        await run_stdio_server(server)
```

## Complete Integration Example

See `docs/SERVER_COMPLETE_EXAMPLE.md` for the complete integrated server.py file.

## Testing the Integration

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Test STDIO Transport (existing behavior)

```bash
python src/server.py
# or
python src/server.py --transport stdio
```

### 3. Test HTTP Transport

```bash
# Start server
MCP_TRANSPORT=http python src/server.py
# or
python src/server.py --transport http

# In another terminal, test health endpoint
curl http://localhost:8000/health

# Test MCP endpoint (placeholder for now)
curl -X POST http://localhost:8000/mcp/v1/messages \\
  -H "Content-Type: application/json" \\
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

### 4. Test with OpenTelemetry

```bash
# Make sure OTel Collector is running (see docs/OBSERVABILITY.md)
OTEL_ENABLED=true \\
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \\
ENVIRONMENT=development \\
python src/server.py --transport http
```

## Verification Checklist

- [ ] Server starts without errors in STDIO mode
- [ ] Server starts without errors in HTTP mode  
- [ ] Health endpoint responds: `curl http://localhost:8000/health`
- [ ] Readiness endpoint responds: `curl http://localhost:8000/ready`
- [ ] OpenTelemetry traces appear in collector/SignNoz
- [ ] Metrics appear in Prometheus
- [ ] Correlation IDs appear in logs
- [ ] Existing tools still work via STDIO

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:
```bash
pip install -r requirements.txt
```

### OpenTelemetry Not Working

Check:
1. Is OTEL_ENABLED=true?
2. Is OTel Collector running on the endpoint?
3. Check logs for telemetry initialization messages

### HTTP Transport Not Available

Install missing dependencies:
```bash
pip install starlette uvicorn[standard]
```

## Next Steps

1. **Complete HTTP Integration**: The HTTP transport currently has placeholder implementations for actual MCP request handling. These need to be implemented using the MCP SDK's HTTP transport capabilities.

2. **Add Tests**: Create integration tests for the new transport and telemetry features.

3. **Deploy to Kubernetes**: See `docs/DEPLOYMENT.md` for Kubernetes deployment guide.

4. **Configure Dashboards**: See `docs/OBSERVABILITY.md` for Grafana dashboard setup.

## Summary

This integration adds:
- Configuration-driven transport selection
- Full OpenTelemetry instrumentation
- Metrics collection for all operations
- Correlation ID tracking
- Backward compatibility with existing STDIO transport

The server now supports both local development (STDIO) and production deployment (HTTP/SSE) with comprehensive observability!
