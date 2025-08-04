"""Tests for TestExecutionTools class."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

try:
    from tools.executions import TestExecutionTools
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError
except ImportError:
    import sys
    sys.path.append('..')
    from tools.executions import TestExecutionTools
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError


@pytest.fixture
def mock_client():
    """Create a mock GraphQL client."""
    client = Mock(spec=XrayGraphQLClient)
    client.execute_query = AsyncMock()
    client.execute_mutation = AsyncMock()
    return client


@pytest.fixture
def execution_tools(mock_client):
    """Create TestExecutionTools instance with mock client."""
    return TestExecutionTools(mock_client)


class TestTestExecutionTools:
    """Test suite for TestExecutionTools class."""
    
    @pytest.mark.asyncio
    async def test_get_test_execution_success(self, execution_tools, mock_client):
        """Test successful test execution retrieval."""
        mock_client.execute_query.return_value = {
            "data": {
                "getTestExecution": {
                    "issueId": "EXEC-123",
                    "tests": {
                        "total": 5,
                        "start": 0,
                        "limit": 100,
                        "results": [
                            {
                                "issueId": "TEST-101",
                                "testType": {"name": "Manual"}
                            }
                        ]
                    },
                    "jira": {
                        "key": "EXEC-123",
                        "summary": "Sprint 10 Execution",
                        "assignee": {"displayName": "John Doe"},
                        "status": {"name": "In Progress"}
                    }
                }
            }
        }
        
        result = await execution_tools.get_test_execution("EXEC-123")
        
        assert result["issueId"] == "EXEC-123"
        assert result["tests"]["total"] == 5
        assert result["jira"]["summary"] == "Sprint 10 Execution"
        
        # Verify query was called correctly
        mock_client.execute_query.assert_called_once()
        args = mock_client.execute_query.call_args
        assert "getTestExecution" in args[0][0]
        assert args[0][1] == {"issueId": "EXEC-123"}
    
    @pytest.mark.asyncio
    async def test_get_test_execution_not_found(self, execution_tools, mock_client):
        """Test get_test_execution when execution doesn't exist."""
        mock_client.execute_query.return_value = {"data": {"getTestExecution": None}}
        
        with pytest.raises(GraphQLError) as exc_info:
            await execution_tools.get_test_execution("NONEXISTENT-1")
        
        assert "Failed to retrieve test execution" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_test_executions_with_jql(self, execution_tools, mock_client):
        """Test retrieving multiple test executions with JQL filter."""
        mock_client.execute_query.return_value = {
            "data": {
                "getTestExecutions": {
                    "total": 3,
                    "start": 0,
                    "limit": 50,
                    "results": [
                        {
                            "issueId": "EXEC-101",
                            "tests": {"total": 10},
                            "jira": {"key": "EXEC-101", "status": {"name": "Done"}}
                        },
                        {
                            "issueId": "EXEC-102",
                            "tests": {"total": 15},
                            "jira": {"key": "EXEC-102", "status": {"name": "In Progress"}}
                        }
                    ]
                }
            }
        }
        
        with patch('tools.executions.validate_jql') as mock_validate:
            mock_validate.return_value = 'project = "TEST" AND fixVersion = "1.0"'
            
            result = await execution_tools.get_test_executions(
                jql='project = "TEST" AND fixVersion = "1.0"',
                limit=50
            )
            
            assert result["total"] == 3
            assert len(result["results"]) == 2
            assert result["results"][0]["tests"]["total"] == 10
            
            mock_validate.assert_called_once_with('project = "TEST" AND fixVersion = "1.0"')
    
    @pytest.mark.asyncio
    async def test_get_test_executions_limit_validation(self, execution_tools):
        """Test that get_test_executions validates limit parameter."""
        with pytest.raises(ValidationError) as exc_info:
            await execution_tools.get_test_executions(limit=101)
        
        assert "Limit cannot exceed 100" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_test_execution_full(self, execution_tools, mock_client):
        """Test creating test execution with all parameters."""
        mock_client.execute_mutation.return_value = {
            "data": {
                "createTestExecution": {
                    "testExecution": {
                        "issueId": "EXEC-201",
                        "jira": {
                            "key": "EXEC-201",
                            "summary": "Regression Test Suite"
                        }
                    },
                    "warnings": [],
                    "createdTestEnvironments": ["Safari"]
                }
            }
        }
        
        result = await execution_tools.create_test_execution(
            project_key="TEST",
            summary="Regression Test Suite",
            test_issue_ids=["TEST-101", "TEST-102", "TEST-103"],
            test_environments=["Chrome", "Firefox", "Safari"],
            description="Full regression testing for release 2.0"
        )
        
        assert result["testExecution"]["issueId"] == "EXEC-201"
        assert result["testExecution"]["jira"]["summary"] == "Regression Test Suite"
        assert "Safari" in result["createdTestEnvironments"]
        
        # Verify mutation parameters
        args = mock_client.execute_mutation.call_args
        variables = args[0][1]
        assert variables["testIssueIds"] == ["TEST-101", "TEST-102", "TEST-103"]
        assert variables["testEnvironments"] == ["Chrome", "Firefox", "Safari"]
        assert variables["jira"]["fields"]["description"] == "Full regression testing for release 2.0"
    
    @pytest.mark.asyncio
    async def test_create_test_execution_minimal(self, execution_tools, mock_client):
        """Test creating test execution with minimal parameters."""
        mock_client.execute_mutation.return_value = {
            "data": {
                "createTestExecution": {
                    "testExecution": {
                        "issueId": "EXEC-202",
                        "jira": {"key": "EXEC-202", "summary": "Quick Test"}
                    },
                    "warnings": [],
                    "createdTestEnvironments": []
                }
            }
        }
        
        result = await execution_tools.create_test_execution(
            project_key="TEST",
            summary="Quick Test"
        )
        
        assert result["testExecution"]["issueId"] == "EXEC-202"
        
        # Verify empty lists for optional parameters
        args = mock_client.execute_mutation.call_args
        variables = args[0][1]
        assert variables["testIssueIds"] == []
        assert variables["testEnvironments"] == []
        assert "description" not in variables["jira"]["fields"]
    
    @pytest.mark.asyncio
    async def test_delete_test_execution(self, execution_tools, mock_client):
        """Test deleting a test execution."""
        mock_client.execute_mutation.return_value = {
            "data": {"deleteTestExecution": True}
        }
        
        result = await execution_tools.delete_test_execution("EXEC-123")
        
        assert result["success"] is True
        assert result["issueId"] == "EXEC-123"
        
        # Verify mutation was called
        mock_client.execute_mutation.assert_called_once()
        args = mock_client.execute_mutation.call_args
        assert "deleteTestExecution" in args[0][0]
        assert args[0][1] == {"issueId": "EXEC-123"}
    
    @pytest.mark.asyncio
    async def test_add_tests_to_execution(self, execution_tools, mock_client):
        """Test adding tests to an execution."""
        mock_client.execute_mutation.return_value = {
            "data": {
                "addTestsToTestExecution": {
                    "addedTests": ["TEST-104", "TEST-105"],
                    "warning": "TEST-106 was already in the execution"
                }
            }
        }
        
        result = await execution_tools.add_tests_to_execution(
            "EXEC-123",
            ["TEST-104", "TEST-105", "TEST-106"]
        )
        
        assert len(result["addedTests"]) == 2
        assert "TEST-104" in result["addedTests"]
        assert "already in the execution" in result["warning"]
    
    @pytest.mark.asyncio
    async def test_remove_tests_from_execution(self, execution_tools, mock_client):
        """Test removing tests from an execution."""
        mock_client.execute_mutation.return_value = {
            "data": {"removeTestsFromTestExecution": True}
        }
        
        result = await execution_tools.remove_tests_from_execution(
            "EXEC-123",
            ["TEST-101", "TEST-102"]
        )
        
        assert result["success"] is True
        assert result["executionId"] == "EXEC-123"
        
        # Verify parameters
        args = mock_client.execute_mutation.call_args
        variables = args[0][1]
        assert variables["issueId"] == "EXEC-123"
        assert variables["testIssueIds"] == ["TEST-101", "TEST-102"]
    
    @pytest.mark.asyncio
    async def test_add_test_environments(self, execution_tools, mock_client):
        """Test adding test environments to an execution."""
        mock_client.execute_mutation.return_value = {
            "data": {
                "addTestEnvironmentsToTestExecution": {
                    "associatedTestEnvironments": ["Chrome", "Firefox", "Safari", "Edge"],
                    "createdTestEnvironments": ["Edge"]
                }
            }
        }
        
        result = await execution_tools.add_test_environments(
            "EXEC-123",
            ["Safari", "Edge"]
        )
        
        assert len(result["associatedTestEnvironments"]) == 4
        assert "Edge" in result["createdTestEnvironments"]
        assert "Safari" in result["associatedTestEnvironments"]
    
    @pytest.mark.asyncio
    async def test_remove_test_environments(self, execution_tools, mock_client):
        """Test removing test environments from an execution."""
        mock_client.execute_mutation.return_value = {
            "data": {"removeTestEnvironmentsFromTestExecution": True}
        }
        
        result = await execution_tools.remove_test_environments(
            "EXEC-123",
            ["IE 11", "Chrome 80"]
        )
        
        assert result["success"] is True
        assert result["executionId"] == "EXEC-123"
        
        # Verify parameters
        args = mock_client.execute_mutation.call_args
        variables = args[0][1]
        assert variables["testEnvironments"] == ["IE 11", "Chrome 80"]
    
    @pytest.mark.asyncio
    async def test_error_handling_in_mutations(self, execution_tools, mock_client):
        """Test proper error handling for failed mutations."""
        mock_client.execute_mutation.return_value = {
            "errors": [{"message": "Permission denied"}]
        }
        
        with pytest.raises(GraphQLError) as exc_info:
            await execution_tools.create_test_execution(
                project_key="TEST",
                summary="Test"
            )
        
        assert "Failed to create test execution" in str(exc_info.value)