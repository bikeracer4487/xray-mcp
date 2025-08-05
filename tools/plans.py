"""Test plan management tools for Xray MCP server.

This module provides functionality for managing test plans in Xray,
including creating, retrieving, updating, and deleting test plans.
Test plans are used to organize and track testing activities for releases,
sprints, or specific features.

The TestPlanTools class serves as the main interface for interacting
with Xray's test plan API through GraphQL queries and mutations.
"""

from typing import Dict, Any, List, Optional

try:
    from ..client import XrayGraphQLClient
    from ..exceptions import GraphQLError, ValidationError
    from ..validators import validate_jql
    from ..utils import IssueIdResolver
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError
    from validators import validate_jql
    from utils import IssueIdResolver


class TestPlanTools:
    """Tools for managing test plans in Xray.

    This class provides methods to interact with test plans, which are containers
    that group tests for planning and tracking purposes. Test plans help organize
    testing activities by release, sprint, feature, or any other logical grouping.

    Attributes:
        client (XrayGraphQLClient): GraphQL client for API communication

    Dependencies:
        - Requires authenticated XrayGraphQLClient instance
        - Depends on Xray GraphQL API for test plan operations

    Note:
        All methods return structured dictionaries compatible with MCP responses.
        Errors are propagated to calling code for centralized error handling.
    """

    def __init__(self, graphql_client: XrayGraphQLClient):
        """Initialize test plan tools with GraphQL client.

        Args:
            graphql_client (XrayGraphQLClient): Authenticated GraphQL client instance
        """
        self.client = graphql_client
        self.id_resolver = IssueIdResolver(graphql_client)

    async def get_test_plan(self, issue_id: str) -> Dict[str, Any]:
        """Retrieve a single test plan by issue ID.

        Fetches detailed information about a specific test plan including
        its associated tests, metadata, and current status.

        Args:
            issue_id: The Jira issue ID of the test plan

        Returns:
            Dict containing:
                - issueId: Test plan issue ID
                - projectId: Project ID
                - summary: Test plan title
                - description: Test plan description
                - tests: Associated tests
                - status: Current status
                - created: Creation timestamp
                - updated: Last update timestamp

        Raises:
            ValidationError: If issue_id is invalid
            GraphQLError: If the GraphQL query fails
        """
        query = """
        query GetTestPlan($issueId: String!) {
            getTestPlan(issueId: $issueId) {
                issueId
                projectId
                jira(fields: ["key", "summary", "description", "status", "priority", "labels", "created", "updated"]) {
                    key
                    fields
                }
                tests(limit: 100) {
                    total
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

        # Resolve Jira key to internal ID if necessary
        resolved_id = await self.id_resolver.resolve_issue_id(issue_id)
        variables = {"issueId": resolved_id}
        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getTestPlan", {})

    async def get_test_plans(
        self, jql: Optional[str] = None, limit: int = 100
    ) -> Dict[str, Any]:
        """Retrieve multiple test plans with optional JQL filtering.

        Searches for test plans matching the specified criteria. Supports
        pagination and JQL-based filtering for precise result sets.

        Args:
            jql: Optional JQL query to filter test plans
            limit: Maximum number of test plans to return (max 100)

        Returns:
            Dict containing:
                - total: Total number of matching test plans
                - start: Starting index of results
                - limit: Number of results requested
                - results: List of test plan objects

        Raises:
            ValidationError: If JQL is invalid or limit exceeds 100
            GraphQLError: If the GraphQL query fails
        """
        if limit > 100:
            raise ValidationError("Limit cannot exceed 100")

        if jql:
            validate_jql(jql)

        query = """
        query GetTestPlans($jql: String, $limit: Int!) {
            getTestPlans(jql: $jql, limit: $limit) {
                total
                start
                limit
                results {
                    issueId
                    projectId
                    jira(fields: ["key", "summary", "description", "status", "priority", "labels", "created", "updated"]) {
                        key
                        fields
                    }
                }
            }
        }
        """

        variables = {"jql": jql, "limit": limit}

        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getTestPlans", {})

    async def create_test_plan(
        self,
        project_key: str,
        summary: str,
        test_issue_ids: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new test plan in Xray.

        Creates a test plan issue in Jira and optionally associates it with
        specified tests. Test plans help organize related tests for planning.

        Args:
            project_key: Jira project key where the test plan will be created
            summary: Test plan title/summary
            test_issue_ids: Optional list of test issue IDs to include
            description: Optional detailed description

        Returns:
            Dict containing:
                - testPlan: Created test plan object with issue ID and key
                - addedTests: List of successfully added tests
                - warnings: Any warnings from the operation

        Raises:
            ValidationError: If required fields are missing or invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation CreateTestPlan($jira: JSON!, $testIssueIds: [String]) {
            createTestPlan(jira: $jira, testIssueIds: $testIssueIds) {
                testPlan {
                    issueId
                    jira(fields: ["key", "summary"])
                }
                warnings
            }
        }
        """

        # Build Jira JSON structure as required by the GraphQL schema
        jira_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": "Test Plan"},
            }
        }

        if description:
            jira_data["fields"]["description"] = description

        variables = {"jira": jira_data, "testIssueIds": test_issue_ids or []}

        result = await self.client.execute_query(mutation, variables)
        create_result = result.get("data", {}).get("createTestPlan", {})

        # If tests were specified, add them to the created test plan
        if test_issue_ids and create_result.get("testPlan", {}).get("issueId"):
            test_plan_id = create_result["testPlan"]["issueId"]
            add_result = await self.add_tests_to_plan(test_plan_id, test_issue_ids)
            create_result["addedTests"] = add_result.get("addedTests", [])

        return create_result

    async def update_test_plan(
        self, issue_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing test plan.

        Modifies the properties of an existing test plan. Supports updating
        summary, description, and other test plan attributes.

        Args:
            issue_id: The Jira issue ID of the test plan to update
            updates: Dictionary containing fields to update:
                - summary: New summary/title
                - description: New description
                - labels: New labels

        Returns:
            Dict containing:
                - testPlan: Updated test plan object
                - success: Boolean indicating operation success

        Raises:
            ValidationError: If issue_id is invalid or updates are malformed
            GraphQLError: If the GraphQL mutation fails
        """
        # Note: This method may not be supported by all Xray instances
        # as updateTestPlan mutation is not documented in the official GraphQL schema
        raise GraphQLError(
            "updateTestPlan mutation is not available in the current GraphQL schema"
        )

        variables = {"issueId": issue_id, "updates": updates}

        result = await self.client.execute_query(mutation, variables)
        return result.get("data", {}).get("updateTestPlan", {})

    async def delete_test_plan(self, issue_id: str) -> Dict[str, Any]:
        """Delete a test plan from Xray.

        Removes the test plan issue from Jira. This operation does not affect
        the individual tests that were associated with the test plan.

        Args:
            issue_id: The Jira issue ID of the test plan to delete

        Returns:
            Dict containing:
                - success: Boolean indicating successful deletion
                - deletedTestPlanId: ID of the deleted test plan

        Raises:
            ValidationError: If issue_id is invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation DeleteTestPlan($issueId: String!) {
            deleteTestPlan(issueId: $issueId)
        }
        """

        # Resolve Jira key to internal ID if necessary
        resolved_id = await self.id_resolver.resolve_issue_id(issue_id)
        variables = {"issueId": resolved_id}
        result = await self.client.execute_query(mutation, variables)

        return {
            "success": result.get("data", {}).get("deleteTestPlan") is not None,
            "deletedTestPlanId": issue_id,
        }

    async def add_tests_to_plan(
        self, issue_id: str, test_issue_ids: List[str]
    ) -> Dict[str, Any]:
        """Add tests to an existing test plan.

        Associates specified tests with a test plan. Tests can belong to
        multiple test plans simultaneously.

        Args:
            issue_id: The Jira issue ID of the test plan
            test_issue_ids: List of test issue IDs to add to the test plan

        Returns:
            Dict containing:
                - addedTests: List of successfully added test IDs (strings)
                - warning: Any warning from the operation

        Raises:
            ValidationError: If issue_id is invalid or test_issue_ids is empty
            GraphQLError: If the GraphQL mutation fails
        """
        if not test_issue_ids:
            raise ValidationError("test_issue_ids cannot be empty")

        mutation = """
        mutation AddTestsToTestPlan($issueId: String!, $testIssueIds: [String!]!) {
            addTestsToTestPlan(issueId: $issueId, testIssueIds: $testIssueIds) {
                addedTests
                warning
            }
        }
        """

        # Resolve Jira keys to internal IDs if necessary
        resolved_plan_id = await self.id_resolver.resolve_issue_id(issue_id)
        resolved_test_ids = await self.id_resolver.resolve_multiple_issue_ids(test_issue_ids)
        variables = {"issueId": resolved_plan_id, "testIssueIds": resolved_test_ids}

        result = await self.client.execute_query(mutation, variables)
        return result.get("data", {}).get("addTestsToTestPlan", {})

    async def remove_tests_from_plan(
        self, issue_id: str, test_issue_ids: List[str]
    ) -> Dict[str, Any]:
        """Remove tests from an existing test plan.

        Disassociates specified tests from a test plan. The tests themselves
        are not deleted, only their association with the test plan.

        Args:
            issue_id: The Jira issue ID of the test plan
            test_issue_ids: List of test issue IDs to remove from the test plan

        Returns:
            Dict containing:
                - success: Boolean indicating operation success (always True if no exception)

        Raises:
            ValidationError: If issue_id is invalid or test_issue_ids is empty
            GraphQLError: If the GraphQL mutation fails
        """
        if not test_issue_ids:
            raise ValidationError("test_issue_ids cannot be empty")

        mutation = """
        mutation RemoveTestsFromTestPlan($issueId: String!, $testIssueIds: [String!]!) {
            removeTestsFromTestPlan(issueId: $issueId, testIssueIds: $testIssueIds)
        }
        """

        # Resolve Jira keys to internal IDs if necessary
        resolved_plan_id = await self.id_resolver.resolve_issue_id(issue_id)
        resolved_test_ids = await self.id_resolver.resolve_multiple_issue_ids(test_issue_ids)
        variables = {"issueId": resolved_plan_id, "testIssueIds": resolved_test_ids}

        result = await self.client.execute_query(mutation, variables)
        # removeTestsFromTestPlan returns null on success
        return {
            "success": result.get("data", {}).get("removeTestsFromTestPlan") is not None
            or "errors" not in result,
            "removedTestIds": test_issue_ids,
        }
