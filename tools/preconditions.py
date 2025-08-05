"""Precondition management tools for Xray MCP server.

This module provides functionality for managing preconditions in Xray,
including creating, retrieving, updating, and deleting preconditions.
Preconditions are prerequisites that must be satisfied before test execution.

The PreconditionTools class serves as the main interface for interacting
with Xray's precondition API through GraphQL queries and mutations.
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


class PreconditionTools:
    """Tools for managing preconditions in Xray.

    This class provides methods to interact with preconditions, which define
    prerequisites that must be met before test execution. Preconditions can
    be associated with multiple tests and help ensure consistent test setup.

    Attributes:
        client (XrayGraphQLClient): GraphQL client for API communication

    Dependencies:
        - Requires authenticated XrayGraphQLClient instance
        - Depends on Xray GraphQL API for precondition operations

    Note:
        All methods return structured dictionaries compatible with MCP responses.
        Errors are propagated to calling code for centralized error handling.
    """

    def __init__(self, client: XrayGraphQLClient):
        """Initialize precondition tools with GraphQL client.

        Args:
            client (XrayGraphQLClient): Authenticated GraphQL client instance
        """
        self.client = client
        self.id_resolver = IssueIdResolver(client)

    async def get_preconditions(
        self, issue_id: str, start: int = 0, limit: int = 100
    ) -> Dict[str, Any]:
        """Retrieve preconditions for a given test issue.

        Fetches all preconditions associated with a specific test, with pagination
        support for handling large numbers of preconditions.

        Args:
            issue_id: The Jira issue ID of the test
            start: Starting index for pagination (0-based)
            limit: Maximum number of preconditions to return (max 100)

        Returns:
            Dict containing:
                - preconditions: List of precondition objects
                - total: Total number of preconditions
                - start: Starting index of results
                - limit: Number of results requested

        Raises:
            ValidationError: If issue_id is invalid or limit exceeds 100
            GraphQLError: If the GraphQL query fails
        """
        if limit > 100:
            raise ValidationError("Limit cannot exceed 100")

        query = """
        query GetPreconditions($issueId: String!, $start: Int!, $limit: Int!) {
            getTest(issueId: $issueId) {
                preconditions(start: $start, limit: $limit) {
                    total
                    start
                    limit
                    results {
                        issueId
                        projectId
                        definition
                        preconditionType {
                            name
                            kind
                        }
                        jira(fields: ["key", "summary", "status", "priority", "labels", "created", "updated"])
                    }
                }
            }
        }
        """

        # Resolve Jira key to internal ID if necessary
        resolved_id = await self.id_resolver.resolve_issue_id(issue_id)
        variables = {"issueId": resolved_id, "start": start, "limit": limit}

        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getTest", {}).get("preconditions", {})

    async def create_precondition(
        self, issue_id: str, precondition_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new precondition and associate it with a test.

        Creates a precondition issue in Jira and links it to the specified test.
        The precondition can be of type Manual, Generic, or Cucumber.

        Args:
            issue_id: The Jira issue ID of the test to associate the precondition with
            precondition_input: Dictionary containing precondition details:
                - preconditionType: Type object {name: "Generic|Manual|Cucumber"}
                - definition: Precondition definition text
                - jira: Jira object with fields {summary: "...", project: {key: "..."}}

        Returns:
            Dict containing:
                - precondition: Created precondition object with issueId, type, definition
                - warnings: Any warnings from the operation
                - addedToTest: Result of adding precondition to the test (if successful)

        Raises:
            ValidationError: If required fields are missing or invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation CreatePrecondition($preconditionType: PreconditionTypeInput!, $definition: String!, $jira: JSON!) {
            createPrecondition(preconditionType: $preconditionType, definition: $definition, jira: $jira) {
                precondition {
                    issueId
                    preconditionType {
                        name
                        kind
                    }
                    definition
                    jira(fields: ["key", "summary"])
                }
                warnings
            }
        }
        """

        # Extract and validate required fields from precondition_input
        if "preconditionType" not in precondition_input:
            raise ValidationError("preconditionType is required")
        if "definition" not in precondition_input:
            raise ValidationError("definition is required")
        if "jira" not in precondition_input:
            raise ValidationError("jira object is required")

        variables = {
            "preconditionType": precondition_input["preconditionType"],
            "definition": precondition_input["definition"],
            "jira": precondition_input["jira"],
        }

        result = await self.client.execute_query(mutation, variables)
        create_result = result.get("data", {}).get("createPrecondition", {})

        # If issue_id was provided, add the created precondition to the test
        if create_result.get("precondition", {}).get("issueId"):
            precondition_id = create_result["precondition"]["issueId"]
            add_mutation = """
            mutation AddPreconditionToTest($issueId: String!, $preconditionIssueIds: [String!]!) {
                addPreconditionsToTest(issueId: $issueId, preconditionIssueIds: $preconditionIssueIds) {
                    addedPreconditions
                    warning
                }
            }
            """
            # Resolve the test issue ID
            resolved_test_id = await self.id_resolver.resolve_issue_id(issue_id)
            add_variables = {
                "issueId": resolved_test_id,
                "preconditionIssueIds": [precondition_id],
            }
            add_result = await self.client.execute_query(add_mutation, add_variables)
            create_result["addedToTest"] = add_result.get("data", {}).get(
                "addPreconditionsToTest", {}
            )

        return create_result

    async def update_precondition(
        self, precondition_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing precondition.

        Modifies the properties of an existing precondition. Supports updating
        definition, precondition type, and other precondition attributes.

        Args:
            precondition_id: The Jira issue ID of the precondition to update
            updates: Dictionary containing fields to update:
                - preconditionType: New precondition type {name: "Generic|Manual|Cucumber"}
                - definition: New definition text
                - folderPath: New folder path for organization

        Returns:
            Dict containing:
                - issueId: Updated precondition issue ID
                - preconditionType: Updated precondition type
                - definition: Updated definition
                - jira: Jira fields including key, summary, updated timestamp

        Raises:
            ValidationError: If precondition_id is invalid or updates are malformed
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation UpdatePrecondition($issueId: String!, $data: UpdatePreconditionInput!) {
            updatePrecondition(issueId: $issueId, data: $data) {
                issueId
                preconditionType {
                    name
                    kind
                }
                definition
                jira(fields: ["key", "summary", "updated"])
            }
        }
        """

        # Resolve Jira key to internal ID if necessary
        resolved_id = await self.id_resolver.resolve_issue_id(precondition_id)
        variables = {"issueId": resolved_id, "data": updates}

        result = await self.client.execute_query(mutation, variables)
        return result.get("data", {}).get("updatePrecondition", {})

    async def delete_precondition(self, precondition_id: str) -> Dict[str, Any]:
        """Delete a precondition from Xray.

        Removes the precondition issue from Jira. This operation also removes
        the precondition from all associated tests.

        Args:
            precondition_id: The Jira issue ID of the precondition to delete

        Returns:
            Dict containing:
                - success: Boolean indicating successful deletion
                - deletedPreconditionId: ID of the deleted precondition

        Raises:
            ValidationError: If precondition_id is invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation DeletePrecondition($preconditionId: String!) {
            deletePrecondition(issueId: $preconditionId) {
                success
            }
        }
        """

        # Resolve Jira key to internal ID if necessary
        resolved_id = await self.id_resolver.resolve_issue_id(precondition_id)
        variables = {"preconditionId": resolved_id}

        result = await self.client.execute_query(mutation, variables)
        return {
            "success": result.get("data", {})
            .get("deletePrecondition", {})
            .get("success", False),
            "deletedPreconditionId": precondition_id,
        }
