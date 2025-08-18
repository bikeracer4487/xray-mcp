"""Test set management tools for Xray MCP server.

This module provides functionality for managing test sets in Xray,
including creating, retrieving, updating, and deleting test sets.
Test sets are collections of tests organized for specific testing purposes.

The TestSetTools class serves as the main interface for interacting
with Xray's test set API through GraphQL queries and mutations.
"""

from typing import Dict, Any, List, Optional

try:
    from ..client import XrayGraphQLClient
    from ..exceptions import GraphQLError, ValidationError
    from ..validators import validate_jql
    from ..utils import IssueIdResolver
    from ..utils.id_resolver import ResourceType
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError
    from validators import validate_jql
    from utils import IssueIdResolver
    from utils.id_resolver import ResourceType


class TestSetTools:
    """Tools for managing test sets in Xray.

    This class provides methods to interact with test sets, which are collections
    of tests that can be organized for specific testing scenarios, releases, or
    functional areas. Test sets help organize and group related tests.

    Attributes:
        client (XrayGraphQLClient): GraphQL client for API communication

    Dependencies:
        - Requires authenticated XrayGraphQLClient instance
        - Depends on Xray GraphQL API for test set operations

    Note:
        All methods return structured dictionaries compatible with MCP responses.
        Errors are propagated to calling code for centralized error handling.
    """

    def __init__(self, client: XrayGraphQLClient):
        """Initialize test set tools with GraphQL client.

        Args:
            client (XrayGraphQLClient): Authenticated GraphQL client instance
        """
        self.client = client
        self.id_resolver = IssueIdResolver(client)

    async def get_test_set(self, issue_id: str) -> Dict[str, Any]:
        """Retrieve a single test set by issue ID.

        Fetches detailed information about a specific test set including
        its associated tests, metadata, and current status.

        Args:
            issue_id: The Jira issue ID of the test set

        Returns:
            Dict containing:
                - issueId: Test set issue ID
                - projectId: Project ID
                - summary: Test set title
                - description: Test set description
                - tests: Associated tests
                - status: Current status
                - created: Creation timestamp
                - updated: Last update timestamp

        Raises:
            ValidationError: If issue_id is invalid
            GraphQLError: If the GraphQL query fails
        """
        query = """
        query GetTestSet($issueId: String!) {
            getTestSet(issueId: $issueId) {
                issueId
                projectId
                jira(fields: ["key", "summary", "description", "status", "priority", "labels", "created", "updated"])
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
        resolved_id = await self.id_resolver.resolve_issue_id(issue_id, ResourceType.TEST_SET)

        variables = {"issueId": resolved_id}
        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getTestSet", {})

    async def get_test_sets(
        self, jql: Optional[str] = None, limit: int = 100
    ) -> Dict[str, Any]:
        """Retrieve multiple test sets with optional JQL filtering.

        Searches for test sets matching the specified criteria. Supports
        pagination and JQL-based filtering for precise result sets.

        Args:
            jql: Optional JQL query to filter test sets
            limit: Maximum number of test sets to return (max 100)

        Returns:
            Dict containing:
                - total: Total number of matching test sets
                - start: Starting index of results
                - limit: Number of results requested
                - results: List of test set objects

        Raises:
            ValidationError: If JQL is invalid or limit exceeds 100
            GraphQLError: If the GraphQL query fails
        """
        if limit > 100:
            raise ValidationError("Limit cannot exceed 100")

        if jql:
            validate_jql(jql)

        query = """
        query GetTestSets($jql: String, $limit: Int!) {
            getTestSets(jql: $jql, limit: $limit) {
                total
                start
                limit
                results {
                    issueId
                    projectId
                    jira(fields: ["key", "summary", "description", "status", "priority", "labels", "created", "updated"])
                }
            }
        }
        """

        variables = {"jql": jql, "limit": limit}

        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getTestSets", {})

    async def create_test_set(
        self,
        project_key: str,
        summary: str,
        test_issue_ids: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new test set in Xray.

        Creates a test set issue in Jira and optionally associates it with
        specified tests. Test sets help organize related tests for execution.

        Args:
            project_key: Jira project key where the test set will be created
            summary: Test set title/summary
            test_issue_ids: Optional list of test issue IDs to include
            description: Optional detailed description

        Returns:
            Dict containing:
                - testSet: Created test set object with issue ID and key
                - addedTests: List of successfully added tests
                - warnings: Any warnings from the operation

        Raises:
            ValidationError: If required fields are missing or invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation CreateTestSet($jira: JSON!, $testIssueIds: [String]) {
            createTestSet(jira: $jira, testIssueIds: $testIssueIds) {
                testSet {
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
                "issuetype": {"name": "Test Set"},
            }
        }

        if description:
            jira_data["fields"]["description"] = description

        variables = {"jira": jira_data, "testIssueIds": test_issue_ids or []}

        result = await self.client.execute_query(mutation, variables)
        create_result = result.get("data", {}).get("createTestSet", {})

        # If tests were specified, add them to the created test set
        if test_issue_ids and create_result.get("testSet", {}).get("issueId"):
            test_set_id = create_result["testSet"]["issueId"]
            add_result = await self.add_tests_to_set(test_set_id, test_issue_ids)
            create_result["addedTests"] = add_result.get("addedTests", [])

        return create_result

    async def update_test_set(
        self, issue_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing test set.

        Modifies the properties of an existing test set. Supports updating
        summary, description, and other test set attributes.

        Args:
            issue_id: The Jira issue ID of the test set to update
            updates: Dictionary containing fields to update:
                - summary: New summary/title
                - description: New description
                - labels: New labels

        Returns:
            Dict containing:
                - testSet: Updated test set object
                - success: Boolean indicating operation success

        Raises:
            ValidationError: If issue_id is invalid or updates are malformed
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation UpdateTestSet($issueId: String!, $updates: UpdateTestSetInput!) {
            updateTestSet(issueId: $issueId, testSet: $updates) {
                testSet {
                    issueId
                    summary
                    description
                    labels
                    updated
                }
            }
        }
        """

        # Resolve Jira key to internal ID if necessary
        resolved_id = await self.id_resolver.resolve_issue_id(issue_id, ResourceType.TEST_SET)

        variables = {"issueId": resolved_id, "updates": updates}

        result = await self.client.execute_query(mutation, variables)
        return result.get("data", {}).get("updateTestSet", {})

    async def delete_test_set(self, issue_id: str) -> Dict[str, Any]:
        """Delete a test set from Xray.

        Removes the test set issue from Jira. This operation does not affect
        the individual tests that were associated with the test set.

        Args:
            issue_id: The Jira issue ID of the test set to delete

        Returns:
            Dict containing:
                - success: Boolean indicating successful deletion
                - deletedTestSetId: ID of the deleted test set

        Raises:
            ValidationError: If issue_id is invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation DeleteTestSet($issueId: String!) {
            deleteTestSet(issueId: $issueId)
        }
        """

        # Resolve Jira key to internal ID if necessary
        resolved_id = await self.id_resolver.resolve_issue_id(issue_id, ResourceType.TEST_SET)

        variables = {"issueId": resolved_id}
        result = await self.client.execute_query(mutation, variables)

        delete_result = result.get("data", {}).get("deleteTestSet")
        
        # Handle both string and object responses
        if isinstance(delete_result, str):
            # If the response is a string, consider it successful if not empty
            success = bool(delete_result)
        elif isinstance(delete_result, dict):
            # If the response is a dict, check for success field
            success = delete_result.get("success", False)
        else:
            # If no response or unexpected type, consider it failed
            success = False
        
        return {
            "success": success,
            "deletedTestSetId": issue_id,
            "message": delete_result if isinstance(delete_result, str) else None,
        }

    async def add_tests_to_set(
        self, issue_id: str, test_issue_ids: List[str]
    ) -> Dict[str, Any]:
        """Add tests to an existing test set.

        Associates specified tests with a test set. Tests can belong to
        multiple test sets simultaneously.

        Args:
            issue_id: The Jira issue ID of the test set
            test_issue_ids: List of test issue IDs to add to the test set

        Returns:
            Dict containing:
                - addedTests: List of successfully added test objects
                - warnings: Any warnings from the operation

        Raises:
            ValidationError: If issue_id is invalid or test_issue_ids is empty
            GraphQLError: If the GraphQL mutation fails
        """
        if not test_issue_ids:
            raise ValidationError("test_issue_ids cannot be empty")

        mutation = """
        mutation AddTestsToTestSet($issueId: String!, $testIssueIds: [String!]!) {
            addTestsToTestSet(issueId: $issueId, testIssueIds: $testIssueIds) {
                addedTests
                warning
            }
        }
        """

        # Resolve Jira keys to internal IDs for both test set and tests
        resolved_set_id = await self.id_resolver.resolve_issue_id(issue_id, ResourceType.TEST_SET)
        resolved_test_ids = await self.id_resolver.resolve_multiple_issue_ids(
            test_issue_ids, ResourceType.TEST
        )

        variables = {"issueId": resolved_set_id, "testIssueIds": resolved_test_ids}

        result = await self.client.execute_query(mutation, variables)
        return result.get("data", {}).get("addTestsToTestSet", {})

    async def remove_tests_from_set(
        self, issue_id: str, test_issue_ids: List[str]
    ) -> Dict[str, Any]:
        """Remove tests from an existing test set.

        Disassociates specified tests from a test set. The tests themselves
        are not deleted, only their association with the test set.

        Args:
            issue_id: The Jira issue ID of the test set
            test_issue_ids: List of test issue IDs to remove from the test set

        Returns:
            Dict containing:
                - removedTests: List of successfully removed test IDs
                - success: Boolean indicating operation success

        Raises:
            ValidationError: If issue_id is invalid or test_issue_ids is empty
            GraphQLError: If the GraphQL mutation fails
        """
        if not test_issue_ids:
            raise ValidationError("test_issue_ids cannot be empty")

        mutation = """
        mutation RemoveTestsFromTestSet($issueId: String!, $testIssueIds: [String!]!) {
            removeTestsFromTestSet(issueId: $issueId, testIssueIds: $testIssueIds)
        }
        """

        # Resolve Jira keys to internal IDs for both test set and tests
        resolved_set_id = await self.id_resolver.resolve_issue_id(issue_id, ResourceType.TEST_SET)
        resolved_test_ids = await self.id_resolver.resolve_multiple_issue_ids(
            test_issue_ids, ResourceType.TEST
        )

        variables = {"issueId": resolved_set_id, "testIssueIds": resolved_test_ids}

        result = await self.client.execute_query(mutation, variables)
        
        return {
            "success": result.get("data", {}).get("removeTestsFromTestSet") is not None,
            "removedTests": test_issue_ids if result.get("data", {}).get("removeTestsFromTestSet") else [],
        }
