"""Integration tests for simplified FastMCP server."""

import pytest
import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from src.server import create_server
from tests.integration.test_helpers import parse_mcp_response as create_simplified_server

load_dotenv()


class TestSimplifiedServerIntegration:
    """Integration tests for simplified FastMCP server."""

    @pytest.fixture
    def server(self):
        """Create simplified FastMCP server instance."""
        return create_simplified_server()

    def test_server_has_single_tool(self, server):
        """Test that simplified server has only one tool registered."""
        # Get tools from tool manager
        tools = []
        if hasattr(server, '_tool_manager') and server._tool_manager:
            tools = list(server._tool_manager._tools.keys())

        # Should have exactly one tool
        assert len(tools) == 1, f"Expected 1 tool, got {len(tools)}: {tools}"
        assert 'xray_test' in tools, f"xray_test not found in tools: {tools}"

    def test_tool_has_correct_schema(self, server):
        """Test that the xray_test tool has correct parameters."""
        tools = server._tool_manager._tools if hasattr(server, '_tool_manager') else {}
        assert 'xray_test' in tools

        tool = tools['xray_test']
        assert tool.description
        assert 'unified' in tool.description.lower() or 'manage' in tool.description.lower()

        # Check that parameters include core fields
        schema = tool.parameters
        assert 'properties' in schema
        properties = schema['properties']

        # Core parameters should be present
        assert 'entity' in properties
        assert 'action' in properties

        # Entity should have proper enum values
        entity_schema = properties['entity']
        assert 'enum' in entity_schema or 'anyOf' in entity_schema

        # Check if enum is directly available or in anyOf structure
        valid_entities = None
        if 'enum' in entity_schema:
            valid_entities = entity_schema['enum']
        elif 'anyOf' in entity_schema:
            # FastMCP might structure it differently
            for option in entity_schema['anyOf']:
                if 'enum' in option:
                    valid_entities = option['enum']
                    break

        if valid_entities:
            expected_entities = ['test', 'test_execution', 'test_plan', 'test_run']
            for expected in expected_entities:
                assert expected in valid_entities, f"Missing entity: {expected}"

    @pytest.mark.asyncio
    async def test_tool_execution_validation(self, server):
        """Test that tool properly validates parameters."""
        tools = server._tool_manager._tools if hasattr(server, '_tool_manager') else {}
        tool = tools['xray_test']

        # Test that missing required parameters fail validation
        with pytest.raises(Exception) as exc_info:
            await tool.run({'action': 'list'})  # Missing entity

        assert 'entity' in str(exc_info.value), "Should complain about missing entity"

    @pytest.mark.asyncio
    async def test_tool_execution_with_valid_params(self, server):
        """Test that tool executes with valid parameters."""
        tools = server._tool_manager._tools if hasattr(server, '_tool_manager') else {}
        tool = tools['xray_test']

        # This should work (though may fail at auth/network level)
        result = await tool.run({
            'entity': 'test',
            'action': 'list',
            'project_key': 'DEMO'
        })

        # Result should be a list of TextContent
        assert isinstance(result, list)
        assert len(result) > 0

        # First item should be TextContent with JSON
        content = result[0]
        assert hasattr(content, 'text')

        # Should be valid JSON with expected structure
        import json
        data = json.loads(content.text)
        assert 'success' in data
        assert 'data' in data
        assert 'warnings' in data
        assert 'errors' in data