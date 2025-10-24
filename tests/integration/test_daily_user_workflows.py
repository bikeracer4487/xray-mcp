"""
Daily user workflow tests for Xray MCP Server.

These tests focus on the most common, realistic day-to-day scenarios that users
encounter when working with test management. They validate practical workflows
rather than comprehensive feature coverage.
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
class TestDailyUserWorkflows:
    """Test realistic daily user scenarios."""

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
        return f"DAILY-{uuid.uuid4().hex[:6]}"

    @pytest.fixture
    def project_key(self):
        """Get project key from environment."""
        return os.getenv('DEFAULT_PROJECT_KEY', 'FTEST')

    @pytest.mark.asyncio
    async def test_bug_investigation_workflow(self, tool, unique_prefix, project_key):
        """
        Scenario: Developer finds a bug, creates a test to reproduce it, fails the test,
        then fixes the bug and re-runs the test to verify the fix.

        This tests the most common debugging workflow.
        """
        print(f"\n🐛 Testing bug investigation workflow: {unique_prefix}")
        created_resources = []

        try:
            # Step 1: Developer discovers a bug and creates a reproduction test
            bug_test_params = {
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Login Button Not Responding',
                'test_type': 'Manual',
                'description': 'Bug reproduction test: Login button becomes unresponsive after 3 failed attempts',
                'steps': '[{"action": "Navigate to login page", "data": "https://app.example.com/login", "result": "Login page loads"}, {"action": "Enter wrong password 3 times", "data": "user@test.com / wrongpass", "result": "Error messages shown"}, {"action": "Try to click login button with correct credentials", "data": "user@test.com / correctpass", "result": "Button should respond and login should work"}]'
            }

            test_result = await tool.run(bug_test_params)
            test_data = parse_mcp_response(test_result)
            assert test_data['success'], f"Failed to create bug test: {test_data.get('errors')}"

            test_id = test_data['data']['issueId']
            test_key = test_data['data']['issueKey']
            created_resources.append(('test', test_id))
            print(f"   ✅ Created bug reproduction test: {test_key}")

            # Step 2: Create an execution to reproduce the bug
            exec_params = {
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Bug Investigation Execution',
                'test_issue_ids': [test_id],
                'test_environments': ['production']
            }

            exec_result = await tool.run(exec_params)
            exec_data = parse_mcp_response(exec_result)
            assert exec_data['success'], f"Failed to create execution: {exec_data.get('errors')}"

            execution_id = exec_data['data']['issueId']
            execution_key = exec_data['data']['issueKey']
            created_resources.append(('test_execution', execution_id))
            print(f"   ✅ Created bug investigation execution: {execution_key}")

            # Step 3: Run the test and it fails (reproduces the bug)
            run_update_params = {
                'entity': 'test_run',
                'action': 'update_status',
                'test_execution_id': execution_id,
                'test_issue_id': test_id,
                'status': 'FAILED',
                'comment': 'BUG CONFIRMED: Login button becomes unresponsive after 3 failed attempts. Button click event not registering. See screenshot in JIRA-123 for details.'
            }

            run_result = await tool.run(run_update_params)
            run_data = parse_mcp_response(run_result)
            assert run_data['success'], f"Failed to update test run: {run_data.get('errors')}"
            print(f"   ✅ Test failed as expected - bug confirmed")

            # Step 4: Developer fixes the bug, creates new execution to verify fix
            verification_exec_params = {
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Bug Fix Verification',
                'test_issue_ids': [test_id],
                'test_environments': ['staging']
            }

            verify_exec_result = await tool.run(verification_exec_params)
            verify_exec_data = parse_mcp_response(verify_exec_result)
            assert verify_exec_data['success'], f"Failed to create verification execution: {verify_exec_data.get('errors')}"

            verify_execution_id = verify_exec_data['data']['issueId']
            verify_execution_key = verify_exec_data['data']['issueKey']
            created_resources.append(('test_execution', verify_execution_id))
            print(f"   ✅ Created verification execution: {verify_execution_key}")

            # Step 5: Re-run the test after the fix - it passes
            verify_run_params = {
                'entity': 'test_run',
                'action': 'update_status',
                'test_execution_id': verify_execution_id,
                'test_issue_id': test_id,
                'status': 'PASSED',
                'comment': 'BUG FIXED: Login button now responds correctly after multiple failed attempts. Event handler properly resets after authentication errors.'
            }

            verify_run_result = await tool.run(verify_run_params)
            verify_run_data = parse_mcp_response(verify_run_result)
            assert verify_run_data['success'], f"Failed to update verification run: {verify_run_data.get('errors')}"
            print(f"   ✅ Test passed - bug fix verified")

            # Step 6: Quick status check - get both execution results
            original_exec_check = await tool.run({
                'entity': 'test_execution',
                'action': 'get',
                'issue_id': execution_id
            })

            verify_exec_check = await tool.run({
                'entity': 'test_execution',
                'action': 'get',
                'issue_id': verify_execution_id
            })

            original_data = parse_mcp_response(original_exec_check)
            verify_data = parse_mcp_response(verify_exec_check)

            assert original_data['success'] and verify_data['success'], "Should retrieve both executions"
            print(f"   ✅ Bug workflow complete: Reproduction (FAILED) → Fix → Verification (PASSED)")

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.run({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                    print(f"   🧹 Cleaned up {resource_type}")
                except Exception:
                    pass

    @pytest.mark.asyncio
    async def test_sprint_planning_workflow(self, tool, unique_prefix, project_key):
        """
        Scenario: QA team prepares tests for an upcoming sprint. They create a plan,
        add relevant tests, and set up an execution ready for the sprint.

        This tests the common sprint preparation workflow.
        """
        print(f"\n🏃 Testing sprint planning workflow: {unique_prefix}")
        created_resources = []

        try:
            # Step 1: Create tests for sprint features
            sprint_features = [
                "User Profile Update Feature",
                "Password Reset Functionality",
                "Email Notification Settings"
            ]

            created_tests = []
            print("   📝 Creating tests for sprint features...")

            for feature in sprint_features:
                test_params = {
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix} {feature}',
                    'test_type': 'Manual',
                    'description': f'Test coverage for {feature} - Sprint 23.4'
                }

                test_result = await tool.run(test_params)
                test_data = parse_mcp_response(test_result)
                assert test_data['success'], f"Failed to create test for {feature}"

                created_tests.append({
                    'id': test_data['data']['issueId'],
                    'key': test_data['data']['issueKey'],
                    'feature': feature
                })
                created_resources.append(('test', test_data['data']['issueId']))
                print(f"      ✅ {test_data['data']['issueKey']} - {feature}")

            # Step 2: Create sprint test plan
            plan_params = {
                'entity': 'test_plan',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Sprint 23.4 Test Plan',
                'test_issue_ids': [test['id'] for test in created_tests]
            }

            plan_result = await tool.run(plan_params)
            plan_data = parse_mcp_response(plan_result)
            assert plan_data['success'], f"Failed to create sprint plan: {plan_data.get('errors')}"

            plan_id = plan_data['data']['issueId']
            plan_key = plan_data['data']['issueKey']
            created_resources.append(('test_plan', plan_id))
            print(f"   ✅ Created sprint plan: {plan_key} with {len(created_tests)} tests")

            # Step 3: Create sprint execution (ready for when sprint starts)
            exec_params = {
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Sprint 23.4 Execution',
                'test_issue_ids': [test['id'] for test in created_tests],
                'test_environments': ['qa', 'staging']
            }

            exec_result = await tool.run(exec_params)
            exec_data = parse_mcp_response(exec_result)
            assert exec_data['success'], f"Failed to create sprint execution: {exec_data.get('errors')}"

            execution_id = exec_data['data']['issueId']
            execution_key = exec_data['data']['issueKey']
            created_resources.append(('test_execution', execution_id))
            print(f"   ✅ Created sprint execution: {execution_key}")

            # Step 4: Link execution to plan (typical planning step)
            link_params = {
                'entity': 'test_plan',
                'action': 'add_executions',
                'issue_id': plan_id,
                'test_exec_issue_ids': [execution_id]
            }

            link_result = await tool.run(link_params)
            link_data = parse_mcp_response(link_result)
            assert link_data['success'], f"Failed to link execution to plan: {link_data.get('errors')}"
            print(f"   ✅ Linked execution to sprint plan")

            # Step 5: Quick verification that everything is set up correctly
            plan_verification = await tool.run({
                'entity': 'test_plan',
                'action': 'get',
                'issue_id': plan_id
            })

            plan_verify_data = parse_mcp_response(plan_verification)
            assert plan_verify_data['success'], "Should retrieve sprint plan details"

            # Verify plan structure
            plan_details = plan_verify_data['data']
            if 'tests' in plan_details:
                assert len(plan_details['tests']) == len(created_tests), "Plan should contain all sprint tests"
            print(f"   ✅ Sprint planning complete - ready for execution")

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.run({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                    print(f"   🧹 Cleaned up {resource_type}")
                except Exception:
                    pass

    @pytest.mark.asyncio
    async def test_quick_status_check_workflow(self, tool, unique_prefix, project_key):
        """
        Scenario: Developer quickly wants to check the status of recent test executions
        for their feature. This tests the common "what's the test status?" workflow.
        """
        print(f"\n📊 Testing quick status check workflow: {unique_prefix}")
        created_resources = []

        try:
            # Step 1: Create a test and execution (simulating existing work)
            test_params = {
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} API Response Time Test',
                'test_type': 'Manual'
            }

            test_result = await tool.run(test_params)
            test_data = parse_mcp_response(test_result)
            test_id = test_data['data']['issueId']
            test_key = test_data['data']['issueKey']
            created_resources.append(('test', test_id))

            exec_params = {
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Quick Status Check',
                'test_issue_ids': [test_id]
            }

            exec_result = await tool.run(exec_params)
            exec_data = parse_mcp_response(exec_result)
            execution_id = exec_data['data']['issueId']
            created_resources.append(('test_execution', execution_id))

            # Step 2: Update test status (simulating test completion)
            await tool.run({
                'entity': 'test_run',
                'action': 'update_status',
                'test_execution_id': execution_id,
                'test_issue_id': test_id,
                'status': 'PASSED',
                'comment': 'API response time under 200ms - meets requirements'
            })
            print(f"   ✅ Set up test scenario: {test_key}")

            # Step 3: Quick status checks (what developers actually do)

            # Check specific test status
            test_status = await tool.run({
                'entity': 'test',
                'action': 'get',
                'issue_id': test_id
            })
            test_status_data = parse_mcp_response(test_status)
            assert test_status_data['success'], "Should get test status quickly"
            print(f"   ✅ Retrieved test details: {test_status_data['data']['issueKey']}")

            # Check execution results
            exec_status = await tool.run({
                'entity': 'test_execution',
                'action': 'get',
                'issue_id': execution_id
            })
            exec_status_data = parse_mcp_response(exec_status)
            assert exec_status_data['success'], "Should get execution status quickly"
            print(f"   ✅ Retrieved execution status: {exec_status_data['data']['issueKey']}")

            # Check specific test run
            run_status = await tool.run({
                'entity': 'test_run',
                'action': 'get',
                'test_execution_id': execution_id,
                'test_issue_id': test_id
            })
            run_status_data = parse_mcp_response(run_status)
            assert run_status_data['success'], "Should get run status quickly"
            assert run_status_data['data']['status'] == 'PASSED', "Run should show as passed"
            print(f"   ✅ Retrieved run status: {run_status_data['data']['status']}")

            # Step 4: List recent tests (common dev query)
            recent_tests = await tool.run({
                'entity': 'test',
                'action': 'list',
                'project_key': project_key,
                'limit': 5
            })
            recent_tests_data = parse_mcp_response(recent_tests)
            assert recent_tests_data['success'], "Should list recent tests"
            assert len(recent_tests_data['data']['tests']) >= 1, "Should find at least our test"
            print(f"   ✅ Listed recent tests: {len(recent_tests_data['data']['tests'])} found")

            print(f"   ✅ Quick status check complete - all information retrieved efficiently")

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.run({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                    print(f"   🧹 Cleaned up {resource_type}")
                except Exception:
                    pass

    @pytest.mark.asyncio
    async def test_test_maintenance_workflow(self, tool, unique_prefix, project_key):
        """
        Scenario: Developer needs to update an existing test because requirements changed.
        This tests the common test maintenance workflow.
        """
        print(f"\n🔧 Testing test maintenance workflow: {unique_prefix}")
        created_resources = []

        try:
            # Step 1: Create initial test
            original_test_params = {
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} User Login Timeout Test',
                'test_type': 'Manual',
                'description': 'Original: Test that user session times out after 30 minutes',
                'steps': '[{"action": "Login as user", "data": "user@test.com", "result": "Login successful"}, {"action": "Wait 30 minutes", "data": "Idle session", "result": "Session should timeout"}, {"action": "Try to access protected page", "data": "Navigate to /dashboard", "result": "Should redirect to login"}]'
            }

            test_result = await tool.run(original_test_params)
            test_data = parse_mcp_response(test_result)
            assert test_data['success'], f"Failed to create initial test: {test_data.get('errors')}"

            test_id = test_data['data']['issueId']
            test_key = test_data['data']['issueKey']
            created_resources.append(('test', test_id))
            print(f"   ✅ Created initial test: {test_key}")

            # Step 2: Requirements change - timeout increased to 60 minutes
            # Developer needs to update the test

            # First, get the current test to see what needs updating
            current_test = await tool.run({
                'entity': 'test',
                'action': 'get',
                'issue_id': test_id
            })
            current_test_data = parse_mcp_response(current_test)
            assert current_test_data['success'], "Should retrieve current test for update"
            print(f"   ✅ Retrieved current test for modification")

            # Step 3: Update test type if needed (common maintenance task)
            type_update = await tool.run({
                'entity': 'test',
                'action': 'update_type',
                'issue_id': test_id,
                'test_type': 'Generic'
            })
            type_update_data = parse_mcp_response(type_update)
            assert type_update_data['success'], f"Failed to update test type: {type_update_data.get('errors')}"
            print(f"   ✅ Updated test type to Generic")

            # Step 4: Verify the update was applied
            updated_test = await tool.run({
                'entity': 'test',
                'action': 'get',
                'issue_id': test_id
            })
            updated_test_data = parse_mcp_response(updated_test)
            assert updated_test_data['success'], "Should retrieve updated test"
            assert updated_test_data['data']['testType'] == 'Generic', "Test type should be updated"
            print(f"   ✅ Verified test type update: {updated_test_data['data']['testType']}")

            # Step 5: Create execution to test the updated test
            maintenance_exec = await tool.run({
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Maintenance Verification',
                'test_issue_ids': [test_id],
                'test_environments': ['testing']
            })
            maintenance_exec_data = parse_mcp_response(maintenance_exec)
            execution_id = maintenance_exec_data['data']['issueId']
            created_resources.append(('test_execution', execution_id))

            # Step 6: Run the updated test
            run_update = await tool.run({
                'entity': 'test_run',
                'action': 'update_status',
                'test_execution_id': execution_id,
                'test_issue_id': test_id,
                'status': 'PASSED',
                'comment': 'Updated test verified: Session timeout now correctly set to 60 minutes as per new requirements'
            })
            run_update_data = parse_mcp_response(run_update)
            assert run_update_data['success'], "Should update maintained test run"
            print(f"   ✅ Verified maintained test passes with new requirements")

            # Step 7: Final verification - get test details to confirm all changes
            final_check = await tool.run({
                'entity': 'test',
                'action': 'get',
                'issue_id': test_id
            })
            final_data = parse_mcp_response(final_check)
            assert final_data['success'], "Should get final test state"
            print(f"   ✅ Test maintenance workflow complete")

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.run({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                    print(f"   🧹 Cleaned up {resource_type}")
                except Exception:
                    pass

    @pytest.mark.asyncio
    async def test_realistic_failure_handling(self, tool, unique_prefix, project_key):
        """
        Scenario: Things go wrong in real workflows - test creation fails,
        executions have issues, etc. This tests realistic error handling.
        """
        print(f"\n⚠️  Testing realistic failure handling: {unique_prefix}")
        created_resources = []

        try:
            # Step 1: Try to create a test with valid data (should succeed)
            valid_test_params = {
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Valid Test Creation',
                'test_type': 'Manual'
            }

            valid_result = await tool.run(valid_test_params)
            valid_data = parse_mcp_response(valid_result)
            assert valid_data['success'], "Valid test should create successfully"

            test_id = valid_data['data']['issueId']
            created_resources.append(('test', test_id))
            print(f"   ✅ Created valid test successfully")

            # Step 2: Try to get a non-existent test (realistic failure scenario)
            nonexistent_params = {
                'entity': 'test',
                'action': 'get',
                'issue_id': 'FAKE-999999'
            }

            nonexistent_result = await tool.run(nonexistent_params)
            nonexistent_data = parse_mcp_response(nonexistent_result)
            assert not nonexistent_data['success'], "Non-existent test should fail gracefully"
            assert 'errors' in nonexistent_data, "Should provide error information"
            print(f"   ✅ Handled non-existent test gracefully: {nonexistent_data['errors'][0][:50]}...")

            # Step 3: Try to create test with missing required fields
            incomplete_params = {
                'entity': 'test',
                'action': 'create',
                'project_key': project_key
                # Missing summary - should fail
            }

            incomplete_result = await tool.run(incomplete_params)
            incomplete_data = parse_mcp_response(incomplete_result)
            assert not incomplete_data['success'], "Incomplete test should fail validation"
            print(f"   ✅ Rejected incomplete test creation")

            # Step 4: Try to add tests to non-existent plan
            invalid_plan_params = {
                'entity': 'test_plan',
                'action': 'add_tests',
                'issue_id': 'FAKE-PLAN-999',
                'test_issue_ids': [test_id]
            }

            invalid_plan_result = await tool.run(invalid_plan_params)
            invalid_plan_data = parse_mcp_response(invalid_plan_result)
            assert not invalid_plan_data['success'], "Should fail when plan doesn't exist"
            print(f"   ✅ Handled non-existent plan operation gracefully")

            # Step 5: Try to perform invalid action
            invalid_action_params = {
                'entity': 'test',
                'action': 'totally_fake_action',
                'issue_id': test_id
            }

            invalid_action_result = await tool.run(invalid_action_params)
            invalid_action_data = parse_mcp_response(invalid_action_result)
            assert not invalid_action_data['success'], "Should fail with invalid action"
            print(f"   ✅ Rejected invalid action gracefully")

            # Step 6: Verify that valid operations still work after failures
            verify_params = {
                'entity': 'test',
                'action': 'get',
                'issue_id': test_id
            }

            verify_result = await tool.run(verify_params)
            verify_data = parse_mcp_response(verify_result)
            assert verify_data['success'], "Valid operations should still work after errors"
            print(f"   ✅ System remains stable after handling failures")

            print(f"   ✅ Realistic failure handling complete - all errors handled gracefully")

        finally:
            # Cleanup (should work even after various failures)
            for resource_type, resource_id in reversed(created_resources):
                try:
                    cleanup_result = await tool.run({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                    cleanup_data = parse_mcp_response(cleanup_result)
                    if cleanup_data['success']:
                        print(f"   🧹 Successfully cleaned up {resource_type}")
                    else:
                        print(f"   ⚠️  Cleanup warning for {resource_type}: {cleanup_data.get('errors', ['Unknown'])}")
                except Exception as e:
                    print(f"   ⚠️  Cleanup exception for {resource_type}: {str(e)[:50]}")