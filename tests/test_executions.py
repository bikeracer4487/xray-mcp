"""Tests for TestExecutionTools class.

Comprehensive test suite covering all CRUD operations for test executions,
including test and environment management functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tools.executions import TestExecutionTools
from exceptions import GraphQLError, ValidationError
from utils.id_resolver import ResourceType


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
    resolver.resolve_issue_id = AsyncMock()
    resolver.resolve_multiple_issue_ids = AsyncMock()
    return resolver


@pytest.fixture
def execution_tools(mock_client, mock_id_resolver):
    """Create TestExecutionTools instance with mocked dependencies."""
    tools = TestExecutionTools(mock_client)
    tools.id_resolver = mock_id_resolver
    return tools


@pytest.mark.asyncio
@pytest.mark.unit
class TestTestExecutionToolsInit:
    """Test TestExecutionTools initialization."""
    
    async def test_init_creates_client_and_resolver(self, mock_client):
        """Test that initialization sets up client and ID resolver."""
        tools = TestExecutionTools(mock_client)
        assert tools.client == mock_client
        assert tools.id_resolver is not None


@pytest.mark.asyncio
@pytest.mark.unit
class TestGetTestExecution:
    """Test get_test_execution method."""
    
    async def test_get_test_execution_success(self, execution_tools, mock_client, mock_id_resolver):
        """Test successful test execution retrieval."""
        # Setup mocks
        mock_id_resolver.resolve_issue_id.return_value = "12345"
        mock_client.execute_query.return_value = {
            "data": {
                "getTestExecution": {
                    "issueId": "12345",
                    "tests": {
                        "total": 5,
                        "start": 0,
                        "limit": 100,
                        "results": [
                            {"issueId": "101", "testType": {"name": "Manual"}},
                            {"issueId": "102", "testType": {"name": "Automated"}}
                        ]
                    },
                    "jira": {
                        "key": "PROJ-123",
                        "summary": "Sprint 1 Execution",
                        "status": "Open"
                    }
                }
            }
        }
        
        result = await execution_tools.get_test_execution("PROJ-123")
        
        # Verify ID resolution
        mock_id_resolver.resolve_issue_id.assert_called_once_with(
            "PROJ-123", ResourceType.TEST_EXECUTION
        )
        
        # Verify query execution
        mock_client.execute_query.assert_called_once()
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]
        assert variables == {"issueId": "12345"}
        
        # Verify result
        assert result["issueId"] == "12345"
        assert result["tests"]["total"] == 5
        assert result["jira"]["key"] == "PROJ-123"
        
    async def test_get_test_execution_not_found(self, execution_tools, mock_client, mock_id_resolver):
        """Test handling when test execution is not found."""
        mock_id_resolver.resolve_issue_id.return_value = "12345"
        mock_client.execute_query.return_value = {"data": {}}
        
        with pytest.raises(GraphQLError, match="Failed to retrieve test execution PROJ-123"):
            await execution_tools.get_test_execution("PROJ-123")
        
    async def test_get_test_execution_graphql_error(self, execution_tools, mock_client, mock_id_resolver):
        """Test handling GraphQL errors during retrieval."""
        mock_id_resolver.resolve_issue_id.return_value = "12345"
        mock_client.execute_query.side_effect = GraphQLError("Network error")
        
        with pytest.raises(GraphQLError, match="Network error"):
            await execution_tools.get_test_execution("PROJ-123")


@pytest.mark.asyncio
@pytest.mark.unit
class TestGetTestExecutions:
    """Test get_test_executions method."""
    
    async def test_get_test_executions_success_no_jql(self, execution_tools, mock_client):
        """Test successful test executions retrieval without JQL."""
        mock_client.execute_query.return_value = {
            "data": {
                "getTestExecutions": {
                    "total": 10,
                    "start": 0,
                    "limit": 100,
                    "results": [
                        {
                            "issueId": "12345",
                            "tests": {"total": 3},
                            "jira": {"key": "PROJ-123", "summary": "Sprint 1"}
                        },
                        {
                            "issueId": "12346",
                            "tests": {"total": 7},
                            "jira": {"key": "PROJ-124", "summary": "Sprint 2"}
                        }
                    ]
                }
            }
        }
        
        result = await execution_tools.get_test_executions()
        
        mock_client.execute_query.assert_called_once()
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]
        assert variables == {"jql": None, "limit": 100}
        
        assert result["total"] == 10
        assert len(result["results"]) == 2
        assert result["results"][0]["jira"]["key"] == "PROJ-123"
        
    async def test_get_test_executions_with_jql(self, execution_tools, mock_client):
        """Test successful test executions retrieval with JQL."""
        jql_query = 'project = "PROJ" AND status = "Open"'
        
        with patch('tools.executions.validate_jql', return_value=jql_query) as mock_validate:
            mock_client.execute_query.return_value = {
                "data": {
                    "getTestExecutions": {
                        "total": 3,
                        "start": 0,
                        "limit": 50,
                        "results": []
                    }
                }
            }
            
            result = await execution_tools.get_test_executions(jql=jql_query, limit=50)
            
            mock_validate.assert_called_once_with(jql_query)
            mock_client.execute_query.assert_called_once()
            call_args = mock_client.execute_query.call_args
            variables = call_args[0][1]
            assert variables == {"jql": jql_query, "limit": 50}
            assert result["total"] == 3
        
    async def test_get_test_executions_limit_validation(self, execution_tools):
        """Test validation error for excessive limit."""
        with pytest.raises(ValidationError, match="Limit cannot exceed 100"):
            await execution_tools.get_test_executions(limit=150)
        
    async def test_get_test_executions_not_found(self, execution_tools, mock_client):
        """Test handling when no test executions are found."""
        mock_client.execute_query.return_value = {"data": {}}
        
        with pytest.raises(GraphQLError, match="Failed to retrieve test executions"):
            await execution_tools.get_test_executions()


@pytest.mark.asyncio
@pytest.mark.unit
class TestCreateTestExecution:
    """Test create_test_execution method."""
    
    async def test_create_test_execution_success_minimal(self, execution_tools, mock_client):
        """Test successful test execution creation with minimal parameters."""
        mock_client.execute_mutation.return_value = {
            "data": {
                "createTestExecution": {
                    "testExecution": {
                        "issueId": "12345",
                        "jira": {"key": "PROJ-200", "summary": "New Execution"}
                    },
                    "warnings": [],
                    "createdTestEnvironments": []
                }
            }
        }
        
        result = await execution_tools.create_test_execution(
            project_key="PROJ",
            summary="New Execution"
        )
        
        mock_client.execute_mutation.assert_called_once()
        call_args = mock_client.execute_mutation.call_args
        variables = call_args[0][1]
        
        assert variables["testIssueIds"] == []
        assert variables["testEnvironments"] == []
        assert variables["jira"]["fields"]["summary"] == "New Execution"
        assert variables["jira"]["fields"]["project"]["key"] == "PROJ"
        
        assert result["testExecution"]["issueId"] == "12345"
        assert result["testExecution"]["jira"]["key"] == "PROJ-200"
        
    async def test_create_test_execution_success_full(self, execution_tools, mock_client):
        """Test successful test execution creation with all parameters."""
        mock_client.execute_mutation.return_value = {
            "data": {
                "createTestExecution": {
                    "testExecution": {
                        "issueId": "12345",
                        "jira": {"key": "PROJ-201", "summary": "Full Execution"}
                    },
                    "warnings": ["Some warning"],
                    "createdTestEnvironments": ["Chrome", "Firefox"]
                }
            }
        }
        
        result = await execution_tools.create_test_execution(
            project_key="PROJ",
            summary="Full Execution",
            test_issue_ids=["101", "102"],
            test_environments=["Chrome", "Firefox"],
            description="Detailed description"
        )
        
        call_args = mock_client.execute_mutation.call_args
        variables = call_args[0][1]
        
        assert variables["testIssueIds"] == ["101", "102"]
        assert variables["testEnvironments"] == ["Chrome", "Firefox"]
        assert variables["jira"]["fields"]["description"] == "Detailed description"
        
        assert len(result["createdTestEnvironments"]) == 2
        assert result["warnings"] == ["Some warning"]
        
    async def test_create_test_execution_failure(self, execution_tools, mock_client):
        """Test handling creation failure."""
        mock_client.execute_mutation.return_value = {"data": {}}
        
        with pytest.raises(GraphQLError, match="Failed to create test execution"):
            await execution_tools.create_test_execution("PROJ", "Test")


@pytest.mark.asyncio
@pytest.mark.unit
class TestDeleteTestExecution:
    """Test delete_test_execution method."""
    
    async def test_delete_test_execution_success(self, execution_tools, mock_client, mock_id_resolver):
        """Test successful test execution deletion."""
        mock_id_resolver.resolve_issue_id.return_value = "12345"
        mock_client.execute_mutation.return_value = {
            "data": {"deleteTestExecution": True}
        }
        
        result = await execution_tools.delete_test_execution("PROJ-123")
        
        mock_id_resolver.resolve_issue_id.assert_called_once_with(
            "PROJ-123", ResourceType.TEST_EXECUTION
        )
        mock_client.execute_mutation.assert_called_once()
        call_args = mock_client.execute_mutation.call_args
        variables = call_args[0][1]
        assert variables == {"issueId": "12345"}
        
        assert result["success"] is True
        assert result["issueId"] == "PROJ-123"
        
    async def test_delete_test_execution_failure(self, execution_tools, mock_client, mock_id_resolver):
        """Test handling deletion failure."""
        mock_id_resolver.resolve_issue_id.return_value = "12345"
        mock_client.execute_mutation.return_value = {"data": {}}
        
        with pytest.raises(GraphQLError, match="Failed to delete test execution PROJ-123"):
            await execution_tools.delete_test_execution("PROJ-123")


@pytest.mark.asyncio
@pytest.mark.unit
class TestAddTestsToExecution:
    """Test add_tests_to_execution method."""
    
    async def test_add_tests_to_execution_success(self, execution_tools, mock_client, mock_id_resolver):
        """Test successful addition of tests to execution."""
        mock_id_resolver.resolve_issue_id.return_value = "12345"
        mock_id_resolver.resolve_multiple_issue_ids.return_value = ["101", "102"]
        mock_client.execute_mutation.return_value = {
            "data": {
                "addTestsToTestExecution": {
                    "addedTests": ["101", "102"],
                    "warning": ""
                }
            }
        }
        
        result = await execution_tools.add_tests_to_execution(
            "PROJ-123", ["TEST-101", "TEST-102"]
        )
        
        mock_id_resolver.resolve_issue_id.assert_called_once_with(
            "PROJ-123", ResourceType.TEST_EXECUTION
        )
        mock_id_resolver.resolve_multiple_issue_ids.assert_called_once_with(
            ["TEST-101", "TEST-102"], ResourceType.TEST
        )
        
        mock_client.execute_mutation.assert_called_once()
        call_args = mock_client.execute_mutation.call_args
        variables = call_args[0][1]
        assert variables == {"issueId": "12345", "testIssueIds": ["101", "102"]}
        
        assert result["addedTests"] == ["101", "102"]
        assert result["warning"] == ""
        
    async def test_add_tests_to_execution_failure(self, execution_tools, mock_client, mock_id_resolver):
        """Test handling failure when adding tests."""
        mock_id_resolver.resolve_issue_id.return_value = "12345"
        mock_id_resolver.resolve_multiple_issue_ids.return_value = ["101"]
        mock_client.execute_mutation.return_value = {"data": {}}
        
        with pytest.raises(GraphQLError, match="Failed to add tests to execution PROJ-123"):
            await execution_tools.add_tests_to_execution("PROJ-123", ["TEST-101"])


@pytest.mark.asyncio
@pytest.mark.unit  
class TestRemoveTestsFromExecution:
    """Test remove_tests_from_execution method."""
    
    async def test_remove_tests_from_execution_success(self, execution_tools, mock_client, mock_id_resolver):
        """Test successful removal of tests from execution."""
        mock_id_resolver.resolve_issue_id.return_value = "12345"
        mock_id_resolver.resolve_multiple_issue_ids.return_value = ["101", "102"]
        mock_client.execute_mutation.return_value = {
            "data": {"removeTestsFromTestExecution": True}
        }
        
        result = await execution_tools.remove_tests_from_execution(
            "PROJ-123", ["TEST-101", "TEST-102"]
        )
        
        mock_id_resolver.resolve_issue_id.assert_called_once_with(
            "PROJ-123", ResourceType.TEST_EXECUTION
        )
        mock_id_resolver.resolve_multiple_issue_ids.assert_called_once_with(
            ["TEST-101", "TEST-102"], ResourceType.TEST
        )
        
        mock_client.execute_mutation.assert_called_once()
        call_args = mock_client.execute_mutation.call_args
        variables = call_args[0][1]
        assert variables == {"issueId": "12345", "testIssueIds": ["101", "102"]}
        
        assert result["success"] is True
        assert result["executionId"] == "PROJ-123"
        
    async def test_remove_tests_from_execution_failure(self, execution_tools, mock_client, mock_id_resolver):
        """Test handling failure when removing tests."""
        mock_id_resolver.resolve_issue_id.return_value = "12345"
        mock_id_resolver.resolve_multiple_issue_ids.return_value = ["101"]
        mock_client.execute_mutation.return_value = {"data": {}}
        
        with pytest.raises(GraphQLError, match="Failed to remove tests from execution PROJ-123"):
            await execution_tools.remove_tests_from_execution("PROJ-123", ["TEST-101"])


@pytest.mark.asyncio
@pytest.mark.unit
class TestAddTestEnvironments:
    """Test add_test_environments method."""
    
    async def test_add_test_environments_success(self, execution_tools, mock_client, mock_id_resolver):
        """Test successful addition of test environments."""
        mock_id_resolver.resolve_issue_id.return_value = "12345"
        mock_client.execute_mutation.return_value = {
            "data": {
                "addTestEnvironmentsToTestExecution": {
                    "associatedTestEnvironments": ["Chrome", "Firefox", "Safari"],
                    "createdTestEnvironments": ["Safari"]
                }
            }
        }
        
        result = await execution_tools.add_test_environments(
            "PROJ-123", ["Chrome", "Firefox", "Safari"]
        )
        
        mock_id_resolver.resolve_issue_id.assert_called_once_with(
            "PROJ-123", ResourceType.TEST_EXECUTION
        )
        
        mock_client.execute_mutation.assert_called_once()
        call_args = mock_client.execute_mutation.call_args
        variables = call_args[0][1]
        assert variables == {
            "issueId": "12345", 
            "testEnvironments": ["Chrome", "Firefox", "Safari"]
        }
        
        assert len(result["associatedTestEnvironments"]) == 3
        assert result["createdTestEnvironments"] == ["Safari"]
        
    async def test_add_test_environments_failure(self, execution_tools, mock_client, mock_id_resolver):
        """Test handling failure when adding environments."""
        mock_id_resolver.resolve_issue_id.return_value = "12345"
        mock_client.execute_mutation.return_value = {"data": {}}
        
        with pytest.raises(GraphQLError, match="Failed to add test environments to execution PROJ-123"):
            await execution_tools.add_test_environments("PROJ-123", ["Chrome"])


@pytest.mark.asyncio
@pytest.mark.unit
class TestRemoveTestEnvironments:
    """Test remove_test_environments method."""
    
    async def test_remove_test_environments_success(self, execution_tools, mock_client, mock_id_resolver):
        """Test successful removal of test environments."""
        mock_id_resolver.resolve_issue_id.return_value = "12345"
        mock_client.execute_mutation.return_value = {
            "data": {"removeTestEnvironmentsFromTestExecution": True}
        }
        
        result = await execution_tools.remove_test_environments(
            "PROJ-123", ["Chrome", "Firefox"]
        )
        
        mock_id_resolver.resolve_issue_id.assert_called_once_with(
            "PROJ-123", ResourceType.TEST_EXECUTION
        )
        
        mock_client.execute_mutation.assert_called_once()
        call_args = mock_client.execute_mutation.call_args
        variables = call_args[0][1]
        assert variables == {
            "issueId": "12345",
            "testEnvironments": ["Chrome", "Firefox"]
        }
        
        assert result["success"] is True
        assert result["executionId"] == "PROJ-123"
        
    async def test_remove_test_environments_failure(self, execution_tools, mock_client, mock_id_resolver):
        """Test handling failure when removing environments."""
        mock_id_resolver.resolve_issue_id.return_value = "12345"
        mock_client.execute_mutation.return_value = {"data": {}}
        
        with pytest.raises(GraphQLError, match="Failed to remove test environments from execution PROJ-123"):
            await execution_tools.remove_test_environments("PROJ-123", ["Chrome"])