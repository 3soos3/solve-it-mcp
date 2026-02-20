"""Integration tests for STDIO transport.

This module tests the STDIO transport functionality to ensure backward compatibility
with the original MCP server implementation.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from mcp.server.lowlevel import Server
from mcp.server.models import InitializationOptions
import mcp.types as types


class TestSTDIOTransport:
    """Test suite for STDIO transport functionality."""

    @pytest.mark.asyncio
    async def test_stdio_transport_import(self):
        """Test that STDIO transport can be imported."""
        from transports import run_stdio_server
        
        assert callable(run_stdio_server)

    @pytest.mark.asyncio
    async def test_stdio_transport_with_mock_server(self):
        """Test STDIO transport with a mock MCP server."""
        from transports import run_stdio_server
        
        # Create a mock server
        mock_server = MagicMock(spec=Server)
        mock_server.get_capabilities = MagicMock(return_value={})
        
        # Mock the STDIO streams
        mock_read_stream = AsyncMock()
        mock_write_stream = AsyncMock()
        
        # Mock server.run to complete immediately
        async def mock_run(*args, **kwargs):
            """Mock run that completes immediately."""
            pass
        
        mock_server.run = AsyncMock(side_effect=mock_run)
        
        # Mock the stdio_server context manager
        class MockSTDIOServer:
            async def __aenter__(self):
                return (mock_read_stream, mock_write_stream)
            
            async def __aexit__(self, *args):
                pass
        
        with patch('transports.stdio_transport.mcp.server.stdio.stdio_server', return_value=MockSTDIOServer()):
            # Run the STDIO transport (will complete immediately due to mock)
            await run_stdio_server(mock_server)
            
            # Verify server.run was called
            mock_server.run.assert_called_once()
            
            # Verify it was called with the correct arguments
            call_args = mock_server.run.call_args
            assert call_args[0][0] == mock_read_stream
            assert call_args[0][1] == mock_write_stream
            assert isinstance(call_args[0][2], InitializationOptions)

    @pytest.mark.asyncio
    async def test_stdio_transport_handles_keyboard_interrupt(self):
        """Test that STDIO transport handles keyboard interrupts gracefully."""
        from transports import run_stdio_server
        
        # Create a mock server
        mock_server = MagicMock(spec=Server)
        mock_server.get_capabilities = MagicMock(return_value={})
        
        # Mock server.run to raise KeyboardInterrupt
        async def mock_run_interrupt(*args, **kwargs):
            raise KeyboardInterrupt()
        
        mock_server.run = AsyncMock(side_effect=mock_run_interrupt)
        
        # Mock the stdio_server context manager
        class MockSTDIOServer:
            async def __aenter__(self):
                return (AsyncMock(), AsyncMock())
            
            async def __aexit__(self, *args):
                pass
        
        with patch('transports.stdio_transport.mcp.server.stdio.stdio_server', return_value=MockSTDIOServer()):
            # Should handle KeyboardInterrupt gracefully (not re-raise)
            try:
                await run_stdio_server(mock_server)
            except KeyboardInterrupt:
                pytest.fail("KeyboardInterrupt should be handled gracefully")

    @pytest.mark.asyncio
    async def test_stdio_transport_logs_startup(self):
        """Test that STDIO transport runs without errors."""
        from transports import run_stdio_server
        
        # Create a mock server
        mock_server = MagicMock(spec=Server)
        mock_server.get_capabilities = MagicMock(return_value={})
        
        # Mock server.run to complete immediately
        mock_server.run = AsyncMock()
        
        # Mock the stdio_server context manager
        class MockSTDIOServer:
            async def __aenter__(self):
                return (AsyncMock(), AsyncMock())
            
            async def __aexit__(self, *args):
                pass
        
        with patch('transports.stdio_transport.mcp.server.stdio.stdio_server', return_value=MockSTDIOServer()):
            # Should run without errors (logging happens but we don't assert on it)
            await run_stdio_server(mock_server)
            
            # Verify server.run was called
            assert mock_server.run.called

    @pytest.mark.asyncio
    async def test_stdio_transport_initialization_options(self):
        """Test that STDIO transport uses correct initialization options."""
        from transports import run_stdio_server
        
        # Create a mock server
        mock_server = MagicMock(spec=Server)
        mock_server.get_capabilities = MagicMock(return_value={
            "tools": {},
            "prompts": {}
        })
        
        # Capture the initialization options
        captured_init_options = None
        
        async def capture_init_options(read_stream, write_stream, init_options):
            nonlocal captured_init_options
            captured_init_options = init_options
        
        mock_server.run = AsyncMock(side_effect=capture_init_options)
        
        # Mock the stdio_server context manager
        class MockSTDIOServer:
            async def __aenter__(self):
                return (AsyncMock(), AsyncMock())
            
            async def __aexit__(self, *args):
                pass
        
        with patch('transports.stdio_transport.mcp.server.stdio.stdio_server', return_value=MockSTDIOServer()):
            await run_stdio_server(mock_server)
            
            # Verify initialization options
            assert captured_init_options is not None
            assert captured_init_options.server_name == "solveit_mcp_server"
            assert captured_init_options.server_version == "0.1.0"
            assert captured_init_options.capabilities is not None


class TestSTDIOTransportBackwardCompatibility:
    """Test backward compatibility with original STDIO implementation."""

    @pytest.mark.asyncio
    async def test_stdio_maintains_same_interface(self):
        """Test that refactored STDIO transport maintains the same interface."""
        from transports import run_stdio_server
        
        # The function should accept a Server instance
        mock_server = MagicMock(spec=Server)
        mock_server.get_capabilities = MagicMock(return_value={})
        mock_server.run = AsyncMock()
        
        class MockSTDIOServer:
            async def __aenter__(self):
                return (AsyncMock(), AsyncMock())
            
            async def __aexit__(self, *args):
                pass
        
        with patch('transports.stdio_transport.mcp.server.stdio.stdio_server', return_value=MockSTDIOServer()):
            # Should work with just a server parameter
            await run_stdio_server(mock_server)
            
            # Verify it was called
            assert mock_server.run.called

    def test_stdio_transport_available_in_transports_module(self):
        """Test that STDIO transport is exported from transports module."""
        from transports import run_stdio_server
        
        # Should be importable from the main transports module
        assert run_stdio_server is not None
        assert callable(run_stdio_server)


class TestSTDIOTransportErrorHandling:
    """Test error handling in STDIO transport."""

    @pytest.mark.asyncio
    async def test_stdio_handles_exception_group(self):
        """Test that STDIO transport handles ExceptionGroup errors."""
        from transports import run_stdio_server
        
        # Create a mock server
        mock_server = MagicMock(spec=Server)
        mock_server.get_capabilities = MagicMock(return_value={})
        
        # Create an exception that mimics ExceptionGroup
        class MockExceptionGroup(Exception):
            def __init__(self, msg, exceptions):
                super().__init__(msg)
                self.exceptions = exceptions
        
        # Mock server.run to raise ExceptionGroup
        async def mock_run_exception(*args, **kwargs):
            raise MockExceptionGroup("Multiple errors", [
                ValueError("Error 1"),
                RuntimeError("Error 2")
            ])
        
        mock_server.run = AsyncMock(side_effect=mock_run_exception)
        
        # Mock the stdio_server context manager
        class MockSTDIOServer:
            async def __aenter__(self):
                return (AsyncMock(), AsyncMock())
            
            async def __aexit__(self, *args):
                pass
        
        with patch('transports.stdio_transport.mcp.server.stdio.stdio_server', return_value=MockSTDIOServer()):
            # Should log the exception and re-raise
            with pytest.raises(MockExceptionGroup):
                await run_stdio_server(mock_server)

    @pytest.mark.asyncio
    async def test_stdio_handles_regular_exceptions(self):
        """Test that STDIO transport handles regular exceptions."""
        from transports import run_stdio_server
        
        # Create a mock server
        mock_server = MagicMock(spec=Server)
        mock_server.get_capabilities = MagicMock(return_value={})
        
        # Mock server.run to raise a regular exception
        async def mock_run_exception(*args, **kwargs):
            raise RuntimeError("Test error")
        
        mock_server.run = AsyncMock(side_effect=mock_run_exception)
        
        # Mock the stdio_server context manager
        class MockSTDIOServer:
            async def __aenter__(self):
                return (AsyncMock(), AsyncMock())
            
            async def __aexit__(self, *args):
                pass
        
        with patch('transports.stdio_transport.mcp.server.stdio.stdio_server', return_value=MockSTDIOServer()):
            # Should log the exception and re-raise
            with pytest.raises(RuntimeError):
                await run_stdio_server(mock_server)
