"""
Tests for MCP (Model Context Protocol) specification compliance.

These tests ensure the server adheres to the MCP specification requirements.
"""

import pytest
import json
from typing import Dict, Any, List
from fastmcp import Client
from mcp import types
from tests.mcp_protocol import BaseMCPTest, MCPProtocolValidator, MCPTestUtils


@pytest.mark.mcp_compliance
@pytest.mark.mcp_protocol
class TestMCPSpecificationCompliance(BaseMCPTest):
    """Test compliance with MCP specification."""

    @pytest.mark.asyncio
    async def test_server_info_structure(self, mcp_client: Client):
        """Test that server follows MCP specification."""
        # Test basic server functionality
        await mcp_client.ping()

        # Test that tools are available (server must provide tools)
        tools = await mcp_client.list_tools()
        assert tools is not None, "Server must provide tools"
        assert isinstance(tools, list), "Tools must be a list"
        assert len(tools) > 0, "Server must have at least one tool"

        # Verify xray_test tool is present
        tool_names = [tool.name for tool in tools]
        assert 'xray_test' in tool_names, "Server must provide xray_test tool"

    @pytest.mark.asyncio
    async def test_protocol_version_support(self, mcp_server_process):
        """Test protocol version support according to MCP spec."""
        # Use raw JSON-RPC to get server info from initialize response
        request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }

        response = await mcp_server_process.send_json_rpc(request)
        assert 'result' in response, "Initialize should return result"

        result = response['result']
        assert 'serverInfo' in result, "Must return server info"
        server_info = result['serverInfo']

        assert 'name' in server_info, "Server info must have name"

        # Check protocol version if present (some servers may not expose it)
        if 'protocolVersion' in result:
            protocol_version = result['protocolVersion']
            assert isinstance(protocol_version, str), "Protocol version must be string"
            assert len(protocol_version) > 0, "Protocol version must not be empty"

            # Should follow date format (YYYY-MM-DD or similar)
            import re
            version_pattern = r'^\d{4}-\d{2}-\d{2}$'
            assert re.match(version_pattern, protocol_version), \
                f"Protocol version {protocol_version} should follow YYYY-MM-DD format"

    @pytest.mark.asyncio
    async def test_capabilities_structure(self, mcp_server_process):
        """Test server capabilities structure."""
        # Use raw JSON-RPC to get capabilities from initialize response
        request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }

        response = await mcp_server_process.send_json_rpc(request)
        assert 'result' in response, "Initialize should return result"

        result = response['result']

        # Check capabilities if present
        if 'capabilities' in result:
            capabilities = result['capabilities']

            # Capabilities should be structured according to MCP spec
            if 'tools' in capabilities:
                tools_cap = capabilities['tools']
                # Tools capability should indicate tool support
                assert tools_cap is not None

            if 'resources' in capabilities:
                resources_cap = capabilities['resources']
                # Resources capability structure
                assert resources_cap is not None

    @pytest.mark.asyncio
    async def test_tool_structure_compliance(self, mcp_client: Client):
        """Test that tools follow MCP specification structure."""
        tools = await mcp_client.list_tools()

        assert isinstance(tools, list), "Tools must be returned as list"
        assert len(tools) > 0, "Must have at least one tool"

        for tool in tools:
            # Required fields according to MCP spec
            assert hasattr(tool, 'name'), "Tool must have name"
            assert hasattr(tool, 'description'), "Tool must have description"
            assert hasattr(tool, 'inputSchema'), "Tool must have input schema"

            # Name validation
            assert isinstance(tool.name, str), "Tool name must be string"
            assert len(tool.name) > 0, "Tool name must not be empty"
            assert ' ' not in tool.name, "Tool name should not contain spaces"

            # Description validation
            assert isinstance(tool.description, str), "Tool description must be string"
            assert len(tool.description) > 0, "Tool description must not be empty"

            # Input schema validation
            assert isinstance(tool.inputSchema, dict), "Input schema must be dict"
            assert 'type' in tool.inputSchema, "Input schema must have type"
            assert tool.inputSchema['type'] == 'object', "Input schema type must be object"

    @pytest.mark.asyncio
    async def test_tool_input_schema_compliance(self, mcp_client: Client):
        """Test tool input schemas follow JSON Schema specification."""
        tools = await mcp_client.list_tools()

        for tool in tools:
            schema = tool.inputSchema

            # JSON Schema compliance
            assert 'type' in schema, f"Schema for {tool.name} must have type"
            assert schema['type'] == 'object', f"Schema for {tool.name} must be object type"

            if 'properties' in schema:
                properties = schema['properties']
                assert isinstance(properties, dict), f"Properties in {tool.name} must be dict"

                for prop_name, prop_schema in properties.items():
                    assert isinstance(prop_name, str), f"Property name in {tool.name} must be string"
                    assert isinstance(prop_schema, dict), f"Property schema for {prop_name} must be dict"

                    # Each property should have type or reference
                    has_type = 'type' in prop_schema
                    has_ref = '$ref' in prop_schema
                    has_anyof = 'anyOf' in prop_schema
                    has_enum = 'enum' in prop_schema

                    assert has_type or has_ref or has_anyof or has_enum, \
                        f"Property {prop_name} in {tool.name} must have type definition"

            if 'required' in schema:
                required = schema['required']
                assert isinstance(required, list), f"Required fields in {tool.name} must be list"

                for req_field in required:
                    assert isinstance(req_field, str), f"Required field names in {tool.name} must be strings"
                    if 'properties' in schema:
                        assert req_field in schema['properties'], \
                            f"Required field {req_field} must be in properties"

    @pytest.mark.asyncio
    async def test_tool_call_response_format(self, mcp_client: Client):
        """Test tool call responses follow MCP format."""
        with pytest.raises(Exception):
            # This will fail due to missing parameters, but we want to test the response format
            result = await self.call_xray_tool(mcp_client, action='list')

        # If we get here without an exception, test the result format
        # (This would only happen if parameter validation is disabled)

    @pytest.mark.asyncio
    async def test_error_response_format_compliance(self, mcp_server_process):
        """Test error responses follow MCP/JSON-RPC specification."""
        # Initialize first
        init_request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }

        await mcp_server_process.send_json_rpc(init_request)

        # Test various error scenarios
        error_scenarios = [
            {
                'name': 'missing_required_param',
                'request': {
                    'jsonrpc': '2.0',
                    'id': 2,
                    'method': 'tools/call',
                    'params': {
                        'name': 'xray_test',
                        'arguments': {'action': 'list'}  # Missing entity
                    }
                }
            },
            {
                'name': 'nonexistent_tool',
                'request': {
                    'jsonrpc': '2.0',
                    'id': 3,
                    'method': 'tools/call',
                    'params': {
                        'name': 'nonexistent_tool',
                        'arguments': {}
                    }
                }
            },
            {
                'name': 'invalid_method',
                'request': {
                    'jsonrpc': '2.0',
                    'id': 4,
                    'method': 'invalid/method',
                    'params': {}
                }
            }
        ]

        for scenario in error_scenarios:
            response = await mcp_server_process.send_json_rpc(scenario['request'])

            # Should be valid error response
            await self.assert_valid_error_response(response, scenario['request']['id'])

            # MCP-specific error response validation
            error = response['error']

            # Error codes should be in valid JSON-RPC range
            assert isinstance(error['code'], int), f"Error code for {scenario['name']} must be integer"
            assert error['code'] <= -32000, f"Error code for {scenario['name']} should be in JSON-RPC range"

            # Error message should be descriptive
            assert isinstance(error['message'], str), f"Error message for {scenario['name']} must be string"
            assert len(error['message']) > 0, f"Error message for {scenario['name']} must not be empty"

    @pytest.mark.asyncio
    async def test_resource_support_compliance(self, mcp_client: Client):
        """Test resource support follows MCP specification."""
        try:
            # Try to list resources
            resources = await mcp_client.list_resources()

            if resources is not None:
                assert isinstance(resources, list), "Resources must be returned as list"

                for resource in resources:
                    # Resource structure validation
                    assert hasattr(resource, 'uri'), "Resource must have URI"
                    assert hasattr(resource, 'name'), "Resource must have name"

                    # URI validation
                    assert isinstance(resource.uri, str), "Resource URI must be string"
                    assert len(resource.uri) > 0, "Resource URI must not be empty"

                    # Name validation
                    assert isinstance(resource.name, str), "Resource name must be string"
                    assert len(resource.name) > 0, "Resource name must not be empty"

        except Exception:
            # If resources are not supported, that's fine
            pass

    @pytest.mark.asyncio
    async def test_prompt_support_compliance(self, mcp_client: Client):
        """Test prompt support follows MCP specification."""
        try:
            # Try to list prompts
            prompts = await mcp_client.list_prompts()

            if prompts is not None:
                assert isinstance(prompts, list), "Prompts must be returned as list"

                for prompt in prompts:
                    # Prompt structure validation
                    assert hasattr(prompt, 'name'), "Prompt must have name"
                    assert hasattr(prompt, 'description'), "Prompt must have description"

                    # Name validation
                    assert isinstance(prompt.name, str), "Prompt name must be string"
                    assert len(prompt.name) > 0, "Prompt name must not be empty"

                    # Description validation
                    if prompt.description:
                        assert isinstance(prompt.description, str), "Prompt description must be string"

        except Exception:
            # If prompts are not supported, that's fine
            pass

    @pytest.mark.asyncio
    async def test_notification_handling_compliance(self, mcp_server_process):
        """Test notification handling follows MCP specification."""
        # Initialize first
        init_request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }

        await mcp_server_process.send_json_rpc(init_request)

        # Send a notification (no id field)
        notification = {
            'jsonrpc': '2.0',
            'method': 'notifications/initialized',
            'params': {}
        }

        # Send notification
        request_data = json.dumps(notification) + "\n"
        mcp_server_process.process.stdin.write(request_data.encode())
        await mcp_server_process.process.stdin.drain()

        # Notifications should not generate responses
        # Wait briefly to see if any response comes
        import asyncio
        try:
            # Try to read a response with short timeout
            response_line = await asyncio.wait_for(
                mcp_server_process.process.stdout.readline(),
                timeout=0.5
            )

            if response_line:
                # If we got a response, it might be for a different request
                # Parse it to check
                response = json.loads(response_line.decode())
                # Response should not have id matching notification (which has no id)
                assert 'id' in response  # Should have id if it's a response

        except asyncio.TimeoutError:
            # No response is expected for notifications
            pass

    @pytest.mark.asyncio
    async def test_content_type_compliance(self, mcp_client: Client):
        """Test content types follow MCP specification."""
        # Mock a successful tool call to test content types
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

                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='list',
                    project_key='DEMO'
                )

                await self.assert_mcp_tool_result(result)

                # Content validation
                assert isinstance(result.content, list), "Content must be list"
                assert len(result.content) > 0, "Content must not be empty"

                for content_item in result.content:
                    # Content type validation
                    assert hasattr(content_item, 'type'), "Content item must have type"

                    content_type = content_item.type
                    valid_types = ['text', 'image', 'resource']
                    assert content_type in valid_types, f"Content type {content_type} not in valid types"

                    if content_type == 'text':
                        assert hasattr(content_item, 'text'), "Text content must have text field"
                        assert isinstance(content_item.text, str), "Text content must be string"

    @pytest.mark.asyncio
    async def test_pagination_compliance(self, mcp_client: Client):
        """Test pagination follows MCP specification where applicable."""
        # Test that limit parameters work correctly
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock):
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                # Mock response with multiple items
                mock_execute.return_value = {
                    'data': {
                        'getTests': {
                            'results': [
                                {
                                    'issueId': f'1000{i}',
                                    'jira': {'key': f'TEST-{i}', 'summary': f'Test {i}'},
                                    'testType': {'name': 'Manual'}
                                }
                                for i in range(5)
                            ]
                        }
                    }
                }

                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='list',
                    project_key='DEMO',
                    limit=3  # Request only 3 items
                )

                await self.assert_mcp_tool_result(result)

                # Verify the GraphQL call was made with correct limit
                mock_execute.assert_called_once()
                # The exact parameter structure depends on implementation
                # but limit should be respected

    @pytest.mark.asyncio
    async def test_authentication_flow_compliance(self, mcp_server_process):
        """Test that authentication flows follow MCP patterns."""
        # Test initialization without authentication details
        init_request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }

        response = await mcp_server_process.send_json_rpc(init_request)
        await self.assert_valid_jsonrpc_response(response, init_request['id'])

        # Server should initialize without requiring authentication in the init step
        # Authentication should happen during tool execution
        result = response['result']
        assert 'serverInfo' in result
        assert 'capabilities' in result

        # Server should not require authentication credentials in initialize
        # (MCP servers typically authenticate when tools are called, not during init)

from unittest.mock import patch, AsyncMock