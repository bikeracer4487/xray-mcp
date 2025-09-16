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

    async def create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new test execution."""
        project_key = params.get('project_key')
        summary = params.get('summary')
        test_issue_ids = params.get('test_issue_ids', [])
        test_environments = params.get('test_environments', [])

        if not project_key:
            return self.create_error_result("Missing required parameter: project_key")
        if not summary:
            return self.create_error_result("Missing required parameter: summary")

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

            return self.create_success_result(response_data, warnings)

        except Exception as e:
            return self.create_error_result(f"Failed to create test execution: {str(e)}")

    async def get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get test execution by issue ID with retry logic for indexing delays."""
        import asyncio

        issue_id = params.get('issue_id')
        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")

        # Retry logic for indexing delays
        max_retries = 3
        base_delay = 2  # seconds

        for attempt in range(max_retries + 1):
            try:
                variables = {'issueId': issue_id}
                result = await self.execute_query(GET_TEST_EXECUTION, variables)

                if not result.get('getTestExecution'):
                    # If this is the last attempt, return the error
                    if attempt == max_retries:
                        return self.create_error_result(f"Test execution with issue ID {issue_id} not found")

                    # Otherwise, wait and retry (likely indexing delay)
                    delay = base_delay * (2 ** attempt)  # Exponential backoff: 2, 4, 8 seconds
                    await asyncio.sleep(delay)
                    continue

                execution_data = result['getTestExecution']
                response_data = self.extract_jira_data(execution_data)

                # Add execution-specific data
                if execution_data.get('testEnvironments'):
                    response_data['testEnvironments'] = execution_data['testEnvironments']
                if execution_data.get('tests'):
                    response_data['tests'] = execution_data['tests']

                return self.create_success_result(response_data)

            except Exception as e:
                # Check if it's an indexing-related error
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ['index', 're-index', 'not found']) and attempt < max_retries:
                    # Wait and retry for indexing issues
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue

                # For other errors or final attempt, return error
                return self.create_error_result(f"Failed to get test execution: {str(e)}")

        # Should not reach here, but fallback
        return self.create_error_result(f"Failed to get test execution after {max_retries} retries")

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
        """Delete test execution by issue ID."""
        issue_id = params.get('issue_id')
        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")

        try:
            # First verify the test execution exists
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
            return self.create_error_result(f"Failed to delete test execution: {str(e)}")

    async def add_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add tests to test execution."""
        issue_id = params.get('issue_id')
        test_issue_ids = params.get('test_issue_ids', [])

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")
        if not test_issue_ids:
            return self.create_error_result("Missing required parameter: test_issue_ids")

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
        """Remove tests from test execution."""
        issue_id = params.get('issue_id')
        test_issue_ids = params.get('test_issue_ids', [])

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")
        if not test_issue_ids:
            return self.create_error_result("Missing required parameter: test_issue_ids")

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