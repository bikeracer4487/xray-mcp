"""GraphQL client for Xray API.

This module provides a GraphQL client specifically designed for Jira Xray's
GraphQL API. It handles authentication, query/mutation execution, and error
management for all GraphQL operations.

The client automatically manages authentication tokens through the provided
auth_manager and handles both GraphQL-level and HTTP-level errors appropriately.
"""

import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional

# Centralized import handling
try:
    from ..utils.imports import import_from
    auth_imports = import_from("..auth", "auth", "XrayAuthManager")
    exception_imports = import_from("..exceptions", "exceptions", "GraphQLError")
    validator_imports = import_from("..validators.graphql_validator", "validators.graphql_validator", "GraphQLValidator")
    security_imports = import_from("..security.response_limiter", "security.response_limiter", "get_response_limiter", "ResponseSizeLimitError")
    pool_imports = import_from("..utils.connection_pool", "utils.connection_pool", "get_connection_pool")
    
    XrayAuthManager = auth_imports['XrayAuthManager']
    GraphQLError = exception_imports['GraphQLError']
    GraphQLValidator = validator_imports['GraphQLValidator']
    get_response_limiter = security_imports['get_response_limiter']
    ResponseSizeLimitError = security_imports['ResponseSizeLimitError']
    get_connection_pool = pool_imports['get_connection_pool']
except ImportError:
    # Fallback for direct execution
    from auth import XrayAuthManager
    from exceptions import GraphQLError
    from validators.graphql_validator import GraphQLValidator
    from security.response_limiter import get_response_limiter, ResponseSizeLimitError
    from utils.connection_pool import get_connection_pool


class XrayGraphQLClient:
    """GraphQL client for interacting with Xray API.

    This client provides a unified interface for executing GraphQL queries
    and mutations against the Xray API. It handles:
    - Automatic token management through XrayAuthManager
    - HTTP request/response handling
    - GraphQL error parsing and reporting
    - Network error handling

    The client is designed to be used by tool classes rather than directly,
    providing a clean separation between API communication and business logic.

    Attributes:
        auth_manager (XrayAuthManager): Handles JWT token lifecycle
        endpoint (str): GraphQL API endpoint URL

    Example:
        auth_manager = XrayAuthManager(client_id, client_secret)
        client = XrayGraphQLClient(auth_manager)
        result = await client.execute_query(\"\"\"
            query {
                getTests(jql: "project = TEST", limit: 10) {
                    total
                    results { issueId jira { key summary } }
                }
            }
        \"\"\")
    """

    def __init__(self, auth_manager: XrayAuthManager):
        """Initialize the GraphQL client with an authentication manager.

        Args:
            auth_manager (XrayAuthManager): Authentication manager instance
                that provides valid JWT tokens for API requests

        Note:
            The GraphQL endpoint is constructed from the auth_manager's
            base_url, supporting both cloud and server Xray instances.
            
            A GraphQL validator is initialized to prevent injection attacks.
            A response limiter provides DoS protection via size limits.
            Connection pooling is used for improved performance.
        """
        self.auth_manager = auth_manager
        self.endpoint = f"{auth_manager.base_url}/api/v2/graphql"
        self.validator = GraphQLValidator()
        self.response_limiter = get_response_limiter()
        self._pool_manager = None
    
    async def _get_pool_manager(self):
        """Get connection pool manager, initializing if needed."""
        if self._pool_manager is None:
            self._pool_manager = await get_connection_pool()
        return self._pool_manager

    async def execute_query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a GraphQL query against the Xray API with security protections.

        Handles the complete request lifecycle including authentication,
        request formatting, error handling, and response parsing. Both
        HTTP-level and GraphQL-level errors are properly handled. Includes
        protection against GraphQL injection attacks and oversized responses.

        Args:
            query (str): GraphQL query string in standard GraphQL syntax
            variables (Optional[Dict[str, Any]]): Optional variables for
                parameterized queries. Keys should match variable names
                in the query.

        Returns:
            Dict[str, Any]: GraphQL response containing:
                - "data": Query results (if successful)
                - May contain partial data even with errors

        Raises:
            GraphQLError: If the request fails due to:
                - GraphQL execution errors (syntax, validation, execution)
                - GraphQL injection attempts (blocked by validator)
                - HTTP errors (4xx, 5xx status codes)
                - Network connectivity issues
                - Response size limit violations (DoS protection)

        Complexity: O(1) - Single HTTP request

        Call Flow:
            1. Validate query for security (injection prevention)
            2. Obtain valid JWT token from auth_manager
            3. Construct request with auth headers
            4. Send POST request to GraphQL endpoint
            5. Parse response with size limits (DoS protection)
            6. Check for errors and return data or raise exception

        Security Features:
            - GraphQL injection prevention via whitelist validation
            - Response size limiting to prevent memory exhaustion
            - Safe error text handling with size limits

        Example:
            query = \"\"\"
                query GetTest($id: String!) {
                    getTest(issueId: $id) {
                        issueId
                        projectId
                        testType { name kind }
                    }
                }
            \"\"\"
            result = await client.execute_query(query, {"id": "TEST-123"})
        """
        # Validate query for security before execution
        try:
            validated_query = self.validator.validate_query(query, variables)
        except Exception as e:
            raise GraphQLError(f"GraphQL query validation failed: {str(e)}")
        
        # Get a fresh or cached valid token
        token = await self.auth_manager.get_valid_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # Construct GraphQL request payload using validated query
        payload = {"query": validated_query}
        if variables:
            payload["variables"] = variables

        try:
            # Use connection pool for improved performance
            pool_manager = await self._get_pool_manager()
            async with pool_manager.session_context() as session:
                async with session.post(
                    self.endpoint, json=payload, headers=headers
                ) as response:
                    if response.status == 200:
                        try:
                            # Use response limiter for safe JSON reading with size limits
                            result = await self.response_limiter.read_json_response(response)
                        except ResponseSizeLimitError as e:
                            # Handle responses that exceed size limits
                            raise GraphQLError(f"Response too large: {str(e)}")
                        except ValueError as e:
                            # Handle malformed JSON responses with limited error text
                            try:
                                error_text = await self.response_limiter.read_text_response(response)
                            except ResponseSizeLimitError:
                                error_text = "Error response too large to display"
                            raise GraphQLError(
                                f"Invalid JSON in response: {str(e)}: {error_text}"
                            )

                        # GraphQL can return 200 OK with errors in the response
                        # Check for GraphQL-level errors and report them
                        if "errors" in result:
                            error_messages = [
                                error.get("message", "Unknown error")
                                for error in result["errors"]
                            ]
                            raise GraphQLError(
                                f"GraphQL errors: {'; '.join(error_messages)}"
                            )

                        return result
                    else:
                        # HTTP-level error (4xx, 5xx) - use response limiter for safe text reading
                        try:
                            error_text = await self.response_limiter.read_text_response(response)
                        except ResponseSizeLimitError as e:
                            error_text = f"Error response too large: {str(e)}"
                        raise GraphQLError(
                            f"GraphQL request failed with status {response.status}: {error_text}"
                        )

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            # Network-level errors (connection, timeout, etc.)
            raise GraphQLError(f"Network error during GraphQL request: {str(e)}")

    async def execute_mutation(
        self, mutation: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a GraphQL mutation against the Xray API.

        This is a convenience method that delegates to execute_query.
        GraphQL treats queries and mutations identically at the transport
        level, differing only in semantics (queries read, mutations write).

        Args:
            mutation (str): GraphQL mutation string in standard syntax
            variables (Optional[Dict[str, Any]]): Optional variables for
                parameterized mutations

        Returns:
            Dict[str, Any]: GraphQL response containing:
                - "data": Mutation results (created/updated entities)
                - May contain partial data even with errors

        Raises:
            GraphQLError: If the mutation fails (same as execute_query)

        Complexity: O(1) - Single HTTP request

        Example:
            mutation = \"\"\"
                mutation CreateTest($projectId: String!, $summary: String!) {
                    createTest(testIssueFields: {
                        projectId: $projectId
                        summary: $summary
                    }) {
                        test { issueId jira { key } }
                        warnings
                    }
                }
            \"\"\"
            result = await client.execute_mutation(
                mutation,
                {"projectId": "10000", "summary": "New test"}
            )
        """
        # Mutations and queries use identical transport mechanism with validation
        return await self.execute_query(mutation, variables)
