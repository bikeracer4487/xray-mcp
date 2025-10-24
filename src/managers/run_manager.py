"""Test run management operations for Xray."""

from typing import Dict, Any, List
from .base_manager import XrayEntityManager
from ..utils.graphql_templates import (
    GET_TEST_RUN, LIST_TEST_RUNS, UPDATE_TEST_RUN_STATUS,
    UPDATE_TEST_RUN_COMMENT, ADD_DEFECTS_TO_TEST_RUN
)
from ..utils.retry_strategy import IndexingDelayMitigator


class RunManager(XrayEntityManager):
    """Manager for Xray test run operations."""

    def __init__(self, client):
        """Initialize RunManager with indexing delay mitigation."""
        super().__init__(client)
        self.retry_mitigator = IndexingDelayMitigator()

    async def create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test runs are created automatically when tests are added to executions."""
        return self.create_error_result("Test runs are created automatically when tests are added to executions")

    async def get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get test run by execution and test ID with advanced indexing delay mitigation and ID format validation."""
        test_execution_id = params.get('test_execution_id')
        test_issue_id = params.get('test_issue_id')

        if not test_execution_id:
            return self.create_error_result("Missing required parameter: test_execution_id")
        if not test_issue_id:
            return self.create_error_result("Missing required parameter: test_issue_id")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate both ID formats before making API calls
        execution_validation = IDFormatValidator.validate_for_xray_graphql(test_execution_id, "test_execution")
        if not execution_validation.is_valid:
            error_msg = f"Invalid test_execution_id: {execution_validation.error_message}"
            if execution_validation.helpful_message:
                error_msg += f". {execution_validation.helpful_message}"
            return self.create_error_result(error_msg)

        test_validation = IDFormatValidator.validate_for_xray_graphql(test_issue_id, "test")
        if not test_validation.is_valid:
            error_msg = f"Invalid test_issue_id: {test_validation.error_message}"
            if test_validation.helpful_message:
                error_msg += f". {test_validation.helpful_message}"
            return self.create_error_result(error_msg)

        async def get_operation():
            variables = {
                'testExecIssueId': test_execution_id,
                'testIssueId': test_issue_id
            }

            result = await self.execute_query(GET_TEST_RUN, variables)

            if result.get('getTestRun'):
                # Success case
                run_data = result['getTestRun']
                response_data = {
                    'id': run_data['id'],
                    'status': run_data['status'],
                    'comment': run_data.get('comment'),
                    'startedOn': run_data.get('startedOn'),
                    'finishedOn': run_data.get('finishedOn'),
                    'executedById': run_data.get('executedById'),
                    'assigneeId': run_data.get('assigneeId'),
                    'evidence': run_data.get('evidence', []),
                    'defects': run_data.get('defects', []),
                    'testId': run_data['test']['issueId'],
                    'testExecutionId': run_data['testExecution']['issueId']
                }
                return response_data
            else:
                raise Exception(f"Test run not found for execution {test_execution_id} and test {test_issue_id}")

        # Use advanced retry strategy with indexing delay mitigation
        retry_result = await self.retry_mitigator.execute_with_retry(
            get_operation,
            f"get_run_{test_execution_id}_{test_issue_id}",
            expected_indexing_delay=True
        )

        if retry_result.success:
            return self.create_success_result(retry_result.result)
        else:
            # Enhanced error message for failed operations
            error_msg = f"Failed to get test run after {retry_result.attempts} attempts"
            if retry_result.last_error:
                error_msg += f": {str(retry_result.last_error)}"
            
            # If the error is "not found" and user provided what looks like a numeric ID,
            # this might be a real indexing delay or the run doesn't exist
            if "not found" in error_msg.lower():
                error_msg += f". Note: Using numeric IDs '{test_execution_id}' and '{test_issue_id}' (correct format). If test run was just created, try again in a few seconds due to indexing delays."
            
            return self.create_error_result(error_msg)

    async def list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List test runs with optional filtering by test or execution IDs."""
        test_issue_ids = params.get('test_issue_ids', [])
        test_exec_issue_ids = params.get('test_exec_issue_ids', [])
        limit = min(params.get('limit', 50), 100)

        # Need at least one filter
        if not test_issue_ids and not test_exec_issue_ids:
            return self.create_error_result("Either test_issue_ids or test_exec_issue_ids are required for listing test runs")

        try:
            variables = {
                'testIssueIds': test_issue_ids if test_issue_ids else None,
                'testExecIssueIds': test_exec_issue_ids if test_exec_issue_ids else None,
                'limit': limit
            }

            result = await self.execute_query(LIST_TEST_RUNS, variables)
            runs_data = result['getTestRuns']

            # Transform results
            runs = []
            for run in runs_data['results']:
                run_info = {
                    'id': run['id'],
                    'status': run['status'],
                    'comment': run.get('comment'),
                    'startedOn': run.get('startedOn'),
                    'finishedOn': run.get('finishedOn'),
                    'testId': run['test']['issueId'],
                    'testExecutionId': run['testExecution']['issueId']
                }
                runs.append(run_info)

            response_data = {
                'runs': runs,
                'total': runs_data['total'],
                'start': runs_data['start'],
                'limit': runs_data['limit']
            }

            return self.create_success_result(response_data)

        except Exception as e:
            return self.create_error_result(f"Failed to list test runs: {str(e)}")

    async def delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test runs cannot be directly deleted."""
        return self.create_error_result("Test runs cannot be directly deleted. Remove tests from executions instead.")

    async def update_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update test run status."""
        # Support both ID-based and execution/test-based lookup
        run_id = params.get('id')
        test_execution_id = params.get('test_execution_id')
        test_issue_id = params.get('test_issue_id')
        status = params.get('status')
        comment = params.get('comment')

        if not status:
            return self.create_error_result("Missing required parameter: status")

        # Validate status value
        valid_statuses = {'PASSED', 'FAILED', 'TODO', 'EXECUTING', 'BLOCKED'}
        if status not in valid_statuses:
            return self.create_error_result(
                f"Invalid status '{status}'. Valid statuses are: {', '.join(sorted(valid_statuses))}"
            )

        # If run_id not provided, get it from execution/test lookup
        if not run_id:
            if not test_execution_id or not test_issue_id:
                return self.create_error_result(
                    "Either 'id' or both 'test_execution_id' and 'test_issue_id' are required"
                )

            # Get the test run to find its ID
            get_result = await self.get({
                'test_execution_id': test_execution_id,
                'test_issue_id': test_issue_id
            })
            if not get_result['success']:
                return get_result
            run_id = get_result['data']['id']

        try:
            # Update status first
            variables = {
                'id': run_id,
                'status': status
            }

            result = await self.execute_query(UPDATE_TEST_RUN_STATUS, variables)
            # updateTestRunStatus returns a String, not an object

            response_data = {
                'id': run_id,
                'status': status,
                'message': f'Test run status updated to {status}'
            }

            # If comment provided, update it separately
            if comment:
                comment_result = await self.update_comment({
                    'id': run_id,
                    'comment': comment
                })
                if comment_result['success']:
                    response_data['comment'] = comment
                else:
                    # Status update succeeded but comment failed
                    response_data['comment_warning'] = f"Comment update failed: {comment_result.get('errors', ['Unknown error'])}"

            return self.create_success_result(response_data)

        except Exception as e:
            return self.create_error_result(f"Failed to update test run status: {str(e)}")

    async def update_comment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update test run comment."""
        run_id = params.get('id')
        test_execution_id = params.get('test_execution_id')
        test_issue_id = params.get('test_issue_id')
        comment = params.get('comment')

        if not comment:
            return self.create_error_result("Missing required parameter: comment")

        # If run_id not provided, get it from execution/test lookup
        if not run_id:
            if not test_execution_id or not test_issue_id:
                return self.create_error_result(
                    "Either 'id' or both 'test_execution_id' and 'test_issue_id' are required"
                )

            # Get the test run to find its ID
            get_result = await self.get({
                'test_execution_id': test_execution_id,
                'test_issue_id': test_issue_id
            })
            if not get_result['success']:
                return get_result
            run_id = get_result['data']['id']

        try:
            variables = {
                'id': run_id,
                'comment': comment
            }

            result = await self.execute_query(UPDATE_TEST_RUN_COMMENT, variables)
            # updateTestRunComment returns a String, not an object

            response_data = {
                'id': run_id,
                'comment': comment,
                'message': 'Test run comment updated successfully'
            }

            return self.create_success_result(response_data)

        except Exception as e:
            return self.create_error_result(f"Failed to update test run comment: {str(e)}")

    async def add_defects(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add defects to test run."""
        run_id = params.get('id')
        test_execution_id = params.get('test_execution_id')
        test_issue_id = params.get('test_issue_id')
        defects = params.get('defects', [])

        if not defects:
            return self.create_error_result("Missing required parameter: defects")

        # If run_id not provided, get it from execution/test lookup
        if not run_id:
            if not test_execution_id or not test_issue_id:
                return self.create_error_result(
                    "Either 'id' or both 'test_execution_id' and 'test_issue_id' are required"
                )

            # Get the test run to find its ID
            get_result = await self.get({
                'test_execution_id': test_execution_id,
                'test_issue_id': test_issue_id
            })
            if not get_result['success']:
                return get_result
            run_id = get_result['data']['id']

        try:
            variables = {
                'id': run_id,
                'issues': defects
            }

            result = await self.execute_query(ADD_DEFECTS_TO_TEST_RUN, variables)
            response = result['addDefectsToTestRun']

            response_data = {
                'id': run_id,
                'addedDefects': response.get('addedDefects', []),
                'message': f'Defects added to test run {run_id}'
            }

            warnings = response.get('warnings', [])
            return self.create_success_result(response_data, warnings)

        except Exception as e:
            return self.create_error_result(f"Failed to add defects to test run: {str(e)}")

    async def add_evidence(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add evidence to test run (requires file upload functionality)."""
        # Evidence upload requires complex multipart file handling
        # This is a documented limitation that would need file upload infrastructure
        return self.create_error_result(
            "Evidence upload requires multipart file handling infrastructure. "
            "This is a documented limitation that needs file upload endpoints."
        )