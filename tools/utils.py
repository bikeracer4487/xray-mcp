"""Utility tools for Xray MCP server.

This module provides utility functionality that doesn't fit into specific
test management categories but is essential for Xray operations. It includes
tools for executing custom JQL queries with security validation and for
validating API connectivity.

The UtilityTools class serves as a collection of helper methods that support
other tools and provide diagnostic capabilities for the MCP server.
"""

from typing import Dict, Any, Optional

try:
    from ..client import XrayGraphQLClient
    from ..exceptions import GraphQLError
    from ..validators import validate_jql
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError
    from validators import validate_jql


class UtilityTools:
    """Utility tools for Xray operations.

    This class provides helper methods for common Xray operations including
    JQL query execution with injection protection and connection validation.
    All JQL queries are validated through the security validator to prevent
    injection attacks.

    Attributes:
        client (XrayGraphQLClient): GraphQL client for Xray API communication

    Example:
        >>> from client import XrayGraphQLClient
        >>> client = XrayGraphQLClient(auth_manager, base_url)
        >>> utils = UtilityTools(client)
        >>>
        >>> # Execute a safe JQL query
        >>> results = await utils.execute_jql_query(
        ...     jql='project = "TEST" AND status = "In Progress"',
        ...     entity_type="test"
        ... )
        >>>
        >>> # Validate API connection
        >>> status = await utils.validate_connection()
        >>> print(f"Connected: {status['authenticated']}")
    """

    def __init__(self, graphql_client: XrayGraphQLClient):
        """Initialize UtilityTools with a GraphQL client.

        Args:
            graphql_client (XrayGraphQLClient): Initialized GraphQL client
                for communicating with the Xray API. Must be properly
                authenticated before use.
        """
        self.client = graphql_client

    async def execute_jql_query(
        self, jql: str, entity_type: str = "test", limit: int = 100
    ) -> Dict[str, Any]:
        """Execute a custom JQL query for different entity types.

        Provides a safe way to execute JQL queries by validating them against
        injection attacks before execution. Supports querying different Xray
        entity types with consistent result formatting.

        Args:
            jql (str): JQL query string to execute. Will be validated using
                the whitelist-based validator to prevent injection attacks.
                Example: 'project = "TEST" AND labels = "automated"'
            entity_type (str): Type of entity to query. Supported values:
                - "test": Query test issues (default)
                - "testexecution": Query test execution issues
            limit (int): Maximum number of results to return. Must be
                between 1 and 100 due to API constraints (default: 100)

        Returns:
            Dict[str, Any]: Query results containing:
                - total: Total number of entities matching the query
                - start: Starting index (0-based)
                - limit: Number of results returned
                - results: List of entity objects with issueId and jira fields

        Raises:
            ValidationError: If JQL contains dangerous patterns or
                limit exceeds maximum allowed value
            GraphQLError: If query execution fails or entity type
                is not supported

        Complexity: O(n) where n is the limit

        Example:
            >>> # Query automated tests in progress
            >>> results = await utils.execute_jql_query(
            ...     jql='project = "TEST" AND labels = "automated" AND status = "In Progress"',
            ...     entity_type="test",
            ...     limit=50
            ... )
            >>> print(f"Found {results['total']} tests")
            >>> for test in results['results']:
            ...     print(f"Test: {test['jira']['key']} - {test['jira']['summary']}")

        Note:
            The JQL validation ensures that only safe query patterns are
            executed, preventing SQL injection and other security risks.
        """
        # Validate and sanitize JQL to prevent injection attacks
        # This is critical for security - all user-provided JQL must be validated
        safe_jql = validate_jql(jql)

        # Route to appropriate query method based on entity type
        # Case-insensitive comparison for user convenience
        if entity_type.lower() == "test":
            return await self._execute_test_jql(safe_jql, limit)
        elif entity_type.lower() == "testexecution":
            return await self._execute_test_execution_jql(safe_jql, limit)
        else:
            # Fail fast for unsupported entity types
            raise GraphQLError(f"Unsupported entity type: {entity_type}")

    async def _execute_test_jql(self, jql: str, limit: int) -> Dict[str, Any]:
        """Execute JQL query specifically for test entities.

        Internal method that constructs and executes a GraphQL query to
        retrieve tests matching the provided JQL criteria.

        Args:
            jql (str): Pre-validated JQL query string
            limit (int): Maximum number of results to return

        Returns:
            Dict[str, Any]: Paginated test results with issueId,
                testType, and basic Jira fields

        Raises:
            GraphQLError: If the query execution fails

        Complexity: O(n) where n is the limit

        Call Flow:
            1. Constructs GraphQL query with test-specific fields
            2. Executes query with provided parameters
            3. Extracts and returns test data from response

        Note:
            This is an internal method. JQL validation should be
            performed before calling this method.
        """
        query = """
        query ExecuteTestJQL($jql: String!, $limit: Int!) {
            getTests(jql: $jql, limit: $limit) {
                total
                start
                limit
                results {
                    issueId
                    testType {
                        name
                    }
                    jira(fields: ["key", "summary", "status", "assignee"])
                }
            }
        }
        """

        variables = {"jql": jql, "limit": limit}
        result = await self.client.execute_query(query, variables)

        if "data" in result and "getTests" in result["data"]:
            return result["data"]["getTests"]
        else:
            raise GraphQLError("Failed to execute JQL query for tests")

    async def _execute_test_execution_jql(self, jql: str, limit: int) -> Dict[str, Any]:
        """Execute JQL query specifically for test execution entities.

        Internal method that constructs and executes a GraphQL query to
        retrieve test executions matching the provided JQL criteria.

        Args:
            jql (str): Pre-validated JQL query string
            limit (int): Maximum number of results to return

        Returns:
            Dict[str, Any]: Paginated test execution results with
                issueId and basic Jira fields

        Raises:
            GraphQLError: If the query execution fails

        Complexity: O(n) where n is the limit

        Call Flow:
            1. Constructs GraphQL query for test executions
            2. Executes query with provided parameters
            3. Extracts and returns execution data from response

        Note:
            This is an internal method. JQL validation should be
            performed before calling this method.
        """
        query = """
        query ExecuteTestExecutionJQL($jql: String!, $limit: Int!) {
            getTestExecutions(jql: $jql, limit: $limit) {
                total
                start
                limit
                results {
                    issueId
                    jira(fields: ["key", "summary", "status", "assignee"])
                }
            }
        }
        """

        variables = {"jql": jql, "limit": limit}
        result = await self.client.execute_query(query, variables)

        if "data" in result and "getTestExecutions" in result["data"]:
            return result["data"]["getTestExecutions"]
        else:
            raise GraphQLError("Failed to execute JQL query for test executions")

    async def validate_connection(self) -> Dict[str, Any]:
        """Test connection and authentication with Xray API.

        Performs a lightweight query to validate that the connection to
        the Xray API is working and that authentication is successful.
        This is useful for diagnostics and health checks.

        Returns:
            Dict[str, Any]: Connection status containing:
                - status: "connected" or "error"
                - message: Human-readable status message
                - authenticated: Boolean indicating if authentication
                  was successful

        Complexity: O(1) - Single lightweight query

        Example:
            >>> # Check if API is accessible
            >>> status = await utils.validate_connection()
            >>> if status['authenticated']:
            ...     print("API connection successful")
            ... else:
            ...     print(f"Connection failed: {status['message']}")

        Note:
            This method catches all exceptions to provide a consistent
            response format, making it suitable for health checks and
            monitoring endpoints.

        Call Flow:
            1. Attempts a minimal GraphQL query (getTests with limit 1)
            2. Checks for successful response with data
            3. Returns standardized status dictionary
            4. Catches and reports any exceptions
        """
        try:
            # Execute a minimal query to test connectivity
            # Using getTests with limit 1 as it's lightweight and always available
            query = """
            query ValidateConnection {
                getTests(limit: 1) {
                    total
                }
            }
            """

            result = await self.client.execute_query(query)

            # Check if we received a valid response with data
            # Presence of "data" indicates successful authentication and query execution
            if "data" in result:
                return {
                    "status": "connected",
                    "message": "Successfully connected to Xray API",
                    "authenticated": True,
                }
            else:
                # Query executed but returned no data - likely auth issue
                return {
                    "status": "error",
                    "message": "Failed to validate connection",
                    "authenticated": False,
                }

        except Exception as e:
            # Catch all exceptions to provide consistent response format
            # This makes the method suitable for health checks
            return {
                "status": "error",
                "message": f"Connection validation failed: {str(e)}",
                "authenticated": False,
            }
