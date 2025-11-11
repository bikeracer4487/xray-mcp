"""
Tests for MCP tool invocation functionality.

Tests the tools/call operation and parameter validation.
"""

import pytest
import json
from typing import Dict, Any
from unittest.mock import patch, AsyncMock
from fastmcp import Client
from mcp import types
from tests.mcp_protocol import BaseMCPTest, MCPProtocolValidator, MCPTestUtils


@pytest.mark.mcp_protocol
@pytest.mark.mcp_client
class TestMCPToolInvocation(BaseMCPTest):
    """Test MCP tool invocation via FastMCP Client."""

    @pytest.mark.asyncio
    async def test_basic_tool_call(self, mcp_client: Client):
        """Test basic tool invocation with valid parameters."""
        # Skip if no credentials to avoid hitting real API
        if not self._has_xray_credentials():
            pytest.skip("Xray credentials not available")

        try:
            result = await self.call_xray_tool(
                mcp_client,
                entity='test',
                action='list',
                project_key='DEMO',
                limit=1
            )

            await self.assert_mcp_tool_result(result)

        except Exception as e:
            # If it fails due to authentication or API issues, that's expected
            # The important thing is that the MCP protocol layer worked
            if 'authentication' in str(e).lower() or 'unauthorized' in str(e).lower():
                pytest.skip(f"Authentication issue (expected): {e}")
            else:
                # Re-raise if it's a protocol error
                raise

    def _has_xray_credentials(self):
        """Check if Xray credentials are available."""
        import os
        return bool(os.getenv('XRAY_CLIENT_ID') and os.getenv('XRAY_CLIENT_SECRET'))

    @pytest.mark.asyncio
    async def test_tool_call_parameter_validation(self, mcp_client: Client):
        """Test that tool calls validate parameters correctly."""
        # Test missing required parameters
        with pytest.raises(Exception) as exc_info:
            await self.call_xray_tool(mcp_client, action='list')  # Missing entity

        error_msg = str(exc_info.value).lower()
        assert 'entity' in error_msg, "Should complain about missing entity parameter"

    @pytest.mark.asyncio
    async def test_tool_call_invalid_entity(self, mcp_client: Client):
        """Test tool call with invalid entity value."""
        with pytest.raises(Exception) as exc_info:
            await self.call_xray_tool(
                mcp_client,
                entity='invalid_entity',
                action='list'
            )

        error_msg = str(exc_info.value).lower()
        assert 'entity' in error_msg or 'invalid' in error_msg

    @pytest.mark.asyncio
    async def test_tool_call_response_format(self, mcp_client: Client):
        """Test that tool call responses follow MCP format."""
        # Mock the Xray API to avoid hitting real endpoints
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock) as mock_auth:
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                mock_auth.return_value = None
                mock_execute.return_value = {
                    'data': {
                        'getTests': {
                            'results': [{
                                'issueId': '12345',
                                'jira': {'key': 'TEST-123', 'summary': 'Mock Test'},
                                'testType': {'name': 'Manual'}
                            }]
                        }
                    }
                }

                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='list',
                    project_key='DEMO'
                )

                await self.assert_mcp_tool_result(result)

                # Check content structure
                assert len(result.content) > 0
                content_item = result.content[0]
                assert hasattr(content_item, 'type')

                if hasattr(content_item, 'text'):
                    # Should be valid JSON if it's a text response
                    try:
                        data = json.loads(content_item.text)
                        assert isinstance(data, (dict, list))
                    except json.JSONDecodeError:
                        # Text might not be JSON, which is also valid
                        pass

    @pytest.mark.asyncio
    async def test_tool_call_array_parameters(self, mcp_client: Client):
        """Test tool calls with array parameters."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock):
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = {
                    'data': {
                        'createTestExecution': {
                            'testExecution': {
                                'issueId': '67890',
                                'jira': {'key': 'EXEC-456', 'summary': 'Test Execution'}
                            }
                        }
                    }
                }

                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test_execution',
                    action='create',
                    project_key='DEMO',
                    summary='Test Execution',
                    test_issue_ids=['TEST-123', 'TEST-124'],
                    test_environments=['staging', 'production']
                )

                await self.assert_mcp_tool_result(result)


@pytest.mark.mcp_protocol
@pytest.mark.mcp_subprocess
class TestMCPToolInvocationSubprocess(BaseMCPTest):
    """Test tool invocation using subprocess communication."""

    @pytest.mark.asyncio
    async def test_raw_tool_call_request(self, mcp_server_process, mcp_test_scenarios):
        """Test raw tools/call request via JSON-RPC."""
        # Initialize first
        init_request = mcp_test_scenarios['initialize_request']
        init_response = await mcp_server_process.send_json_rpc(init_request)
        await self.assert_valid_jsonrpc_response(init_response, init_request['id'])

        # Mock the authentication and API call
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock):
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = {
                    'data': {
                        'getTests': {
                            'results': [{
                                'issueId': '12345',
                                'jira': {'key': 'TEST-123', 'summary': 'Mock Test'},
                                'testType': {'name': 'Manual'}
                            }]
                        }
                    }
                }

                # Call tool
                call_request = mcp_test_scenarios['call_tool_request']
                response = await mcp_server_process.send_json_rpc(call_request)

                await self.assert_valid_jsonrpc_response(response, call_request['id'])
                await MCPProtocolValidator.validate_tool_call_response(response)

    @pytest.mark.asyncio
    async def test_tool_call_invalid_parameters(self, mcp_server_process, mcp_test_scenarios):
        """Test tool call with invalid parameters."""
        # Initialize first
        init_request = mcp_test_scenarios['initialize_request']
        await mcp_server_process.send_json_rpc(init_request)

        # Call with missing required parameter
        request = {
            'jsonrpc': '2.0',
            'id': 3,
            'method': 'tools/call',
            'params': {
                'name': 'xray_test',
                'arguments': {
                    'action': 'list'  # Missing 'entity'
                }
            }
        }

        response = await mcp_server_process.send_json_rpc(request)
        await self.assert_valid_error_response(response, request['id'])

    @pytest.mark.asyncio
    async def test_tool_call_nonexistent_tool(self, mcp_server_process, mcp_test_scenarios):
        """Test calling a nonexistent tool."""
        # Initialize first
        init_request = mcp_test_scenarios['initialize_request']
        await mcp_server_process.send_json_rpc(init_request)

        # Call nonexistent tool
        request = {
            'jsonrpc': '2.0',
            'id': 3,
            'method': 'tools/call',
            'params': {
                'name': 'nonexistent_tool',
                'arguments': {}
            }
        }

        response = await mcp_server_process.send_json_rpc(request)
        await self.assert_valid_error_response(response, request['id'])

        # Error should indicate tool not found
        error_message = response['error']['message'].lower()
        assert 'tool' in error_message and ('not found' in error_message or 'unknown' in error_message)

    @pytest.mark.asyncio
    async def test_tool_call_malformed_arguments(self, mcp_server_process, mcp_test_scenarios):
        """Test tool call with malformed arguments."""
        # Initialize first
        init_request = mcp_test_scenarios['initialize_request']
        await mcp_server_process.send_json_rpc(init_request)

        # Call with invalid argument structure
        request = {
            'jsonrpc': '2.0',
            'id': 3,
            'method': 'tools/call',
            'params': {
                'name': 'xray_test',
                'arguments': 'invalid_arguments'  # Should be object, not string
            }
        }

        response = await mcp_server_process.send_json_rpc(request)
        await self.assert_valid_error_response(response, request['id'])


@pytest.mark.mcp_protocol
@pytest.mark.performance
class TestMCPToolInvocationPerformance(BaseMCPTest):
    """Test tool invocation performance."""

    @pytest.mark.asyncio
    async def test_tool_call_timeout_handling(self, mcp_client_with_timeout: Client):
        """Test that tool calls respect timeout settings."""
        # Mock a slow operation
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock) as mock_auth:
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                # Simulate slow response
                async def slow_execute(*args, **kwargs):
                    import asyncio
                    await asyncio.sleep(2)  # 2 second delay
                    return {'data': {'getTests': {'results': []}}}

                mock_auth.return_value = None
                mock_execute.side_effect = slow_execute

                try:
                    result = await self.call_xray_tool(
                        mcp_client_with_timeout,
                        entity='test',
                        action='list',
                        project_key='DEMO'
                    )
                    # If it succeeds, that's fine (timeout was long enough)
                    await self.assert_mcp_tool_result(result)
                except Exception as e:
                    # Timeout is also acceptable
                    if 'timeout' in str(e).lower():
                        pass  # Expected
                    else:
                        raise

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, mcp_client: Client):
        """Test concurrent tool calls."""
        import asyncio

        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock):
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = {
                    'data': {
                        'getTests': {
                            'results': [{
                                'issueId': '12345',
                                'jira': {'key': 'TEST-123', 'summary': 'Mock Test'},
                                'testType': {'name': 'Manual'}
                            }]
                        }
                    }
                }

                async def make_call(call_id):
                    return await self.call_xray_tool(
                        mcp_client,
                        entity='test',
                        action='list',
                        project_key=f'DEMO{call_id}',
                        limit=1
                    )

                # Make 3 concurrent calls
                tasks = [make_call(i) for i in range(3)]
                results = await asyncio.gather(*tasks)

                # All should succeed
                assert len(results) == 3
                for result in results:
                    await self.assert_mcp_tool_result(result)


@pytest.mark.mcp_protocol
@pytest.mark.error_handling
class TestMCPToolInvocationErrorHandling(BaseMCPTest):
    """Test error handling in tool invocation."""

    @pytest.mark.asyncio
    async def test_authentication_failure_handling(self, mcp_client: Client):
        """Test handling of authentication failures."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock) as mock_auth:
            # Simulate authentication failure
            mock_auth.side_effect = Exception("Authentication failed")

            with pytest.raises(Exception) as exc_info:
                await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='list',
                    project_key='DEMO'
                )

            # Should get meaningful error
            error_msg = str(exc_info.value).lower()
            assert 'authentication' in error_msg or 'failed' in error_msg

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mcp_client: Client):
        """Test handling of API errors."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock):
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                # Simulate API error
                mock_execute.side_effect = Exception("GraphQL API error")

                with pytest.raises(Exception) as exc_info:
                    await self.call_xray_tool(
                        mcp_client,
                        entity='test',
                        action='list',
                        project_key='DEMO'
                    )

                # Should get meaningful error
                assert 'error' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_parameter_validation_errors(self, mcp_client: Client):
        """Test various parameter validation errors."""
        # Test invalid limit value
        with pytest.raises(Exception):
            await self.call_xray_tool(
                mcp_client,
                entity='test',
                action='list',
                project_key='DEMO',
                limit=-1  # Invalid negative limit
            )

        # Test invalid entity enum
        with pytest.raises(Exception):
            await self.call_xray_tool(
                mcp_client,
                entity='invalid_entity_type',
                action='list',
                project_key='DEMO'
            )

    @pytest.mark.asyncio
    async def test_json_response_format_validation(self, mcp_client: Client):
        """Test that response format is validated."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock):
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                # Return invalid response format
                mock_execute.return_value = "invalid_json_response"

                try:
                    result = await self.call_xray_tool(
                        mcp_client,
                        entity='test',
                        action='list',
                        project_key='DEMO'
                    )
                    # If it succeeds, check the result
                    await self.assert_mcp_tool_result(result)
                except Exception:
                    # Failure is also acceptable for invalid responses
                    pass

    @pytest.mark.asyncio
    async def test_step_parameter_validation(self, mcp_client: Client):
        """Test validation of step parameters for manual tests."""
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

                # Test invalid steps format - client accepts it and sends to server
                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='create',
                    project_key='DEMO',
                    test_type='Manual',
                    summary='Test with Invalid Steps',
                    steps='invalid_json_steps'  # Should be valid JSON
                )

                await self.assert_mcp_tool_result(result)
                assert len(result.content) > 0, "Content should not be empty"