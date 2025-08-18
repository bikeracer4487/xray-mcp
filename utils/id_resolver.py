"""Shared utility for resolving Jira keys to internal issue IDs.

This module provides functionality to resolve Jira keys (like "TEST-123") to
internal numeric issue IDs that are required by some Xray GraphQL operations.
"""

from typing import Dict, Any, Optional, List
from enum import Enum

try:
    from ..client import XrayGraphQLClient
    from ..exceptions import GraphQLError
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError


class ResourceType(Enum):
    """Enumeration of Xray resource types for optimized ID resolution."""
    TEST = "test"
    TEST_SET = "test_set"
    TEST_EXECUTION = "test_execution"
    TEST_PLAN = "test_plan"
    PRECONDITION = "precondition"
    NON_TEST_ISSUE = "non_test_issue"  # Stories, tasks, bugs, etc.
    UNKNOWN = "unknown"


class IssueIdResolver:
    """Utility class for resolving Jira keys to internal issue IDs.

    This enhanced resolver uses a fallback chain approach to handle different
    resource types efficiently. It can also leverage resource type hints to
    minimize API calls when the expected type is known.

    Attributes:
        client (XrayGraphQLClient): GraphQL client for API communication
        cache (Dict[str, str]): In-memory cache for resolved IDs
    """

    def __init__(self, client: XrayGraphQLClient):
        """Initialize the resolver with a GraphQL client.

        Args:
            client (XrayGraphQLClient): Authenticated GraphQL client instance
        """
        self.client = client
        self.cache: Dict[str, str] = {}  # Simple in-memory cache

    async def resolve_issue_id(self, identifier: str, resource_type: Optional[ResourceType] = None) -> str:
        """Resolve a Jira key or issue ID to a numeric issue ID using fallback chain.

        Args:
            identifier: Either a Jira key (e.g., "TEST-123") or numeric issue ID (e.g., "1162822")
            resource_type: Optional hint about expected resource type for optimization

        Returns:
            str: Numeric issue ID that can be used with GraphQL queries

        Raises:
            GraphQLError: If the identifier cannot be resolved
        """
        # If it's already numeric, return as-is
        if identifier.isdigit():
            return identifier

        # Check cache first
        if identifier in self.cache:
            return self.cache[identifier]

        # If it looks like a Jira key (contains dash), try to resolve it
        if "-" in identifier:
            resolved_id = await self._resolve_with_fallback_chain(identifier, resource_type)
            
            # Cache the result for future use
            self.cache[identifier] = resolved_id
            return resolved_id

        # If it's neither numeric nor contains dash, assume it's already an issue ID
        return identifier

    async def _resolve_with_fallback_chain(self, jira_key: str, resource_type: Optional[ResourceType] = None) -> str:
        """Resolve using fallback chain based on resource type optimization.

        Args:
            jira_key: Jira key to resolve (e.g., "TEST-123")
            resource_type: Optional resource type hint for optimization

        Returns:
            str: Numeric issue ID

        Raises:
            GraphQLError: If resolution fails through all methods
        """
        # Define fallback chain based on resource type hint
        if resource_type == ResourceType.TEST:
            methods = [self._try_tests, self._try_test_sets, self._try_test_executions, self._try_test_plans, self._try_coverable_issues]
        elif resource_type == ResourceType.TEST_SET:
            methods = [self._try_test_sets, self._try_tests, self._try_test_executions, self._try_test_plans, self._try_coverable_issues]
        elif resource_type == ResourceType.TEST_EXECUTION:
            methods = [self._try_test_executions, self._try_tests, self._try_test_sets, self._try_test_plans, self._try_coverable_issues]
        elif resource_type == ResourceType.TEST_PLAN:
            methods = [self._try_test_plans, self._try_tests, self._try_test_sets, self._try_test_executions, self._try_coverable_issues]
        elif resource_type == ResourceType.PRECONDITION:
            methods = [self._try_tests, self._try_coverable_issues, self._try_test_sets, self._try_test_executions, self._try_test_plans]
        else:
            # Default fallback chain when no type hint provided
            methods = [self._try_tests, self._try_test_sets, self._try_test_executions, self._try_test_plans, self._try_coverable_issues]

        # Try each method in the fallback chain
        for method in methods:
            try:
                result = await method(jira_key)
                if result:
                    return result
            except GraphQLError:
                # Continue to next method if this one fails
                continue

        # If all methods fail, raise error
        raise GraphQLError(f"Could not resolve Jira key {jira_key} to issue ID through any available method")

    async def _try_tests(self, jira_key: str) -> Optional[str]:
        """Try to resolve using getTests query."""
        query = """
        query GetTestByKey($jql: String!, $limit: Int!) {
            getTests(jql: $jql, limit: $limit) {
                results {
                    issueId
                }
            }
        }
        """
        variables = {"jql": f'key = "{jira_key}"', "limit": 1}
        result = await self.client.execute_query(query, variables)

        if (
            "data" in result
            and "getTests" in result["data"]
            and result["data"]["getTests"]["results"]
        ):
            return result["data"]["getTests"]["results"][0]["issueId"]
        return None

    async def _try_test_sets(self, jira_key: str) -> Optional[str]:
        """Try to resolve using getTestSets query."""
        query = """
        query GetTestSetByKey($jql: String!, $limit: Int!) {
            getTestSets(jql: $jql, limit: $limit) {
                results {
                    issueId
                }
            }
        }
        """
        variables = {"jql": f'key = "{jira_key}"', "limit": 1}
        result = await self.client.execute_query(query, variables)

        if (
            "data" in result
            and "getTestSets" in result["data"]
            and result["data"]["getTestSets"]["results"]
        ):
            return result["data"]["getTestSets"]["results"][0]["issueId"]
        return None

    async def _try_test_executions(self, jira_key: str) -> Optional[str]:
        """Try to resolve using getTestExecutions query."""
        query = """
        query GetTestExecutionByKey($jql: String!, $limit: Int!) {
            getTestExecutions(jql: $jql, limit: $limit) {
                results {
                    issueId
                }
            }
        }
        """
        variables = {"jql": f'key = "{jira_key}"', "limit": 1}
        result = await self.client.execute_query(query, variables)

        if (
            "data" in result
            and "getTestExecutions" in result["data"]
            and result["data"]["getTestExecutions"]["results"]
        ):
            return result["data"]["getTestExecutions"]["results"][0]["issueId"]
        return None

    async def _try_test_plans(self, jira_key: str) -> Optional[str]:
        """Try to resolve using getTestPlans query."""
        query = """
        query GetTestPlanByKey($jql: String!, $limit: Int!) {
            getTestPlans(jql: $jql, limit: $limit) {
                results {
                    issueId
                }
            }
        }
        """
        variables = {"jql": f'key = "{jira_key}"', "limit": 1}
        result = await self.client.execute_query(query, variables)

        if (
            "data" in result
            and "getTestPlans" in result["data"]
            and result["data"]["getTestPlans"]["results"]
        ):
            return result["data"]["getTestPlans"]["results"][0]["issueId"]
        return None

    async def _try_coverable_issues(self, jira_key: str) -> Optional[str]:
        """Try to resolve using getCoverableIssues query for non-test issues."""
        query = """
        query GetCoverableIssueByKey($jql: String!, $limit: Int!) {
            getCoverableIssues(jql: $jql, limit: $limit) {
                results {
                    issueId
                }
            }
        }
        """
        variables = {"jql": f'key = "{jira_key}"', "limit": 1}
        result = await self.client.execute_query(query, variables)

        if (
            "data" in result
            and "getCoverableIssues" in result["data"]
            and result["data"]["getCoverableIssues"]["results"]
        ):
            return result["data"]["getCoverableIssues"]["results"][0]["issueId"]
        return None

    async def resolve_multiple_issue_ids(self, identifiers: List[str], resource_type: Optional[ResourceType] = None) -> List[str]:
        """Resolve multiple Jira keys or issue IDs to numeric issue IDs.

        Args:
            identifiers: List of Jira keys or numeric issue IDs
            resource_type: Optional resource type hint for optimization

        Returns:
            List[str]: List of numeric issue IDs

        Raises:
            GraphQLError: If any identifier cannot be resolved
        """
        resolved_ids = []
        for identifier in identifiers:
            resolved_id = await self.resolve_issue_id(identifier, resource_type)
            resolved_ids.append(resolved_id)
        return resolved_ids

    def clear_cache(self) -> None:
        """Clear the ID resolution cache."""
        self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring and debugging.
        
        Returns:
            Dict containing cache size and cached keys
        """
        return {
            "cache_size": len(self.cache),
            "cached_keys": list(self.cache.keys())
        }
