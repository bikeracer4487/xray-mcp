"""Base classes and utilities for MCP protocol testing."""

import pytest
import asyncio
import json
from typing import Dict, Any, List, Optional
from fastmcp import Client
from mcp import types


class BaseMCPTest:
    """Base class for MCP protocol tests."""

    async def assert_valid_jsonrpc_response(self, response: Dict[str, Any], request_id: Any = None):
        """Assert that a response follows JSON-RPC 2.0 specification."""
        assert isinstance(response, dict), "Response must be a dictionary"
        assert response.get('jsonrpc') == '2.0', "Response must have jsonrpc: '2.0'"

        if request_id is not None:
            assert 'id' in response, "Response must have 'id' field"
            assert response['id'] == request_id, f"Response ID {response['id']} should match request ID {request_id}"

        # Response should have either 'result' or 'error', but not both
        has_result = 'result' in response
        has_error = 'error' in response
        assert has_result or has_error, "Response must have either 'result' or 'error'"
        assert not (has_result and has_error), "Response cannot have both 'result' and 'error'"

    async def assert_valid_error_response(self, response: Dict[str, Any], request_id: Any = None):
        """Assert that an error response follows JSON-RPC 2.0 specification."""
        await self.assert_valid_jsonrpc_response(response, request_id)

        assert 'error' in response, "Error response must have 'error' field"
        error = response['error']
        assert isinstance(error, dict), "Error must be a dictionary"
        assert 'code' in error, "Error must have 'code' field"
        assert 'message' in error, "Error must have 'message' field"
        assert isinstance(error['code'], int), "Error code must be an integer"
        assert isinstance(error['message'], str), "Error message must be a string"

    async def assert_mcp_tool_result(self, result: types.CallToolResult):
        """Assert that a tool result follows MCP specification."""
        assert isinstance(result, types.CallToolResult), "Result must be CallToolResult"
        assert hasattr(result, 'content'), "Result must have content"
        assert isinstance(result.content, list), "Content must be a list"
        assert len(result.content) > 0, "Content must not be empty"

        for content_item in result.content:
            assert hasattr(content_item, 'type'), "Content item must have type"

            if hasattr(content_item, 'text'):
                assert isinstance(content_item.text, str), "Text content must be string"

    async def send_initialize_request(self, client: Client) -> Dict[str, Any]:
        """Send initialize request and return response."""
        return await client.call('initialize', {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {
                'name': 'test-client',
                'version': '1.0.0'
            }
        })

    async def get_tool_by_name(self, client: Client, tool_name: str) -> Optional[types.Tool]:
        """Get a tool by name from the server."""
        tools = await client.list_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool
        return None

    async def assert_xray_tool_available(self, client: Client):
        """Assert that the xray_test tool is available and properly configured."""
        tool = await self.get_tool_by_name(client, 'xray_test')
        assert tool is not None, "xray_test tool should be available"
        assert tool.description, "Tool should have a description"
        assert 'unified' in tool.description.lower() or 'manage' in tool.description.lower(), \
            "Tool description should indicate unified management"

        # Validate input schema
        assert hasattr(tool, 'inputSchema'), "Tool should have input schema"
        schema = tool.inputSchema
        assert 'properties' in schema, "Schema should have properties"

        properties = schema['properties']
        assert 'entity' in properties, "Schema should require 'entity' parameter"
        assert 'action' in properties, "Schema should require 'action' parameter"

        # Check entity enum values
        entity_schema = properties['entity']
        if 'enum' in entity_schema:
            valid_entities = entity_schema['enum']
        elif 'anyOf' in entity_schema:
            # Handle complex schema structures
            valid_entities = []
            for option in entity_schema['anyOf']:
                if 'enum' in option:
                    valid_entities.extend(option['enum'])
        else:
            valid_entities = []

        expected_entities = ['test', 'test_execution', 'test_plan', 'test_run']
        for expected in expected_entities:
            assert expected in valid_entities, f"Entity '{expected}' should be in enum: {valid_entities}"

    async def call_xray_tool(self, client: Client, **kwargs) -> types.CallToolResult:
        """Call the xray_test tool with given parameters."""
        content = await client.call_tool('xray_test', kwargs)
        # FastMCP Client returns content directly, wrap it in CallToolResult
        return types.CallToolResult(content=content)

    async def mock_auth_success(self, mock_responses: Dict[str, Any]):
        """Helper to mock successful authentication."""
        return mock_responses['auth_success']

    async def mock_api_call(self, mock_responses: Dict[str, Any], response_key: str):
        """Helper to mock API calls."""
        return mock_responses.get(response_key, {})


class MCPProtocolValidator:
    """Validates MCP protocol compliance."""

    @staticmethod
    async def validate_initialize_response(response: Dict[str, Any]):
        """Validate initialize response structure."""
        assert 'result' in response, "Initialize should return result"
        result = response['result']

        assert 'protocolVersion' in result, "Result should have protocolVersion"
        assert 'capabilities' in result, "Result should have capabilities"
        assert 'serverInfo' in result, "Result should have serverInfo"

        server_info = result['serverInfo']
        assert 'name' in server_info, "Server info should have name"
        assert isinstance(server_info['name'], str), "Server name should be string"

    @staticmethod
    async def validate_tools_list_response(response: Dict[str, Any]):
        """Validate tools/list response structure."""
        assert 'result' in response, "Tools list should return result"
        result = response['result']

        assert 'tools' in result, "Result should have tools array"
        tools = result['tools']
        assert isinstance(tools, list), "Tools should be a list"

        for tool in tools:
            assert 'name' in tool, "Tool should have name"
            assert 'description' in tool, "Tool should have description"
            assert 'inputSchema' in tool, "Tool should have input schema"

            schema = tool['inputSchema']
            assert 'type' in schema, "Schema should have type"
            assert schema['type'] == 'object', "Schema type should be object"

    @staticmethod
    async def validate_tool_call_response(response: Dict[str, Any]):
        """Validate tools/call response structure."""
        assert 'result' in response, "Tool call should return result"
        result = response['result']

        assert 'content' in result, "Result should have content"
        content = result['content']
        assert isinstance(content, list), "Content should be a list"
        assert len(content) > 0, "Content should not be empty"

        for content_item in content:
            assert 'type' in content_item, "Content item should have type"
            if content_item['type'] == 'text':
                assert 'text' in content_item, "Text content should have text field"


class MCPTestUtils:
    """Utility functions for MCP testing."""

    @staticmethod
    def create_jsonrpc_request(method: str, params: Dict[str, Any] = None, request_id: int = 1) -> Dict[str, Any]:
        """Create a JSON-RPC 2.0 request."""
        request = {
            'jsonrpc': '2.0',
            'id': request_id,
            'method': method
        }
        if params is not None:
            request['params'] = params
        return request

    @staticmethod
    def create_tool_call_request(tool_name: str, arguments: Dict[str, Any], request_id: int = 1) -> Dict[str, Any]:
        """Create a tools/call request."""
        return MCPTestUtils.create_jsonrpc_request(
            'tools/call',
            {
                'name': tool_name,
                'arguments': arguments
            },
            request_id
        )

    @staticmethod
    async def wait_for_server_ready(client: Client, timeout: float = 10.0):
        """Wait for server to be ready for requests."""
        start_time = asyncio.get_event_loop().time()

        while True:
            try:
                await client.ping()
                return
            except Exception:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise TimeoutError(f"Server not ready after {timeout} seconds")
                await asyncio.sleep(0.1)