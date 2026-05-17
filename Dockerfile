# syntax=docker/dockerfile:1.4
# Production Dockerfile for SOLVE-IT MCP Server - Alpine Linux
# Multi-stage build for minimal image size and maximum security
# Supports multi-architecture: linux/amd64, linux/arm64, linux/arm/v7

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.12-alpine AS builder

# Build args
ARG SOLVE_IT_VERSION=main
ARG SOLVE_IT_SHA=unknown
ARG MCP_VERSION=unknown

# Install build dependencies (will be removed in same layer)
RUN apk add --no-cache --virtual .build-deps \
    build-base \
    libffi-dev \
    openssl-dev \
    git \
    cargo \
    rust

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy pyproject.toml and README for pip install
WORKDIR /build
COPY pyproject.toml README.md ./

# Fetch SOLVE-IT data
RUN git clone --depth 1 --branch ${SOLVE_IT_VERSION} \
    https://github.com/SOLVE-IT-DF/solve-it.git /tmp/solve-it-main && \
    rm -rf /tmp/solve-it-main/.git

# Install all dependencies (app + solve-it library), then clean up
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . && \
    grep -v '^\s*pytest' /tmp/solve-it-main/requirements.txt | \
        pip install --no-cache-dir -r /dev/stdin && \
    # Cleanup to reduce venv size
    pip uninstall -y pip setuptools wheel && \
    find /opt/venv -type f -name '*.pyc' -delete && \
    find /opt/venv -type f -name '*.pyo' -delete && \
    find /opt/venv -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true

# Remove build dependencies
RUN apk del .build-deps

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.12-alpine AS runtime

# Build arguments for flexibility
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=stable
ARG BUILD_DATE_RFC3339=${BUILD_DATE:-1970-01-01T00:00:00Z}
ARG SOLVE_IT_SHA=unknown
ARG MCP_VERSION=unknown

# Metadata labels following OCI Image Spec
LABEL org.opencontainers.image.created="${BUILD_DATE_RFC3339}" \
      org.opencontainers.image.url="https://github.com/3soos3/solve-it-mcp" \
      org.opencontainers.image.documentation="https://github.com/3soos3/solve-it-mcp/blob/main/README.md" \
      org.opencontainers.image.source="https://github.com/3soos3/solve-it-mcp" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.title="SOLVE-IT MCP Server" \
      org.opencontainers.image.description="MCP server providing LLM access to the SOLVE-IT Digital Forensics Knowledge Base" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.base.name="docker.io/library/python:3.12-alpine"

# Install minimal runtime dependencies and create non-root user
# Removed: git (only needed in builder), curl (use wget instead)
RUN apk add --no-cache \
        ca-certificates \
        libffi \
        openssl && \
    # Create non-root user for security
    addgroup -g 1000 mcpuser && \
    adduser -D -u 1000 -G mcpuser -h /home/mcpuser -s /bin/sh mcpuser && \
    # Security hardening
    chmod 750 /home/mcpuser && \
    # Create tmp directories for runtime
    mkdir -p /tmp/app-cache /tmp/app-tmp && \
    chown -R mcpuser:mcpuser /tmp/app-cache /tmp/app-tmp && \
    # Clean apk cache
    rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source code
COPY --chown=mcpuser:mcpuser src/ /app/src/

# Copy SOLVE-IT data from builder stage (no git in runtime)
COPY --from=builder --chown=mcpuser:mcpuser /tmp/solve-it-main /app/solve-it-main

# Switch to non-root user
USER mcpuser

# Environment variables with sensible defaults
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SOLVE_IT_DATA_PATH=/app/solve-it-main/data \
    MCP_TRANSPORT=http \
    HTTP_HOST=0.0.0.0 \
    HTTP_PORT=8000 \
    OTEL_ENABLED=true \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    TMPDIR=/tmp/app-tmp \
    IMAGE_TAG=${SOLVE_IT_SHA}-${MCP_VERSION} \
    MCP_VERSION=${MCP_VERSION} \
    FORENSIC_METADATA=false

# Expose HTTP port (default 8000, configurable via HTTP_PORT)
EXPOSE 8000

# Health check using wget (built into Alpine, no curl needed)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD if [ "$MCP_TRANSPORT" = "http" ]; then \
            wget --no-verbose --tries=1 --spider http://localhost:${HTTP_PORT}/healthz || exit 1; \
        else \
            exit 0; \
        fi

# Start the server
CMD ["sh", "-c", "python3 /app/src/server.py --transport ${MCP_TRANSPORT}"]
