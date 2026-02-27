"""MCP-specific metrics collection using OpenTelemetry.

This module provides comprehensive metrics collection for monitoring MCP server
performance, errors, and resource usage. All metrics follow OpenTelemetry
semantic conventions and include appropriate dimensional attributes.

Metrics Categories:
1. Request Metrics: Tool invocation counts, error rates
2. Performance Metrics: Latency histograms, throughput, data sizes
3. Security Metrics: Violation counts, rate limit hits
4. Resource Metrics: CPU usage, memory usage, file descriptors

The metrics are exported via OpenTelemetry to Prometheus (via OTel Collector
Gateway) and can be visualized in Grafana dashboards.

Typical usage:
    >>> from opentelemetry import metrics
    >>> from utils.metrics import MCPMetrics
    >>>
    >>> meter = metrics.get_meter(__name__)
    >>> mcp_metrics = MCPMetrics(meter)
    >>>
    >>> # Record a successful tool invocation
    >>> mcp_metrics.record_tool_invocation(
    ...     tool_name="search",
    ...     duration_ms=45.2,
    ...     input_size=256,
    ...     output_size=1024
    ... )

Integration:
    Works with OpenTelemetry Collector to export metrics to:
    - Prometheus (via prometheus exporter in OTel Collector)
    - SignNoz (via OTLP exporter)
    - Grafana (via Prometheus data source)
"""

import logging
import os
from typing import Any

# Conditional import for graceful degradation
try:
    from opentelemetry import metrics

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    metrics = None

# Resource monitoring (optional)
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


# Module-level logger
logger = logging.getLogger(__name__)


class MCPMetrics:
    """OpenTelemetry metrics for MCP server operations.

    This class provides a comprehensive metrics collection system for
    monitoring MCP server performance, errors, and resource usage.
    All metrics follow OpenTelemetry naming conventions.

    Metrics Naming Convention:
        All metrics are prefixed with "mcp." and follow the pattern:
        mcp.{category}.{metric_name}

        Categories:
        - tool: Tool invocation metrics
        - request: Request-level metrics
        - security: Security-related metrics
        - process: Process resource usage

    Attributes:
        meter: OpenTelemetry meter for creating metric instruments
        tool_invocations: Counter for total tool invocations
        tool_errors: Counter for tool errors
        tool_duration: Histogram for tool execution duration
        validation_duration: Histogram for parameter validation duration
        active_requests: UpDownCounter for active request count
        input_size: Histogram for request size in bytes
        output_size: Histogram for response size in bytes
        security_violations: Counter for security policy violations
        rate_limit_hits: Counter for rate limit hits

    Examples:
        Basic usage:

        >>> from opentelemetry import metrics
        >>> meter = metrics.get_meter(__name__)
        >>> mcp_metrics = MCPMetrics(meter)

        Record successful tool invocation:

        >>> mcp_metrics.record_tool_invocation(
        ...     tool_name="get_technique_details",
        ...     duration_ms=23.5,
        ...     input_size=128,
        ...     output_size=4096,
        ...     attributes={"technique_id": "T1001"}
        ... )

        Record error:

        >>> mcp_metrics.record_tool_invocation(
        ...     tool_name="search",
        ...     duration_ms=5.2,
        ...     input_size=256,
        ...     output_size=0,
        ...     error=True,
        ...     attributes={"error_type": "ValidationError"}
        ... )

        Track active requests:

        >>> mcp_metrics.active_requests.add(1, {"tool_name": "search"})
        >>> try:
        ...     # Process request
        ...     pass
        >>> finally:
        ...     mcp_metrics.active_requests.add(-1, {"tool_name": "search"})

        Record security violation:

        >>> mcp_metrics.security_violations.add(1, {
        ...     "violation_type": "input_too_large",
        ...     "tool_name": "search"
        ... })

    Grafana Dashboard Integration:
        These metrics are exported to Prometheus and can be queried:

        - Request rate: rate(mcp_tool_invocations_total[5m])
        - Error rate: rate(mcp_tool_errors_total[5m])
        - Latency p95: histogram_quantile(0.95, rate(mcp_tool_duration_bucket[5m]))
        - Active requests: mcp_requests_active

    Note:
        If OpenTelemetry is not available, the class creates no-op metric
        instruments that can be safely used without recording data.
    """

    def __init__(self, meter: metrics.Meter | None = None):
        """Initialize MCP metrics with OpenTelemetry meter.

        Args:
            meter: OpenTelemetry meter for creating metric instruments.
                If None, creates no-op instruments.

        Examples:
            With OpenTelemetry:

            >>> from opentelemetry import metrics
            >>> meter = metrics.get_meter(__name__)
            >>> mcp_metrics = MCPMetrics(meter)

            Without OpenTelemetry (no-op mode):

            >>> mcp_metrics = MCPMetrics(None)
            >>> # Metrics can be used but won't record
        """
        self.meter = meter

        # Initialize all metric instruments
        if meter is not None and OTEL_AVAILABLE:
            self._init_request_metrics()
            self._init_performance_metrics()
            self._init_security_metrics()
            self._init_resource_metrics()
        else:
            # Create no-op instruments
            self._init_noop_metrics()

    def _init_request_metrics(self) -> None:
        """Initialize request-related metrics instruments.

        Creates counters for:
        - Total tool invocations (with tool_name label)
        - Tool errors (with tool_name and error_type labels)
        - Active request count (up/down counter)

        These metrics enable monitoring of request rates, error rates,
        and concurrent request load.

        Prometheus Queries:
            Request rate per tool:
            ```promql
            rate(mcp_tool_invocations_total[5m])
            ```

            Error rate per tool:
            ```promql
            rate(mcp_tool_errors_total[5m])
            ```

            Active concurrent requests:
            ```promql
            mcp_requests_active
            ```

        Examples:
            >>> metrics._init_request_metrics()
            >>> # Instruments are now available:
            >>> metrics.tool_invocations.add(1, {"tool_name": "search"})
        """
        self.tool_invocations = self.meter.create_counter(
            name="mcp.tool.invocations", description="Total number of tool invocations", unit="1"
        )

        self.tool_errors = self.meter.create_counter(
            name="mcp.tool.errors", description="Total number of tool errors", unit="1"
        )

        self.active_requests = self.meter.create_up_down_counter(
            name="mcp.requests.active", description="Number of currently active requests", unit="1"
        )

        logger.debug("Request metrics initialized")

    def _init_performance_metrics(self) -> None:
        """Initialize performance-related metrics instruments.

        Creates histograms for:
        - Tool execution duration (milliseconds)
        - Parameter validation duration (milliseconds)
        - Request size (bytes)
        - Response size (bytes)

        Histograms enable percentile calculations (p50, p95, p99) for
        latency analysis and SLO monitoring. OpenTelemetry automatically
        creates buckets for efficient percentile queries.

        Prometheus Queries:
            P95 latency per tool:
            ```promql
            histogram_quantile(0.95,
              rate(mcp_tool_duration_bucket[5m]))
            ```

            P99 latency:
            ```promql
            histogram_quantile(0.99,
              rate(mcp_tool_duration_bucket[5m]))
            ```

            Average response size:
            ```promql
            rate(mcp_response_size_sum[5m]) /
            rate(mcp_response_size_count[5m])
            ```

        Examples:
            >>> metrics._init_performance_metrics()
            >>> # Record latency
            >>> metrics.tool_duration.record(45.2, {"tool_name": "search"})

        Note:
            Histogram buckets are automatically determined by OpenTelemetry
            to provide good percentile accuracy across typical latency ranges.
        """
        self.tool_duration = self.meter.create_histogram(
            name="mcp.tool.duration",
            description="Tool execution duration in milliseconds",
            unit="ms",
        )

        self.validation_duration = self.meter.create_histogram(
            name="mcp.tool.validation.duration",
            description="Parameter validation duration in milliseconds",
            unit="ms",
        )

        self.input_size = self.meter.create_histogram(
            name="mcp.request.size", description="Request size in bytes", unit="By"
        )

        self.output_size = self.meter.create_histogram(
            name="mcp.response.size", description="Response size in bytes", unit="By"
        )

        logger.debug("Performance metrics initialized")

    def _init_security_metrics(self) -> None:
        """Initialize security-related metrics instruments.

        Creates counters for:
        - Security policy violations (with violation_type label)
        - Rate limit hits (with tool_name label)

        These metrics enable security monitoring and alerting on
        potential abuse or misconfigurations.

        Prometheus Queries:
            Security violations by type:
            ```promql
            rate(mcp_security_violations_total[5m])
            ```

            Rate limit alerts:
            ```promql
            rate(mcp_ratelimit_hits_total[1m]) > 10
            ```

        Grafana Alerts:
            Set up alerts for:
            - High security violation rate (>1/min)
            - Repeated rate limit hits from same source
            - Unusual spike in violations

        Examples:
            >>> metrics._init_security_metrics()
            >>> # Record violation
            >>> metrics.security_violations.add(1, {
            ...     "violation_type": "input_too_large",
            ...     "tool_name": "search"
            ... })
        """
        self.security_violations = self.meter.create_counter(
            name="mcp.security.violations", description="Security policy violations", unit="1"
        )

        self.rate_limit_hits = self.meter.create_counter(
            name="mcp.ratelimit.hits", description="Rate limit hits", unit="1"
        )

        logger.debug("Security metrics initialized")

    def _init_resource_metrics(self) -> None:
        """Initialize resource usage metrics with observable gauges.

        Creates observable gauges for:
        - CPU usage percentage (if psutil available)
        - Memory usage in megabytes (if psutil available)
        - Open file descriptors (if psutil available)

        Observable gauges are sampled automatically by OpenTelemetry at
        export time, providing current resource usage without application
        overhead between exports.

        Prometheus Queries:
            CPU usage by pod:
            ```promql
            mcp_process_cpu_usage{k8s_pod_name="mcp-server-abc"}
            ```

            Memory usage trend:
            ```promql
            mcp_process_memory_usage
            ```

            File descriptor usage:
            ```promql
            mcp_process_open_fds
            ```

        Kubernetes Integration:
            These metrics complement Kubernetes resource metrics:
            - Compare to pod resource limits
            - Identify memory leaks
            - Monitor CPU throttling

        Examples:
            >>> metrics._init_resource_metrics()
            >>> # Gauges are sampled automatically
            >>> # No manual recording needed

        Note:
            If psutil is not available, these metrics are not created.
            The application continues to function normally without
            resource monitoring.
        """
        if not PSUTIL_AVAILABLE:
            logger.debug("psutil not available - resource metrics disabled")
            return

        # CPU usage callback
        def get_cpu_usage(options):
            """Get current CPU usage percentage."""
            try:
                return [metrics.Observation(psutil.cpu_percent(interval=0.1))]
            except Exception as e:
                logger.warning(f"Failed to get CPU usage: {e}")
                return [metrics.Observation(0.0)]

        self.meter.create_observable_gauge(
            name="mcp.process.cpu.usage",
            callbacks=[get_cpu_usage],
            unit="%",
            description="CPU usage percentage",
        )

        # Memory usage callback
        def get_memory_usage(options):
            """Get current memory usage in megabytes."""
            try:
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                return [metrics.Observation(memory_mb)]
            except Exception as e:
                logger.warning(f"Failed to get memory usage: {e}")
                return [metrics.Observation(0.0)]

        self.meter.create_observable_gauge(
            name="mcp.process.memory.usage",
            callbacks=[get_memory_usage],
            unit="MiBy",
            description="Memory usage in megabytes",
        )

        # File descriptor count callback (Linux/Unix only)
        if hasattr(psutil.Process, "num_fds"):

            def get_open_fds(options):
                """Get count of open file descriptors."""
                try:
                    process = psutil.Process(os.getpid())
                    return [metrics.Observation(process.num_fds())]
                except Exception as e:
                    logger.warning(f"Failed to get file descriptors: {e}")
                    return [metrics.Observation(0.0)]

            self.meter.create_observable_gauge(
                name="mcp.process.open_fds",
                callbacks=[get_open_fds],
                unit="1",
                description="Number of open file descriptors",
            )

        logger.debug("Resource metrics initialized with psutil")

    def _init_noop_metrics(self) -> None:
        """Initialize no-op metric instruments.

        Creates no-op (no-operation) metric instruments that implement
        the metrics API but don't actually record any data. This enables
        the application to run without OpenTelemetry dependencies.

        Examples:
            >>> metrics._init_noop_metrics()
            >>> # Instruments can be used but don't record
            >>> metrics.tool_invocations.add(1)  # No-op
        """

        class NoOpCounter:
            def add(self, amount: float, attributes: dict[str, Any] | None = None) -> None:
                pass

        class NoOpHistogram:
            def record(self, amount: float, attributes: dict[str, Any] | None = None) -> None:
                pass

        class NoOpUpDownCounter:
            def add(self, amount: float, attributes: dict[str, Any] | None = None) -> None:
                pass

        self.tool_invocations = NoOpCounter()
        self.tool_errors = NoOpCounter()
        self.tool_duration = NoOpHistogram()
        self.validation_duration = NoOpHistogram()
        self.input_size = NoOpHistogram()
        self.output_size = NoOpHistogram()
        self.active_requests = NoOpUpDownCounter()
        self.security_violations = NoOpCounter()
        self.rate_limit_hits = NoOpCounter()

        logger.debug("No-op metrics initialized (OpenTelemetry not available)")

    def record_tool_invocation(
        self,
        tool_name: str,
        duration_ms: float,
        input_size: int,
        output_size: int,
        error: bool = False,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Record comprehensive metrics for a tool invocation.

        This method records multiple related metrics for a single tool
        invocation including counts, duration, and data sizes. It's the
        primary interface for tracking tool execution metrics.

        Metrics Recorded:
        - Tool invocation count (+1)
        - Tool duration (histogram)
        - Request size (histogram)
        - Response size (histogram)
        - Tool error count (+1 if error=True)

        Args:
            tool_name: Name of the invoked tool (e.g., "search", "get_technique_details")
            duration_ms: Execution duration in milliseconds
            input_size: Input data size in bytes
            output_size: Output data size in bytes
            error: Whether the invocation resulted in an error. Defaults to False.
            attributes: Additional metric attributes for filtering and grouping.
                Common attributes include correlation_id, technique_id, etc.

        Examples:
            Record successful tool invocation:

            >>> metrics.record_tool_invocation(
            ...     tool_name="get_technique_details",
            ...     duration_ms=23.5,
            ...     input_size=128,
            ...     output_size=4096,
            ...     attributes={"technique_id": "T1001", "correlation_id": "req_abc"}
            ... )

            Record error case:

            >>> metrics.record_tool_invocation(
            ...     tool_name="search",
            ...     duration_ms=5.2,
            ...     input_size=256,
            ...     output_size=0,
            ...     error=True,
            ...     attributes={"error_type": "ValidationError"}
            ... )

            With full context:

            >>> from utils.correlation import CorrelationContext
            >>> ctx = CorrelationContext.get_trace_context()
            >>> metrics.record_tool_invocation(
            ...     tool_name="search",
            ...     duration_ms=42.1,
            ...     input_size=512,
            ...     output_size=2048,
            ...     attributes=ctx
            ... )

        Grafana Dashboard:
            These metrics power the following dashboard panels:
            - Tool invocation rate: rate(mcp_tool_invocations_total[5m])
            - Error rate: rate(mcp_tool_errors_total[5m]) / rate(mcp_tool_invocations_total[5m])
            - Latency p95: histogram_quantile(0.95, rate(mcp_tool_duration_bucket[5m]))
            - Throughput: rate(mcp_response_size_sum[5m])

        Note:
            Attributes are merged with the tool_name and propagated to
            all recorded metrics. This enables filtering in Prometheus
            queries and Grafana dashboards (e.g., by correlation_id).
        """
        # Merge tool_name into attributes
        attrs = {"tool_name": tool_name}
        if attributes:
            attrs.update(attributes)

        # Record invocation count
        self.tool_invocations.add(1, attrs)

        # Record duration
        self.tool_duration.record(duration_ms, attrs)

        # Record sizes
        self.input_size.record(input_size, attrs)
        self.output_size.record(output_size, attrs)

        # Record error if applicable
        if error:
            self.tool_errors.add(1, attrs)
