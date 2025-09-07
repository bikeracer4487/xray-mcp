"""TestExecutionTool for managing Xray test executions via GraphQL API."""

from typing import Dict, Any, Optional, List
from src.graphql_client import XrayGraphQLClient


class TestExecutionTool:
    """Tool for managing Xray test executions via GraphQL API."""
    
    def __init__(self, client: XrayGraphQLClient):
        """Initialize TestExecutionTool with GraphQL client.
        
        Args:
            client: Authenticated XrayGraphQLClient instance
        """
        self.client = client
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test execution operation based on action parameter.
        
        Args:
            params: Dictionary containing action and action-specific parameters
            
        Returns:
            Dictionary containing operation results
            
        Raises:
            ValueError: If action is invalid or required parameters are missing
            Exception: If GraphQL operation fails
        """
        action = params.get('action')
        
        if not action:
            raise ValueError("Missing required parameter: action")
        
        if action == 'create':
            return await self._create_test_execution(params)
        elif action == 'get':
            return await self._get_test_execution(params)
        elif action == 'delete':
            return await self._delete_test_execution(params)
        elif action == 'add_tests':
            return await self._add_tests(params)
        elif action == 'remove_tests':
            return await self._remove_tests(params)
        else:
            raise ValueError(f"Invalid action: {action}")
    
    async def _create_test_execution(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new test execution."""
        project_key = params.get('project_key')
        summary = params.get('summary')
        test_ids = params.get('test_ids', [])
        test_environments = params.get('test_environments', [])
        
        if not project_key:
            raise ValueError("Missing required parameter: project_key")
        if not summary:
            raise ValueError("Missing required parameter: summary")
        
        mutation = """
        mutation CreateTestExecution(
            $testIssueIds: [String!],
            $testEnvironments: [String!],
            $summary: String!,
            $projectKey: String!
        ) {
            createTestExecution(
                testIssueIds: $testIssueIds,
                testEnvironments: $testEnvironments,
                jira: {
                    fields: { 
                        summary: $summary, 
                        project: {key: $projectKey}
                    }
                }
            ) {
                testExecution {
                    issueId
                    jira(fields: ["key", "summary"])
                }
                warnings
                createdTestEnvironments
            }
        }
        """
        
        variables = {
            "testIssueIds": test_ids,
            "testEnvironments": test_environments,
            "summary": summary,
            "projectKey": project_key
        }
        
        try:
            result = await self.client.execute(mutation, variables)
            
            execution_data = result['createTestExecution']['testExecution']
            jira_data = execution_data['jira']
            
            response = {
                'issueId': execution_data['issueId'],
                'issueKey': jira_data['key'],
                'summary': jira_data['summary']
            }
            
            if result['createTestExecution'].get('warnings'):
                response['warnings'] = result['createTestExecution']['warnings']
            if result['createTestExecution'].get('createdTestEnvironments'):
                response['createdTestEnvironments'] = result['createTestExecution']['createdTestEnvironments']
            
            return response
            
        except Exception as e:
            raise Exception(f"Failed to create test execution: {str(e)}")
    
    async def _get_test_execution(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get test execution by issue ID."""
        issue_id = params.get('issue_id')
        
        if not issue_id:
            raise ValueError("Missing required parameter: issue_id")
        
        query = """
        query GetTestExecution($issueId: String!) {
            getTestExecution(issueId: $issueId) {
                issueId
                projectId
                jira(fields: ["key", "summary", "description", "assignee", "reporter"])
                tests(limit: 100) {
                    total
                    start
                    limit
                    results {
                        issueId
                        testType {
                            name
                        }
                        jira(fields: ["key", "summary"])
                    }
                }
            }
        }
        """
        
        variables = {"issueId": issue_id}
        
        try:
            result = await self.client.execute(query, variables)
            
            if not result.get('getTestExecution'):
                raise Exception(f"Test execution with issue ID {issue_id} not found")
            
            execution_data = result['getTestExecution']
            jira_data = execution_data['jira']
            
            response = {
                'issueId': execution_data['issueId'],
                'issueKey': jira_data['key'],
                'summary': jira_data['summary'],
                'projectId': execution_data['projectId']
            }
            
            # Add optional fields
            if jira_data.get('description'):
                response['description'] = jira_data['description']
            if jira_data.get('assignee'):
                response['assignee'] = jira_data['assignee']
            if jira_data.get('reporter'):
                response['reporter'] = jira_data['reporter']
            if execution_data.get('tests'):
                response['tests'] = execution_data['tests']
            
            return response
            
        except Exception as e:
            if "not found" in str(e).lower():
                raise Exception(f"Test execution with issue ID {issue_id} not found")
            raise Exception(f"Failed to get test execution: {str(e)}")
    
    async def _delete_test_execution(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete test execution by issue ID."""
        issue_id = params.get('issue_id')
        
        if not issue_id:
            raise ValueError("Missing required parameter: issue_id")
        
        # First verify the test execution exists
        try:
            await self._get_test_execution({'issue_id': issue_id})
        except Exception as e:
            if "not found" in str(e).lower():
                raise Exception(f"Cannot delete test execution: Test execution with issue ID {issue_id} not found")
            raise e
        
        mutation = """
        mutation DeleteTestExecution($issueId: String!) {
            deleteTestExecution(issueId: $issueId)
        }
        """
        
        variables = {"issueId": issue_id}
        
        try:
            await self.client.execute(mutation, variables)
            
            return {
                'success': True,
                'message': f'Test execution with issue ID {issue_id} has been deleted successfully'
            }
            
        except Exception as e:
            raise Exception(f"Failed to delete test execution: {str(e)}")
    
    async def _add_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add tests to test execution."""
        issue_id = params.get('issue_id')
        test_ids = params.get('test_ids', [])
        
        if not issue_id:
            raise ValueError("Missing required parameter: issue_id")
        if not test_ids:
            raise ValueError("Missing required parameter: test_ids")
        
        mutation = """
        mutation AddTestsToTestExecution($issueId: String!, $testIssueIds: [String!]!) {
            addTestsToTestExecution(issueId: $issueId, testIssueIds: $testIssueIds) {
                addedTests
                warning
            }
        }
        """
        
        variables = {
            "issueId": issue_id,
            "testIssueIds": test_ids
        }
        
        try:
            result = await self.client.execute(mutation, variables)
            return result['addTestsToTestExecution']
            
        except Exception as e:
            raise Exception(f"Failed to add tests to test execution: {str(e)}")
    
    async def _remove_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove tests from test execution."""
        issue_id = params.get('issue_id')
        test_ids = params.get('test_ids', [])
        
        if not issue_id:
            raise ValueError("Missing required parameter: issue_id")
        if not test_ids:
            raise ValueError("Missing required parameter: test_ids")
        
        mutation = """
        mutation RemoveTestsFromTestExecution($issueId: String!, $testIssueIds: [String!]!) {
            removeTestsFromTestExecution(issueId: $issueId, testIssueIds: $testIssueIds)
        }
        """
        
        variables = {
            "issueId": issue_id,
            "testIssueIds": test_ids
        }
        
        try:
            await self.client.execute(mutation, variables)
            
            return {
                'success': True,
                'message': f'Tests {test_ids} removed from test execution {issue_id}'
            }
            
        except Exception as e:
            raise Exception(f"Failed to remove tests from test execution: {str(e)}")