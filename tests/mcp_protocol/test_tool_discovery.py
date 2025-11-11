"""
Tests for MCP tool discovery functionality.

Tests the tools/list operation and tool schema validation.
"""

import pytest
import json
from typing import Dict, Any, List
from fastmcp import Client
from mcp import types
from tests.mcp_protocol import BaseMCPTest, MCPProtocolValidator, MCPTestUtils


@pytest.mark.mcp_protocol
@pytest.mark.mcp_client
class TestMCPToolDiscovery(BaseMCPTest):
    """Test MCP tool discovery via FastMCP Client."""

    @pytest.mark.asyncio
    async def test_list_tools_basic(self, mcp_client: Client):
        """Test basic tools/list functionality."""
        tools = await mcp_client.list_tools()

        assert isinstance(tools, list), "Tools should be returned as a list"
        assert len(tools) > 0, "Should have at least one tool"

        # Check that xray_test tool is present
        tool_names = [tool.name for tool in tools]
        assert 'xray_test' in tool_names, f"xray_test tool not found in: {tool_names}"

    @pytest.mark.asyncio
    async def test_xray_tool_structure(self, mcp_client: Client):
        """Test that xray_test tool has correct structure."""
        await self.assert_xray_tool_available(mcp_client)

        tool = await self.get_tool_by_name(mcp_client, 'xray_test')

        # Validate tool metadata
        assert isinstance(tool.name, str), "Tool name should be string"
        assert isinstance(tool.description, str), "Tool description should be string"
        assert len(tool.description) > 10, "Tool description should be meaningful"

        # Validate input schema
        schema = tool.inputSchema
        assert schema['type'] == 'object', "Input schema should be object type"
        assert 'properties' in schema, "Schema should have properties"

        # Check required fields
        required_fields = schema.get('required', [])
        assert 'entity' in required_fields, "entity should be required"
        assert 'action' in required_fields, "action should be required"

    @pytest.mark.asyncio
    async def test_tool_parameter_schemas(self, mcp_client: Client):
        """Test detailed parameter schemas for xray_test tool."""
        tool = await self.get_tool_by_name(mcp_client, 'xray_test')
        properties = tool.inputSchema['properties']

        # Test entity parameter
        entity_param = properties['entity']
        assert 'enum' in entity_param or 'anyOf' in entity_param, \
            "Entity should have enum or anyOf with enum options"

        # Test action parameter
        action_param = properties['action']
        assert 'type' in action_param, "Action should have type"
        assert action_param['type'] == 'string', "Action should be string type"

        # Test optional parameters exist
        optional_params = [
            'issue_id', 'project_key', 'summary', 'test_type',
            'test_issue_ids', 'limit', 'start', 'jql'
        ]
        for param in optional_params:
            assert param in properties, f"Optional parameter {param} should be in schema"

        # Test array parameters have correct type
        array_params = ['test_issue_ids', 'test_environments', 'defects']
        for param in array_params:
            if param in properties:
                param_schema = properties[param]
                # Accept either direct 'type' field or 'anyOf' pattern
                if 'type' in param_schema:
                    assert param_schema['type'] == 'array', f"{param} should be array type"
                elif 'anyOf' in param_schema:
                    # Check if any of the anyOf options is an array type
                    has_array_option = any(
                        option.get('type') == 'array'
                        for option in param_schema['anyOf']
                    )
                    assert has_array_option, f"{param} should have array option in anyOf"
                else:
                    assert False, f"{param} should have type or anyOf definition"

    @pytest.mark.asyncio
    async def test_tool_schema_validation(self, mcp_client: Client):
        """Test that tool schemas are valid JSON Schema."""
        tools = await mcp_client.list_tools()

        for tool in tools:
            schema = tool.inputSchema

            # Basic JSON Schema validation
            assert 'type' in schema, f"Tool {tool.name} schema should have type"

            if schema['type'] == 'object':
                assert 'properties' in schema, f"Tool {tool.name} object schema should have properties"

                # Validate each property
                for prop_name, prop_schema in schema['properties'].items():
                    assert 'type' in prop_schema or 'anyOf' in prop_schema or 'enum' in prop_schema, \
                        f"Property {prop_name} in {tool.name} should have type definition"


@pytest.mark.mcp_protocol
@pytest.mark.mcp_subprocess
class TestMCPToolDiscoverySubprocess(BaseMCPTest):
    """Test tool discovery using subprocess communication."""

    @pytest.mark.asyncio
    async def test_raw_tools_list_request(self, mcp_server_process, mcp_test_scenarios):
        """Test raw tools/list request via JSON-RPC."""
        # First initialize
        init_request = mcp_test_scenarios['initialize_request']
        init_response = await mcp_server_process.send_json_rpc(init_request)
        await self.assert_valid_jsonrpc_response(init_response, init_request['id'])

        # Then list tools
        list_request = mcp_test_scenarios['list_tools_request']
        response = await mcp_server_process.send_json_rpc(list_request)

        await self.assert_valid_jsonrpc_response(response, list_request['id'])
        await MCPProtocolValidator.validate_tools_list_response(response)

        # Check xray_test tool is present
        tools = response['result']['tools']
        tool_names = [tool['name'] for tool in tools]
        assert 'xray_test' in tool_names, f"xray_test not found in {tool_names}"

    @pytest.mark.asyncio
    async def test_tools_list_without_initialize(self, mcp_server_process):
        """Test tools/list request without prior initialization."""
        request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/list',
            'params': {}
        }

        response = await mcp_server_process.send_json_rpc(request)

        # Server might require initialization first
        if 'error' in response:
            await self.assert_valid_error_response(response, request['id'])
            # Error should indicate initialization required
            error_message = response['error']['message'].lower()
            assert 'initialize' in error_message or 'not initialized' in error_message
        else:
            # Or server might allow it
            await self.assert_valid_jsonrpc_response(response, request['id'])
            await MCPProtocolValidator.validate_tools_list_response(response)

    @pytest.mark.asyncio
    async def test_tools_list_with_params(self, mcp_server_process, mcp_test_scenarios):
        """Test tools/list with various parameters."""
        # Initialize first
        init_request = mcp_test_scenarios['initialize_request']
        await mcp_server_process.send_json_rpc(init_request)

        # Test with empty params
        request = {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/list',
            'params': {}
        }

        response = await mcp_server_process.send_json_rpc(request)
        await self.assert_valid_jsonrpc_response(response, request['id'])

        # Test with null params
        request['id'] = 3
        request['params'] = None
        response = await mcp_server_process.send_json_rpc(request)

        # Should work or return appropriate error
        if 'error' in response:
            await self.assert_valid_error_response(response, request['id'])
        else:
            await self.assert_valid_jsonrpc_response(response, request['id'])

    @pytest.mark.asyncio
    async def test_malformed_tools_list_request(self, mcp_server_process, mcp_test_scenarios):
        """Test malformed tools/list requests."""
        # Initialize first
        init_request = mcp_test_scenarios['initialize_request']
        await mcp_server_process.send_json_rpc(init_request)

        # Missing params field entirely
        request = {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/list'
            # No params field
        }

        response = await mcp_server_process.send_json_rpc(request)

        # Should work (params is optional) or return appropriate error
        if 'error' in response:
            await self.assert_valid_error_response(response, request['id'])
        else:
            await self.assert_valid_jsonrpc_response(response, request['id'])


@pytest.mark.mcp_protocol
@pytest.mark.performance
class TestMCPToolDiscoveryPerformance(BaseMCPTest):
    """Test tool discovery performance."""

    @pytest.mark.asyncio
    async def test_tools_list_performance(self, mcp_client: Client, performance_timer):
        """Test that tools/list completes quickly."""
        with performance_timer("Tools List") as timer:
            tools = await mcp_client.list_tools()

        # Should complete within 1 second
        timer.assert_duration_under(1.0)
        assert len(tools) > 0

    @pytest.mark.asyncio
    async def test_repeated_tools_list(self, mcp_client: Client):
        """Test that repeated tools/list calls are consistent."""
        results = []

        for i in range(5):
            tools = await mcp_client.list_tools()
            tool_names = sorted([tool.name for tool in tools])
            results.append(tool_names)

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result, "Tools list should be consistent across calls"

    @pytest.mark.asyncio
    async def test_concurrent_tools_list(self, mcp_client: Client):
        """Test concurrent tools/list requests."""
        import asyncio

        async def get_tools():
            return await mcp_client.list_tools()

        # Make 3 concurrent requests
        tasks = [get_tools() for _ in range(3)]
        results = await asyncio.gather(*tasks)

        # All should succeed and return same results
        assert len(results) == 3
        first_names = sorted([tool.name for tool in results[0]])

        for result in results[1:]:
            names = sorted([tool.name for tool in result])
            assert names == first_names


@pytest.mark.mcp_protocol
@pytest.mark.edge_case
class TestMCPToolDiscoveryEdgeCases(BaseMCPTest):
    """Test edge cases in tool discovery."""

    @pytest.mark.asyncio
    async def test_tool_with_complex_schema(self, mcp_client: Client):
        """Test that tools with complex schemas are handled correctly."""
        tool = await self.get_tool_by_name(mcp_client, 'xray_test')
        schema = tool.inputSchema

        # Should handle nested schemas
        if 'properties' in schema:
            for prop_name, prop_schema in schema['properties'].items():
                if 'anyOf' in prop_schema:
                    # Validate anyOf structure
                    any_of = prop_schema['anyOf']
                    assert isinstance(any_of, list), f"anyOf in {prop_name} should be list"
                    assert len(any_of) > 0, f"anyOf in {prop_name} should not be empty"

                if 'items' in prop_schema:
                    # Array type validation
                    items = prop_schema['items']
                    assert isinstance(items, dict), f"items in {prop_name} should be dict"

    @pytest.mark.asyncio
    async def test_tool_description_content(self, mcp_client: Client):
        """Test that tool descriptions are informative."""
        tools = await mcp_client.list_tools()

        for tool in tools:
            description = tool.description

            # Should be meaningful length
            assert len(description) > 20, f"Tool {tool.name} description too short: {description}"

            # Should not be just the name
            assert description.lower() != tool.name.lower(), \
                f"Tool {tool.name} description should not just be the name"

            # Should contain useful keywords for xray_test
            if tool.name == 'xray_test':
                desc_lower = description.lower()
                useful_keywords = ['xray', 'test', 'manage', 'unified', 'execution', 'plan']
                has_keyword = any(keyword in desc_lower for keyword in useful_keywords)
                assert has_keyword, f"xray_test description should contain useful keywords: {description}"

    @pytest.mark.asyncio
    async def test_schema_required_vs_optional_parameters(self, mcp_client: Client):
        """Test distinction between required and optional parameters."""
        tool = await self.get_tool_by_name(mcp_client, 'xray_test')
        schema = tool.inputSchema

        required = set(schema.get('required', []))
        all_properties = set(schema.get('properties', {}).keys())
        optional = all_properties - required

        # Should have both required and optional parameters
        assert len(required) > 0, "Should have some required parameters"
        assert len(optional) > 0, "Should have some optional parameters"

        # Specific expectations for xray_test
        assert 'entity' in required, "entity should be required"
        assert 'action' in required, "action should be required"
        assert 'limit' in optional, "limit should be optional"
        assert 'start' in optional, "start should be optional"