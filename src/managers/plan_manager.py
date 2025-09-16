"""Test plan management operations for Xray."""

from typing import Dict, Any, List
from .base_manager import XrayEntityManager
from ..utils.graphql_templates import (
    CREATE_TEST_PLAN, GET_TEST_PLAN, LIST_TEST_PLANS,
    DELETE_TEST_PLAN, ADD_TESTS_TO_PLAN, REMOVE_TESTS_FROM_PLAN,
    ADD_EXECUTIONS_TO_PLAN, REMOVE_EXECUTIONS_FROM_PLAN
)


class PlanManager(XrayEntityManager):
    """Manager for Xray test plan operations."""

    async def create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new test plan."""
        project_key = params.get('project_key')
        summary = params.get('summary')
        test_issue_ids = params.get('test_issue_ids', [])

        if not project_key:
            return self.create_error_result("Missing required parameter: project_key")
        if not summary:
            return self.create_error_result("Missing required parameter: summary")

        try:
            variables = {
                'projectKey': project_key,
                'summary': summary,
                'testIssueIds': test_issue_ids
            }

            result = await self.execute_query(CREATE_TEST_PLAN, variables)
            plan_data = result['createTestPlan']['testPlan']
            jira_data = plan_data['jira']

            response_data = {
                'issueId': plan_data['issueId'],
                'issueKey': jira_data['key'],
                'summary': jira_data['summary']
            }

            warnings = result['createTestPlan'].get('warnings', [])
            return self.create_success_result(response_data, warnings)

        except Exception as e:
            return self.create_error_result(f"Failed to create test plan: {str(e)}")

    async def get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get test plan by issue ID."""
        issue_id = params.get('issue_id')
        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")

        try:
            variables = {'issueId': issue_id}
            result = await self.execute_query(GET_TEST_PLAN, variables)

            if not result.get('getTestPlan'):
                return self.create_error_result(f"Test plan with issue ID {issue_id} not found")

            plan_data = result['getTestPlan']
            response_data = self.extract_jira_data(plan_data)

            # Add plan-specific data
            if plan_data.get('tests'):
                response_data['tests'] = plan_data['tests']

            return self.create_success_result(response_data)

        except Exception as e:
            return self.create_error_result(f"Failed to get test plan: {str(e)}")

    async def list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List test plans with optional filtering."""
        project_key = params.get('project_key')
        jql = params.get('jql')
        limit = min(params.get('limit', 50), 100)
        start = params.get('start', 0)

        try:
            # Build JQL query
            final_jql = self.build_jql(project_key, jql, 'Test Plan')

            variables = {
                'jql': final_jql,
                'limit': limit,
                'start': start
            }

            result = await self.execute_query(LIST_TEST_PLANS, variables)
            plans_data = result['getTestPlans']

            # Transform results
            plans = []
            for plan in plans_data['results']:
                plan_info = self.extract_jira_data(plan)
                plans.append(plan_info)

            response_data = {
                'plans': plans,
                'total': plans_data['total'],
                'start': plans_data['start'],
                'limit': plans_data['limit']
            }

            return self.create_success_result(response_data)

        except Exception as e:
            return self.create_error_result(f"Failed to list test plans: {str(e)}")

    async def delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete test plan by issue ID."""
        issue_id = params.get('issue_id')
        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")

        try:
            # First verify the test plan exists
            get_result = await self.get({'issue_id': issue_id})
            if not get_result['success']:
                return self.create_error_result(f"Cannot delete test plan: {get_result['errors'][0]}")

            variables = {'issueId': issue_id}
            await self.execute_query(DELETE_TEST_PLAN, variables)

            response_data = {
                'message': f'Test plan with issue ID {issue_id} has been deleted successfully'
            }
            return self.create_success_result(response_data)

        except Exception as e:
            return self.create_error_result(f"Failed to delete test plan: {str(e)}")

    async def add_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add tests to test plan."""
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

            result = await self.execute_query(ADD_TESTS_TO_PLAN, variables)
            response = result['addTestsToTestPlan']

            return self.create_success_result(response)

        except Exception as e:
            return self.create_error_result(f"Failed to add tests to test plan: {str(e)}")

    async def remove_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove tests from test plan."""
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

            await self.execute_query(REMOVE_TESTS_FROM_PLAN, variables)

            response_data = {
                'message': f'Tests {test_issue_ids} removed from test plan {issue_id}'
            }
            return self.create_success_result(response_data)

        except Exception as e:
            return self.create_error_result(f"Failed to remove tests from test plan: {str(e)}")

    async def add_executions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add test executions to test plan."""
        issue_id = params.get('issue_id')
        exec_issue_ids = params.get('test_exec_issue_ids', [])

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")
        if not exec_issue_ids:
            return self.create_error_result("Missing required parameter: test_exec_issue_ids")

        try:
            variables = {
                'issueId': issue_id,
                'testExecIssueIds': exec_issue_ids
            }

            result = await self.execute_query(ADD_EXECUTIONS_TO_PLAN, variables)
            response = result['addTestExecutionsToTestPlan']

            return self.create_success_result(response)

        except Exception as e:
            return self.create_error_result(f"Failed to add executions to test plan: {str(e)}")

    async def remove_executions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove test executions from test plan."""
        issue_id = params.get('issue_id')
        exec_issue_ids = params.get('test_exec_issue_ids', [])

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")
        if not exec_issue_ids:
            return self.create_error_result("Missing required parameter: test_exec_issue_ids")

        try:
            variables = {
                'issueId': issue_id,
                'testExecIssueIds': exec_issue_ids
            }

            await self.execute_query(REMOVE_EXECUTIONS_FROM_PLAN, variables)

            response_data = {
                'message': f'Test executions {exec_issue_ids} removed from test plan {issue_id}'
            }
            return self.create_success_result(response_data)

        except Exception as e:
            return self.create_error_result(f"Failed to remove executions from test plan: {str(e)}")