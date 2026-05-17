# Getting Started

This guide will get the SOLVE-IT MCP Server running in under 5 minutes.

## Prerequisites

- Docker installed (recommended) **or** Python 3.12
- Basic familiarity with Model Context Protocol (MCP)

## Choose Your Path

=== "Docker (Recommended)"

    ### Quick Start

    ```bash
    # Pull and run in HTTP mode
    docker pull 3soos3/solve-it-mcp:latest
    docker run -p 8000:8000 \
      -e MCP_TRANSPORT=http \
      3soos3/solve-it-mcp:latest
    ```

    ### Verify It's Working

    ```bash
    curl http://localhost:8000/healthz
    ```

    You should see: `{"status":"healthy","service":"solveit-mcp-server"}`

    ```bash
    # List available tools
    curl -X POST http://localhost:8000/mcp/v1/messages \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
    ```

    The response will list all 24 available tools.

    ### Next Steps

    - [Complete Docker Documentation](deployment/docker.md)
    - [Environment Variables Reference](reference/environment-variables.md)

=== "Python"

    ### Prerequisites

    - Python 3.12
    - SOLVE-IT data repository cloned separately

    ### Installation

    #### 1. Clone the SOLVE-IT Knowledge Base

    ```bash
    git clone https://github.com/SOLVE-IT-DF/solve-it.git
    export SOLVE_IT_DATA_PATH=$(pwd)/solve-it/data
    ```

    #### 2. Clone and Install the MCP Server

    ```bash
    git clone https://github.com/3soos3/solve-it-mcp.git
    cd solve-it-mcp
    pip install -e .
    ```

    #### 3. Run the Server

    ```bash
    # stdio mode (for desktop MCP clients)
    python3 src/server.py

    # HTTP mode
    MCP_TRANSPORT=http python3 src/server.py
    ```

    ### Verify

    In HTTP mode:

    ```bash
    curl http://localhost:8000/healthz
    ```

    In stdio mode, the server is ready when logs show:
    ```
    INFO: SOLVE-IT MCP Server initialized successfully
    ```

    ### Next Steps

    - [Local Development Guide](development/local-testing.md)
    - [Environment Variables Reference](reference/environment-variables.md)

=== "Desktop MCP Client"

    ### Claude Desktop / Cline / Other MCP Clients

    The simplest integration uses Docker in stdio mode.

    #### 1. Configure Your MCP Client

    Add to your MCP client configuration (e.g. `claude_desktop_config.json`):

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

    #### 2. Restart Your Client

    Restart your MCP client to load the new configuration.

    #### 3. Verify

    Ask your client: *"What SOLVE-IT tools are available?"*

    You should see all 24 forensic investigation tools listed.

    #### Alternative: Python-based

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

    ### Next Steps

    - [Integration Guide](guides/integration.md)
    - [Troubleshooting](guides/troubleshooting.md)

## Your First Query

Once the server is running in HTTP mode, try these examples:

### Search for Techniques

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search",
      "arguments": {
        "keywords": "memory acquisition",
        "item_types": ["techniques"]
      }
    }
  }'
```

### Get Technique Details

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0", "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get_technique_details",
      "arguments": {"technique_id": "DFT-1001"}
    }
  }'
```

### Explore Relationships

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0", "id": 3,
    "method": "tools/call",
    "params": {
      "name": "get_weaknesses_for_technique",
      "arguments": {"technique_id": "DFT-1001"}
    }
  }'
```

## Quick Docker Compose Setup

For a persistent local deployment:

```yaml
services:
  solve-it-mcp:
    image: 3soos3/solve-it-mcp:latest
    ports:
      - "8000:8000"
    environment:
      - MCP_TRANSPORT=http
      - LOG_LEVEL=INFO
      - OTEL_ENABLED=false
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 3s
      retries: 3
    restart: unless-stopped
```

```bash
docker compose up -d
```

## Common Configuration

| Variable | Default | Description |
|---|---|---|
| `MCP_TRANSPORT` | `stdio` (local), `http` (Docker) | Transport mode |
| `HTTP_PORT` | `8000` | HTTP server port |
| `SOLVE_IT_DATA_PATH` | `/app/solve-it-main/data` | Path to SOLVE-IT data |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `OTEL_ENABLED` | `true` | Enable OpenTelemetry tracing |

See the [Environment Variables Reference](reference/environment-variables.md) for the complete list.

## Troubleshooting

### Server won't start

```bash
# Check port availability
lsof -i :8000

# Check container logs
docker logs <container-id>
```

### SOLVE-IT data not found

For Docker images, data is embedded — this should not occur. File a bug if it does.

For Python installs, verify `SOLVE_IT_DATA_PATH` points to a directory containing `techniques.json`, `weaknesses.json`, and `mitigations.json`.

### Tools not appearing in MCP client

1. Restart your MCP client
2. Check configuration file syntax
3. Verify the server is running: `curl http://localhost:8000/healthz`

For more help, see the [Troubleshooting Guide](guides/troubleshooting.md).

## Next Steps

- **Forensic Analysts**: [Practical Investigation Guide](guides/for-forensic-analysts.md)
- **Researchers**: [Citation & Academic Use](guides/for-researchers.md)
- **Production Deployment**: [Docker Guide](deployment/docker.md) | [Kubernetes Guide](deployment/kubernetes.md)
- **All Tools**: [Tools Reference](reference/tools-overview.md)
