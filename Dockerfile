# Production Dockerfile for SOLVE-IT MCP Server - Alpine Linux
# Multi-stage build for minimal image size and maximum security
# Supports multi-architecture: linux/amd64, linux/arm64, linux/arm/v7
# Base: Alpine Linux (musl libc) for smallest attack surface

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.12-alpine AS builder

# Install system dependencies needed for building Python packages
# Alpine uses apk instead of apt-get
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    git \
    cargo \
    rust

# Create virtual environment for isolated dependency management
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements file
WORKDIR /build
COPY requirements.txt .

# Install only production dependencies (exclude dev tools)
# We filter out pytest, mypy, black, ruff from requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    sed -E '/^(pytest|mypy|black|ruff)/d' requirements.txt > requirements.prod.txt && \
    pip install --no-cache-dir -r requirements.prod.txt

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.12-alpine AS runtime

# Build arguments for flexibility
ARG SOLVE_IT_SOURCE=github
ARG SOLVE_IT_VERSION=main
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=stable
# Ensure BUILD_DATE is RFC3339 compliant, provide fallback if empty
ARG BUILD_DATE_RFC3339=${BUILD_DATE:-1970-01-01T00:00:00Z}

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

# Install runtime system dependencies and create non-root user
# Alpine uses apk instead of apt-get
RUN apk add --no-cache \
        git \
        curl \
        ca-certificates \
        libffi \
        openssl && \
    # Create non-root user for security \
    # Alpine uses addgroup/adduser instead of groupadd/useradd \
    addgroup -g 1000 mcpuser && \
    adduser -D -u 1000 -G mcpuser -h /home/mcpuser -s /bin/sh mcpuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source code
COPY --chown=mcpuser:mcpuser src/ /app/src/

# Fetch SOLVE-IT knowledge base data and set ownership
# Two options based on SOLVE_IT_SOURCE build arg:
# 1. github (default): Clone from GitHub repository
# 2. local: Copy from local build context (requires solve-it-main/ directory)
RUN if [ "$SOLVE_IT_SOURCE" = "github" ]; then \
        echo "Cloning SOLVE-IT data from GitHub..."; \
        git clone --depth 1 --branch ${SOLVE_IT_VERSION} \
            https://github.com/SOLVE-IT-DF/solve-it.git /app/solve-it-main && \
        rm -rf /app/solve-it-main/.git; \
    else \
        echo "SOLVE-IT data will be copied from local context"; \
        mkdir -p /app/solve-it-main; \
    fi && \
    # Set ownership of all app files to non-root user \
    chown -R mcpuser:mcpuser /app

# Copy local SOLVE-IT data if building with SOLVE_IT_SOURCE=local
# Note: This step is only used when SOLVE_IT_SOURCE=local (requires solve-it-main/ in build context)
# For github mode (default), data is already cloned in previous step
# Commented out to avoid Podman build issues - uncomment if using local SOLVE-IT data
# COPY --chown=mcpuser:mcpuser solve-it-main/ /app/solve-it-main/

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
    LOG_FORMAT=json

# Expose HTTP port (default 8000, configurable via HTTP_PORT)
EXPOSE 8000

# Health check for HTTP mode (liveness probe using Kubernetes standard /healthz)
# Checks every 30s, timeout 3s, start after 10s, 3 retries before unhealthy
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD if [ "$MCP_TRANSPORT" = "http" ]; then \
            curl -f http://localhost:${HTTP_PORT}/healthz || exit 1; \
        else \
            exit 0; \
        fi

# Start the server
# Transport mode is controlled by MCP_TRANSPORT environment variable
# - http: HTTP/SSE transport for Kubernetes deployments
# - stdio: STDIO transport for MCP client connections
CMD ["sh", "-c", "python3 /app/src/server.py --transport ${MCP_TRANSPORT}"]
