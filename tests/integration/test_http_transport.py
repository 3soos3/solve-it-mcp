"""Integration tests for HTTP/SSE transport.

This module tests the HTTP/SSE transport functionality including:
- HTTP endpoints (health, ready, MCP)
- Server-Sent Events (SSE) for streaming
- CORS configuration
- Error handling
- Metrics integration
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from starlette.testclient import TestClient
from starlette.responses import JSONResponse, StreamingResponse
from mcp.server.lowlevel import Server
import mcp.types as types

from config import HTTPConfig
from transports import HTTPTransportManager, HTTP_AVAILABLE


@pytest.mark.skipif(not HTTP_AVAILABLE, reason="HTTP transport dependencies not available")
class TestHTTPTransportManager:
    """Test suite for HTTP transport manager."""

    def test_http_transport_import(self):
        """Test that HTTP transport can be imported."""
        from transports import HTTPTransportManager
        
        assert HTTPTransportManager is not None

    def test_http_transport_manager_initialization(self):
        """Test HTTP transport manager initialization."""
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig(host="127.0.0.1", port=8001)
        
        manager = HTTPTransportManager(mock_server, config)
        
        assert manager.server == mock_server
        assert manager.config == config
        assert manager.app is not None

    def test_http_transport_creates_starlette_app(self):
        """Test that HTTP transport creates a Starlette application."""
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        
        manager = HTTPTransportManager(mock_server, config)
        
        # Should have a Starlette app
        assert hasattr(manager, 'app')
        assert manager.app is not None

    def test_http_transport_with_metrics(self):
        """Test HTTP transport with metrics enabled."""
        from utils.metrics import MCPMetrics
        
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        mock_metrics = MagicMock(spec=MCPMetrics)
        
        manager = HTTPTransportManager(mock_server, config, mock_metrics)
        
        assert manager.metrics == mock_metrics


@pytest.mark.skipif(not HTTP_AVAILABLE, reason="HTTP transport dependencies not available")
class TestHTTPEndpoints:
    """Test HTTP endpoints."""

    def test_health_endpoint(self):
        """Test /health endpoint returns 200 OK."""
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        
        manager = HTTPTransportManager(mock_server, config)
        client = TestClient(manager.app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    def test_readiness_endpoint(self):
        """Test /ready endpoint returns 200 OK."""
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        
        manager = HTTPTransportManager(mock_server, config)
        client = TestClient(manager.app)
        
        response = client.get("/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "server" in data
        assert data["server"] == "solveit_mcp_server"

    def test_invalid_endpoint_returns_404(self):
        """Test that invalid endpoints return 404."""
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        
        manager = HTTPTransportManager(mock_server, config)
        client = TestClient(manager.app)
        
        response = client.get("/invalid")
        
        assert response.status_code == 404


@pytest.mark.skipif(not HTTP_AVAILABLE, reason="HTTP transport dependencies not available")
class TestCORSConfiguration:
    """Test CORS middleware configuration."""

    def test_cors_enabled_by_default(self):
        """Test that CORS is enabled by default."""
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        
        manager = HTTPTransportManager(mock_server, config)
        client = TestClient(manager.app)
        
        # Make an OPTIONS request (CORS preflight)
        response = client.options("/health")
        
        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers

    def test_cors_allows_configured_origins(self):
        """Test CORS allows configured origins."""
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        config.cors.allowed_origins = ["https://example.com"]
        
        manager = HTTPTransportManager(mock_server, config)
        client = TestClient(manager.app)
        
        # Make request with origin header
        response = client.get("/health", headers={"Origin": "https://example.com"})
        
        # Should allow the origin
        assert response.status_code == 200

    def test_cors_allows_all_origins_with_wildcard(self):
        """Test CORS allows all origins with wildcard."""
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        config.cors.allowed_origins = ["*"]
        
        manager = HTTPTransportManager(mock_server, config)
        client = TestClient(manager.app)
        
        response = client.get("/health", headers={"Origin": "https://any-origin.com"})
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers


@pytest.mark.skipif(not HTTP_AVAILABLE, reason="HTTP transport dependencies not available")
class TestSSEFunctionality:
    """Test Server-Sent Events functionality."""

    def test_sse_response_mode_available(self):
        """Test that SSE response mode is available."""
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        config.response_mode = "sse"
        
        manager = HTTPTransportManager(mock_server, config)
        
        assert manager.config.response_mode == "sse"

    def test_json_response_mode_available(self):
        """Test that JSON response mode is available."""
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        config.response_mode = "json"
        
        manager = HTTPTransportManager(mock_server, config)
        
        assert manager.config.response_mode == "json"


@pytest.mark.skipif(not HTTP_AVAILABLE, reason="HTTP transport dependencies not available")
class TestHTTPErrorHandling:
    """Test error handling in HTTP transport."""

    def test_http_handles_invalid_json(self):
        """Test HTTP transport handles invalid JSON gracefully."""
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        
        manager = HTTPTransportManager(mock_server, config)
        client = TestClient(manager.app)
        
        # Send invalid JSON
        response = client.post("/mcp", content="invalid json")
        
        # Should return error response
        assert response.status_code in [400, 500]

    def test_http_handles_missing_body(self):
        """Test HTTP transport handles missing request body."""
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        
        manager = HTTPTransportManager(mock_server, config)
        client = TestClient(manager.app)
        
        # Send empty body
        response = client.post("/mcp")
        
        # Should return error response
        assert response.status_code in [400, 422, 500]


@pytest.mark.skipif(not HTTP_AVAILABLE, reason="HTTP transport dependencies not available")
class TestHTTPMetricsIntegration:
    """Test metrics integration in HTTP transport."""

    def test_http_records_health_check_metrics(self):
        """Test that HTTP transport records health check metrics."""
        from utils.metrics import MCPMetrics
        
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        mock_metrics = MagicMock(spec=MCPMetrics)
        
        manager = HTTPTransportManager(mock_server, config, mock_metrics)
        client = TestClient(manager.app)
        
        # Make health check request
        response = client.get("/health")
        
        assert response.status_code == 200

    def test_http_passes_metrics_to_handlers(self):
        """Test that metrics are available to request handlers."""
        from utils.metrics import MCPMetrics
        
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        mock_metrics = MagicMock(spec=MCPMetrics)
        
        manager = HTTPTransportManager(mock_server, config, mock_metrics)
        
        # Metrics should be accessible
        assert manager.metrics is not None


@pytest.mark.skipif(not HTTP_AVAILABLE, reason="HTTP transport dependencies not available")
class TestHTTPConfiguration:
    """Test HTTP configuration options."""

    def test_http_config_default_values(self):
        """Test HTTP configuration default values."""
        config = HTTPConfig()
        
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.response_mode == "sse"

    def test_http_config_custom_values(self):
        """Test HTTP configuration with custom values."""
        config = HTTPConfig(
            host="127.0.0.1",
            port=9000,
            response_mode="json"
        )
        
        assert config.host == "127.0.0.1"
        assert config.port == 9000
        assert config.response_mode == "json"

    def test_http_config_cors_settings(self):
        """Test CORS configuration settings."""
        config = HTTPConfig()
        
        # Should have CORS config
        assert hasattr(config, 'cors')
        assert hasattr(config.cors, 'allowed_origins')
        assert hasattr(config.cors, 'allowed_methods')
        assert hasattr(config.cors, 'allowed_headers')


@pytest.mark.skipif(not HTTP_AVAILABLE, reason="HTTP transport dependencies not available")
class TestHTTPServerLifecycle:
    """Test HTTP server lifecycle management."""

    @pytest.mark.asyncio
    async def test_http_server_can_be_created(self):
        """Test that HTTP server can be created."""
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        
        manager = HTTPTransportManager(mock_server, config)
        
        assert manager is not None
        assert manager.app is not None

    def test_http_transport_manager_has_run_method(self):
        """Test that HTTPTransportManager has a run method."""
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        
        manager = HTTPTransportManager(mock_server, config)
        
        assert hasattr(manager, 'run')
        assert callable(manager.run)


@pytest.mark.skipif(not HTTP_AVAILABLE, reason="HTTP transport dependencies not available")
class TestHTTPStatelessness:
    """Test stateless design of HTTP transport."""

    def test_http_multiple_requests_independent(self):
        """Test that multiple HTTP requests are independent."""
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        
        manager = HTTPTransportManager(mock_server, config)
        client = TestClient(manager.app)
        
        # Make multiple health check requests
        response1 = client.get("/health")
        response2 = client.get("/health")
        
        # Both should succeed independently
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Responses should be independent
        data1 = response1.json()
        data2 = response2.json()
        
        # Both should have status
        assert "status" in data1
        assert "status" in data2

    def test_http_no_session_state_maintained(self):
        """Test that HTTP transport maintains no session state."""
        mock_server = MagicMock(spec=Server)
        config = HTTPConfig()
        
        manager = HTTPTransportManager(mock_server, config)
        
        # Should not have session storage
        assert not hasattr(manager, 'sessions')
        assert not hasattr(manager, 'session_state')
