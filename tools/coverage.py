"""Status and coverage query tools for Xray MCP server.

This module provides functionality for querying test status and coverage
information in Xray, including test execution status, coverage metrics,
and coverable issues analysis.

The CoverageTools class serves as the main interface for interacting
with Xray's status and coverage API through GraphQL queries.
"""

from typing import Dict, Any, List, Optional

try:
    from ..client import XrayGraphQLClient
    from ..exceptions import GraphQLError, ValidationError
    from ..validators import validate_jql
    from ..utils.id_resolver import IssueIdResolver
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError
    from validators import validate_jql
    from utils.id_resolver import IssueIdResolver


class CoverageTools:
    """Tools for querying test status and coverage in Xray.

    This class provides methods to query test execution status, coverage metrics,
    and analyze coverable issues. These tools help understand test coverage
    and execution status across projects and releases.

    Attributes:
        client (XrayGraphQLClient): GraphQL client for API communication

    Dependencies:
        - Requires authenticated XrayGraphQLClient instance
        - Depends on Xray GraphQL API for status and coverage queries

    Note:
        All methods return structured dictionaries compatible with MCP responses.
        Errors are propagated to calling code for centralized error handling.
    """

    def __init__(self, client: XrayGraphQLClient):
        """Initialize coverage tools with GraphQL client.

        Args:
            client (XrayGraphQLClient): Authenticated GraphQL client instance
        """
        self.client = client
        self.id_resolver = IssueIdResolver(client)

    async def get_test_status(
        self,
        issue_id: str,
        environment: Optional[str] = None,
        version: Optional[str] = None,
        test_plan: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get test execution status for a specific test.

        Retrieves the current execution status of a test, optionally filtered
        by environment, version, or test plan context.

        Args:
            issue_id: The Jira issue ID of the test
            environment: Optional test environment to filter by
            version: Optional version to filter by
            test_plan: Optional test plan issue ID to filter by

        Returns:
            Dict containing:
                - issueId: The test issue ID
                - status: Current execution status (string)
                - testType: Test type information
                - jira: Jira fields including key and summary

        Raises:
            ValidationError: If issue_id is invalid
            GraphQLError: If the GraphQL query fails
        """
        query = """
        query GetTestStatus(
            $issueId: String!,
            $environment: String,
            $version: String,
            $testPlan: String
        ) {
            getTest(issueId: $issueId) {
                issueId
                status(
                    environment: $environment,
                    version: $version,
                    testPlan: $testPlan
                ) {
                    name
                    color
                }
                testType {
                    name
                }
                jira(fields: ["key", "summary"])
            }
        }
        """

        # Resolve Jira key to internal ID if necessary
        resolved_id = await self.id_resolver.resolve_issue_id(issue_id)
        resolved_test_plan = None
        if test_plan:
            resolved_test_plan = await self.id_resolver.resolve_issue_id(test_plan)

        variables = {
            "issueId": resolved_id,
            "environment": environment,
            "version": version,
            "testPlan": resolved_test_plan,
        }

        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getTest", {})

    async def get_coverable_issues(
        self, jql: Optional[str] = None, limit: int = 100
    ) -> Dict[str, Any]:
        """Retrieve issues that can be covered by tests.

        Finds Jira issues (stories, bugs, requirements) that can be linked
        to tests for coverage tracking. Supports JQL filtering for precise
        issue selection.

        Args:
            jql: Optional JQL query to filter coverable issues
            limit: Maximum number of issues to return (max 100)

        Returns:
            Dict containing:
                - total: Total number of matching coverable issues
                - start: Starting index of results
                - limit: Number of results requested
                - results: List of coverable issue objects with:
                    - issueId: Issue ID
                    - jira: Jira fields including key, summary, issuetype, priority, assignee, reporter, status

        Raises:
            ValidationError: If JQL is invalid or limit exceeds 100
            GraphQLError: If the GraphQL query fails
        """
        if limit > 100:
            raise ValidationError("Limit cannot exceed 100")

        if jql:
            validate_jql(jql)

        query = """
        query GetCoverableIssues($jql: String, $limit: Int!) {
            getCoverableIssues(jql: $jql, limit: $limit) {
                total
                start
                limit
                results {
                    issueId
                    jira(fields: ["key", "summary", "issuetype", "priority", "assignee", "reporter", "status"])
                }
            }
        }
        """

        variables = {"jql": jql, "limit": limit}

        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getCoverableIssues", {})
