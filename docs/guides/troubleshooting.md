# Troubleshooting Guide

Common issues and solutions for SOLVE-IT MCP Server.

## Installation Issues

### Docker Image Won't Pull

**Problem**: `Error response from daemon: manifest unknown`

**Solutions**:
- Verify image name: `3soos3/solve-it-mcp:latest`
- Check Docker Hub status
- Try alternative registry: `ghcr.io/3soos3/solve-it-mcp:latest`
- Verify network connectivity

### Python Dependencies Fail to Install

**Problem**: `pip install` fails with dependency conflicts

**Solutions**:
- Use Python 3.11 or 3.12: `python3 --version`
- Create clean virtual environment:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  ```
- Check for conflicting packages: `pip list`

## Runtime Issues

### Server Won't Start

**Problem**: Server crashes immediately or won't bind to port

**Solutions**:

1. **Check port availability**:
   ```bash
   lsof -i :8000  # Linux/Mac
   netstat -ano | findstr :8000  # Windows
   ```

2. **Try different port**:
   ```bash
   docker run -p 8080:8080 \
     -e HTTP_PORT=8080 \
     3soos3/solve-it-mcp:latest
   ```

3. **Check Docker daemon**:
   ```bash
   docker ps  # Verify Docker is running
   docker logs <container-id>  # Check logs
   ```

### SOLVE-IT Data Not Found

**Problem**: `Failed to load SOLVE-IT knowledge base`

**Solutions**:

**For Docker** (data is embedded):
- Should not occur; file a bug if it does

**For Python installation**:
```bash
# Verify SOLVE-IT data path
ls $SOLVE_IT_DATA_PATH

# Should contain:
# - techniques.json
# - weaknesses.json
# - mitigations.json
# - objective_mappings/

# Set correct path
export SOLVE_IT_DATA_PATH=/path/to/solve-it/data
```

### Health Check Fails

**Problem**: `/healthz` endpoint returns error

**Solutions**:

1. **Wait for startup** (can take 5-10 seconds):
   ```bash
   sleep 10 && curl http://localhost:8000/healthz
   ```

2. **Check logs**:
   ```bash
   docker logs <container-id>
   ```

3. **Verify transport mode**:
   ```bash
   # For HTTP mode
   docker run -p 8000:8000 \
     -e MCP_TRANSPORT=http \
     3soos3/solve-it-mcp:latest
   ```

## MCP Client Issues

### Tools Don't Appear in Client

**Problem**: MCP client doesn't show SOLVE-IT tools

**Solutions**:

1. **Verify client configuration**:
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

2. **Check for typos** in config file

3. **Restart MCP client** completely

4. **Verify server runs standalone**:
   ```bash
   docker run -i --rm \
     -e MCP_TRANSPORT=stdio \
     3soos3/solve-it-mcp:latest
   ```

### Connection Refused

**Problem**: Client can't connect to HTTP server

**Solutions**:

1. **Verify server is running**:
   ```bash
   curl http://localhost:8000/healthz
   ```

2. **Check firewall rules**:
   ```bash
   # Linux
   sudo ufw status
   sudo ufw allow 8000/tcp
   ```

3. **Verify host binding**:
   ```bash
   docker run -p 8000:8000 \
     -e HTTP_HOST=0.0.0.0 \
     -e MCP_TRANSPORT=http \
     3soos3/solve-it-mcp:latest
   ```

## Query Issues

### Empty or No Results

**Problem**: Queries return no results when data should exist

**Solutions**:

1. **Check search syntax**:
   ```bash
   # Correct
   {"keywords": "network analysis"}
   
   # Wrong
   {"keywords": network analysis}  # Missing quotes
   ```

2. **Verify item types**:
   ```bash
   # Correct
   {"item_types": ["techniques"]}
   
   # Wrong
   {"item_types": "techniques"}  # Should be array
   ```

3. **Check ID format**:
   ```bash
   # Correct: Uppercase T, exact ID
   {"technique_id": "T1001"}
   
   # Wrong
   {"technique_id": "t1001"}  # Lowercase
   {"technique_id": "T001"}   # Missing digit
   ```

### Invalid JSON Errors

**Problem**: `Invalid JSON` or parsing errors

**Solutions**:

1. **Validate JSON** before sending:
   ```bash
   echo '{"method":"tools/list"}' | jq .
   ```

2. **Escape special characters**:
   ```bash
   # In shell, use single quotes for JSON
   curl -X POST http://localhost:8000/mcp/v1/messages \
     -H 'Content-Type: application/json' \
     -d '{"method":"tools/list"}'
   ```

3. **Check for trailing commas** (not allowed in JSON)

## Performance Issues

### Slow Queries

**Problem**: Queries take longer than expected

**Solutions**:

1. **Use specific queries** instead of bulk operations when possible

2. **Disable telemetry** for faster performance:
   ```bash
   docker run -p 8000:8000 \
     -e OTEL_ENABLED=false \
     3soos3/solve-it-mcp:latest
   ```

3. **Reduce logging**:
   ```bash
   docker run -p 8000:8000 \
     -e LOG_LEVEL=ERROR \
     3soos3/solve-it-mcp:latest
   ```

### High Memory Usage

**Problem**: Container uses excessive memory

**Solutions**:

1. **Set memory limits**:
   ```bash
   docker run -p 8000:8000 \
     --memory=256m \
     3soos3/solve-it-mcp:latest
   ```

2. **Restart periodically** for long-running instances

## Deployment Issues

### Kubernetes Pod CrashLoopBackOff

**Problem**: Pod keeps restarting

**Solutions**:

1. **Check logs**:
   ```bash
   kubectl logs -f <pod-name>
   kubectl describe pod <pod-name>
   ```

2. **Verify resource limits**:
   ```yaml
   resources:
     requests:
       memory: "128Mi"
       cpu: "100m"
     limits:
       memory: "256Mi"
       cpu: "500m"
   ```

3. **Check liveness probe timing**:
   ```yaml
   livenessProbe:
     initialDelaySeconds: 30  # Increase if startup is slow
     periodSeconds: 10
   ```

### Image Pull Errors in Kubernetes

**Problem**: `ImagePullBackOff` or authentication errors

**Solutions**:

1. **Use public registry** (no auth required):
   ```yaml
   image: 3soos3/solve-it-mcp:latest
   ```

2. **For GHCR, create secret**:
   ```bash
   kubectl create secret docker-registry ghcr-secret \
     --docker-server=ghcr.io \
     --docker-username=<username> \
     --docker-password=<token>
   ```

## Common Error Messages

### "Transport mode must be stdio or http"

**Cause**: Invalid `MCP_TRANSPORT` value

**Solution**:
```bash
# Valid values
MCP_TRANSPORT=stdio
MCP_TRANSPORT=http

# Invalid
MCP_TRANSPORT=https  # Not supported
```

### "Knowledge base not initialized"

**Cause**: Server started before data loaded

**Solution**: Wait for initialization message in logs

### "Tool not found"

**Cause**: Typo in tool name

**Solution**: List available tools:
```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{"method":"tools/list"}'
```

## Getting More Help

### Enable Debug Logging

```bash
docker run -p 8000:8000 \
  -e LOG_LEVEL=DEBUG \
  -e LOG_FORMAT=text \
  3soos3/solve-it-mcp:latest
```

### Collect Diagnostic Information

When reporting issues, include:

1. **Server version**:
   ```bash
   docker inspect 3soos3/solve-it-mcp:latest | grep "Created"
   ```

2. **Environment**:
   - OS and version
   - Docker version: `docker --version`
   - Python version (if applicable): `python3 --version`

3. **Logs**:
   ```bash
   docker logs <container-id> > server-logs.txt
   ```

4. **Configuration**:
   - Environment variables
   - docker-compose.yml or Kubernetes manifests

### Report Issues

- **GitHub Issues**: [https://github.com/3soos3/solve-it-mcp/issues](https://github.com/3soos3/solve-it-mcp/issues)
- **Include**: Diagnostic info, steps to reproduce, expected vs actual behavior
- **Security issues**: See [SECURITY.md](https://github.com/3soos3/solve-it-mcp/blob/main/SECURITY.md)

## Quick Fixes Reference

| Problem | Quick Fix |
|---------|-----------|
| Port in use | `docker run -p 8080:8080 -e HTTP_PORT=8080 ...` |
| Connection refused | Verify server: `curl http://localhost:8000/healthz` |
| No tools in client | Restart client, check config syntax |
| Slow queries | `-e OTEL_ENABLED=false -e LOG_LEVEL=ERROR` |
| High memory | `--memory=256m` |
| Pod won't start | Increase `initialDelaySeconds` in liveness probe |
| Invalid JSON | Validate with `jq` before sending |
| Empty results | Check ID format (uppercase, exact) |

## Still Need Help?

1. Check [Documentation](../index.md)
2. Search [GitHub Issues](https://github.com/3soos3/solve-it-mcp/issues)
3. Ask in [Discussions](https://github.com/3soos3/solve-it-mcp/discussions)
4. File new issue with diagnostic info
