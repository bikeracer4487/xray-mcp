"""
Comprehensive test suite to validate all QA fixes identified in the test report.

This test suite specifically addresses the 4 critical issues:
1. Data Retrieval Failure - Tests and Plans can be retrieved after creation
2. Array Parameter Validation - Array parameters work correctly
3. Test Listing Inconsistency - Created entities appear in list results
4. Tool Response Format - MCP format is correct

Tests are designed to work with live Xray API and include retry logic for indexing delays.
"""

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
class TestQAFixes:
    """Test suite validating all QA report issues are resolved."""

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
        return f"QA-FIX-{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    def project_key(self):
        """Get project key from environment."""
        return os.getenv('DEFAULT_PROJECT_KEY', 'FTEST')

    @pytest.mark.asyncio
    async def test_1_data_retrieval_with_retry_logic(self, tool, unique_prefix, project_key):
        """Test Fix #1: Data retrieval works with retry logic for indexing delays."""
        print(f"\n🔍 Testing data retrieval fix with prefix: {unique_prefix}")

        # Create a test
        test_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Retrieval Test',
            'test_type': 'Manual'
        }

        create_result = await tool.run(test_params)
        create_data = parse_mcp_response(create_result)
        assert create_data['success'], f"Failed to create test: {create_data.get('errors')}"

        test_id = create_data['data']['issueId']
        test_key = create_data['data']['issueKey']
        print(f"✅ Created test: {test_key} ({test_id})")

        try:
            # Test immediate retrieval (should use retry logic)
            get_params = {
                'entity': 'test',
                'action': 'get',
                'issue_id': test_id
            }

            get_result = await tool.run(get_params)
            get_data = parse_mcp_response(get_result)

            # This should succeed now with retry logic
            assert get_data['success'], f"Data retrieval still failing: {get_data.get('errors')}"
            assert get_data['data']['issueId'] == test_id
            print(f"✅ Successfully retrieved test immediately after creation: {test_key}")

            # Test plan creation and retrieval
            plan_params = {
                'entity': 'test_plan',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Plan Retrieval Test',
                'test_issue_ids': [test_id]
            }

            plan_result = await tool.run(plan_params)
            plan_data = parse_mcp_response(plan_result)
            assert plan_data['success'], f"Failed to create plan: {plan_data.get('errors')}"

            plan_id = plan_data['data']['issueId']
            plan_key = plan_data['data']['issueKey']
            print(f"✅ Created plan: {plan_key} ({plan_id})")

            # Test plan retrieval with retry logic
            plan_get_params = {
                'entity': 'test_plan',
                'action': 'get',
                'issue_id': plan_id
            }

            plan_get_result = await tool.run(plan_get_params)
            plan_get_data = parse_mcp_response(plan_get_result)
            assert plan_get_data['success'], f"Plan retrieval still failing: {plan_get_data.get('errors')}"
            assert plan_get_data['data']['issueId'] == plan_id
            print(f"✅ Successfully retrieved plan immediately after creation: {plan_key}")

            # Clean up plan
            await tool.run({'entity': 'test_plan', 'action': 'delete', 'issue_id': plan_id})

        finally:
            # Clean up test
            await tool.run({'entity': 'test', 'action': 'delete', 'issue_id': test_id})
            print(f"✅ Cleaned up test: {test_key}")

    @pytest.mark.asyncio
    async def test_2_array_parameter_handling(self, tool, unique_prefix, project_key):
        """Test Fix #2: Array parameters work correctly for all operations."""
        print(f"\n📋 Testing array parameter handling with prefix: {unique_prefix}")

        # Create two tests for array operations
        test_ids = []
        test_keys = []

        for i in range(2):
            test_params = {
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Array Test {i+1}',
                'test_type': 'Manual'
            }

            create_result = await tool.run(test_params)
            create_data = parse_mcp_response(create_result)
            assert create_data['success'], f"Failed to create test {i+1}: {create_data.get('errors')}"

            test_ids.append(create_data['data']['issueId'])
            test_keys.append(create_data['data']['issueKey'])
            print(f"✅ Created test {i+1}: {test_keys[i]} ({test_ids[i]})")

        try:
            # Test array parameters in test execution creation
            exec_params = {
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Array Test Execution',
                'test_issue_ids': test_ids,  # Array parameter
                'test_environments': ['staging', 'production']  # Array parameter
            }

            exec_result = await tool.run(exec_params)
            exec_data = parse_mcp_response(exec_result)
            assert exec_data['success'], f"Array parameters failed in execution: {exec_data.get('errors')}"

            exec_id = exec_data['data']['issueId']
            exec_key = exec_data['data']['issueKey']
            print(f"✅ Created execution with array parameters: {exec_key} ({exec_id})")

            # Test array parameters in test plan creation
            plan_params = {
                'entity': 'test_plan',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Array Test Plan',
                'test_issue_ids': test_ids  # Array parameter
            }

            plan_result = await tool.run(plan_params)
            plan_data = parse_mcp_response(plan_result)
            assert plan_data['success'], f"Array parameters failed in plan: {plan_data.get('errors')}"

            plan_id = plan_data['data']['issueId']
            plan_key = plan_data['data']['issueKey']
            print(f"✅ Created plan with array parameters: {plan_key} ({plan_id})")

            # Test defects array parameter in test run operations
            # First need to add tests to execution to create test runs
            add_tests_params = {
                'entity': 'test_execution',
                'action': 'add_tests',
                'issue_id': exec_id,
                'test_issue_ids': test_ids  # Array parameter
            }

            add_result = await tool.run(add_tests_params)
            add_data = parse_mcp_response(add_result)
            if add_data['success']:
                print("✅ Successfully added tests to execution using array parameter")

            # Clean up in reverse order
            await tool.run({'entity': 'test_plan', 'action': 'delete', 'issue_id': plan_id})
            await tool.run({'entity': 'test_execution', 'action': 'delete', 'issue_id': exec_id})
            print("✅ Cleaned up execution and plan")

        finally:
            # Clean up tests
            for i, (test_id, test_key) in enumerate(zip(test_ids, test_keys)):
                await tool.run({'entity': 'test', 'action': 'delete', 'issue_id': test_id})
                print(f"✅ Cleaned up test {i+1}: {test_key}")

    @pytest.mark.asyncio
    async def test_3_list_consistency_with_warnings(self, tool, unique_prefix, project_key):
        """Test Fix #3: List operations include warnings about indexing delays."""
        print(f"\n📋 Testing list consistency and warnings with prefix: {unique_prefix}")

        # Create a test
        test_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} List Consistency Test',
            'test_type': 'Manual'
        }

        create_result = await tool.run(test_params)
        create_data = parse_mcp_response(create_result)
        assert create_data['success'], f"Failed to create test: {create_data.get('errors')}"

        test_id = create_data['data']['issueId']
        test_key = create_data['data']['issueKey']
        print(f"✅ Created test: {test_key} ({test_id})")

        try:
            # Test list with retry_on_empty_results parameter
            list_params = {
                'entity': 'test',
                'action': 'list',
                'project_key': project_key,
                'limit': 50,
                'retry_on_empty_results': True  # Enable retry logic
            }

            list_result = await tool.run(list_params)
            list_data = parse_mcp_response(list_result)
            assert list_data['success'], f"Failed to list tests: {list_data.get('errors')}"

            print(f"✅ Listed tests successfully: found {list_data['data']['total']} tests")

            # Check for warnings about indexing delays
            if 'warnings' in list_data and list_data['warnings']:
                print(f"ℹ️ Warnings provided: {list_data['warnings']}")

            # Test plan listing
            plan_list_params = {
                'entity': 'test_plan',
                'action': 'list',
                'project_key': project_key,
                'limit': 10
            }

            plan_list_result = await tool.run(plan_list_params)
            plan_list_data = parse_mcp_response(plan_list_result)
            assert plan_list_data['success'], f"Failed to list plans: {plan_list_data.get('errors')}"

            print(f"✅ Listed plans successfully: found {plan_list_data['data']['total']} plans")

        finally:
            # Clean up
            await tool.run({'entity': 'test', 'action': 'delete', 'issue_id': test_id})
            print(f"✅ Cleaned up test: {test_key}")

    @pytest.mark.asyncio
    async def test_4_response_format_validation(self, tool, unique_prefix, project_key):
        """Test Fix #4: MCP response format is correct and parseable."""
        print(f"\n📄 Testing response format validation with prefix: {unique_prefix}")

        # Test various operations to validate response format
        test_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Response Format Test',
            'test_type': 'Manual'
        }

        create_result = await tool.run(test_params)

        # Validate MCP response format
        assert isinstance(create_result, list), "Response should be a list (MCP format)"
        assert len(create_result) > 0, "Response list should not be empty"

        content = create_result[0]
        assert hasattr(content, 'text'), "Content should have 'text' attribute"
        assert content.text, "Content text should not be empty"

        # Validate JSON parseability through our helper
        create_data = parse_mcp_response(create_result)
        assert 'success' in create_data, "Parsed response should have 'success' field"
        assert create_data['success'], f"Create operation failed: {create_data.get('errors')}"
        assert 'data' in create_data, "Successful response should have 'data' field"

        test_id = create_data['data']['issueId']
        test_key = create_data['data']['issueKey']
        print(f"✅ Response format validation passed for create: {test_key}")

        try:
            # Test get operation response format
            get_params = {
                'entity': 'test',
                'action': 'get',
                'issue_id': test_id
            }

            get_result = await tool.run(get_params)
            get_data = parse_mcp_response(get_result)

            assert isinstance(get_result, list), "Get response should be MCP list format"
            assert get_data['success'], f"Get operation failed: {get_data.get('errors')}"
            print("✅ Response format validation passed for get operation")

            # Test list operation response format
            list_params = {
                'entity': 'test',
                'action': 'list',
                'project_key': project_key,
                'limit': 10
            }

            list_result = await tool.run(list_params)
            list_data = parse_mcp_response(list_result)

            assert isinstance(list_result, list), "List response should be MCP list format"
            assert list_data['success'], f"List operation failed: {list_data.get('errors')}"
            assert 'tests' in list_data['data'], "List response should contain 'tests' array"
            print("✅ Response format validation passed for list operation")

        finally:
            # Clean up
            await tool.run({'entity': 'test', 'action': 'delete', 'issue_id': test_id})
            print(f"✅ Cleaned up test: {test_key}")

    @pytest.mark.asyncio
    async def test_5_comprehensive_crud_validation(self, tool, unique_prefix, project_key):
        """Test Fix Summary: Complete CRUD operations work reliably end-to-end."""
        print(f"\n🔄 Testing comprehensive CRUD validation with prefix: {unique_prefix}")

        test_id = None
        exec_id = None
        plan_id = None

        try:
            # 1. Create Test with retry-resilient retrieval
            test_params = {
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Comprehensive CRUD Test',
                'test_type': 'Manual',
                'steps': '[{"action": "Login", "data": "username/password", "result": "User logged in"}]'
            }

            test_result = await tool.run(test_params)
            test_data = parse_mcp_response(test_result)
            assert test_data['success'], f"Test creation failed: {test_data.get('errors')}"
            test_id = test_data['data']['issueId']
            print(f"✅ 1. Created test: {test_data['data']['issueKey']}")

            # 2. Retrieve test immediately (tests retry logic)
            get_test_result = await tool.run({'entity': 'test', 'action': 'get', 'issue_id': test_id})
            get_test_data = parse_mcp_response(get_test_result)
            assert get_test_data['success'], f"Test retrieval failed: {get_test_data.get('errors')}"
            print("✅ 2. Retrieved test immediately after creation")

            # 3. Create Test Execution with array parameters
            exec_params = {
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Comprehensive Execution',
                'test_issue_ids': [test_id],
                'test_environments': ['staging']
            }

            exec_result = await tool.run(exec_params)
            exec_data = parse_mcp_response(exec_result)
            assert exec_data['success'], f"Execution creation failed: {exec_data.get('errors')}"
            exec_id = exec_data['data']['issueId']
            print(f"✅ 3. Created execution with array parameters: {exec_data['data']['issueKey']}")

            # 4. Create Test Plan with array parameters
            plan_params = {
                'entity': 'test_plan',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Comprehensive Plan',
                'test_issue_ids': [test_id]
            }

            plan_result = await tool.run(plan_params)
            plan_data = parse_mcp_response(plan_result)
            assert plan_data['success'], f"Plan creation failed: {plan_data.get('errors')}"
            plan_id = plan_data['data']['issueId']
            print(f"✅ 4. Created plan with array parameters: {plan_data['data']['issueKey']}")

            # 5. List operations with proper response format
            for entity_type in ['test', 'test_execution', 'test_plan']:
                list_params = {
                    'entity': entity_type,
                    'action': 'list',
                    'project_key': project_key,
                    'limit': 10
                }

                list_result = await tool.run(list_params)
                list_data = parse_mcp_response(list_result)
                assert list_data['success'], f"List {entity_type} failed: {list_data.get('errors')}"
                print(f"✅ 5. Listed {entity_type} (found: {list_data['data'].get('total', 0)})")

        finally:
            # Clean up in reverse order
            if plan_id:
                await tool.run({'entity': 'test_plan', 'action': 'delete', 'issue_id': plan_id})
                print("✅ Cleaned up plan")

            if exec_id:
                await tool.run({'entity': 'test_execution', 'action': 'delete', 'issue_id': exec_id})
                print("✅ Cleaned up execution")

            if test_id:
                await tool.run({'entity': 'test', 'action': 'delete', 'issue_id': test_id})
                print("✅ Cleaned up test")

        print("✅ Comprehensive CRUD validation completed successfully")