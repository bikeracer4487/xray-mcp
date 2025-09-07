"""
Test Tool for Xray MCP Server.

Handles test management operations including create, get, update, list, and delete.
"""

from typing import Dict, Any, List, Optional
from ..graphql_client import XrayGraphQLClient


class TestTool:
    """Tool for managing Xray tests via GraphQL API."""
    
    def __init__(self, client: XrayGraphQLClient):
        """Initialize TestTool with GraphQL client.
        
        Args:
            client: Authenticated XrayGraphQLClient instance
        """
        self.client = client
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test operation based on action parameter.
        
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
            return await self._create_test(params)
        elif action == 'get':
            return await self._get_test(params)
        elif action == 'update':
            return await self._update_test(params)
        elif action == 'list':
            return await self._list_tests(params)
        elif action == 'delete':
            return await self._delete_test(params)
        else:
            raise ValueError(f"Invalid action: {action}")
    
    async def _create_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new test."""
        test_type = params.get('test_type')
        project_key = params.get('project_key')
        summary = params.get('summary')
        description = params.get('description', '')
        steps = params.get('steps', [])
        
        if not test_type:
            raise ValueError("Missing required parameter: test_type")
        if not project_key:
            raise ValueError("Missing required parameter: project_key")
        if not summary:
            raise ValueError("Missing required parameter: summary")
        
        mutation_parts = []
        variables = {}
        
        if test_type.lower() == 'manual':
            # Manual test with steps
            mutation = """
            mutation CreateManualTest($testType: UpdateTestTypeInput!, $steps: [CreateStepInput!], $summary: String!, $projectKey: String!, $description: String) {
                createTest(
                    testType: $testType,
                    steps: $steps,
                    jira: {
                        fields: { 
                            summary: $summary, 
                            project: {key: $projectKey},
                            description: $description
                        }
                    }
                ) {
                    test {
                        issueId
                        testType { name }
                        steps {
                            action
                            data
                            result
                        }
                        jira(fields: ["key", "summary"])
                    }
                    warnings
                }
            }
            """
            
            variables = {
                "testType": {"name": "Manual"},
                "steps": [
                    {
                        "action": step.get('action', ''),
                        "data": step.get('data', ''),
                        "result": step.get('result', '')
                    }
                    for step in steps
                ],
                "summary": summary,
                "projectKey": project_key,
                "description": description
            }
            
        elif test_type.lower() == 'generic':
            # Generic test with unstructured definition
            mutation = """
            mutation CreateGenericTest($testType: UpdateTestTypeInput!, $unstructured: String, $summary: String!, $projectKey: String!, $description: String) {
                createTest(
                    testType: $testType,
                    unstructured: $unstructured,
                    jira: {
                        fields: { 
                            summary: $summary, 
                            project: {key: $projectKey},
                            description: $description
                        }
                    }
                ) {
                    test {
                        issueId
                        testType { name }
                        unstructured
                        jira(fields: ["key", "summary"])
                    }
                    warnings
                }
            }
            """
            
            variables = {
                "testType": {"name": "Generic"},
                "unstructured": description or "Generic test definition",
                "summary": summary,
                "projectKey": project_key,
                "description": description
            }
            
        elif test_type.lower() == 'cucumber':
            # Cucumber test with gherkin
            gherkin = params.get('gherkin', 'Feature: Test\n  Scenario: Test scenario\n    Given a test\n    When executed\n    Then it passes')
            
            mutation = """
            mutation CreateCucumberTest($testType: UpdateTestTypeInput!, $gherkin: String, $summary: String!, $projectKey: String!, $description: String) {
                createTest(
                    testType: $testType,
                    gherkin: $gherkin,
                    jira: {
                        fields: { 
                            summary: $summary, 
                            project: {key: $projectKey},
                            description: $description
                        }
                    }
                ) {
                    test {
                        issueId
                        testType { name }
                        gherkin
                        jira(fields: ["key", "summary"])
                    }
                    warnings
                }
            }
            """
            
            variables = {
                "testType": {"name": "Cucumber"},
                "gherkin": gherkin,
                "summary": summary,
                "projectKey": project_key,
                "description": description
            }
            
        else:
            raise ValueError(f"Unsupported test type: {test_type}")
        
        try:
            result = await self.client.execute(mutation, variables)
            
            test_data = result['createTest']['test']
            jira_data = test_data['jira']
            
            response = {
                'issueId': test_data['issueId'],
                'issueKey': jira_data['key'],
                'summary': jira_data['summary'],
                'testType': test_data['testType']['name']
            }
            
            # Add type-specific data
            if 'steps' in test_data:
                response['steps'] = test_data['steps']
            if 'unstructured' in test_data:
                response['unstructured'] = test_data['unstructured']
            if 'gherkin' in test_data:
                response['gherkin'] = test_data['gherkin']
            
            if result['createTest'].get('warnings'):
                response['warnings'] = result['createTest']['warnings']
            
            return response
            
        except Exception as e:
            raise Exception(f"Failed to create test: {str(e)}")
    
    async def _get_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get test by issue ID."""
        issue_id = params.get('issue_id')
        
        if not issue_id:
            raise ValueError("Missing required parameter: issue_id")
        
        query = """
        query GetTest($issueId: String!) {
            getTest(issueId: $issueId) {
                issueId
                testType { name }
                steps {
                    action
                    data
                    result
                }
                unstructured
                gherkin
                jira(fields: ["key", "summary", "description"])
            }
        }
        """
        
        variables = {"issueId": issue_id}
        
        try:
            result = await self.client.execute(query, variables)
            
            if not result.get('getTest'):
                raise Exception(f"Test with issue ID {issue_id} not found")
            
            test_data = result['getTest']
            jira_data = test_data['jira']
            
            response = {
                'issueId': test_data['issueId'],
                'issueKey': jira_data['key'],
                'summary': jira_data['summary'],
                'testType': test_data['testType']['name']
            }
            
            # Add optional fields
            if jira_data.get('description'):
                response['description'] = jira_data['description']
            if test_data.get('steps'):
                response['steps'] = test_data['steps']
            if test_data.get('unstructured'):
                response['unstructured'] = test_data['unstructured']
            if test_data.get('gherkin'):
                response['gherkin'] = test_data['gherkin']
            
            return response
            
        except Exception as e:
            if "not found" in str(e).lower():
                raise Exception(f"Test with issue ID {issue_id} not found")
            raise Exception(f"Failed to get test: {str(e)}")
    
    async def _update_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing test."""
        issue_id = params.get('issue_id')
        
        if not issue_id:
            raise ValueError("Missing required parameter: issue_id")
        
        # Get the current test to understand its current state
        current_test = await self._get_test({'issue_id': issue_id})
        
        updates_made = []
        
        # Update test type if provided
        new_test_type = params.get('test_type')
        if new_test_type and new_test_type != current_test['testType']:
            await self._update_test_type(issue_id, new_test_type)
            updates_made.append('test_type')
        
        # Update description via unstructured definition for Generic tests
        description = params.get('description')
        final_test_type = new_test_type or current_test['testType']
        
        if description and final_test_type.lower() == 'generic':
            await self._update_unstructured_definition(issue_id, description)
            updates_made.append('description')
        
        # Update steps for Manual tests
        steps = params.get('steps')
        if steps is not None and final_test_type.lower() == 'manual':
            await self._update_test_steps(issue_id, steps)
            updates_made.append('steps')
        
        # Get the updated test to return
        updated_test = await self._get_test({'issue_id': issue_id})
        updated_test['updates_made'] = updates_made
        
        return updated_test
    
    async def _update_test_type(self, issue_id: str, test_type: str) -> None:
        """Update the test type of an existing test."""
        mutation = """
        mutation UpdateTestType($issueId: String!, $testType: UpdateTestTypeInput!) {
            updateTestType(issueId: $issueId, testType: $testType) {
                issueId
                testType { name }
            }
        }
        """
        
        variables = {
            "issueId": issue_id,
            "testType": {"name": test_type}
        }
        
        await self.client.execute(mutation, variables)
    
    async def _update_unstructured_definition(self, issue_id: str, unstructured: str) -> None:
        """Update the unstructured definition of a generic test."""
        mutation = """
        mutation UpdateUnstructuredDefinition($issueId: String!, $unstructured: String!) {
            updateUnstructuredTestDefinition(issueId: $issueId, unstructured: $unstructured) {
                issueId
                unstructured
            }
        }
        """
        
        variables = {
            "issueId": issue_id,
            "unstructured": unstructured
        }
        
        await self.client.execute(mutation, variables)
    
    async def _update_test_steps(self, issue_id: str, steps: List[Dict[str, Any]]) -> None:
        """Update test steps by removing all existing steps and adding new ones."""
        # First, remove all existing steps
        remove_mutation = """
        mutation RemoveAllSteps($issueId: String!) {
            removeAllTestSteps(issueId: $issueId)
        }
        """
        
        await self.client.execute(remove_mutation, {"issueId": issue_id})
        
        # Then add new steps
        for step in steps:
            add_mutation = """
            mutation AddTestStep($issueId: String!, $step: CreateStepInput!) {
                addTestStep(issueId: $issueId, step: $step) {
                    id
                    action
                    data
                    result
                }
            }
            """
            
            step_input = {
                "action": step.get('action', ''),
                "data": step.get('data', ''),
                "result": step.get('result', '')
            }
            
            variables = {
                "issueId": issue_id,
                "step": step_input
            }
            
            await self.client.execute(add_mutation, variables)
    
    async def _list_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List tests with optional filtering."""
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
            query_jql = f"project = '{project_key}' AND issuetype = 'Test'"
        else:
            # Default to all tests (be careful with this)
            query_jql = "issuetype = 'Test'"
        
        # Ensure limit doesn't exceed 100 (Xray constraint)
        if limit > 100:
            limit = 100
        
        query = """
        query GetTests($jql: String!, $limit: Int!, $start: Int!) {
            getTests(jql: $jql, limit: $limit, start: $start) {
                total
                start
                limit
                results {
                    issueId
                    testType { name }
                    steps {
                        action
                        data
                        result
                    }
                    unstructured
                    gherkin
                    jira(fields: ["key", "summary", "description"])
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
            
            tests_data = result['getTests']
            tests = []
            
            for test_data in tests_data['results']:
                jira_data = test_data['jira']
                
                test_item = {
                    'issueId': test_data['issueId'],
                    'issueKey': jira_data['key'],
                    'summary': jira_data['summary'],
                    'testType': test_data['testType']['name']
                }
                
                # Add optional fields
                if jira_data.get('description'):
                    test_item['description'] = jira_data['description']
                if test_data.get('steps'):
                    test_item['steps'] = test_data['steps']
                if test_data.get('unstructured'):
                    test_item['unstructured'] = test_data['unstructured']
                if test_data.get('gherkin'):
                    test_item['gherkin'] = test_data['gherkin']
                
                tests.append(test_item)
            
            return {
                'tests': tests,
                'total': tests_data['total'],
                'start': tests_data['start'],
                'limit': tests_data['limit']
            }
            
        except Exception as e:
            raise Exception(f"Failed to list tests: {str(e)}")
    
    async def _delete_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete test by issue ID."""
        issue_id = params.get('issue_id')
        
        if not issue_id:
            raise ValueError("Missing required parameter: issue_id")
        
        # First verify the test exists
        try:
            await self._get_test({'issue_id': issue_id})
        except Exception as e:
            if "not found" in str(e).lower():
                raise Exception(f"Cannot delete test: Test with issue ID {issue_id} not found")
            raise e
        
        mutation = """
        mutation DeleteTest($issueId: String!) {
            deleteTest(issueId: $issueId)
        }
        """
        
        variables = {"issueId": issue_id}
        
        try:
            await self.client.execute(mutation, variables)
            
            return {
                'success': True,
                'message': f'Test with issue ID {issue_id} has been deleted successfully'
            }
            
        except Exception as e:
            raise Exception(f"Failed to delete test: {str(e)}")