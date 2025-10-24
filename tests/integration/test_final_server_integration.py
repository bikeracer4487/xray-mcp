"""Integration tests for the final simplified server."""

import pytest
import os
from dotenv import load_dotenv
from src.server import create_server
from tests.integration.test_helpers import parse_mcp_response

load_dotenv()


class TestFinalServerIntegration:
    """Integration tests for the final simplified server."""

    @pytest.fixture
    def server(self):
        """Create server instance."""
        return create_server()

    def test_server_has_single_tool(self, server):
        """Test that server has exactly one tool registered."""
        tools = []
        if hasattr(server, '_tool_manager') and server._tool_manager:
            tools = list(server._tool_manager._tools.keys())

        assert len(tools) == 1, f"Expected 1 tool, got {len(tools)}: {tools}"
        assert 'xray_test' in tools, f"xray_test not found in tools: {tools}"

    def test_tool_schema_completeness(self, server):
        """Test that the tool has comprehensive parameters."""
        tool = server._tool_manager._tools['xray_test']
        schema = tool.parameters
        properties = schema.get('properties', {})

        # Core required parameters
        assert 'entity' in properties, "Missing entity parameter"
        assert 'action' in properties, "Missing action parameter"

        # Check entity enum values
        entity_schema = properties['entity']
        valid_entities = []
        if 'enum' in entity_schema:
            valid_entities = entity_schema['enum']
        elif 'anyOf' in entity_schema:
            for option in entity_schema['anyOf']:
                if 'enum' in option:
                    valid_entities.extend(option['enum'])

        expected_entities = ['test', 'test_execution', 'test_plan', 'test_run']
        for entity in expected_entities:
            assert entity in valid_entities, f"Missing entity: {entity}"

        # Optional parameters should be comprehensive
        optional_params = [
            'issue_id', 'project_key', 'summary', 'test_type', 'test_issue_ids',
            'limit', 'start', 'jql', 'description', 'steps', 'gherkin',
            'status', 'comment', 'test_environments', 'test_execution_id',
            'defects', 'environments', 'id'
        ]

        for param in optional_params:
            assert param in properties, f"Missing optional parameter: {param}"

    @pytest.mark.asyncio
    async def test_tool_validation(self, server):
        """Test that tool properly validates parameters."""
        tool = server._tool_manager._tools['xray_test']

        # Test missing required parameter
        with pytest.raises(Exception) as exc_info:
            await tool.run({'action': 'list'})  # Missing entity

        error_str = str(exc_info.value)
        assert 'entity' in error_str, "Should complain about missing entity"

    @pytest.mark.asyncio
    async def test_basic_functionality(self, server):
        """Test basic functionality works."""
        tool = server._tool_manager._tools['xray_test']

        # Test list operation
        result = await tool.run({
            'entity': 'test',
            'action': 'list',
            'project_key': 'DEMO',
            'limit': 5
        })

        assert isinstance(result, list), "Should return list"
        assert len(result) > 0, "Should have content"

        # Parse JSON response
        import json
        data = parse_mcp_response(result)

        assert 'success' in data, "Should have success field"
        assert 'data' in data, "Should have data field"
        assert 'warnings' in data, "Should have warnings field"
        assert 'errors' in data, "Should have errors field"

    @pytest.mark.asyncio
    async def test_all_entities_accessible(self, server):
        """Test that all entities are accessible through the tool."""
        tool = server._tool_manager._tools['xray_test']
        entities = ['test', 'test_execution', 'test_plan', 'test_run']

        for entity in entities:
            # Test that each entity can be accessed (may fail due to missing params, but shouldn't fail on entity)
            try:
                result = await tool.run({
                    'entity': entity,
                    'action': 'list',
                    'project_key': 'DEMO'
                })
                # Should get a result, even if it's an error about missing parameters
                assert isinstance(result, list), f"Entity {entity} should return list"
            except Exception as e:
                # Should not fail on unknown entity
                error_str = str(e)
                assert 'Invalid entity' not in error_str, f"Entity {entity} should be recognized"

    def test_server_description(self, server):
        """Test that server has proper description."""
        tool = server._tool_manager._tools['xray_test']
        assert hasattr(tool, 'description'), "Tool should have description"
        assert tool.description, "Tool description should not be empty"
        assert 'unified' in tool.description.lower() or 'manage' in tool.description.lower(), \
            "Description should indicate unified management"