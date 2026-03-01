# Getting Started with SOLVE-IT MCP Server

This guide will get you up and running with the SOLVE-IT MCP Server in less than 5 minutes.

## What You'll Need

- Docker installed (recommended) **OR** Python 3.11/3.12
- Basic understanding of Model Context Protocol (MCP)
- 5 minutes of your time

## Choose Your Path

=== "Docker (Recommended)"

    ### Why Docker?
    
    - **Fastest setup**: No Python dependencies to manage
    - **Cross-platform**: Works on Linux, macOS, Windows
    - **Production-ready**: Same image used in production deployments
    - **Multi-architecture**: Native support for AMD64, ARM64, ARMv7

    ### Quick Start

    ```bash
    # Pull the latest image
    docker pull 3soos3/solve-it-mcp:latest

    # Run in HTTP mode
    docker run -p 8000:8000 \
      -e MCP_TRANSPORT=http \
      -e HTTP_PORT=8000 \
      3soos3/solve-it-mcp:latest
    ```

    ### Verify It's Working

    ```bash
    # Test health endpoint
    curl http://localhost:8000/healthz

    # List available tools
    curl -X POST http://localhost:8000/mcp/v1/messages \
      -H "Content-Type: application/json" \
      -d '{"method":"tools/list"}'
    ```

    **Success!** You should see a JSON response listing 20+ available tools.

    ### Next Steps

    - [Complete Docker Documentation](deployment/docker.md)
    - [Environment Variables Reference](deployment/docker.md#environment-variables)
    - [Docker Compose Examples](deployment/docker.md#docker-compose)

=== "Python/pip"

    ### Prerequisites

    - Python 3.11 or 3.12
    - pip package manager
    - SOLVE-IT knowledge base (downloaded separately)

    ### Installation Steps

    #### 1. Clone SOLVE-IT Knowledge Base

    ```bash
    # Clone the knowledge base
    git clone https://github.com/SOLVE-IT-DF/solve-it.git
    cd solve-it
    export SOLVE_IT_DATA_PATH=$(pwd)/data
    ```

    #### 2. Install MCP Server

    ```bash
    # Clone this repository
    git clone https://github.com/3soos3/solve-it-mcp.git
    cd solve-it-mcp

    # Install dependencies
    pip install -r requirements.txt
    ```

    #### 3. Run the Server

    ```bash
    # Run in stdio mode (for desktop MCP clients)
    python3 src/server.py

    # Or run in HTTP mode
    python3 src/server.py --transport http --port 8000
    ```

    ### Verify It's Working

    If running in HTTP mode:

    ```bash
    # Test health endpoint
    curl http://localhost:8000/healthz
    ```

    If running in stdio mode, the server is ready when you see:
    ```
    INFO: SOLVE-IT MCP Server initialized successfully
    INFO: Transport mode: stdio
    ```

    ### Next Steps

    - [Local Development Guide](development/local-testing.md)
    - [Configuration Reference](deployment/docker.md#environment-variables)

=== "Desktop MCP Client"

    ### For Claude Desktop / Cline / Other MCP Clients

    The easiest way to use with desktop MCP clients is via Docker in stdio mode.

    #### 1. Install Docker

    Make sure Docker is installed and running on your system.

    #### 2. Configure Your MCP Client

    Add to your MCP client configuration (e.g., `claude_desktop_config.json`):

    ```json
    {
      "mcpServers": {
        "solveit": {
          "command": "docker",
          "args": [
            "run",
            "-i",
            "--rm",
            "-e", "MCP_TRANSPORT=stdio",
            "3soos3/solve-it-mcp:latest"
          ]
        }
      }
    }
    ```

    #### 3. Restart Your Client

    Restart your MCP client to load the new configuration.

    #### 4. Verify Installation

    In your MCP client, try asking:
    
    > "What SOLVE-IT tools are available?"

    You should see a list of 20+ forensic investigation tools.

    ### Alternative: Python-based

    If you prefer not to use Docker:

    ```json
    {
      "mcpServers": {
        "solveit": {
          "command": "python3",
          "args": ["/path/to/solve-it-mcp/src/server.py"],
          "cwd": "/path/to/solve-it-mcp",
          "env": {
            "SOLVE_IT_DATA_PATH": "/path/to/solve-it/data"
          }
        }
      }
    }
    ```

    ### Next Steps

    - [Integration Guide](guides/integration.md)
    - [Troubleshooting](guides/troubleshooting.md)

## Your First Query

Once the server is running, try these example queries:

### Example 1: Search for Techniques

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "search",
      "arguments": {
        "keywords": "network analysis",
        "item_types": ["techniques"]
      }
    }
  }'
```

### Example 2: Get Technique Details

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_technique_details",
      "arguments": {
        "technique_id": "T1001"
      }
    }
  }'
```

### Example 3: Explore Relationships

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_weaknesses_for_technique",
      "arguments": {
        "technique_id": "T1001"
      }
    }
  }'
```

## Understanding the Response

Successful responses will include:

- **Content**: The requested data (technique details, search results, etc.)
- **Metadata**: Information about the query and results
- **Structure**: JSON-formatted for easy parsing

Example response structure:

```json
{
  "content": [
    {
      "type": "text",
      "text": "{ \"results\": [...] }"
    }
  ],
  "isError": false
}
```

## Common Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `http` or `stdio` |
| `HTTP_HOST` | `0.0.0.0` | HTTP server bind address |
| `HTTP_PORT` | `8000` | HTTP server port |
| `SOLVE_IT_DATA_PATH` | `/app/solve-it-main/data` | Path to SOLVE-IT data |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FORMAT` | `json` | Log format: `json` or `text` |

### Docker Compose Example

For persistent setups, use Docker Compose:

```yaml
version: '3.8'
services:
  solve-it-mcp:
    image: 3soos3/solve-it-mcp:latest
    ports:
      - "8000:8000"
    environment:
      - MCP_TRANSPORT=http
      - HTTP_PORT=8000
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 3s
      retries: 3
    restart: unless-stopped
```

Save as `docker-compose.yml` and run:

```bash
docker-compose up -d
```

## Next Steps

### For Forensic Analysts
Learn how to use SOLVE-IT MCP in real investigations:

- [Forensic Analysts Guide](guides/for-forensic-analysts.md)
- [Tools Reference](reference/tools-overview.md)
- [Common Investigation Patterns](guides/for-forensic-analysts.md#common-workflows)

### For Researchers
Understand how to use SOLVE-IT MCP in your research:

- [Researchers Guide](guides/for-researchers.md)
- [Citation Information](guides/for-researchers.md#citing-this-software)
- [Data Structure](reference/techniques.md)

### For Developers
Set up a development environment:

- [Local Development Guide](development/local-testing.md)
- [Contributing Guide](development/contributing.md)
- [Architecture Overview](architecture/overview.md)

### For Production Deployments
Deploy to Kubernetes or production environments:

- [Kubernetes Deployment](deployment/kubernetes.md)
- [Security Considerations](architecture/security-model.md)
- [Monitoring & Observability](deployment/kubernetes.md#monitoring)

## Troubleshooting

### Server Won't Start

**Problem**: `Connection refused` or server doesn't start

**Solutions**:
- Verify Docker is running: `docker ps`
- Check port availability: `lsof -i :8000`
- Review logs: `docker logs <container-id>`

### SOLVE-IT Data Not Found

**Problem**: `Failed to load SOLVE-IT knowledge base`

**Solutions**:
- Verify `SOLVE_IT_DATA_PATH` environment variable
- Check that the path contains `techniques.json`, `weaknesses.json`, etc.
- For Docker: the data is embedded in the image (no action needed)

### Tools Not Appearing

**Problem**: MCP client doesn't show SOLVE-IT tools

**Solutions**:
- Restart your MCP client
- Check client configuration syntax
- Verify server is running: `curl http://localhost:8000/healthz`
- Check client logs for errors

For more help, see the [Troubleshooting Guide](guides/troubleshooting.md).

## Getting Help

- **Documentation Issues**: Check [Troubleshooting](guides/troubleshooting.md)
- **Bug Reports**: [GitHub Issues](https://github.com/3soos3/solve-it-mcp/issues)
- **Questions**: [GitHub Discussions](https://github.com/3soos3/solve-it-mcp/discussions)
- **Security Issues**: See [SECURITY.md](https://github.com/3soos3/solve-it-mcp/blob/main/SECURITY.md)
