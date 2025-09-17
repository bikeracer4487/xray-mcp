"""Test management operations for Xray."""

from typing import Dict, Any, List, Optional
from .base_manager import XrayEntityManager
from ..utils.graphql_templates import (
    CREATE_MANUAL_TEST, CREATE_GENERIC_TEST, CREATE_CUCUMBER_TEST,
    GET_TEST, LIST_TESTS, DELETE_TEST, UPDATE_TEST_TYPE,
    UPDATE_UNSTRUCTURED_TEST_DEFINITION, UPDATE_GHERKIN_TEST_DEFINITION
)


class TestManager(XrayEntityManager):
    """Manager for Xray test operations."""

    async def create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new test."""
        project_key = params.get('project_key')
        summary = params.get('summary')
        test_type = params.get('test_type', 'Manual')
        description = params.get('description', '')
        steps = params.get('steps', [])
        gherkin = params.get('gherkin')

        if not project_key:
            return self.create_error_result("Missing required parameter: project_key")
        if not summary:
            return self.create_error_result("Missing required parameter: summary")

        # Parse steps parameter if it's a JSON string
        if isinstance(steps, str):
            try:
                import json
                steps = json.loads(steps)
            except json.JSONDecodeError as e:
                return self.create_error_result(f"Invalid JSON format for steps parameter: {str(e)}")
        
        # Validate steps format if provided
        if steps and not isinstance(steps, list):
            return self.create_error_result("Steps parameter must be a list of step objects or a JSON string")
        
        # Validate each step has required structure for CreateStepInput
        if steps:
            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    return self.create_error_result(f"Step {i+1} must be an object with 'action', 'data', and 'result' fields")
                # Note: action, data, result are optional in CreateStepInput but commonly used

        try:
            # Choose template based on test type
            if test_type == 'Manual':
                query = CREATE_MANUAL_TEST
                variables = {
                    'projectKey': project_key,
                    'summary': summary,
                    'description': description,
                    'steps': steps
                }
            elif test_type == 'Cucumber':
                if not gherkin:
                    return self.create_error_result("Missing required parameter: gherkin for Cucumber tests")
                query = CREATE_CUCUMBER_TEST
                variables = {
                    'projectKey': project_key,
                    'summary': summary,
                    'description': description,
                    'gherkin': gherkin
                }
            else:  # Generic
                query = CREATE_GENERIC_TEST
                variables = {
                    'projectKey': project_key,
                    'summary': summary,
                    'description': description
                }

            result = await self.execute_query(query, variables)
            test_data = result['createTest']['test']
            jira_data = test_data['jira']

            response_data = {
                'issueId': test_data['issueId'],
                'issueKey': jira_data['key'],
                'summary': jira_data['summary'],
                'testType': test_data['testType']['name']
            }

            warnings = result['createTest'].get('warnings', [])
            return self.create_success_result(response_data, warnings)

        except Exception as e:
            return self.create_error_result(f"Failed to create test: {str(e)}")

    async def get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get test by issue ID."""
        issue_id = params.get('issue_id')
        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")

        try:
            variables = {'issueId': issue_id}
            result = await self.execute_query(GET_TEST, variables)

            if not result.get('getTest'):
                return self.create_error_result(f"Test with issue ID {issue_id} not found")

            test_data = result['getTest']
            response_data = self.extract_jira_data(test_data)
            response_data['testType'] = test_data['testType']['name']

            # Add test-specific data
            if test_data.get('steps'):
                response_data['steps'] = test_data['steps']
            if test_data.get('gherkin'):
                response_data['gherkin'] = test_data['gherkin']
            if test_data.get('lastModified'):
                response_data['lastModified'] = test_data['lastModified']

            return self.create_success_result(response_data)

        except Exception as e:
            return self.create_error_result(f"Failed to get test: {str(e)}")

    async def list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List tests with optional filtering."""
        project_key = params.get('project_key')
        jql = params.get('jql')
        limit = min(params.get('limit', 50), 100)
        start = params.get('start', 0)

        try:
            # Build JQL query
            final_jql = self.build_jql(project_key, jql, 'Test')

            variables = {
                'jql': final_jql,
                'limit': limit,
                'start': start
            }

            result = await self.execute_query(LIST_TESTS, variables)
            tests_data = result['getTests']

            # Transform results
            tests = []
            for test in tests_data['results']:
                test_info = self.extract_jira_data(test)
                test_info['testType'] = test['testType']['name']
                if test.get('lastModified'):
                    test_info['lastModified'] = test['lastModified']
                tests.append(test_info)

            response_data = {
                'tests': tests,
                'total': tests_data['total'],
                'start': tests_data['start'],
                'limit': tests_data['limit']
            }

            return self.create_success_result(response_data)

        except Exception as e:
            return self.create_error_result(f"Failed to list tests: {str(e)}")

    async def delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete test by issue ID."""
        issue_id = params.get('issue_id')
        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")

        try:
            # First verify the test exists
            get_result = await self.get({'issue_id': issue_id})
            if not get_result['success']:
                return self.create_error_result(f"Cannot delete test: {get_result['errors'][0]}")

            variables = {'issueId': issue_id}
            await self.execute_query(DELETE_TEST, variables)

            response_data = {
                'message': f'Test with issue ID {issue_id} has been deleted successfully'
            }
            return self.create_success_result(response_data)

        except Exception as e:
            return self.create_error_result(f"Failed to delete test: {str(e)}")

    async def update_type(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update test type."""
        issue_id = params.get('issue_id')
        test_type = params.get('test_type')

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")
        if not test_type:
            return self.create_error_result("Missing required parameter: test_type")

        try:
            variables = {
                'issueId': issue_id,
                'testType': {'name': test_type}
            }

            result = await self.execute_query(UPDATE_TEST_TYPE, variables)
            warnings = result['updateTestType'].get('warnings', [])

            response_data = {
                'issueId': issue_id,
                'testType': test_type,
                'message': f'Test type updated to {test_type}'
            }

            return self.create_success_result(response_data, warnings)

        except Exception as e:
            return self.create_error_result(f"Failed to update test type: {str(e)}")

    async def update_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update test content (Gherkin for Cucumber tests)."""
        issue_id = params.get('issue_id')
        gherkin = params.get('gherkin')
        steps = params.get('steps')

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")

        if gherkin:
            # Update Gherkin content for Cucumber tests
            try:
                variables = {
                    'issueId': issue_id,
                    'gherkin': gherkin
                }

                result = await self.execute_query(UPDATE_GHERKIN_TEST_DEFINITION, variables)
                warnings = result['updateGherkinTestDefinition'].get('warnings', [])

                response_data = {
                    'issueId': issue_id,
                    'gherkin': gherkin,
                    'message': 'Test Gherkin content updated successfully'
                }

                return self.create_success_result(response_data, warnings)

            except Exception as e:
                return self.create_error_result(f"Failed to update test content: {str(e)}")

        elif steps:
            # Manual test steps require individual step operations
            return self.create_success_result({
                'issueId': issue_id,
                'message': 'Manual test step updates require individual step operations'
            }, ['Step updates require individual step operations'])

        else:
            return self.create_error_result("No content updates specified (gherkin or steps required)")