"""Comprehensive unit tests for TestPlanTools."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

try:
    from tools.plans import TestPlanTools
    from exceptions import GraphQLError, ValidationError
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tools.plans import TestPlanTools
    from exceptions import GraphQLError, ValidationError


class TestTestPlanTools:
    """Test suite for TestPlanTools class."""

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
    def testplan_tools(self, mock_client, mock_id_resolver):
        """Create TestPlanTools instance with mocked dependencies."""
        tools = TestPlanTools(mock_client)
        tools.id_resolver = mock_id_resolver
        return tools

    @pytest.mark.asyncio
    async def test_init(self, mock_client):
        """Test TestPlanTools initialization."""
        tools = TestPlanTools(mock_client)
        assert tools.client == mock_client
        assert tools.id_resolver is not None

    @pytest.mark.asyncio
    async def test_get_test_plan_success(self, testplan_tools, mock_client, mock_id_resolver):
        """Test successful test plan retrieval."""
        # Setup
        issue_id = "TEST-123"
        resolved_id = "1162822"
        expected_response = {
            "data": {
                "getTestPlan": {
                    "issueId": resolved_id,
                    "projectId": "10000",
                    "jira": {
                        "key": "TEST-123",
                        "fields": {
                            "summary": "Test Plan 1",
                            "description": "Test description",
                            "status": {"name": "Open"},
                            "priority": {"name": "Medium"},
                            "labels": [],
                            "created": "2023-01-01T10:00:00Z",
                            "updated": "2023-01-02T10:00:00Z"
                        }
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
        result = await testplan_tools.get_test_plan(issue_id)

        # Assert
        assert result == expected_response["data"]["getTestPlan"]
        mock_id_resolver.resolve_issue_id.assert_called_once_with(issue_id)
        mock_client.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_test_plan_not_found(self, testplan_tools, mock_client, mock_id_resolver):
        """Test test plan retrieval when not found."""
        # Setup
        issue_id = "TEST-999"
        resolved_id = "9999999"
        mock_id_resolver.resolve_issue_id.return_value = resolved_id
        mock_client.execute_query.return_value = {"data": {"getTestPlan": {}}}

        # Execute
        result = await testplan_tools.get_test_plan(issue_id)

        # Assert
        assert result == {}

    @pytest.mark.asyncio
    async def test_get_test_plans_success(self, testplan_tools, mock_client):
        """Test successful test plans retrieval with JQL."""
        # Setup
        jql = 'project = "TEST"'
        limit = 50
        expected_response = {
            "data": {
                "getTestPlans": {
                    "total": 1,
                    "start": 0,
                    "limit": 50,
                    "results": [
                        {
                            "issueId": "1162822",
                            "projectId": "10000",
                            "jira": {
                                "key": "TEST-123",
                                "fields": {
                                    "summary": "Test Plan 1"
                                }
                            }
                        }
                    ]
                }
            }
        }

        mock_client.execute_query.return_value = expected_response

        # Execute
        result = await testplan_tools.get_test_plans(jql=jql, limit=limit)

        # Assert
        assert result == expected_response["data"]["getTestPlans"]
        mock_client.execute_query.assert_called_once()
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]  # variables are the second positional argument
        assert variables["jql"] == jql
        assert variables["limit"] == limit

    @pytest.mark.asyncio
    async def test_get_test_plans_no_jql(self, testplan_tools, mock_client):
        """Test test plans retrieval without JQL."""
        # Setup
        expected_response = {
            "data": {
                "getTestPlans": {
                    "total": 0,
                    "start": 0,
                    "limit": 100,
                    "results": []
                }
            }
        }

        mock_client.execute_query.return_value = expected_response

        # Execute
        result = await testplan_tools.get_test_plans()

        # Assert
        assert result == expected_response["data"]["getTestPlans"]
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]  # variables are the second positional argument
        assert variables["jql"] is None
        assert variables["limit"] == 100

    @pytest.mark.asyncio
    async def test_get_test_plans_limit_exceeded(self, testplan_tools):
        """Test that limit over 100 raises ValidationError."""
        with pytest.raises(ValidationError, match="Limit cannot exceed 100"):
            await testplan_tools.get_test_plans(limit=101)

    @pytest.mark.asyncio
    async def test_create_test_plan_success(self, testplan_tools, mock_client):
        """Test successful test plan creation."""
        # Setup
        project_key = "TEST"
        summary = "New Test Plan"
        description = "Test description"
        test_issue_ids = ["1162823", "1162824"]
        expected_response = {
            "data": {
                "createTestPlan": {
                    "testPlan": {
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
        testplan_tools.add_tests_to_plan = AsyncMock(return_value={"addedTests": ["1162823", "1162824"]})

        # Execute
        result = await testplan_tools.create_test_plan(
            project_key=project_key,
            summary=summary,
            description=description,
            test_issue_ids=test_issue_ids
        )

        # Assert
        assert result["testPlan"]["issueId"] == "1162825"
        assert result["addedTests"] == ["1162823", "1162824"]
        mock_client.execute_query.assert_called_once()
        
        # Verify Jira data structure
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]  # variables are the second positional argument
        jira_data = variables["jira"]
        assert jira_data["fields"]["project"]["key"] == project_key
        assert jira_data["fields"]["summary"] == summary
        assert jira_data["fields"]["description"] == description
        assert jira_data["fields"]["issuetype"]["name"] == "Test Plan"

    @pytest.mark.asyncio
    async def test_create_test_plan_no_description(self, testplan_tools, mock_client):
        """Test test plan creation without description."""
        # Setup
        project_key = "TEST"
        summary = "New Test Plan"
        expected_response = {
            "data": {
                "createTestPlan": {
                    "testPlan": {
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
        result = await testplan_tools.create_test_plan(
            project_key=project_key,
            summary=summary
        )

        # Assert
        assert result == expected_response["data"]["createTestPlan"]
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]  # variables are the second positional argument
        jira_data = variables["jira"]
        assert "description" not in jira_data["fields"]

    @pytest.mark.asyncio
    async def test_create_test_plan_no_tests(self, testplan_tools, mock_client):
        """Test test plan creation without tests."""
        # Setup
        project_key = "TEST"
        summary = "New Test Plan"
        expected_response = {
            "data": {
                "createTestPlan": {
                    "testPlan": {
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
        result = await testplan_tools.create_test_plan(
            project_key=project_key,
            summary=summary
        )

        # Assert
        assert result == expected_response["data"]["createTestPlan"]
        assert "addedTests" not in result

    @pytest.mark.asyncio
    async def test_update_test_plan_not_supported(self, testplan_tools):
        """Test that update_test_plan raises GraphQLError as it's not supported."""
        issue_id = "TEST-123"
        updates = {"summary": "Updated Summary"}
        
        with pytest.raises(GraphQLError, match="updateTestPlan mutation is not available"):
            await testplan_tools.update_test_plan(issue_id, updates)

    @pytest.mark.asyncio
    async def test_delete_test_plan_success(self, testplan_tools, mock_client, mock_id_resolver):
        """Test successful test plan deletion."""
        # Setup
        issue_id = "TEST-123"
        resolved_id = "1162822"
        mock_id_resolver.resolve_issue_id.return_value = resolved_id
        mock_client.execute_query.return_value = {
            "data": {"deleteTestPlan": "Test plan deleted successfully"}
        }

        # Execute
        result = await testplan_tools.delete_test_plan(issue_id)

        # Assert
        assert result["success"] is True
        assert result["deletedTestPlanId"] == issue_id
        mock_id_resolver.resolve_issue_id.assert_called_once_with(issue_id)

    @pytest.mark.asyncio
    async def test_delete_test_plan_failure(self, testplan_tools, mock_client, mock_id_resolver):
        """Test test plan deletion failure."""
        # Setup
        issue_id = "TEST-123"
        resolved_id = "1162822"
        mock_id_resolver.resolve_issue_id.return_value = resolved_id
        mock_client.execute_query.return_value = {
            "data": {"deleteTestPlan": None}
        }

        # Execute
        result = await testplan_tools.delete_test_plan(issue_id)

        # Assert
        assert result["success"] is False
        assert result["deletedTestPlanId"] == issue_id

    @pytest.mark.asyncio
    async def test_add_tests_to_plan_success(self, testplan_tools, mock_client, mock_id_resolver):
        """Test successful adding tests to test plan."""
        # Setup
        plan_issue_id = "TEST-123"
        test_issue_ids = ["TEST-124", "TEST-125"]
        resolved_plan_id = "1162822"
        resolved_test_ids = ["1162823", "1162824"]
        expected_response = {
            "data": {
                "addTestsToTestPlan": {
                    "addedTests": resolved_test_ids,
                    "warning": None
                }
            }
        }

        mock_id_resolver.resolve_issue_id.return_value = resolved_plan_id
        mock_id_resolver.resolve_multiple_issue_ids.return_value = resolved_test_ids
        mock_client.execute_query.return_value = expected_response

        # Execute
        result = await testplan_tools.add_tests_to_plan(plan_issue_id, test_issue_ids)

        # Assert
        assert result == expected_response["data"]["addTestsToTestPlan"]
        mock_id_resolver.resolve_issue_id.assert_called_once_with(plan_issue_id)
        mock_id_resolver.resolve_multiple_issue_ids.assert_called_once_with(test_issue_ids)
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]  # variables are the second positional argument
        assert variables["issueId"] == resolved_plan_id
        assert variables["testIssueIds"] == resolved_test_ids

    @pytest.mark.asyncio
    async def test_add_tests_to_plan_empty_list(self, testplan_tools):
        """Test adding empty test list raises ValidationError."""
        with pytest.raises(ValidationError, match="test_issue_ids cannot be empty"):
            await testplan_tools.add_tests_to_plan("TEST-123", [])

    @pytest.mark.asyncio
    async def test_remove_tests_from_plan_success(self, testplan_tools, mock_client, mock_id_resolver):
        """Test successful removing tests from test plan."""
        # Setup
        plan_issue_id = "TEST-123"
        test_issue_ids = ["TEST-124", "TEST-125"]
        resolved_plan_id = "1162822"
        resolved_test_ids = ["1162823", "1162824"]

        mock_id_resolver.resolve_issue_id.return_value = resolved_plan_id
        mock_id_resolver.resolve_multiple_issue_ids.return_value = resolved_test_ids
        mock_client.execute_query.return_value = {
            "data": {"removeTestsFromTestPlan": None}  # Returns None on success
        }

        # Execute
        result = await testplan_tools.remove_tests_from_plan(plan_issue_id, test_issue_ids)

        # Assert
        assert result["success"] is True  # None is not None, so success is True
        assert result["removedTestIds"] == test_issue_ids
        mock_id_resolver.resolve_issue_id.assert_called_once_with(plan_issue_id)
        mock_id_resolver.resolve_multiple_issue_ids.assert_called_once_with(test_issue_ids)

    @pytest.mark.asyncio
    async def test_remove_tests_from_plan_with_error(self, testplan_tools, mock_client, mock_id_resolver):
        """Test removing tests from test plan with GraphQL error."""
        # Setup
        plan_issue_id = "TEST-123"
        test_issue_ids = ["TEST-124", "TEST-125"]
        resolved_plan_id = "1162822"
        resolved_test_ids = ["1162823", "1162824"]

        mock_id_resolver.resolve_issue_id.return_value = resolved_plan_id
        mock_id_resolver.resolve_multiple_issue_ids.return_value = resolved_test_ids
        mock_client.execute_query.return_value = {
            "errors": [{"message": "Some error occurred"}]
        }

        # Execute
        result = await testplan_tools.remove_tests_from_plan(plan_issue_id, test_issue_ids)

        # Assert
        assert result["success"] is False  # errors present, so success is False
        assert result["removedTestIds"] == test_issue_ids

    @pytest.mark.asyncio
    async def test_remove_tests_from_plan_empty_list(self, testplan_tools):
        """Test removing empty test list raises ValidationError."""
        with pytest.raises(ValidationError, match="test_issue_ids cannot be empty"):
            await testplan_tools.remove_tests_from_plan("TEST-123", [])

    @pytest.mark.asyncio
    async def test_graphql_error_handling(self, testplan_tools, mock_client, mock_id_resolver):
        """Test GraphQL error handling in get_test_plan."""
        # Setup
        issue_id = "TEST-123"
        resolved_id = "1162822"
        mock_id_resolver.resolve_issue_id.return_value = resolved_id
        mock_client.execute_query.side_effect = GraphQLError("GraphQL query failed")

        # Execute and Assert
        with pytest.raises(GraphQLError, match="GraphQL query failed"):
            await testplan_tools.get_test_plan(issue_id)

    @pytest.mark.asyncio
    async def test_id_resolver_error_handling(self, testplan_tools, mock_id_resolver):
        """Test ID resolver error handling."""
        # Setup
        issue_id = "TEST-999"
        mock_id_resolver.resolve_issue_id.side_effect = GraphQLError("Could not resolve issue ID")

        # Execute and Assert
        with pytest.raises(GraphQLError, match="Could not resolve issue ID"):
            await testplan_tools.get_test_plan(issue_id)

    @pytest.mark.asyncio
    async def test_create_test_plan_with_failed_add_tests(self, testplan_tools, mock_client):
        """Test create test plan when adding tests fails."""
        # Setup
        project_key = "TEST"
        summary = "New Test Plan"
        test_issue_ids = ["1162823", "1162824"]
        
        # Mock successful creation but no testPlan in response
        create_response = {
            "data": {
                "createTestPlan": {
                    "testPlan": {},  # Empty testPlan, no issueId
                    "warnings": []
                }
            }
        }
        mock_client.execute_query.return_value = create_response

        # Execute
        result = await testplan_tools.create_test_plan(
            project_key=project_key,
            summary=summary,
            test_issue_ids=test_issue_ids
        )

        # Assert - should not attempt to add tests since no issueId
        assert result == create_response["data"]["createTestPlan"]
        assert "addedTests" not in result