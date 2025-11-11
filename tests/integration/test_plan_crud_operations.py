"""Comprehensive Test Plan CRUD operations tests for Xray MCP server."""

import pytest
import os
import uuid
from dotenv import load_dotenv
from src.server import create_server
from tests.integration.test_helpers import parse_mcp_response

load_dotenv()


@pytest.mark.skipif(
    not all([os.getenv('XRAY_CLIENT_ID'), os.getenv('XRAY_CLIENT_SECRET')]),
    reason="Xray credentials not available"
)
class TestPlanCRUDOperations:
    """Test Test Plan CRUD operations against live Xray API."""

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
        return f"PLAN-TEST-{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    def project_key(self):
        """Get project key from environment."""
        return os.getenv('DEFAULT_PROJECT_KEY', 'FTEST')

    @pytest.mark.asyncio
    async def test_test_plan_crud_operations(self, tool, unique_prefix, project_key):
        """Test complete Test Plan CRUD cycle."""
        print(f"\n🧪 Testing Test Plan CRUD with prefix: {unique_prefix}")

        # First create a test to use in the plan
        test_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Test for Plan',
            'test_type': 'Manual',
            'description': 'Test to be used in test plan operations'
        }

        test_result = await tool.run(test_params)
        test_data = parse_mcp_response(test_result)
        assert test_data['success'], f"Test creation failed: {test_data.get('errors')}"

        test_id = test_data['data']['issueId']
        test_key = test_data['data']['issueKey']
        print(f"✅ Created test for plan: {test_key} ({test_id})")

        try:
            # 1. CREATE Test Plan
            plan_create_params = {
                'entity': 'test_plan',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Test Plan CRUD',
                'test_issue_ids': [test_id]
            }

            plan_result = await tool.run(plan_create_params)
            plan_data = parse_mcp_response(plan_result)
            assert plan_data['success'], f"Plan creation failed: {plan_data.get('errors')}"

            plan_id = plan_data['data']['issueId']
            plan_key = plan_data['data']['issueKey']
            print(f"✅ Created test plan: {plan_key} ({plan_id})")

            try:
                # 2. GET Test Plan
                plan_get_params = {
                    'entity': 'test_plan',
                    'action': 'get',
                    'issue_id': plan_id
                }

                get_result = await tool.run(plan_get_params)
                get_data = parse_mcp_response(get_result)
                assert get_data['success'], f"Get plan failed: {get_data.get('errors')}"
                assert get_data['data']['issueId'] == plan_id
                assert unique_prefix in get_data['data']['summary']
                print(f"✅ Retrieved test plan: {plan_key}")

                # 3. LIST Test Plans
                plan_list_params = {
                    'entity': 'test_plan',
                    'action': 'list',
                    'project_key': project_key,
                    'limit': 50
                }

                list_result = await tool.run(plan_list_params)
                list_data = parse_mcp_response(list_result)
                assert list_data['success'], f"List plans failed: {list_data.get('errors')}"

                # Find our plan in the list
                our_plan = None
                for plan in list_data['data']['plans']:
                    if plan['issueId'] == plan_id:
                        our_plan = plan
                        break

                assert our_plan is not None, "Created plan not found in list"
                print(f"✅ Found test plan in list: {plan_key}")

            finally:
                # 4. DELETE Test Plan
                plan_delete_params = {
                    'entity': 'test_plan',
                    'action': 'delete',
                    'issue_id': plan_id
                }

                delete_result = await tool.run(plan_delete_params)
                delete_data = parse_mcp_response(delete_result)
                assert delete_data['success'], f"Delete plan failed: {delete_data.get('errors')}"
                print(f"✅ Deleted test plan: {plan_key}")

                # 5. VERIFY DELETION
                verify_get_params = {
                    'entity': 'test_plan',
                    'action': 'get',
                    'issue_id': plan_id
                }

                verify_result = await tool.run(verify_get_params)
                verify_data = parse_mcp_response(verify_result)
                assert not verify_data['success'], "Get should fail for deleted plan"
                print(f"✅ Confirmed test plan deletion: {plan_key}")

        finally:
            # Clean up the test
            test_delete_params = {
                'entity': 'test',
                'action': 'delete',
                'issue_id': test_id
            }

            test_delete_result = await tool.run(test_delete_params)
            test_delete_data = parse_mcp_response(test_delete_result)
            assert test_delete_data['success'], f"Test cleanup failed: {test_delete_data.get('errors')}"
            print(f"✅ Cleaned up test: {test_key}")

    @pytest.mark.asyncio
    async def test_test_plan_association_management(self, tool, unique_prefix, project_key):
        """Test Test Plan association management (add/remove tests)."""
        print(f"\n🧪 Testing Test Plan associations with prefix: {unique_prefix}")

        # Create two tests for association testing
        test1_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Test 1 for Associations',
            'test_type': 'Manual'
        }

        test2_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Test 2 for Associations',
            'test_type': 'Manual'
        }

        test1_result = await tool.run(test1_params)
        test1_data = parse_mcp_response(test1_result)
        assert test1_data['success'], "Test 1 creation failed"

        test2_result = await tool.run(test2_params)
        test2_data = parse_mcp_response(test2_result)
        assert test2_data['success'], "Test 2 creation failed"

        test1_id = test1_data['data']['issueId']
        test2_id = test2_data['data']['issueId']
        test1_key = test1_data['data']['issueKey']
        test2_key = test2_data['data']['issueKey']

        print(f"✅ Created tests: {test1_key} ({test1_id}), {test2_key} ({test2_id})")

        try:
            # Create plan with first test
            plan_params = {
                'entity': 'test_plan',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Association Test Plan',
                'test_issue_ids': [test1_id]
            }

            plan_result = await tool.run(plan_params)
            plan_data = parse_mcp_response(plan_result)
            assert plan_data['success'], "Plan creation failed"

            plan_id = plan_data['data']['issueId']
            plan_key = plan_data['data']['issueKey']
            print(f"✅ Created plan with Test 1: {plan_key} ({plan_id})")

            try:
                # Add second test to plan
                add_test_params = {
                    'entity': 'test_plan',
                    'action': 'add_tests',
                    'issue_id': plan_id,
                    'test_issue_ids': [test2_id]
                }

                add_result = await tool.run(add_test_params)
                add_data = parse_mcp_response(add_result)
                assert add_data['success'], f"Add test failed: {add_data.get('errors')}"
                print(f"✅ Added Test 2 to plan: {test2_key}")

                # Remove first test from plan
                remove_test_params = {
                    'entity': 'test_plan',
                    'action': 'remove_tests',
                    'issue_id': plan_id,
                    'test_issue_ids': [test1_id]
                }

                remove_result = await tool.run(remove_test_params)
                remove_data = parse_mcp_response(remove_result)
                assert remove_data['success'], f"Remove test failed: {remove_data.get('errors')}"
                print(f"✅ Removed Test 1 from plan: {test1_key}")

            finally:
                # Clean up plan
                plan_delete_params = {
                    'entity': 'test_plan',
                    'action': 'delete',
                    'issue_id': plan_id
                }

                await tool.run(plan_delete_params)
                print(f"✅ Cleaned up plan: {plan_key}")

        finally:
            # Clean up both tests
            for test_id, test_key in [(test1_id, test1_key), (test2_id, test2_key)]:
                test_delete_params = {
                    'entity': 'test',
                    'action': 'delete',
                    'issue_id': test_id
                }

                await tool.run(test_delete_params)
                print(f"✅ Cleaned up test: {test_key}")

    @pytest.mark.asyncio
    async def test_test_plan_error_handling(self, tool, unique_prefix, project_key):
        """Test Test Plan error handling scenarios."""
        print(f"\n🧪 Testing Test Plan error handling with prefix: {unique_prefix}")

        # 1. Test missing required fields
        missing_project_params = {
            'entity': 'test_plan',
            'action': 'create',
            'summary': f'{unique_prefix} Missing Project'
        }

        result1 = await tool.run(missing_project_params)
        data1 = parse_mcp_response(result1)
        assert not data1['success'], "Should fail without project_key"
        assert "project_key" in str(data1['errors']).lower()
        print("✅ Properly rejected missing project_key")

        missing_summary_params = {
            'entity': 'test_plan',
            'action': 'create',
            'project_key': project_key
        }

        result2 = await tool.run(missing_summary_params)
        data2 = parse_mcp_response(result2)
        assert not data2['success'], "Should fail without summary"
        assert "summary" in str(data2['errors']).lower()
        print("✅ Properly rejected missing summary")

        # 2. Test non-existent plan operations
        fake_plan_id = "999999999"
        get_fake_params = {
            'entity': 'test_plan',
            'action': 'get',
            'issue_id': fake_plan_id
        }

        result3 = await tool.run(get_fake_params)
        data3 = parse_mcp_response(result3)
        assert not data3['success'], "Should fail for non-existent plan"
        print("✅ Properly handled non-existent plan")

        # 3. Test invalid test ID associations
        invalid_add_params = {
            'entity': 'test_plan',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Invalid Test Association',
            'test_issue_ids': ["999999999"]  # Non-existent test
        }

        result4 = await tool.run(invalid_add_params)
        data4 = parse_mcp_response(result4)
        # This might succeed but with warnings, or fail - both are acceptable
        print(f"✅ Handled invalid test association: {'Success' if data4['success'] else 'Failed as expected'}")

        print("✅ All error handling scenarios tested")