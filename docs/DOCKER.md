# Docker Deployment Guide - SOLVE-IT MCP Server

This guide covers running the SOLVE-IT MCP Server using Docker and Docker Compose.

## Table of Contents

- [Quick Start](#quick-start)
- [Docker Images](#docker-images)
- [Transport Modes](#transport-modes)
- [Configuration](#configuration)
- [Docker Compose](#docker-compose)
- [Building Images](#building-images)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

---

## Quick Start

### Pull and Run (HTTP Mode)

```bash
# Pull the latest image
docker pull 3soos3/solve-it-mcp:latest

# Run in HTTP mode (for Kubernetes/web clients)
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  3soos3/solve-it-mcp:latest

# Test the server (Kubernetes standard endpoint)
curl http://localhost:8000/healthzz
```

### Run with Docker Compose

```bash
# Production mode (HTTP transport)
docker-compose up -d

# Development mode (STDIO transport with volume mounts)
docker-compose -f docker-compose.dev.yml up
```

---

## Docker Images

### Image Tags

Available on Docker Hub: `3soos3/solve-it-mcp`

| Tag | Description | Use Case |
|-----|-------------|----------|
| `latest` | Latest stable build | Production (auto-updates) |
| `stable` | Manual stable marker | Production (manually marked as stable) |
| `v0.2025-10-0.1.0` | Full version tag | Production (specific version) |
| `sha-abc1234` | Git commit SHA | Reproducible builds, debugging |

### Multi-Architecture Support

Images are available for:
- `linux/amd64` - Intel/AMD 64-bit (most common)
- `linux/arm64` - ARM 64-bit (Apple Silicon, AWS Graviton)
- `linux/arm/v7` - ARM 32-bit (Raspberry Pi)

Docker automatically pulls the correct architecture for your platform.

### Image Size

- **Production image**: ~200 MB (multi-stage build, optimized)
- **Development image**: ~450 MB (includes dev tools)

---

## Transport Modes

The server supports two transport modes, controlled by the `MCP_TRANSPORT` environment variable.

### HTTP Mode (Default in Docker)

Recommended for:
- Kubernetes deployments
- Web-based MCP clients
- Load-balanced environments
- Health check monitoring

```bash
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e HTTP_PORT=8000 \
  3soos3/solve-it-mcp:latest
```

**Health Endpoints:**
- `GET /healthz` - Liveness probe (Kubernetes standard)
- `GET /readyz` - Readiness probe (Kubernetes standard)
- `GET /health` - Legacy liveness probe (deprecated, use /healthz)
- `GET /ready` - Legacy readiness probe (deprecated, use /readyz)
- `POST /mcp/v1` - Main MCP endpoint (JSON or SSE)

### STDIO Mode

Recommended for:
- MCP clients (like Claude Desktop)
- Direct process communication
- Local development

```bash
docker run -i \
  -e MCP_TRANSPORT=stdio \
  3soos3/solve-it-mcp:latest
```

**Note**: STDIO mode requires `-i` (interactive) flag and doesn't expose HTTP endpoints.

---

## Configuration

### Environment Variables

#### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `http` | Transport mode: `http` or `stdio` |
| `LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | `json` | Log format: `json` or `text` |
| `SOLVEIT_DATA_PATH` | `/app/solve-it-main/data` | Path to SOLVE-IT knowledge base |

#### HTTP Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `HTTP_HOST` | `0.0.0.0` | Bind address (use 0.0.0.0 for Docker) |
| `HTTP_PORT` | `8000` | HTTP server port |
| `HTTP_WORKERS` | `1` | Number of worker processes |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |

#### OpenTelemetry Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OTEL_ENABLED` | `true` | Enable OpenTelemetry |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTel collector endpoint |
| `ENVIRONMENT` | `production` | Environment: `development`, `staging`, `production` |
| `OTEL_TRACE_SAMPLE_RATE` | varies | Trace sampling rate (0.0-1.0) |

**Sampling defaults:**
- Development: 100% (1.0)
- Staging: 50% (0.5)
- Production: 10% (0.1)

#### Kubernetes Metadata (Auto-injected)

| Variable | Default | Description |
|----------|---------|-------------|
| `K8S_POD_NAME` | `unknown` | Pod name (from downward API) |
| `K8S_NODE_NAME` | `unknown` | Node name (from downward API) |
| `K8S_NAMESPACE` | `default` | Namespace (from downward API) |

### Example Configurations

#### Minimal Production

```bash
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e LOG_LEVEL=INFO \
  -e OTEL_ENABLED=false \
  3soos3/solve-it-mcp:latest
```

#### Full Observability

```bash
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e OTEL_ENABLED=true \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317 \
  -e ENVIRONMENT=production \
  -e LOG_FORMAT=json \
  3soos3/solve-it-mcp:latest
```

#### Development (STDIO)

```bash
docker run -i \
  -e MCP_TRANSPORT=stdio \
  -e LOG_LEVEL=DEBUG \
  -e LOG_FORMAT=text \
  -e OTEL_ENABLED=false \
  3soos3/solve-it-mcp:latest
```

---

## Docker Compose

### Production Setup

**File**: `docker-compose.yml`

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Check health
curl http://localhost:8000/health

# Stop services
docker-compose down
```

**Features:**
- HTTP/SSE transport
- JSON logging
- OpenTelemetry enabled
- Health checks
- Resource limits (512MB memory, 1 CPU)
- Non-root user
- Auto-restart policy

### Development Setup

**File**: `docker-compose.dev.yml`

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up

# Run with volume mounts for hot-reload
docker-compose -f docker-compose.dev.yml up
```

**Features:**
- STDIO transport
- Volume mounts for live code editing
- DEBUG logging (text format)
- OpenTelemetry disabled
- Interactive mode
- No auto-restart

### Custom Compose Files

Override specific settings by creating a `docker-compose.override.yml`:

```yaml
version: '3.8'
services:
  solveit-mcp:
    environment:
      LOG_LEVEL: DEBUG
      CORS_ORIGINS: https://myapp.com
    ports:
      - "9000:8000"  # Use different port
```

Docker Compose automatically merges override files.

---

## Building Images

### Using the Build Script

The repository includes a helper script for building multi-arch images:

```bash
# Build and push to Docker Hub
./scripts/build-and-push.sh

# Build locally (no push)
./scripts/build-and-push.sh --no-push

# Build for specific platform
./scripts/build-and-push.sh --platform linux/amd64 --no-push

# Build and tag as latest
./scripts/build-and-push.sh --latest

# Add custom tags
./scripts/build-and-push.sh --tag v1.0.0 --tag production
```

### Manual Build (Single Architecture)

```bash
# Build for local platform
docker build -t solve-it-mcp:local .

# Build with custom SOLVE-IT version
docker build \
  --build-arg SOLVE_IT_VERSION=v0.2025-10 \
  -t solve-it-mcp:0.2025-10 .

# Build using local SOLVE-IT data
docker build \
  --build-arg SOLVE_IT_SOURCE=local \
  -t solve-it-mcp:local-data .
```

**Note**: For local SOLVE-IT data, place the dataset in `./solve-it-main/` before building.

### Multi-Architecture Build

Requires Docker Buildx:

```bash
# Create builder
docker buildx create --name mcp-builder --use

# Build for all platforms
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --tag 3soos3/solve-it-mcp:latest \
  --push \
  .
```

### Development Image

```bash
# Build development image
docker build -f Dockerfile.dev -t solve-it-mcp:dev .

# Run with volume mounts
docker run -i \
  -v $(pwd)/src:/app/src:ro \
  solve-it-mcp:dev
```

---

## Troubleshooting

### Common Issues

#### 1. Container Exits Immediately

**Problem**: Container starts but exits right away.

**Solution**: Check logs:
```bash
docker logs <container-id>

# Or with compose
docker-compose logs
```

Common causes:
- Invalid transport mode (use `http` or `stdio`)
- Missing required environment variables
- Port already in use

#### 2. Health Check Failing

**Problem**: `/healthz` endpoint returns errors or timeouts.

**Solution**:
```bash
# Check if HTTP mode is enabled
docker exec <container-id> env | grep MCP_TRANSPORT

# Should show: MCP_TRANSPORT=http

# Test from inside container (Kubernetes standard)
docker exec <container-id> curl -f http://localhost:8000/healthz

# Or test legacy endpoint (deprecated)
docker exec <container-id> curl -f http://localhost:8000/health
```

Health checks only work in HTTP mode. In STDIO mode, health checks are disabled.

**Note**: Use `/healthz` and `/readyz` (Kubernetes standard) instead of `/health` and `/ready` (deprecated).

#### 3. Permission Denied

**Problem**: Cannot write to mounted volumes.

**Solution**: The container runs as UID 1000. Ensure your volume directories have correct permissions:
```bash
# Fix permissions
sudo chown -R 1000:1000 ./local-data/

# Or run with current user
docker run --user $(id -u):$(id -g) ...
```

#### 4. SOLVE-IT Data Not Found

**Problem**: Server can't load knowledge base data.

**Solution**: The data is baked into the image. If using custom data:
```bash
# Verify data exists in container
docker exec <container-id> ls -la /app/solve-it-main/data/

# Should show: techniques.json, weaknesses.json, mitigations.json

# If missing, rebuild image or mount data:
docker run -v $(pwd)/solve-it-main:/app/solve-it-main:ro ...
```

#### 5. Multi-arch Build Fails

**Problem**: `docker buildx build` fails or is slow.

**Solution**:
```bash
# Install QEMU for cross-platform builds
docker run --privileged --rm tonistiigi/binfmt --install all

# Use buildkit cache
docker buildx build --cache-from type=registry,ref=3soos3/solve-it-mcp:buildcache ...
```

For local testing, build only your platform:
```bash
./scripts/build-and-push.sh --platform linux/amd64 --no-push
```

### Debugging

#### Enable Debug Logging

```bash
docker run -e LOG_LEVEL=DEBUG -e LOG_FORMAT=text ...
```

#### Access Container Shell

```bash
# Running container
docker exec -it <container-id> /bin/bash

# New container
docker run -it --entrypoint /bin/bash 3soos3/solve-it-mcp:latest
```

#### Inspect Image Layers

```bash
# View image history
docker history 3soos3/solve-it-mcp:latest

# Inspect image metadata
docker inspect 3soos3/solve-it-mcp:latest
```

---

## Security

### Image Security

✅ **Non-root user**: Container runs as UID 1000 (mcpuser)  
✅ **Minimal base image**: Python 3.12-slim (reduces attack surface)  
✅ **Multi-stage build**: Build tools excluded from runtime  
✅ **Vulnerability scanning**: Trivy scanning in CI/CD  
✅ **No secrets**: No hardcoded credentials or tokens  
✅ **Read-only filesystem**: Compatible with read-only root (optional)

### Vulnerability Scanning

Images are automatically scanned in CI/CD. Scan locally:

```bash
# Install Trivy
brew install aquasecurity/trivy/trivy  # macOS
# or: apt-get install trivy             # Debian/Ubuntu

# Scan image
trivy image 3soos3/solve-it-mcp:latest

# Scan for CRITICAL/HIGH only
trivy image --severity CRITICAL,HIGH 3soos3/solve-it-mcp:latest
```

### Runtime Security

**Docker Run Flags:**
```bash
docker run \
  --security-opt=no-new-privileges:true \
  --cap-drop=ALL \
  --read-only \
  --tmpfs /tmp \
  -u 1000:1000 \
  3soos3/solve-it-mcp:latest
```

**Docker Compose Security:**
```yaml
services:
  solveit-mcp:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp
    user: "1000:1000"
```

### Network Security

**Limit exposed ports:**
```bash
# Bind to localhost only
docker run -p 127.0.0.1:8000:8000 ...
```

**Configure CORS:**
```bash
# Production: specific origins only
docker run -e CORS_ORIGINS=https://app.example.com,https://dashboard.example.com ...

# Development: allow all
docker run -e CORS_ORIGINS=* ...
```

### Secrets Management

**Never pass secrets via environment variables in production.**

Use Docker secrets or volume mounts:

```bash
# Docker secrets (Swarm)
echo "my-secret-token" | docker secret create mcp_token -
docker service create --secret mcp_token ...

# Volume mount (single container)
docker run -v /path/to/secrets:/secrets:ro ...
```

---

## Next Steps

- **Kubernetes Deployment**: See [KUBERNETES.md](./KUBERNETES.md)
- **Helm Charts**: Visit [3soos3/solveit-charts](https://github.com/3soos3/solveit-charts)
- **CI/CD**: Check `.github/workflows/docker-publish.yml` for automated builds
- **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## Resources

- **Docker Hub**: https://hub.docker.com/r/3soos3/solve-it-mcp
- **GitHub**: https://github.com/3soos3/solve-it-mcp
- **SOLVE-IT Dataset**: https://github.com/SOLVE-IT-DF/solve-it
- **MCP Specification**: https://modelcontextprotocol.io
