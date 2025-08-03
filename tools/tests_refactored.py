"""Refactored test management tools using abstractions.

This module demonstrates how to use the abstraction layer to create
cleaner, more testable tool implementations with less code duplication.
"""

from typing import Dict, Any, List, Optional

# Handle both package and direct execution import modes
try:
    from ..abstractions import BaseTool, Repository, tool_error_handler, validate_required
    from ..exceptions import ValidationError
    from ..validators import validate_jql
except ImportError:
    import sys
    sys.path.append('..')
    from abstractions import BaseTool, Repository, tool_error_handler, validate_required
    from exceptions import ValidationError
    from validators import validate_jql


class TestToolsRefactored(BaseTool):
    """Refactored tools for managing tests in Xray.
    
    This implementation uses the abstraction layer to reduce coupling
    with the GraphQL client and standardize error handling.
    """
    
    def __init__(self, repository: Repository):
        """Initialize with a repository instead of GraphQL client."""
        super().__init__(repository)
        self._name = "TestTools"
        self._description = "Tools for managing tests in Xray"
    
    @tool_error_handler
    @validate_required('issue_id')
    async def get_test(self, issue_id: str) -> Dict[str, Any]:
        """Retrieve a single test by issue ID.
        
        Args:
            issue_id: The Jira issue ID of the test
            
        Returns:
            Test information including type, steps, and other fields
        """
        query = """
        query GetTest($issueId: String!) {
            getTests(jql: "issue = $issueId", limit: 1) {
                total
                results {
                    issueId
                    jira {
                        key
                        summary
                        description
                        project {
                            key
                            name
                        }
                    }
                    testType {
                        name
                        kind
                    }
                    steps {
                        id
                        action
                        data
                        result
                    }
                    gherkin
                    unstructured
                }
            }
        }
        """
        
        # Use string interpolation instead of GraphQL variables for simple cases
        jql = f'issue = "{issue_id}"'
        safe_jql = validate_jql(jql)
        
        result = await self.repository.execute_query(
            query.replace('$issueId', safe_jql),
            {}
        )
        
        tests = result.get("getTests", {})
        if tests.get("total", 0) == 0:
            raise ValidationError(f"Test not found: {issue_id}")
        
        return tests["results"][0]
    
    @tool_error_handler
    async def get_tests(
        self,
        jql: Optional[str] = None,
        limit: int = 100,
        start: int = 0
    ) -> Dict[str, Any]:
        """Retrieve multiple tests based on JQL query.
        
        Args:
            jql: Optional JQL query to filter tests
            limit: Maximum number of tests to return (default: 100)
            start: Starting index for pagination (default: 0)
            
        Returns:
            Dictionary containing total count and list of tests
        """
        # Validate JQL if provided
        if jql:
            jql = validate_jql(jql)
        else:
            jql = 'type = "Test"'
        
        query = """
        query GetTests($jql: String!, $limit: Int!, $start: Int!) {
            getTests(jql: $jql, limit: $limit, start: $start) {
                total
                start
                results {
                    issueId
                    jira {
                        key
                        summary
                        project {
                            key
                        }
                    }
                    testType {
                        name
                    }
                }
            }
        }
        """
        
        variables = {
            "jql": jql,
            "limit": limit,
            "start": start
        }
        
        return await self.repository.execute_query(query, variables)
    
    @tool_error_handler
    @validate_required('project_key', 'summary', 'test_type')
    async def create_test(
        self,
        project_key: str,
        summary: str,
        test_type: str,
        description: Optional[str] = None,
        steps: Optional[List[Dict[str, str]]] = None,
        gherkin: Optional[str] = None,
        unstructured: Optional[str] = None,
        labels: Optional[List[str]] = None,
        components: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new test in Xray.
        
        Args:
            project_key: Jira project key
            summary: Test summary
            test_type: Type of test (Manual, Cucumber, Generic)
            description: Optional test description
            steps: Optional list of test steps (for Manual tests)
            gherkin: Optional Gherkin content (for Cucumber tests)
            unstructured: Optional unstructured content (for Generic tests)
            labels: Optional list of labels
            components: Optional list of components
            
        Returns:
            Created test information
        """
        # Validate test type
        valid_types = ["Manual", "Cucumber", "Generic"]
        if test_type not in valid_types:
            raise ValidationError(f"Invalid test type: {test_type}. Must be one of {valid_types}")
        
        # Build mutation based on test type
        if test_type == "Manual":
            mutation = self._build_manual_test_mutation()
            variables = self._build_manual_test_variables(
                project_key, summary, description, steps, labels, components
            )
        elif test_type == "Cucumber":
            mutation = self._build_cucumber_test_mutation()
            variables = self._build_cucumber_test_variables(
                project_key, summary, description, gherkin, labels, components
            )
        else:  # Generic
            mutation = self._build_generic_test_mutation()
            variables = self._build_generic_test_variables(
                project_key, summary, description, unstructured, labels, components
            )
        
        return await self.repository.execute_mutation(mutation, variables)
    
    @tool_error_handler
    @validate_required('issue_id')
    async def delete_test(self, issue_id: str) -> Dict[str, Any]:
        """Delete a test from Xray.
        
        Args:
            issue_id: The Jira issue ID of the test to delete
            
        Returns:
            Deletion confirmation
        """
        mutation = """
        mutation DeleteTest($issueId: String!) {
            deleteTest(issueId: $issueId) {
                success
                message
            }
        }
        """
        
        variables = {"issueId": issue_id}
        
        result = await self.repository.execute_mutation(mutation, variables)
        
        if not result.get("deleteTest", {}).get("success", False):
            raise Exception(
                f"Failed to delete test: {result.get('deleteTest', {}).get('message', 'Unknown error')}"
            )
        
        return {"success": True, "issue_id": issue_id}
    
    # Private helper methods
    def _build_manual_test_mutation(self) -> str:
        """Build GraphQL mutation for creating Manual test."""
        return """
        mutation CreateManualTest(
            $projectKey: String!,
            $summary: String!,
            $description: String,
            $steps: [TestStepInput!],
            $labels: [String!],
            $components: [String!]
        ) {
            createTest(
                testType: {name: "Manual"},
                testSpecification: {
                    projectKey: $projectKey,
                    summary: $summary,
                    description: $description,
                    labels: $labels,
                    components: $components,
                    steps: $steps
                }
            ) {
                issueId
                jira {
                    key
                    summary
                }
                testType {
                    name
                }
            }
        }
        """
    
    def _build_manual_test_variables(
        self,
        project_key: str,
        summary: str,
        description: Optional[str],
        steps: Optional[List[Dict[str, str]]],
        labels: Optional[List[str]],
        components: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Build variables for Manual test creation."""
        variables = {
            "projectKey": project_key,
            "summary": summary,
            "description": description,
            "labels": labels or [],
            "components": components or []
        }
        
        # Format steps if provided
        if steps:
            variables["steps"] = [
                {
                    "action": step.get("action", ""),
                    "data": step.get("data", ""),
                    "result": step.get("result", "")
                }
                for step in steps
            ]
        
        return variables
    
    def _build_cucumber_test_mutation(self) -> str:
        """Build GraphQL mutation for creating Cucumber test."""
        return """
        mutation CreateCucumberTest(
            $projectKey: String!,
            $summary: String!,
            $description: String,
            $gherkin: String!,
            $labels: [String!],
            $components: [String!]
        ) {
            createTest(
                testType: {name: "Cucumber"},
                testSpecification: {
                    projectKey: $projectKey,
                    summary: $summary,
                    description: $description,
                    labels: $labels,
                    components: $components,
                    gherkin: $gherkin
                }
            ) {
                issueId
                jira {
                    key
                    summary
                }
                testType {
                    name
                }
            }
        }
        """
    
    def _build_cucumber_test_variables(
        self,
        project_key: str,
        summary: str,
        description: Optional[str],
        gherkin: Optional[str],
        labels: Optional[List[str]],
        components: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Build variables for Cucumber test creation."""
        if not gherkin:
            raise ValidationError("Gherkin content is required for Cucumber tests")
        
        return {
            "projectKey": project_key,
            "summary": summary,
            "description": description,
            "gherkin": gherkin,
            "labels": labels or [],
            "components": components or []
        }
    
    def _build_generic_test_mutation(self) -> str:
        """Build GraphQL mutation for creating Generic test."""
        return """
        mutation CreateGenericTest(
            $projectKey: String!,
            $summary: String!,
            $description: String,
            $unstructured: String!,
            $labels: [String!],
            $components: [String!]
        ) {
            createTest(
                testType: {name: "Generic"},
                testSpecification: {
                    projectKey: $projectKey,
                    summary: $summary,
                    description: $description,
                    labels: $labels,
                    components: $components,
                    unstructured: $unstructured
                }
            ) {
                issueId
                jira {
                    key
                    summary
                }
                testType {
                    name
                }
            }
        }
        """
    
    def _build_generic_test_variables(
        self,
        project_key: str,
        summary: str,
        description: Optional[str],
        unstructured: Optional[str],
        labels: Optional[List[str]],
        components: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Build variables for Generic test creation."""
        if not unstructured:
            raise ValidationError("Unstructured content is required for Generic tests")
        
        return {
            "projectKey": project_key,
            "summary": summary,
            "description": description,
            "unstructured": unstructured,
            "labels": labels or [],
            "components": components or []
        }
    
    # Implement the abstract execute method
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute tool based on the action parameter."""
        action = kwargs.get('action')
        
        if action == 'get':
            return await self.get_test(kwargs.get('issue_id'))
        elif action == 'list':
            return await self.get_tests(
                kwargs.get('jql'),
                kwargs.get('limit', 100),
                kwargs.get('start', 0)
            )
        elif action == 'create':
            return await self.create_test(**kwargs)
        elif action == 'delete':
            return await self.delete_test(kwargs.get('issue_id'))
        else:
            raise ValidationError(f"Unknown action: {action}")