"""Comprehensive unit tests for TestSetTools."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

try:
    from tools.testsets import TestSetTools
    from exceptions import GraphQLError, ValidationError
    from utils.id_resolver import ResourceType
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tools.testsets import TestSetTools
    from exceptions import GraphQLError, ValidationError
    from utils.id_resolver import ResourceType


class TestTestSetTools:
    """Test suite for TestSetTools class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock GraphQL client."""
        client = AsyncMock()
        return client

    @pytest.fixture
    def mock_id_resolver(self):
        """Create a mock ID resolver."""
        resolver = AsyncMock()
        return resolver

    @pytest.fixture
    def testset_tools(self, mock_client, mock_id_resolver):
        """Create TestSetTools instance with mocked dependencies."""
        tools = TestSetTools(mock_client)
        tools.id_resolver = mock_id_resolver
        return tools

    @pytest.mark.asyncio
    async def test_init(self, mock_client):
        """Test TestSetTools initialization."""
        tools = TestSetTools(mock_client)
        assert tools.client == mock_client
        assert tools.id_resolver is not None

    @pytest.mark.asyncio
    async def test_get_test_set_success(self, testset_tools, mock_client, mock_id_resolver):
        """Test successful test set retrieval."""
        # Setup
        issue_id = "TEST-123"
        resolved_id = "1162822"
        expected_response = {
            "data": {
                "getTestSet": {
                    "issueId": resolved_id,
                    "projectId": "10000",
                    "jira": {
                        "key": "TEST-123",
                        "summary": "Test Set 1",
                        "description": "Test description",
                        "status": {"name": "Open"},
                        "priority": {"name": "Medium"},
                        "labels": [],
                        "created": "2023-01-01T10:00:00Z",
                        "updated": "2023-01-02T10:00:00Z"
                    },
                    "tests": {
                        "total": 2,
                        "results": [
                            {
                                "issueId": "1162823",
                                "testType": {"name": "Manual"},
                                "jira": {
                                    "key": "TEST-124",
                                    "summary": "Login Test"
                                }
                            }
                        ]
                    }
                }
            }
        }

        mock_id_resolver.resolve_issue_id.return_value = resolved_id
        mock_client.execute_query.return_value = expected_response

        # Execute
        result = await testset_tools.get_test_set(issue_id)

        # Assert
        assert result == expected_response["data"]["getTestSet"]
        mock_id_resolver.resolve_issue_id.assert_called_once_with(issue_id, ResourceType.TEST_SET)
        mock_client.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_test_set_not_found(self, testset_tools, mock_client, mock_id_resolver):
        """Test test set retrieval when not found."""
        # Setup
        issue_id = "TEST-999"
        resolved_id = "9999999"
        mock_id_resolver.resolve_issue_id.return_value = resolved_id
        mock_client.execute_query.return_value = {"data": {"getTestSet": {}}}

        # Execute
        result = await testset_tools.get_test_set(issue_id)

        # Assert
        assert result == {}

    @pytest.mark.asyncio
    async def test_get_test_sets_success(self, testset_tools, mock_client):
        """Test successful test sets retrieval with JQL."""
        # Setup
        jql = 'project = "TEST"'
        limit = 50
        expected_response = {
            "data": {
                "getTestSets": {
                    "total": 1,
                    "start": 0,
                    "limit": 50,
                    "results": [
                        {
                            "issueId": "1162822",
                            "projectId": "10000",
                            "jira": {
                                "key": "TEST-123",
                                "summary": "Test Set 1"
                            }
                        }
                    ]
                }
            }
        }

        mock_client.execute_query.return_value = expected_response

        # Execute
        result = await testset_tools.get_test_sets(jql=jql, limit=limit)

        # Assert
        assert result == expected_response["data"]["getTestSets"]
        mock_client.execute_query.assert_called_once()
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]  # variables are the second positional argument
        assert variables["jql"] == jql
        assert variables["limit"] == limit

    @pytest.mark.asyncio
    async def test_get_test_sets_no_jql(self, testset_tools, mock_client):
        """Test test sets retrieval without JQL."""
        # Setup
        expected_response = {
            "data": {
                "getTestSets": {
                    "total": 0,
                    "start": 0,
                    "limit": 100,
                    "results": []
                }
            }
        }

        mock_client.execute_query.return_value = expected_response

        # Execute
        result = await testset_tools.get_test_sets()

        # Assert
        assert result == expected_response["data"]["getTestSets"]
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]  # variables are the second positional argument
        assert variables["jql"] is None
        assert variables["limit"] == 100

    @pytest.mark.asyncio
    async def test_get_test_sets_limit_exceeded(self, testset_tools):
        """Test that limit over 100 raises ValidationError."""
        with pytest.raises(ValidationError, match="Limit cannot exceed 100"):
            await testset_tools.get_test_sets(limit=101)

    @pytest.mark.asyncio
    async def test_create_test_set_success(self, testset_tools, mock_client):
        """Test successful test set creation."""
        # Setup
        project_key = "TEST"
        summary = "New Test Set"
        description = "Test description"
        test_issue_ids = ["1162823", "1162824"]
        expected_response = {
            "data": {
                "createTestSet": {
                    "testSet": {
                        "issueId": "1162825",
                        "jira": {
                            "key": "TEST-125",
                            "summary": summary
                        }
                    },
                    "warnings": []
                }
            }
        }

        mock_client.execute_query.return_value = expected_response
        testset_tools.add_tests_to_set = AsyncMock(return_value={"addedTests": ["1162823", "1162824"]})

        # Execute
        result = await testset_tools.create_test_set(
            project_key=project_key,
            summary=summary,
            description=description,
            test_issue_ids=test_issue_ids
        )

        # Assert
        assert result["testSet"]["issueId"] == "1162825"
        assert result["addedTests"] == ["1162823", "1162824"]
        mock_client.execute_query.assert_called_once()
        
        # Verify Jira data structure
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]  # variables are the second positional argument
        jira_data = variables["jira"]
        assert jira_data["fields"]["project"]["key"] == project_key
        assert jira_data["fields"]["summary"] == summary
        assert jira_data["fields"]["description"] == description
        assert jira_data["fields"]["issuetype"]["name"] == "Test Set"

    @pytest.mark.asyncio
    async def test_create_test_set_no_description(self, testset_tools, mock_client):
        """Test test set creation without description."""
        # Setup
        project_key = "TEST"
        summary = "New Test Set"
        expected_response = {
            "data": {
                "createTestSet": {
                    "testSet": {
                        "issueId": "1162825",
                        "jira": {
                            "key": "TEST-125",
                            "summary": summary
                        }
                    },
                    "warnings": []
                }
            }
        }

        mock_client.execute_query.return_value = expected_response

        # Execute
        result = await testset_tools.create_test_set(
            project_key=project_key,
            summary=summary
        )

        # Assert
        assert result == expected_response["data"]["createTestSet"]
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]  # variables are the second positional argument
        jira_data = variables["jira"]
        assert "description" not in jira_data["fields"]

    @pytest.mark.asyncio
    async def test_create_test_set_no_tests(self, testset_tools, mock_client):
        """Test test set creation without tests."""
        # Setup
        project_key = "TEST"
        summary = "New Test Set"
        expected_response = {
            "data": {
                "createTestSet": {
                    "testSet": {
                        "issueId": "1162825",
                        "jira": {
                            "key": "TEST-125",
                            "summary": summary
                        }
                    },
                    "warnings": []
                }
            }
        }

        mock_client.execute_query.return_value = expected_response

        # Execute
        result = await testset_tools.create_test_set(
            project_key=project_key,
            summary=summary
        )

        # Assert
        assert result == expected_response["data"]["createTestSet"]
        assert "addedTests" not in result

    @pytest.mark.asyncio
    async def test_update_test_set_success(self, testset_tools, mock_client, mock_id_resolver):
        """Test successful test set update."""
        # Setup
        issue_id = "TEST-123"
        resolved_id = "1162822"
        updates = {
            "summary": "Updated Summary",
            "description": "Updated description",
            "labels": ["regression", "smoke"]
        }
        expected_response = {
            "data": {
                "updateTestSet": {
                    "testSet": {
                        "issueId": resolved_id,
                        "summary": updates["summary"],
                        "description": updates["description"],
                        "labels": updates["labels"],
                        "updated": "2023-01-03T10:00:00Z"
                    }
                }
            }
        }

        mock_id_resolver.resolve_issue_id.return_value = resolved_id
        mock_client.execute_query.return_value = expected_response

        # Execute
        result = await testset_tools.update_test_set(issue_id, updates)

        # Assert
        assert result == expected_response["data"]["updateTestSet"]
        mock_id_resolver.resolve_issue_id.assert_called_once_with(issue_id, ResourceType.TEST_SET)
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]  # variables are the second positional argument
        assert variables["issueId"] == resolved_id
        assert variables["updates"] == updates

    @pytest.mark.asyncio
    async def test_delete_test_set_success_string_response(self, testset_tools, mock_client, mock_id_resolver):
        """Test successful test set deletion with string response."""
        # Setup
        issue_id = "TEST-123"
        resolved_id = "1162822"
        mock_id_resolver.resolve_issue_id.return_value = resolved_id
        mock_client.execute_query.return_value = {
            "data": {"deleteTestSet": "Test set deleted successfully"}
        }

        # Execute
        result = await testset_tools.delete_test_set(issue_id)

        # Assert
        assert result["success"] is True
        assert result["deletedTestSetId"] == issue_id
        assert result["message"] == "Test set deleted successfully"
        mock_id_resolver.resolve_issue_id.assert_called_once_with(issue_id, ResourceType.TEST_SET)

    @pytest.mark.asyncio
    async def test_delete_test_set_success_dict_response(self, testset_tools, mock_client, mock_id_resolver):
        """Test successful test set deletion with dict response."""
        # Setup
        issue_id = "TEST-123"
        resolved_id = "1162822"
        mock_id_resolver.resolve_issue_id.return_value = resolved_id
        mock_client.execute_query.return_value = {
            "data": {"deleteTestSet": {"success": True}}
        }

        # Execute
        result = await testset_tools.delete_test_set(issue_id)

        # Assert
        assert result["success"] is True
        assert result["deletedTestSetId"] == issue_id
        assert result["message"] is None

    @pytest.mark.asyncio
    async def test_delete_test_set_failure(self, testset_tools, mock_client, mock_id_resolver):
        """Test test set deletion failure."""
        # Setup
        issue_id = "TEST-123"
        resolved_id = "1162822"
        mock_id_resolver.resolve_issue_id.return_value = resolved_id
        mock_client.execute_query.return_value = {
            "data": {"deleteTestSet": None}
        }

        # Execute
        result = await testset_tools.delete_test_set(issue_id)

        # Assert
        assert result["success"] is False
        assert result["deletedTestSetId"] == issue_id

    @pytest.mark.asyncio
    async def test_add_tests_to_set_success(self, testset_tools, mock_client, mock_id_resolver):
        """Test successful adding tests to test set."""
        # Setup
        set_issue_id = "TEST-123"
        test_issue_ids = ["TEST-124", "TEST-125"]
        resolved_set_id = "1162822"
        resolved_test_ids = ["1162823", "1162824"]
        expected_response = {
            "data": {
                "addTestsToTestSet": {
                    "addedTests": resolved_test_ids,
                    "warning": None
                }
            }
        }

        mock_id_resolver.resolve_issue_id.return_value = resolved_set_id
        mock_id_resolver.resolve_multiple_issue_ids.return_value = resolved_test_ids
        mock_client.execute_query.return_value = expected_response

        # Execute
        result = await testset_tools.add_tests_to_set(set_issue_id, test_issue_ids)

        # Assert
        assert result == expected_response["data"]["addTestsToTestSet"]
        mock_id_resolver.resolve_issue_id.assert_called_once_with(set_issue_id, ResourceType.TEST_SET)
        mock_id_resolver.resolve_multiple_issue_ids.assert_called_once_with(test_issue_ids, ResourceType.TEST)
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]  # variables are the second positional argument
        assert variables["issueId"] == resolved_set_id
        assert variables["testIssueIds"] == resolved_test_ids

    @pytest.mark.asyncio
    async def test_add_tests_to_set_empty_list(self, testset_tools):
        """Test adding empty test list raises ValidationError."""
        with pytest.raises(ValidationError, match="test_issue_ids cannot be empty"):
            await testset_tools.add_tests_to_set("TEST-123", [])

    @pytest.mark.asyncio
    async def test_remove_tests_from_set_success(self, testset_tools, mock_client, mock_id_resolver):
        """Test successful removing tests from test set."""
        # Setup
        set_issue_id = "TEST-123"
        test_issue_ids = ["TEST-124", "TEST-125"]
        resolved_set_id = "1162822"
        resolved_test_ids = ["1162823", "1162824"]

        mock_id_resolver.resolve_issue_id.return_value = resolved_set_id
        mock_id_resolver.resolve_multiple_issue_ids.return_value = resolved_test_ids
        mock_client.execute_query.return_value = {
            "data": {"removeTestsFromTestSet": "Tests removed successfully"}
        }

        # Execute
        result = await testset_tools.remove_tests_from_set(set_issue_id, test_issue_ids)

        # Assert
        assert result["success"] is True
        assert result["removedTests"] == test_issue_ids
        mock_id_resolver.resolve_issue_id.assert_called_once_with(set_issue_id, ResourceType.TEST_SET)
        mock_id_resolver.resolve_multiple_issue_ids.assert_called_once_with(test_issue_ids, ResourceType.TEST)

    @pytest.mark.asyncio
    async def test_remove_tests_from_set_failure(self, testset_tools, mock_client, mock_id_resolver):
        """Test removing tests from test set failure."""
        # Setup
        set_issue_id = "TEST-123"
        test_issue_ids = ["TEST-124", "TEST-125"]
        resolved_set_id = "1162822"
        resolved_test_ids = ["1162823", "1162824"]

        mock_id_resolver.resolve_issue_id.return_value = resolved_set_id
        mock_id_resolver.resolve_multiple_issue_ids.return_value = resolved_test_ids
        mock_client.execute_query.return_value = {
            "data": {"removeTestsFromTestSet": None}
        }

        # Execute
        result = await testset_tools.remove_tests_from_set(set_issue_id, test_issue_ids)

        # Assert
        assert result["success"] is False
        assert result["removedTests"] == []

    @pytest.mark.asyncio
    async def test_remove_tests_from_set_empty_list(self, testset_tools):
        """Test removing empty test list raises ValidationError."""
        with pytest.raises(ValidationError, match="test_issue_ids cannot be empty"):
            await testset_tools.remove_tests_from_set("TEST-123", [])

    @pytest.mark.asyncio
    async def test_graphql_error_handling(self, testset_tools, mock_client, mock_id_resolver):
        """Test GraphQL error handling in get_test_set."""
        # Setup
        issue_id = "TEST-123"
        resolved_id = "1162822"
        mock_id_resolver.resolve_issue_id.return_value = resolved_id
        mock_client.execute_query.side_effect = GraphQLError("GraphQL query failed")

        # Execute and Assert
        with pytest.raises(GraphQLError, match="GraphQL query failed"):
            await testset_tools.get_test_set(issue_id)

    @pytest.mark.asyncio
    async def test_id_resolver_error_handling(self, testset_tools, mock_id_resolver):
        """Test ID resolver error handling."""
        # Setup
        issue_id = "TEST-999"
        mock_id_resolver.resolve_issue_id.side_effect = GraphQLError("Could not resolve issue ID")

        # Execute and Assert
        with pytest.raises(GraphQLError, match="Could not resolve issue ID"):
            await testset_tools.get_test_set(issue_id)

    @pytest.mark.asyncio
    async def test_create_test_set_with_failed_add_tests(self, testset_tools, mock_client):
        """Test create test set when adding tests fails."""
        # Setup
        project_key = "TEST"
        summary = "New Test Set"
        test_issue_ids = ["1162823", "1162824"]
        
        # Mock successful creation but no testSet in response
        create_response = {
            "data": {
                "createTestSet": {
                    "testSet": {},  # Empty testSet, no issueId
                    "warnings": []
                }
            }
        }
        mock_client.execute_query.return_value = create_response

        # Execute
        result = await testset_tools.create_test_set(
            project_key=project_key,
            summary=summary,
            test_issue_ids=test_issue_ids
        )

        # Assert - should not attempt to add tests since no issueId
        assert result == create_response["data"]["createTestSet"]
        assert "addedTests" not in result

    @pytest.mark.asyncio
    async def test_update_test_set_empty_response(self, testset_tools, mock_client, mock_id_resolver):
        """Test update test set with empty response."""
        # Setup
        issue_id = "TEST-123"
        resolved_id = "1162822"
        updates = {"summary": "Updated Summary"}
        
        mock_id_resolver.resolve_issue_id.return_value = resolved_id
        mock_client.execute_query.return_value = {"data": {"updateTestSet": {}}}

        # Execute
        result = await testset_tools.update_test_set(issue_id, updates)

        # Assert
        assert result == {}