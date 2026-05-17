# Troubleshooting Guide

Common issues and solutions for SOLVE-IT MCP Server.

## Installation Issues

### Docker Image Won't Pull

**Problem**: `Error response from daemon: manifest unknown`

**Solutions**:

- Verify the image name: `3soos3/solve-it-mcp:latest`
- Try the alternative registry: `ghcr.io/3soos3/solve-it-mcp:latest`
- Check your network connectivity and Docker Hub status

### Python Dependencies Fail

**Problem**: `pip install` fails with dependency conflicts

**Solutions**:

```bash
# Use Python 3.12
python3 --version

# Use a clean virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .
```

## Runtime Issues

### Server Won't Start

**Problem**: Server crashes or won't bind to port

**Check port availability:**

```bash
lsof -i :8000          # Linux/macOS
netstat -ano | findstr :8000  # Windows
```

**Try a different port:**

```bash
docker run -p 8080:8080 -e HTTP_PORT=8080 3soos3/solve-it-mcp:latest
```

**Check Docker logs:**

```bash
docker logs <container-id>
```

### SOLVE-IT Data Not Found

**Problem**: `Failed to load SOLVE-IT knowledge base`

For Docker (`:latest` or `:release`) — data is baked in; this should not occur. File a bug if it does.

For Python installs:

```bash
# Verify the path is set and contains the right files
ls $SOLVE_IT_DATA_PATH
# Should show: techniques.json, weaknesses.json, mitigations.json, objective_mappings/

# Set correct path
export SOLVE_IT_DATA_PATH=/path/to/solve-it/data
```

### Health Check Fails

**Problem**: `/healthz` returns an error or connection refused

1. The server may still be starting — wait 5–10 seconds then retry
2. Check that `MCP_TRANSPORT=http` is set (health endpoints only work in HTTP mode)
3. Inspect logs: `docker logs <container-id>`

The health endpoint is `/healthz` (liveness) and `/readyz` (readiness). The legacy endpoints `/health` and `/ready` also work but are deprecated.

## MCP Client Issues

### Tools Don't Appear in Client

**Problem**: MCP client doesn't show SOLVE-IT tools

**Check configuration syntax:**

```json
{
  "mcpServers": {
    "solveit": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT=stdio",
               "3soos3/solve-it-mcp:latest"]
    }
  }
}
```

**Steps:**

1. Verify the server runs standalone: `docker run -i --rm -e MCP_TRANSPORT=stdio 3soos3/solve-it-mcp:latest`
2. Restart your MCP client completely
3. Check the client's log output for errors

### Connection Refused (HTTP Mode)

```bash
# Verify server is running
curl http://localhost:8000/healthz

# Check firewall
sudo ufw status
sudo ufw allow 8000/tcp

# Verify host binding
docker run -p 8000:8000 -e HTTP_HOST=0.0.0.0 -e MCP_TRANSPORT=http \
  3soos3/solve-it-mcp:latest
```

## Query Issues

### Empty or No Results

**Problem**: Queries return no results when data should exist

**Check ID format** — IDs must be uppercase with a 4-digit number:

```
Correct:  DFT-1001
Wrong:    t1001     (lowercase)
Wrong:    DFT-001   (only 3 digits)
```

**Check item_types** — must be an array:

```json
{"item_types": ["techniques"]}    // correct
{"item_types": "techniques"}      // wrong
```

**For search** — try broader terms or use `substring_match: true`:

```json
{
  "keywords": "memory",
  "substring_match": true
}
```

### Invalid JSON Errors

Validate JSON before sending:

```bash
echo '{"method":"tools/list"}' | jq .
```

Use single quotes in shell to avoid escaping issues:

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

## Performance Issues

### Slow Queries

1. Use specific tools instead of bulk operations where possible
2. Disable telemetry: `-e OTEL_ENABLED=false`
3. Reduce logging: `-e LOG_LEVEL=ERROR`

### High Memory Usage

Set container memory limits:

```bash
docker run --memory=256m 3soos3/solve-it-mcp:latest
```

## Kubernetes Issues

### Pod CrashLoopBackOff

```bash
kubectl logs -f <pod-name>
kubectl describe pod <pod-name>
```

Common causes:

- Resource limits too low (OOMKilled)
- `MCP_TRANSPORT` not set to `http`
- Liveness probe firing before startup completes

Increase the initial delay:

```yaml
livenessProbe:
  initialDelaySeconds: 30
  periodSeconds: 10
```

### ImagePullBackOff

For Docker Hub (no auth required for public images):

```yaml
image: 3soos3/solve-it-mcp:latest
```

For GHCR, create an image pull secret:

```bash
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=<username> \
  --docker-password=<token>
```

## Common Error Messages

| Error | Cause | Fix |
|---|---|---|
| `Transport mode must be stdio or http` | Invalid `MCP_TRANSPORT` value | Use `stdio` or `http` |
| `Knowledge base not initialized` | Tool called before data loaded | Wait for startup to complete |
| `Tool not found` | Typo in tool name | Call `tools/list` to see correct names |

## Diagnostics

### Enable Debug Logging

```bash
docker run -p 8000:8000 \
  -e LOG_LEVEL=DEBUG \
  -e LOG_FORMAT=text \
  3soos3/solve-it-mcp:latest
```

### When Reporting Issues

Include:

1. **Image/version**: `docker inspect 3soos3/solve-it-mcp:latest | grep Created`
2. **Platform**: OS, Docker version (`docker --version`), Python version if applicable
3. **Logs**: `docker logs <container-id> > server-logs.txt`
4. **Configuration**: environment variables, compose file or Kubernetes manifest

**Report bugs**: [GitHub Issues](https://github.com/3soos3/solve-it-mcp/issues)

**Security issues**: See [SECURITY.md](https://github.com/3soos3/solve-it-mcp/blob/main/SECURITY.md)

## Quick Reference

| Problem | Quick Fix |
|---|---|
| Port in use | `-p 8080:8080 -e HTTP_PORT=8080` |
| Connection refused | `curl http://localhost:8000/healthz` |
| No tools in client | Restart client, check config syntax |
| Slow queries | `-e OTEL_ENABLED=false -e LOG_LEVEL=ERROR` |
| High memory | `--memory=256m` |
| Pod won't start | Increase `initialDelaySeconds` in liveness probe |
| Empty results | Check ID format: uppercase, 4 digits (DFT-1001) |
