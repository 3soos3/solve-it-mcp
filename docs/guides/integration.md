# Integration Guide

This guide shows how to integrate SOLVE-IT MCP Server with common MCP clients and workflows.

## MCP Clients

### Claude Desktop

Add to `claude_desktop_config.json` (typically at `~/.config/claude/` on Linux or `~/Library/Application Support/Claude/` on macOS):

```json
{
  "mcpServers": {
    "solveit": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "MCP_TRANSPORT=stdio",
        "3soos3/solve-it-mcp:latest"
      ]
    }
  }
}
```

Restart Claude Desktop after saving. You can then ask questions like:

- "What forensic techniques are available for mobile device acquisition?"
- "What are the weaknesses of timeline analysis (DFT-1023)?"
- "Find mitigations for hash collision weaknesses"

### Cline (VS Code Extension)

Add to your Cline MCP settings:

```json
{
  "mcpServers": {
    "solveit": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "MCP_TRANSPORT=stdio",
        "3soos3/solve-it-mcp:latest"
      ]
    }
  }
}
```

### Python-based MCP Client (stdio)

If you prefer not to use Docker:

```json
{
  "mcpServers": {
    "solveit": {
      "command": "python3",
      "args": ["/path/to/solve-it-mcp/src/server.py"],
      "env": {
        "SOLVE_IT_DATA_PATH": "/path/to/solve-it/data"
      }
    }
  }
}
```

## HTTP Transport

For web clients, Kubernetes deployments, and multi-user scenarios, use HTTP mode.

### Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/mcp/v1/messages` | `POST` | Main MCP endpoint (JSON-RPC) |
| `/mcp/v1/messages` | `GET` | SSE stream for server-initiated events |
| `/healthz` | `GET` | Liveness probe |
| `/readyz` | `GET` | Readiness probe |

!!! note "Base path"
    The default base path is `/mcp/v1`. Set `MCP_BASE_PATH=/` to serve at the domain root — useful behind a reverse proxy with host-based routing (e.g. Traefik at `mcp.yourdomain.tld`).

### MCP Initialization

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

## Reverse Proxy Integration

### Traefik

When running behind Traefik with host-based routing:

```yaml
environment:
  - MCP_TRANSPORT=http
  - MCP_BASE_PATH=/            # Serve at domain root
```

Add a middleware to prevent SSE stream buffering:

```yaml
# Traefik middleware
http:
  middlewares:
    no-sse-buffer:
      headers:
        customResponseHeaders:
          X-Accel-Buffering: "no"
```

### Nginx

```nginx
location /mcp/ {
    proxy_pass http://localhost:8000/mcp/;
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_buffering off;                        # Required for SSE
    proxy_set_header X-Accel-Buffering no;
    proxy_read_timeout 300s;
}
```

## Troubleshooting Integration Issues

### Tools not appearing

1. Confirm the server is running: `curl http://localhost:8000/healthz`
2. Restart your MCP client
3. Check for JSON syntax errors in your config file

### SSE streaming not working

- Ensure the `Accept: application/json, text/event-stream` header is sent
- Check for buffering proxies — add `X-Accel-Buffering: no` middleware
- Nginx: set `proxy_buffering off`

### Connection refused

- Verify the server is bound to the correct interface (`HTTP_HOST=0.0.0.0` for Docker)
- Check port mapping: `-p 8000:8000`

## Next Steps

- [Environment Variables Reference](../reference/environment-variables.md) — all configuration options
- [Docker Deployment](../deployment/docker.md) — image types and examples
- [Kubernetes Deployment](../deployment/kubernetes.md) — production Kubernetes setup
- [Troubleshooting](troubleshooting.md) — common issues
