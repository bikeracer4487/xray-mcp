"""
Test Set Tool for Xray MCP Server.

Handles test set management operations including create, get, add_tests, remove_tests, list, and delete.
"""

from typing import Dict, Any, List, Optional
from ..graphql_client import XrayGraphQLClient


class TestSetTool:
    """Tool for managing Xray test sets via GraphQL API."""
    
    def __init__(self, client: XrayGraphQLClient):
        """Initialize TestSetTool with GraphQL client.
        
        Args:
            client: Authenticated XrayGraphQLClient instance
        """
        self.client = client
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test set operation based on action parameter.
        
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
            return await self._create_test_set(params)
        elif action == 'get':
            return await self._get_test_set(params)
        elif action == 'add_tests':
            return await self._add_tests_to_test_set(params)
        elif action == 'remove_tests':
            return await self._remove_tests_from_test_set(params)
        elif action == 'list':
            return await self._list_test_sets(params)
        elif action == 'delete':
            return await self._delete_test_set(params)
        else:
            raise ValueError(f"Invalid action: {action}")
    
    async def _create_test_set(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new test set."""
        project_key = params.get('project_key')
        summary = params.get('summary')
        description = params.get('description', '')
        test_ids = params.get('test_ids', [])
        
        if not project_key:
            raise ValueError("Missing required parameter: project_key")
        if not summary:
            raise ValueError("Missing required parameter: summary")
        
        mutation = """
        mutation CreateTestSet($testIssueIds: [String], $summary: String!, $projectKey: String!, $description: String) {
            createTestSet(
                testIssueIds: $testIssueIds, 
                jira: {
                    fields: { 
                        summary: $summary, 
                        project: {key: $projectKey},
                        description: $description
                    }
                }
            ) {
                testSet {
                    issueId
                    jira(fields: ["key", "summary"])
                    tests(limit: 100) {
                        results {
                            issueId
                            jira(fields: ["key"])
                        }
                    }
                }
                warnings
            }
        }
        """
        
        variables = {
            "testIssueIds": test_ids if test_ids else [],
            "summary": summary,
            "projectKey": project_key,
            "description": description
        }
        
        try:
            result = await self.client.execute(mutation, variables)
            
            test_set_data = result['createTestSet']['testSet']
            jira_data = test_set_data['jira']
            
            response = {
                'issueId': test_set_data['issueId'],
                'issueKey': jira_data['key'],
                'summary': jira_data['summary']
            }
            
            # Add test information if tests were included
            if test_set_data.get('tests') and test_set_data['tests'].get('results'):
                response['tests'] = test_set_data['tests']['results']
            else:
                response['tests'] = []
            
            if result['createTestSet'].get('warnings'):
                response['warnings'] = result['createTestSet']['warnings']
            
            return response
            
        except Exception as e:
            raise Exception(f"Failed to create test set: {str(e)}")
    
    async def _get_test_set(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get test set by issue ID."""
        issue_id = params.get('issue_id')
        
        if not issue_id:
            raise ValueError("Missing required parameter: issue_id")
        
        query = """
        query GetTestSet($issueId: String!) {
            getTestSet(issueId: $issueId) {
                issueId
                jira(fields: ["key", "summary", "description"])
                tests(limit: 100) {
                    results {
                        issueId
                        jira(fields: ["key", "summary"])
                    }
                }
            }
        }
        """
        
        variables = {"issueId": issue_id}
        
        try:
            result = await self.client.execute(query, variables)
            
            if not result.get('getTestSet'):
                raise Exception(f"Test set with issue ID {issue_id} not found")
            
            test_set_data = result['getTestSet']
            jira_data = test_set_data['jira']
            
            response = {
                'issueId': test_set_data['issueId'],
                'issueKey': jira_data['key'],
                'summary': jira_data['summary']
            }
            
            # Add optional fields
            if jira_data.get('description'):
                response['description'] = jira_data['description']
            
            # Add tests if available
            if test_set_data.get('tests') and test_set_data['tests'].get('results'):
                response['tests'] = test_set_data['tests']['results']
            else:
                response['tests'] = []
            
            return response
            
        except Exception as e:
            if "not found" in str(e).lower():
                raise Exception(f"Test set with issue ID {issue_id} not found")
            raise Exception(f"Failed to get test set: {str(e)}")
    
    async def _add_tests_to_test_set(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add tests to existing test set."""
        issue_id = params.get('issue_id')
        test_ids = params.get('test_ids')
        
        if not issue_id:
            raise ValueError("Missing required parameter: issue_id")
        if not test_ids or not isinstance(test_ids, list):
            raise ValueError("Missing required parameter: test_ids (must be a list)")
        
        mutation = """
        mutation AddTestsToTestSet($issueId: String!, $testIssueIds: [String]!) {
            addTestsToTestSet(issueId: $issueId, testIssueIds: $testIssueIds) {
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
            
            response = {
                'success': True
            }
            
            if result['addTestsToTestSet'].get('addedTests'):
                response['addedTests'] = result['addTestsToTestSet']['addedTests']
            
            if result['addTestsToTestSet'].get('warning'):
                response['warning'] = result['addTestsToTestSet']['warning']
            
            return response
            
        except Exception as e:
            raise Exception(f"Failed to add tests to test set: {str(e)}")
    
    async def _remove_tests_from_test_set(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove tests from test set."""
        issue_id = params.get('issue_id')
        test_ids = params.get('test_ids')
        
        if not issue_id:
            raise ValueError("Missing required parameter: issue_id")
        if not test_ids or not isinstance(test_ids, list):
            raise ValueError("Missing required parameter: test_ids (must be a list)")
        
        mutation = """
        mutation RemoveTestsFromTestSet($issueId: String!, $testIssueIds: [String]!) {
            removeTestsFromTestSet(issueId: $issueId, testIssueIds: $testIssueIds)
        }
        """
        
        variables = {
            "issueId": issue_id,
            "testIssueIds": test_ids
        }
        
        try:
            await self.client.execute(mutation, variables)
            
            return {
                'success': True
            }
            
        except Exception as e:
            raise Exception(f"Failed to remove tests from test set: {str(e)}")
    
    async def _list_test_sets(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List test sets with optional filtering."""
        project_key = params.get('project_key')
        limit = params.get('limit', 50)
        start = params.get('start', 0)
        jql = params.get('jql')
        
        # Build JQL query
        if jql:
            # Use provided JQL
            query_jql = jql
        elif project_key:
            # Build basic project filter
            query_jql = f"project = '{project_key}' AND issuetype = 'Test Set'"
        else:
            # Default to all test sets (be careful with this)
            query_jql = "issuetype = 'Test Set'"
        
        # Ensure limit doesn't exceed 100 (Xray constraint)
        if limit > 100:
            limit = 100
        
        query = """
        query GetTestSets($jql: String!, $limit: Int!, $start: Int!) {
            getTestSets(jql: $jql, limit: $limit, start: $start) {
                total
                start
                limit
                results {
                    issueId
                    jira(fields: ["key", "summary", "description"])
                    tests(limit: 100) {
                        results {
                            issueId
                            jira(fields: ["key"])
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "jql": query_jql,
            "limit": limit,
            "start": start
        }
        
        try:
            result = await self.client.execute(query, variables)
            
            test_sets_data = result['getTestSets']
            test_sets = []
            
            for test_set_data in test_sets_data['results']:
                jira_data = test_set_data['jira']
                
                test_set_item = {
                    'issueId': test_set_data['issueId'],
                    'issueKey': jira_data['key'],
                    'summary': jira_data['summary']
                }
                
                # Add optional fields
                if jira_data.get('description'):
                    test_set_item['description'] = jira_data['description']
                
                # Add tests if available
                if test_set_data.get('tests') and test_set_data['tests'].get('results'):
                    test_set_item['tests'] = test_set_data['tests']['results']
                else:
                    test_set_item['tests'] = []
                
                test_sets.append(test_set_item)
            
            return {
                'testSets': test_sets,
                'total': test_sets_data['total'],
                'start': test_sets_data['start'],
                'limit': test_sets_data['limit']
            }
            
        except Exception as e:
            raise Exception(f"Failed to list test sets: {str(e)}")
    
    async def _delete_test_set(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete test set by issue ID."""
        issue_id = params.get('issue_id')
        
        if not issue_id:
            raise ValueError("Missing required parameter: issue_id")
        
        # First verify the test set exists
        try:
            await self._get_test_set({'issue_id': issue_id})
        except Exception as e:
            if "not found" in str(e).lower():
                raise Exception(f"Cannot delete test set: Test set with issue ID {issue_id} not found")
            raise e
        
        mutation = """
        mutation DeleteTestSet($issueId: String!) {
            deleteTestSet(issueId: $issueId)
        }
        """
        
        variables = {"issueId": issue_id}
        
        try:
            await self.client.execute(mutation, variables)
            
            return {
                'success': True,
                'message': f'Test set with issue ID {issue_id} has been deleted successfully'
            }
            
        except Exception as e:
            raise Exception(f"Failed to delete test set: {str(e)}")