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
        elif action == 'add_environments':
            return await self._add_environments(params)
        elif action == 'remove_environments':
            return await self._remove_environments(params)
        elif action == 'get_test_runs':
            return await self._get_test_runs(params)
        elif action == 'list':
            return await self._list_test_executions(params)
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
                    testEnvironments
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
            
            # Include test environments from the execution data
            if execution_data.get('testEnvironments'):
                response['testEnvironments'] = execution_data['testEnvironments']
            
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
            response = result['addTestsToTestExecution']
            response['success'] = True
            return response
            
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
    
    async def _add_environments(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add test environments to test execution."""
        issue_id = params.get('issue_id')
        environments = params.get('environments', [])
        
        if not issue_id:
            raise ValueError("Missing required parameter: issue_id")
        if not environments:
            raise ValueError("Missing required parameter: environments")
        
        mutation = """
        mutation AddTestEnvironmentsToTestExecution($issueId: String!, $testEnvironments: [String!]!) {
            addTestEnvironmentsToTestExecution(issueId: $issueId, testEnvironments: $testEnvironments) {
                associatedTestEnvironments
                createdTestEnvironments
                warning
            }
        }
        """
        
        variables = {
            "issueId": issue_id,
            "testEnvironments": environments
        }
        
        try:
            result = await self.client.execute(mutation, variables)
            response = result['addTestEnvironmentsToTestExecution']
            response['success'] = True
            return response
            
        except Exception as e:
            raise Exception(f"Failed to add test environments to test execution: {str(e)}")
    
    async def _remove_environments(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove test environments from test execution."""
        issue_id = params.get('issue_id')
        environments = params.get('environments', [])
        
        if not issue_id:
            raise ValueError("Missing required parameter: issue_id")
        if not environments:
            raise ValueError("Missing required parameter: environments")
        
        mutation = """
        mutation RemoveTestEnvironmentsFromTestExecution($issueId: String!, $testEnvironments: [String!]!) {
            removeTestEnvironmentsFromTestExecution(issueId: $issueId, testEnvironments: $testEnvironments)
        }
        """
        
        variables = {
            "issueId": issue_id,
            "testEnvironments": environments
        }
        
        try:
            await self.client.execute(mutation, variables)
            
            return {
                'success': True,
                'message': f'Test environments {environments} removed from test execution {issue_id}'
            }
            
        except Exception as e:
            raise Exception(f"Failed to remove test environments from test execution: {str(e)}")
    
    async def _get_test_runs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get test runs for a test execution."""
        issue_id = params.get('issue_id')
        limit = params.get('limit', 50)
        start = params.get('start', 0)
        
        if not issue_id:
            raise ValueError("Missing required parameter: issue_id")
        
        # Ensure limit doesn't exceed 100 (Xray constraint)
        if limit > 100:
            limit = 100
        
        query = """
        query GetTestExecution($issueId: String!, $limit: Int!, $start: Int!) {
            getTestExecution(issueId: $issueId) {
                testRuns(limit: $limit, start: $start) {
                    total
                    start
                    limit
                    results {
                        id
                        status {
                            name
                            color
                            description
                        }
                        comment
                        startedOn
                        finishedOn
                        executedById
                        assigneeId
                        evidence {
                            id
                            filename
                        }
                        defects
                        test {
                            issueId
                        }
                        testExecution {
                            issueId
                        }
                        testType {
                            name
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "issueId": issue_id,
            "limit": limit,
            "start": start
        }
        
        try:
            result = await self.client.execute(query, variables)
            
            if not result.get('getTestExecution'):
                raise Exception(f"Test execution with issue ID {issue_id} not found")
            
            test_runs_data = result['getTestExecution']['testRuns']
            
            return {
                'testRuns': test_runs_data['results'],
                'total': test_runs_data['total'],
                'start': test_runs_data['start'],
                'limit': test_runs_data['limit']
            }
            
        except Exception as e:
            if "not found" in str(e).lower():
                raise Exception(f"Test execution with issue ID {issue_id} not found")
            raise Exception(f"Failed to get test runs for test execution: {str(e)}")
    
    async def _list_test_executions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List test executions with optional filtering."""
        project_key = params.get('project_key')
        jql = params.get('jql')
        limit = params.get('limit', 50)
        start = params.get('start', 0)
        
        # Ensure limit doesn't exceed 100 (Xray constraint)
        if limit > 100:
            limit = 100
        
        # Build JQL query
        if project_key and not jql:
            jql = f"project = {project_key} AND issuetype = 'Test Execution'"
        elif not jql:
            # Default to getting recent test executions if no filter provided
            jql = "issuetype = 'Test Execution' ORDER BY created DESC"
        
        query = """
        query GetTestExecutions($jql: String!, $limit: Int!, $start: Int!) {
            getTestExecutions(jql: $jql, limit: $limit, start: $start) {
                total
                start
                limit
                results {
                    issueId
                    projectId
                    testEnvironments
                    jira(fields: ["key", "summary", "description", "assignee", "reporter", "created", "updated"])
                    lastModified
                }
            }
        }
        """
        
        variables = {
            "jql": jql,
            "limit": limit,
            "start": start
        }
        
        try:
            result = await self.client.execute(query, variables)
            
            executions_data = result['getTestExecutions']
            
            return {
                'executions': executions_data['results'],
                'total': executions_data['total'],
                'start': executions_data['start'],
                'limit': executions_data['limit']
            }
            
        except Exception as e:
            raise Exception(f"Failed to list test executions: {str(e)}")