"""Integration tests for Xray MCP Server."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import json
from typing import Dict, Any

try:
    from main import create_server
    from client import XrayGraphQLClient
    from auth.manager import XrayAuthManager
    from tools.tests import TestTools
    from tools.executions import TestExecutionTools
    from tools.utils import UtilityTools
except ImportError:
    import sys

    sys.path.append("..")
    from main import create_server
    from client import XrayGraphQLClient
    from auth.manager import XrayAuthManager
    from tools.tests import TestTools
    from tools.executions import TestExecutionTools
    from tools.utils import UtilityTools


@pytest.mark.integration
class TestServerIntegration:
    """Integration tests for the MCP server."""

    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test that server initializes correctly with all tools."""
        with patch.dict(
            "os.environ",
            {"XRAY_CLIENT_ID": "test-client", "XRAY_CLIENT_SECRET": "test-secret"},
        ):
            server = await create_server()

            # Verify server has all expected tools
            tool_names = [tool.name for tool in server.tools]

            expected_tools = [
                "get_test",
                "get_tests",
                "create_test",
                "delete_test",
                "get_test_execution",
                "get_test_executions",
                "create_test_execution",
                "execute_jql_query",
                "validate_connection",
            ]

            for tool_name in expected_tools:
                assert any(
                    tool_name in name for name in tool_names
                ), f"Tool {tool_name} not found in server"

    @pytest.mark.asyncio
    async def test_end_to_end_test_creation_and_execution(self):
        """Test complete workflow: create test, create execution, add test to execution."""
        # Mock the authentication and client
        mock_auth = Mock(spec=XrayAuthManager)
        mock_auth.get_valid_token = AsyncMock(return_value="test-token")

        mock_client = Mock(spec=XrayGraphQLClient)

        # Setup test tools
        test_tools = TestTools(mock_client)
        exec_tools = TestExecutionTools(mock_client)

        # Step 1: Create a test
        mock_client.execute_mutation = AsyncMock(
            return_value={
                "data": {
                    "createTest": {
                        "test": {
                            "issueId": "TEST-301",
                            "testType": {"name": "Manual"},
                            "jira": {"key": "TEST-301"},
                        },
                        "warnings": [],
                    }
                }
            }
        )

        test_result = await test_tools.create_test(
            project_key="TEST",
            summary="Integration test case",
            test_type="Manual",
            steps=[{"action": "Step 1", "result": "Expected 1"}],
        )

        assert test_result["test"]["issueId"] == "TEST-301"

        # Step 2: Create a test execution
        mock_client.execute_mutation = AsyncMock(
            return_value={
                "data": {
                    "createTestExecution": {
                        "testExecution": {
                            "issueId": "EXEC-301",
                            "jira": {"key": "EXEC-301"},
                        },
                        "warnings": [],
                        "createdTestEnvironments": [],
                    }
                }
            }
        )

        exec_result = await exec_tools.create_test_execution(
            project_key="TEST",
            summary="Integration test execution",
            test_issue_ids=["TEST-301"],
        )

        assert exec_result["testExecution"]["issueId"] == "EXEC-301"

    @pytest.mark.asyncio
    async def test_jql_validation_across_tools(self):
        """Test that JQL validation works consistently across different tools."""
        mock_auth = Mock(spec=XrayAuthManager)
        mock_auth.get_valid_token = AsyncMock(return_value="test-token")

        mock_client = Mock(spec=XrayGraphQLClient)
        mock_client.execute_query = AsyncMock(
            return_value={"data": {"getTests": {"total": 0, "results": []}}}
        )

        # Test with test tools
        test_tools = TestTools(mock_client)
        exec_tools = TestExecutionTools(mock_client)
        util_tools = UtilityTools(mock_client)

        valid_jql = 'project = "TEST" AND status = "Done"'

        with patch("validators.jql_validator.validate_jql") as mock_validate:
            mock_validate.return_value = valid_jql

            # All tools should validate JQL the same way
            await test_tools.get_tests(jql=valid_jql)
            await exec_tools.get_test_executions(jql=valid_jql)
            await util_tools.execute_jql_query(jql=valid_jql)

            # Verify validation was called for each
            assert mock_validate.call_count == 3

    @pytest.mark.asyncio
    async def test_error_propagation_through_layers(self):
        """Test that errors propagate correctly through all layers."""
        mock_auth = Mock(spec=XrayAuthManager)
        mock_auth.get_valid_token = AsyncMock(return_value="test-token")

        mock_client = Mock(spec=XrayGraphQLClient)
        mock_client.execute_query = AsyncMock(side_effect=Exception("Network error"))

        test_tools = TestTools(mock_client)

        # Error should propagate with proper context
        with pytest.raises(Exception) as exc_info:
            await test_tools.get_test("TEST-123")

        assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_connection_validation_workflow(self):
        """Test the connection validation workflow."""
        mock_auth = Mock(spec=XrayAuthManager)
        mock_client = Mock(spec=XrayGraphQLClient)

        util_tools = UtilityTools(mock_client)

        # Test successful connection
        mock_client.execute_query = AsyncMock(
            return_value={"data": {"getTests": {"total": 10}}}
        )

        result = await util_tools.validate_connection()
        assert result["status"] == "connected"
        assert result["authenticated"] is True

        # Test failed connection
        mock_client.execute_query = AsyncMock(side_effect=Exception("Auth failed"))

        result = await util_tools.validate_connection()
        assert result["status"] == "error"
        assert result["authenticated"] is False
        assert "Auth failed" in result["message"]


@pytest.mark.integration
class TestAbstractionLayerIntegration:
    """Test the abstraction layer integration."""

    @pytest.mark.asyncio
    async def test_repository_pattern_integration(self):
        """Test that repository pattern works with actual tools."""
        from abstractions.repository import Repository

        mock_client = Mock(spec=XrayGraphQLClient)
        mock_client.execute_query = AsyncMock(
            return_value={"data": {"getTest": {"issueId": "TEST-123"}}}
        )

        repo = Repository(mock_client)

        # Test data fetching through repository
        result = await repo.fetch_data(
            "query { getTest(issueId: $id) { issueId } }", {"id": "TEST-123"}
        )

        assert result["getTest"]["issueId"] == "TEST-123"

    @pytest.mark.asyncio
    async def test_error_handler_decorator_integration(self):
        """Test error handler decorator with real async functions."""
        from abstractions.decorators import async_error_handler

        @async_error_handler(operation="test_operation")
        async def failing_function():
            raise ValueError("Test error")

        result = await failing_function()

        assert result["error"] is True
        assert result["error_code"] == "VAL_001"
        assert "Test error" in result["message"]
        assert result["context"]["operation"] == "test_operation"

    @pytest.mark.asyncio
    async def test_validation_decorator_integration(self):
        """Test validation decorator with real functions."""
        from abstractions.decorators import validate_required

        @validate_required(["name", "project"])
        async def create_something(name: str, project: str, optional: str = None):
            return {"name": name, "project": project, "optional": optional}

        # Should work with all required params
        result = await create_something(name="Test", project="PROJ")
        assert result["name"] == "Test"

        # Should fail with missing required param
        with pytest.raises(ValueError) as exc_info:
            await create_something(name="Test")

        assert "project" in str(exc_info.value)
