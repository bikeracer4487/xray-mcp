"""Shared utility for resolving Jira keys to internal issue IDs.

This module provides functionality to resolve Jira keys (like "TEST-123") to
internal numeric issue IDs that are required by some Xray GraphQL operations.
"""

from typing import Dict, Any

try:
    from ..client import XrayGraphQLClient
    from ..exceptions import GraphQLError
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError


class IssueIdResolver:
    """Utility class for resolving Jira keys to internal issue IDs.

    Some Xray GraphQL operations require numeric internal issue IDs rather than
    Jira keys. This class provides a centralized way to resolve identifiers
    to the appropriate format.

    Attributes:
        client (XrayGraphQLClient): GraphQL client for API communication
    """

    def __init__(self, client: XrayGraphQLClient):
        """Initialize the resolver with a GraphQL client.

        Args:
            client (XrayGraphQLClient): Authenticated GraphQL client instance
        """
        self.client = client

    async def resolve_issue_id(self, identifier: str) -> str:
        """Resolve a Jira key or issue ID to a numeric issue ID.

        Args:
            identifier: Either a Jira key (e.g., "TEST-123") or numeric issue ID (e.g., "1162822")

        Returns:
            str: Numeric issue ID that can be used with GraphQL queries

        Raises:
            GraphQLError: If the identifier cannot be resolved
        """
        # If it's already numeric, return as-is
        if identifier.isdigit():
            return identifier

        # If it looks like a Jira key (contains dash), try to resolve it
        if "-" in identifier:
            # Use JQL query to find the issue ID for this key
            query = """
            query GetTestByKey($jql: String!, $limit: Int!) {
                getTests(jql: $jql, limit: $limit) {
                    results {
                        issueId
                        jira(fields: ["key"])
                    }
                }
            }
            """

            variables = {"jql": f'key = "{identifier}"', "limit": 1}
            result = await self.client.execute_query(query, variables)

            if (
                "data" in result
                and "getTests" in result["data"]
                and result["data"]["getTests"]["results"]
            ):
                return result["data"]["getTests"]["results"][0]["issueId"]
            else:
                raise GraphQLError(
                    f"Could not resolve Jira key {identifier} to issue ID"
                )

        # If it's neither numeric nor contains dash, assume it's already an issue ID
        return identifier

    async def resolve_multiple_issue_ids(self, identifiers: list[str]) -> list[str]:
        """Resolve multiple Jira keys or issue IDs to numeric issue IDs.

        Args:
            identifiers: List of Jira keys or numeric issue IDs

        Returns:
            List[str]: List of numeric issue IDs

        Raises:
            GraphQLError: If any identifier cannot be resolved
        """
        resolved_ids = []
        for identifier in identifiers:
            resolved_id = await self.resolve_issue_id(identifier)
            resolved_ids.append(resolved_id)
        return resolved_ids
