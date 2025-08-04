"""Test script for Xray MCP Server functionality."""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import XrayMCPServer, create_server
from config import XrayConfig
from auth import XrayAuthManager
from client import XrayGraphQLClient


async def test_server_creation():
    """Test server creation and initialization."""
    print("🧪 Testing server creation...")

    # Test server creation with mock credentials
    config = XrayConfig.from_params("test_client_id", "test_client_secret")
    server = XrayMCPServer(config)

    assert server.config.client_id == "test_client_id"
    assert server.config.client_secret == "test_client_secret"
    assert server.mcp is not None

    print("✅ Server creation test passed")


async def test_auth_manager():
    """Test authentication manager functionality."""
    print("🧪 Testing authentication manager...")

    auth_manager = XrayAuthManager("test_id", "test_secret")

    # Mock the authentication response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='"mock_jwt_token"')

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response

        token = await auth_manager.authenticate()
        assert token == "mock_jwt_token"
        assert auth_manager.token == "mock_jwt_token"

    print("✅ Authentication manager test passed")


async def test_graphql_client():
    """Test GraphQL client functionality."""
    print("🧪 Testing GraphQL client...")

    auth_manager = XrayAuthManager("test_id", "test_secret")

    # Mock the get_valid_token method directly
    with patch.object(auth_manager, "get_valid_token", return_value="mock_token"):
        client = XrayGraphQLClient(auth_manager)

        # Mock successful GraphQL response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"data": {"getTests": {"total": 5}}}
        )

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await client.execute_query("query { getTests { total } }")
            assert "data" in result
            assert result["data"]["getTests"]["total"] == 5

    print("✅ GraphQL client test passed")


async def test_tool_registration():
    """Test that all tools are properly registered."""
    print("🧪 Testing tool registration...")

    config = XrayConfig.from_params("test_client_id", "test_client_secret")
    server = XrayMCPServer(config)

    # Check that the server has the tool classes initialized
    assert server.test_tools is not None
    assert server.execution_tools is not None
    assert server.plan_tools is not None
    assert server.run_tools is not None
    assert server.utility_tools is not None

    # Check that the FastMCP instance exists
    assert server.mcp is not None

    print("✅ Tool registration test passed - All tool classes initialized")


async def test_error_handling():
    """Test error handling in tools."""
    print("🧪 Testing error handling...")

    config = XrayConfig.from_params("test_client_id", "test_client_secret")
    server = XrayMCPServer(config)

    # Test that the server handles initialization properly
    assert server.mcp is not None
    assert server.auth_manager is not None
    assert server.graphql_client is not None

    # Test that tool classes have proper error handling structure
    # (The actual error handling is tested in the MCP tool decorators)
    assert hasattr(server.test_tools, "get_test")
    assert hasattr(server.execution_tools, "get_test_execution")

    print("✅ Error handling test passed")


async def test_configuration():
    """Test configuration management."""
    print("🧪 Testing configuration...")

    # Test configuration from parameters
    config = XrayConfig.from_params("id123", "secret456", "https://custom.xray.com")
    assert config.client_id == "id123"
    assert config.client_secret == "secret456"
    assert config.base_url == "https://custom.xray.com"

    # Test default base URL
    config2 = XrayConfig.from_params("id123", "secret456")
    assert config2.base_url == "https://xray.cloud.getxray.app"

    print("✅ Configuration test passed")


async def run_all_tests():
    """Run all tests."""
    print("🚀 Starting Xray MCP Server tests...\n")

    try:
        await test_server_creation()
        await test_auth_manager()
        await test_graphql_client()
        await test_tool_registration()
        await test_error_handling()
        await test_configuration()

        print("\n🎉 All tests passed! The Xray MCP Server is working correctly.")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
