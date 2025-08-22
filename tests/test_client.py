"""Tests for XrayGraphQLClient."""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import json
from typing import Dict, Any

try:
    from client import XrayGraphQLClient
    from auth.manager import XrayAuthManager
    from exceptions import GraphQLError, AuthenticationError
except ImportError:
    import sys

    sys.path.append("..")
    from client import XrayGraphQLClient
    from auth.manager import XrayAuthManager
    from exceptions import GraphQLError, AuthenticationError


@pytest.fixture
def mock_auth_manager():
    """Create a mock authentication manager."""
    auth_manager = Mock(spec=XrayAuthManager)
    auth_manager.get_valid_token = AsyncMock(return_value="test-token-123")
    auth_manager.base_url = "https://api.example.com"
    return auth_manager


@pytest.fixture
def client(mock_auth_manager):
    """Create a test client instance."""
    return XrayGraphQLClient(auth_manager=mock_auth_manager)


class TestXrayGraphQLClient:
    """Test suite for XrayGraphQLClient."""

    @pytest.mark.asyncio
    async def test_client_initialization(self, mock_auth_manager):
        """Test client initialization with valid parameters."""
        client = XrayGraphQLClient(auth_manager=mock_auth_manager)

        assert client.auth_manager == mock_auth_manager
        assert client.endpoint == "https://api.example.com/api/v2/graphql"

    @pytest.mark.asyncio
    async def test_execute_query_success(self, client, mock_auth_manager):
        """Test successful query execution."""
        query = """
        query GetTest($issueId: String!) {
            getTest(issueId: $issueId) {
                issueId
            }
        }
        """
        variables = {"issueId": "TEST-123"}

        # Mock the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"data": {"getTest": {"issueId": "TEST-123"}}}
        )

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_post_context = AsyncMock()
            mock_post_context.__aenter__.return_value = mock_response
            mock_post_context.__aexit__.return_value = None
            
            mock_session = AsyncMock()
            mock_session.post = MagicMock(return_value=mock_post_context)
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_class.return_value = mock_session

            result = await client.execute_query(query, variables)

            assert result["data"]["getTest"]["issueId"] == "TEST-123"
            mock_auth_manager.get_valid_token.assert_called_once()

            # Verify the request was made correctly
            mock_session.post.assert_called_once()
            call_args = mock_session.post.call_args
            assert call_args[0][0] == client.endpoint
            assert call_args[1]["headers"]["Authorization"] == "Bearer test-token-123"

    @pytest.mark.asyncio
    async def test_execute_query_graphql_error(self, client, mock_auth_manager):
        """Test query execution with GraphQL errors."""
        query = "query { invalid }"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "errors": [
                    {
                        "message": "Field 'invalid' doesn't exist",
                        "extensions": {"code": "FIELD_NOT_FOUND"},
                    }
                ]
            }
        )

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_post_context = AsyncMock()
            mock_post_context.__aenter__.return_value = mock_response
            mock_post_context.__aexit__.return_value = None
            
            mock_session = AsyncMock()
            mock_session.post = MagicMock(return_value=mock_post_context)
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_class.return_value = mock_session

            with pytest.raises(GraphQLError) as exc_info:
                await client.execute_query(query)

            assert "GraphQL errors" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_query_network_error(self, client, mock_auth_manager):
        """Test query execution with network errors."""
        query = "query { test }"

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            
            # Create a context manager that raises on entry
            class MockPostContextError:
                async def __aenter__(self):
                    import aiohttp
                    raise aiohttp.ClientError("Network connection failed")
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None
            
            mock_session.post = MagicMock(return_value=MockPostContextError())
            mock_session_class.return_value = mock_session

            with pytest.raises(GraphQLError) as exc_info:
                await client.execute_query(query)

            assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_query_authentication_error(self, client, mock_auth_manager):
        """Test query execution with authentication errors."""
        query = "query { test }"

        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text = AsyncMock(return_value="Unauthorized")

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_post_context = AsyncMock()
            mock_post_context.__aenter__.return_value = mock_response
            mock_post_context.__aexit__.return_value = None
            
            mock_session = AsyncMock()
            mock_session.post = MagicMock(return_value=mock_post_context)
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_class.return_value = mock_session

            with pytest.raises(GraphQLError) as exc_info:
                await client.execute_query(query)

            assert "401" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_mutation_success(self, client, mock_auth_manager):
        """Test successful mutation execution."""
        mutation = """
        mutation CreateTest($input: TestInput!) {
            createTest(input: $input) {
                test {
                    issueId
                }
            }
        }
        """
        variables = {"input": {"summary": "New test"}}

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"data": {"createTest": {"test": {"issueId": "TEST-124"}}}}
        )

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_post_context = AsyncMock()
            mock_post_context.__aenter__.return_value = mock_response
            mock_post_context.__aexit__.return_value = None
            
            mock_session = AsyncMock()
            mock_session.post = MagicMock(return_value=mock_post_context)
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_class.return_value = mock_session

            result = await client.execute_mutation(mutation, variables)

            assert result["data"]["createTest"]["test"]["issueId"] == "TEST-124"

    @pytest.mark.asyncio
    async def test_execute_query_headers_customization(self, client, mock_auth_manager):
        """Test that custom headers are properly set."""
        query = "query { test }"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"data": {"test": "ok"}})

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_post_context = AsyncMock()
            mock_post_context.__aenter__.return_value = mock_response
            mock_post_context.__aexit__.return_value = None
            
            mock_session = AsyncMock()
            mock_session.post = MagicMock(return_value=mock_post_context)
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_class.return_value = mock_session

            await client.execute_query(query)

            # Verify headers
            call_args = mock_session.post.call_args
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer test-token-123"
            assert headers["Content-Type"] == "application/json"
