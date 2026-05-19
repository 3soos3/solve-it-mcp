# HTTP Transport

The HTTP transport enables SOLVE-IT MCP Server to be accessed over HTTP with SSE streaming, suitable for Kubernetes deployments, web clients, and multi-user scenarios.

## Implementation

The server uses the official MCP Python SDK `StreamableHTTPSessionManager` with Starlette/Uvicorn, providing:

- Full MCP `2025-11-25` specification compliance
- SSE (Server-Sent Events) streaming with event IDs for resumability
- Stateless session management (horizontal scaling support)
- Protocol version negotiation

## Endpoints

| Path | Method | Description |
|---|---|---|
| `/mcp/v1/messages` | `POST` | Main MCP endpoint (JSON-RPC) |
| `/mcp/v1/messages` | `GET` | SSE stream for server-initiated events |
| `/healthz` | `GET` | Liveness probe (primary) |
| `/readyz` | `GET` | Readiness probe (primary) |
| `/health` | `GET` | Liveness probe (legacy, deprecated) |
| `/ready` | `GET` | Readiness probe (legacy, deprecated) |

!!! note "Base path"
    The default base path is `/mcp/v1`, set via `MCP_BASE_PATH`. Set to `/` for domain-root deployments behind a reverse proxy (e.g. Traefik).

## Starting the Server

```bash
# Environment variable
MCP_TRANSPORT=http python3 src/server.py

# CLI argument
python3 src/server.py --transport http
```

## Configuration

See [Environment Variables Reference](../reference/environment-variables.md) for the complete list.

Core HTTP variables:

| Variable | Default | Description |
|---|---|---|
| `MCP_TRANSPORT` | `stdio` (local) / `http` (Docker) | Transport selection |
| `HTTP_HOST` | `0.0.0.0` | Bind address |
| `HTTP_PORT` | `8000` | TCP port |
| `HTTP_WORKERS` | `1` | Uvicorn worker processes |
| `MCP_BASE_PATH` | `/mcp/v1` | URL path prefix |

## Protocol Usage

### Initialize

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-11-25",
      "capabilities": {},
      "clientInfo": {"name": "my-client", "version": "1.0"}
    }
  }'
```

### List Tools

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

### Call a Tool

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0", "id": 3,
    "method": "tools/call",
    "params": {
      "name": "search",
      "arguments": {"keywords": "memory forensics", "item_types": ["techniques"]}
    }
  }'
```

## SSE Response Format

Responses are streamed as Server-Sent Events:

```
event: message
data: {"jsonrpc":"2.0","id":1,"result":{...}}

```

Each event includes an `id:` field for resumability via `Last-Event-ID`.

## Kubernetes Deployment

```yaml
containers:
- name: solveit-mcp
  image: 3soos3/solve-it-mcp:latest
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
```

See [Kubernetes Deployment](../deployment/kubernetes.md) for a complete manifest.

## Reverse Proxy Considerations

### SSE Buffering

SSE streams must not be buffered by the proxy. Add the `X-Accel-Buffering: no` header.

**Nginx:**

```nginx
location /mcp/ {
    proxy_pass http://localhost:8000/mcp/;
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_buffering off;
    proxy_read_timeout 300s;
}
```

**Traefik:**

```yaml
http:
  middlewares:
    no-sse-buffer:
      headers:
        customResponseHeaders:
          X-Accel-Buffering: "no"
```

## Horizontal Scaling

The server runs in stateless mode, allowing multiple pods to serve the same client without sticky sessions.

For Kubernetes, keep `HTTP_WORKERS=1` and scale via pod replicas:

```bash
kubectl scale deployment solveit-mcp --replicas=5
```

## Troubleshooting

### SSE stream not working

- Ensure `Accept: application/json, text/event-stream` header is sent
- Check for buffering proxies (Nginx: `proxy_buffering off`)
- Verify the client supports SSE

## STDIO vs HTTP

| Feature | STDIO | HTTP |
|---|---|---|
| Use case | CLI, desktop MCP clients | Web, cloud, Kubernetes |
| Scaling | Single session | Horizontal (stateless) |
| Protocol | Newline-delimited JSON-RPC | SSE over HTTP |
| Health checks | Not available | `/healthz`, `/readyz` |

## References

- [MCP Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/)
- [Environment Variables Reference](../reference/environment-variables.md)
- [Kubernetes Deployment](../deployment/kubernetes.md)
