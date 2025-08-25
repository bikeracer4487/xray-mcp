"""Tests for TestRunTools class.

Comprehensive test suite covering all CRUD operations for test runs,
including status updates, field updates, and reset functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tools.runs import TestRunTools
from exceptions import GraphQLError, ValidationError


@pytest.fixture
def mock_client():
    """Create a mock GraphQL client."""
    client = MagicMock()
    client.execute_query = AsyncMock()
    client.execute_mutation = AsyncMock()
    return client


@pytest.fixture  
def mock_id_resolver():
    """Create a mock ID resolver."""
    resolver = MagicMock()
    resolver.resolve_multiple_issue_ids = AsyncMock()
    return resolver


@pytest.fixture
def run_tools(mock_client, mock_id_resolver):
    """Create TestRunTools instance with mocked dependencies."""
    tools = TestRunTools(mock_client)
    tools.id_resolver = mock_id_resolver
    return tools


@pytest.mark.asyncio
@pytest.mark.unit
class TestTestRunToolsInit:
    """Test TestRunTools initialization."""
    
    async def test_init_creates_client_and_resolver(self, mock_client):
        """Test that initialization sets up client and ID resolver."""
        tools = TestRunTools(mock_client)
        assert tools.client == mock_client
        assert tools.id_resolver is not None


@pytest.mark.asyncio
@pytest.mark.unit
class TestGetTestRun:
    """Test get_test_run method."""
    
    async def test_get_test_run_success(self, run_tools, mock_client):
        """Test successful test run retrieval by internal ID."""
        mock_client.execute_query.return_value = {
            "data": {
                "getTestRunById": {
                    "id": "12345",
                    "status": {
                        "name": "PASSED",
                        "color": "GREEN",
                        "description": "Test passed"
                    },
                    "gherkin": "Given a test scenario",
                    "scenarioType": "NORMAL",
                    "comment": "Test executed successfully",
                    "startedOn": "2024-01-01T10:00:00Z",
                    "finishedOn": "2024-01-01T10:05:00Z",
                    "test": {"issueId": "101"},
                    "testExecution": {"issueId": "200"},
                    "steps": [
                        {
                            "id": "step1",
                            "action": "Click button",
                            "data": "Login button",
                            "result": "User logged in",
                            "status": {"name": "PASSED", "color": "GREEN"}
                        }
                    ]
                }
            }
        }
        
        result = await run_tools.get_test_run("12345")
        
        mock_client.execute_query.assert_called_once()
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]
        assert variables == {"id": "12345"}
        
        assert result["id"] == "12345"
        assert result["status"]["name"] == "PASSED"
        assert result["test"]["issueId"] == "101"
        assert result["testExecution"]["issueId"] == "200"
        assert len(result["steps"]) == 1
        
    async def test_get_test_run_not_found(self, run_tools, mock_client):
        """Test handling when test run is not found."""
        mock_client.execute_query.return_value = {"data": {}}
        
        result = await run_tools.get_test_run("nonexistent")
        assert result == {}
        
    async def test_get_test_run_graphql_error(self, run_tools, mock_client):
        """Test handling GraphQL errors during retrieval."""
        mock_client.execute_query.side_effect = GraphQLError("Network error")
        
        with pytest.raises(GraphQLError, match="Network error"):
            await run_tools.get_test_run("12345")


@pytest.mark.asyncio
@pytest.mark.unit
class TestGetTestRuns:
    """Test get_test_runs method."""
    
    async def test_get_test_runs_success_no_filters(self, run_tools, mock_client):
        """Test successful test runs retrieval without filters."""
        mock_client.execute_query.return_value = {
            "data": {
                "getTestRuns": {
                    "total": 5,
                    "start": 0,
                    "limit": 100,
                    "results": [
                        {
                            "id": "run1",
                            "status": {"name": "PASSED", "color": "GREEN"},
                            "test": {"issueId": "101"},
                            "testExecution": {"issueId": "200"}
                        },
                        {
                            "id": "run2", 
                            "status": {"name": "FAILED", "color": "RED"},
                            "test": {"issueId": "102"},
                            "testExecution": {"issueId": "201"}
                        }
                    ]
                }
            }
        }
        
        result = await run_tools.get_test_runs()
        
        mock_client.execute_query.assert_called_once()
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]
        assert variables == {"testIssueIds": None, "testExecIssueIds": None, "limit": 100}
        
        assert result["total"] == 5
        assert len(result["results"]) == 2
        assert result["results"][0]["id"] == "run1"
        assert result["results"][1]["id"] == "run2"
        
    async def test_get_test_runs_with_filters(self, run_tools, mock_client, mock_id_resolver):
        """Test successful test runs retrieval with filters."""
        mock_id_resolver.resolve_multiple_issue_ids.side_effect = [
            ["101", "102"],  # test IDs
            ["200", "201"]   # execution IDs
        ]
        
        mock_client.execute_query.return_value = {
            "data": {
                "getTestRuns": {
                    "total": 2,
                    "start": 0,
                    "limit": 50,
                    "results": []
                }
            }
        }
        
        result = await run_tools.get_test_runs(
            test_issue_ids=["TEST-101", "TEST-102"],
            test_exec_issue_ids=["EXEC-200", "EXEC-201"],
            limit=50
        )
        
        assert mock_id_resolver.resolve_multiple_issue_ids.call_count == 2
        mock_client.execute_query.assert_called_once()
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]
        assert variables == {
            "testIssueIds": ["101", "102"],
            "testExecIssueIds": ["200", "201"], 
            "limit": 50
        }
        assert result["total"] == 2
        
    async def test_get_test_runs_limit_validation(self, run_tools):
        """Test validation error for excessive limit."""
        with pytest.raises(ValidationError, match="Limit cannot exceed 100"):
            await run_tools.get_test_runs(limit=150)
        
    async def test_get_test_runs_not_found(self, run_tools, mock_client):
        """Test handling when no test runs are found."""
        mock_client.execute_query.return_value = {"data": {}}
        
        result = await run_tools.get_test_runs()
        assert result == {}


@pytest.mark.asyncio
@pytest.mark.unit
class TestCreateTestRun:
    """Test create_test_run method."""
    
    async def test_create_test_run_success_minimal(self, run_tools, mock_client):
        """Test successful test run creation with minimal parameters."""
        mock_client.execute_query.return_value = {
            "data": {
                "createTestRun": {
                    "testRun": {
                        "issueId": "12345",
                        "jira": {"key": "PROJ-300", "summary": "New Test Run"}
                    },
                    "warnings": []
                }
            }
        }
        
        result = await run_tools.create_test_run(
            project_key="PROJ",
            summary="New Test Run"
        )
        
        mock_client.execute_query.assert_called_once()
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]
        
        expected_jira_data = {
            "fields": {
                "project": {"key": "PROJ"},
                "summary": "New Test Run", 
                "issuetype": {"name": "Test Run"}
            }
        }
        assert variables["jira"] == expected_jira_data
        assert variables["testEnvironments"] == []
        
        assert result["testRun"]["issueId"] == "12345"
        assert result["testRun"]["jira"]["key"] == "PROJ-300"
        
    async def test_create_test_run_success_full(self, run_tools, mock_client):
        """Test successful test run creation with all parameters."""
        mock_client.execute_query.return_value = {
            "data": {
                "createTestRun": {
                    "testRun": {
                        "issueId": "12346",
                        "jira": {"key": "PROJ-301", "summary": "Full Test Run"}
                    },
                    "warnings": ["Some warning"]
                }
            }
        }
        
        result = await run_tools.create_test_run(
            project_key="PROJ",
            summary="Full Test Run",
            test_environments=["Chrome", "Firefox"],
            description="Detailed description"
        )
        
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]
        
        expected_jira_data = {
            "fields": {
                "project": {"key": "PROJ"},
                "summary": "Full Test Run",
                "issuetype": {"name": "Test Run"},
                "description": "Detailed description"
            }
        }
        assert variables["jira"] == expected_jira_data
        assert variables["testEnvironments"] == ["Chrome", "Firefox"]
        assert result["warnings"] == ["Some warning"]
        
    async def test_create_test_run_mutation_not_found(self, run_tools, mock_client):
        """Test handling when createTestRun mutation doesn't exist."""
        mock_client.execute_query.side_effect = GraphQLError(
            "Cannot query field 'createTestRun' on type 'Mutation'"
        )
        
        with pytest.raises(ValidationError, match="createTestRun mutation is not available"):
            await run_tools.create_test_run("PROJ", "Test")
        
    async def test_create_test_run_other_error(self, run_tools, mock_client):
        """Test handling other GraphQL errors during creation."""
        mock_client.execute_query.side_effect = GraphQLError("Some other error")
        
        with pytest.raises(GraphQLError, match="Some other error"):
            await run_tools.create_test_run("PROJ", "Test")
            
    async def test_create_test_run_empty_response(self, run_tools, mock_client):
        """Test handling empty response from creation."""
        mock_client.execute_query.return_value = {"data": {}}
        
        result = await run_tools.create_test_run("PROJ", "Test")
        assert result == {}


@pytest.mark.asyncio
@pytest.mark.unit
class TestUpdateTestRunStatus:
    """Test update_test_run_status method."""
    
    async def test_update_test_run_status_success(self, run_tools, mock_client):
        """Test successful test run status update."""
        mock_client.execute_query.return_value = {"data": {"updateTestRunStatus": None}}
        
        result = await run_tools.update_test_run_status("run123", "PASSED")
        
        mock_client.execute_query.assert_called_once()
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]
        assert variables == {"id": "run123", "status": "PASSED"}
        
        assert result["success"] is True
        assert result["testRunId"] == "run123"
        assert result["status"] == "PASSED"
        
    async def test_update_test_run_status_with_errors(self, run_tools, mock_client):
        """Test status update with errors in response."""
        mock_client.execute_query.return_value = {
            "data": {"updateTestRunStatus": None},
            "errors": [{"message": "Some error"}]
        }
        
        result = await run_tools.update_test_run_status("run123", "FAILED")
        
        assert result["success"] is False
        assert result["testRunId"] == "run123"
        assert result["status"] == "FAILED"
        
    async def test_update_test_run_status_graphql_error(self, run_tools, mock_client):
        """Test handling GraphQL errors during status update."""
        mock_client.execute_query.side_effect = GraphQLError("Network error")
        
        with pytest.raises(GraphQLError, match="Network error"):
            await run_tools.update_test_run_status("run123", "PASSED")


@pytest.mark.asyncio
@pytest.mark.unit
class TestUpdateTestRun:
    """Test update_test_run method."""
    
    async def test_update_test_run_success(self, run_tools, mock_client):
        """Test successful test run update with multiple fields."""
        mock_client.execute_query.return_value = {
            "data": {
                "updateTestRun": {
                    "warnings": ["Field updated"]
                }
            }
        }
        
        result = await run_tools.update_test_run(
            test_run_id="run123",
            comment="Test completed",
            started_on="2024-01-01T10:00:00Z",
            finished_on="2024-01-01T10:05:00Z",
            assignee_id="user1",
            executed_by_id="user2"
        )
        
        mock_client.execute_query.assert_called_once()
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]
        assert variables == {
            "id": "run123",
            "comment": "Test completed", 
            "startedOn": "2024-01-01T10:00:00Z",
            "finishedOn": "2024-01-01T10:05:00Z",
            "assigneeId": "user1",
            "executedById": "user2"
        }
        
        assert result["success"] is True
        assert result["testRunId"] == "run123"
        assert result["warnings"] == ["Field updated"]
        
    async def test_update_test_run_minimal(self, run_tools, mock_client):
        """Test test run update with minimal parameters."""
        mock_client.execute_query.return_value = {
            "data": {"updateTestRun": {"warnings": []}}
        }
        
        result = await run_tools.update_test_run("run123", comment="Updated")
        
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]
        assert variables["id"] == "run123"
        assert variables["comment"] == "Updated"
        assert variables["startedOn"] is None
        assert variables["finishedOn"] is None
        assert result["warnings"] == []
        
    async def test_update_test_run_with_errors(self, run_tools, mock_client):
        """Test update with errors in response."""
        mock_client.execute_query.return_value = {
            "data": {"updateTestRun": {"warnings": []}},
            "errors": [{"message": "Update failed"}]
        }
        
        result = await run_tools.update_test_run("run123")
        assert result["success"] is False
        
    async def test_update_test_run_empty_response(self, run_tools, mock_client):
        """Test handling empty response from update."""
        mock_client.execute_query.return_value = {"data": {}}
        
        result = await run_tools.update_test_run("run123")
        assert result["warnings"] == []
        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.unit
class TestResetTestRun:
    """Test reset_test_run method."""
    
    async def test_reset_test_run_success(self, run_tools, mock_client):
        """Test successful test run reset."""
        mock_client.execute_query.return_value = {"data": {"resetTestRun": None}}
        
        result = await run_tools.reset_test_run("run123")
        
        mock_client.execute_query.assert_called_once()
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]
        assert variables == {"id": "run123"}
        
        assert result["success"] is True
        assert result["resetTestRunId"] == "run123"
        
    async def test_reset_test_run_with_errors(self, run_tools, mock_client):
        """Test reset with errors in response."""
        mock_client.execute_query.return_value = {
            "data": {"resetTestRun": None},
            "errors": [{"message": "Reset failed"}]
        }
        
        result = await run_tools.reset_test_run("run123")
        assert result["success"] is False
        assert result["resetTestRunId"] == "run123"
        
    async def test_reset_test_run_graphql_error(self, run_tools, mock_client):
        """Test handling GraphQL errors during reset."""
        mock_client.execute_query.side_effect = GraphQLError("Network error")
        
        with pytest.raises(GraphQLError, match="Network error"):
            await run_tools.reset_test_run("run123")