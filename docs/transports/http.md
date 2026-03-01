# HTTP Transport for SOLVE-IT MCP Server

This document describes the HTTP/SSE transport implementation for the SOLVE-IT MCP server using the **official MCP Python SDK**.

## Overview

The HTTP transport enables the SOLVE-IT MCP server to be accessed over HTTP/SSE, making it suitable for:
- Web-based MCP clients
- Kubernetes deployments with horizontal scaling
- Cloud-native architectures
- Remote access scenarios

## Implementation

The HTTP transport uses the **official MCP Python SDK** `StreamableHTTPSessionManager`, which provides:
- ✅ Full MCP 2025-11-25 specification compliance
- ✅ SSE (Server-Sent Events) streaming with event IDs
- ✅ Session management (stateless and stateful modes)
- ✅ Resumability support via `Last-Event-ID`
- ✅ Protocol version negotiation
- ✅ Proper error handling

## Architecture

```
HTTP Client → Starlette App → StreamableHTTPSessionManager → MCP Server → Tools
                    ↓
              CORS Middleware
              Health Checks
```

### Key Components

1. **`http_transport_sdk.py`** - Integration with official SDK
2. **`StreamableHTTPSessionManager`** - From `mcp.server.streamable_http_manager`
3. **Starlette ASGI App** - HTTP server framework
4. **Uvicorn** - ASGI server

## Configuration

### Environment Variables

```bash
# Transport mode
MCP_TRANSPORT=http

# Server binding
HTTP_HOST=0.0.0.0        # Bind to all interfaces (required for Kubernetes)
HTTP_PORT=8000           # Server port

# Worker processes
HTTP_WORKERS=1           # Number of Uvicorn workers

# CORS
CORS_ORIGINS=*           # Allowed origins (comma-separated)
```

### Python Configuration

```python
from config import HTTPConfig

config = HTTPConfig(
    host="0.0.0.0",          # Bind address
    port=8000,               # Port
    workers=1,               # Worker processes
    stateless=True,          # Stateless mode for K8s scaling
    sse_enabled=True,        # Enable SSE endpoint
    cors=CORSConfig(
        allowed_origins=["*"],
        allowed_methods=["GET", "POST", "DELETE", "OPTIONS"],
    )
)
```

## Endpoints

### MCP Protocol Endpoint

**POST `/mcp/v1/messages`**
- Main MCP endpoint for JSON-RPC messages
- Supports both SSE streaming and JSON responses
- **Requires** `Accept: application/json, text/event-stream` header

Example:
```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-11-25",
      "capabilities": {},
      "clientInfo": {"name": "my-client", "version": "1.0"}
    }
  }'
```

**GET `/mcp/v1/messages`**
- SSE-only endpoint for server-initiated notifications
- Used for long-lived connections

### Health Check Endpoints

**GET `/healthz`** (Kubernetes standard)
- Liveness probe endpoint
- Returns: `{"status": "healthy", "service": "solveit-mcp-server"}`

**GET `/readyz`** (Kubernetes standard)
- Readiness probe endpoint
- Returns: `{"status": "ready", "service": "solveit-mcp-server"}`

**GET `/health`** (Legacy)
- Backward compatibility
- Same as `/healthz`

**GET `/ready`** (Legacy)
- Backward compatibility  
- Same as `/readyz`

## Usage

### Starting the Server

```bash
# Using environment variable
MCP_TRANSPORT=http python3 src/server.py

# Using command-line argument
python3 src/server.py --transport http
```

### Docker

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .
RUN pip install -e .

ENV MCP_TRANSPORT=http
ENV HTTP_HOST=0.0.0.0
ENV HTTP_PORT=8000

EXPOSE 8000

CMD ["python3", "src/server.py", "--transport", "http"]
```

```bash
docker build -t solveit-mcp .
docker run -p 8000:8000 solveit-mcp
```

### Podman

```bash
# Pull latest image
podman pull ghcr.io/3soos3/solve-it-mcp:latest

# Run with HTTP transport
podman run -d \
  --name solveit-mcp \
  --network=host \
  -e MCP_TRANSPORT=http \
  ghcr.io/3soos3/solve-it-mcp:latest
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: solveit-mcp
spec:
  replicas: 3  # Horizontal scaling (stateless mode)
  selector:
    matchLabels:
      app: solveit-mcp
  template:
    metadata:
      labels:
        app: solveit-mcp
    spec:
      containers:
      - name: solveit-mcp
        image: ghcr.io/3soos3/solve-it-mcp:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: MCP_TRANSPORT
          value: "http"
        - name: HTTP_HOST
          value: "0.0.0.0"
        - name: HTTP_PORT
          value: "8000"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: solveit-mcp
spec:
  selector:
    app: solveit-mcp
  ports:
  - port: 8000
    targetPort: 8000
    name: http
  type: ClusterIP
```

## MCP Protocol Compliance

### Supported Methods

- ✅ `initialize` - Initialize MCP session
- ✅ `tools/list` - List available tools (20 SOLVE-IT tools)
- ✅ `tools/call` - Execute a tool
- ✅ `resources/list` - List resources (if configured)
- ✅ `resources/read` - Read resource content

### Protocol Features

- ✅ **MCP 2025-11-25 Spec Compliant**
- ✅ **SSE Streaming** - Real-time event delivery
- ✅ **Event IDs** - For stream resumability
- ✅ **Last-Event-ID** - Reconnection support
- ✅ **MCP-Session-Id Header** - Session tracking
- ✅ **MCP-Protocol-Version Header** - Version negotiation
- ✅ **Stateless Mode** - Horizontal scaling support

### Response Format

All responses are streamed as **Server-Sent Events (SSE)**:

```
event: message
data: {"jsonrpc":"2.0","id":1,"result":{...}}

```

Each event includes:
- `event:` field with event type
- `data:` field with JSON-RPC message
- `id:` field for resumability (optional)

## Testing

### Unit Tests

```bash
pytest tests/test_http_transport_sdk.py -v
```

### Integration Tests

```bash
./tests/integration/test_http_mcp.sh
```

This runs 10 integration tests:
1. Health check (`/healthz`)
2. Readiness check (`/readyz`)
3. MCP initialize
4. Tools list
5. Tool count (20 tools)
6. Search tool present
7. Tool call execution
8. SSE format compliance
9. SSE Content-Type header
10. Accept header requirement

### Manual Testing

```bash
# Health check
curl http://localhost:8000/healthz | jq .

# Initialize
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "curl", "version": "1.0"}}}'

# List tools
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}'

# Call tool
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "search", "arguments": {"keywords": "memory forensics"}}}'
```

## Performance

### Benchmarks (Preliminary)

- **Latency**: ~10-50ms per request (local)
- **Throughput**: ~100-500 req/s (single worker)
- **Concurrent Connections**: 100+ (default)
- **Horizontal Scaling**: Linear (stateless mode)

### Optimization Tips

1. **Increase Workers**: Set `HTTP_WORKERS=<cpu_cores * 2>`
2. **Use Stateless Mode**: Enable horizontal scaling
3. **Nginx Reverse Proxy**: For load balancing
4. **Connection Pooling**: Client-side connection reuse

## Security

### Best Practices

1. **CORS Configuration**: Restrict origins in production
   ```python
   allowed_origins=["https://app.example.com"]
   ```

2. **HTTPS**: Always use HTTPS in production
   ```bash
   # Use reverse proxy (nginx, traefik)
   # Or configure Uvicorn with SSL
   ```

3. **Origin Validation**: Enabled by default (DNS rebinding protection)

4. **Rate Limiting**: Add via middleware or reverse proxy

5. **Authentication**: Implement OAuth 2.0 (future enhancement)

## Troubleshooting

### Server Won't Start

```bash
# Check if port is in use
lsof -i :8000

# Check logs
tail -f /tmp/mcp_server.log
```

### Connection Refused

```bash
# Verify server is listening
netstat -tulpn | grep 8000

# Check firewall
sudo ufw status
```

### SSE Stream Not Working

- Ensure `Accept: application/json, text/event-stream` header is sent
- Check for buffering proxies (nginx: `X-Accel-Buffering: no`)
- Verify client supports SSE

### CORS Errors

- Check `CORS_ORIGINS` environment variable
- Verify `Origin` header in request
- Check browser console for details

## Comparison: STDIO vs HTTP

| Feature | STDIO | HTTP/SSE |
|---------|-------|----------|
| **Use Case** | CLI, local tools | Web, cloud, remote |
| **Scaling** | Single process | Horizontal (stateless) |
| **Protocol** | Newline-delimited JSON-RPC | SSE over HTTP |
| **Session** | Single session | Multiple sessions |
| **Deployment** | Simple | Kubernetes, Docker |
| **Network** | Local only | LAN/WAN/Internet |
| **Security** | Process isolation | HTTPS, CORS, Auth |

## References

- [MCP Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [SSE Standard](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [Starlette Documentation](https://www.starlette.io/)
- [Uvicorn Documentation](https://www.uvicorn.org/)

## Support

For issues or questions:
- GitHub Issues: https://github.com/3soos3/solve-it-mcp
- MCP Community: https://modelcontextprotocol.io/community/
