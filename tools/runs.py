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

        Note: This method uses getTestRunById which requires the internal test run ID,
        not a Jira issue ID. Test runs don't have Jira issues - they exist within
        test executions.

        Args:
            issue_id: The internal test run ID (not a Jira issue ID)

        Returns:
            Dict containing:
                - id: Test run internal ID
                - status: Current execution status
                - gherkin: Gherkin definition for Cucumber tests
                - examples: Test examples for data-driven tests
                - steps: Test run steps with status and results
                - test: Associated test information
                - testExecution: Associated test execution

        Raises:
            ValidationError: If issue_id is invalid
            GraphQLError: If the GraphQL query fails
        """
        query = """
        query GetTestRunById($id: String!) {
            getTestRunById(id: $id) {
                id
                status {
                    name
                    color
                    description
                }
                gherkin
                scenarioType
                comment
                startedOn
                finishedOn
                executedById
                assigneeId
                evidence
                defects
                unstructured
                testType {
                    name
                    kind
                }
                steps {
                    id
                    action
                    data
                    result
                    status {
                        name
                        color
                    }
                    comment
                    actualResult
                    evidence {
                        id
                        filename
                    }
                    defects
                }
                examples {
                    id
                    status {
                        name
                        color
                        description
                    }
                }
                test {
                    issueId
                }
                testExecution {
                    issueId
                }
            }
        }
        """

        variables = {"id": issue_id}
        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getTestRunById", {})

    async def get_test_runs(
        self,
        test_issue_ids: Optional[List[str]] = None,
        test_exec_issue_ids: Optional[List[str]] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Retrieve multiple test runs by test and execution IDs.

        Note: Test runs are retrieved by specifying test issue IDs and test execution
        issue IDs, not by JQL. This matches the actual GraphQL schema.

        Args:
            test_issue_ids: Optional list of test issue IDs to filter by
            test_exec_issue_ids: Optional list of test execution issue IDs to filter by
            limit: Maximum number of test runs to return (max 100)

        Returns:
            Dict containing:
                - total: Total number of matching test runs
                - start: Starting index of results
                - limit: Number of results requested
                - results: List of test run objects with internal IDs and status

        Raises:
            ValidationError: If limit exceeds 100
            GraphQLError: If the GraphQL query fails
        """
        if limit > 100:
            raise ValidationError("Limit cannot exceed 100")

        query = """
        query GetTestRuns($testIssueIds: [String], $testExecIssueIds: [String], $limit: Int!) {
            getTestRuns(testIssueIds: $testIssueIds, testExecIssueIds: $testExecIssueIds, limit: $limit) {
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
                    gherkin
                    scenarioType
                    comment
                    startedOn
                    finishedOn
                    executedById
                    assigneeId
                    examples {
                        id
                        status {
                            name
                            color
                            description
                        }
                    }
                    test {
                        issueId
                    }
                    testExecution {
                        issueId
                    }
                }
            }
        }
        """

        variables = {
            "testIssueIds": test_issue_ids,
            "testExecIssueIds": test_exec_issue_ids,
            "limit": limit,
        }

        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getTestRuns", {})

    async def update_test_run_status(
        self, test_run_id: str, status: str
    ) -> Dict[str, Any]:
        """Update the status of a test run.

        Updates the execution status of a test run. Test runs are not created
        directly - they exist within test executions. This method updates an
        existing test run's status.

        Args:
            test_run_id: The internal ID of the test run (not a Jira issue ID)
            status: New execution status (PASSED, FAILED, EXECUTING, TODO, etc.)

        Returns:
            Dict containing:
                - success: Boolean indicating operation success
                - warnings: Any warnings from the operation

        Raises:
            ValidationError: If required fields are missing or invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation UpdateTestRunStatus($id: String!, $status: String!) {
            updateTestRunStatus(id: $id, status: $status)
        }
        """

        variables = {"id": test_run_id, "status": status}

        result = await self.client.execute_query(mutation, variables)
        # updateTestRunStatus returns null on success
        return {
            "success": "errors" not in result,
            "testRunId": test_run_id,
            "status": status,
        }

    async def update_test_run(
        self,
        test_run_id: str,
        comment: Optional[str] = None,
        started_on: Optional[str] = None,
        finished_on: Optional[str] = None,
        assignee_id: Optional[str] = None,
        executed_by_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a test run with multiple fields.

        Updates various fields of a test run including comment, timing, and assignment.
        Uses the updateTestRun mutation which accepts individual field parameters.

        Args:
            test_run_id: The internal ID of the test run to update
            comment: Optional execution comment
            started_on: Optional execution start time (ISO format)
            finished_on: Optional execution end time (ISO format)
            assignee_id: Optional user ID for assignment
            executed_by_id: Optional user ID who executed the test

        Returns:
            Dict containing:
                - warnings: Any warnings from the operation
                - success: Boolean indicating operation success

        Raises:
            ValidationError: If test_run_id is invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation UpdateTestRun(
            $id: String!,
            $comment: String,
            $startedOn: String,
            $finishedOn: String,
            $assigneeId: String,
            $executedById: String
        ) {
            updateTestRun(
                id: $id,
                comment: $comment,
                startedOn: $startedOn,
                finishedOn: $finishedOn,
                assigneeId: $assigneeId,
                executedById: $executedById
            ) {
                warnings
            }
        }
        """

        variables = {
            "id": test_run_id,
            "comment": comment,
            "startedOn": started_on,
            "finishedOn": finished_on,
            "assigneeId": assignee_id,
            "executedById": executed_by_id,
        }

        result = await self.client.execute_query(mutation, variables)
        update_result = result.get("data", {}).get("updateTestRun", {})
        return {
            "warnings": update_result.get("warnings", []),
            "success": "errors" not in result,
            "testRunId": test_run_id,
        }

    async def reset_test_run(self, test_run_id: str) -> Dict[str, Any]:
        """Reset a test run to its initial state.

        Resets a test run, clearing its execution status and results.
        This is the closest equivalent to "deleting" a test run since
        test runs cannot be deleted independently from their test execution.

        Args:
            test_run_id: The internal ID of the test run to reset

        Returns:
            Dict containing:
                - success: Boolean indicating successful reset
                - resetTestRunId: ID of the reset test run

        Raises:
            ValidationError: If test_run_id is invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation ResetTestRun($id: String!) {
            resetTestRun(id: $id)
        }
        """

        variables = {"id": test_run_id}
        result = await self.client.execute_query(mutation, variables)

        # resetTestRun returns null on success
        return {"success": "errors" not in result, "resetTestRunId": test_run_id}
