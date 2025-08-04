"""Tests for TestTools class."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

try:
    from tools.tests import TestTools, TestStep
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError
except ImportError:
    import sys

    sys.path.append("..")
    from tools.tests import TestTools, TestStep
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
                    "issueId": "12345",
                    "testType": {"name": "Manual"},
                    "steps": [
                        {
                            "id": "1",
                            "action": "Click button",
                            "data": "Button A",
                            "result": "Page loads",
                            "attachments": [],
                        }
                    ],
                    "gherkin": None,
                    "unstructured": None,
                    "jira": {"key": "TEST-123", "summary": "Test login functionality"},
                }
            }
        }

        result = await test_tools.get_test("12345")  # Use numeric ID to skip resolution

        assert result["issueId"] == "12345"
        assert result["testType"]["name"] == "Manual"
        assert len(result["steps"]) == 1
        assert result["steps"][0]["action"] == "Click button"

        # Verify query was called correctly
        mock_client.execute_query.assert_called_once()
        args = mock_client.execute_query.call_args
        assert "getTest" in args[0][0]
        assert args[0][1] == {"issueId": "12345"}

    @pytest.mark.asyncio
    async def test_get_test_not_found(self, test_tools, mock_client):
        """Test get_test when test doesn't exist."""
        mock_client.execute_query.return_value = {"data": {"getTest": None}}

        with pytest.raises(GraphQLError) as exc_info:
            await test_tools.get_test("99999")  # Use numeric ID

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
                            "jira": {"key": "TEST-101", "summary": "Test 1"},
                        },
                        {
                            "issueId": "TEST-102",
                            "testType": {"name": "Cucumber"},
                            "gherkin": "Scenario: Test",
                            "jira": {"key": "TEST-102", "summary": "Test 2"},
                        },
                    ],
                }
            }
        }

        with patch("tools.tests.validate_jql") as mock_validate:
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
                                "result": "App loads",
                            }
                        ],
                        "jira": {"key": "TEST-201", "summary": "New manual test"},
                    },
                    "warnings": [],
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
                    "result": "App loads",
                }
            ],
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
                        "jira": {"key": "TEST-202", "summary": "Cucumber test"},
                    },
                    "warnings": [],
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
            gherkin=gherkin_scenario,
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
                        "jira": {"key": "TEST-203", "summary": "Generic test"},
                    },
                    "warnings": [],
                }
            }
        }

        result = await test_tools.create_test(
            project_key="TEST",
            summary="Generic test",
            test_type="Generic",
            unstructured="Free form test content",
        )

        assert result["test"]["issueId"] == "TEST-203"
        assert result["test"]["testType"]["name"] == "Generic"
        assert result["test"]["unstructured"] == "Free form test content"

    @pytest.mark.asyncio
    async def test_delete_test_success(self, test_tools, mock_client):
        """Test successful test deletion."""
        mock_client.execute_mutation.return_value = {"data": {"deleteTest": True}}

        result = await test_tools.delete_test("TEST-123")

        assert result["success"] is True
        assert result["issueId"] == "TEST-123"

        # Verify mutation was called
        mock_client.execute_mutation.assert_called_once()
        args = mock_client.execute_mutation.call_args
        assert "deleteTest" in args[0][0]
        assert args[0][1] == {"issueId": "TEST-123"}

    @pytest.mark.asyncio
    async def test_create_manual_test_with_teststep_objects(
        self, test_tools, mock_client
    ):
        """Test creating a manual test using TestStep objects."""
        mock_client.execute_mutation.return_value = {
            "data": {
                "createTest": {
                    "test": {
                        "issueId": "TEST-204",
                        "testType": {"name": "Manual"},
                        "steps": [
                            {
                                "id": "1",
                                "action": "Login to application",
                                "data": "username: admin",
                                "result": "Successfully logged in",
                            },
                            {
                                "id": "2",
                                "action": "Navigate to dashboard",
                                "result": "Dashboard loads correctly",
                            },
                        ],
                        "jira": {"key": "TEST-204", "summary": "Login test with steps"},
                    },
                    "warnings": [],
                }
            }
        }

        # Create test with TestStep objects
        steps = [
            TestStep(
                action="Login to application",
                result="Successfully logged in",
                data="username: admin",
            ),
            TestStep(
                action="Navigate to dashboard", result="Dashboard loads correctly"
            ),
        ]

        result = await test_tools.create_test(
            project_key="TEST",
            summary="Login test with steps",
            test_type="Manual",
            steps=steps,
        )

        assert result["test"]["issueId"] == "TEST-204"
        assert result["test"]["testType"]["name"] == "Manual"
        assert len(result["test"]["steps"]) == 2

        # Verify the mutation was called with correct step format
        mock_client.execute_mutation.assert_called_once()
        args = mock_client.execute_mutation.call_args
        variables = args[0][1]
        assert len(variables["steps"]) == 2
        assert variables["steps"][0]["action"] == "Login to application"
        assert variables["steps"][0]["data"] == "username: admin"
        assert (
            "data" not in variables["steps"][1]
        )  # TestStep without data should omit field

    @pytest.mark.asyncio
    async def test_create_manual_test_without_steps(self, test_tools, mock_client):
        """Test creating a manual test without steps (empty Manual test)."""
        mock_client.execute_mutation.return_value = {
            "data": {
                "createTest": {
                    "test": {
                        "issueId": "TEST-205",
                        "testType": {"name": "Manual"},
                        "steps": [],
                        "jira": {"key": "TEST-205", "summary": "Empty manual test"},
                    },
                    "warnings": [],
                }
            }
        }

        result = await test_tools.create_test(
            project_key="TEST",
            summary="Empty manual test",
            test_type="Manual",
            # No steps provided
        )

        assert result["test"]["issueId"] == "TEST-205"
        assert result["test"]["testType"]["name"] == "Manual"
        assert result["test"]["steps"] == []

        # Verify the mutation was called without steps parameter
        mock_client.execute_mutation.assert_called_once()
        args = mock_client.execute_mutation.call_args
        variables = args[0][1]
        assert (
            "steps" not in variables
        )  # Should not include steps parameter for empty Manual test
        assert variables["testType"]["name"] == "Manual"

    @pytest.mark.asyncio
    async def test_teststep_to_dict_with_data(self):
        """Test TestStep.to_dict() method with data field."""
        step = TestStep(
            action="Click login button",
            result="Login form submits",
            data="Button ID: login-btn",
        )

        expected = {
            "action": "Click login button",
            "result": "Login form submits",
            "data": "Button ID: login-btn",
        }

        assert step.to_dict() == expected

    @pytest.mark.asyncio
    async def test_teststep_to_dict_without_data(self):
        """Test TestStep.to_dict() method without data field."""
        step = TestStep(action="Verify page loads", result="Page loads successfully")

        expected = {"action": "Verify page loads", "result": "Page loads successfully"}

        assert step.to_dict() == expected
        assert "data" not in step.to_dict()

    @pytest.mark.asyncio
    async def test_create_test_step_validation_error(self, test_tools):
        """Test step validation error when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            await test_tools.create_test(
                project_key="TEST",
                summary="Invalid test",
                test_type="Manual",
                steps=[{"action": "Login"}],  # Missing required 'result' field
            )

        assert "must have 'action' and 'result' fields" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_test_invalid_step_type(self, test_tools):
        """Test validation error for invalid step types."""
        with pytest.raises(ValidationError) as exc_info:
            await test_tools.create_test(
                project_key="TEST",
                summary="Invalid test",
                test_type="Manual",
                steps=["invalid_step_type"],  # Steps must be dicts or TestStep objects
            )

        assert "Steps must be either TestStep objects or dictionaries" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_update_test_type(self, test_tools, mock_client):
        """Test updating test type with corrected GraphQL response structure."""
        # Updated mock response to match the corrected GraphQL structure
        mock_client.execute_mutation.return_value = {
            "data": {
                "updateTestType": {
                    "issueId": "TEST-123",
                    "testType": {"name": "Manual", "kind": "Manual"},
                }
            }
        }

        result = await test_tools.update_test_type("TEST-123", "Manual")

        # Should return the direct fields, not nested under 'test'
        assert result["issueId"] == "TEST-123"
        assert result["testType"]["name"] == "Manual"
        assert result["testType"]["kind"] == "Manual"

        # Verify the mutation was called correctly
        mock_client.execute_mutation.assert_called_once()
        args = mock_client.execute_mutation.call_args
        assert "updateTestType" in args[0][0]
        variables = args[0][1]
        assert variables["issueId"] == "TEST-123"
        assert variables["testType"]["name"] == "Manual"

    @pytest.mark.asyncio
    async def test_get_expanded_test(self, test_tools, mock_client):
        """Test getting expanded test with version support."""
        mock_client.execute_query.return_value = {
            "data": {
                "getExpandedTest": {
                    "issueId": "12345",
                    "versionId": 2,
                    "testType": {"name": "Manual"},
                    "steps": [
                        {
                            "id": "1",
                            "action": "Step 1",
                            "parentTestIssueId": None,
                            "calledTestIssueId": "54321",
                        }
                    ],
                    "warnings": [],
                    "jira": {"key": "TEST-123"},
                }
            }
        }

        result = await test_tools.get_expanded_test(
            "12345", test_version_id=2
        )  # Use numeric ID

        assert result["issueId"] == "12345"
        assert result["versionId"] == 2
        assert result["steps"][0]["calledTestIssueId"] == "54321"

        # Verify version parameter was passed
        args = mock_client.execute_query.call_args
        assert args[0][1]["versionId"] == 2

    # ============================================================================
    # NEW TESTS FOR QA FIXES - ID FORMAT CONSISTENCY
    # ============================================================================

    @pytest.mark.asyncio
    async def test_resolve_issue_id_numeric(self, test_tools):
        """Test _resolve_issue_id with numeric ID (should return as-is)."""
        result = await test_tools._resolve_issue_id("1162822")
        assert result == "1162822"

    @pytest.mark.asyncio
    async def test_resolve_issue_id_jira_key(self, test_tools, mock_client):
        """Test _resolve_issue_id with Jira key (should resolve to numeric ID)."""
        mock_client.execute_query.return_value = {
            "data": {
                "getTests": {
                    "results": [
                        {
                            "issueId": "1162822",
                            "jira": {"key": "FRAMED-1693"}
                        }
                    ]
                }
            }
        }
        
        result = await test_tools._resolve_issue_id("FRAMED-1693")
        assert result == "1162822"
        
        # Verify JQL query was used correctly
        mock_client.execute_query.assert_called_once()
        args = mock_client.execute_query.call_args
        assert 'key = "FRAMED-1693"' in args[0][1]["jql"]

    @pytest.mark.asyncio
    async def test_resolve_issue_id_jira_key_not_found(self, test_tools, mock_client):
        """Test _resolve_issue_id when Jira key cannot be resolved."""
        mock_client.execute_query.return_value = {
            "data": {
                "getTests": {
                    "results": []
                }
            }
        }
        
        with pytest.raises(GraphQLError) as exc_info:
            await test_tools._resolve_issue_id("NONEXISTENT-123")
        
        assert "Could not resolve Jira key NONEXISTENT-123" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_test_with_jira_key(self, test_tools, mock_client):
        """Test delete_test with Jira key (should resolve to numeric ID first)."""
        # Mock the resolution query
        mock_client.execute_query.return_value = {
            "data": {
                "getTests": {
                    "results": [
                        {
                            "issueId": "1162822", 
                            "jira": {"key": "FRAMED-1693"}
                        }
                    ]
                }
            }
        }
        
        # Mock the deletion mutation
        mock_client.execute_mutation.return_value = {
            "data": {"deleteTest": True}
        }
        
        result = await test_tools.delete_test("FRAMED-1693")
        
        assert result["success"] is True
        assert result["issueId"] == "1162822"  # Should return resolved numeric ID
        
        # Verify both resolution query and deletion mutation were called
        assert mock_client.execute_query.call_count == 1
        assert mock_client.execute_mutation.call_count == 1
        
        # Verify deletion used resolved numeric ID
        mutation_args = mock_client.execute_mutation.call_args
        assert mutation_args[0][1]["issueId"] == "1162822"

    @pytest.mark.asyncio
    async def test_delete_test_with_numeric_id(self, test_tools, mock_client):
        """Test delete_test with numeric ID (should not need resolution)."""
        mock_client.execute_mutation.return_value = {
            "data": {"deleteTest": True}
        }
        
        result = await test_tools.delete_test("1162822")
        
        assert result["success"] is True
        assert result["issueId"] == "1162822"
        
        # Should only call mutation, not resolution query
        assert mock_client.execute_query.call_count == 0
        assert mock_client.execute_mutation.call_count == 1

    @pytest.mark.asyncio
    async def test_update_test_type_with_jira_key(self, test_tools, mock_client):
        """Test update_test_type with Jira key (should resolve to numeric ID first)."""
        # Mock the resolution query
        mock_client.execute_query.return_value = {
            "data": {
                "getTests": {
                    "results": [
                        {
                            "issueId": "1162822",
                            "jira": {"key": "FRAMED-1693"}
                        }
                    ]
                }
            }
        }
        
        # Mock the update mutation
        mock_client.execute_mutation.return_value = {
            "data": {
                "updateTestType": {
                    "issueId": "1162822",
                    "testType": {"name": "Manual", "kind": "Steps"}
                }
            }
        }
        
        result = await test_tools.update_test_type("FRAMED-1693", "Manual")
        
        assert result["issueId"] == "1162822"
        assert result["testType"]["name"] == "Manual"
        
        # Verify both resolution query and update mutation were called
        assert mock_client.execute_query.call_count == 1
        assert mock_client.execute_mutation.call_count == 1
        
        # Verify update used resolved numeric ID
        mutation_args = mock_client.execute_mutation.call_args
        assert mutation_args[0][1]["issueId"] == "1162822"

    @pytest.mark.asyncio
    async def test_update_test_type_with_numeric_id(self, test_tools, mock_client):
        """Test update_test_type with numeric ID (should not need resolution)."""
        mock_client.execute_mutation.return_value = {
            "data": {
                "updateTestType": {
                    "issueId": "1162822",
                    "testType": {"name": "Manual", "kind": "Steps"}
                }
            }
        }
        
        result = await test_tools.update_test_type("1162822", "Manual")
        
        assert result["issueId"] == "1162822"
        assert result["testType"]["name"] == "Manual"
        
        # Should only call mutation, not resolution query
        assert mock_client.execute_query.call_count == 0
        assert mock_client.execute_mutation.call_count == 1

    # ============================================================================
    # NEW TESTS FOR MANUAL TEST STEPS VALIDATION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_create_manual_test_with_steps_success(self, test_tools, mock_client):
        """Test creating Manual test with steps (fixed validation)."""
        mock_client.execute_mutation.return_value = {
            "data": {
                "createTest": {
                    "test": {
                        "issueId": "1163175",
                        "testType": {"name": "Manual"},
                        "steps": [
                            {
                                "action": "Navigate to login page",
                                "data": "URL: https://example.com/login",
                                "result": "Login page should be displayed"
                            }
                        ],
                        "jira": {"key": "FRAMED-1694", "summary": "Manual Test with Steps"}
                    },
                    "warnings": []
                }
            }
        }
        
        steps = [
            {
                "action": "Navigate to login page",
                "data": "URL: https://example.com/login",
                "result": "Login page should be displayed"
            }
        ]
        
        result = await test_tools.create_test(
            project_key="FRAMED",
            summary="Manual Test with Steps",
            test_type="Manual",
            steps=steps
        )
        
        assert result["test"]["testType"]["name"] == "Manual"
        assert len(result["test"]["steps"]) == 1
        assert result["test"]["steps"][0]["action"] == "Navigate to login page"
        
        # Verify mutation used optional steps parameter (not required)
        mutation_args = mock_client.execute_mutation.call_args
        mutation_query = mutation_args[0][0]
        # Should use optional parameter syntax: $steps: [CreateStepInput!]
        # NOT required syntax: $steps: [CreateStepInput!]!
        assert "$steps: [CreateStepInput!]" in mutation_query
        assert "$steps: [CreateStepInput!]!" not in mutation_query

    @pytest.mark.asyncio
    async def test_create_manual_test_with_teststep_objects(self, test_tools, mock_client):
        """Test creating Manual test with TestStep objects."""
        mock_client.execute_mutation.return_value = {
            "data": {
                "createTest": {
                    "test": {
                        "issueId": "1163175",
                        "testType": {"name": "Manual"},
                        "steps": [
                            {
                                "action": "Navigate to page",
                                "data": "URL: /test",
                                "result": "Page loads"
                            }
                        ],
                        "jira": {"key": "TEST-123", "summary": "Manual Test"}
                    },
                    "warnings": []
                }
            }
        }
        
        steps = [
            TestStep(
                action="Navigate to page",
                data="URL: /test",
                result="Page loads"
            )
        ]
        
        result = await test_tools.create_test(
            project_key="TEST",
            summary="Manual Test",
            test_type="Manual",
            steps=steps
        )
        
        assert result["test"]["testType"]["name"] == "Manual"
        assert len(result["test"]["steps"]) == 1

    # ============================================================================
    # NEW TESTS FOR IMPROVED ERROR HANDLING
    # ============================================================================

    @pytest.mark.asyncio
    async def test_create_test_validation_error_with_context(self, test_tools, mock_client):
        """Test improved error messages for validation failures."""
        mock_client.execute_mutation.return_value = {
            "errors": [
                {"message": "Input validation error: '[JSON_ARRAY]' is not valid under any of the given schemas"}
            ]
        }
        
        steps = [
            {
                "action": "Navigate to login page",
                "result": "Login page should be displayed"
            }
        ]
        
        with pytest.raises(GraphQLError) as exc_info:
            await test_tools.create_test(
                project_key="FRAMED",
                summary="Manual Test",
                test_type="Manual",
                steps=steps
            )
        
        error_message = str(exc_info.value)
        assert "Manual test with 1 steps failed validation" in error_message
        assert "Ensure each step has 'action' and 'result' fields" in error_message
        assert "Example:" in error_message

    @pytest.mark.asyncio
    async def test_delete_test_not_found_error_with_context(self, test_tools, mock_client):
        """Test improved error messages for deletion failures."""
        mock_client.execute_mutation.return_value = {
            "errors": [
                {"message": "test with id FRAMED-1694 not found!"}
            ]
        }
        
        with pytest.raises(GraphQLError) as exc_info:
            await test_tools.delete_test("1162822")
        
        error_message = str(exc_info.value)
        assert "Failed to delete test 1162822" in error_message
        assert "Test with ID/key '1162822' not found" in error_message
        assert "Verify the test exists and you have permission" in error_message

    @pytest.mark.asyncio
    async def test_update_test_type_invalid_id_error_with_context(self, test_tools, mock_client):
        """Test improved error messages for update failures."""
        mock_client.execute_mutation.return_value = {
            "errors": [
                {"message": "issueId provided is not valid"}
            ]
        }
        
        with pytest.raises(GraphQLError) as exc_info:
            await test_tools.update_test_type("1162822", "Manual")
        
        error_message = str(exc_info.value)
        assert "Failed to update test type for 1162822" in error_message
        assert "Issue ID/key '1162822' is not valid" in error_message
        assert "Ensure the test exists and use either numeric ID" in error_message
