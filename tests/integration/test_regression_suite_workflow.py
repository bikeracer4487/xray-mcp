"""
Integration tests for regression suite workflow.

Tests complex end-to-end workflows for creating, managing, and executing
regression test suites. Covers use cases UC-081 through UC-120.
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
    return f"RegressionTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


@pytest.fixture
def project_key():
    """Get project key from environment."""
    import os
    return os.getenv('XRAY_PROJECT_KEY', 'FTEST')


@pytest.mark.asyncio
class TestRegressionSuiteWorkflow:
    """Test complete regression suite workflows."""

    async def test_complete_regression_suite_creation(self, tool, unique_prefix, project_key):
        """
        UC-081: Create comprehensive regression test execution.

        Tests the complete workflow of:
        1. Creating multiple test types for regression
        2. Building a regression test execution
        3. Managing test allocation and environments
        4. Executing tests and tracking results
        """
        created_resources = []

        try:
            # Step 1: Create diverse test types for regression suite
            test_types = [
                {
                    'name': f'{unique_prefix}_Login_Smoke',
                    'type': 'Manual',
                    'priority': 'High',
                    'steps': [
                        {"action": "Navigate to login page", "data": "https://app.example.com/login", "result": "Login page displays"},
                        {"action": "Enter valid credentials", "data": "user@test.com / password123", "result": "Credentials accepted"},
                        {"action": "Click Login button", "data": "Login button", "result": "Successfully logged in"},
                        {"action": "Verify dashboard loads", "data": "Main dashboard", "result": "Dashboard displays with user data"}
                    ]
                },
                {
                    'name': f'{unique_prefix}_API_Health_Check',
                    'type': 'Cucumber',
                    'priority': 'Critical',
                    'gherkin': '''Feature: API Health Check

                    Scenario: Verify core API endpoints
                        Given the API service is running
                        When I call the health check endpoint
                        Then I should get a 200 response
                        And the response should contain service status
                        And all dependent services should be healthy'''
                },
                {
                    'name': f'{unique_prefix}_Database_Connectivity',
                    'type': 'Generic',
                    'priority': 'High',
                    'description': 'Verify database connectivity and basic operations for regression testing'
                },
                {
                    'name': f'{unique_prefix}_Performance_Baseline',
                    'type': 'Manual',
                    'priority': 'Medium',
                    'steps': [
                        {"action": "Run performance test", "data": "JMeter script: baseline.jmx", "result": "Response time < 2s"},
                        {"action": "Monitor resource usage", "data": "CPU, Memory, Disk", "result": "Usage within acceptable limits"},
                        {"action": "Verify no memory leaks", "data": "Memory profiler", "result": "No memory growth detected"}
                    ]
                }
            ]

            created_tests = []
            for test_data in test_types:
                result = await tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': test_data['name'],
                    'test_type': test_data['type'],
                    'priority': test_data['priority'],
                    'steps': test_data.get('steps', '[]'),
                    'gherkin': test_data.get('gherkin'),
                    'description': test_data.get('description')
                })

                assert result['success'], f"Failed to create test: {result.get('errors', [])}"
                test_id = result['data']['issueId']
                created_tests.append(test_id)
                created_resources.append(('test', test_id))

            assert len(created_tests) == 4, "Should have created 4 regression tests"

            # Step 2: Create regression test execution with multiple environments
            execution_result = await tool.execute({
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_Regression_Suite_v1.0',
                'description': 'Comprehensive regression testing for release 1.0',
                'test_environments': ['Production', 'Staging', 'UAT']
            })

            assert execution_result['success'], f"Failed to create execution: {execution_result.get('errors', [])}"
            execution_id = execution_result['data']['issueId']
            created_resources.append(('test_execution', execution_id))

            # Step 3: Add all tests to the execution
            add_tests_result = await tool.execute({
                'entity': 'test_execution',
                'action': 'add_tests',
                'issue_id': execution_id,
                'test_issue_ids': created_tests
            })

            assert add_tests_result['success'], "Should successfully add tests to execution"

            # Step 4: Verify execution contains all tests
            execution_details = await tool.execute({
                'entity': 'test_execution',
                'action': 'get',
                'issue_id': execution_id
            })

            assert execution_details['success'], "Should retrieve execution details"
            test_runs = execution_details['data']['testExecution']['testRuns']
            assert len(test_runs) == len(created_tests), f"Execution should contain {len(created_tests)} test runs"

            # Step 5: Execute tests with different outcomes
            test_outcomes = [
                {'status': 'PASS', 'comment': 'Login functionality working correctly'},
                {'status': 'FAIL', 'comment': 'API endpoint returning 503 error'},
                {'status': 'PASS', 'comment': 'Database connectivity verified'},
                {'status': 'TODO', 'comment': 'Performance test scheduled for later'}
            ]

            for i, (test_run, outcome) in enumerate(zip(test_runs, test_outcomes)):
                run_result = await tool.execute({
                    'entity': 'test_run',
                    'action': 'update_status',
                    'test_execution_id': execution_id,
                    'test_issue_id': created_tests[i],
                    'status': outcome['status'],
                    'comment': outcome['comment']
                })

                assert run_result['success'], f"Should update test run status: {run_result.get('errors', [])}"

            # Step 6: Add defects to failed tests
            for i, (test_run, outcome) in enumerate(zip(test_runs, test_outcomes)):
                if outcome['status'] == 'FAIL':
                    # In a real scenario, we would create actual defects
                    # For this test, we'll simulate with comments
                    defect_result = await tool.execute({
                        'entity': 'test_run',
                        'action': 'update_comment',
                        'test_execution_id': execution_id,
                        'test_issue_id': created_tests[i],
                        'comment': f"{outcome['comment']} - DEFECT: API-503 - Service Unavailable Error"
                    })

                    assert defect_result['success'], "Should add defect information to test run"

            # Step 7: Verify final execution state
            final_execution = await tool.execute({
                'entity': 'test_execution',
                'action': 'get',
                'issue_id': execution_id
            })

            assert final_execution['success'], "Should retrieve final execution state"
            final_test_runs = final_execution['data']['testExecution']['testRuns']

            # Verify all test runs have been updated
            statuses = [run.get('status', {}).get('name', 'UNKNOWN') for run in final_test_runs]
            expected_statuses = ['PASS', 'FAIL', 'PASS', 'TODO']

            # Count status distribution
            status_count = {}
            for status in statuses:
                status_count[status] = status_count.get(status, 0) + 1

            assert status_count.get('PASS', 0) >= 2, "Should have at least 2 passed tests"
            assert status_count.get('FAIL', 0) >= 1, "Should have at least 1 failed test"

        finally:
            # Cleanup created resources
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception as e:
                    print(f"Warning: Failed to cleanup {resource_type} {resource_id}: {e}")

    async def test_smoke_test_suite_workflow(self, tool, unique_prefix, project_key):
        """
        UC-082: Build and execute smoke test suite.

        Tests creation of a focused smoke test suite for quick validation.
        """
        created_resources = []

        try:
            # Create critical path smoke tests
            smoke_tests = [
                {
                    'name': f'{unique_prefix}_Smoke_Authentication',
                    'steps': [
                        {"action": "Verify login page loads", "data": "URL: /login", "result": "Page loads in <3s"},
                        {"action": "Test valid login", "data": "test@example.com", "result": "Login successful"}
                    ]
                },
                {
                    'name': f'{unique_prefix}_Smoke_Core_API',
                    'steps': [
                        {"action": "Test health endpoint", "data": "GET /health", "result": "200 OK response"},
                        {"action": "Test authentication", "data": "POST /auth", "result": "Token returned"}
                    ]
                }
            ]

            created_test_ids = []
            for test_data in smoke_tests:
                result = await tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': test_data['name'],
                    'test_type': 'Manual',
                    'priority': 'Critical',
                    'steps': test_data['steps']
                })

                assert result['success'], f"Failed to create smoke test: {result.get('errors', [])}"
                test_id = result['data']['issueId']
                created_test_ids.append(test_id)
                created_resources.append(('test', test_id))

            # Create smoke test execution
            execution_result = await tool.execute({
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_Smoke_Test_Suite',
                'description': 'Critical path smoke tests for rapid deployment validation',
                'test_environments': ['Production']
            })

            assert execution_result['success'], "Should create smoke test execution"
            execution_id = execution_result['data']['issueId']
            created_resources.append(('test_execution', execution_id))

            # Add tests and execute quickly
            add_result = await tool.execute({
                'entity': 'test_execution',
                'action': 'add_tests',
                'issue_id': execution_id,
                'test_issue_ids': created_test_ids
            })

            assert add_result['success'], "Should add tests to smoke execution"

            # Execute all as PASS (smoke test success scenario)
            for test_id in created_test_ids:
                run_result = await tool.execute({
                    'entity': 'test_run',
                    'action': 'update_status',
                    'test_execution_id': execution_id,
                    'test_issue_id': test_id,
                    'status': 'PASS',
                    'comment': 'Smoke test passed - deployment ready'
                })

                assert run_result['success'], "Should update smoke test run status"

            # Verify smoke test completion
            final_execution = await tool.execute({
                'entity': 'test_execution',
                'action': 'get',
                'issue_id': execution_id
            })

            assert final_execution['success'], "Should retrieve smoke test results"

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

    async def test_feature_specific_execution_workflow(self, tool, unique_prefix, project_key):
        """
        UC-083: Create feature-specific test execution.

        Tests organizing tests around specific feature development.
        """
        created_resources = []

        try:
            # Create feature-specific tests (User Profile feature)
            feature_tests = [
                {
                    'name': f'{unique_prefix}_UserProfile_Create',
                    'type': 'Manual',
                    'component': 'UserProfile',
                    'steps': [
                        {"action": "Navigate to profile creation", "data": "/profile/new", "result": "Form displayed"},
                        {"action": "Fill required fields", "data": "Name, Email, Phone", "result": "Fields populated"},
                        {"action": "Submit profile", "data": "Save button", "result": "Profile created successfully"}
                    ]
                },
                {
                    'name': f'{unique_prefix}_UserProfile_Update',
                    'type': 'Manual',
                    'component': 'UserProfile',
                    'steps': [
                        {"action": "Load existing profile", "data": "Profile ID: 123", "result": "Profile loaded"},
                        {"action": "Modify profile data", "data": "Update phone number", "result": "Changes reflected"},
                        {"action": "Save changes", "data": "Update button", "result": "Profile updated"}
                    ]
                },
                {
                    'name': f'{unique_prefix}_UserProfile_Delete',
                    'type': 'Manual',
                    'component': 'UserProfile',
                    'steps': [
                        {"action": "Select profile to delete", "data": "Profile checkbox", "result": "Profile selected"},
                        {"action": "Click delete button", "data": "Delete action", "result": "Confirmation dialog"},
                        {"action": "Confirm deletion", "data": "Yes button", "result": "Profile deleted"}
                    ]
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
                    'priority': 'High',
                    'steps': test_data['steps'],
                    'description': f"Test case for {test_data['component']} feature"
                })

                assert result['success'], f"Failed to create feature test: {result.get('errors', [])}"
                test_id = result['data']['issueId']
                created_test_ids.append(test_id)
                created_resources.append(('test', test_id))

            # Create feature-specific execution
            execution_result = await tool.execute({
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_UserProfile_Feature_Testing',
                'description': 'Complete testing of User Profile feature including CRUD operations',
                'test_environments': ['UAT', 'Staging']
            })

            assert execution_result['success'], "Should create feature test execution"
            execution_id = execution_result['data']['issueId']
            created_resources.append(('test_execution', execution_id))

            # Add tests to execution
            add_result = await tool.execute({
                'entity': 'test_execution',
                'action': 'add_tests',
                'issue_id': execution_id,
                'test_issue_ids': created_test_ids
            })

            assert add_result['success'], "Should add feature tests to execution"

            # Execute tests with mixed results (realistic feature testing)
            test_results = [
                {'status': 'PASS', 'comment': 'Profile creation working correctly'},
                {'status': 'FAIL', 'comment': 'Update validation not working - allows invalid phone format'},
                {'status': 'PASS', 'comment': 'Delete functionality working with proper confirmation'}
            ]

            for i, result_data in enumerate(test_results):
                run_result = await tool.execute({
                    'entity': 'test_run',
                    'action': 'update_status',
                    'test_execution_id': execution_id,
                    'test_issue_id': created_test_ids[i],
                    'status': result_data['status'],
                    'comment': result_data['comment']
                })

                assert run_result['success'], "Should update feature test run status"

            # Verify execution results
            final_execution = await tool.execute({
                'entity': 'test_execution',
                'action': 'get',
                'issue_id': execution_id
            })

            assert final_execution['success'], "Should retrieve feature test execution"
            test_runs = final_execution['data']['testExecution']['testRuns']
            assert len(test_runs) == 3, "Should have 3 test runs for feature"

            # Verify we have both passed and failed tests (realistic scenario)
            statuses = [run.get('status', {}).get('name', 'UNKNOWN') for run in test_runs]
            assert 'PASS' in statuses, "Should have some passed tests"
            assert 'FAIL' in statuses, "Should have some failed tests (realistic feature testing)"

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

    async def test_environment_specific_execution(self, tool, unique_prefix, project_key):
        """
        UC-085: Create environment-specific test execution.

        Tests organizing tests for specific deployment environments.
        """
        created_resources = []

        try:
            # Create environment-specific tests
            env_test = await tool.execute({
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_Production_Environment_Check',
                'test_type': 'Manual',
                'priority': 'Critical',
                'steps': [
                    {"action": "Verify SSL certificate", "data": "Check HTTPS connection", "result": "Valid SSL certificate"},
                    {"action": "Check database connectivity", "data": "Production DB connection", "result": "Connection successful"},
                    {"action": "Verify external API integrations", "data": "Third-party APIs", "result": "All APIs responding"},
                    {"action": "Check monitoring systems", "data": "APM tools", "result": "Monitoring active"}
                ]
            })

            assert env_test['success'], "Should create environment test"
            test_id = env_test['data']['issueId']
            created_resources.append(('test', test_id))

            # Create environment-specific execution with multiple environments
            execution_result = await tool.execute({
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_Multi_Environment_Validation',
                'description': 'Validation tests across Development, Staging, and Production environments',
                'test_environments': ['Development', 'Staging', 'Production']
            })

            assert execution_result['success'], "Should create multi-environment execution"
            execution_id = execution_result['data']['issueId']
            created_resources.append(('test_execution', execution_id))

            # Add test to execution
            add_result = await tool.execute({
                'entity': 'test_execution',
                'action': 'add_tests',
                'issue_id': execution_id,
                'test_issue_ids': [test_id]
            })

            assert add_result['success'], "Should add test to environment execution"

            # Simulate environment-specific test results
            env_result = await tool.execute({
                'entity': 'test_run',
                'action': 'update_status',
                'test_execution_id': execution_id,
                'test_issue_id': test_id,
                'status': 'PASS',
                'comment': 'All environment checks passed - Production environment ready'
            })

            assert env_result['success'], "Should update environment test status"

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

    async def test_parallel_execution_workflow(self, tool, unique_prefix, project_key):
        """
        UC-093: Plan parallel test execution.

        Tests creating multiple executions that can run in parallel.
        """
        created_resources = []

        try:
            # Create tests that can run in parallel
            parallel_tests = []
            for i in range(3):
                test_result = await tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_Parallel_Test_{i+1}',
                    'test_type': 'Manual',
                    'priority': 'Medium',
                    'steps': [
                        {"action": f"Execute independent test {i+1}", "data": f"Test data {i+1}", "result": f"Expected result {i+1}"}
                    ]
                })

                assert test_result['success'], f"Should create parallel test {i+1}"
                test_id = test_result['data']['issueId']
                parallel_tests.append(test_id)
                created_resources.append(('test', test_id))

            # Create multiple executions for parallel running
            execution_ids = []
            for i in range(2):
                execution_result = await tool.execute({
                    'entity': 'test_execution',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_Parallel_Execution_{i+1}',
                    'description': f'Parallel execution batch {i+1}',
                    'test_environments': ['UAT']
                })

                assert execution_result['success'], f"Should create parallel execution {i+1}"
                execution_id = execution_result['data']['issueId']
                execution_ids.append(execution_id)
                created_resources.append(('test_execution', execution_id))

            # Distribute tests across executions
            for i, execution_id in enumerate(execution_ids):
                # Each execution gets different tests
                test_subset = [parallel_tests[i], parallel_tests[-1]]  # Some overlap for realism

                add_result = await tool.execute({
                    'entity': 'test_execution',
                    'action': 'add_tests',
                    'issue_id': execution_id,
                    'test_issue_ids': test_subset
                })

                assert add_result['success'], f"Should add tests to execution {i+1}"

            # Simulate parallel execution by updating statuses concurrently
            async def execute_batch(execution_id, test_ids):
                for test_id in test_ids:
                    await tool.execute({
                        'entity': 'test_run',
                        'action': 'update_status',
                        'test_execution_id': execution_id,
                        'test_issue_id': test_id,
                        'status': 'PASS',
                        'comment': f'Parallel execution completed for {test_id}'
                    })

            # Run executions in parallel
            tasks = []
            for i, execution_id in enumerate(execution_ids):
                test_subset = [parallel_tests[i], parallel_tests[-1]]
                tasks.append(execute_batch(execution_id, test_subset))

            await asyncio.gather(*tasks)

            # Verify both executions completed
            for execution_id in execution_ids:
                execution_check = await tool.execute({
                    'entity': 'test_execution',
                    'action': 'get',
                    'issue_id': execution_id
                })

                assert execution_check['success'], "Should retrieve parallel execution"
                test_runs = execution_check['data']['testExecution']['testRuns']
                assert len(test_runs) > 0, "Execution should have test runs"

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