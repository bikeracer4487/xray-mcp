"""Test execution management tools for Xray MCP server.

This module provides functionality for managing test executions in Xray,
including creating, retrieving, updating, and deleting test executions.
It also handles the association of tests and test environments with executions.

The TestExecutionTools class serves as the main interface for interacting
with Xray's test execution API through GraphQL queries and mutations.
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


class TestExecutionTools:
    """Tools for managing test executions in Xray.
    
    This class provides methods to interact with test executions, which are
    containers that group test runs for a specific test cycle or release.
    Test executions track the execution status of multiple tests and can be
    associated with test environments.
    
    Attributes:
        client (XrayGraphQLClient): GraphQL client for Xray API communication
    
    Example:
        >>> from client import XrayGraphQLClient
        >>> client = XrayGraphQLClient(auth_manager, base_url)
        >>> exec_tools = TestExecutionTools(client)
        >>> execution = await exec_tools.get_test_execution("PROJ-123")
    """
    
    def __init__(self, graphql_client: XrayGraphQLClient):
        """Initialize TestExecutionTools with a GraphQL client.
        
        Args:
            graphql_client (XrayGraphQLClient): Initialized GraphQL client
                for communicating with the Xray API
        """
        self.client = graphql_client
    
    async def get_test_execution(self, issue_id: str) -> Dict[str, Any]:
        """Retrieve a single test execution by issue ID.
        
        Fetches detailed information about a test execution including its
        associated tests, test types, and Jira fields.
        
        Args:
            issue_id (str): The Jira issue ID of the test execution
                (e.g., "PROJ-123")
        
        Returns:
            Dict[str, Any]: Test execution data containing:
                - issueId: The execution's issue ID
                - tests: Paginated list of associated tests with their types
                - jira: Jira fields (key, summary, assignee, reporter, status, priority)
        
        Raises:
            GraphQLError: If the test execution cannot be retrieved
        
        Example:
            >>> execution = await exec_tools.get_test_execution("PROJ-123")
            >>> print(f"Execution: {execution['jira']['key']}")
            >>> print(f"Total tests: {execution['tests']['total']}")
        """
        query = """
        query GetTestExecution($issueId: String!) {
            getTestExecution(issueId: $issueId) {
                issueId
                tests(limit: 100) {
                    total
                    start
                    limit
                    results {
                        issueId
                        testType {
                            name
                        }
                    }
                }
                jira(fields: ["key", "summary", "assignee", "reporter", "status", "priority"])
            }
        }
        """
        
        variables = {"issueId": issue_id}
        result = await self.client.execute_query(query, variables)
        
        if "data" in result and "getTestExecution" in result["data"]:
            return result["data"]["getTestExecution"]
        else:
            raise GraphQLError(f"Failed to retrieve test execution {issue_id}")
    
    async def get_test_executions(self, jql: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Retrieve multiple test executions with optional JQL filtering.
        
        Fetches a paginated list of test executions, optionally filtered by
        a JQL (Jira Query Language) query. Each execution includes a preview
        of its associated tests.
        
        Args:
            jql (Optional[str]): JQL query to filter test executions.
                If None, returns all test executions. The query is validated
                to prevent injection attacks.
            limit (int): Maximum number of test executions to return.
                Must be between 1 and 100 (default: 100).
        
        Returns:
            Dict[str, Any]: Paginated results containing:
                - total: Total number of test executions matching the query
                - start: Starting index of results
                - limit: Number of results returned
                - results: List of test execution objects with:
                    - issueId: The execution's issue ID
                    - tests: Preview of associated tests (up to 10)
                    - jira: Basic Jira fields (key, summary, assignee, status)
        
        Raises:
            ValidationError: If limit exceeds 100 or JQL is invalid
            GraphQLError: If test executions cannot be retrieved
        
        Example:
            >>> # Get all test executions for a specific version
            >>> executions = await exec_tools.get_test_executions(
            ...     jql='project = "PROJ" AND fixVersion = "1.0"',
            ...     limit=50
            ... )
            >>> print(f"Found {executions['total']} test executions")
        
        Note:
            The JQL query is validated using the validate_jql function to
            prevent SQL injection attacks.
        """
        # Validate limit to stay within API constraints
        if limit > 100:
            raise ValidationError("Limit cannot exceed 100 due to Xray API restrictions")
        
        # Validate JQL if provided to prevent injection attacks
        if jql:
            jql = validate_jql(jql)
        
        query = """
        query GetTestExecutions($jql: String, $limit: Int!) {
            getTestExecutions(jql: $jql, limit: $limit) {
                total
                start
                limit
                results {
                    issueId
                    tests(limit: 10) {
                        total
                        start
                        limit
                        results {
                            issueId
                            testType {
                                name
                            }
                        }
                    }
                    jira(fields: ["key", "summary", "assignee", "status"])
                }
            }
        }
        """
        
        variables = {"jql": jql, "limit": limit}
        result = await self.client.execute_query(query, variables)
        
        if "data" in result and "getTestExecutions" in result["data"]:
            return result["data"]["getTestExecutions"]
        else:
            raise GraphQLError("Failed to retrieve test executions")
    
    async def create_test_execution(
        self,
        project_key: str,
        summary: str,
        test_issue_ids: Optional[List[str]] = None,
        test_environments: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new test execution.
        
        Creates a test execution in Jira/Xray with the specified tests and
        environments. Test executions are used to group and track the execution
        of multiple tests for a specific test cycle, sprint, or release.
        
        Args:
            project_key (str): Jira project key where the test execution
                will be created (e.g., "PROJ")
            summary (str): Summary/title for the test execution
            test_issue_ids (Optional[List[str]]): List of test issue IDs
                to include in the execution. Can be added later if not provided.
            test_environments (Optional[List[str]]): List of test environment
                names to associate with the execution (e.g., ["Chrome", "Firefox"])
            description (Optional[str]): Detailed description of the test
                execution purpose or scope
        
        Returns:
            Dict[str, Any]: Created test execution data containing:
                - testExecution: Object with:
                    - issueId: The created execution's issue ID
                    - jira: Basic Jira fields (key, summary)
                - warnings: Any warnings from the creation process
                - createdTestEnvironments: List of newly created environments
        
        Raises:
            GraphQLError: If the test execution cannot be created
        
        Example:
            >>> # Create execution for regression testing
            >>> execution = await exec_tools.create_test_execution(
            ...     project_key="PROJ",
            ...     summary="Sprint 10 - Regression Test Execution",
            ...     test_issue_ids=["PROJ-101", "PROJ-102", "PROJ-103"],
            ...     test_environments=["Chrome", "Firefox"],
            ...     description="Regression testing for Sprint 10 features"
            ... )
            >>> print(f"Created: {execution['testExecution']['jira']['key']}")
        
        Note:
            Test environments will be automatically created if they don't
            already exist in the project.
        """
        # Build the jira fields for the test execution issue
        jira_fields = {
            "summary": summary,
            "project": {"key": project_key}
        }
        
        # Add optional description if provided
        if description:
            jira_fields["description"] = description
        
        mutation = """
        mutation CreateTestExecution($testIssueIds: [String!], $testEnvironments: [String!], $jira: JSON!) {
            createTestExecution(testIssueIds: $testIssueIds, testEnvironments: $testEnvironments, jira: $jira) {
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
            "testIssueIds": test_issue_ids or [],
            "testEnvironments": test_environments or [],
            "jira": {"fields": jira_fields}
        }
        
        result = await self.client.execute_mutation(mutation, variables)
        
        if "data" in result and "createTestExecution" in result["data"]:
            return result["data"]["createTestExecution"]
        else:
            raise GraphQLError("Failed to create test execution")
    
    async def delete_test_execution(self, issue_id: str) -> Dict[str, Any]:
        """Delete a test execution.
        
        Permanently deletes a test execution from Jira/Xray. This action
        cannot be undone and will remove all execution history for the
        associated tests.
        
        Args:
            issue_id (str): The Jira issue ID of the test execution
                to delete (e.g., "PROJ-123")
        
        Returns:
            Dict[str, Any]: Deletion result containing:
                - success: Boolean indicating if deletion was successful
                - issueId: The deleted execution's issue ID
        
        Raises:
            GraphQLError: If the test execution cannot be deleted
        
        Example:
            >>> result = await exec_tools.delete_test_execution("PROJ-123")
            >>> if result['success']:
            ...     print(f"Deleted execution: {result['issueId']}")
        
        Warning:
            This operation is irreversible. All test run data associated
            with this execution will be permanently lost.
        """
        mutation = """
        mutation DeleteTestExecution($issueId: String!) {
            deleteTestExecution(issueId: $issueId)
        }
        """
        
        variables = {"issueId": issue_id}
        result = await self.client.execute_mutation(mutation, variables)
        
        if "data" in result and "deleteTestExecution" in result["data"]:
            return {"success": result["data"]["deleteTestExecution"], "issueId": issue_id}
        else:
            raise GraphQLError(f"Failed to delete test execution {issue_id}")
    
    async def add_tests_to_execution(self, execution_issue_id: str, test_issue_ids: List[str]) -> Dict[str, Any]:
        """Add tests to a test execution.
        
        Adds one or more tests to an existing test execution. This is useful
        for incrementally building test executions or adding tests that were
        created after the execution.
        
        Args:
            execution_issue_id (str): The Jira issue ID of the test execution
                (e.g., "PROJ-123")
            test_issue_ids (List[str]): List of test issue IDs to add
                (e.g., ["PROJ-101", "PROJ-102"])
        
        Returns:
            Dict[str, Any]: Operation result containing:
                - addedTests: List of test IDs that were successfully added
                - warning: Any warnings about tests that couldn't be added
        
        Raises:
            GraphQLError: If tests cannot be added to the execution
        
        Example:
            >>> # Add new tests to existing execution
            >>> result = await exec_tools.add_tests_to_execution(
            ...     "PROJ-200",
            ...     ["PROJ-104", "PROJ-105"]
            ... )
            >>> print(f"Added {len(result['addedTests'])} tests")
        
        Note:
            Tests that are already in the execution will be skipped.
            The warning field will contain information about any tests
            that couldn't be added (e.g., invalid IDs, already present).
        """
        mutation = """
        mutation AddTestsToTestExecution($issueId: String!, $testIssueIds: [String!]!) {
            addTestsToTestExecution(issueId: $issueId, testIssueIds: $testIssueIds) {
                addedTests
                warning
            }
        }
        """
        
        variables = {
            "issueId": execution_issue_id,
            "testIssueIds": test_issue_ids
        }
        
        result = await self.client.execute_mutation(mutation, variables)
        
        if "data" in result and "addTestsToTestExecution" in result["data"]:
            return result["data"]["addTestsToTestExecution"]
        else:
            raise GraphQLError(f"Failed to add tests to execution {execution_issue_id}")
    
    async def remove_tests_from_execution(self, execution_issue_id: str, test_issue_ids: List[str]) -> Dict[str, Any]:
        """Remove tests from a test execution.
        
        Removes one or more tests from an existing test execution. This is
        useful for refining the scope of a test execution or removing tests
        that are no longer relevant.
        
        Args:
            execution_issue_id (str): The Jira issue ID of the test execution
                (e.g., "PROJ-123")
            test_issue_ids (List[str]): List of test issue IDs to remove
                (e.g., ["PROJ-101", "PROJ-102"])
        
        Returns:
            Dict[str, Any]: Operation result containing:
                - success: Boolean indicating if removal was successful
                - executionId: The execution's issue ID
        
        Raises:
            GraphQLError: If tests cannot be removed from the execution
        
        Example:
            >>> # Remove obsolete tests from execution
            >>> result = await exec_tools.remove_tests_from_execution(
            ...     "PROJ-200",
            ...     ["PROJ-101", "PROJ-102"]
            ... )
            >>> if result['success']:
            ...     print(f"Removed tests from {result['executionId']}")
        
        Note:
            Removing tests from an execution will delete their execution
            history within this specific execution. The tests themselves
            are not deleted.
        """
        mutation = """
        mutation RemoveTestsFromTestExecution($issueId: String!, $testIssueIds: [String!]!) {
            removeTestsFromTestExecution(issueId: $issueId, testIssueIds: $testIssueIds)
        }
        """
        
        variables = {
            "issueId": execution_issue_id,
            "testIssueIds": test_issue_ids
        }
        
        result = await self.client.execute_mutation(mutation, variables)
        
        if "data" in result and "removeTestsFromTestExecution" in result["data"]:
            return {"success": result["data"]["removeTestsFromTestExecution"], "executionId": execution_issue_id}
        else:
            raise GraphQLError(f"Failed to remove tests from execution {execution_issue_id}")
    
    async def add_test_environments(self, execution_issue_id: str, test_environments: List[str]) -> Dict[str, Any]:
        """Add test environments to a test execution.
        
        Associates one or more test environments with a test execution.
        Test environments help track where tests were executed (e.g.,
        different browsers, operating systems, or deployment environments).
        
        Args:
            execution_issue_id (str): The Jira issue ID of the test execution
                (e.g., "PROJ-123")
            test_environments (List[str]): List of environment names to add
                (e.g., ["Chrome", "Firefox", "Safari"])
        
        Returns:
            Dict[str, Any]: Operation result containing:
                - associatedTestEnvironments: List of all environments now
                  associated with the execution
                - createdTestEnvironments: List of environments that were
                  newly created during this operation
        
        Raises:
            GraphQLError: If environments cannot be added to the execution
        
        Example:
            >>> # Add browser environments to execution
            >>> result = await exec_tools.add_test_environments(
            ...     "PROJ-200",
            ...     ["Chrome 96", "Firefox 95", "Safari 15"]
            ... )
            >>> print(f"Total environments: {len(result['associatedTestEnvironments'])}")
            >>> if result['createdTestEnvironments']:
            ...     print(f"Created new: {result['createdTestEnvironments']}")
        
        Note:
            - Test environments are project-scoped and will be created
              automatically if they don't already exist
            - Environment names are case-sensitive
            - Environments help in filtering and reporting test results
        """
        mutation = """
        mutation AddTestEnvironmentsToTestExecution($issueId: String!, $testEnvironments: [String!]!) {
            addTestEnvironmentsToTestExecution(issueId: $issueId, testEnvironments: $testEnvironments) {
                associatedTestEnvironments
                createdTestEnvironments
            }
        }
        """
        
        variables = {
            "issueId": execution_issue_id,
            "testEnvironments": test_environments
        }
        
        result = await self.client.execute_mutation(mutation, variables)
        
        if "data" in result and "addTestEnvironmentsToTestExecution" in result["data"]:
            return result["data"]["addTestEnvironmentsToTestExecution"]
        else:
            raise GraphQLError(f"Failed to add test environments to execution {execution_issue_id}")
    
    async def remove_test_environments(self, execution_issue_id: str, test_environments: List[str]) -> Dict[str, Any]:
        """Remove test environments from a test execution.
        
        Disassociates one or more test environments from a test execution.
        This doesn't delete the environments themselves, only removes their
        association with this specific execution.
        
        Args:
            execution_issue_id (str): The Jira issue ID of the test execution
                (e.g., "PROJ-123")
            test_environments (List[str]): List of environment names to remove
                (e.g., ["Chrome", "Firefox"])
        
        Returns:
            Dict[str, Any]: Operation result containing:
                - success: Boolean indicating if removal was successful
                - executionId: The execution's issue ID
        
        Raises:
            GraphQLError: If environments cannot be removed from the execution
        
        Example:
            >>> # Remove deprecated browser environments
            >>> result = await exec_tools.remove_test_environments(
            ...     "PROJ-200",
            ...     ["IE 11", "Chrome 80"]
            ... )
            >>> if result['success']:
            ...     print(f"Removed environments from {result['executionId']}")
        
        Note:
            - Only removes the association; environments remain available
              for use in other executions
            - Environment names must match exactly (case-sensitive)
            - Useful for correcting environment assignments or cleaning up
              after testing scope changes
        """
        mutation = """
        mutation RemoveTestEnvironmentsFromTestExecution($issueId: String!, $testEnvironments: [String!]!) {
            removeTestEnvironmentsFromTestExecution(issueId: $issueId, testEnvironments: $testEnvironments)
        }
        """
        
        variables = {
            "issueId": execution_issue_id,
            "testEnvironments": test_environments
        }
        
        result = await self.client.execute_mutation(mutation, variables)
        
        if "data" in result and "removeTestEnvironmentsFromTestExecution" in result["data"]:
            return {"success": result["data"]["removeTestEnvironmentsFromTestExecution"], "executionId": execution_issue_id}
        else:
            raise GraphQLError(f"Failed to remove test environments from execution {execution_issue_id}")

