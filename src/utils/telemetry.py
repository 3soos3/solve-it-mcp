"""OpenTelemetry initialization and lifecycle management.

This module provides comprehensive OpenTelemetry configuration and lifecycle
management for the SOLVE-IT MCP Server, including:

- Trace provider setup with environment-based sampling
- Metrics provider configuration with periodic export
- OTLP exporter initialization for collector communication
- Auto-instrumentation of common async libraries
- Resource attribute management for service identification

The telemetry manager implements graceful degradation when OpenTelemetry
dependencies are not available, ensuring the server can run without observability
if needed (e.g., minimal testing environments).

Typical usage:
    >>> from config import load_config
    >>> from utils.telemetry import TelemetryManager
    >>> 
    >>> config = load_config()
    >>> manager = TelemetryManager(config.otel)
    >>> tracer, meter = manager.configure()
    >>> 
    >>> # Use tracer for custom spans
    >>> with tracer.start_as_current_span("my_operation") as span:
    ...     span.set_attribute("key", "value")
    ...     # ... operation code ...

Environment-Based Sampling:
    The telemetry manager automatically adjusts sampling rates based on
    the deployment environment:
    - Development: 100% sampling (full observability)
    - Staging: 50% sampling (balanced)
    - Production: 10% sampling (low overhead)

Integration:
    Works with OpenTelemetry Collector (DaemonSet + Gateway architecture)
    to export telemetry data to multiple backends:
    - SignNoz for traces and logs
    - Prometheus for metrics
    - Grafana for visualization
"""

from typing import Optional, Tuple
import logging

# Conditional imports for graceful degradation
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
    from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatioBased
    
    # Auto-instrumentation imports
    from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        HTTPX_INSTRUMENTATION_AVAILABLE = True
    except ImportError:
        HTTPX_INSTRUMENTATION_AVAILABLE = False
    
    try:
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
        LOGGING_INSTRUMENTATION_AVAILABLE = True
    except ImportError:
        LOGGING_INSTRUMENTATION_AVAILABLE = False
    
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None
    metrics = None

# Import configuration (always available)
from config import OpenTelemetryConfig


# Module-level logger
logger = logging.getLogger(__name__)


class TelemetryManager:
    """Manages OpenTelemetry configuration and lifecycle.
    
    This class handles the complete lifecycle of OpenTelemetry including:
    - Trace provider setup with environment-based sampling
    - Metrics provider configuration
    - OTLP exporter initialization
    - Auto-instrumentation of common libraries
    - Resource attribute management
    
    The manager implements graceful degradation when OpenTelemetry is not
    available, returning no-op tracer and meter instances that can be safely
    used without actually recording telemetry.
    
    Attributes:
        config: OpenTelemetry configuration object
        tracer: OpenTelemetry tracer instance (None until configured)
        meter: OpenTelemetry meter instance (None until configured)
    
    Examples:
        Basic configuration:
        
        >>> from config import OpenTelemetryConfig
        >>> config = OpenTelemetryConfig(
        ...     enabled=True,
        ...     environment="production",
        ...     otlp_endpoint="http://otel-collector:4317"
        ... )
        >>> manager = TelemetryManager(config)
        >>> tracer, meter = manager.configure()
        
        Using the tracer:
        
        >>> with tracer.start_as_current_span("database_query") as span:
        ...     span.set_attribute("db.table", "techniques")
        ...     result = execute_query()
        ...     span.set_attribute("db.rows", len(result))
        
        Using the meter:
        
        >>> counter = meter.create_counter("requests.count")
        >>> counter.add(1, {"endpoint": "/search"})
        
        Disabling telemetry:
        
        >>> config = OpenTelemetryConfig(enabled=False)
        >>> manager = TelemetryManager(config)
        >>> tracer, meter = manager.configure()
        >>> # tracer and meter are no-op instances
    
    Note:
        This class should be instantiated once during application startup.
        Multiple instances will create multiple global providers, which
        may cause unexpected behavior.
    """
    
    def __init__(self, config: OpenTelemetryConfig):
        """Initialize telemetry manager with configuration.
        
        Args:
            config: OpenTelemetry configuration object containing
                endpoint, sampling, and performance settings
        
        Examples:
            >>> from config import load_config
            >>> config = load_config()
            >>> manager = TelemetryManager(config.otel)
        """
        self.config = config
        self.tracer: Optional[trace.Tracer] = None
        self.meter: Optional[metrics.Meter] = None
    
    def configure(self) -> Tuple[trace.Tracer, metrics.Meter]:
        """Configure OpenTelemetry with all providers and exporters.
        
        This method performs complete OpenTelemetry setup including:
        1. Resource creation with service metadata and Kubernetes attributes
        2. Trace provider with sampling and batch span processing
        3. Metrics provider with periodic OTLP export
        4. Auto-instrumentation for asyncio, httpx, and logging
        
        The configuration is environment-aware and automatically adjusts
        sampling rates based on the deployment environment (development,
        staging, or production).
        
        Returns:
            tuple[Tracer, Meter]: Configured tracer and meter instances.
                If OpenTelemetry is disabled or unavailable, returns
                no-op instances that can be safely used without recording.
        
        Raises:
            RuntimeError: If OpenTelemetry SDK initialization fails critically
                (rare - usually due to invalid endpoint URLs)
        
        Examples:
            Production configuration:
            
            >>> config = OpenTelemetryConfig(
            ...     environment="production",
            ...     otlp_endpoint="http://otel-collector:4317"
            ... )
            >>> manager = TelemetryManager(config)
            >>> tracer, meter = manager.configure()
            >>> print(f"Sample rate: {config.get_sample_rate()}")
            0.1  # 10% sampling in production
            
            Development configuration:
            
            >>> config = OpenTelemetryConfig(environment="development")
            >>> manager = TelemetryManager(config)
            >>> tracer, meter = manager.configure()
            >>> print(f"Sample rate: {config.get_sample_rate()}")
            1.0  # 100% sampling in development
            
            With telemetry disabled:
            
            >>> config = OpenTelemetryConfig(enabled=False)
            >>> manager = TelemetryManager(config)
            >>> tracer, meter = manager.configure()
            >>> # Returns no-op instances - no telemetry recorded
        
        Note:
            This method should be called once during application startup.
            It configures global OpenTelemetry providers that affect all
            subsequent tracing and metrics operations.
        
        Performance:
            Configuration is fast (<50ms) and should not significantly
            impact startup time. The actual telemetry overhead depends
            on sampling rate and export batch settings.
        """
        if not OTEL_AVAILABLE:
            logger.warning(
                "OpenTelemetry SDK not available - telemetry disabled. "
                "Install opentelemetry-* packages to enable observability."
            )
            # Return no-op tracer and meter
            return self._get_noop_telemetry()
        
        if not self.config.enabled:
            logger.info("OpenTelemetry disabled by configuration")
            return self._get_noop_telemetry()
        
        logger.info(
            f"Configuring OpenTelemetry for {self.config.environment} environment "
            f"with {self.config.get_sample_rate() * 100}% sampling"
        )
        
        try:
            # Create resource with service metadata
            resource = self._create_resource()
            
            # Configure tracing
            self._configure_tracing(resource)
            logger.debug("Trace provider configured")
            
            # Configure metrics
            self._configure_metrics(resource)
            logger.debug("Metrics provider configured")
            
            # Enable auto-instrumentation
            self._configure_auto_instrumentation()
            logger.debug("Auto-instrumentation enabled")
            
            # Get configured tracer and meter
            self.tracer = trace.get_tracer(__name__)
            self.meter = metrics.get_meter(__name__)
            
            logger.info(
                f"OpenTelemetry configured successfully: "
                f"endpoint={self.config.otlp_endpoint}, "
                f"service={self.config.service_name}"
            )
            
            return self.tracer, self.meter
            
        except Exception as e:
            logger.error(
                f"Failed to configure OpenTelemetry: {e}. "
                f"Falling back to no-op telemetry.",
                exc_info=True
            )
            return self._get_noop_telemetry()
    
    def _create_resource(self) -> Resource:
        """Create OpenTelemetry resource with service and environment metadata.
        
        The resource contains attributes that identify the service across
        all telemetry signals (traces, metrics, logs). These attributes
        appear in observability backends for filtering and grouping.
        
        Returns:
            Resource: OpenTelemetry resource with service metadata
        
        Resource Attributes:
            - service.name: Service identifier
            - service.version: Deployment version
            - deployment.environment: dev/staging/production
            - telemetry.sdk.language: Always "python"
            - telemetry.sdk.name: Always "opentelemetry"
        
        Examples:
            >>> resource = manager._create_resource()
            >>> attrs = resource.attributes
            >>> print(attrs[SERVICE_NAME])
            'solveit-mcp-server'
        
        Note:
            This is an internal method called by configure().
            Additional Kubernetes attributes (pod name, namespace, etc.)
            are added by the k8sattributes processor in the OTel Collector.
        """
        return Resource.create({
            SERVICE_NAME: self.config.service_name,
            SERVICE_VERSION: self.config.service_version,
            "deployment.environment": self.config.environment,
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry",
        })
    
    def _configure_tracing(self, resource: Resource) -> None:
        """Configure trace provider with sampling and OTLP export.
        
        Sets up the global trace provider with:
        - Parent-based trace ID ratio sampling (respects upstream decisions)
        - Batch span processor for efficient export
        - OTLP gRPC exporter to collector
        - Performance-optimized batch settings
        
        Args:
            resource: OpenTelemetry resource with service metadata
        
        Sampling Strategy:
            Uses ParentBasedTraceIdRatioBased sampler which:
            - Respects sampling decisions from upstream services
            - Samples new traces based on configured rate
            - Ensures complete traces (all spans in sampled traces)
        
        Batch Processing:
            Spans are batched before export for efficiency:
            - Queue size: 2048 spans (configurable)
            - Schedule delay: 5000ms (export every 5 seconds)
            - Batch size: 512 spans per export
            - Timeout: 30 seconds
        
        Examples:
            >>> resource = manager._create_resource()
            >>> manager._configure_tracing(resource)
            >>> # Global trace provider is now configured
        
        Note:
            This is an internal method called by configure().
            The sampling rate is determined by environment configuration
            via config.get_sample_rate().
        
        Performance:
            Batch processing significantly reduces export overhead.
            With default settings, export happens at most every 5 seconds
            or when 512 spans accumulate, whichever comes first.
        """
        # Environment-based sampling
        sample_rate = self.config.get_sample_rate()
        sampler = ParentBasedTraceIdRatioBased(sample_rate)
        
        # Create trace provider
        provider = TracerProvider(
            resource=resource,
            sampler=sampler
        )
        
        # OTLP exporter configuration
        otlp_exporter = OTLPSpanExporter(
            endpoint=self.config.otlp_endpoint,
            insecure=True  # Use TLS in production by setting to False
        )
        
        # Batch processor for performance
        batch_processor = BatchSpanProcessor(
            otlp_exporter,
            max_queue_size=self.config.max_queue_size,
            schedule_delay_millis=self.config.batch_schedule_delay_ms,
            max_export_batch_size=self.config.max_export_batch_size,
            export_timeout_millis=30000,  # 30 second timeout
        )
        
        provider.add_span_processor(batch_processor)
        trace.set_tracer_provider(provider)
        
        logger.debug(
            f"Trace provider configured: sample_rate={sample_rate}, "
            f"batch_size={self.config.max_export_batch_size}"
        )
    
    def _configure_metrics(self, resource: Resource) -> None:
        """Configure metrics provider with periodic OTLP export.
        
        Sets up the global metrics provider with:
        - OTLP metric exporter (gRPC)
        - Periodic export reader (default: 60 second interval)
        - Resource attributes for service identification
        
        Args:
            resource: OpenTelemetry resource with service metadata
        
        Export Strategy:
            Metrics are exported periodically (not batched like traces):
            - Default interval: 60 seconds
            - Configurable via metric_export_interval_ms
            - All accumulated metrics sent each interval
        
        Examples:
            >>> resource = manager._create_resource()
            >>> manager._configure_metrics(resource)
            >>> # Global meter provider is now configured
        
        Note:
            This is an internal method called by configure().
            Export interval is configurable via metric_export_interval_ms
            in the OpenTelemetryConfig (default: 60000ms = 1 minute).
        
        Performance:
            Metric export is lightweight compared to traces. The 60-second
            interval balances freshness with export overhead. For high-frequency
            dashboards, reduce to 15-30 seconds. For resource conservation,
            increase to 120 seconds.
        """
        # OTLP metric exporter
        otlp_exporter = OTLPMetricExporter(
            endpoint=self.config.otlp_endpoint,
            insecure=True  # Use TLS in production
        )
        
        # Periodic export reader
        metric_reader = PeriodicExportingMetricReader(
            otlp_exporter,
            export_interval_millis=self.config.metric_export_interval_ms
        )
        
        # Create meter provider
        provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader]
        )
        
        metrics.set_meter_provider(provider)
        
        logger.debug(
            f"Metrics provider configured: "
            f"interval={self.config.metric_export_interval_ms}ms"
        )
    
    def _configure_auto_instrumentation(self) -> None:
        """Enable auto-instrumentation for common async libraries.
        
        Instruments the following libraries automatically:
        - asyncio: Traces async tasks and coroutines
        - httpx: Traces HTTP client requests (if available)
        - logging: Correlates logs with trace context (if available)
        
        This provides automatic observability for dependency operations
        without requiring manual instrumentation code in the application.
        
        Auto-instrumentation creates spans automatically for:
        - AsyncIO task creation and execution
        - HTTPX HTTP requests (method, URL, status code)
        - Log records (adds trace context to log metadata)
        
        Examples:
            >>> manager._configure_auto_instrumentation()
            >>> 
            >>> # Now asyncio tasks are automatically traced
            >>> async def my_task():
            ...     await asyncio.sleep(1)  # Automatically traced
            >>> 
            >>> # HTTP requests are automatically traced
            >>> import httpx
            >>> response = await httpx.get("https://api.example.com")
            >>> # Span created with HTTP method, URL, status code
            >>> 
            >>> # Logs include trace context
            >>> logger.info("Event occurred")
            >>> # Log record includes trace_id and span_id
        
        Note:
            This is an internal method called by configure().
            Auto-instrumentation has minimal overhead (~1-2ms) and is
            safe to enable in production environments.
        
        Graceful Degradation:
            If specific instrumentation packages are not available,
            they are skipped with a debug log. The core asyncio
            instrumentation is always enabled if OpenTelemetry is available.
        """
        # AsyncIO instrumentation (always available with OpenTelemetry)
        try:
            AsyncioInstrumentor().instrument()
            logger.debug("AsyncIO auto-instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to enable AsyncIO instrumentation: {e}")
        
        # HTTPX instrumentation (optional)
        if HTTPX_INSTRUMENTATION_AVAILABLE:
            try:
                HTTPXClientInstrumentor().instrument()
                logger.debug("HTTPX auto-instrumentation enabled")
            except Exception as e:
                logger.warning(f"Failed to enable HTTPX instrumentation: {e}")
        else:
            logger.debug("HTTPX instrumentation not available (package not installed)")
        
        # Logging instrumentation (optional)
        if LOGGING_INSTRUMENTATION_AVAILABLE:
            try:
                LoggingInstrumentor().instrument(set_logging_format=True)
                logger.debug("Logging auto-instrumentation enabled")
            except Exception as e:
                logger.warning(f"Failed to enable logging instrumentation: {e}")
        else:
            logger.debug("Logging instrumentation not available (package not installed)")
    
    def _get_noop_telemetry(self) -> Tuple[trace.Tracer, metrics.Meter]:
        """Get no-op tracer and meter instances.
        
        Returns no-op (no-operation) tracer and meter instances that
        implement the OpenTelemetry API but don't actually record any
        telemetry. This enables the application to run without
        OpenTelemetry dependencies.
        
        Returns:
            tuple[Tracer, Meter]: No-op tracer and meter instances
        
        Examples:
            >>> tracer, meter = manager._get_noop_telemetry()
            >>> # These instances can be used safely but don't record
            >>> with tracer.start_as_current_span("operation"):
            ...     pass  # No span is actually created
        
        Note:
            This method is called when OpenTelemetry is disabled or
            unavailable. The returned instances follow the OpenTelemetry
            API but are optimized to have near-zero overhead.
        """
        if OTEL_AVAILABLE:
            return trace.get_tracer(__name__), metrics.get_meter(__name__)
        else:
            # Create minimal no-op implementations
            class NoOpTracer:
                def start_as_current_span(self, name, **kwargs):
                    from contextlib import nullcontext
                    return nullcontext()
            
            class NoOpMeter:
                def create_counter(self, name, **kwargs):
                    class NoOpCounter:
                        def add(self, amount, attributes=None):
                            pass
                    return NoOpCounter()
                
                def create_histogram(self, name, **kwargs):
                    class NoOpHistogram:
                        def record(self, amount, attributes=None):
                            pass
                    return NoOpHistogram()
                
                def create_up_down_counter(self, name, **kwargs):
                    class NoOpUpDownCounter:
                        def add(self, amount, attributes=None):
                            pass
                    return NoOpUpDownCounter()
            
            return NoOpTracer(), NoOpMeter()
