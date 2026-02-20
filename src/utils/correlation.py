"""Correlation ID management and trace context propagation.

This module provides a context-aware correlation ID system that integrates
with OpenTelemetry distributed tracing. Correlation IDs enable request tracking
across log aggregation, metrics, and distributed traces.

The implementation uses Python's contextvars for async-safe context propagation
across task boundaries, ensuring correlation IDs persist through asyncio operations.

Key Features:
- Automatic correlation ID generation
- Integration with OpenTelemetry span attributes
- Async-safe context propagation
- Trace context extraction for structured logging

Typical usage:
    >>> from utils.correlation import CorrelationContext
    >>> 
    >>> # Generate and set correlation ID
    >>> cid = CorrelationContext.generate_id("tool")
    >>> CorrelationContext.set_correlation_id(cid)
    >>> 
    >>> # Later, in another function
    >>> current = CorrelationContext.get_correlation_id()
    >>> print(current)
    'tool_a1b2c3d4e5f6'
    >>> 
    >>> # Get full trace context for logging
    >>> ctx = CorrelationContext.get_trace_context()
    >>> logger.info("Processing", extra=ctx)

Integration with OpenTelemetry:
    The correlation context automatically adds correlation IDs to active
    OpenTelemetry spans, enabling correlation between logs, metrics, and traces
    in observability backends like SignNoz and Grafana.
"""

import contextvars
import uuid
from typing import Dict, Optional

# Conditional import for OpenTelemetry (graceful degradation if not available)
try:
    from opentelemetry import trace
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


# Context variable for async-safe correlation ID propagation
# This automatically handles propagation across asyncio task boundaries
correlation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'correlation_id',
    default=None
)


class CorrelationContext:
    """Manages correlation IDs and trace context propagation.
    
    This class provides a context-aware correlation ID system that integrates
    with OpenTelemetry distributed tracing. Correlation IDs enable request
    tracking across log aggregation, metrics, and distributed traces.
    
    The implementation uses Python's contextvars for async-safe context
    propagation across task boundaries.
    
    All methods are static as correlation IDs are stored in context variables
    rather than instance state.
    
    Examples:
        Basic usage:
        
        >>> # Generate and set correlation ID
        >>> cid = CorrelationContext.generate_id("tool")
        >>> CorrelationContext.set_correlation_id(cid)
        >>> 
        >>> # Retrieve in another function
        >>> current_cid = CorrelationContext.get_correlation_id()
        >>> print(current_cid)
        'tool_a1b2c3d4e5f6'
        
        Integration with structured logging:
        
        >>> ctx = CorrelationContext.get_trace_context()
        >>> logger.info("Processing request", extra=ctx)
        # Logs: {"message": "Processing request", "trace_id": "...", 
        #        "span_id": "...", "correlation_id": "tool_a1b2c3d4e5f6"}
        
        Async task propagation:
        
        >>> async def parent_task():
        ...     CorrelationContext.set_correlation_id("req_parent")
        ...     await child_task()
        >>> 
        >>> async def child_task():
        ...     # Correlation ID is automatically available
        ...     cid = CorrelationContext.get_correlation_id()
        ...     print(cid)  # 'req_parent'
    
    Note:
        Context variables are automatically isolated between concurrent
        asyncio tasks, preventing correlation ID leakage between requests.
    """
    
    @staticmethod
    def generate_id(prefix: str = "req") -> str:
        """Generate a unique correlation ID with optional prefix.
        
        Creates a correlation ID in the format: {prefix}_{12_hex_chars}
        The hex characters are derived from a UUID4 for global uniqueness.
        
        Args:
            prefix: Prefix for the correlation ID. Common prefixes:
                - "req": Generic request
                - "tool": Tool invocation
                - "http": HTTP request
                - "sse": SSE connection
                - "list": List tools request
        
        Returns:
            str: Unique correlation ID (e.g., "req_a1b2c3d4e5f6")
        
        Examples:
            Tool invocation:
            
            >>> cid = CorrelationContext.generate_id("tool")
            >>> print(cid)
            'tool_a1b2c3d4e5f6'
            >>> print(len(cid))
            17  # "tool_" (5 chars) + 12 hex chars
            
            HTTP request:
            
            >>> cid = CorrelationContext.generate_id("http")
            >>> print(cid.startswith("http_"))
            True
            
            Default prefix:
            
            >>> cid = CorrelationContext.generate_id()
            >>> print(cid.startswith("req_"))
            True
        
        Note:
            The 12-character hex suffix provides sufficient uniqueness for
            billions of requests while keeping IDs human-readable in logs.
        """
        return f"{prefix}_{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def set_correlation_id(correlation_id: str) -> None:
        """Set correlation ID in current async context and active span.
        
        Stores the correlation ID in:
        1. AsyncIO context variable (for propagation across async tasks)
        2. Current OpenTelemetry span attributes (if span is active)
        
        This dual storage enables correlation across:
        - Application logs (via context variable)
        - Distributed traces (via span attributes)
        - Metrics (via span context in metric attributes)
        
        Args:
            correlation_id: Correlation ID to set in current context
        
        Examples:
            Basic usage:
            
            >>> CorrelationContext.set_correlation_id("req_abc123")
            >>> # ID is now available in current context
            >>> current = CorrelationContext.get_correlation_id()
            >>> print(current)
            'req_abc123'
            
            Within an OpenTelemetry span:
            
            >>> from opentelemetry import trace
            >>> tracer = trace.get_tracer(__name__)
            >>> with tracer.start_as_current_span("operation") as span:
            ...     CorrelationContext.set_correlation_id("req_xyz")
            ...     # Correlation ID is now in span attributes
            ...     attrs = span.get_span_context()
            ...     # Can be queried in trace backend
            
            Async task creation:
            
            >>> async def handler():
            ...     CorrelationContext.set_correlation_id("req_main")
            ...     # Child tasks inherit this ID automatically
            ...     await process_request()
        
        Note:
            If called within an OpenTelemetry span, the correlation ID
            is automatically added as a span attribute named "correlation.id".
            This appears in trace backends like SignNoz and Jaeger.
        """
        # Set in context variable for async propagation
        correlation_id_var.set(correlation_id)
        
        # Also set in current OpenTelemetry span if available
        if OTEL_AVAILABLE:
            current_span = trace.get_current_span()
            if current_span and current_span.is_recording():
                current_span.set_attribute("correlation.id", correlation_id)
    
    @staticmethod
    def get_correlation_id() -> str:
        """Retrieve correlation ID from current async context.
        
        Gets the correlation ID from the context variable. If no correlation
        ID has been set in the current context, automatically generates a new
        one to ensure every operation has a correlation ID.
        
        Returns:
            str: Current correlation ID, or newly generated if none exists
        
        Examples:
            With existing correlation ID:
            
            >>> CorrelationContext.set_correlation_id("req_xyz789")
            >>> cid = CorrelationContext.get_correlation_id()
            >>> print(cid)
            'req_xyz789'
            
            Without existing correlation ID (auto-generates):
            
            >>> # In fresh context, no ID set
            >>> cid = CorrelationContext.get_correlation_id()
            >>> print(cid.startswith("req_"))
            True
            >>> print(len(cid))
            16  # "req_" + 12 hex chars
            
            In async tasks:
            
            >>> async def task():
            ...     # Inherits parent's correlation ID
            ...     cid = CorrelationContext.get_correlation_id()
            ...     logger.info("Task running", extra={"correlation_id": cid})
        
        Note:
            Auto-generation ensures every request has a correlation ID
            even if not explicitly set, preventing gaps in observability.
            The auto-generated ID uses the default "req_" prefix.
        """
        cid = correlation_id_var.get()
        if cid is None:
            # Auto-generate if not set
            cid = CorrelationContext.generate_id()
            CorrelationContext.set_correlation_id(cid)
        return cid
    
    @staticmethod
    def get_trace_context() -> Dict[str, str]:
        """Extract complete trace context for structured logging.
        
        Retrieves OpenTelemetry trace and span IDs along with the correlation
        ID, formatted for JSON logging and log aggregation systems like Loki,
        Elasticsearch, or CloudWatch.
        
        The trace context enables correlation between:
        - Application logs (via correlation_id)
        - Distributed traces (via trace_id and span_id)
        - Metrics (via trace context attributes)
        
        Returns:
            dict: Trace context dictionary with keys:
                - trace_id (str): OpenTelemetry trace ID (32 hex chars), or None
                - span_id (str): OpenTelemetry span ID (16 hex chars), or None
                - correlation_id (str): Correlation ID (always present)
        
        Examples:
            Basic usage:
            
            >>> ctx = CorrelationContext.get_trace_context()
            >>> print(ctx)
            {
                'trace_id': '1234567890abcdef1234567890abcdef',
                'span_id': '1234567890abcdef',
                'correlation_id': 'req_a1b2c3d4e5f6'
            }
            
            Structured logging:
            
            >>> import logging
            >>> logger = logging.getLogger(__name__)
            >>> ctx = CorrelationContext.get_trace_context()
            >>> logger.info("Request processed", extra=ctx)
            # JSON log: {"message": "Request processed", 
            #           "trace_id": "...", "span_id": "...", 
            #           "correlation_id": "req_..."}
            
            Without active span:
            
            >>> # Outside of a span context
            >>> ctx = CorrelationContext.get_trace_context()
            >>> print(ctx)
            {'correlation_id': 'req_a1b2c3d4e5f6'}
            # trace_id and span_id are omitted
            
            Grafana Loki integration:
            
            >>> ctx = CorrelationContext.get_trace_context()
            >>> logger.info("Event occurred", extra=ctx)
            # In Grafana, you can jump from logs to traces using trace_id
        
        Note:
            When OpenTelemetry is not available or no span is active,
            only the correlation_id is returned. This ensures the function
            always succeeds and provides at least basic correlation.
        
        Integration:
            The trace_id and span_id can be used in log aggregation systems
            to link logs directly to distributed traces, enabling seamless
            navigation from log entries to their associated trace spans.
        """
        result: Dict[str, str] = {}
        
        # Always include correlation ID
        result["correlation_id"] = CorrelationContext.get_correlation_id()
        
        # Add trace context if OpenTelemetry is available
        if OTEL_AVAILABLE:
            span = trace.get_current_span()
            if span and span.is_recording():
                ctx = span.get_span_context()
                if ctx.is_valid:
                    # Format trace IDs as hex strings for log aggregation
                    result["trace_id"] = format(ctx.trace_id, '032x')
                    result["span_id"] = format(ctx.span_id, '016x')
        
        return result
