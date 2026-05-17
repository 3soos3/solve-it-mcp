# Docker Deployment

This guide covers running SOLVE-IT MCP Server with Docker and Docker Compose.

## Quick Start

```bash
docker pull 3soos3/solve-it-mcp:latest

docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  3soos3/solve-it-mcp:latest

curl http://localhost:8000/healthz
```

---

## Image Types

Three image types are published, differing in how SOLVE-IT data is sourced and when.

| | `:live` | `:latest` | `:release` |
|---|---|---|---|
| **Data source** | Fetched from URL at startup | SOLVE-IT `main` SHA baked in at build | Official SOLVE-IT release baked in at build |
| **Data version** | Always latest | Changes with each SOLVE-IT commit | Pinned to a specific release (e.g. `v2025-10`) |
| **`FORENSIC_METADATA`** | `false` | `false` | `true` |
| **Use case** | Always-current testing | Tracking SOLVE-IT main | Forensic casework, research, production |

### Image Tag Format

| Image | Tag format | Example |
|---|---|---|
| `:live` | `live-<mcp-sha>` | `live-abc1234` |
| `:latest` | `<solve-it-sha>-<mcp-sha>` | `def5678-abc1234` |
| `:release` | `<solve-it-release>-<mcp-sha>` | `v2025-10-abc1234` |

!!! warning "Forensic use"
    For forensic investigations or research requiring reproducibility, use `:release` images. The `:live` image fetches data fresh at startup — two containers started at different times may have different knowledge bases. See [FORENSIC_METADATA](../reference/environment-variables.md#forensic_metadata) for details.

---

## Registries

Images are published to two registries:

### Docker Hub — `3soos3/solve-it-mcp`

For general use. No authentication required.

```bash
docker pull 3soos3/solve-it-mcp:latest
```

Does **not** include Cosign signatures or SBOM attachments (keeps tag list clean).

### GHCR — `ghcr.io/3soos3/solve-it-mcp`

For CI/CD pipelines and forensic verification. Includes Cosign signatures, SBOM, and SLSA provenance.

```bash
docker pull ghcr.io/3soos3/solve-it-mcp:latest
```

---

## Transport Modes

### HTTP Mode (default in Docker)

For Kubernetes, web clients, and load-balanced deployments.

```bash
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  3soos3/solve-it-mcp:latest
```

**Health endpoints:**

- `GET /healthz` — liveness probe (primary)
- `GET /readyz` — readiness probe (primary)
- `GET /health` — legacy alias (deprecated)
- `GET /ready` — legacy alias (deprecated)

### STDIO Mode

For desktop MCP clients (Claude Desktop, Cline).

```bash
docker run -i \
  -e MCP_TRANSPORT=stdio \
  3soos3/solve-it-mcp:latest
```

!!! note
    STDIO mode requires the `-i` (interactive) flag. Health endpoints are not available in STDIO mode.

---

## Configuration

All configuration is via environment variables. See the [Environment Variables Reference](../reference/environment-variables.md) for the complete list.

### Common Examples

**Minimal (no telemetry):**

```bash
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e OTEL_ENABLED=false \
  -e LOG_FORMAT=text \
  3soos3/solve-it-mcp:latest
```

**With OpenTelemetry:**

```bash
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e OTEL_ENABLED=true \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317 \
  -e ENVIRONMENT=production \
  3soos3/solve-it-mcp:latest
```

**Development (STDIO, debug logging):**

```bash
docker run -i \
  -e MCP_TRANSPORT=stdio \
  -e LOG_LEVEL=DEBUG \
  -e LOG_FORMAT=text \
  -e OTEL_ENABLED=false \
  3soos3/solve-it-mcp:latest
```

**Behind Traefik at domain root:**

```bash
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e MCP_BASE_PATH=/ \
  3soos3/solve-it-mcp:latest
```

---

## Docker Compose

```yaml
services:
  solve-it-mcp:
    image: 3soos3/solve-it-mcp:latest
    ports:
      - "8000:8000"
    environment:
      - MCP_TRANSPORT=http
      - LOG_LEVEL=INFO
      - LOG_FORMAT=json
      - OTEL_ENABLED=false
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 15s
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp
    user: "1000:1000"
```

---

## Multi-Architecture Support

All images are built for:

- `linux/amd64` — Intel/AMD 64-bit
- `linux/arm64` — ARM 64-bit (Apple Silicon, AWS Graviton)
- `linux/arm/v7` — ARM 32-bit (Raspberry Pi)

Docker pulls the correct architecture automatically.

---

## Building Locally

### Single Architecture

```bash
docker build -t solve-it-mcp:local .

# With a specific SOLVE-IT version
docker build \
  --build-arg SOLVE_IT_VERSION=v0.2025-10 \
  -t solve-it-mcp:0.2025-10 .
```

### Multi-Architecture

```bash
docker buildx create --name mcp-builder --use

docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --tag 3soos3/solve-it-mcp:local \
  --push \
  .
```

---

## Security

### Image Security

- Non-root user: `mcpuser` (UID 1000)
- Base image: Python 3.12-Alpine (minimal attack surface)
- Multi-stage build: build tools excluded from runtime image
- Trivy vulnerability scanning in CI/CD

### Hardened Runtime Flags

```bash
docker run \
  --security-opt=no-new-privileges:true \
  --cap-drop=ALL \
  --read-only \
  --tmpfs /tmp \
  -u 1000:1000 \
  3soos3/solve-it-mcp:latest
```

### Vulnerability Scanning

```bash
# Install Trivy
brew install aquasecurity/trivy/trivy   # macOS
# apt-get install trivy                 # Debian/Ubuntu

trivy image --severity CRITICAL,HIGH 3soos3/solve-it-mcp:latest
```

---

## Forensic Verification (GHCR Only)

GHCR images include cryptographic signatures, SBOM, and SLSA provenance.

### Verify Image Signature

```bash
cosign verify ghcr.io/3soos3/solve-it-mcp:latest \
  --certificate-identity-regexp=github \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com
```

### Download SBOM

```bash
cosign download sbom ghcr.io/3soos3/solve-it-mcp:latest > sbom.spdx.json

# Inspect dependencies
jq '.packages[] | {name: .name, version: .versionInfo}' sbom.spdx.json
```

### View Build Provenance

```bash
cosign download attestation ghcr.io/3soos3/solve-it-mcp:latest | jq
```

!!! note
    Docker Hub images do **not** include Cosign signatures or SBOM to keep the tag list clean. Use GHCR images for forensic verification and compliance.

---

## Troubleshooting

### Container Exits Immediately

```bash
docker logs <container-id>
```

Common causes: invalid `MCP_TRANSPORT` value, port already in use.

### Health Check Failing

```bash
# Check transport mode
docker exec <container-id> env | grep MCP_TRANSPORT

# Test endpoint
docker exec <container-id> wget -qO- http://localhost:8000/healthz
```

### Permission Denied on Volume Mount

The container runs as UID 1000. Fix volume permissions:

```bash
sudo chown -R 1000:1000 ./local-data/
```

---

## Next Steps

- [Kubernetes Deployment](kubernetes.md) — production Kubernetes with Helm
- [Environment Variables Reference](../reference/environment-variables.md) — complete configuration reference
- [Security Model](../architecture/security-model.md) — chain-of-custody and verification details
