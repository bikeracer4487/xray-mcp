"""Tests for UtilityTools class."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

try:
    from tools.utils import UtilityTools
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError
except ImportError:
    import sys

    sys.path.append("..")
    from tools.utils import UtilityTools
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError


@pytest.fixture
def mock_client():
    """Create a mock GraphQL client."""
    client = Mock(spec=XrayGraphQLClient)
    client.execute_query = AsyncMock()
    return client


@pytest.fixture
def utility_tools(mock_client):
    """Create UtilityTools instance with mock client."""
    return UtilityTools(mock_client)


class TestUtilityTools:
    """Test suite for UtilityTools class."""

    @pytest.mark.asyncio
    async def test_execute_jql_query_for_tests(self, utility_tools, mock_client):
        """Test executing JQL query for test entities."""
        mock_client.execute_query.return_value = {
            "data": {
                "getTests": {
                    "total": 10,
                    "start": 0,
                    "limit": 100,
                    "results": [
                        {
                            "issueId": "TEST-101",
                            "testType": {"name": "Manual"},
                            "jira": {
                                "key": "TEST-101",
                                "summary": "Login test",
                                "status": {"name": "Done"},
                            },
                        }
                    ],
                }
            }
        }

        with patch("tools.utils.validate_jql") as mock_validate:
            mock_validate.return_value = 'project = "TEST" AND status = "Done"'

            result = await utility_tools.execute_jql_query(
                jql='project = "TEST" AND status = "Done"',
                entity_type="test",
                limit=100,
            )

            assert result["total"] == 10
            assert result["results"][0]["issueId"] == "TEST-101"
            assert result["results"][0]["jira"]["status"]["name"] == "Done"

            # Verify JQL was validated
            mock_validate.assert_called_once_with(
                'project = "TEST" AND status = "Done"'
            )

            # Verify correct query was executed
            args = mock_client.execute_query.call_args
            assert "getTests" in args[0][0]
            assert args[0][1]["jql"] == 'project = "TEST" AND status = "Done"'
            assert args[0][1]["limit"] == 100

    @pytest.mark.asyncio
    async def test_execute_jql_query_for_test_executions(
        self, utility_tools, mock_client
    ):
        """Test executing JQL query for test execution entities."""
        mock_client.execute_query.return_value = {
            "data": {
                "getTestExecutions": {
                    "total": 5,
                    "start": 0,
                    "limit": 50,
                    "results": [
                        {
                            "issueId": "EXEC-201",
                            "jira": {
                                "key": "EXEC-201",
                                "summary": "Sprint 10 Execution",
                                "status": {"name": "In Progress"},
                            },
                        }
                    ],
                }
            }
        }

        with patch("tools.utils.validate_jql") as mock_validate:
            mock_validate.return_value = 'project = "TEST" AND type = "Test Execution"'

            result = await utility_tools.execute_jql_query(
                jql='project = "TEST" AND type = "Test Execution"',
                entity_type="testexecution",
                limit=50,
            )

            assert result["total"] == 5
            assert result["results"][0]["issueId"] == "EXEC-201"
            assert result["results"][0]["jira"]["summary"] == "Sprint 10 Execution"

            # Verify correct query was executed
            args = mock_client.execute_query.call_args
            assert "getTestExecutions" in args[0][0]

    @pytest.mark.asyncio
    async def test_execute_jql_query_case_insensitive_entity_type(
        self, utility_tools, mock_client
    ):
        """Test that entity type is case insensitive."""
        mock_client.execute_query.return_value = {
            "data": {"getTests": {"total": 0, "results": []}}
        }

        with patch("tools.utils.validate_jql") as mock_validate:
            mock_validate.return_value = "project = TEST"

            # Test various case combinations
            for entity_type in ["TEST", "Test", "TeSt"]:
                await utility_tools.execute_jql_query(
                    jql="project = TEST", entity_type=entity_type
                )

            # All should result in getTests query
            assert mock_client.execute_query.call_count == 3
            for call in mock_client.execute_query.call_args_list:
                assert "getTests" in call[0][0]

    @pytest.mark.asyncio
    async def test_execute_jql_query_unsupported_entity_type(self, utility_tools):
        """Test error handling for unsupported entity types."""
        with pytest.raises(GraphQLError) as exc_info:
            await utility_tools.execute_jql_query(
                jql="project = TEST", entity_type="unsupported"
            )

        assert "Unsupported entity type: unsupported" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_jql_query_validation_error(self, utility_tools):
        """Test that validation errors are properly propagated."""
        with patch("tools.utils.validate_jql") as mock_validate:
            mock_validate.side_effect = ValidationError(
                "JQL contains dangerous patterns"
            )

            with pytest.raises(ValidationError) as exc_info:
                await utility_tools.execute_jql_query(
                    jql="project = TEST; DROP TABLE users;", entity_type="test"
                )

            assert "dangerous patterns" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_connection_success(self, utility_tools, mock_client):
        """Test successful connection validation."""
        mock_client.execute_query.return_value = {"data": {"getTests": {"total": 42}}}

        result = await utility_tools.validate_connection()

        assert result["status"] == "connected"
        assert result["authenticated"] is True
        assert "Successfully connected" in result["message"]

        # Verify minimal query was executed
        args = mock_client.execute_query.call_args
        assert "getTests(limit: 1)" in args[0][0]

    @pytest.mark.asyncio
    async def test_validate_connection_no_data(self, utility_tools, mock_client):
        """Test connection validation when no data is returned."""
        mock_client.execute_query.return_value = {
            "errors": [{"message": "Unauthorized"}]
        }

        result = await utility_tools.validate_connection()

        assert result["status"] == "error"
        assert result["authenticated"] is False
        assert "Failed to validate connection" in result["message"]

    @pytest.mark.asyncio
    async def test_validate_connection_exception(self, utility_tools, mock_client):
        """Test connection validation with network exception."""
        mock_client.execute_query.side_effect = Exception("Network timeout")

        result = await utility_tools.validate_connection()

        assert result["status"] == "error"
        assert result["authenticated"] is False
        assert "Network timeout" in result["message"]

    @pytest.mark.asyncio
    async def test_execute_test_jql_error_handling(self, utility_tools, mock_client):
        """Test error handling in _execute_test_jql."""
        mock_client.execute_query.return_value = {
            "errors": [{"message": "Query failed"}]
        }

        with patch("tools.utils.validate_jql") as mock_validate:
            mock_validate.return_value = "project = TEST"

            with pytest.raises(GraphQLError) as exc_info:
                await utility_tools.execute_jql_query(
                    jql="project = TEST", entity_type="test"
                )

            assert "Failed to execute JQL query for tests" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_test_execution_jql_error_handling(
        self, utility_tools, mock_client
    ):
        """Test error handling in _execute_test_execution_jql."""
        mock_client.execute_query.return_value = {
            "errors": [{"message": "Query failed"}]
        }

        with patch("tools.utils.validate_jql") as mock_validate:
            mock_validate.return_value = "project = TEST"

            with pytest.raises(GraphQLError) as exc_info:
                await utility_tools.execute_jql_query(
                    jql="project = TEST", entity_type="testexecution"
                )

            assert "Failed to execute JQL query for test executions" in str(
                exc_info.value
            )
