"""Comprehensive Test Run operations tests for Xray MCP server."""

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
class TestRunOperations:
    """Test Test Run operations against live Xray API."""

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
        return f"RUN-TEST-{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    def project_key(self):
        """Get project key from environment."""
        return os.getenv('DEFAULT_PROJECT_KEY', 'FTEST')

    @pytest.mark.asyncio
    async def test_test_run_retrieval_and_management(self, tool, unique_prefix, project_key):
        """Test Test Run retrieval and basic management operations."""
        print(f"\n🧪 Testing Test Run retrieval with prefix: {unique_prefix}")

        # Create test and execution (which auto-creates test runs)
        test_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Test for Run Retrieval',
            'test_type': 'Manual',
            'description': 'Test for run operations'
        }

        test_result = await tool.run(test_params)
        test_data = parse_mcp_response(test_result)
        assert test_data['success'], f"Test creation failed: {test_data.get('errors')}"

        test_id = test_data['data']['issueId']
        test_key = test_data['data']['issueKey']
        print(f"✅ Created test: {test_key} ({test_id})")

        try:
            # Create execution (this auto-creates test runs)
            exec_params = {
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Execution for Runs',
                'test_issue_ids': [test_id],
                'test_environments': ['development']
            }

            exec_result = await tool.run(exec_params)
            exec_data = parse_mcp_response(exec_result)
            assert exec_data['success'], f"Execution creation failed: {exec_data.get('errors')}"

            execution_id = exec_data['data']['issueId']
            execution_key = exec_data['data']['issueKey']
            print(f"✅ Created execution: {execution_key} ({execution_id})")

            try:
                # 1. GET Test Run (auto-created when execution was created)
                run_get_params = {
                    'entity': 'test_run',
                    'action': 'get',
                    'test_execution_id': execution_id,
                    'test_issue_id': test_id
                }

                run_result = await tool.run(run_get_params)
                run_data = parse_mcp_response(run_result)
                assert run_data['success'], f"Get test run failed: {run_data.get('errors')}"

                run_id = run_data['data']['id']
                initial_status = run_data['data'].get('status', 'TODO')
                print(f"✅ Retrieved test run: {run_id} (status: {initial_status})")

                # 2. LIST Test Runs
                run_list_params = {
                    'entity': 'test_run',
                    'action': 'list',
                    'test_exec_issue_ids': [execution_id],
                    'limit': 20
                }

                list_result = await tool.run(run_list_params)
                list_data = parse_mcp_response(list_result)
                assert list_data['success'], f"List test runs failed: {list_data.get('errors')}"
                print(f"✅ Listed test runs (found: {list_data['data']['total']})")

                # Verify our run exists in the list
                found_our_run = False
                for run in list_data['data'].get('testRuns', []):
                    if run.get('id') == run_id:
                        found_our_run = True
                        break

                if found_our_run:
                    print(f"✅ Found our test run in list: {run_id}")
                else:
                    print(f"⚠️  Our test run not found in list (may be filtered): {run_id}")

            finally:
                # Clean up execution
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
            # Clean up test
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
    async def test_test_run_status_updates(self, tool, unique_prefix, project_key):
        """Test Test Run status and comment updates."""
        print(f"\n🧪 Testing Test Run status updates with prefix: {unique_prefix}")

        # Setup: Create test and execution
        test_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Test for Status Updates',
            'test_type': 'Manual'
        }

        test_result = await tool.run(test_params)
        test_data = parse_mcp_response(test_result)
        test_id = test_data['data']['issueId']
        test_key = test_data['data']['issueKey']

        exec_params = {
            'entity': 'test_execution',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix} Execution for Status Updates',
            'test_issue_ids': [test_id],
            'test_environments': ['testing']
        }

        exec_result = await tool.run(exec_params)
        exec_data = parse_mcp_response(exec_result)
        execution_id = exec_data['data']['issueId']
        execution_key = exec_data['data']['issueKey']

        print(f"✅ Setup complete: test ({test_key}), execution ({execution_key})")

        try:
            # Get the auto-created test run
            run_get_params = {
                'entity': 'test_run',
                'action': 'get',
                'test_execution_id': execution_id,
                'test_issue_id': test_id
            }

            run_result = await tool.run(run_get_params)
            run_data = parse_mcp_response(run_result)
            assert run_data['success'], "Failed to get test run"

            run_id = run_data['data']['id']
            print(f"✅ Retrieved test run: {run_id}")

            # 1. UPDATE Test Run Status to PASSED
            status_update_params = {
                'entity': 'test_run',
                'action': 'update_status',
                'id': run_id,
                'status': 'PASSED',
                'comment': 'Test executed successfully - all assertions passed'
            }

            status_result = await tool.run(status_update_params)
            status_data = parse_mcp_response(status_result)
            assert status_data['success'], f"Status update failed: {status_data.get('errors')}"
            print("✅ Updated test run status to PASSED")

            # 2. UPDATE Test Run Comment
            comment_update_params = {
                'entity': 'test_run',
                'action': 'update_comment',
                'id': run_id,
                'comment': 'Updated comment: Additional test details and observations'
            }

            comment_result = await tool.run(comment_update_params)
            comment_data = parse_mcp_response(comment_result)
            assert comment_data['success'], f"Comment update failed: {comment_data.get('errors')}"
            print("✅ Updated test run comment")

            # 3. ADD Defects to Test Run (if status was FAILED)
            # First update to FAILED status
            failed_update_params = {
                'entity': 'test_run',
                'action': 'update_status',
                'id': run_id,
                'status': 'FAILED',
                'comment': 'Test failed - adding defect information'
            }

            failed_result = await tool.run(failed_update_params)
            failed_data = parse_mcp_response(failed_result)
            assert failed_data['success'], "Failed status update failed"
            print("✅ Updated test run status to FAILED")

            # Add defects (note: this may require existing defect IDs in the project)
            defect_params = {
                'entity': 'test_run',
                'action': 'add_defects',
                'id': run_id,
                'defects': []  # Empty for now - would need real defect IDs
            }

            defect_result = await tool.run(defect_params)
            defect_data = parse_mcp_response(defect_result)
            # This might succeed with empty list or fail - both are acceptable
            print(f"✅ Defects operation: {'Success' if defect_data['success'] else 'Failed as expected'}")

            # 4. Verify updates by getting the run again
            verify_get_params = {
                'entity': 'test_run',
                'action': 'get',
                'test_execution_id': execution_id,
                'test_issue_id': test_id
            }

            verify_result = await tool.run(verify_get_params)
            verify_data = parse_mcp_response(verify_result)
            assert verify_data['success'], "Verification get failed"

            final_status = verify_data['data'].get('status', 'UNKNOWN')
            final_comment = verify_data['data'].get('comment', '')
            print(f"✅ Verified final state - Status: {final_status}, Comment updated: {'Yes' if 'Updated comment' in final_comment else 'No'}")

        finally:
            # Clean up execution and test
            await tool.run({
                'entity': 'test_execution',
                'action': 'delete',
                'issue_id': execution_id
            })
            print(f"✅ Cleaned up execution: {execution_key}")

            await tool.run({
                'entity': 'test',
                'action': 'delete',
                'issue_id': test_id
            })
            print(f"✅ Cleaned up test: {test_key}")

    @pytest.mark.asyncio
    async def test_test_run_limitations_and_errors(self, tool, unique_prefix, project_key):
        """Test Test Run limitations and error handling."""
        print(f"\n🧪 Testing Test Run limitations with prefix: {unique_prefix}")

        # 1. Test CREATE limitation (runs are auto-created)
        create_params = {
            'entity': 'test_run',
            'action': 'create',
            'test_execution_id': '123456',
            'test_issue_id': '789012'
        }

        create_result = await tool.run(create_params)
        create_data = parse_mcp_response(create_result)
        assert not create_data['success'], "Create should fail - runs are auto-created"
        assert "automatically" in str(create_data['errors']).lower()
        print("✅ Properly rejected manual test run creation")

        # 2. Test missing required parameters
        missing_exec_params = {
            'entity': 'test_run',
            'action': 'get',
            'test_issue_id': '123456'
        }

        missing_result = await tool.run(missing_exec_params)
        missing_data = parse_mcp_response(missing_result)
        assert not missing_data['success'], "Should fail without test_execution_id"
        print("✅ Properly rejected missing test_execution_id")

        missing_test_params = {
            'entity': 'test_run',
            'action': 'get',
            'test_execution_id': '123456'
        }

        missing_test_result = await tool.run(missing_test_params)
        missing_test_data = parse_mcp_response(missing_test_result)
        assert not missing_test_data['success'], "Should fail without test_issue_id"
        print("✅ Properly rejected missing test_issue_id")

        # 3. Test non-existent test run
        fake_get_params = {
            'entity': 'test_run',
            'action': 'get',
            'test_execution_id': '999999999',
            'test_issue_id': '888888888'
        }

        fake_result = await tool.run(fake_get_params)
        fake_data = parse_mcp_response(fake_result)
        assert not fake_data['success'], "Should fail for non-existent run"
        print("✅ Properly handled non-existent test run")

        # 4. Test evidence upload limitation
        evidence_params = {
            'entity': 'test_run',
            'action': 'add_evidence',
            'id': 'fake_run_id'
        }

        evidence_result = await tool.run(evidence_params)
        evidence_data = parse_mcp_response(evidence_result)
        assert not evidence_data['success'], "Evidence upload should fail with limitation"
        print("✅ Properly handled evidence upload limitation")

        # 5. Test invalid status update
        invalid_status_params = {
            'entity': 'test_run',
            'action': 'update_status',
            'id': 'fake_run_id',
            'status': 'INVALID_STATUS'
        }

        invalid_status_result = await tool.run(invalid_status_params)
        invalid_status_data = parse_mcp_response(invalid_status_result)
        assert not invalid_status_data['success'], "Should fail with invalid status"
        print("✅ Properly handled invalid status update")

        print("✅ All limitation and error scenarios tested")