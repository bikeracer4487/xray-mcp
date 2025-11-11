"""End-to-end CRUD tests for Xray MCP server."""

import pytest
import os
import uuid
import json
from dotenv import load_dotenv
from src.server import create_server
from tests.integration.test_helpers import parse_mcp_response

load_dotenv()


@pytest.mark.skipif(
    not all([os.getenv('XRAY_CLIENT_ID'), os.getenv('XRAY_CLIENT_SECRET')]),
    reason="Xray credentials not available"
)
class TestEndToEndCRUD:
    """Test actual CRUD operations against live Xray API."""

    @pytest.fixture
    def server(self):
        """Create server instance."""
        return create_server()

    @pytest.fixture
    def tool(self, server):
        """Get the xray_test tool."""
        return server._tool_manager._tools['xray_test']

    @pytest.fixture
    def unique_prefix(self):
        """Generate unique prefix for test data."""
        return f"MCP-TEST-{uuid.uuid4().hex[:8]}"

    @pytest.mark.asyncio
    async def test_test_crud_operations(self, tool, unique_prefix):
        """Test complete CRUD cycle for tests."""
        project_key = os.getenv('DEFAULT_PROJECT_KEY', 'FTEST')  # Using project from env

        # 1. CREATE TEST
        create_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Test CRUD Operation',
            'test_type': 'Manual',
            'description': 'End-to-end CRUD test',
            'steps': '[{"action": "Click login", "data": "username field", "result": "Field selected"}, {"action": "Enter credentials", "data": "valid username", "result": "Username entered"}]'
        }

        create_result = await tool.run(create_params)
        assert isinstance(create_result, list), "Create should return list"

        create_data = parse_mcp_response(create_result)
        assert create_data['success'], f"Create failed: {create_data.get('errors')}"

        test_id = create_data['data']['issueId']
        test_key = create_data['data']['issueKey']
        print(f"✅ Created test: {test_key} ({test_id})")

        # 2. READ TEST
        get_params = {
            'entity': 'test',
            'action': 'get',
            'issue_id': test_id
        }

        get_result = await tool.run(get_params)
        get_data = parse_mcp_response(get_result)
        assert get_data['success'], f"Get failed: {get_data.get('errors')}"
        assert get_data['data']['issueId'] == test_id
        assert unique_prefix in get_data['data']['summary']
        print(f"✅ Retrieved test: {test_key}")

        # 3. LIST TESTS (verify our test appears)
        list_params = {
            'entity': 'test',
            'action': 'list',
            'project_key': project_key,
            'limit': 50
        }

        list_result = await tool.run(list_params)
        list_data = parse_mcp_response(list_result)
        assert list_data['success'], f"List failed: {list_data.get('errors')}"

        # Find our test in the list
        our_test = None
        for test in list_data['data']['tests']:
            if test['issueId'] == test_id:
                our_test = test
                break

        assert our_test is not None, "Created test not found in list"
        print(f"✅ Found test in list: {test_key}")

        # 4. UPDATE TEST TYPE
        update_params = {
            'entity': 'test',
            'action': 'update_type',
            'issue_id': test_id,
            'test_type': 'Generic'
        }

        update_result = await tool.run(update_params)
        update_data = parse_mcp_response(update_result)
        assert update_data['success'], f"Update failed: {update_data.get('errors')}"
        print(f"✅ Updated test type: {test_key}")

        # 5. DELETE TEST
        delete_params = {
            'entity': 'test',
            'action': 'delete',
            'issue_id': test_id
        }

        delete_result = await tool.run(delete_params)
        delete_data = parse_mcp_response(delete_result)
        assert delete_data['success'], f"Delete failed: {delete_data.get('errors')}"
        print(f"✅ Deleted test: {test_key}")

        # 6. VERIFY DELETION
        get_deleted_result = await tool.run(get_params)
        get_deleted_data = parse_mcp_response(get_deleted_result)
        assert not get_deleted_data['success'], "Get should fail for deleted test"
        print(f"✅ Confirmed test deletion: {test_key}")

    @pytest.mark.asyncio
    async def test_test_execution_crud(self, tool, unique_prefix):
        """Test test execution CRUD operations."""
        project_key = os.getenv('DEFAULT_PROJECT_KEY', 'FTEST')

        # First create a test to use in execution
        test_create_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Execution Test',
            'test_type': 'Generic'
        }

        test_result = await tool.run(test_create_params)
        test_data = parse_mcp_response(test_result)
        assert test_data['success'], "Test creation failed"
        test_id = test_data['data']['issueId']

        try:
            # Create test execution
            execution_params = {
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Test Execution',
                'test_issue_ids': [test_id],
                'test_environments': ['staging']
            }

            exec_result = await tool.run(execution_params)
            exec_data = parse_mcp_response(exec_result)
            assert exec_data['success'], f"Execution create failed: {exec_data.get('errors')}"

            execution_id = exec_data['data']['issueId']
            execution_key = exec_data['data']['issueKey']
            print(f"✅ Created test execution: {execution_key}")

            # Get test execution
            get_exec_params = {
                'entity': 'test_execution',
                'action': 'get',
                'issue_id': execution_id
            }

            get_exec_result = await tool.run(get_exec_params)
            get_exec_data = parse_mcp_response(get_exec_result)
            assert get_exec_data['success'], "Execution get failed"
            print(f"✅ Retrieved test execution: {execution_key}")

            # Delete test execution
            delete_exec_params = {
                'entity': 'test_execution',
                'action': 'delete',
                'issue_id': execution_id
            }

            delete_exec_result = await tool.run(delete_exec_params)
            delete_exec_data = parse_mcp_response(delete_exec_result)
            assert delete_exec_data['success'], "Execution delete failed"
            print(f"✅ Deleted test execution: {execution_key}")

        finally:
            # Clean up test
            await tool.run({
                'entity': 'test',
                'action': 'delete',
                'issue_id': test_id
            })

    @pytest.mark.asyncio
    async def test_error_handling(self, tool):
        """Test error handling for invalid operations."""

        # Test with invalid issue ID
        invalid_params = {
            'entity': 'test',
            'action': 'get',
            'issue_id': 'INVALID-123'
        }

        result = await tool.run(invalid_params)
        data = parse_mcp_response(result)
        assert not data['success'], "Should fail with invalid issue ID"
        assert len(data['errors']) > 0, "Should have error messages"
        print(f"✅ Error handling works: {data['errors'][0]}")

    @pytest.mark.asyncio
    async def test_entity_validation(self, tool):
        """Test that entity validation works."""

        # Test invalid entity
        with pytest.raises(Exception) as exc_info:
            await tool.run({
                'entity': 'invalid_entity',
                'action': 'list'
            })

        assert 'invalid_entity' in str(exc_info.value).lower()
        print("✅ Entity validation works")

    @pytest.mark.asyncio
    async def test_all_entities_accessible(self, tool):
        """Test that all entities are accessible."""
        entities = ['test', 'test_execution', 'test_plan', 'test_run']

        for entity in entities:
            params = {
                'entity': entity,
                'action': 'list',
                'project_key': os.getenv('DEFAULT_PROJECT_KEY', 'FTEST'),
                'limit': 1
            }

            result = await tool.run(params)
            data = parse_mcp_response(result)

            # Should either succeed or fail gracefully (not crash on entity)
            if not data['success']:
                # If it fails, should be a meaningful error, not "Invalid entity"
                error_msg = data['errors'][0] if data['errors'] else ""
                assert 'invalid entity' not in error_msg.lower(), f"Entity {entity} not recognized"

            print(f"✅ Entity {entity} accessible")

        print("✅ All entities are accessible through unified tool")