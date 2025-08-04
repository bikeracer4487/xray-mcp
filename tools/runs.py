"""Test run management tools for Xray MCP server.

This module provides functionality for managing test runs in Xray,
including creating, retrieving, updating, and deleting test runs.
Test runs represent the actual execution of a test within a test execution
context, tracking the results, evidence, and execution details.

The TestRunTools class serves as the main interface for interacting
with Xray's test run API through GraphQL queries and mutations.
"""

from typing import Dict, Any, List, Optional

try:
    from ..client import XrayGraphQLClient
    from ..exceptions import GraphQLError, ValidationError
    from ..validators import validate_jql
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError
    from validators import validate_jql


class TestRunTools:
    """Tools for managing test runs in Xray.
    
    This class provides methods to interact with test runs, which represent
    individual test executions with their results, defects, evidence, and
    execution details. Each test run is associated with a test and a test execution.
    
    Attributes:
        client (XrayGraphQLClient): GraphQL client for API communication
    
    Dependencies:
        - Requires authenticated XrayGraphQLClient instance
        - Depends on Xray GraphQL API for test run operations
    
    Note:
        All methods return structured dictionaries compatible with MCP responses.
        Errors are propagated to calling code for centralized error handling.
    """
    
    def __init__(self, graphql_client: XrayGraphQLClient):
        """Initialize test run tools with GraphQL client.
        
        Args:
            graphql_client (XrayGraphQLClient): Authenticated GraphQL client instance
        """
        self.client = graphql_client
    
    async def get_test_run(self, issue_id: str) -> Dict[str, Any]:
        """Retrieve a single test run by issue ID.
        
        Fetches detailed information about a specific test run including
        its status, execution details, defects, evidence, and comments.
        
        Args:
            issue_id: The Jira issue ID of the test run
        
        Returns:
            Dict containing:
                - issueId: Test run issue ID
                - status: Current execution status
                - executedBy: User who executed the test
                - startedOn: Execution start timestamp
                - finishedOn: Execution end timestamp
                - defects: Associated defect issue IDs
                - evidence: Attached evidence items
                - comment: Execution comments
        
        Raises:
            ValidationError: If issue_id is invalid
            GraphQLError: If the GraphQL query fails
        """
        query = """
        query GetTestRun($issueId: String!) {
            getTestRun(issueId: $issueId) {
                issueId
                projectId
                summary
                description
                status {
                    name
                    color
                }
                executedBy {
                    displayName
                    emailAddress
                }
                startedOn
                finishedOn
                defects {
                    issueId
                    summary
                    status {
                        name
                    }
                }
                evidence {
                    filename
                    url
                    mimeType
                }
                comment
                created
                updated
            }
        }
        """
        
        variables = {"issueId": issue_id}
        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getTestRun", {})
    
    async def get_test_runs(
        self, 
        jql: Optional[str] = None, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Retrieve multiple test runs with optional JQL filtering.
        
        Searches for test runs matching the specified criteria. Supports
        pagination and JQL-based filtering for precise result sets.
        
        Args:
            jql: Optional JQL query to filter test runs
            limit: Maximum number of test runs to return (max 100)
        
        Returns:
            Dict containing:
                - total: Total number of matching test runs
                - start: Starting index of results
                - limit: Number of results requested
                - results: List of test run objects
        
        Raises:
            ValidationError: If JQL is invalid or limit exceeds 100
            GraphQLError: If the GraphQL query fails
        """
        if limit > 100:
            raise ValidationError("Limit cannot exceed 100")
        
        if jql:
            validate_jql(jql)
        
        query = """
        query GetTestRuns($jql: String, $limit: Int!) {
            getTestRuns(jql: $jql, limit: $limit) {
                total
                start
                limit
                results {
                    issueId
                    projectId
                    summary
                    status {
                        name
                        color
                    }
                    executedBy {
                        displayName
                    }
                    startedOn
                    finishedOn
                    created
                    updated
                }
            }
        }
        """
        
        variables = {
            "jql": jql,
            "limit": limit
        }
        
        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getTestRuns", {})
    
    async def create_test_run(
        self,
        test_execution_id: str,
        results_input: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create test runs with results in a test execution.
        
        Creates test run instances within a test execution and records their
        execution results. This is the primary way to record test outcomes.
        
        Args:
            test_execution_id: The Jira issue ID of the test execution
            results_input: List of test result objects containing:
                - testIssueId: ID of the test being executed
                - status: Execution status (PASS, FAIL, TODO, etc.)
                - comment: Optional execution comment
                - defects: Optional list of defect issue IDs
                - evidence: Optional list of evidence attachments
                - executedBy: Optional user who executed the test
                - startedOn: Optional execution start time
                - finishedOn: Optional execution end time
        
        Returns:
            Dict containing:
                - testRuns: List of created test run objects
                - warnings: Any warnings from the operation
        
        Raises:
            ValidationError: If required fields are missing or invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation CreateTestRuns($testExecutionId: String!, $resultsInput: [TestResultInput!]!) {
            createTestRun(testExecutionId: $testExecutionId, results: $resultsInput) {
                testRuns {
                    issueId
                    testIssueId
                    status {
                        name
                    }
                    executedBy {
                        displayName
                    }
                    startedOn
                    finishedOn
                    comment
                }
                warnings
            }
        }
        """
        
        variables = {
            "testExecutionId": test_execution_id,
            "resultsInput": results_input
        }
        
        result = await self.client.execute_query(mutation, variables)
        return result.get("data", {}).get("createTestRun", {})
    
    async def update_test_run(
        self, 
        issue_id: str, 
        results_input: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Update existing test runs with new results.
        
        Updates test run execution results, status, comments, defects, and evidence.
        This method can update multiple test runs within a test execution.
        
        Args:
            issue_id: The Jira issue ID of the test execution containing the runs
            results_input: List of test result updates containing:
                - testRunId: ID of the test run to update
                - status: New execution status
                - comment: Updated execution comment
                - defects: Updated list of defect issue IDs
                - evidence: Updated list of evidence attachments
                - executedBy: User who executed the test
                - startedOn: Execution start time
                - finishedOn: Execution end time
        
        Returns:
            Dict containing:
                - updatedTestRuns: List of updated test run objects
                - success: Boolean indicating operation success
        
        Raises:
            ValidationError: If issue_id is invalid or results_input is malformed
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation UpdateTestRuns($issueId: String!, $resultsInput: [TestResultUpdateInput!]!) {
            updateTestRun(testExecutionId: $issueId, results: $resultsInput) {
                updatedTestRuns {
                    issueId
                    testIssueId
                    status {
                        name
                    }
                    executedBy {
                        displayName
                    }
                    startedOn
                    finishedOn
                    comment
                    updated
                }
            }
        }
        """
        
        variables = {
            "issueId": issue_id,
            "resultsInput": results_input
        }
        
        result = await self.client.execute_query(mutation, variables)
        return result.get("data", {}).get("updateTestRun", {})
    
    async def delete_test_run(self, issue_id: str) -> Dict[str, Any]:
        """Delete a test run from Xray.
        
        Removes the test run issue from Jira. This operation also removes
        all associated execution results, evidence, and defect links.
        
        Args:
            issue_id: The Jira issue ID of the test run to delete
        
        Returns:
            Dict containing:
                - success: Boolean indicating successful deletion
                - deletedTestRunId: ID of the deleted test run
        
        Raises:
            ValidationError: If issue_id is invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation DeleteTestRun($issueId: String!) {
            deleteTestRun(issueId: $issueId) {
                success
            }
        }
        """
        
        variables = {"issueId": issue_id}
        result = await self.client.execute_query(mutation, variables)
        
        return {
            "success": result.get("data", {}).get("deleteTestRun", {}).get("success", False),
            "deletedTestRunId": issue_id
        }

