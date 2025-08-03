"""GraphQL client for Xray API.

This module provides a GraphQL client specifically designed for Jira Xray's
GraphQL API. It handles authentication, query/mutation execution, and error
management for all GraphQL operations.

The client automatically manages authentication tokens through the provided
auth_manager and handles both GraphQL-level and HTTP-level errors appropriately.
"""

import json
import aiohttp
from typing import Dict, Any, Optional

# Handle both package and direct execution import modes
try:
    from ..auth import XrayAuthManager
    from ..exceptions import GraphQLError
except ImportError:
    from auth import XrayAuthManager
    from exceptions import GraphQLError


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
        """
        self.auth_manager = auth_manager
        self.endpoint = f"{auth_manager.base_url}/api/v2/graphql"
    
    async def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query against the Xray API.
        
        Handles the complete request lifecycle including authentication,
        request formatting, error handling, and response parsing. Both
        HTTP-level and GraphQL-level errors are properly handled.
        
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
                - HTTP errors (4xx, 5xx status codes)
                - Network connectivity issues
        
        Complexity: O(1) - Single HTTP request
        
        Call Flow:
            1. Obtain valid JWT token from auth_manager
            2. Construct request with auth headers
            3. Send POST request to GraphQL endpoint
            4. Parse response and check for errors
            5. Return data or raise appropriate exception
        
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
        # Get a fresh or cached valid token
        token = await self.auth_manager.get_valid_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Construct GraphQL request payload
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # GraphQL can return 200 OK with errors in the response
                        # Check for GraphQL-level errors and report them
                        if "errors" in result:
                            error_messages = [error.get("message", "Unknown error") for error in result["errors"]]
                            raise GraphQLError(f"GraphQL errors: {'; '.join(error_messages)}")
                        
                        return result
                    else:
                        # HTTP-level error (4xx, 5xx)
                        error_text = await response.text()
                        raise GraphQLError(f"GraphQL request failed with status {response.status}: {error_text}")
        
        except aiohttp.ClientError as e:
            # Network-level errors (connection, timeout, etc.)
            raise GraphQLError(f"Network error during GraphQL request: {str(e)}")
    
    async def execute_mutation(self, mutation: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
        # Mutations and queries use identical transport mechanism
        return await self.execute_query(mutation, variables)

