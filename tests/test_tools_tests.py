"""Tests for TestTools class."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

try:
    from tools.tests import TestTools
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError
except ImportError:
    import sys
    sys.path.append('..')
    from tools.tests import TestTools
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
def test_tools(mock_client):
    """Create TestTools instance with mock client."""
    return TestTools(mock_client)


class TestTestTools:
    """Test suite for TestTools class."""
    
    @pytest.mark.asyncio
    async def test_get_test_success(self, test_tools, mock_client):
        """Test successful test retrieval."""
        mock_client.execute_query.return_value = {
            "data": {
                "getTest": {
                    "issueId": "TEST-123",
                    "testType": {"name": "Manual"},
                    "steps": [
                        {
                            "id": "1",
                            "action": "Click button",
                            "data": "Button A",
                            "result": "Page loads",
                            "attachments": []
                        }
                    ],
                    "gherkin": None,
                    "unstructured": None,
                    "jira": {
                        "key": "TEST-123",
                        "summary": "Test login functionality"
                    }
                }
            }
        }
        
        result = await test_tools.get_test("TEST-123")
        
        assert result["issueId"] == "TEST-123"
        assert result["testType"]["name"] == "Manual"
        assert len(result["steps"]) == 1
        assert result["steps"][0]["action"] == "Click button"
        
        # Verify query was called correctly
        mock_client.execute_query.assert_called_once()
        args = mock_client.execute_query.call_args
        assert "getTest" in args[0][0]
        assert args[0][1] == {"issueId": "TEST-123"}
    
    @pytest.mark.asyncio
    async def test_get_test_not_found(self, test_tools, mock_client):
        """Test get_test when test doesn't exist."""
        mock_client.execute_query.return_value = {"data": {"getTest": None}}
        
        with pytest.raises(GraphQLError) as exc_info:
            await test_tools.get_test("NONEXISTENT-1")
        
        assert "Failed to retrieve test" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_tests_with_jql(self, test_tools, mock_client):
        """Test retrieving multiple tests with JQL filter."""
        mock_client.execute_query.return_value = {
            "data": {
                "getTests": {
                    "total": 2,
                    "start": 0,
                    "limit": 100,
                    "results": [
                        {
                            "issueId": "TEST-101",
                            "testType": {"name": "Manual"},
                            "steps": [],
                            "jira": {"key": "TEST-101", "summary": "Test 1"}
                        },
                        {
                            "issueId": "TEST-102",
                            "testType": {"name": "Cucumber"},
                            "gherkin": "Scenario: Test",
                            "jira": {"key": "TEST-102", "summary": "Test 2"}
                        }
                    ]
                }
            }
        }
        
        with patch('tools.tests.validate_jql') as mock_validate:
            mock_validate.return_value = 'project = "TEST"'
            
            result = await test_tools.get_tests(jql='project = "TEST"', limit=50)
            
            assert result["total"] == 2
            assert len(result["results"]) == 2
            assert result["results"][0]["testType"]["name"] == "Manual"
            assert result["results"][1]["testType"]["name"] == "Cucumber"
            
            mock_validate.assert_called_once_with('project = "TEST"')
    
    @pytest.mark.asyncio
    async def test_get_tests_limit_validation(self, test_tools):
        """Test that get_tests validates limit parameter."""
        with pytest.raises(ValidationError) as exc_info:
            await test_tools.get_tests(limit=101)
        
        assert "Limit cannot exceed 100" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_manual_test(self, test_tools, mock_client):
        """Test creating a manual test with steps."""
        mock_client.execute_mutation.return_value = {
            "data": {
                "createTest": {
                    "test": {
                        "issueId": "TEST-201",
                        "testType": {"name": "Manual"},
                        "steps": [
                            {
                                "id": "1",
                                "action": "Open application",
                                "data": "URL: /app",
                                "result": "App loads"
                            }
                        ],
                        "jira": {"key": "TEST-201", "summary": "New manual test"}
                    },
                    "warnings": []
                }
            }
        }
        
        result = await test_tools.create_test(
            project_key="TEST",
            summary="New manual test",
            test_type="Manual",
            description="Test description",
            steps=[
                {
                    "action": "Open application",
                    "data": "URL: /app",
                    "result": "App loads"
                }
            ]
        )
        
        assert result["test"]["issueId"] == "TEST-201"
        assert result["test"]["testType"]["name"] == "Manual"
        assert len(result["test"]["steps"]) == 1
        
        # Verify mutation was called
        mock_client.execute_mutation.assert_called_once()
        args = mock_client.execute_mutation.call_args
        assert "createTest" in args[0][0]
        variables = args[0][1]
        assert variables["testType"]["name"] == "Manual"
        assert len(variables["steps"]) == 1
    
    @pytest.mark.asyncio
    async def test_create_cucumber_test(self, test_tools, mock_client):
        """Test creating a Cucumber test with Gherkin."""
        mock_client.execute_mutation.return_value = {
            "data": {
                "createTest": {
                    "test": {
                        "issueId": "TEST-202",
                        "testType": {"name": "Cucumber"},
                        "gherkin": "Scenario: Login\n  Given I am on login page",
                        "jira": {"key": "TEST-202", "summary": "Cucumber test"}
                    },
                    "warnings": []
                }
            }
        }
        
        gherkin_scenario = """Scenario: Login
  Given I am on login page
  When I enter credentials
  Then I should be logged in"""
        
        result = await test_tools.create_test(
            project_key="TEST",
            summary="Cucumber test",
            test_type="Cucumber",
            gherkin=gherkin_scenario
        )
        
        assert result["test"]["issueId"] == "TEST-202"
        assert result["test"]["testType"]["name"] == "Cucumber"
        assert "Scenario: Login" in result["test"]["gherkin"]
    
    @pytest.mark.asyncio
    async def test_create_generic_test(self, test_tools, mock_client):
        """Test creating a generic test."""
        mock_client.execute_mutation.return_value = {
            "data": {
                "createTest": {
                    "test": {
                        "issueId": "TEST-203",
                        "testType": {"name": "Generic"},
                        "unstructured": "Free form test content",
                        "jira": {"key": "TEST-203", "summary": "Generic test"}
                    },
                    "warnings": []
                }
            }
        }
        
        result = await test_tools.create_test(
            project_key="TEST",
            summary="Generic test",
            test_type="Generic",
            unstructured="Free form test content"
        )
        
        assert result["test"]["issueId"] == "TEST-203"
        assert result["test"]["testType"]["name"] == "Generic"
        assert result["test"]["unstructured"] == "Free form test content"
    
    @pytest.mark.asyncio
    async def test_delete_test_success(self, test_tools, mock_client):
        """Test successful test deletion."""
        mock_client.execute_mutation.return_value = {
            "data": {"deleteTest": True}
        }
        
        result = await test_tools.delete_test("TEST-123")
        
        assert result["success"] is True
        assert result["issueId"] == "TEST-123"
        
        # Verify mutation was called
        mock_client.execute_mutation.assert_called_once()
        args = mock_client.execute_mutation.call_args
        assert "deleteTest" in args[0][0]
        assert args[0][1] == {"issueId": "TEST-123"}
    
    @pytest.mark.asyncio
    async def test_update_test_type(self, test_tools, mock_client):
        """Test updating test type."""
        mock_client.execute_mutation.return_value = {
            "data": {
                "updateTestType": {
                    "test": {
                        "issueId": "TEST-123",
                        "testType": {"name": "Manual"},
                        "jira": {"key": "TEST-123", "summary": "Updated test"}
                    },
                    "warnings": ["Some content may have been lost"]
                }
            }
        }
        
        result = await test_tools.update_test_type("TEST-123", "Manual")
        
        assert result["test"]["testType"]["name"] == "Manual"
        assert len(result["warnings"]) == 1
        assert "content may have been lost" in result["warnings"][0]
    
    @pytest.mark.asyncio
    async def test_get_expanded_test(self, test_tools, mock_client):
        """Test getting expanded test with version support."""
        mock_client.execute_query.return_value = {
            "data": {
                "getExpandedTest": {
                    "issueId": "TEST-123",
                    "versionId": 2,
                    "testType": {"name": "Manual"},
                    "steps": [
                        {
                            "id": "1",
                            "action": "Step 1",
                            "parentTestIssueId": None,
                            "calledTestIssueId": "TEST-100"
                        }
                    ],
                    "warnings": [],
                    "jira": {"key": "TEST-123"}
                }
            }
        }
        
        result = await test_tools.get_expanded_test("TEST-123", test_version_id=2)
        
        assert result["issueId"] == "TEST-123"
        assert result["versionId"] == 2
        assert result["steps"][0]["calledTestIssueId"] == "TEST-100"
        
        # Verify version parameter was passed
        args = mock_client.execute_query.call_args
        assert args[0][1]["versionId"] == 2