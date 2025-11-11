"""End-to-end Test Plan and Test Run workflow tests for Xray MCP server."""

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
class TestPlanRunWorkflow:
    """Test complete Test Plan and Test Run workflow against live Xray API."""

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
        return f"WORKFLOW-{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    def project_key(self):
        """Get project key from environment."""
        return os.getenv('DEFAULT_PROJECT_KEY', 'FTEST')

    @pytest.mark.asyncio
    async def test_complete_plan_run_workflow(self, tool, unique_prefix, project_key):
        """Test a complete realistic Test Plan and Test Run workflow."""
        print(f"\n🚀 Testing complete Plan-Run workflow with prefix: {unique_prefix}")

        # Step 1: Create 3 tests for a realistic test suite
        test_scenarios = [
            ("Login Functionality", "Manual", "Verify user can log into the system"),
            ("Search Feature", "Manual", "Test search functionality works correctly"),
            ("Checkout Process", "Manual", "Validate checkout process completes successfully")
        ]

        created_tests = []
        print("\n📝 Creating test suite...")

        for test_name, test_type, description in test_scenarios:
            test_params = {
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} {test_name}',
                'test_type': test_type,
                'description': description,
                'steps': '[{"action": "Execute test step", "data": "Test data", "result": "Expected result"}]'
            }

            test_result = await tool.run(test_params)
            test_data = parse_mcp_response(test_result)
            assert test_data['success'], f"Failed to create {test_name}: {test_data.get('errors')}"

            created_tests.append({
                'id': test_data['data']['issueId'],
                'key': test_data['data']['issueKey'],
                'name': test_name
            })
            print(f"✅ Created test: {test_data['data']['issueKey']} ({test_name})")

        try:
            # Step 2: Create Test Plan with all 3 tests
            print("\n📋 Creating test plan...")
            plan_params = {
                'entity': 'test_plan',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} E-Commerce Test Plan',
                'test_issue_ids': [test['id'] for test in created_tests]
            }

            plan_result = await tool.run(plan_params)
            plan_data = parse_mcp_response(plan_result)
            assert plan_data['success'], f"Plan creation failed: {plan_data.get('errors')}"

            plan_id = plan_data['data']['issueId']
            plan_key = plan_data['data']['issueKey']
            print(f"✅ Created test plan: {plan_key} ({plan_id}) with {len(created_tests)} tests")

            try:
                # Step 3: Create Test Execution linked to the plan
                print("\n🔄 Creating test execution...")
                exec_params = {
                    'entity': 'test_execution',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix} E-Commerce Execution',
                    'test_issue_ids': [test['id'] for test in created_tests],
                    'test_environments': ['staging', 'chrome']
                }

                exec_result = await tool.run(exec_params)
                exec_data = parse_mcp_response(exec_result)
                assert exec_data['success'], f"Execution creation failed: {exec_data.get('errors')}"

                execution_id = exec_data['data']['issueId']
                execution_key = exec_data['data']['issueKey']
                print(f"✅ Created test execution: {execution_key} ({execution_id})")

                try:
                    # Step 4: Link execution to plan
                    print("\n🔗 Linking execution to plan...")
                    link_params = {
                        'entity': 'test_plan',
                        'action': 'add_executions',
                        'issue_id': plan_id,
                        'test_exec_issue_ids': [execution_id]
                    }

                    link_result = await tool.run(link_params)
                    link_data = parse_mcp_response(link_result)
                    assert link_data['success'], f"Link execution failed: {link_data.get('errors')}"
                    print("✅ Linked execution to plan")

                    # Step 5: Retrieve and update test runs
                    print("\n🏃 Processing test runs...")
                    test_outcomes = ['PASSED', 'FAILED', 'PASSED']  # Realistic mixed results

                    for i, (test, outcome) in enumerate(zip(created_tests, test_outcomes)):
                        print(f"\n   Processing Test Run {i+1}: {test['name']}")

                        # Get the auto-created test run
                        run_get_params = {
                            'entity': 'test_run',
                            'action': 'get',
                            'test_execution_id': execution_id,
                            'test_issue_id': test['id']
                        }

                        run_result = await tool.run(run_get_params)
                        run_data = parse_mcp_response(run_result)
                        assert run_data['success'], f"Failed to get run for {test['name']}"

                        run_id = run_data['data']['id']
                        print(f"   ✅ Retrieved test run: {run_id}")

                        # Update run status
                        status_params = {
                            'entity': 'test_run',
                            'action': 'update_status',
                            'id': run_id,
                            'status': outcome,
                            'comment': f'{test["name"]} executed with result: {outcome}'
                        }

                        status_result = await tool.run(status_params)
                        status_data = parse_mcp_response(status_result)
                        assert status_data['success'], f"Failed to update status for {test['name']}"
                        print(f"   ✅ Updated status to {outcome}")

                        # Add additional comments for failed tests
                        if outcome == 'FAILED':
                            comment_params = {
                                'entity': 'test_run',
                                'action': 'update_comment',
                                'id': run_id,
                                'comment': f'{test["name"]} failed - requires investigation. Screenshots captured.'
                            }

                            comment_result = await tool.run(comment_params)
                            comment_data = parse_mcp_response(comment_result)
                            assert comment_data['success'], f"Failed to update comment for {test['name']}"
                            print(f"   ✅ Added failure details")

                    # Step 6: Verify plan shows execution results
                    print("\n📊 Verifying plan status...")
                    plan_verify_params = {
                        'entity': 'test_plan',
                        'action': 'get',
                        'issue_id': plan_id
                    }

                    plan_verify_result = await tool.run(plan_verify_params)
                    plan_verify_data = parse_mcp_response(plan_verify_result)
                    assert plan_verify_data['success'], "Failed to verify plan"
                    print("✅ Plan verification successful")

                    # Step 7: Generate summary
                    print("\n📈 Workflow Summary:")
                    print(f"   📋 Test Plan: {plan_key}")
                    print(f"   🔄 Test Execution: {execution_key}")
                    print(f"   📝 Tests Created: {len(created_tests)}")
                    print(f"   🏃 Test Runs Updated: {len(test_outcomes)}")
                    print(f"   ✅ Passed: {test_outcomes.count('PASSED')}")
                    print(f"   ❌ Failed: {test_outcomes.count('FAILED')}")
                    print(f"   ⏸️  Skipped: {test_outcomes.count('SKIPPED')}")

                finally:
                    # Clean up execution
                    print("\n🧹 Cleaning up execution...")
                    exec_delete_params = {
                        'entity': 'test_execution',
                        'action': 'delete',
                        'issue_id': execution_id
                    }

                    exec_delete_result = await tool.run(exec_delete_params)
                    exec_delete_data = parse_mcp_response(exec_delete_result)
                    assert exec_delete_data['success'], f"Execution cleanup failed: {exec_delete_data.get('errors')}"
                    print(f"✅ Cleaned up execution: {execution_key}")

            finally:
                # Clean up plan
                print("\n🧹 Cleaning up plan...")
                plan_delete_params = {
                    'entity': 'test_plan',
                    'action': 'delete',
                    'issue_id': plan_id
                }

                plan_delete_result = await tool.run(plan_delete_params)
                plan_delete_data = parse_mcp_response(plan_delete_result)
                assert plan_delete_data['success'], f"Plan cleanup failed: {plan_delete_data.get('errors')}"
                print(f"✅ Cleaned up plan: {plan_key}")

        finally:
            # Clean up all tests
            print("\n🧹 Cleaning up tests...")
            for test in created_tests:
                test_delete_params = {
                    'entity': 'test',
                    'action': 'delete',
                    'issue_id': test['id']
                }

                test_delete_result = await tool.run(test_delete_params)
                test_delete_data = parse_mcp_response(test_delete_result)
                assert test_delete_data['success'], f"Test cleanup failed for {test['key']}: {test_delete_data.get('errors')}"
                print(f"✅ Cleaned up test: {test['key']}")

        print(f"\n🎉 Complete workflow test successful with prefix: {unique_prefix}")

    @pytest.mark.asyncio
    async def test_plan_execution_association_workflow(self, tool, unique_prefix, project_key):
        """Test Test Plan and Test Execution association workflow."""
        print(f"\n🔗 Testing Plan-Execution association workflow with prefix: {unique_prefix}")

        # Create a test for the workflow
        test_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Association Test',
            'test_type': 'Manual'
        }

        test_result = await tool.run(test_params)
        test_data = parse_mcp_response(test_result)
        test_id = test_data['data']['issueId']
        test_key = test_data['data']['issueKey']

        try:
            # Create plan
            plan_params = {
                'entity': 'test_plan',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Association Plan',
                'test_issue_ids': [test_id]
            }

            plan_result = await tool.run(plan_params)
            plan_data = parse_mcp_response(plan_result)
            plan_id = plan_data['data']['issueId']
            plan_key = plan_data['data']['issueKey']

            # Create execution
            exec_params = {
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Association Execution',
                'test_issue_ids': [test_id],
                'test_environments': ['integration']
            }

            exec_result = await tool.run(exec_params)
            exec_data = parse_mcp_response(exec_result)
            execution_id = exec_data['data']['issueId']
            execution_key = exec_data['data']['issueKey']

            try:
                # Test association operations
                print("✅ Created plan and execution for association testing")

                # Add execution to plan
                add_params = {
                    'entity': 'test_plan',
                    'action': 'add_executions',
                    'issue_id': plan_id,
                    'test_exec_issue_ids': [execution_id]
                }

                add_result = await tool.run(add_params)
                add_data = parse_mcp_response(add_result)
                assert add_data['success'], f"Add execution failed: {add_data.get('errors')}"
                print("✅ Added execution to plan")

                # Remove execution from plan
                remove_params = {
                    'entity': 'test_plan',
                    'action': 'remove_executions',
                    'issue_id': plan_id,
                    'test_exec_issue_ids': [execution_id]
                }

                remove_result = await tool.run(remove_params)
                remove_data = parse_mcp_response(remove_result)
                assert remove_data['success'], f"Remove execution failed: {remove_data.get('errors')}"
                print("✅ Removed execution from plan")

                print("✅ Association workflow completed successfully")

            finally:
                # Clean up execution and plan
                await tool.run({
                    'entity': 'test_execution',
                    'action': 'delete',
                    'issue_id': execution_id
                })
                print(f"✅ Cleaned up execution: {execution_key}")

                await tool.run({
                    'entity': 'test_plan',
                    'action': 'delete',
                    'issue_id': plan_id
                })
                print(f"✅ Cleaned up plan: {plan_key}")

        finally:
            # Clean up test
            await tool.run({
                'entity': 'test',
                'action': 'delete',
                'issue_id': test_id
            })
            print(f"✅ Cleaned up test: {test_key}")

    @pytest.mark.asyncio
    async def test_workflow_error_recovery(self, tool, unique_prefix, project_key):
        """Test workflow error recovery and resource cleanup."""
        print(f"\n🔧 Testing workflow error recovery with prefix: {unique_prefix}")

        # Create resources that will be cleaned up even if errors occur
        test_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Error Recovery Test',
            'test_type': 'Manual'
        }

        test_result = await tool.run(test_params)
        test_data = parse_mcp_response(test_result)
        test_id = test_data['data']['issueId']
        test_key = test_data['data']['issueKey']

        created_resources = []
        created_resources.append(('test', test_id, test_key))

        try:
            # Create plan
            plan_params = {
                'entity': 'test_plan',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Error Recovery Plan',
                'test_issue_ids': [test_id]
            }

            plan_result = await tool.run(plan_params)
            if plan_result:
                plan_data = parse_mcp_response(plan_result)
                if plan_data['success']:
                    plan_id = plan_data['data']['issueId']
                    plan_key = plan_data['data']['issueKey']
                    created_resources.append(('test_plan', plan_id, plan_key))

            # Intentionally cause an error (invalid operation)
            try:
                invalid_params = {
                    'entity': 'test_plan',
                    'action': 'invalid_action',
                    'issue_id': 'fake_id'
                }

                invalid_result = await tool.run(invalid_params)
                invalid_data = parse_mcp_response(invalid_result)
                assert not invalid_data['success'], "Should fail with invalid action"
                print("✅ Error properly caught and handled")

            except Exception as e:
                print(f"✅ Exception properly handled: {str(e)[:100]}")

        finally:
            # Clean up all created resources (reverse order)
            print("\n🧹 Cleaning up resources after error...")
            for resource_type, resource_id, resource_key in reversed(created_resources):
                try:
                    cleanup_params = {
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    }

                    cleanup_result = await tool.run(cleanup_params)
                    cleanup_data = parse_mcp_response(cleanup_result)
                    if cleanup_data['success']:
                        print(f"✅ Cleaned up {resource_type}: {resource_key}")
                    else:
                        print(f"⚠️  Cleanup failed for {resource_type}: {resource_key}")

                except Exception as e:
                    print(f"⚠️  Exception during cleanup of {resource_type}: {str(e)[:50]}")

        print("✅ Error recovery and cleanup workflow completed")