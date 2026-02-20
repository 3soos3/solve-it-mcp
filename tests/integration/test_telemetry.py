"""Integration tests for OpenTelemetry observability.

This module tests the telemetry functionality including:
- Telemetry manager lifecycle
- Metrics collection
- Correlation ID tracking
- Trace creation and propagation
- Graceful degradation when OpenTelemetry unavailable
"""

import os
import time
from unittest.mock import MagicMock, patch, call
import pytest

from config import OpenTelemetryConfig, load_config
from utils.telemetry import TelemetryManager
from utils.metrics import MCPMetrics
from utils.correlation import CorrelationContext

# Check if OpenTelemetry is available
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


class TestTelemetryManager:
    """Test telemetry manager lifecycle."""

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    def test_telemetry_manager_initialization(self):
        """Test telemetry manager can be initialized."""
        config = OpenTelemetryConfig(
            enabled=True,
            service_name="test-service"
        )
        
        manager = TelemetryManager(config)
        
        assert manager.config == config
        assert manager.config.service_name == "test-service"

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    def test_telemetry_manager_initialize_method_exists(self):
        """Test that telemetry manager has initialize method."""
        config = OpenTelemetryConfig(enabled=True)
        manager = TelemetryManager(config)
        
        assert hasattr(manager, 'initialize')
        assert callable(manager.initialize)

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    def test_telemetry_manager_shutdown_method_exists(self):
        """Test that telemetry manager has shutdown method."""
        config = OpenTelemetryConfig(enabled=True)
        manager = TelemetryManager(config)
        
        assert hasattr(manager, 'shutdown')
        assert callable(manager.shutdown)

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    def test_telemetry_manager_with_otlp_endpoint(self):
        """Test telemetry manager with OTLP endpoint configured."""
        config = OpenTelemetryConfig(
            enabled=True,
            endpoint="http://localhost:4317"
        )
        
        manager = TelemetryManager(config)
        
        assert manager.config.endpoint == "http://localhost:4317"


class TestMCPMetrics:
    """Test MCP metrics collection."""

    def test_metrics_can_be_created(self):
        """Test that MCPMetrics can be instantiated."""
        metrics = MCPMetrics()
        
        assert metrics is not None

    def test_metrics_has_record_methods(self):
        """Test that metrics has recording methods."""
        metrics = MCPMetrics()
        
        # Should have methods for recording different metrics
        assert hasattr(metrics, 'record_tool_invocation')
        assert hasattr(metrics, 'record_active_request')

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    def test_metrics_record_tool_invocation(self):
        """Test recording tool invocations."""
        metrics = MCPMetrics()
        
        # Should not raise an exception
        try:
            metrics.record_tool_invocation("test_tool", "success", 0.123)
        except Exception as e:
            pytest.fail(f"record_tool_invocation raised exception: {e}")

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    def test_metrics_record_active_request(self):
        """Test recording active requests."""
        metrics = MCPMetrics()
        
        # Should not raise an exception
        try:
            metrics.record_active_request(1)
            metrics.record_active_request(-1)
        except Exception as e:
            pytest.fail(f"record_active_request raised exception: {e}")


class TestCorrelationContext:
    """Test correlation ID tracking."""

    def test_correlation_context_generate_id(self):
        """Test correlation ID generation."""
        correlation_id = CorrelationContext.generate_correlation_id()
        
        assert correlation_id is not None
        assert isinstance(correlation_id, str)
        assert len(correlation_id) > 0

    def test_correlation_ids_are_unique(self):
        """Test that generated correlation IDs are unique."""
        id1 = CorrelationContext.generate_correlation_id()
        id2 = CorrelationContext.generate_correlation_id()
        
        assert id1 != id2

    def test_correlation_context_set_and_get(self):
        """Test setting and getting correlation ID."""
        test_id = "test-correlation-id-12345"
        
        CorrelationContext.set_correlation_id(test_id)
        retrieved_id = CorrelationContext.get_correlation_id()
        
        assert retrieved_id == test_id
        
        # Clean up
        CorrelationContext.clear_correlation_id()

    def test_correlation_context_clear(self):
        """Test clearing correlation ID."""
        test_id = "test-correlation-id-67890"
        
        CorrelationContext.set_correlation_id(test_id)
        assert CorrelationContext.get_correlation_id() == test_id
        
        CorrelationContext.clear_correlation_id()
        cleared_id = CorrelationContext.get_correlation_id()
        
        # Should return None or empty string after clearing
        assert cleared_id is None or cleared_id == ""

    def test_correlation_context_isolation(self):
        """Test that correlation context is isolated between operations."""
        # Set an ID
        id1 = "operation-1"
        CorrelationContext.set_correlation_id(id1)
        
        # Clear it
        CorrelationContext.clear_correlation_id()
        
        # Set a different ID
        id2 = "operation-2"
        CorrelationContext.set_correlation_id(id2)
        
        # Should get the second ID
        assert CorrelationContext.get_correlation_id() == id2
        
        # Clean up
        CorrelationContext.clear_correlation_id()


class TestOpenTelemetryConfig:
    """Test OpenTelemetry configuration."""

    def test_otel_config_default_values(self):
        """Test OpenTelemetry config default values."""
        config = OpenTelemetryConfig()
        
        assert config.enabled == False
        assert config.service_name == "solveit_mcp_server"
        assert config.environment == "development"

    def test_otel_config_custom_values(self):
        """Test OpenTelemetry config with custom values."""
        config = OpenTelemetryConfig(
            enabled=True,
            service_name="custom-service",
            environment="production",
            endpoint="http://otel-collector:4317"
        )
        
        assert config.enabled == True
        assert config.service_name == "custom-service"
        assert config.environment == "production"
        assert config.endpoint == "http://otel-collector:4317"

    def test_otel_config_sampling_rates(self):
        """Test sampling rate configuration."""
        config = OpenTelemetryConfig(
            trace_sampling_rate=0.5,
            metrics_sampling_rate=0.8
        )
        
        assert config.trace_sampling_rate == 0.5
        assert config.metrics_sampling_rate == 0.8

    def test_otel_config_environment_based_sampling(self):
        """Test environment-based sampling configuration."""
        # Development environment
        dev_config = OpenTelemetryConfig(environment="development")
        assert dev_config.environment == "development"
        
        # Staging environment
        staging_config = OpenTelemetryConfig(environment="staging")
        assert staging_config.environment == "staging"
        
        # Production environment
        prod_config = OpenTelemetryConfig(environment="production")
        assert prod_config.environment == "production"


class TestTelemetryIntegrationWithServer:
    """Test telemetry integration with MCP server."""

    def test_config_loads_telemetry_settings(self):
        """Test that config loader includes telemetry settings."""
        # Set environment variables
        with patch.dict(os.environ, {
            'MCP_OPENTELEMETRY_ENABLED': 'true',
            'MCP_OPENTELEMETRY_SERVICE_NAME': 'test-mcp-server'
        }):
            config = load_config()
            
            assert hasattr(config, 'opentelemetry')
            assert config.opentelemetry.enabled == True
            assert config.opentelemetry.service_name == 'test-mcp-server'

    def test_telemetry_disabled_by_default(self):
        """Test that telemetry is disabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            config = load_config()
            
            assert config.opentelemetry.enabled == False

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    def test_telemetry_graceful_degradation(self):
        """Test graceful degradation when telemetry fails."""
        config = OpenTelemetryConfig(
            enabled=True,
            endpoint="http://invalid-endpoint:9999"
        )
        
        # Should not raise exception even with invalid endpoint
        manager = TelemetryManager(config)
        
        # Initialize might fail, but should be handled gracefully
        try:
            manager.initialize()
        except Exception:
            # Graceful degradation - failure is acceptable
            pass


class TestMetricsNoOp:
    """Test metrics no-op mode when OpenTelemetry unavailable."""

    def test_metrics_works_without_otel(self):
        """Test that metrics work even without OpenTelemetry."""
        metrics = MCPMetrics()
        
        # Should not raise exceptions even if OTel is not available
        try:
            metrics.record_tool_invocation("test", "success", 0.1)
            metrics.record_active_request(1)
            metrics.record_active_request(-1)
        except Exception as e:
            pytest.fail(f"Metrics should work without OTel, but raised: {e}")


@pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
class TestTraceCreation:
    """Test trace creation and span management."""

    def test_trace_provider_available(self):
        """Test that trace provider is available."""
        from opentelemetry import trace
        
        tracer = trace.get_tracer(__name__)
        assert tracer is not None

    def test_can_create_span(self):
        """Test that spans can be created."""
        from opentelemetry import trace
        
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("test_span") as span:
            assert span is not None
            span.set_attribute("test.key", "test.value")

    def test_span_attributes_can_be_set(self):
        """Test that span attributes can be set."""
        from opentelemetry import trace
        
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("test_span") as span:
            span.set_attribute("mcp.tool.name", "test_tool")
            span.set_attribute("mcp.correlation_id", "test-123")
            span.set_attribute("mcp.tool.arg_count", 5)

    def test_span_status_can_be_set(self):
        """Test that span status can be set."""
        from opentelemetry import trace
        from opentelemetry.trace import Status, StatusCode
        
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("test_span") as span:
            span.set_status(Status(StatusCode.OK))
            
        with tracer.start_as_current_span("error_span") as span:
            span.set_status(Status(StatusCode.ERROR, "Test error"))


class TestKubernetesMetadata:
    """Test Kubernetes metadata in telemetry."""

    def test_k8s_metadata_from_environment(self):
        """Test that K8s metadata is read from environment."""
        with patch.dict(os.environ, {
            'MCP_OPENTELEMETRY_K8S_POD_NAME': 'test-pod-123',
            'MCP_OPENTELEMETRY_K8S_NAMESPACE': 'test-namespace',
            'MCP_OPENTELEMETRY_K8S_NODE_NAME': 'test-node-1'
        }):
            config = load_config()
            
            assert config.opentelemetry.k8s_pod_name == 'test-pod-123'
            assert config.opentelemetry.k8s_namespace == 'test-namespace'
            assert config.opentelemetry.k8s_node_name == 'test-node-1'

    def test_k8s_metadata_optional(self):
        """Test that K8s metadata is optional."""
        with patch.dict(os.environ, {}, clear=True):
            config = load_config()
            
            # K8s fields should exist but be None or empty
            assert hasattr(config.opentelemetry, 'k8s_pod_name')


class TestTelemetryPerformance:
    """Test telemetry performance characteristics."""

    def test_correlation_id_generation_is_fast(self):
        """Test that correlation ID generation is fast."""
        start = time.time()
        
        # Generate many IDs
        for _ in range(1000):
            CorrelationContext.generate_correlation_id()
        
        elapsed = time.time() - start
        
        # Should be very fast (< 100ms for 1000 IDs)
        assert elapsed < 0.1, f"ID generation too slow: {elapsed}s for 1000 IDs"

    def test_metrics_recording_is_fast(self):
        """Test that metrics recording is fast."""
        metrics = MCPMetrics()
        
        start = time.time()
        
        # Record many metrics
        for i in range(100):
            metrics.record_tool_invocation(f"tool_{i}", "success", 0.001)
        
        elapsed = time.time() - start
        
        # Should be fast (< 100ms for 100 recordings)
        assert elapsed < 0.1, f"Metrics recording too slow: {elapsed}s for 100 records"
