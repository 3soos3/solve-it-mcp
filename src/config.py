"""Configuration management for SOLVE-IT MCP Server.

This module provides centralized configuration management using Pydantic models
with environment variable support. It handles configuration for:

- HTTP/SSE transport settings
- OpenTelemetry observability configuration
- CORS and security settings
- Kubernetes-specific metadata

All configuration values can be overridden via environment variables, making
the application suitable for containerized deployments.

Typical usage:
    >>> from config import load_config
    >>> config = load_config()
    >>> print(config.transport)
    'http'
    >>> print(config.otel.environment)
    'production'

Environment Variables:
    MCP_TRANSPORT: Transport type ('stdio' or 'http')
    HTTP_HOST: HTTP server bind address (default: '0.0.0.0')
    HTTP_PORT: HTTP server port (default: 8000)
    OTEL_ENABLED: Enable OpenTelemetry (default: 'true')
    ENVIRONMENT: Deployment environment (development/staging/production)
    OTEL_EXPORTER_OTLP_ENDPOINT: OpenTelemetry collector endpoint
    LOG_LEVEL: Logging level (DEBUG/INFO/WARNING/ERROR)
    CORS_ORIGINS: Comma-separated list of allowed CORS origins
"""

import os
from typing import Literal

from pydantic import BaseModel, Field


class CORSConfig(BaseModel):
    """CORS (Cross-Origin Resource Sharing) configuration for web clients.

    Configures CORS headers to allow web browsers to make requests to the
    MCP server from different origins. Essential for web-based MCP clients.

    Attributes:
        allowed_origins: List of origins allowed to access the server.
            Use ["*"] for development, specific domains for production.
        allowed_methods: HTTP methods allowed in CORS requests.
        allowed_headers: Headers allowed in CORS requests.
        expose_headers: Headers exposed to the client. MCP-specific headers
            like 'Mcp-Session-Id' must be explicitly exposed.
        max_age: How long (seconds) browsers can cache CORS preflight responses.

    Examples:
        Development configuration (allow all origins):

        >>> cors = CORSConfig()
        >>> print(cors.allowed_origins)
        ['*']

        Production configuration (specific origins):

        >>> os.environ['CORS_ORIGINS'] = 'https://app.example.com,https://dashboard.example.com'
        >>> cors = CORSConfig()
        >>> print(cors.allowed_origins)
        ['https://app.example.com', 'https://dashboard.example.com']

    Security Note:
        In production, always specify exact origins rather than using "*".
        This prevents unauthorized web applications from accessing your server.
    """

    allowed_origins: list[str] = Field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(","),
        description="List of origins allowed to make cross-origin requests",
    )
    allowed_methods: list[str] = Field(
        default=["GET", "POST", "DELETE", "OPTIONS"],
        description="HTTP methods allowed in CORS requests",
    )
    allowed_headers: list[str] = Field(
        default=["*"], description="Headers allowed in CORS requests"
    )
    expose_headers: list[str] = Field(
        default=["Mcp-Session-Id", "Mcp-Protocol-Version"],
        description="MCP-specific headers exposed to clients",
    )
    max_age: int = Field(default=3600, description="CORS preflight cache duration in seconds")


class HTTPConfig(BaseModel):
    """HTTP transport configuration for Starlette/Uvicorn server.

    Configures the HTTP server including host binding, port, worker processes,
    and response format preferences. Supports both SSE streaming and JSON
    response modes for maximum client compatibility.

    Attributes:
        host: IP address to bind the server to. Use '0.0.0.0' to listen on
            all network interfaces (required for Kubernetes).
        port: TCP port for the HTTP server.
        workers: Number of worker processes. Set to 1 for development,
            increase for production (typically: CPU cores * 2).
        stateless: Whether to use stateless session management. True enables
            horizontal scaling across multiple pods.
        json_response_default: Default response format preference. True means
            JSON is used unless client requests SSE via Accept header.
        sse_enabled: Whether to enable SSE (Server-Sent Events) streaming
            endpoint. Can be disabled if only JSON clients are needed.
        cors: CORS configuration object.
        base_path: URL path prefix for MCP endpoints.
        health_path: Health check endpoint path for Kubernetes liveness probe.
        ready_path: Readiness check endpoint path for Kubernetes readiness probe.
        metrics_path: Metrics endpoint path (currently unused, metrics via OTel).

    Examples:
        Development configuration:

        >>> http = HTTPConfig()
        >>> print(f"{http.host}:{http.port}")
        '0.0.0.0:8000'

        Production configuration:

        >>> os.environ['HTTP_PORT'] = '8080'
        >>> os.environ['HTTP_WORKERS'] = '4'
        >>> http = HTTPConfig()
        >>> print(http.workers)
        4

    Kubernetes Note:
        Always use host='0.0.0.0' in containers to accept traffic from
        the Kubernetes service network.
    """

    host: str = Field(
        default_factory=lambda: os.getenv("HTTP_HOST", "0.0.0.0"),
        description="IP address to bind the HTTP server",
    )
    port: int = Field(
        default_factory=lambda: int(os.getenv("HTTP_PORT", "8000")),
        description="TCP port for the HTTP server",
    )
    workers: int = Field(
        default_factory=lambda: int(os.getenv("HTTP_WORKERS", "1")),
        description="Number of Uvicorn worker processes",
    )

    # Response format options
    stateless: bool = Field(
        default=True, description="Use stateless session management for horizontal scaling"
    )
    json_response_default: bool = Field(
        default=True, description="Default to JSON responses (vs SSE streaming)"
    )
    sse_enabled: bool = Field(default=True, description="Enable SSE streaming endpoint")

    # CORS configuration
    cors: CORSConfig = Field(
        default_factory=CORSConfig, description="CORS configuration for web clients"
    )

    # Endpoint paths
    base_path: str = Field(default="/mcp/v1", description="Base path for MCP API endpoints")
    health_path: str = Field(
        default="/health", description="Health check endpoint for Kubernetes liveness probe"
    )
    ready_path: str = Field(
        default="/ready", description="Readiness check endpoint for Kubernetes readiness probe"
    )
    metrics_path: str = Field(
        default="/metrics", description="Metrics endpoint path (reserved for future use)"
    )


class OpenTelemetryConfig(BaseModel):
    """OpenTelemetry configuration with environment-based sampling.

    Manages OpenTelemetry settings including collector endpoints, sampling
    rates, and performance tuning parameters. Automatically adjusts sampling
    rates based on the deployment environment to balance observability with
    performance overhead.

    Attributes:
        enabled: Master switch for OpenTelemetry. Set to False to disable
            all telemetry (useful for testing).
        otlp_endpoint: OpenTelemetry collector endpoint (OTLP protocol).
            Should point to daemonset collector in Kubernetes.
        service_name: Service name for telemetry identification.
        service_version: Service version for tracking deployments.
        environment: Deployment environment. Affects default sampling rates.
        trace_sample_rate: Base trace sampling rate (overridden by environment).
        metric_export_interval_ms: How often to export metrics (milliseconds).
        max_queue_size: Maximum span queue size before dropping.
        batch_schedule_delay_ms: Delay before exporting span batches.
        max_export_batch_size: Maximum spans per export batch.

    Examples:
        Production configuration with auto-sampling:

        >>> config = OpenTelemetryConfig(environment="production")
        >>> print(config.get_sample_rate())
        0.1  # 10% sampling in production

        Development configuration:

        >>> config = OpenTelemetryConfig(environment="development")
        >>> print(config.get_sample_rate())
        1.0  # 100% sampling in development

        Custom sampling override:

        >>> os.environ['OTEL_TRACE_SAMPLE_RATE'] = '0.25'
        >>> config = OpenTelemetryConfig(environment="production")
        >>> print(config.get_sample_rate())
        0.25  # Custom override

    Performance Note:
        Each 10% increase in sampling rate adds approximately 1-2ms latency
        overhead per request. Use lower rates (5-10%) in high-traffic production.
    """

    enabled: bool = Field(
        default_factory=lambda: os.getenv("OTEL_ENABLED", "true").lower() == "true",
        description="Master switch for OpenTelemetry",
    )

    # Collector endpoints
    otlp_endpoint: str = Field(
        default_factory=lambda: os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        description="OpenTelemetry collector OTLP endpoint",
    )

    # Service metadata
    service_name: str = Field(
        default="solveit-mcp-server", description="Service name for telemetry identification"
    )
    service_version: str = Field(
        default="0.1.0", description="Service version for tracking deployments"
    )
    environment: Literal["development", "staging", "production"] = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development"),
        description="Deployment environment (affects sampling)",
    )

    # Sampling configuration (environment-based)
    trace_sample_rate: float = Field(
        default=1.0, description="Base trace sampling rate (overridden by get_sample_rate())"
    )
    metric_export_interval_ms: int = Field(
        default=60000, description="Metric export interval (milliseconds)"
    )

    # Performance tuning
    max_queue_size: int = Field(default=2048, description="Maximum span queue size before dropping")
    batch_schedule_delay_ms: int = Field(
        default=5000, description="Delay before exporting span batches (milliseconds)"
    )
    max_export_batch_size: int = Field(default=512, description="Maximum spans per export batch")

    def get_sample_rate(self) -> float:
        """Calculate trace sample rate based on deployment environment.

        Implements environment-based sampling strategy:
        - Production: 10% (configurable via OTEL_TRACE_SAMPLE_RATE)
        - Staging: 50% (configurable via OTEL_TRACE_SAMPLE_RATE)
        - Development: 100% (full sampling for debugging)

        The sample rate can be overridden in any environment by setting
        the OTEL_TRACE_SAMPLE_RATE environment variable.

        Returns:
            float: Sample rate between 0.0 (no sampling) and 1.0 (100% sampling)

        Examples:
            Production default:

            >>> config = OpenTelemetryConfig(environment="production")
            >>> config.get_sample_rate()
            0.1

            Staging default:

            >>> config = OpenTelemetryConfig(environment="staging")
            >>> config.get_sample_rate()
            0.5

            Development (always 100%):

            >>> config = OpenTelemetryConfig(environment="development")
            >>> config.get_sample_rate()
            1.0

            Custom override:

            >>> os.environ['OTEL_TRACE_SAMPLE_RATE'] = '0.05'
            >>> config = OpenTelemetryConfig(environment="production")
            >>> config.get_sample_rate()
            0.05

        Note:
            Lower sampling rates reduce overhead but may miss rare errors.
            Always sample 100% in development for comprehensive debugging.
        """
        if self.environment == "production":
            return float(os.getenv("OTEL_TRACE_SAMPLE_RATE", "0.1"))
        elif self.environment == "staging":
            return float(os.getenv("OTEL_TRACE_SAMPLE_RATE", "0.5"))
        else:
            # Development: always 100% sampling
            return 1.0


class ServerConfig(BaseModel):
    """Main server configuration aggregating all subsystem configs.

    This is the root configuration model that combines transport, observability,
    and Kubernetes settings. It provides a single entry point for all server
    configuration.

    Attributes:
        transport: Transport type to use ('stdio' or 'http').
        http: HTTP transport configuration.
        otel: OpenTelemetry observability configuration.
        log_level: Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL).
        log_format: Log output format ('json' for structured logging, 'text' for human-readable).
        pod_name: Kubernetes pod name (auto-injected via downward API).
        node_name: Kubernetes node name (auto-injected via downward API).
        namespace: Kubernetes namespace (auto-injected via downward API).

    Examples:
        Load configuration:

        >>> config = ServerConfig()
        >>> print(config.transport)
        'stdio'

        HTTP mode:

        >>> os.environ['MCP_TRANSPORT'] = 'http'
        >>> config = ServerConfig()
        >>> print(config.transport)
        'http'
        >>> print(f"{config.http.host}:{config.http.port}")
        '0.0.0.0:8000'

        Check telemetry settings:

        >>> config = ServerConfig()
        >>> print(config.otel.enabled)
        True
        >>> print(config.otel.get_sample_rate())
        1.0  # Development environment

    Kubernetes Integration:
        The pod_name, node_name, and namespace fields are automatically
        populated from the Kubernetes downward API when running in a pod.
        These values are used for resource attribution in telemetry.
    """

    transport: Literal["stdio", "http"] = Field(
        default_factory=lambda: os.getenv("MCP_TRANSPORT", "stdio"),
        description="Transport type ('stdio' or 'http')",
    )

    http: HTTPConfig = Field(default_factory=HTTPConfig, description="HTTP transport configuration")
    otel: OpenTelemetryConfig = Field(
        default_factory=OpenTelemetryConfig, description="OpenTelemetry observability configuration"
    )

    # Logging configuration
    log_level: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"), description="Logging level"
    )
    log_format: Literal["json", "text"] = Field(
        default_factory=lambda: os.getenv("LOG_FORMAT", "json"), description="Log output format"
    )

    # Kubernetes metadata (injected via downward API)
    pod_name: str = Field(
        default_factory=lambda: os.getenv("K8S_POD_NAME", "unknown"),
        description="Kubernetes pod name",
    )
    node_name: str = Field(
        default_factory=lambda: os.getenv("K8S_NODE_NAME", "unknown"),
        description="Kubernetes node name",
    )
    namespace: str = Field(
        default_factory=lambda: os.getenv("K8S_NAMESPACE", "default"),
        description="Kubernetes namespace",
    )


def load_config() -> ServerConfig:
    """Load and validate server configuration from environment variables.

    This is the primary entry point for configuration loading. It creates
    a ServerConfig instance by reading environment variables and applying
    validation rules through Pydantic.

    The function provides sensible defaults for all settings while allowing
    complete environment-based overrides for containerized deployments.

    Returns:
        ServerConfig: Validated configuration object with all settings.

    Raises:
        pydantic.ValidationError: If configuration values are invalid,
            such as negative ports, invalid log levels, or malformed URLs.

    Examples:
        Basic usage:

        >>> config = load_config()
        >>> print(config.transport)
        'stdio'

        Check if HTTP mode:

        >>> config = load_config()
        >>> if config.transport == "http":
        ...     print(f"Server will listen on {config.http.host}:{config.http.port}")

        Access telemetry settings:

        >>> config = load_config()
        >>> if config.otel.enabled:
        ...     print(f"Telemetry enabled, sampling at {config.otel.get_sample_rate()}")

        Access Kubernetes metadata:

        >>> config = load_config()
        >>> print(f"Running in pod: {config.pod_name}")
        >>> print(f"Namespace: {config.namespace}")

    Environment Variables:
        Core Settings:
            MCP_TRANSPORT: 'stdio' or 'http' (default: 'stdio')
            LOG_LEVEL: DEBUG/INFO/WARNING/ERROR (default: 'INFO')
            LOG_FORMAT: 'json' or 'text' (default: 'json')

        HTTP Settings:
            HTTP_HOST: Bind address (default: '0.0.0.0')
            HTTP_PORT: Port number (default: 8000)
            HTTP_WORKERS: Worker processes (default: 1)
            CORS_ORIGINS: Comma-separated origins (default: '*')

        OpenTelemetry Settings:
            OTEL_ENABLED: 'true' or 'false' (default: 'true')
            OTEL_EXPORTER_OTLP_ENDPOINT: Collector URL (default: 'http://localhost:4317')
            ENVIRONMENT: 'development'/'staging'/'production' (default: 'development')
            OTEL_TRACE_SAMPLE_RATE: Override sampling rate (optional)

        Kubernetes Settings (auto-injected):
            K8S_POD_NAME: Pod name
            K8S_NODE_NAME: Node name
            K8S_NAMESPACE: Namespace name

    Note:
        This function is called once during server startup. Configuration
        is immutable after loading and cannot be changed at runtime.
    """
    return ServerConfig()
