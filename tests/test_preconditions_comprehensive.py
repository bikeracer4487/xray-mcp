"""Comprehensive tests for PreconditionTools.

Tests cover CRUD operations, validation, ID resolution, and edge cases.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

from tools.preconditions import PreconditionTools
from client.graphql import XrayGraphQLClient
from exceptions import GraphQLError, ValidationError
from utils.id_resolver import IssueIdResolver


@pytest.fixture
def mock_graphql_client():
    """Create mock GraphQL client."""
    client = AsyncMock(spec=XrayGraphQLClient)
    return client


@pytest.fixture
def mock_id_resolver():
    """Create mock ID resolver."""
    resolver = AsyncMock(spec=IssueIdResolver)
    resolver.resolve_issue_id = AsyncMock(side_effect=lambda x: f"resolved_{x}")
    return resolver


@pytest.fixture
def precondition_tools(mock_graphql_client, mock_id_resolver, mocker):
    """Create PreconditionTools with mocked dependencies."""
    mocker.patch('tools.preconditions.IssueIdResolver', return_value=mock_id_resolver)
    tools = PreconditionTools(mock_graphql_client)
    tools.id_resolver = mock_id_resolver
    return tools


@pytest.mark.asyncio
@pytest.mark.unit
class TestGetPreconditions:
    """Test precondition retrieval."""

    async def test_get_preconditions_success(self, precondition_tools, mock_graphql_client):
        """Test successful precondition retrieval with pagination."""
        mock_response = {
            "data": {
                "getTest": {
                    "preconditions": {
                        "total": 25,
                        "start": 0,
                        "limit": 10,
                        "results": [
                            {
                                "issueId": "PREC-1",
                                "definition": "Setup test data",
                                "preconditionType": {"name": "Manual", "kind": "MANUAL"}
                            },
                            {
                                "issueId": "PREC-2",
                                "definition": "Clear cache",
                                "preconditionType": {"name": "Generic", "kind": "GENERIC"}
                            }
                        ]
                    }
                }
            }
        }
        mock_graphql_client.execute_query = AsyncMock(return_value=mock_response)
        
        result = await precondition_tools.get_preconditions("TEST-123", start=0, limit=10)
        
        assert result["total"] == 25
        assert result["start"] == 0
        assert result["limit"] == 10
        assert len(result["results"]) == 2
        assert result["results"][0]["issueId"] == "PREC-1"

    async def test_get_preconditions_limit_validation(self, precondition_tools):
        """Test limit exceeding 100 raises ValidationError."""
        with pytest.raises(ValidationError, match="Limit cannot exceed 100"):
            await precondition_tools.get_preconditions("TEST-123", limit=101)

    async def test_get_preconditions_pagination_boundary(self, precondition_tools, mock_graphql_client):
        """Test pagination at boundary conditions."""
        mock_response = {
            "data": {
                "getTest": {
                    "preconditions": {
                        "total": 100,
                        "start": 99,
                        "limit": 1,
                        "results": [{"issueId": "PREC-100"}]
                    }
                }
            }
        }
        mock_graphql_client.execute_query = AsyncMock(return_value=mock_response)
        
        # Get last item
        result = await precondition_tools.get_preconditions("TEST-123", start=99, limit=1)
        assert result["start"] == 99
        assert len(result["results"]) == 1

    async def test_get_preconditions_empty_results(self, precondition_tools, mock_graphql_client):
        """Test handling empty precondition list."""
        mock_response = {
            "data": {
                "getTest": {
                    "preconditions": {
                        "total": 0,
                        "start": 0,
                        "limit": 100,
                        "results": []
                    }
                }
            }
        }
        mock_graphql_client.execute_query = AsyncMock(return_value=mock_response)
        
        result = await precondition_tools.get_preconditions("TEST-123")
        assert result["total"] == 0
        assert result["results"] == []

    async def test_get_preconditions_id_resolution(self, precondition_tools, mock_graphql_client, mock_id_resolver):
        """Test issue ID resolution for Jira keys."""
        mock_response = {"data": {"getTest": {"preconditions": {"results": []}}}}
        mock_graphql_client.execute_query = AsyncMock(return_value=mock_response)
        
        await precondition_tools.get_preconditions("TEST-123")
        
        # Verify ID was resolved
        mock_id_resolver.resolve_issue_id.assert_called_once_with("TEST-123")
        
        # Verify resolved ID was used in query
        call_args = mock_graphql_client.execute_query.call_args
        assert call_args[0][1]["issueId"] == "resolved_TEST-123"

    async def test_get_preconditions_graphql_error(self, precondition_tools, mock_graphql_client):
        """Test GraphQL error propagation."""
        mock_graphql_client.execute_query = AsyncMock(
            side_effect=GraphQLError("Invalid query")
        )
        
        with pytest.raises(GraphQLError, match="Invalid query"):
            await precondition_tools.get_preconditions("TEST-123")


@pytest.mark.asyncio
@pytest.mark.unit
class TestCreatePrecondition:
    """Test precondition creation."""

    async def test_create_precondition_minimal_fields(self, precondition_tools, mock_graphql_client):
        """Test creation with only required fields."""
        create_response = {
            "data": {
                "createPrecondition": {
                    "precondition": {
                        "issueId": "PREC-NEW",
                        "preconditionType": {"name": "Generic", "kind": "GENERIC"}
                    },
                    "warnings": None
                }
            }
        }
        add_response = {
            "data": {
                "addPreconditionsToTest": {
                    "addedPreconditions": 1,
                    "warning": None
                }
            }
        }
        mock_graphql_client.execute_query = AsyncMock(
            side_effect=[create_response, add_response]
        )
        
        input_data = {
            "jira": {
                "summary": "New precondition",
                "project": {"key": "PROJ"}
            }
        }
        
        result = await precondition_tools.create_precondition("TEST-123", input_data)
        
        assert result["precondition"]["issueId"] == "PREC-NEW"
        assert result["addedToTest"]["addedPreconditions"] == 1

    async def test_create_precondition_with_all_fields(self, precondition_tools, mock_graphql_client):
        """Test creation with all optional fields."""
        create_response = {
            "data": {
                "createPrecondition": {
                    "precondition": {
                        "issueId": "PREC-FULL",
                        "definition": "Complete setup",
                        "preconditionType": {"name": "Manual", "kind": "MANUAL"}
                    }
                }
            }
        }
        add_response = {"data": {"addPreconditionsToTest": {"addedPreconditions": 1}}}
        mock_graphql_client.execute_query = AsyncMock(
            side_effect=[create_response, add_response]
        )
        
        input_data = {
            "jira": {"summary": "Full precondition", "project": {"key": "PROJ"}},
            "definition": "Complete setup",
            "preconditionType": {"name": "Manual"}
        }
        
        result = await precondition_tools.create_precondition("TEST-123", input_data)
        assert result["precondition"]["definition"] == "Complete setup"

    async def test_create_precondition_string_type_conversion(self, precondition_tools, mock_graphql_client):
        """Test string preconditionType conversion to object."""
        mock_graphql_client.execute_query = AsyncMock(
            return_value={"data": {"createPrecondition": {"precondition": {"issueId": "PREC-1"}}}}
        )
        
        input_data = {
            "jira": {"summary": "Test", "project": {"key": "PROJ"}},
            "preconditionType": "Manual"  # String instead of object
        }
        
        await precondition_tools.create_precondition("TEST-123", input_data)
        
        # Verify string was converted to object format
        call_args = mock_graphql_client.execute_query.call_args[0][1]
        assert call_args["preconditionType"] == {"name": "Manual"}

    async def test_create_precondition_invalid_type_format(self, precondition_tools):
        """Test invalid preconditionType format raises error."""
        input_data = {
            "jira": {"summary": "Test", "project": {"key": "PROJ"}},
            "preconditionType": 123  # Invalid type
        }
        
        with pytest.raises(ValidationError, match="preconditionType must be a string or object"):
            await precondition_tools.create_precondition("TEST-123", input_data)

    async def test_create_precondition_missing_jira(self, precondition_tools):
        """Test missing required jira field."""
        with pytest.raises(ValidationError, match="jira object is required"):
            await precondition_tools.create_precondition("TEST-123", {"definition": "test"})

    async def test_create_precondition_no_add_to_test(self, precondition_tools, mock_graphql_client):
        """Test handling when precondition creation doesn't return issueId."""
        create_response = {
            "data": {
                "createPrecondition": {
                    "precondition": {},  # No issueId
                    "warnings": "Some warning"
                }
            }
        }
        mock_graphql_client.execute_query = AsyncMock(return_value=create_response)
        
        input_data = {"jira": {"summary": "Test", "project": {"key": "PROJ"}}}
        result = await precondition_tools.create_precondition("TEST-123", input_data)
        
        # Should not attempt to add to test
        assert "addedToTest" not in result
        assert mock_graphql_client.execute_query.call_count == 1


@pytest.mark.asyncio
@pytest.mark.unit
class TestUpdatePrecondition:
    """Test precondition updates."""

    async def test_update_precondition_success(self, precondition_tools, mock_graphql_client):
        """Test successful precondition update."""
        mock_response = {
            "data": {
                "updatePrecondition": {
                    "issueId": "PREC-1",
                    "definition": "Updated definition",
                    "preconditionType": {"name": "Manual", "kind": "MANUAL"},
                    "jira": {"key": "PREC-1", "summary": "Updated", "updated": "2024-01-01"}
                }
            }
        }
        mock_graphql_client.execute_query = AsyncMock(return_value=mock_response)
        
        updates = {
            "definition": "Updated definition",
            "preconditionType": {"name": "Manual"}
        }
        
        result = await precondition_tools.update_precondition("PREC-1", updates)
        assert result["definition"] == "Updated definition"
        assert result["jira"]["updated"] == "2024-01-01"

    async def test_update_precondition_partial_update(self, precondition_tools, mock_graphql_client):
        """Test partial update with single field."""
        mock_response = {
            "data": {
                "updatePrecondition": {
                    "issueId": "PREC-1",
                    "definition": "New definition only"
                }
            }
        }
        mock_graphql_client.execute_query = AsyncMock(return_value=mock_response)
        
        result = await precondition_tools.update_precondition("PREC-1", {"definition": "New definition only"})
        assert result["definition"] == "New definition only"

    async def test_update_precondition_id_resolution(self, precondition_tools, mock_graphql_client, mock_id_resolver):
        """Test ID resolution for update."""
        mock_graphql_client.execute_query = AsyncMock(
            return_value={"data": {"updatePrecondition": {}}}
        )
        
        await precondition_tools.update_precondition("PREC-KEY", {"definition": "test"})
        
        mock_id_resolver.resolve_issue_id.assert_called_once_with("PREC-KEY")
        call_args = mock_graphql_client.execute_query.call_args[0][1]
        assert call_args["issueId"] == "resolved_PREC-KEY"

    async def test_update_precondition_invalid_updates(self, precondition_tools, mock_graphql_client):
        """Test GraphQL error on invalid update data."""
        mock_graphql_client.execute_query = AsyncMock(
            side_effect=GraphQLError("Invalid update fields")
        )
        
        with pytest.raises(GraphQLError, match="Invalid update fields"):
            await precondition_tools.update_precondition("PREC-1", {"invalid": "field"})


@pytest.mark.asyncio
@pytest.mark.unit
class TestDeletePrecondition:
    """Test precondition deletion."""

    async def test_delete_precondition_success(self, precondition_tools, mock_graphql_client):
        """Test successful deletion."""
        mock_response = {
            "data": {
                "deletePrecondition": {
                    "success": True
                }
            }
        }
        mock_graphql_client.execute_query = AsyncMock(return_value=mock_response)
        
        result = await precondition_tools.delete_precondition("PREC-1")
        
        assert result["success"] is True
        assert result["deletedPreconditionId"] == "PREC-1"

    async def test_delete_precondition_failure(self, precondition_tools, mock_graphql_client):
        """Test deletion failure returns false."""
        mock_response = {
            "data": {
                "deletePrecondition": {
                    "success": False
                }
            }
        }
        mock_graphql_client.execute_query = AsyncMock(return_value=mock_response)
        
        result = await precondition_tools.delete_precondition("PREC-NONEXISTENT")
        
        assert result["success"] is False
        assert result["deletedPreconditionId"] == "PREC-NONEXISTENT"

    async def test_delete_precondition_id_resolution(self, precondition_tools, mock_graphql_client, mock_id_resolver):
        """Test ID resolution for deletion."""
        mock_graphql_client.execute_query = AsyncMock(
            return_value={"data": {"deletePrecondition": {"success": True}}}
        )
        
        await precondition_tools.delete_precondition("PREC-KEY")
        
        mock_id_resolver.resolve_issue_id.assert_called_once_with("PREC-KEY")
        call_args = mock_graphql_client.execute_query.call_args[0][1]
        assert call_args["preconditionId"] == "resolved_PREC-KEY"

    async def test_delete_precondition_graphql_error(self, precondition_tools, mock_graphql_client):
        """Test GraphQL error during deletion."""
        mock_graphql_client.execute_query = AsyncMock(
            side_effect=GraphQLError("Insufficient permissions")
        )
        
        with pytest.raises(GraphQLError, match="Insufficient permissions"):
            await precondition_tools.delete_precondition("PREC-1")


@pytest.mark.asyncio
@pytest.mark.integration
class TestPreconditionToolsIntegration:
    """Integration tests for precondition tools."""

    async def test_full_precondition_lifecycle(self, precondition_tools, mock_graphql_client):
        """Test complete CRUD lifecycle."""
        # Create
        create_response = {
            "data": {
                "createPrecondition": {
                    "precondition": {"issueId": "PREC-NEW"},
                    "warnings": None
                }
            }
        }
        add_response = {"data": {"addPreconditionsToTest": {"addedPreconditions": 1}}}
        
        # Get
        get_response = {
            "data": {
                "getTest": {
                    "preconditions": {
                        "results": [{"issueId": "PREC-NEW", "definition": "Initial"}]
                    }
                }
            }
        }
        
        # Update
        update_response = {
            "data": {
                "updatePrecondition": {
                    "issueId": "PREC-NEW",
                    "definition": "Updated"
                }
            }
        }
        
        # Delete
        delete_response = {"data": {"deletePrecondition": {"success": True}}}
        
        mock_graphql_client.execute_query = AsyncMock(
            side_effect=[
                create_response, add_response,
                get_response,
                update_response,
                delete_response
            ]
        )
        
        # Create
        input_data = {"jira": {"summary": "Test", "project": {"key": "PROJ"}}}
        create_result = await precondition_tools.create_precondition("TEST-123", input_data)
        assert create_result["precondition"]["issueId"] == "PREC-NEW"
        
        # Get
        get_result = await precondition_tools.get_preconditions("TEST-123")
        assert get_result["results"][0]["definition"] == "Initial"
        
        # Update
        update_result = await precondition_tools.update_precondition("PREC-NEW", {"definition": "Updated"})
        assert update_result["definition"] == "Updated"
        
        # Delete
        delete_result = await precondition_tools.delete_precondition("PREC-NEW")
        assert delete_result["success"] is True

    async def test_pagination_full_traversal(self, precondition_tools, mock_graphql_client):
        """Test paginating through all preconditions."""
        # Simulate 250 preconditions with 100-item pages
        page1 = {
            "data": {
                "getTest": {
                    "preconditions": {
                        "total": 250,
                        "start": 0,
                        "limit": 100,
                        "results": [{"issueId": f"PREC-{i}"} for i in range(100)]
                    }
                }
            }
        }
        page2 = {
            "data": {
                "getTest": {
                    "preconditions": {
                        "total": 250,
                        "start": 100,
                        "limit": 100,
                        "results": [{"issueId": f"PREC-{i}"} for i in range(100, 200)]
                    }
                }
            }
        }
        page3 = {
            "data": {
                "getTest": {
                    "preconditions": {
                        "total": 250,
                        "start": 200,
                        "limit": 100,
                        "results": [{"issueId": f"PREC-{i}"} for i in range(200, 250)]
                    }
                }
            }
        }
        
        mock_graphql_client.execute_query = AsyncMock(
            side_effect=[page1, page2, page3]
        )
        
        all_results = []
        for start in [0, 100, 200]:
            result = await precondition_tools.get_preconditions("TEST-123", start=start, limit=100)
            all_results.extend(result["results"])
        
        assert len(all_results) == 250
        assert all_results[0]["issueId"] == "PREC-0"
        assert all_results[-1]["issueId"] == "PREC-249"