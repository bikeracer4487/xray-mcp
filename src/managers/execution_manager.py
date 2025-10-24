"""Test execution management operations for Xray."""

from typing import Dict, Any, List
from .base_manager import XrayEntityManager
from ..utils.graphql_templates import (
    CREATE_TEST_EXECUTION, GET_TEST_EXECUTION, LIST_TEST_EXECUTIONS,
    DELETE_TEST_EXECUTION, ADD_TESTS_TO_EXECUTION, REMOVE_TESTS_FROM_EXECUTION,
    ADD_TEST_ENVIRONMENTS_TO_EXECUTION, REMOVE_TEST_ENVIRONMENTS_FROM_EXECUTION
)


class ExecutionManager(XrayEntityManager):
    """Manager for Xray test execution operations."""

    def __init__(self, client):
        """Initialize ExecutionManager with indexing delay mitigation."""
        super().__init__(client)
        from ..utils.retry_strategy import IndexingDelayMitigator
        self.retry_mitigator = IndexingDelayMitigator()

    async def create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new test execution with array validation for test IDs."""
        project_key = params.get('project_key')
        summary = params.get('summary')
        test_issue_ids = params.get('test_issue_ids', [])
        test_environments = params.get('test_environments', [])

        if not project_key:
            return self.create_error_result("Missing required parameter: project_key")
        if not summary:
            return self.create_error_result("Missing required parameter: summary")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate test_issue_ids array if provided (allow empty arrays for creation)
        if test_issue_ids:
            validation_result = IDFormatValidator.validate_id_array_for_xray_graphql_allow_empty(test_issue_ids, "test")
            if not validation_result.is_valid:
                # Provide helpful error message for array validation issues
                error_msg = f"Invalid test_issue_ids: {validation_result.error_message}"
                if validation_result.helpful_message:
                    error_msg += f". {validation_result.helpful_message}"
                return self.create_error_result(error_msg)

        try:
            variables = {
                'projectKey': project_key,
                'summary': summary,
                'testIssueIds': test_issue_ids,
                'testEnvironments': test_environments
            }

            result = await self.execute_query(CREATE_TEST_EXECUTION, variables)
            execution_data = result['createTestExecution']['testExecution']
            jira_data = execution_data['jira']

            response_data = {
                'issueId': execution_data['issueId'],
                'issueKey': jira_data['key'],
                'summary': jira_data['summary']
            }

            # Include test environments if present
            if execution_data.get('testEnvironments'):
                response_data['testEnvironments'] = execution_data['testEnvironments']

            warnings = result['createTestExecution'].get('warnings', [])
            if result['createTestExecution'].get('createdTestEnvironments'):
                response_data['createdTestEnvironments'] = result['createTestExecution']['createdTestEnvironments']

            # Add indexing delay advisory for immediate follow-up operations
            warnings.append(
                f"INDEXING DELAY ADVISORY: Test execution '{response_data['issueKey']}' created successfully. "
                f"If you plan to immediately search for, retrieve, or add tests to this execution, "
                f"please wait 2-5 seconds for Xray indexing to complete."
            )

            return self.create_success_result(response_data, warnings)

        except Exception as e:
            return self.create_error_result(f"Failed to create test execution: {str(e)}")

    async def get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get test execution by issue ID with advanced indexing delay mitigation and ID format validation."""
        issue_id = params.get('issue_id')
        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate ID format before making API calls
        validation_result = IDFormatValidator.validate_for_xray_graphql(issue_id, "test_execution")
        if not validation_result.is_valid:
            # Provide helpful error message for ID format issues
            error_msg = validation_result.error_message
            if validation_result.helpful_message:
                error_msg += f". {validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        async def get_operation():
            variables = {'issueId': issue_id}
            result = await self.execute_query(GET_TEST_EXECUTION, variables)

            if result.get('getTestExecution'):
                # Success case
                execution_data = result['getTestExecution']
                response_data = self.extract_jira_data(execution_data)

                # Add execution-specific data
                if execution_data.get('testEnvironments'):
                    response_data['testEnvironments'] = execution_data['testEnvironments']
                if execution_data.get('tests'):
                    response_data['tests'] = execution_data['tests']

                return response_data
            else:
                raise Exception(f"Test execution with issue ID {issue_id} not found")

        # Use advanced retry strategy with indexing delay mitigation
        retry_result = await self.retry_mitigator.execute_with_retry(
            get_operation,
            f"get_execution_{issue_id}",
            expected_indexing_delay=True
        )

        if retry_result.success:
            return self.create_success_result(retry_result.result)
        else:
            # Enhanced error message for failed operations
            error_msg = f"Failed to get test execution after {retry_result.attempts} attempts"
            if retry_result.last_error:
                error_msg += f": {str(retry_result.last_error)}"
            
            # If the error is "not found" and user provided what looks like a numeric ID,
            # this might be a real indexing delay or the execution doesn't exist
            if "not found" in error_msg.lower():
                error_msg += f". Note: Using numeric ID '{issue_id}' (correct format). If execution was just created, try again in a few seconds due to indexing delays."
            
            return self.create_error_result(error_msg)

    async def list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List test executions with optional filtering."""
        project_key = params.get('project_key')
        jql = params.get('jql')
        limit = min(params.get('limit', 50), 100)
        start = params.get('start', 0)

        try:
            # Build JQL query
            final_jql = self.build_jql(project_key, jql, 'Test Execution')

            variables = {
                'jql': final_jql,
                'limit': limit,
                'start': start
            }

            result = await self.execute_query(LIST_TEST_EXECUTIONS, variables)
            executions_data = result['getTestExecutions']

            # Transform results
            executions = []
            for execution in executions_data['results']:
                execution_info = self.extract_jira_data(execution)
                if execution.get('testEnvironments'):
                    execution_info['testEnvironments'] = execution['testEnvironments']
                executions.append(execution_info)

            response_data = {
                'executions': executions,
                'total': executions_data['total'],
                'start': executions_data['start'],
                'limit': executions_data['limit']
            }

            return self.create_success_result(response_data)

        except Exception as e:
            return self.create_error_result(f"Failed to list test executions: {str(e)}")

    async def delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete test execution by issue ID with ID format validation."""
        issue_id = params.get('issue_id')
        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate ID format before making API calls
        validation_result = IDFormatValidator.validate_for_xray_graphql(issue_id, "test_execution")
        if not validation_result.is_valid:
            # Provide helpful error message for ID format issues
            error_msg = validation_result.error_message
            if validation_result.helpful_message:
                error_msg += f". {validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        try:
            # First verify the test execution exists (this will also benefit from ID validation in get method)
            get_result = await self.get({'issue_id': issue_id})
            if not get_result['success']:
                return self.create_error_result(f"Cannot delete test execution: {get_result['errors'][0]}")

            variables = {'issueId': issue_id}
            await self.execute_query(DELETE_TEST_EXECUTION, variables)

            response_data = {
                'message': f'Test execution with issue ID {issue_id} has been deleted successfully'
            }
            return self.create_success_result(response_data)

        except Exception as e:
            error_msg = f"Failed to delete test execution: {str(e)}"
            
            # Enhance error message if it's a "not found" error
            if "not found" in error_msg.lower():
                error_msg += f". Note: Using numeric ID '{issue_id}' (correct format). Verify the test execution exists and try again if recently created (indexing delays)."
            
            return self.create_error_result(error_msg)

    async def add_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add tests to test execution with ID format validation."""
        issue_id = params.get('issue_id')
        test_issue_ids = params.get('test_issue_ids')

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")
        
        # Check if test_issue_ids parameter was provided
        if test_issue_ids is None:
            return self.create_error_result("Missing required parameter: test_issue_ids")
        
        # Check if array is empty
        if len(test_issue_ids) == 0:
            return self.create_error_result("At least one test ID must be provided in test_issue_ids array")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate execution ID format
        validation_result = IDFormatValidator.validate_for_xray_graphql(issue_id, "test_execution")
        if not validation_result.is_valid:
            error_msg = f"Invalid execution issue_id: {validation_result.error_message}"
            if validation_result.helpful_message:
                error_msg += f". {validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        # Validate test_issue_ids array
        array_validation_result = IDFormatValidator.validate_id_array_for_xray_graphql(test_issue_ids, "test")
        if not array_validation_result.is_valid:
            error_msg = f"Invalid test_issue_ids: {array_validation_result.error_message}"
            if array_validation_result.helpful_message:
                error_msg += f". {array_validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        try:
            variables = {
                'issueId': issue_id,
                'testIssueIds': test_issue_ids
            }

            result = await self.execute_query(ADD_TESTS_TO_EXECUTION, variables)
            response = result['addTestsToTestExecution']

            return self.create_success_result(response)

        except Exception as e:
            return self.create_error_result(f"Failed to add tests to test execution: {str(e)}")

    async def remove_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove tests from test execution with ID format validation."""
        issue_id = params.get('issue_id')
        test_issue_ids = params.get('test_issue_ids')

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")
        
        # Check if test_issue_ids parameter was provided
        if test_issue_ids is None:
            return self.create_error_result("Missing required parameter: test_issue_ids")
        
        # Check if array is empty
        if len(test_issue_ids) == 0:
            return self.create_error_result("At least one test ID must be provided in test_issue_ids array")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate execution ID format
        validation_result = IDFormatValidator.validate_for_xray_graphql(issue_id, "test_execution")
        if not validation_result.is_valid:
            error_msg = f"Invalid execution issue_id: {validation_result.error_message}"
            if validation_result.helpful_message:
                error_msg += f". {validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        # Validate test_issue_ids array
        array_validation_result = IDFormatValidator.validate_id_array_for_xray_graphql(test_issue_ids, "test")
        if not array_validation_result.is_valid:
            error_msg = f"Invalid test_issue_ids: {array_validation_result.error_message}"
            if array_validation_result.helpful_message:
                error_msg += f". {array_validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        try:
            variables = {
                'issueId': issue_id,
                'testIssueIds': test_issue_ids
            }

            await self.execute_query(REMOVE_TESTS_FROM_EXECUTION, variables)

            response_data = {
                'message': f'Tests {test_issue_ids} removed from test execution {issue_id}'
            }
            return self.create_success_result(response_data)

        except Exception as e:
            return self.create_error_result(f"Failed to remove tests from test execution: {str(e)}")

    async def add_environments(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add test environments to test execution."""
        issue_id = params.get('issue_id')
        environments = params.get('environments', [])

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")
        if not environments:
            return self.create_error_result("Missing required parameter: environments")

        try:
            variables = {
                'issueId': issue_id,
                'testEnvironments': environments
            }

            result = await self.execute_query(ADD_TEST_ENVIRONMENTS_TO_EXECUTION, variables)
            response = result['addTestEnvironmentsToTestExecution']

            return self.create_success_result(response)

        except Exception as e:
            return self.create_error_result(f"Failed to add test environments to test execution: {str(e)}")

    async def remove_environments(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove test environments from test execution."""
        issue_id = params.get('issue_id')
        environments = params.get('environments', [])

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")
        if not environments:
            return self.create_error_result("Missing required parameter: environments")

        try:
            variables = {
                'issueId': issue_id,
                'testEnvironments': environments
            }

            await self.execute_query(REMOVE_TEST_ENVIRONMENTS_FROM_EXECUTION, variables)

            response_data = {
                'message': f'Test environments {environments} removed from test execution {issue_id}'
            }
            return self.create_success_result(response_data)

        except Exception as e:
            return self.create_error_result(f"Failed to remove test environments from test execution: {str(e)}")

    async def update_metadata(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update test execution metadata (summary and description) with enhanced workaround guidance.

        Note: Xray's GraphQL API does not support direct metadata updates for executions.
        This provides comprehensive workaround guidance specific to test executions.
        """
        issue_id = params.get('issue_id')
        summary = params.get('summary')
        description = params.get('description')

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")

        if not summary and not description:
            return self.create_error_result("At least one of summary or description must be provided")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate ID format to provide helpful guidance
        validation_result = IDFormatValidator.validate_for_xray_graphql(issue_id, "test_execution")
        if not validation_result.is_valid:
            error_msg = f"Invalid execution ID: {validation_result.error_message}"
            if validation_result.helpful_message:
                error_msg += f". {validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        # Get current execution details to provide context for workarounds
        try:
            current_execution = await self.get({'issue_id': issue_id})
            if not current_execution['success']:
                return self.create_error_result(f"Cannot update metadata: {current_execution['errors'][0]}")

            exec_data = current_execution['data']
            exec_key = exec_data.get('issueKey', 'Unknown')
            project_key = exec_key.split('-')[0] if '-' in exec_key else 'PROJECT'

            # Create detailed workaround guidance for test execution metadata
            workaround_guidance = [
                f"1. JIRA UI: Navigate to {exec_key} in Jira and edit Summary/Description directly",
                f"2. RECREATION: Create a new test execution with desired metadata:",
                f"   entity='test_execution', action='create', project_key='{project_key}', summary='{summary or exec_data.get('summary', 'New Summary')}', description='{description or exec_data.get('description', 'New Description')}'",
                f"3. JIRA REST API: Use Jira's REST API PUT /rest/api/2/issue/{exec_key} with appropriate authentication",
                f"4. BULK EDIT: If updating multiple executions, use Jira's bulk edit feature in the UI"
            ]

            error_lines = [
                "LIMITATION: Metadata-only updates are not supported by Xray's GraphQL API",
                f"EXECUTION CONTEXT: {exec_key} (ID: {issue_id})",
                "WORKAROUND OPTIONS:"
            ]
            error_lines.extend(workaround_guidance)
            return self.create_error_result("; ".join(error_lines))

        except Exception as e:
            # Fallback to basic error message if we can't get execution details
            error_message = "; ".join([
                "Metadata-only updates are not supported by Xray's GraphQL API for test executions",
                "This is a known limitation of the Xray Cloud platform",
                "Workarounds: (1) Update metadata directly in Jira UI",
                "(2) Use Jira's REST API separately (requires additional authentication setup)",
                "(3) Create a new execution with desired metadata"
            ])
            return self.create_error_result(error_message)
