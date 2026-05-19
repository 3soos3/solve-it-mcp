# Environment Variables Reference

Complete reference for all environment variables supported by the SOLVE-IT MCP Server.
Variables can be set in a `docker run -e` flag, a `docker-compose.yml` `environment:` block,
a Kubernetes ConfigMap, or directly in the shell before running the server locally.

---

## Quick Reference

| Variable | Default | Image type |
|---|---|---|
| [`MCP_TRANSPORT`](#mcp_transport) | `stdio` / `http`* | all |
| [`HTTP_HOST`](#http_host) | `0.0.0.0` | all |
| [`HTTP_PORT`](#http_port) | `8000` | all |
| [`HTTP_WORKERS`](#http_workers) | `1` | all |
| [`MCP_BASE_PATH`](#mcp_base_path) | `/mcp/v1` | all |
| [`SOLVE_IT_DATA_PATH`](#solve_it_data_path) | `/app/solve-it-main/data` | latest, release |
| [`SOLVE_IT_DATA_URL`](#solve_it_data_url) | `https://data.solveit-df.org/solve-it-latest.zip` | live |
| [`FORENSIC_METADATA`](#forensic_metadata) | `false` / `true`* | all |
| [`IMAGE_TAG`](#image_tag) | set at build time | all |
| [`MCP_VERSION`](#mcp_version) | set at build time | all |
| [`OTEL_ENABLED`](#otel_enabled) | `true` | all |
| [`OTEL_EXPORTER_OTLP_ENDPOINT`](#otel_exporter_otlp_endpoint) | `http://localhost:4317` | all |
| [`ENVIRONMENT`](#environment) | `production` | all |
| [`OTEL_TRACE_SAMPLE_RATE`](#otel_trace_sample_rate) | env-based | all |
| [`LOG_LEVEL`](#log_level) | `INFO` | all |
| [`LOG_FORMAT`](#log_format) | `json` | all |
| [`K8S_POD_NAME`](#kubernetes-metadata) | `unknown` | all |
| [`K8S_NODE_NAME`](#kubernetes-metadata) | `unknown` | all |
| [`K8S_NAMESPACE`](#kubernetes-metadata) | `default` | all |

\* `MCP_TRANSPORT` defaults to `http` inside Docker images, `stdio` when running locally.
`FORENSIC_METADATA` defaults to `true` only in the `:release` image; `false` in `:live` and `:latest`.

---

## Transport & Networking

### `MCP_TRANSPORT`

Transport protocol used by the server.

| | |
|---|---|
| **Values** | `http`, `stdio` |
| **Default (Docker)** | `http` |
| **Default (local)** | `stdio` |

```bash
# HTTP mode — web clients, Kubernetes, Traefik
docker run -e MCP_TRANSPORT=http ...

# STDIO mode — Claude Desktop, local tools
docker run -i -e MCP_TRANSPORT=stdio ...
```

---

### `HTTP_HOST`

IP address the HTTP server binds to.

| | |
|---|---|
| **Values** | any valid IP or `0.0.0.0` |
| **Default** | `0.0.0.0` |

Always use `0.0.0.0` in containers so the server accepts traffic from outside the container network.

---

### `HTTP_PORT`

TCP port the HTTP server listens on.

| | |
|---|---|
| **Values** | any valid port number |
| **Default** | `8000` |

```bash
docker run -p 9000:9000 -e HTTP_PORT=9000 ...
```

---

### `HTTP_WORKERS`

Number of Uvicorn worker processes.

| | |
|---|---|
| **Values** | positive integer |
| **Default** | `1` |

For production under load, set to `CPU cores × 2`. For Kubernetes with horizontal pod autoscaling, keep at `1` and scale pods instead.

---

### `MCP_BASE_PATH`

URL path prefix for all MCP endpoints.

| | |
|---|---|
| **Values** | any URL path string |
| **Default** | `/mcp/v1` |

The default exposes the server at `http://host:8000/mcp/v1`. Set to `/` to expose at the domain root — useful when running behind a reverse proxy with host-based routing (e.g. Traefik on `mcp.yourdomain.tld`).

```bash
# Access at https://mcp.yourdomain.tld (no path prefix)
docker run -e MCP_BASE_PATH=/ ...
```

!!! note "Traefik + SSE buffering"
    When using Traefik, add a middleware that sets `X-Accel-Buffering: no` to prevent SSE stream buffering.

---


## Data

### `SOLVE_IT_DATA_PATH`

Path to the SOLVE-IT knowledge base data directory inside the container.

| | |
|---|---|
| **Values** | absolute path |
| **Default** | `/app/solve-it-main/data` |
| **Applies to** | `:latest`, `:release` images (data is baked in) |

Only change this if you mount custom SOLVE-IT data into the container:

```bash
docker run -v /path/to/my-solve-it/data:/data:ro \
           -e SOLVE_IT_DATA_PATH=/data ...
```

---

### `SOLVE_IT_DATA_URL`

URL from which the `:live` image downloads SOLVE-IT data at container startup.

| | |
|---|---|
| **Values** | any HTTPS URL to a `.zip` archive |
| **Default** | `https://data.solveit-df.org/solve-it-latest.zip` |
| **Applies to** | `:live` image only |

Override to point at a specific archived snapshot for reproducible testing:

```bash
docker run -e SOLVE_IT_DATA_URL=https://your-mirror.example.com/solve-it-2026-01.zip ...
```

!!! warning "Forensic use"
    The `:live` image always fetches the latest data at startup, so two containers started at different times may query different knowledge bases. For forensically reproducible results, use `:release` images where the data is pinned at build time.

---

## Forensic Traceability

### `FORENSIC_METADATA`

When enabled, every tool response includes a `_meta` block containing the image tag, MCP version, and a UTC timestamp. This allows you to reconstruct exactly which software and data version produced a given result.

| | |
|---|---|
| **Values** | `true`, `1`, `yes` to enable; anything else disables |
| **Default (`:live`)** | `false` |
| **Default (`:latest`)** | `false` |
| **Default (`:release`)** | `true` |

```bash
# Enable on live/latest for testing or academic use
docker run -e FORENSIC_METADATA=true ...
```

**Example `_meta` block injected into every tool response:**

```json
{
  "id": "DFT-1001",
  "name": "RAM Acquisition",
  ...
  "_meta": {
    "image_tag": "v2025-10-abc1234",
    "mcp_version": "abc1234",
    "timestamp": "2026-05-17T09:32:11.042Z"
  }
}
```

**Why only `:release` by default?**

- **`:release`** — data and code are both pinned; the `_meta` block is a meaningful, citable record of exactly which version produced the output.
- **`:latest`** — data changes weekly; `image_tag` changes with every SOLVE-IT commit. The metadata is technically accurate but adds noise to every response without a stable reference for citations.
- **`:live`** — data is fetched fresh at startup; two containers started minutes apart may produce different results. The metadata reflects the MCP image version but not the data version, making it misleading for forensic purposes.

---

### `IMAGE_TAG`

Human-readable tag embedded in the `_meta.image_tag` field. Set automatically at build time; **not intended to be overridden at runtime**.

| Image | Value |
|---|---|
| `:live` | `live-<mcp-sha>` |
| `:latest` | `<solve-it-sha>-<mcp-sha>` |
| `:release` | `<solve-it-release>-<mcp-sha>` |

Example: `v2025-10-abc1234` — SOLVE-IT release `v2025-10`, MCP commit `abc1234`.

---

### `MCP_VERSION`

Short Git SHA of the MCP server commit, embedded in `_meta.mcp_version`. Set at build time.

| | |
|---|---|
| **Default** | set from `VCS_REF` build ARG |
| **Example value** | `abc1234` |

This is a short SHA, not a semver. For the full image identity, see `IMAGE_TAG` which combines both the SOLVE-IT data reference and the MCP SHA.

---

## Observability

### `OTEL_ENABLED`

Master switch for OpenTelemetry tracing and metrics.

| | |
|---|---|
| **Values** | `true`, `false` |
| **Default** | `true` |

Disable for local development or when no OTel collector is available:

```bash
-e OTEL_ENABLED=false
```

---

### `OTEL_EXPORTER_OTLP_ENDPOINT`

OpenTelemetry collector endpoint (OTLP gRPC protocol).

| | |
|---|---|
| **Values** | URL |
| **Default** | `http://localhost:4317` |

```bash
-e OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

---

### `ENVIRONMENT`

Deployment environment. Controls the default trace sampling rate and affects log context.

| | |
|---|---|
| **Values** | `development`, `staging`, `production` |
| **Default (Docker)** | `production` |
| **Default (local)** | `development` |

---

### `OTEL_TRACE_SAMPLE_RATE`

Override the automatic sampling rate for traces.

| | |
|---|---|
| **Values** | float `0.0`–`1.0` |
| **Default** | derived from `ENVIRONMENT` |

| `ENVIRONMENT` | Default rate |
|---|---|
| `production` | `0.1` (10%) |
| `staging` | `0.5` (50%) |
| `development` | `1.0` (100%) |

```bash
# Sample 25% regardless of environment
-e OTEL_TRACE_SAMPLE_RATE=0.25
```

---

## Logging

### `LOG_LEVEL`

Minimum log severity to emit.

| | |
|---|---|
| **Values** | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| **Default** | `INFO` |

```bash
-e LOG_LEVEL=DEBUG    # verbose, for troubleshooting
-e LOG_LEVEL=WARNING  # quiet, for high-traffic production
```

---

### `LOG_FORMAT`

Log output format.

| | |
|---|---|
| **Values** | `json`, `text` |
| **Default** | `json` |

- `json` — structured JSON lines, best for log aggregators (Loki, Splunk, ELK)
- `text` — human-readable, best for local development

---

## Kubernetes Metadata

These are auto-injected by the Kubernetes downward API. Do not set manually.

| Variable | Description | Default |
|---|---|---|
| `K8S_POD_NAME` | Name of the running pod | `unknown` |
| `K8S_NODE_NAME` | Node the pod is scheduled on | `unknown` |
| `K8S_NAMESPACE` | Kubernetes namespace | `default` |

Example downward API configuration:

```yaml
env:
  - name: K8S_POD_NAME
    valueFrom:
      fieldRef:
        fieldPath: metadata.name
  - name: K8S_NODE_NAME
    valueFrom:
      fieldRef:
        fieldPath: spec.nodeName
  - name: K8S_NAMESPACE
    valueFrom:
      fieldRef:
        fieldPath: metadata.namespace
```

---

## Image-type Summary

| Variable | `:live` | `:latest` | `:release` |
|---|---|---|---|
| `MCP_TRANSPORT` | `http` | `http` | `http` |
| `SOLVE_IT_DATA_PATH` | n/a (fetched at startup) | `/app/solve-it-main/data` | `/app/solve-it-main/data` |
| `SOLVE_IT_DATA_URL` | `https://data.solveit-df.org/...` | n/a | n/a |
| `IMAGE_TAG` | `live-<mcp-sha>` | `<solve-it-sha>-<mcp-sha>` | `<solve-it-release>-<mcp-sha>` |
| `FORENSIC_METADATA` | `false` | `false` | `true` |
| `ENVIRONMENT` | `production` | `production` | `production` |
| `OTEL_ENABLED` | `true` | `true` | `true` |

---

## Example Configurations

### Minimal local run (no telemetry)

```bash
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e OTEL_ENABLED=false \
  -e LOG_FORMAT=text \
  3soos3/solve-it-mcp:latest
```

### Behind Traefik at `mcp.yourdomain.tld`

```yaml
environment:
  - MCP_TRANSPORT=http
  - MCP_BASE_PATH=/
  - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
  - ENVIRONMENT=production
  - LOG_LEVEL=INFO
```

### Forensic investigation (release image)

```bash
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e FORENSIC_METADATA=true \
  -e LOG_LEVEL=INFO \
  ghcr.io/3soos3/solve-it-mcp:v2025-10-abc1234
```

### Live image with metadata enabled (academic / testing)

```bash
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e FORENSIC_METADATA=true \
  3soos3/solve-it-mcp:live
```

!!! note
    Even with `FORENSIC_METADATA=true`, the `:live` image `_meta.image_tag` only reflects the MCP version — not the SOLVE-IT data version, because the data is fetched dynamically at startup.
