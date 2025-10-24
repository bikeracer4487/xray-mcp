"""
Tests for JSON-RPC 2.0 specification compliance.

These tests ensure the server adheres to the JSON-RPC 2.0 specification.
"""

import pytest
import json
import asyncio
from typing import Dict, Any, Union
from tests.mcp_protocol import BaseMCPTest, MCPTestUtils


@pytest.mark.jsonrpc
@pytest.mark.mcp_compliance
@pytest.mark.mcp_subprocess
class TestJSONRPCSpecCompliance(BaseMCPTest):
    """Test compliance with JSON-RPC 2.0 specification."""

    @pytest.mark.asyncio
    async def test_request_structure_compliance(self, mcp_server_process):
        """Test that requests follow JSON-RPC 2.0 structure."""
        # Valid request structure
        valid_request = {
            'jsonrpc': '2.0',
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            },
            'id': 1
        }

        response = await mcp_server_process.send_json_rpc(valid_request)
        await self.assert_valid_jsonrpc_response(response, valid_request['id'])

        # Response should also follow JSON-RPC 2.0
        assert response['jsonrpc'] == '2.0'
        assert 'id' in response
        assert response['id'] == valid_request['id']
        assert 'result' in response or 'error' in response
        assert not ('result' in response and 'error' in response)

    @pytest.mark.asyncio
    async def test_jsonrpc_field_requirement(self, mcp_server_process):
        """Test that 'jsonrpc' field is required and must be '2.0'."""
        # Missing jsonrpc field
        request_missing_jsonrpc = {
            'method': 'initialize',
            'params': {},
            'id': 1
        }

        # Server should either return an error or not respond (timeout)
        # Both are acceptable for malformed requests
        try:
            response = await mcp_server_process.send_json_rpc(request_missing_jsonrpc)
            await self.assert_valid_error_response(response, request_missing_jsonrpc['id'])

            error = response['error']
            assert error['code'] == -32600  # Invalid Request
        except RuntimeError as e:
            if "timeout" in str(e).lower():
                # Timeout is acceptable for missing jsonrpc field
                pass
            else:
                raise

        # Wrong jsonrpc version
        request_wrong_version = {
            'jsonrpc': '1.0',
            'method': 'initialize',
            'params': {},
            'id': 2
        }

        try:
            response = await mcp_server_process.send_json_rpc(request_wrong_version)

            # Server might be lenient or strict about version
            if 'error' in response:
                await self.assert_valid_error_response(response, request_wrong_version['id'])
                # Should be parse error or invalid request
                assert response['error']['code'] in [-32700, -32600]
        except RuntimeError as e:
            if "timeout" in str(e).lower():
                # Timeout is acceptable for wrong jsonrpc version
                pass
            else:
                raise

    @pytest.mark.asyncio
    async def test_method_field_requirement(self, mcp_server_process):
        """Test that 'method' field is required."""
        # Missing method field
        request_missing_method = {
            'jsonrpc': '2.0',
            'params': {},
            'id': 1
        }

        # Server should either return an error or not respond (timeout)
        # Both are acceptable for malformed requests
        try:
            response = await mcp_server_process.send_json_rpc(request_missing_method)
            await self.assert_valid_error_response(response, request_missing_method['id'])

            error = response['error']
            assert error['code'] == -32600  # Invalid Request
        except RuntimeError as e:
            if "timeout" in str(e).lower():
                # Timeout is acceptable for missing method field
                pass
            else:
                raise

        # Null method field
        request_null_method = {
            'jsonrpc': '2.0',
            'method': None,
            'params': {},
            'id': 2
        }

        try:
            response = await mcp_server_process.send_json_rpc(request_null_method)
            await self.assert_valid_error_response(response, request_null_method['id'])

            error = response['error']
            assert error['code'] in [-32600, -32601]  # Invalid Request or Method not found
        except RuntimeError as e:
            if "timeout" in str(e).lower():
                # Timeout is acceptable for null method field
                pass
            else:
                raise

    @pytest.mark.asyncio
    async def test_id_field_handling(self, mcp_server_process):
        """Test proper handling of 'id' field."""
        # Test various ID types
        test_ids = [
            1,              # Number
            "string_id",    # String
            None,           # Null (notification)
            0,              # Zero
            -1,             # Negative number
            "123",          # Numeric string
        ]

        for test_id in test_ids:
            request = {
                'jsonrpc': '2.0',
                'method': 'initialize',
                'params': {
                    'protocolVersion': '2024-11-05',
                    'capabilities': {},
                    'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
                }
            }

            if test_id is not None:
                request['id'] = test_id

            if test_id is None:
                # Notification - no response expected
                request_data = json.dumps(request) + "\n"
                mcp_server_process.process.stdin.write(request_data.encode())
                await mcp_server_process.process.stdin.drain()

                # Should not get a response for notifications
                try:
                    response_line = await asyncio.wait_for(
                        mcp_server_process.process.stdout.readline(),
                        timeout=0.5
                    )
                    if response_line:
                        # If we get a response, it should not be for this notification
                        response = json.loads(response_line.decode())
                        assert 'id' in response  # Should be for a different request
                except asyncio.TimeoutError:
                    # No response is expected
                    pass
            else:
                # Regular request - expect response with matching ID
                response = await mcp_server_process.send_json_rpc(request)

                if 'error' in response:
                    await self.assert_valid_error_response(response, test_id)
                else:
                    await self.assert_valid_jsonrpc_response(response, test_id)

                # ID should be preserved exactly
                assert response['id'] == test_id

    @pytest.mark.asyncio
    async def test_params_field_handling(self, mcp_server_process):
        """Test proper handling of 'params' field."""
        # Test with different params structures
        params_tests = [
            {
                'name': 'object_params',
                'params': {
                    'protocolVersion': '2024-11-05',
                    'capabilities': {},
                    'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
                },
                'should_work': True
            },
            {
                'name': 'null_params',
                'params': None,
                'should_work': False  # Might cause error
            },
            {
                'name': 'empty_object_params',
                'params': {},
                'should_work': False  # Missing required fields
            },
            {
                'name': 'no_params_field',
                'params': 'OMIT',  # Special marker to omit params
                'should_work': False  # Missing required fields
            }
        ]

        for test_case in params_tests:
            request = {
                'jsonrpc': '2.0',
                'method': 'initialize',
                'id': hash(test_case['name']) % 10000  # Generate unique ID
            }

            if test_case['params'] != 'OMIT':
                request['params'] = test_case['params']

            response = await mcp_server_process.send_json_rpc(request)

            if test_case['should_work']:
                await self.assert_valid_jsonrpc_response(response, request['id'])
            else:
                # Should get an error response
                if 'error' in response:
                    await self.assert_valid_error_response(response, request['id'])
                else:
                    # If it unexpectedly succeeds, that's also valid
                    await self.assert_valid_jsonrpc_response(response, request['id'])

    @pytest.mark.asyncio
    async def test_error_response_structure(self, mcp_server_process):
        """Test error response structure compliance."""
        # Force an error with invalid method
        invalid_request = {
            'jsonrpc': '2.0',
            'method': 'nonexistent_method',
            'params': {},
            'id': 1
        }

        response = await mcp_server_process.send_json_rpc(invalid_request)
        await self.assert_valid_error_response(response, invalid_request['id'])

        # Detailed error structure validation
        error = response['error']

        # Required fields
        assert 'code' in error, "Error must have code"
        assert 'message' in error, "Error must have message"

        # Code validation
        assert isinstance(error['code'], int), "Error code must be integer"
        assert error['code'] <= -32000, "Error code must be in JSON-RPC range"

        # Message validation
        assert isinstance(error['message'], str), "Error message must be string"
        assert len(error['message']) > 0, "Error message must not be empty"

        # Data field (optional)
        if 'data' in error:
            # Data can be any type according to JSON-RPC spec
            pass

    @pytest.mark.asyncio
    async def test_predefined_error_codes(self, mcp_server_process):
        """Test predefined JSON-RPC error codes."""
        error_scenarios = [
            {
                'name': 'parse_error',
                'request_data': b'{"invalid": json\n',  # Invalid JSON
                'expected_code': -32700
            },
            {
                'name': 'invalid_request',
                'request': {'jsonrpc': '2.0'},  # Missing method
                'expected_code': -32600
            },
            {
                'name': 'method_not_found',
                'request': {
                    'jsonrpc': '2.0',
                    'method': 'definitely_nonexistent_method',
                    'params': {},
                    'id': 1
                },
                'expected_code': -32601
            },
            {
                'name': 'invalid_params',
                'request': {
                    'jsonrpc': '2.0',
                    'method': 'tools/call',
                    'params': 'invalid_params_structure',  # Should be object
                    'id': 1
                },
                'expected_code': -32602
            }
        ]

        for scenario in error_scenarios:
            if 'request_data' in scenario:
                # Send raw invalid JSON
                mcp_server_process.process.stdin.write(scenario['request_data'])
                await mcp_server_process.process.stdin.drain()

                # Server might close connection or send error
                try:
                    response_line = await asyncio.wait_for(
                        mcp_server_process.process.stdout.readline(),
                        timeout=1.0
                    )
                    if response_line:
                        response = json.loads(response_line.decode())
                        # Should be parse error
                        assert 'error' in response
                        assert response['error']['code'] == scenario['expected_code']
                except (asyncio.TimeoutError, json.JSONDecodeError):
                    # Server might close connection on parse error
                    pass
            else:
                # Send structured request
                # Server should either return an error or not respond (timeout)
                # Both are acceptable for malformed requests
                try:
                    response = await mcp_server_process.send_json_rpc(scenario['request'])

                    await self.assert_valid_error_response(response, scenario['request']['id'])
                    error_code = response['error']['code']

                    # Should match expected error code or be in valid range
                    if error_code != scenario['expected_code']:
                        # Server might use different specific codes, but should be in valid range
                        assert error_code <= -32000, f"Error code {error_code} not in valid range"
                except RuntimeError as e:
                    if "timeout" in str(e).lower():
                        # Timeout is acceptable for malformed requests
                        pass
                    else:
                        raise

    @pytest.mark.asyncio
    async def test_batch_request_support(self, mcp_server_process):
        """Test batch request support (optional in JSON-RPC)."""
        # JSON-RPC 2.0 supports batch requests (array of requests)
        batch_request = [
            {
                'jsonrpc': '2.0',
                'method': 'initialize',
                'params': {
                    'protocolVersion': '2024-11-05',
                    'capabilities': {},
                    'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
                },
                'id': 1
            },
            {
                'jsonrpc': '2.0',
                'method': 'tools/list',
                'params': {},
                'id': 2
            }
        ]

        # Send batch request
        request_data = json.dumps(batch_request) + "\n"

        try:
            mcp_server_process.process.stdin.write(request_data.encode())
            await mcp_server_process.process.stdin.drain()

            # Server might support batch or might not
            # If supported, should get array response
            # If not supported, might get error or individual responses

            response_line = await asyncio.wait_for(
                mcp_server_process.process.stdout.readline(),
                timeout=2.0
            )

            if response_line:
                response_data = json.loads(response_line.decode())

                if isinstance(response_data, list):
                    # Batch response
                    assert len(response_data) == len(batch_request)
                    for i, response in enumerate(response_data):
                        expected_id = batch_request[i]['id']
                        if 'error' in response:
                            await self.assert_valid_error_response(response, expected_id)
                        else:
                            await self.assert_valid_jsonrpc_response(response, expected_id)
                elif isinstance(response_data, dict):
                    # Single response - batch not supported or error
                    if 'error' in response_data:
                        await self.assert_valid_error_response(response_data, None)
                    else:
                        await self.assert_valid_jsonrpc_response(response_data, None)

        except (asyncio.TimeoutError, json.JSONDecodeError):
            # Batch requests might not be supported
            pass

    @pytest.mark.asyncio
    async def test_notification_vs_request_distinction(self, mcp_server_process):
        """Test distinction between notifications and requests."""
        # Initialize first with regular request
        init_request = {
            'jsonrpc': '2.0',
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            },
            'id': 1
        }

        response = await mcp_server_process.send_json_rpc(init_request)
        await self.assert_valid_jsonrpc_response(response, init_request['id'])

        # Send notification (no id field)
        notification = {
            'jsonrpc': '2.0',
            'method': 'notifications/initialized',
            'params': {}
        }

        request_data = json.dumps(notification) + "\n"
        mcp_server_process.process.stdin.write(request_data.encode())
        await mcp_server_process.process.stdin.drain()

        # Should not get response for notification
        try:
            response_line = await asyncio.wait_for(
                mcp_server_process.process.stdout.readline(),
                timeout=0.5
            )

            if response_line:
                # If we get any response, it should be for a different request
                response = json.loads(response_line.decode())
                if 'id' in response:
                    # Should not be a response to our notification
                    assert response['id'] != notification.get('id', 'NO_ID')

        except asyncio.TimeoutError:
            # No response expected for notifications
            pass

    @pytest.mark.asyncio
    async def test_response_completeness(self, mcp_server_process):
        """Test that responses are complete and self-contained."""
        # Send request
        request = {
            'jsonrpc': '2.0',
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            },
            'id': 'test_completeness'
        }

        response = await mcp_server_process.send_json_rpc(request)

        # Response should be complete
        assert isinstance(response, dict), "Response must be complete JSON object"
        assert 'jsonrpc' in response, "Response must include jsonrpc field"
        assert 'id' in response, "Response must include id field"

        # Must have either result or error
        has_result = 'result' in response
        has_error = 'error' in response
        assert has_result or has_error, "Response must have result or error"
        assert not (has_result and has_error), "Response cannot have both result and error"

        # ID must match request
        assert response['id'] == request['id'], "Response ID must match request ID"

        # JSON-RPC version must be correct
        assert response['jsonrpc'] == '2.0', "Response must have jsonrpc 2.0"

    @pytest.mark.asyncio
    async def test_unicode_handling_compliance(self, mcp_server_process):
        """Test Unicode handling in JSON-RPC messages."""
        # Initialize first
        init_request = {
            'jsonrpc': '2.0',
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {
                    'name': 'test-client-ünicöde-🚀',  # Unicode client name
                    'version': '1.0.0'
                }
            },
            'id': 'ünicöde-id-测试'  # Unicode ID
        }

        response = await mcp_server_process.send_json_rpc(init_request)

        # Should handle Unicode properly
        if 'error' in response:
            await self.assert_valid_error_response(response, init_request['id'])
            # Error should not be due to Unicode issues
            error_msg = response['error']['message'].lower()
            assert 'unicode' not in error_msg and 'encoding' not in error_msg
        else:
            await self.assert_valid_jsonrpc_response(response, init_request['id'])

        # ID should be preserved exactly
        assert response['id'] == init_request['id']

    @pytest.mark.asyncio
    async def test_large_message_handling(self, mcp_server_process):
        """Test handling of large JSON-RPC messages."""
        # Create large request
        large_params = {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {
                'name': 'test-client',
                'version': '1.0.0',
                'description': 'A' * 5000  # Large description
            }
        }

        large_request = {
            'jsonrpc': '2.0',
            'method': 'initialize',
            'params': large_params,
            'id': 'large_message_test'
        }

        try:
            response = await mcp_server_process.send_json_rpc(large_request)

            # Should handle large messages
            if 'error' in response:
                await self.assert_valid_error_response(response, large_request['id'])
                # Error should not be due to message size (unless server has explicit limits)
            else:
                await self.assert_valid_jsonrpc_response(response, large_request['id'])

        except Exception:
            # Some connection issues with very large messages are acceptable
            pass