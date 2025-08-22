"""Comprehensive tests for XrayGraphQLClient.

Tests cover query execution, error handling, and edge cases.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from client.graphql import XrayGraphQLClient
from auth.manager import XrayAuthManager
from exceptions import GraphQLError


@pytest.fixture
def mock_auth_manager():
    """Create mock auth manager with valid token."""
    auth = AsyncMock(spec=XrayAuthManager)
    auth.get_valid_token = AsyncMock(return_value="valid_token")
    auth.base_url = "https://xray.cloud.getxray.app"
    return auth


@pytest.mark.asyncio
@pytest.mark.unit
class TestExecuteQuerySuccess:
    """Test successful query execution scenarios."""

    async def test_execute_query_simple_success(self, mock_auth_manager, mocker):
        """Test successful query returns data dict."""
        client = XrayGraphQLClient(mock_auth_manager)
        mock_session = AsyncMock()
        mock_response = AsyncMock(
            status=200,
            json=AsyncMock(return_value={"data": {"test": "result"}})
        )
        mock_post_context = AsyncMock()
        mock_post_context.__aenter__.return_value = mock_response
        mock_post_context.__aexit__.return_value = None
        mock_session.post = MagicMock(return_value=mock_post_context)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        result = await client.execute_query("query { test }")
        assert result == {"data": {"test": "result"}}
        
        # Verify correct headers and endpoint
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "https://xray.cloud.getxray.app/api/v2/graphql"
        assert call_args[1]["headers"]["Authorization"] == "Bearer valid_token"
        assert call_args[1]["headers"]["Content-Type"] == "application/json"

    async def test_execute_query_with_variables(self, mock_auth_manager, mocker):
        """Test query with variables passes them correctly."""
        client = XrayGraphQLClient(mock_auth_manager)
        mock_session = AsyncMock()
        mock_response = AsyncMock(
            status=200,
            json=AsyncMock(return_value={"data": {"result": "value"}})
        )
        mock_post_context = AsyncMock()
        mock_post_context.__aenter__.return_value = mock_response
        mock_post_context.__aexit__.return_value = None
        mock_session.post = MagicMock(return_value=mock_post_context)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        variables = {"id": "TEST-123", "limit": 10}
        result = await client.execute_query(
            "query GetTest($id: String!, $limit: Int!) { getTest(id: $id, limit: $limit) }",
            variables
        )
        
        # Verify variables were included in payload
        call_args = mock_session.post.call_args
        payload = call_args[1]["json"]
        assert payload["variables"] == variables
        assert "query" in payload

    async def test_execute_query_empty_response(self, mock_auth_manager, mocker):
        """Test handling of empty but valid response."""
        client = XrayGraphQLClient(mock_auth_manager)
        mock_session = AsyncMock()
        mock_response = AsyncMock(
            status=200,
            json=AsyncMock(return_value={"data": {}})
        )
        mock_post_context = AsyncMock()
        mock_post_context.__aenter__.return_value = mock_response
        mock_post_context.__aexit__.return_value = None
        mock_session.post = MagicMock(return_value=mock_post_context)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        result = await client.execute_query("query { empty }")
        assert result == {"data": {}}

    async def test_execute_mutation_delegates_to_query(self, mock_auth_manager, mocker):
        """Test mutation uses same execution path as query."""
        client = XrayGraphQLClient(mock_auth_manager)
        mocker.patch.object(client, 'execute_query', AsyncMock(return_value={"data": "mutated"}))
        
        result = await client.execute_mutation(
            "mutation CreateTest($input: TestInput!) { createTest(input: $input) }",
            {"input": {"name": "test"}}
        )
        
        assert result == {"data": "mutated"}
        client.execute_query.assert_called_once_with(
            "mutation CreateTest($input: TestInput!) { createTest(input: $input) }",
            {"input": {"name": "test"}}
        )


@pytest.mark.asyncio
@pytest.mark.unit
class TestExecuteQueryErrors:
    """Test error handling in query execution."""

    async def test_execute_query_graphql_errors(self, mock_auth_manager, mocker):
        """Test 200 response with errors field raises GraphQLError."""
        client = XrayGraphQLClient(mock_auth_manager)
        mock_session = AsyncMock()
        mock_response = AsyncMock(
            status=200,
            json=AsyncMock(return_value={
                "errors": [
                    {"message": "Field 'invalid' doesn't exist"},
                    {"message": "Syntax error at line 1"}
                ]
            })
        )
        mock_post_context = AsyncMock()
        mock_post_context.__aenter__.return_value = mock_response
        mock_post_context.__aexit__.return_value = None
        mock_session.post = MagicMock(return_value=mock_post_context)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        with pytest.raises(GraphQLError, match="GraphQL errors: Field 'invalid' doesn't exist; Syntax error at line 1"):
            await client.execute_query("query { invalid }")

    async def test_execute_query_partial_data_with_errors(self, mock_auth_manager, mocker):
        """Test partial data with errors still raises exception."""
        client = XrayGraphQLClient(mock_auth_manager)
        mock_session = AsyncMock()
        mock_response = AsyncMock(
            status=200,
            json=AsyncMock(return_value={
                "data": {"partial": "result"},
                "errors": [{"message": "Some field failed"}]
            })
        )
        mock_post_context = AsyncMock()
        mock_post_context.__aenter__.return_value = mock_response
        mock_post_context.__aexit__.return_value = None
        mock_session.post = MagicMock(return_value=mock_post_context)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        # GraphQL spec: even with partial data, errors should be raised
        with pytest.raises(GraphQLError, match="GraphQL errors: Some field failed"):
            await client.execute_query("query { partial failing }")

    async def test_execute_query_http_400_error(self, mock_auth_manager, mocker):
        """Test HTTP 400 error handling."""
        client = XrayGraphQLClient(mock_auth_manager)
        mock_session = AsyncMock()
        mock_response = AsyncMock(
            status=400,
            text=AsyncMock(return_value="Bad GraphQL query syntax")
        )
        mock_post_context = AsyncMock()
        mock_post_context.__aenter__.return_value = mock_response
        mock_post_context.__aexit__.return_value = None
        mock_session.post = MagicMock(return_value=mock_post_context)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        with pytest.raises(GraphQLError, match="GraphQL request failed with status 400: Bad GraphQL query syntax"):
            await client.execute_query("malformed query")

    async def test_execute_query_http_401_error(self, mock_auth_manager, mocker):
        """Test HTTP 401 unauthorized error."""
        client = XrayGraphQLClient(mock_auth_manager)
        mock_session = AsyncMock()
        mock_response = AsyncMock(
            status=401,
            text=AsyncMock(return_value="Token expired or invalid")
        )
        mock_post_context = AsyncMock()
        mock_post_context.__aenter__.return_value = mock_response
        mock_post_context.__aexit__.return_value = None
        mock_session.post = MagicMock(return_value=mock_post_context)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        with pytest.raises(GraphQLError, match="GraphQL request failed with status 401: Token expired or invalid"):
            await client.execute_query("query { test }")

    async def test_execute_query_http_500_error(self, mock_auth_manager, mocker):
        """Test HTTP 500 server error."""
        client = XrayGraphQLClient(mock_auth_manager)
        mock_session = AsyncMock()
        mock_response = AsyncMock(
            status=500,
            text=AsyncMock(return_value="Internal server error")
        )
        mock_post_context = AsyncMock()
        mock_post_context.__aenter__.return_value = mock_response
        mock_post_context.__aexit__.return_value = None
        mock_session.post = MagicMock(return_value=mock_post_context)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        with pytest.raises(GraphQLError, match="GraphQL request failed with status 500: Internal server error"):
            await client.execute_query("query { test }")

    async def test_execute_query_network_error(self, mock_auth_manager, mocker):
        """Test network connectivity errors."""
        client = XrayGraphQLClient(mock_auth_manager)
        mock_session = AsyncMock()
        
        class MockPostContextError:
            async def __aenter__(self):
                raise aiohttp.ClientError("Connection refused")
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        mock_session.post = MagicMock(return_value=MockPostContextError())
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        with pytest.raises(GraphQLError, match="Network error during GraphQL request: Connection refused"):
            await client.execute_query("query { test }")

    async def test_execute_query_timeout_error(self, mock_auth_manager, mocker):
        """Test request timeout handling."""
        client = XrayGraphQLClient(mock_auth_manager)
        mock_session = AsyncMock()
        
        class MockPostContextTimeout:
            async def __aenter__(self):
                import asyncio
                raise asyncio.TimeoutError("Request timeout")
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        mock_session.post = MagicMock(return_value=MockPostContextTimeout())
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        with pytest.raises(GraphQLError, match="Network error during GraphQL request"):
            await client.execute_query("query { test }")


@pytest.mark.asyncio
@pytest.mark.unit
class TestExecuteQueryEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_execute_query_large_payload(self, mock_auth_manager, mocker):
        """Test handling of large query payload."""
        client = XrayGraphQLClient(mock_auth_manager)
        mock_session = AsyncMock()
        
        # Simulate large response
        large_data = {"data": {"results": [{"id": f"TEST-{i}"} for i in range(1000)]}}
        mock_response = AsyncMock(
            status=200,
            json=AsyncMock(return_value=large_data)
        )
        mock_post_context = AsyncMock()
        mock_post_context.__aenter__.return_value = mock_response
        mock_post_context.__aexit__.return_value = None
        mock_session.post = MagicMock(return_value=mock_post_context)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        result = await client.execute_query("query { getLargeDataset }")
        assert len(result["data"]["results"]) == 1000

    async def test_execute_query_null_variables(self, mock_auth_manager, mocker):
        """Test query with None variables parameter."""
        client = XrayGraphQLClient(mock_auth_manager)
        mock_session = AsyncMock()
        mock_response = AsyncMock(
            status=200,
            json=AsyncMock(return_value={"data": {"test": "ok"}})
        )
        mock_post_context = AsyncMock()
        mock_post_context.__aenter__.return_value = mock_response
        mock_post_context.__aexit__.return_value = None
        mock_session.post = MagicMock(return_value=mock_post_context)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        result = await client.execute_query("query { test }", None)
        
        # Verify variables not included when None
        call_args = mock_session.post.call_args
        payload = call_args[1]["json"]
        assert "variables" not in payload

    async def test_execute_query_empty_variables(self, mock_auth_manager, mocker):
        """Test query with empty variables dict."""
        client = XrayGraphQLClient(mock_auth_manager)
        mock_session = AsyncMock()
        mock_response = AsyncMock(
            status=200,
            json=AsyncMock(return_value={"data": {"test": "ok"}})
        )
        mock_post_context = AsyncMock()
        mock_post_context.__aenter__.return_value = mock_response
        mock_post_context.__aexit__.return_value = None
        mock_session.post = MagicMock(return_value=mock_post_context)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        result = await client.execute_query("query { test }", {})
        
        # Empty dict should not be included
        call_args = mock_session.post.call_args
        payload = call_args[1]["json"]
        assert "variables" not in payload

    async def test_execute_query_malformed_json_response(self, mock_auth_manager, mocker):
        """Test handling of malformed JSON response."""
        client = XrayGraphQLClient(mock_auth_manager)
        mock_session = AsyncMock()
        mock_response = AsyncMock(status=200)
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = AsyncMock(return_value="Not JSON content")
        mock_post_context = AsyncMock()
        mock_post_context.__aenter__.return_value = mock_response
        mock_post_context.__aexit__.return_value = None
        mock_session.post = MagicMock(return_value=mock_post_context)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        with pytest.raises(GraphQLError):
            await client.execute_query("query { test }")

    async def test_execute_query_token_refresh_during_request(self, mock_auth_manager, mocker):
        """Test token refresh triggered by get_valid_token."""
        client = XrayGraphQLClient(mock_auth_manager)
        
        # Simulate token refresh during request
        tokens = ["old_token", "new_token"]
        mock_auth_manager.get_valid_token = AsyncMock(side_effect=tokens)
        
        mock_session = AsyncMock()
        mock_response = AsyncMock(
            status=200,
            json=AsyncMock(return_value={"data": {"test": "ok"}})
        )
        mock_post_context = AsyncMock()
        mock_post_context.__aenter__.return_value = mock_response
        mock_post_context.__aexit__.return_value = None
        mock_session.post = MagicMock(return_value=mock_post_context)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        # Make two requests
        await client.execute_query("query { test1 }")
        await client.execute_query("query { test2 }")
        
        # Verify different tokens were used
        calls = mock_session.post.call_args_list
        assert calls[0][1]["headers"]["Authorization"] == "Bearer old_token"
        assert calls[1][1]["headers"]["Authorization"] == "Bearer new_token"


@pytest.mark.asyncio
@pytest.mark.integration
class TestGraphQLClientIntegration:
    """Integration tests for GraphQL client."""

    async def test_client_with_custom_base_url(self, mocker):
        """Test client with custom server URL."""
        auth = AsyncMock(spec=XrayAuthManager)
        auth.get_valid_token = AsyncMock(return_value="token")
        auth.base_url = "https://jira.company.com"
        
        client = XrayGraphQLClient(auth)
        assert client.endpoint == "https://jira.company.com/api/v2/graphql"
        
        mock_session = AsyncMock()
        mock_response = AsyncMock(
            status=200,
            json=AsyncMock(return_value={"data": {"test": "ok"}})
        )
        mock_post_context = AsyncMock()
        mock_post_context.__aenter__.return_value = mock_response
        mock_post_context.__aexit__.return_value = None
        mock_session.post = MagicMock(return_value=mock_post_context)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        await client.execute_query("query { test }")
        
        # Verify custom endpoint was used
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "https://jira.company.com/api/v2/graphql"

    async def test_concurrent_queries(self, mock_auth_manager, mocker):
        """Test concurrent query execution."""
        client = XrayGraphQLClient(mock_auth_manager)
        
        mock_session = AsyncMock()
        responses = [
            AsyncMock(status=200, json=AsyncMock(return_value={"data": {"test": i}}))
            for i in range(5)
        ]
        mock_post_context = AsyncMock()
        mock_post_context.__aenter__.side_effect = responses
        mock_post_context.__aexit__.return_value = None
        mock_session.post = MagicMock(return_value=mock_post_context)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        # Execute 5 concurrent queries
        import asyncio
        queries = [client.execute_query(f"query {{ test{i} }}") for i in range(5)]
        results = await asyncio.gather(*queries)
        
        # All should succeed with different results
        for i, result in enumerate(results):
            assert result == {"data": {"test": i}}