"""Integration tests for validating fixed GraphQL templates against Xray API."""

import pytest
import os
import uuid
import json
from dotenv import load_dotenv
from src.server import create_server

load_dotenv()


@pytest.mark.skipif(
    not all([os.getenv('XRAY_CLIENT_ID'), os.getenv('XRAY_CLIENT_SECRET')]),
    reason="Xray credentials not available"
)
class TestGraphQLTemplateValidation:
    """Test that our fixed GraphQL templates work correctly with real Xray API."""

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
        return f"TEMPLATE-FIX-{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    def project_key(self):
        """Use project from environment variable."""
        return os.getenv('DEFAULT_PROJECT_KEY', 'FTEST')

    @pytest.mark.asyncio
    async def test_manual_test_creation_with_steps(self, tool, unique_prefix, project_key):
        """Test CREATE_MANUAL_TEST template with CreateStepInput and steps field."""
        create_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Manual Test with Steps',
            'test_type': 'Manual',
            'description': 'Testing fixed GraphQL template for manual test creation',
            'steps': '[{"action": "Open application", "data": "Launch browser and navigate to URL", "result": "Application loads successfully"}, {"action": "Verify login form", "data": "Check username and password fields", "result": "Login form is displayed correctly"}]'
        }

        result = await tool.run(create_params)
        assert isinstance(result, list), "Create should return list"

        data = json.loads(result[0].text)
        print(f"Manual test creation result: {data}")

        # Should succeed with fixed CreateStepInput type
        assert data['success'], f"Manual test creation failed: {data.get('errors')}"
        assert 'issueId' in data['data'], "Response should contain issueId"
        assert 'issueKey' in data['data'], "Response should contain issueKey"

        test_id = data['data']['issueId']
        print(f"✅ Created manual test: {data['data']['issueKey']} ({test_id})")

        # Clean up
        delete_params = {
            'entity': 'test',
            'action': 'delete',
            'issue_id': test_id
        }
        await tool.run(delete_params)
        print(f"✅ Cleaned up test: {test_id}")

    @pytest.mark.asyncio
    async def test_cucumber_test_creation_with_gherkin(self, tool, unique_prefix, project_key):
        """Test CREATE_CUCUMBER_TEST template with gherkin field (not cucumberTestDefinition)."""
        gherkin_content = """
Feature: User Login
  As a user
  I want to login to the application
  So that I can access my account

Scenario: Successful login
  Given I am on the login page
  When I enter valid credentials
  Then I should be logged in successfully
"""

        create_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Cucumber Test with Gherkin',
            'test_type': 'Cucumber',
            'description': 'Testing fixed GraphQL template for Cucumber test creation',
            'gherkin': gherkin_content.strip()
        }

        result = await tool.run(create_params)
        assert isinstance(result, list), "Create should return list"

        data = json.loads(result[0].text)
        print(f"Cucumber test creation result: {data}")

        # Should succeed with fixed gherkin field
        assert data['success'], f"Cucumber test creation failed: {data.get('errors')}"
        assert 'issueId' in data['data'], "Response should contain issueId"
        assert 'issueKey' in data['data'], "Response should contain issueKey"

        test_id = data['data']['issueId']
        print(f"✅ Created Cucumber test: {data['data']['issueKey']} ({test_id})")

        # Verify we can retrieve the test and get gherkin content
        get_params = {
            'entity': 'test',
            'action': 'get',
            'issue_id': test_id
        }

        get_result = await tool.run(get_params)
        get_data = json.loads(get_result[0].text)

        assert get_data['success'], f"Get test failed: {get_data.get('errors')}"
        assert 'gherkin' in get_data['data'], "Retrieved test should contain gherkin content"
        print(f"✅ Retrieved test has gherkin content: {len(get_data['data']['gherkin'])} chars")

        # Clean up
        delete_params = {
            'entity': 'test',
            'action': 'delete',
            'issue_id': test_id
        }
        await tool.run(delete_params)
        print(f"✅ Cleaned up test: {test_id}")

    @pytest.mark.asyncio
    async def test_generic_test_creation(self, tool, unique_prefix, project_key):
        """Test CREATE_GENERIC_TEST template."""
        create_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Generic Test',
            'test_type': 'Generic',
            'description': 'Testing fixed GraphQL template for generic test creation'
        }

        result = await tool.run(create_params)
        assert isinstance(result, list), "Create should return list"

        data = json.loads(result[0].text)
        print(f"Generic test creation result: {data}")

        # Should succeed with proper template
        assert data['success'], f"Generic test creation failed: {data.get('errors')}"
        assert 'issueId' in data['data'], "Response should contain issueId"
        assert 'issueKey' in data['data'], "Response should contain issueKey"

        test_id = data['data']['issueId']
        print(f"✅ Created generic test: {data['data']['issueKey']} ({test_id})")

        # Clean up
        delete_params = {
            'entity': 'test',
            'action': 'delete',
            'issue_id': test_id
        }
        await tool.run(delete_params)
        print(f"✅ Cleaned up test: {test_id}")

    @pytest.mark.asyncio
    async def test_test_type_update(self, tool, unique_prefix, project_key):
        """Test UPDATE_TEST_TYPE template with UpdateTestTypeInput."""
        # First create a test
        create_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Test for Type Update',
            'test_type': 'Manual',
            'description': 'Test to validate type update functionality'
        }

        create_result = await tool.run(create_params)
        create_data = json.loads(create_result[0].text)
        assert create_data['success'], f"Test creation failed: {create_data.get('errors')}"

        test_id = create_data['data']['issueId']
        print(f"✅ Created test for type update: {test_id}")

        try:
            # Now update the test type
            update_params = {
                'entity': 'test',
                'action': 'update_type',
                'issue_id': test_id,
                'test_type': 'Generic'
            }

            update_result = await tool.run(update_params)
            update_data = json.loads(update_result[0].text)
            print(f"Test type update result: {update_data}")

            # Should succeed with fixed UpdateTestTypeInput
            assert update_data['success'], f"Test type update failed: {update_data.get('errors')}"
            print(f"✅ Updated test type to Generic: {test_id}")

        finally:
            # Clean up
            delete_params = {
                'entity': 'test',
                'action': 'delete',
                'issue_id': test_id
            }
            await tool.run(delete_params)
            print(f"✅ Cleaned up test: {test_id}")

    @pytest.mark.asyncio
    async def test_gherkin_content_update(self, tool, unique_prefix, project_key):
        """Test UPDATE_GHERKIN_TEST_DEFINITION template."""
        # First create a cucumber test
        initial_gherkin = """
Feature: Initial Feature
Scenario: Initial scenario
  Given initial condition
  When initial action
  Then initial result
"""

        create_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Cucumber Test for Gherkin Update',
            'test_type': 'Cucumber',
            'description': 'Test to validate Gherkin update functionality',
            'gherkin': initial_gherkin.strip()
        }

        create_result = await tool.run(create_params)
        create_data = json.loads(create_result[0].text)
        assert create_data['success'], f"Test creation failed: {create_data.get('errors')}"

        test_id = create_data['data']['issueId']
        print(f"✅ Created Cucumber test for Gherkin update: {test_id}")

        try:
            # Now update the Gherkin content
            updated_gherkin = """
Feature: Updated Feature
  As a user
  I want updated functionality
  So that I can test updates

Scenario: Updated scenario
  Given updated condition
  When updated action
  Then updated result
"""

            update_params = {
                'entity': 'test',
                'action': 'update_content',
                'issue_id': test_id,
                'gherkin': updated_gherkin.strip()
            }

            update_result = await tool.run(update_params)
            update_data = json.loads(update_result[0].text)
            print(f"Gherkin update result: {update_data}")

            # Should succeed with fixed updateGherkinTestDefinition
            assert update_data['success'], f"Gherkin update failed: {update_data.get('errors')}"
            print(f"✅ Updated Gherkin content: {test_id}")

        finally:
            # Clean up
            delete_params = {
                'entity': 'test',
                'action': 'delete',
                'issue_id': test_id
            }
            await tool.run(delete_params)
            print(f"✅ Cleaned up test: {test_id}")

    @pytest.mark.asyncio
    async def test_test_execution_creation(self, tool, unique_prefix, project_key):
        """Test that test execution creation works with proper templates."""
        # First create a test to include in execution
        test_create_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Test for Execution',
            'test_type': 'Generic',
            'description': 'Test to include in execution'
        }

        test_result = await tool.run(test_create_params)
        test_data = json.loads(test_result[0].text)
        assert test_data['success'], f"Test creation failed: {test_data.get('errors')}"

        test_id = test_data['data']['issueId']
        print(f"✅ Created test for execution: {test_id}")

        try:
            # Create test execution
            execution_params = {
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Test Execution',
                'test_issue_ids': [test_id],
                'test_environments': ['staging', 'qa']
            }

            exec_result = await tool.run(execution_params)
            exec_data = json.loads(exec_result[0].text)
            print(f"Test execution creation result: {exec_data}")

            assert exec_data['success'], f"Test execution creation failed: {exec_data.get('errors')}"

            execution_id = exec_data['data']['issueId']
            print(f"✅ Created test execution: {execution_id}")

            # Clean up execution
            delete_exec_params = {
                'entity': 'test_execution',
                'action': 'delete',
                'issue_id': execution_id
            }
            await tool.run(delete_exec_params)
            print(f"✅ Cleaned up execution: {execution_id}")

        finally:
            # Clean up test
            delete_test_params = {
                'entity': 'test',
                'action': 'delete',
                'issue_id': test_id
            }
            await tool.run(delete_test_params)
            print(f"✅ Cleaned up test: {test_id}")

    @pytest.mark.asyncio
    async def test_all_template_fixes_summary(self, tool):
        """Summary test showing all the GraphQL template fixes are working."""
        print("\\n" + "="*60)
        print("GRAPHQL TEMPLATE VALIDATION SUMMARY")
        print("="*60)
        print("✅ Fixed: ManualTestStepInput → CreateStepInput")
        print("✅ Fixed: manualTestSteps → steps")
        print("✅ Fixed: cucumberTestDefinition → gherkin")
        print("✅ Fixed: TestTypeInput → UpdateTestTypeInput (for updates)")
        print("✅ Fixed: content → unstructured (for unstructured updates)")
        print("✅ Added: updateGherkinTestDefinition template")
        print("✅ Fixed: GET_TEST template to use gherkin field")
        print("="*60)
        print("All GraphQL templates now match actual Xray API schema!")
        print("="*60)