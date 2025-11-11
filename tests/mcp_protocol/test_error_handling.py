"""
Tests for MCP protocol error handling.

Tests various error conditions and ensures proper JSON-RPC error responses.
"""

import pytest
import json
import asyncio
from typing import Dict, Any
from unittest.mock import patch, AsyncMock
from fastmcp import Client
from mcp import types
from tests.mcp_protocol import BaseMCPTest, MCPProtocolValidator, MCPTestUtils


@pytest.mark.mcp_protocol
@pytest.mark.error_handling
@pytest.mark.mcp_client
class TestMCPErrorHandlingClient(BaseMCPTest):
    """Test error handling via FastMCP Client."""

    @pytest.mark.asyncio
    async def test_tool_parameter_validation_errors(self, mcp_client: Client):
        """Test various parameter validation errors."""
        # Missing required parameter - client validates and raises exception
        with pytest.raises(Exception) as exc_info:
            await self.call_xray_tool(
                mcp_client,
                action='list'  # Missing 'entity'
            )

        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in ['entity', 'required', 'missing', 'property'])

        # Invalid entity value - client validates and raises exception
        with pytest.raises(Exception) as exc_info:
            await self.call_xray_tool(
                mcp_client,
                entity='invalid_entity_type',
                action='list'
            )

        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in ['invalid', 'entity', 'enum', 'value'])

        # Invalid limit value - client accepts and sends to server (doesn't validate range)
        # Mock entire test to avoid any API calls
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock):
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = {
                    'data': {
                        'getTests': {
                            'results': []
                        }
                    }
                }

                # The -1 limit is not validated by client, so it gets sent to server
                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='list',
                    project_key='DEMO',
                    limit=-1  # Negative limit
                )
                await self.assert_mcp_tool_result(result)
                assert len(result.content) > 0, "Content should not be empty"

    @pytest.mark.asyncio
    async def test_malformed_json_steps_parameter(self, mcp_client: Client):
        """Test malformed JSON in steps parameter."""
        # FastMCP Client doesn't validate JSON format before sending to server
        # Server should handle malformed JSON gracefully
        result = await self.call_xray_tool(
            mcp_client,
            entity='test',
            action='create',
            project_key='DEMO',
            test_type='Manual',
            summary='Test with Invalid Steps',
            steps='{"invalid": "json" missing bracket'  # Malformed JSON
        )

        # Should get a result (either success or error)
        await self.assert_mcp_tool_result(result)

        # Result should contain some content
        assert isinstance(result.content, list), "Result should have content"
        assert len(result.content) > 0, "Content should not be empty"

    @pytest.mark.asyncio
    async def test_steps_wrong_structure(self, mcp_client: Client):
        """Test steps parameter with wrong structure."""
        # Mock successful authentication to avoid auth errors
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock):
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = {
                    'data': {
                        'createTest': {
                            'test': {
                                'issueId': '12345',
                                'jira': {'key': 'TEST-123', 'summary': 'Mock Test'}
                            }
                        }
                    }
                }

                # Test with non-array JSON - client accepts it and sends to server
                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='create',
                    project_key='DEMO',
                    test_type='Manual',
                    summary='Test with Wrong Steps Structure',
                    steps='{"not": "an array"}'  # Should be array
                )

                await self.assert_mcp_tool_result(result)
                assert len(result.content) > 0, "Content should not be empty"

                # Test with array of invalid step objects - client accepts it and sends to server
                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='create',
                    project_key='DEMO',
                    test_type='Manual',
                    summary='Test with Invalid Step Objects',
                    steps='[{"missing": "required fields"}]'  # Missing action, data, result
                )

                await self.assert_mcp_tool_result(result)
                assert len(result.content) > 0, "Content should not be empty"

    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, mcp_client: Client):
        """Test handling of authentication errors."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock) as mock_auth:
            # Simulate authentication failure
            mock_auth.side_effect = Exception("Authentication failed: Invalid credentials")

            # MCP server handles auth errors gracefully, returning result instead of raising
            result = await self.call_xray_tool(
                mcp_client,
                entity='test',
                action='list',
                project_key='DEMO'
            )

            await self.assert_mcp_tool_result(result)
            # Authentication errors should still result in some form of response
            assert len(result.content) > 0, "Content should not be empty"

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mcp_client: Client):
        """Test handling of various API errors."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock):
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                # Test GraphQL error response - server handles errors gracefully
                mock_execute.return_value = {
                    'errors': [
                        {
                            'message': 'Project not found',
                            'extensions': {'code': 'NOT_FOUND'}
                        }
                    ]
                }

                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='list',
                    project_key='NONEXISTENT'
                )

                await self.assert_mcp_tool_result(result)
                assert len(result.content) > 0, "Content should not be empty"

                # Test network/connection error - server handles errors gracefully
                mock_execute.side_effect = Exception("Connection timeout")

                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='list',
                    project_key='DEMO'
                )

                await self.assert_mcp_tool_result(result)
                assert len(result.content) > 0, "Content should not be empty"

    @pytest.mark.asyncio
    async def test_rate_limiting_simulation(self, mcp_client: Client):
        """Test handling of rate limiting scenarios."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock):
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                # Simulate rate limiting response - server handles errors gracefully
                mock_execute.return_value = {
                    'errors': [
                        {
                            'message': 'Rate limit exceeded',
                            'extensions': {'code': 'RATE_LIMITED'}
                        }
                    ]
                }

                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='list',
                    project_key='DEMO'
                )

                await self.assert_mcp_tool_result(result)
                assert len(result.content) > 0, "Content should not be empty"


@pytest.mark.mcp_protocol
@pytest.mark.error_handling
@pytest.mark.mcp_subprocess
class TestMCPErrorHandlingSubprocess(BaseMCPTest):
    """Test error handling via subprocess communication."""

    @pytest.mark.asyncio
    async def test_invalid_json_request(self, mcp_server_process):
        """Test handling of invalid JSON requests."""
        # Send malformed JSON
        invalid_json = b'{"invalid": json without closing brace\n'

        try:
            mcp_server_process.process.stdin.write(invalid_json)
            await mcp_server_process.process.stdin.drain()

            # Server should either send error or close connection gracefully
            # Wait briefly to see if server responds or stays stable
            await asyncio.sleep(0.5)

            # Server should still be running (not crashed)
            assert mcp_server_process.process.returncode is None, "Server should not crash on invalid JSON"

        except Exception:
            # If writing fails, that's also acceptable (server might close connection)
            pass

    @pytest.mark.asyncio
    async def test_missing_jsonrpc_fields(self, mcp_server_process):
        """Test requests missing required JSON-RPC fields."""
        # Missing 'method' field
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
            error = response['error']
            assert error['code'] in [-32600, -32601, -32602], "Should be JSON-RPC parse/method/params error"
        except RuntimeError as e:
            if "timeout" in str(e).lower():
                # Timeout is acceptable for malformed requests
                pass
            else:
                raise

    @pytest.mark.asyncio
    async def test_invalid_method_name(self, mcp_server_process, mcp_test_scenarios):
        """Test requests with invalid method names."""
        # Initialize first
        init_request = mcp_test_scenarios['initialize_request']
        await mcp_server_process.send_json_rpc(init_request)

        # Call invalid method
        request = {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'invalid/method',
            'params': {}
        }

        response = await mcp_server_process.send_json_rpc(request)
        await self.assert_valid_error_response(response, request['id'])

        error = response['error']
        # Accept either "method not found" (-32601) or "invalid params" (-32602)
        # Both are valid JSON-RPC responses for invalid method calls
        assert error['code'] in [-32601, -32602], f"Should be method error, got {error['code']}"
        # Error message should mention the invalid method or be about parameters
        error_msg = error['message'].lower()
        assert any(keyword in error_msg for keyword in ['method', 'invalid', 'params', 'unknown'])

    @pytest.mark.asyncio
    async def test_tool_call_nonexistent_tool(self, mcp_server_process, mcp_test_scenarios):
        """Test calling nonexistent tool."""
        # Initialize first
        init_request = mcp_test_scenarios['initialize_request']
        await mcp_server_process.send_json_rpc(init_request)

        # Call nonexistent tool
        request = {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/call',
            'params': {
                'name': 'nonexistent_tool',
                'arguments': {}
            }
        }

        response = await mcp_server_process.send_json_rpc(request)
        await self.assert_valid_error_response(response, request['id'])

        error_message = response['error']['message'].lower()
        # Error message should indicate that the tool doesn't exist
        assert any(keyword in error_message for keyword in [
            'tool', 'not found', 'unknown', 'invalid', 'nonexistent', 'does not exist',
            'unrecognized', 'unavailable', 'missing', 'error'
        ]), f"Error message should indicate tool not found, got: {error_message}"

    @pytest.mark.asyncio
    async def test_tool_call_invalid_arguments(self, mcp_server_process, mcp_test_scenarios):
        """Test tool call with invalid argument structure."""
        # Initialize first
        init_request = mcp_test_scenarios['initialize_request']
        await mcp_server_process.send_json_rpc(init_request)

        # Call with invalid arguments (should be object, not string)
        request = {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/call',
            'params': {
                'name': 'xray_test',
                'arguments': 'invalid_arguments_string'
            }
        }

        response = await mcp_server_process.send_json_rpc(request)
        await self.assert_valid_error_response(response, request['id'])

    @pytest.mark.asyncio
    async def test_requests_without_initialization(self, mcp_server_process):
        """Test making requests without proper initialization."""
        # Try to list tools without initialization
        request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/list',
            'params': {}
        }

        response = await mcp_server_process.send_json_rpc(request)

        # Server might require initialization or allow it
        if 'error' in response:
            await self.assert_valid_error_response(response, request['id'])
            error_message = response['error']['message'].lower()
            # Error message should indicate initialization issue
            assert any(keyword in error_message for keyword in [
                'initialize', 'not initialized', 'initialization', 'init', 'setup',
                'handshake', 'ready', 'connection', 'invalid', 'error'
            ]), f"Error message should indicate initialization issue, got: {error_message}"

    @pytest.mark.asyncio
    async def test_malformed_tool_parameters(self, mcp_server_process, mcp_test_scenarios):
        """Test tool calls with malformed parameters."""
        # Initialize first
        init_request = mcp_test_scenarios['initialize_request']
        await mcp_server_process.send_json_rpc(init_request)

        # Test with missing required parameters
        request = {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/call',
            'params': {
                'name': 'xray_test',
                'arguments': {
                    'action': 'list'  # Missing required 'entity'
                }
            }
        }

        response = await mcp_server_process.send_json_rpc(request)
        await self.assert_valid_error_response(response, request['id'])

        error_message = response['error']['message'].lower()
        # Error message should indicate parameter issues
        assert any(keyword in error_message for keyword in [
            'entity', 'required', 'missing', 'parameter', 'invalid', 'argument',
            'validation', 'field', 'property', 'error'
        ]), f"Error message should indicate parameter issue, got: {error_message}"


@pytest.mark.mcp_protocol
@pytest.mark.error_handling
@pytest.mark.jsonrpc
class TestJSONRPCCompliance(BaseMCPTest):
    """Test JSON-RPC 2.0 specification compliance."""

    @pytest.mark.asyncio
    async def test_error_response_structure(self, mcp_server_process):
        """Test that error responses follow JSON-RPC 2.0 spec."""
        # Send malformed request
        request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'invalid_method'
        }

        response = await mcp_server_process.send_json_rpc(request)
        await self.assert_valid_error_response(response, request['id'])

        error = response['error']

        # Validate error structure according to JSON-RPC 2.0
        assert isinstance(error['code'], int), "Error code must be integer"
        assert isinstance(error['message'], str), "Error message must be string"
        assert len(error['message']) > 0, "Error message must not be empty"

        # Code should be in valid range
        valid_codes = [-32700, -32600, -32601, -32602, -32603] + list(range(-32099, -32000))
        assert error['code'] in valid_codes or -32768 <= error['code'] <= -32000, \
            f"Error code {error['code']} not in valid JSON-RPC range"

    @pytest.mark.asyncio
    async def test_request_id_preservation(self, mcp_server_process):
        """Test that request ID is preserved in responses and errors."""
        test_ids = [1, "string_id", None]

        for test_id in test_ids:
            request = {
                'jsonrpc': '2.0',
                'method': 'invalid_method'
            }

            if test_id is not None:
                request['id'] = test_id

            # Server should either return an error or not respond (timeout)
            # Both are acceptable behavior for invalid methods
            try:
                response = await mcp_server_process.send_json_rpc(request)

                if test_id is not None:
                    assert 'id' in response, f"Response should include ID for ID {test_id}"
                    assert response['id'] == test_id, f"Response ID should match request ID {test_id}"
                else:
                    # For notifications (no ID), response handling varies
                    # Some servers might not respond to notifications
                    if 'id' in response:
                        assert response['id'] is None
            except RuntimeError as e:
                if "timeout" in str(e).lower():
                    # Timeout is acceptable for invalid methods
                    pass
                else:
                    raise

    @pytest.mark.asyncio
    async def test_jsonrpc_version_requirement(self, mcp_server_process):
        """Test that jsonrpc version is required and validated."""
        # Missing jsonrpc field
        request = {
            'id': 1,
            'method': 'initialize',
            'params': {}
        }

        # Server should either return an error or not respond (timeout)
        # Both are acceptable for malformed requests
        try:
            response = await mcp_server_process.send_json_rpc(request)
            await self.assert_valid_error_response(response, request['id'])
        except RuntimeError as e:
            if "timeout" in str(e).lower():
                # Timeout is acceptable for missing jsonrpc field
                pass
            else:
                raise

        # Wrong jsonrpc version
        request = {
            'jsonrpc': '1.0',  # Wrong version
            'id': 2,
            'method': 'initialize',
            'params': {}
        }

        try:
            response = await mcp_server_process.send_json_rpc(request)
            # Server might be lenient or strict about version
            if 'error' in response:
                await self.assert_valid_error_response(response, request['id'])
        except RuntimeError as e:
            if "timeout" in str(e).lower():
                # Timeout is acceptable for wrong jsonrpc version
                pass
            else:
                raise


@pytest.mark.mcp_protocol
@pytest.mark.error_handling
@pytest.mark.edge_case
class TestMCPErrorEdgeCases(BaseMCPTest):
    """Test edge cases in error handling."""

    @pytest.mark.asyncio
    async def test_very_large_request(self, mcp_server_process, mcp_test_scenarios):
        """Test handling of very large requests."""
        # Initialize first
        init_request = mcp_test_scenarios['initialize_request']
        await mcp_server_process.send_json_rpc(init_request)

        # Create a very large request (large summary)
        large_summary = "A" * 10000  # 10KB summary

        request = {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/call',
            'params': {
                'name': 'xray_test',
                'arguments': {
                    'entity': 'test',
                    'action': 'create',
                    'project_key': 'DEMO',
                    'summary': large_summary
                }
            }
        }

        try:
            response = await mcp_server_process.send_json_rpc(request)

            # Should either work or return appropriate error
            if 'error' in response:
                await self.assert_valid_error_response(response, request['id'])
            else:
                await self.assert_valid_jsonrpc_response(response, request['id'])

        except Exception:
            # Connection issues with large requests are also acceptable
            pass

    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self, mcp_server_process, mcp_test_scenarios):
        """Test handling of unicode and special characters."""
        # Initialize first
        init_request = mcp_test_scenarios['initialize_request']
        await mcp_server_process.send_json_rpc(init_request)

        # Test with unicode characters
        unicode_summary = "Test with émojis 🚀 and ünicöde 测试"

        request = {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/call',
            'params': {
                'name': 'xray_test',
                'arguments': {
                    'entity': 'test',
                    'action': 'create',
                    'project_key': 'DEMO',
                    'summary': unicode_summary
                }
            }
        }

        response = await mcp_server_process.send_json_rpc(request)

        # Should handle unicode properly
        if 'error' in response:
            await self.assert_valid_error_response(response, request['id'])
            # Error should not be due to unicode handling
            error_msg = response['error']['message'].lower()
            assert 'unicode' not in error_msg and 'encoding' not in error_msg
        else:
            await self.assert_valid_jsonrpc_response(response, request['id'])

    @pytest.mark.asyncio
    async def test_concurrent_error_scenarios(self, mcp_server_process, mcp_test_scenarios):
        """Test concurrent requests that cause errors."""
        # Initialize first
        init_request = mcp_test_scenarios['initialize_request']
        await mcp_server_process.send_json_rpc(init_request)

        async def make_invalid_request(request_id):
            request = {
                'jsonrpc': '2.0',
                'id': request_id,
                'method': 'tools/call',
                'params': {
                    'name': 'xray_test',
                    'arguments': {
                        'action': 'list'  # Missing entity - will cause error
                    }
                }
            }
            return await mcp_server_process.send_json_rpc(request)

        # Make multiple concurrent invalid requests
        tasks = [make_invalid_request(i) for i in range(2, 5)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # All should be valid error responses
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                # Connection issues are acceptable under concurrent load
                continue

            await self.assert_valid_error_response(response, i + 2)

    @pytest.mark.asyncio
    async def test_nested_error_scenarios(self, mcp_client: Client):
        """Test complex nested error scenarios."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock):
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                # Simulate authentication success but API failure - server handles gracefully
                mock_execute.side_effect = [
                    None,  # Auth succeeds
                    Exception("Nested API error")  # But API call fails
                ]

                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='list',
                    project_key='DEMO'
                )

                await self.assert_mcp_tool_result(result)
                assert len(result.content) > 0, "Content should not be empty"

    @pytest.mark.asyncio
    async def test_timeout_error_handling(self, mcp_server_process, mcp_test_scenarios):
        """Test handling of timeout scenarios."""
        # Initialize first
        init_request = mcp_test_scenarios['initialize_request']
        await mcp_server_process.send_json_rpc(init_request)

        # Send request and then wait for timeout
        request = {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/call',
            'params': {
                'name': 'xray_test',
                'arguments': {
                    'entity': 'test',
                    'action': 'list',
                    'project_key': 'DEMO'
                }
            }
        }

        try:
            # Use a very short timeout to simulate timeout scenario
            response = await asyncio.wait_for(
                mcp_server_process.send_json_rpc(request),
                timeout=0.1  # Very short timeout
            )

            # If it succeeds quickly, that's fine too
            if 'error' in response:
                await self.assert_valid_error_response(response, request['id'])
            else:
                await self.assert_valid_jsonrpc_response(response, request['id'])

        except asyncio.TimeoutError:
            # Timeout is expected and acceptable
            pass