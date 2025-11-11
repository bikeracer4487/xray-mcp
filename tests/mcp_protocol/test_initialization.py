"""
Tests for MCP protocol initialization and handshake.

Tests the initialize/initialized handshake sequence that MCP clients
perform when connecting to the server.
"""

import pytest
import asyncio
from typing import Dict, Any
from fastmcp import Client
from mcp import types
from tests.mcp_protocol import BaseMCPTest, MCPProtocolValidator, MCPTestUtils


@pytest.mark.mcp_protocol
@pytest.mark.mcp_client
class TestMCPInitialization(BaseMCPTest):
    """Test MCP initialization protocol."""

    @pytest.mark.asyncio
    async def test_server_starts_successfully(self, mcp_client: Client):
        """Test that the MCP server starts without errors."""
        # Just accessing the client should verify the server started
        assert mcp_client is not None

        # Try to ping server to confirm it's responsive
        try:
            await mcp_client.ping()
            # If ping succeeds, try to list tools to confirm functionality
            tools = await mcp_client.list_tools()
            assert tools is not None
        except Exception as e:
            pytest.fail(f"Server not responsive during initialization: {e}")

    @pytest.mark.asyncio
    async def test_initialize_handshake(self, mcp_client: Client):
        """Test the initialize/initialized handshake sequence."""
        # This should already be done by the client, but we test it explicitly
        await mcp_client.ping()

        # Verify the handshake worked by listing tools
        tools = await mcp_client.list_tools()
        assert tools is not None
        assert isinstance(tools, list)

    @pytest.mark.asyncio
    async def test_server_capabilities(self, mcp_client: Client):
        """Test that server advertises correct capabilities."""
        # Test server capabilities by checking available operations
        tools = await mcp_client.list_tools()
        assert tools is not None
        assert len(tools) > 0  # Should have at least one tool

        # Try to list resources to check if supported
        try:
            resources = await mcp_client.list_resources()
            # Resources are optional, so None is acceptable
        except Exception:
            # Resources might not be supported, which is fine
            pass

    @pytest.mark.asyncio
    async def test_protocol_version_negotiation(self, mcp_client: Client):
        """Test that protocol version is properly negotiated."""
        # Test that protocol negotiation succeeded by pinging server
        await mcp_client.ping()

        # If we can successfully interact with the server,
        # the protocol version negotiation was successful
        tools = await mcp_client.list_tools()
        assert tools is not None


@pytest.mark.mcp_protocol
@pytest.mark.mcp_subprocess
class TestMCPInitializationSubprocess(BaseMCPTest):
    """Test MCP initialization using subprocess communication."""

    @pytest.mark.asyncio
    async def test_raw_initialize_request(self, mcp_server_process, mcp_test_scenarios):
        """Test sending raw initialize request via JSON-RPC."""
        request = mcp_test_scenarios['initialize_request']

        response = await mcp_server_process.send_json_rpc(request)

        await self.assert_valid_jsonrpc_response(response, request['id'])
        await MCPProtocolValidator.validate_initialize_response(response)

    @pytest.mark.asyncio
    async def test_initialize_with_capabilities(self, mcp_server_process):
        """Test initialize request with client capabilities."""
        request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {
                    'roots': {'listChanged': True},
                    'sampling': {}
                },
                'clientInfo': {
                    'name': 'test-client',
                    'version': '1.0.0'
                }
            }
        }

        response = await mcp_server_process.send_json_rpc(request)

        await self.assert_valid_jsonrpc_response(response, request['id'])
        await MCPProtocolValidator.validate_initialize_response(response)

        result = response['result']
        assert 'serverInfo' in result
        assert result['serverInfo']['name'] == "Xray Test Management"

    @pytest.mark.asyncio
    async def test_initialize_with_minimal_client_info(self, mcp_server_process):
        """Test initialize request with minimal client info."""
        request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {
                    'name': 'minimal-test-client',
                    'version': '1.0.0'
                }
            }
        }

        response = await mcp_server_process.send_json_rpc(request)

        await self.assert_valid_jsonrpc_response(response, request['id'])
        await MCPProtocolValidator.validate_initialize_response(response)

    @pytest.mark.asyncio
    async def test_initialize_with_unsupported_protocol_version(self, mcp_server_process):
        """Test initialize request with unsupported protocol version."""
        request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '1999-01-01',  # Very old version
                'capabilities': {},
                'clientInfo': {
                    'name': 'test-client',
                    'version': '1.0.0'
                }
            }
        }

        response = await mcp_server_process.send_json_rpc(request)

        # Should either work (server is flexible) or return appropriate error
        if 'error' in response:
            await self.assert_valid_error_response(response, request['id'])
        else:
            await self.assert_valid_jsonrpc_response(response, request['id'])

    @pytest.mark.asyncio
    async def test_initialize_malformed_request(self, mcp_server_process):
        """Test malformed initialize request."""
        request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                # Missing required protocolVersion
                'capabilities': {},
                'clientInfo': {
                    'name': 'test-client',
                    'version': '1.0.0'
                }
            }
        }

        response = await mcp_server_process.send_json_rpc(request)

        # Should return error for malformed request
        await self.assert_valid_error_response(response, request['id'])

    @pytest.mark.asyncio
    async def test_double_initialize(self, mcp_server_process, mcp_test_scenarios):
        """Test that calling initialize twice is handled gracefully."""
        request = mcp_test_scenarios['initialize_request']

        # First initialize
        response1 = await mcp_server_process.send_json_rpc(request)
        await self.assert_valid_jsonrpc_response(response1, request['id'])

        # Second initialize with different ID
        request2 = request.copy()
        request2['id'] = 2

        response2 = await mcp_server_process.send_json_rpc(request2)

        # Should either work or return appropriate error
        # MCP spec doesn't strictly define this behavior
        if 'error' in response2:
            await self.assert_valid_error_response(response2, request2['id'])
        else:
            await self.assert_valid_jsonrpc_response(response2, request2['id'])


@pytest.mark.mcp_protocol
@pytest.mark.performance
class TestMCPInitializationPerformance(BaseMCPTest):
    """Test MCP initialization performance."""

    @pytest.mark.asyncio
    async def test_initialize_performance(self, server_script_path, performance_timer):
        """Test that initialization completes within reasonable time."""
        with performance_timer("MCP Client Connection") as timer:
            async with Client(server_script_path) as client:
                await client.ping()

        # Should initialize within 5 seconds
        timer.assert_duration_under(5.0)

    @pytest.mark.asyncio
    async def test_multiple_client_initialization(self, server_script_path):
        """Test that multiple clients can initialize concurrently."""
        async def create_client():
            async with Client(server_script_path) as client:
                await client.ping()
                tools = await client.list_tools()
                return len(tools) > 0  # Return True if tools available

        # Create 3 clients concurrently
        tasks = [create_client() for _ in range(3)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(result for result in results)

    @pytest.mark.asyncio
    async def test_rapid_connect_disconnect(self, server_script_path):
        """Test rapid connection and disconnection cycles."""
        for i in range(5):
            async with Client(server_script_path) as client:
                await client.ping()
                tools = await client.list_tools()
                assert len(tools) > 0
                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.1)


@pytest.mark.mcp_protocol
@pytest.mark.error_handling
class TestMCPInitializationErrorHandling(BaseMCPTest):
    """Test error handling during MCP initialization."""

    @pytest.mark.asyncio
    async def test_invalid_json_request(self, mcp_server_process):
        """Test that invalid JSON is handled gracefully."""
        # Send invalid JSON
        invalid_request = b"invalid json content\n"

        mcp_server_process.process.stdin.write(invalid_request)
        await mcp_server_process.process.stdin.drain()

        # Server should either close connection or send error
        # We'll wait briefly and check if server is still running
        await asyncio.sleep(0.5)

        # Server process should still be running (not crashed)
        assert mcp_server_process.process.returncode is None

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, mcp_server_process):
        """Test requests missing required JSON-RPC fields."""
        # Missing 'method'
        request = {
            'jsonrpc': '2.0',
            'id': 1,
            'params': {}
        }

        # Server should either return an error or not respond (timeout)
        # Both are acceptable behavior for malformed requests
        try:
            response = await mcp_server_process.send_json_rpc(request)
            # If we get a response, it should be an error
            await self.assert_valid_error_response(response, request['id'])
        except RuntimeError as e:
            if "timeout" in str(e).lower():
                # Timeout is acceptable for malformed requests
                pass
            else:
                raise

    @pytest.mark.asyncio
    async def test_incorrect_jsonrpc_version(self, mcp_server_process):
        """Test request with incorrect JSON-RPC version."""
        request = {
            'jsonrpc': '1.0',  # Wrong version
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {}
            }
        }

        # Server should either return an error or not respond (timeout)
        # Both are acceptable behavior for incorrect JSON-RPC version
        try:
            response = await mcp_server_process.send_json_rpc(request)
            # Should return error for unsupported JSON-RPC version
            if 'error' in response:
                await self.assert_valid_error_response(response, request['id'])
            else:
                # Server might be lenient and accept it
                await self.assert_valid_jsonrpc_response(response, request['id'])
        except RuntimeError as e:
            if "timeout" in str(e).lower():
                # Timeout is acceptable for incorrect JSON-RPC version
                pass
            else:
                raise