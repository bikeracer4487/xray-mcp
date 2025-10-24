"""
Integration tests for release planning workflow.

Tests complex end-to-end workflows for creating and managing test plans
for software releases. Covers use cases UC-141 through UC-180.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from typing import Dict, Any, List

from src.server import create_server
from src.tools.xray_tool import XrayTool


@pytest.fixture
def unique_prefix():
    """Generate unique prefix for test names."""
    return f"ReleasePlan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


@pytest.fixture
def project_key():
    """Get project key from environment."""
    import os
    return os.getenv('XRAY_PROJECT_KEY', 'FTEST')


@pytest.mark.asyncio
class TestReleasePlanningWorkflow:
    """Test complete release planning workflows."""

    async def test_complete_release_planning_workflow(self, tool, unique_prefix, project_key):
        """
        UC-141: Create comprehensive release test plan.

        Tests the complete workflow of:
        1. Creating diverse tests for a release
        2. Organizing tests by feature areas and risk levels
        3. Creating test executions for different phases
        4. Linking everything in a master test plan
        5. Managing dependencies and traceability
        """
        created_resources = []

        try:
            # Step 1: Create tests for different features of the release
            feature_tests = [
                # Authentication Feature
                {
                    'name': f'{unique_prefix}_Auth_Login',
                    'feature': 'Authentication',
                    'risk': 'High',
                    'type': 'Manual',
                    'steps': [
                        {"action": "Enter valid credentials", "data": "user@test.com / SecurePass123", "result": "Login successful"},
                        {"action": "Verify session creation", "data": "Check session token", "result": "Valid session established"},
                        {"action": "Test remember me functionality", "data": "Check remember me option", "result": "Session persists across browser restart"}
                    ]
                },
                {
                    'name': f'{unique_prefix}_Auth_Logout',
                    'feature': 'Authentication',
                    'risk': 'Medium',
                    'type': 'Manual',
                    'steps': [
                        {"action": "Click logout button", "data": "Logout button", "result": "Logout confirmation displayed"},
                        {"action": "Confirm logout", "data": "Yes button", "result": "User logged out"},
                        {"action": "Verify session cleared", "data": "Check session token", "result": "No valid session"}
                    ]
                },
                # Payment Feature
                {
                    'name': f'{unique_prefix}_Payment_CreditCard',
                    'feature': 'Payment',
                    'risk': 'Critical',
                    'type': 'Manual',
                    'steps': [
                        {"action": "Enter payment details", "data": "4111111111111111, 12/25, 123", "result": "Card details accepted"},
                        {"action": "Submit payment", "data": "Pay button", "result": "Payment processing"},
                        {"action": "Verify payment confirmation", "data": "Confirmation page", "result": "Payment successful"}
                    ]
                },
                {
                    'name': f'{unique_prefix}_Payment_PayPal',
                    'feature': 'Payment',
                    'risk': 'Critical',
                    'type': 'Manual',
                    'steps': [
                        {"action": "Select PayPal option", "data": "PayPal radio button", "result": "PayPal selected"},
                        {"action": "Redirect to PayPal", "data": "PayPal button", "result": "PayPal login page"},
                        {"action": "Complete PayPal payment", "data": "PayPal credentials", "result": "Payment confirmed"}
                    ]
                },
                # User Profile Feature
                {
                    'name': f'{unique_prefix}_Profile_Update',
                    'feature': 'UserProfile',
                    'risk': 'Low',
                    'type': 'Manual',
                    'steps': [
                        {"action": "Navigate to profile", "data": "/profile", "result": "Profile page loads"},
                        {"action": "Update profile information", "data": "Name, email, phone", "result": "Changes reflected"},
                        {"action": "Save changes", "data": "Save button", "result": "Profile updated successfully"}
                    ]
                },
                # API Integration
                {
                    'name': f'{unique_prefix}_API_UserData',
                    'feature': 'API',
                    'risk': 'High',
                    'type': 'Cucumber',
                    'gherkin': '''Feature: User Data API

                    Scenario: Retrieve user profile data
                        Given I have a valid authentication token
                        When I make a GET request to /api/user/profile
                        Then I should receive a 200 status code
                        And the response should contain user profile data
                        And the data should include name, email, and creation date'''
                }
            ]

            created_test_ids = []
            tests_by_feature = {}

            for test_data in feature_tests:
                result = await tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': test_data['name'],
                    'test_type': test_data['type'],
                    'priority': test_data['risk'],
                    'steps': test_data.get('steps', '[]'),
                    'gherkin': test_data.get('gherkin'),
                    'description': f"Test for {test_data['feature']} feature - Risk Level: {test_data['risk']}"
                })

                assert result['success'], f"Failed to create test: {result.get('errors', [])}"
                test_id = result['data']['issueId']
                created_test_ids.append(test_id)
                created_resources.append(('test', test_id))

                # Group by feature for organization
                feature = test_data['feature']
                if feature not in tests_by_feature:
                    tests_by_feature[feature] = []
                tests_by_feature[feature].append(test_id)

            assert len(created_test_ids) == 6, "Should have created 6 feature tests"

            # Step 2: Create feature-specific test executions
            execution_ids = []
            for feature, test_ids in tests_by_feature.items():
                execution_result = await tool.execute({
                    'entity': 'test_execution',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_{feature}_Feature_Testing',
                    'description': f'Testing execution for {feature} feature in release v2.0',
                    'test_environments': ['Staging', 'UAT']
                })

                assert execution_result['success'], f"Failed to create {feature} execution"
                execution_id = execution_result['data']['issueId']
                execution_ids.append(execution_id)
                created_resources.append(('test_execution', execution_id))

                # Add feature tests to execution
                add_tests_result = await tool.execute({
                    'entity': 'test_execution',
                    'action': 'add_tests',
                    'issue_id': execution_id,
                    'test_issue_ids': test_ids
                })

                assert add_tests_result['success'], f"Should add tests to {feature} execution"

            # Step 3: Create master release test plan
            plan_result = await tool.execute({
                'entity': 'test_plan',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_Release_v2.0_Master_Plan',
                'description': 'Master test plan for Release v2.0 covering all features: Authentication, Payment, UserProfile, and API integration'
            })

            assert plan_result['success'], "Should create master release plan"
            plan_id = plan_result['data']['issueId']
            created_resources.append(('test_plan', plan_id))

            # Step 4: Add all tests to master plan
            plan_add_tests_result = await tool.execute({
                'entity': 'test_plan',
                'action': 'add_tests',
                'issue_id': plan_id,
                'test_issue_ids': created_test_ids
            })

            assert plan_add_tests_result['success'], "Should add all tests to master plan"

            # Step 5: Add all executions to master plan
            plan_add_executions_result = await tool.execute({
                'entity': 'test_plan',
                'action': 'add_executions',
                'issue_id': plan_id,
                'test_exec_issue_ids': execution_ids
            })

            assert plan_add_executions_result['success'], "Should add all executions to master plan"

            # Step 6: Verify master plan structure
            plan_details = await tool.execute({
                'entity': 'test_plan',
                'action': 'get',
                'issue_id': plan_id
            })

            assert plan_details['success'], "Should retrieve master plan details"
            plan_data = plan_details['data']['testPlan']

            # Verify plan contains all tests
            plan_tests = plan_data.get('tests', [])
            assert len(plan_tests) == len(created_test_ids), f"Plan should contain {len(created_test_ids)} tests"

            # Verify plan contains all executions
            plan_executions = plan_data.get('testExecutions', [])
            assert len(plan_executions) == len(execution_ids), f"Plan should contain {len(execution_ids)} executions"

            # Step 7: Execute critical path tests (High and Critical risk)
            critical_executions = []
            for execution_id in execution_ids:
                execution_details = await tool.execute({
                    'entity': 'test_execution',
                    'action': 'get',
                    'issue_id': execution_id
                })

                if execution_details['success']:
                    test_runs = execution_details['data']['testExecution']['testRuns']
                    for test_run in test_runs:
                        test_issue_id = test_run['test']['issueId']

                        # Execute critical and high risk tests first
                        # Simulate risk-based execution priority
                        if any(test_data['name'].endswith(test_issue_id.split('-')[-1]) and
                               test_data['risk'] in ['Critical', 'High']
                               for test_data in feature_tests):

                            run_result = await tool.execute({
                                'entity': 'test_run',
                                'action': 'update_status',
                                'test_execution_id': execution_id,
                                'test_issue_id': test_issue_id,
                                'status': 'PASSED',
                                'comment': 'Critical path test passed - release blocker cleared'
                            })

                            assert run_result['success'], "Should update critical test status"

            # Step 8: Simulate finding a critical bug in payment
            # Update one payment test as failed
            payment_execution = None
            for execution_id in execution_ids:
                execution_details = await tool.execute({
                    'entity': 'test_execution',
                    'action': 'get',
                    'issue_id': execution_id
                })

                if execution_details['success']:
                    exec_summary = execution_details['data']['testExecution']['jira']['summary']
                    if 'Payment' in exec_summary:
                        payment_execution = execution_id
                        test_runs = execution_details['data']['testExecution']['testRuns']

                        for test_run in test_runs:
                            test_issue_id = test_run['test']['issueId']

                            # Fail the credit card test
                            if 'CreditCard' in test_run['test']['jira']['summary']:
                                fail_result = await tool.execute({
                                    'entity': 'test_run',
                                    'action': 'update_status',
                                    'test_execution_id': execution_id,
                                    'test_issue_id': test_issue_id,
                                    'status': 'FAILED',
                                    'comment': 'CRITICAL BUG: Credit card validation not working - Invalid cards accepted'
                                })

                                assert fail_result['success'], "Should update failed payment test"
                        break

            # Step 9: Verify release readiness assessment
            final_plan = await tool.execute({
                'entity': 'test_plan',
                'action': 'get',
                'issue_id': plan_id
            })

            assert final_plan['success'], "Should retrieve final plan state"

            # Count overall test execution status across all executions
            total_runs = 0
            passed_runs = 0
            failed_runs = 0

            for execution_id in execution_ids:
                execution_details = await tool.execute({
                    'entity': 'test_execution',
                    'action': 'get',
                    'issue_id': execution_id
                })

                if execution_details['success']:
                    test_runs = execution_details['data']['testExecution']['testRuns']
                    for test_run in test_runs:
                        total_runs += 1
                        status = test_run.get('status', {}).get('name', 'TODO')
                        if status == 'PASSED':
                            passed_runs += 1
                        elif status == 'FAILED':
                            failed_runs += 1

            # Verify we have executed some tests and have mixed results
            assert total_runs > 0, "Should have executed some tests"
            assert passed_runs > 0, "Should have some passed tests"
            assert failed_runs > 0, "Should have at least one failed test (payment bug)"

            # Release decision: Not ready due to critical payment bug
            assert failed_runs >= 1, "Release should be blocked by critical payment failure"

        finally:
            # Cleanup created resources in reverse order
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception as e:
                    print(f"Warning: Failed to cleanup {resource_type} {resource_id}: {e}")

    async def test_sprint_planning_workflow(self, tool, unique_prefix, project_key):
        """
        UC-142: Create sprint test plan.

        Tests creating focused test plans for agile sprints.
        """
        created_resources = []

        try:
            # Create sprint-specific tests
            sprint_tests = [
                {
                    'name': f'{unique_prefix}_Sprint_UserStory_001',
                    'user_story': 'US-001',
                    'type': 'Manual',
                    'priority': 'High',
                    'steps': [
                        {"action": "Test user story implementation", "data": "US-001 acceptance criteria", "result": "All criteria met"}
                    ]
                },
                {
                    'name': f'{unique_prefix}_Sprint_UserStory_002',
                    'user_story': 'US-002',
                    'type': 'Cucumber',
                    'priority': 'Medium',
                    'gherkin': '''Feature: Sprint User Story 002

                    Scenario: Implement user story functionality
                        Given the user story requirements are clear
                        When I implement the functionality
                        Then all acceptance criteria should be met'''
                }
            ]

            created_test_ids = []
            for test_data in sprint_tests:
                result = await tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': test_data['name'],
                    'test_type': test_data['type'],
                    'priority': test_data['priority'],
                    'steps': test_data.get('steps', '[]'),
                    'gherkin': test_data.get('gherkin'),
                    'description': f"Test for {test_data['user_story']} in current sprint"
                })

                assert result['success'], f"Failed to create sprint test: {result.get('errors', [])}"
                test_id = result['data']['issueId']
                created_test_ids.append(test_id)
                created_resources.append(('test', test_id))

            # Create sprint test plan
            plan_result = await tool.execute({
                'entity': 'test_plan',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_Sprint_15_Test_Plan',
                'description': 'Test plan for Sprint 15 - User Stories US-001 and US-002'
            })

            assert plan_result['success'], "Should create sprint test plan"
            plan_id = plan_result['data']['issueId']
            created_resources.append(('test_plan', plan_id))

            # Add sprint tests to plan
            add_tests_result = await tool.execute({
                'entity': 'test_plan',
                'action': 'add_tests',
                'issue_id': plan_id,
                'test_issue_ids': created_test_ids
            })

            assert add_tests_result['success'], "Should add tests to sprint plan"

            # Create sprint execution
            execution_result = await tool.execute({
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_Sprint_15_Execution',
                'description': 'Test execution for Sprint 15 features',
                'test_environments': ['Development']
            })

            assert execution_result['success'], "Should create sprint execution"
            execution_id = execution_result['data']['issueId']
            created_resources.append(('test_execution', execution_id))

            # Link execution to plan
            link_execution_result = await tool.execute({
                'entity': 'test_plan',
                'action': 'add_executions',
                'issue_id': plan_id,
                'test_exec_issue_ids': [execution_id]
            })

            assert link_execution_result['success'], "Should link execution to sprint plan"

            # Verify sprint plan structure
            plan_details = await tool.execute({
                'entity': 'test_plan',
                'action': 'get',
                'issue_id': plan_id
            })

            assert plan_details['success'], "Should retrieve sprint plan details"
            assert len(plan_details['data']['testPlan']['tests']) == 2, "Sprint plan should have 2 tests"

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception:
                    pass

    async def test_feature_test_plan_workflow(self, tool, unique_prefix, project_key):
        """
        UC-143: Create feature test plan.

        Tests organizing tests around specific feature development.
        """
        created_resources = []

        try:
            # Create comprehensive feature tests
            feature_name = "SearchFunctionality"
            feature_tests = [
                {
                    'name': f'{unique_prefix}_{feature_name}_BasicSearch',
                    'component': 'Search',
                    'type': 'Manual',
                    'priority': 'High',
                    'steps': [
                        {"action": "Enter search term", "data": "product name", "result": "Search results displayed"},
                        {"action": "Verify results relevance", "data": "Check result items", "result": "Results match search term"},
                        {"action": "Test result pagination", "data": "Navigate pages", "result": "Pagination works correctly"}
                    ]
                },
                {
                    'name': f'{unique_prefix}_{feature_name}_AdvancedSearch',
                    'component': 'Search',
                    'type': 'Manual',
                    'priority': 'Medium',
                    'steps': [
                        {"action": "Open advanced search", "data": "Advanced search link", "result": "Advanced form displayed"},
                        {"action": "Set multiple filters", "data": "Category, price range, rating", "result": "Filters applied"},
                        {"action": "Execute search", "data": "Search button", "result": "Filtered results displayed"}
                    ]
                },
                {
                    'name': f'{unique_prefix}_{feature_name}_SearchAPI',
                    'component': 'Search',
                    'type': 'Cucumber',
                    'priority': 'High',
                    'gherkin': '''Feature: Search API

                    Scenario: API search functionality
                        Given I have access to the search API
                        When I send a search request with query "laptop"
                        Then I should receive a 200 response
                        And the response should contain relevant products
                        And the results should be sorted by relevance'''
                }
            ]

            created_test_ids = []
            for test_data in feature_tests:
                result = await tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': test_data['name'],
                    'test_type': test_data['type'],
                    'priority': test_data['priority'],
                    'steps': test_data.get('steps', '[]'),
                    'gherkin': test_data.get('gherkin'),
                    'description': f"Test for {test_data['component']} component - {feature_name} feature"
                })

                assert result['success'], f"Failed to create feature test: {result.get('errors', [])}"
                test_id = result['data']['issueId']
                created_test_ids.append(test_id)
                created_resources.append(('test', test_id))

            # Create feature test plan
            plan_result = await tool.execute({
                'entity': 'test_plan',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_{feature_name}_Feature_Plan',
                'description': f'Comprehensive test plan for {feature_name} feature including UI and API testing'
            })

            assert plan_result['success'], "Should create feature test plan"
            plan_id = plan_result['data']['issueId']
            created_resources.append(('test_plan', plan_id))

            # Add feature tests to plan
            add_tests_result = await tool.execute({
                'entity': 'test_plan',
                'action': 'add_tests',
                'issue_id': plan_id,
                'test_issue_ids': created_test_ids
            })

            assert add_tests_result['success'], "Should add tests to feature plan"

            # Create multiple executions for different test phases
            execution_phases = [
                {'name': 'UI_Testing', 'env': ['UAT'], 'description': 'User interface testing phase'},
                {'name': 'API_Testing', 'env': ['Staging'], 'description': 'API and backend testing phase'},
                {'name': 'Integration_Testing', 'env': ['Integration'], 'description': 'End-to-end integration testing'}
            ]

            execution_ids = []
            for phase in execution_phases:
                execution_result = await tool.execute({
                    'entity': 'test_execution',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f"{unique_prefix}_{feature_name}_{phase['name']}",
                    'description': phase['description'],
                    'test_environments': phase['env']
                })

                assert execution_result['success'], f"Should create {phase['name']} execution"
                execution_id = execution_result['data']['issueId']
                execution_ids.append(execution_id)
                created_resources.append(('test_execution', execution_id))

            # Add executions to feature plan
            add_executions_result = await tool.execute({
                'entity': 'test_plan',
                'action': 'add_executions',
                'issue_id': plan_id,
                'test_exec_issue_ids': execution_ids
            })

            assert add_executions_result['success'], "Should add executions to feature plan"

            # Verify comprehensive feature plan
            plan_details = await tool.execute({
                'entity': 'test_plan',
                'action': 'get',
                'issue_id': plan_id
            })

            assert plan_details['success'], "Should retrieve feature plan details"
            plan_data = plan_details['data']['testPlan']

            assert len(plan_data['tests']) == 3, "Feature plan should have 3 tests"
            assert len(plan_data['testExecutions']) == 3, "Feature plan should have 3 executions"

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception:
                    pass

    async def test_cross_entity_operations_workflow(self, tool, unique_prefix, project_key):
        """
        UC-161 to UC-170: Test cross-entity operations.

        Tests moving, copying, and managing relationships between different entities.
        """
        created_resources = []

        try:
            # Create tests for movement operations
            moveable_tests = []
            for i in range(3):
                test_result = await tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_Moveable_Test_{i+1}',
                    'test_type': 'Manual',
                    'priority': 'Medium',
                    'steps': [
                        {"action": f"Execute test {i+1}", "data": f"Test data {i+1}", "result": f"Expected result {i+1}"}
                    ]
                })

                assert test_result['success'], f"Should create moveable test {i+1}"
                test_id = test_result['data']['issueId']
                moveable_tests.append(test_id)
                created_resources.append(('test', test_id))

            # Create multiple test plans for movement operations
            plan_ids = []
            plan_names = ['Source_Plan', 'Destination_Plan', 'Backup_Plan']

            for plan_name in plan_names:
                plan_result = await tool.execute({
                    'entity': 'test_plan',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_{plan_name}',
                    'description': f'Test plan for cross-entity operations: {plan_name}'
                })

                assert plan_result['success'], f"Should create {plan_name}"
                plan_id = plan_result['data']['issueId']
                plan_ids.append(plan_id)
                created_resources.append(('test_plan', plan_id))

            # UC-161: Move tests between plans
            source_plan_id, dest_plan_id, backup_plan_id = plan_ids

            # Add tests to source plan
            add_to_source = await tool.execute({
                'entity': 'test_plan',
                'action': 'add_tests',
                'issue_id': source_plan_id,
                'test_issue_ids': moveable_tests
            })

            assert add_to_source['success'], "Should add tests to source plan"

            # Verify tests are in source plan
            source_check = await tool.execute({
                'entity': 'test_plan',
                'action': 'get',
                'issue_id': source_plan_id
            })

            assert source_check['success'], "Should retrieve source plan"
            source_tests = source_check['data']['testPlan']['tests']
            assert len(source_tests) == 3, "Source plan should have 3 tests"

            # Move tests to destination plan (remove from source, add to destination)
            # First, add to destination
            add_to_dest = await tool.execute({
                'entity': 'test_plan',
                'action': 'add_tests',
                'issue_id': dest_plan_id,
                'test_issue_ids': moveable_tests[:2]  # Move only first 2 tests
            })

            assert add_to_dest['success'], "Should add tests to destination plan"

            # Remove from source
            remove_from_source = await tool.execute({
                'entity': 'test_plan',
                'action': 'remove_tests',
                'issue_id': source_plan_id,
                'test_issue_ids': moveable_tests[:2]
            })

            assert remove_from_source['success'], "Should remove tests from source plan"

            # Verify movement completed
            source_final = await tool.execute({
                'entity': 'test_plan',
                'action': 'get',
                'issue_id': source_plan_id
            })

            dest_final = await tool.execute({
                'entity': 'test_plan',
                'action': 'get',
                'issue_id': dest_plan_id
            })

            assert source_final['success'] and dest_final['success'], "Should retrieve both plans"
            assert len(source_final['data']['testPlan']['tests']) == 1, "Source should have 1 remaining test"
            assert len(dest_final['data']['testPlan']['tests']) == 2, "Destination should have 2 moved tests"

            # UC-166: Archive and UC-167: Restore operations simulation
            # We'll simulate archiving by removing all tests from a plan, then restoring

            # "Archive" backup plan by ensuring it's empty
            backup_check = await tool.execute({
                'entity': 'test_plan',
                'action': 'get',
                'issue_id': backup_plan_id
            })

            assert backup_check['success'], "Should check backup plan"
            # Backup plan should be empty (represents archived state)

            # "Restore" by adding tests to backup plan
            restore_result = await tool.execute({
                'entity': 'test_plan',
                'action': 'add_tests',
                'issue_id': backup_plan_id,
                'test_issue_ids': [moveable_tests[2]]  # Restore the remaining test
            })

            assert restore_result['success'], "Should restore test to backup plan"

            # Verify restore
            restored_check = await tool.execute({
                'entity': 'test_plan',
                'action': 'get',
                'issue_id': backup_plan_id
            })

            assert restored_check['success'], "Should check restored plan"
            assert len(restored_check['data']['testPlan']['tests']) == 1, "Restored plan should have 1 test"

            # UC-169: Simulate migration to new project (same project but different plan)
            # This demonstrates the pattern for cross-project migration
            migration_plan = await tool.execute({
                'entity': 'test_plan',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_Migration_Target',
                'description': 'Target plan for migration simulation'
            })

            assert migration_plan['success'], "Should create migration target plan"
            migration_plan_id = migration_plan['data']['issueId']
            created_resources.append(('test_plan', migration_plan_id))

            # Migrate all tests to new plan
            migrate_result = await tool.execute({
                'entity': 'test_plan',
                'action': 'add_tests',
                'issue_id': migration_plan_id,
                'test_issue_ids': moveable_tests
            })

            assert migrate_result['success'], "Should migrate tests to new plan"

            # Verify migration
            migration_check = await tool.execute({
                'entity': 'test_plan',
                'action': 'get',
                'issue_id': migration_plan_id
            })

            assert migration_check['success'], "Should check migrated plan"
            assert len(migration_check['data']['testPlan']['tests']) == 3, "Migrated plan should have all 3 tests"

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception:
                    pass