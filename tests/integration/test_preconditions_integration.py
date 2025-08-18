"""Integration tests for PreconditionTools against real Xray API.

These tests validate that our mock unit tests accurately represent
the real API behavior for precondition operations.
"""

import pytest
import asyncio
from typing import Dict, Any, List

from tools.preconditions import PreconditionTools
from tools.tests import TestTools
from exceptions import GraphQLError, ValidationError

# Import from conftest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from conftest import INTEGRATION_PROJECT_KEY, INTEGRATION_TEST_PREFIX, wait_for_consistency


@pytest.mark.integration
@pytest.mark.cleanup
class TestPreconditionCRUD:
    """Test precondition CRUD operations against real API."""
    
    async def test_create_precondition_minimal(
        self, 
        precondition_tools, 
        test_tools,
        test_data_tracker, 
        cleanup_helper,
        generate_test_name,
        sample_precondition_definition
    ):
        """Validate creating precondition with minimal required fields."""
        # First create a test to attach precondition to
        test_name = generate_test_name("ForPrecondition")
        test_result = await test_tools.create_test(
            project_key=INTEGRATION_PROJECT_KEY,
            summary=test_name,
            test_type="Generic",
            unstructured="Test for precondition attachment"
        )
        test_id = test_result["test"]["issueId"]
        test_data_tracker.add_test(test_id)
        
        # Create precondition with minimal fields
        # Note: Precondition type must match test type for association to work
        precondition_input = {
            "jira": {
                "fields": {
                    "summary": generate_test_name("Precondition"),
                    "project": {"key": INTEGRATION_PROJECT_KEY}
                }
            },
            "preconditionType": {"name": "Generic"}  # Match the test type
        }
        
        result = await precondition_tools.create_precondition(test_id, precondition_input)
        
        # Validate response structure matches our mocks
        assert "precondition" in result
        assert "issueId" in result["precondition"]
        
        created_id = result["precondition"]["issueId"]
        test_data_tracker.add_precondition(created_id)
        
        # Validate it was added to the test
        if "addedToTest" in result:
            print(f"DEBUG: addedToTest response: {result['addedToTest']}")
            added = result["addedToTest"].get("addedPreconditions", [])
            # addedPreconditions can be a list of IDs or a count
            if isinstance(added, list):
                assert len(added) >= 1, f"Expected at least 1 precondition added, got {added}"
            else:
                assert added >= 1, f"Expected at least 1 precondition added, got {added}"
        
        # Wait for consistency
        await wait_for_consistency()
        
        # Verify precondition appears in test's preconditions
        preconditions = await precondition_tools.get_preconditions(test_id)
        assert preconditions["total"] >= 1
        
        # Find our created precondition
        found = any(p["issueId"] == created_id for p in preconditions["results"])
        assert found, f"Created precondition {created_id} not found in test's preconditions"
    
    async def test_create_precondition_with_all_fields(
        self,
        precondition_tools,
        test_tools,
        test_data_tracker,
        cleanup_helper,
        generate_test_name,
        sample_precondition_definition
    ):
        """Validate creating precondition with all optional fields."""
        # Create test first
        test_result = await test_tools.create_test(
            project_key=INTEGRATION_PROJECT_KEY,
            summary=generate_test_name("ForFullPrecondition"),
            test_type="Manual"
        )
        test_id = test_result["test"]["issueId"]
        test_data_tracker.add_test(test_id)
        
        # Create precondition with all fields
        precondition_input = {
            "jira": {
                "fields": {
                    "summary": generate_test_name("FullPrecondition"),
                    "project": {"key": INTEGRATION_PROJECT_KEY},
                    "description": "Detailed precondition description for integration test"
                }
            },
            "definition": sample_precondition_definition,
            "preconditionType": {"name": "Manual"}
        }
        
        result = await precondition_tools.create_precondition(test_id, precondition_input)
        
        # Validate all fields are present
        precondition = result["precondition"]
        assert precondition["issueId"] is not None
        
        if "definition" in precondition:
            # Strip whitespace for comparison as API may normalize it
            assert sample_precondition_definition.strip() in precondition["definition"]
        
        if "preconditionType" in precondition:
            assert precondition["preconditionType"]["name"] in ["Manual", "Generic"]
        
        test_data_tracker.add_precondition(precondition["issueId"])
    
    async def test_get_preconditions_pagination(
        self,
        precondition_tools,
        test_tools,
        test_data_tracker,
        cleanup_helper,
        generate_test_name
    ):
        """Validate pagination works correctly with real API."""
        # Create a test with multiple preconditions
        test_result = await test_tools.create_test(
            project_key=INTEGRATION_PROJECT_KEY,
            summary=generate_test_name("WithManyPreconditions"),
            test_type="Generic"
        )
        test_id = test_result["test"]["issueId"]
        test_data_tracker.add_test(test_id)
        
        # Create multiple preconditions
        created_ids = []
        for i in range(3):
            input_data = {
                "jira": {
                    "fields": {
                        "summary": generate_test_name(f"Precondition_{i}"),
                        "project": {"key": INTEGRATION_PROJECT_KEY}
                    }
                },
                "definition": f"Precondition {i} definition"
            }
            
            result = await precondition_tools.create_precondition(test_id, input_data)
            created_id = result["precondition"]["issueId"]
            created_ids.append(created_id)
            test_data_tracker.add_precondition(created_id)
        
        await wait_for_consistency()
        
        # Test pagination
        # Get first page
        page1 = await precondition_tools.get_preconditions(test_id, start=0, limit=2)
        assert page1["limit"] == 2
        assert page1["start"] == 0
        assert len(page1["results"]) <= 2
        
        # Get second page
        page2 = await precondition_tools.get_preconditions(test_id, start=2, limit=2)
        assert page2["start"] == 2
        
        # Validate no duplicate IDs across pages
        page1_ids = [p["issueId"] for p in page1["results"]]
        page2_ids = [p["issueId"] for p in page2["results"]]
        assert len(set(page1_ids) & set(page2_ids)) == 0, "Pages should not have duplicate items"
    
    async def test_update_precondition(
        self,
        precondition_tools,
        test_tools,
        test_data_tracker,
        cleanup_helper,
        generate_test_name
    ):
        """Validate updating precondition fields."""
        # Create test and precondition
        test_result = await test_tools.create_test(
            project_key=INTEGRATION_PROJECT_KEY,
            summary=generate_test_name("ForUpdate"),
            test_type="Generic"
        )
        test_id = test_result["test"]["issueId"]
        test_data_tracker.add_test(test_id)
        
        # Create initial precondition
        initial_definition = "Initial precondition definition"
        create_input = {
            "jira": {
                "fields": {
                    "summary": generate_test_name("ToUpdate"),
                "project": {"key": INTEGRATION_PROJECT_KEY}
                }
            },
            "definition": initial_definition,
            "preconditionType": {"name": "Generic"}
        }
        
        create_result = await precondition_tools.create_precondition(test_id, create_input)
        precondition_id = create_result["precondition"]["issueId"]
        test_data_tracker.add_precondition(precondition_id)
        
        await wait_for_consistency()
        
        # Update the precondition
        new_definition = "Updated precondition definition with more details"
        updates = {
            "definition": new_definition,
            "preconditionType": {"name": "Manual"}
        }
        
        update_result = await precondition_tools.update_precondition(precondition_id, updates)
        
        # Validate update response
        assert update_result["issueId"] == precondition_id
        
        if "definition" in update_result:
            assert new_definition in update_result["definition"]
        
        # Verify update persisted
        await wait_for_consistency()
        preconditions = await precondition_tools.get_preconditions(test_id)
        
        updated = next((p for p in preconditions["results"] if p["issueId"] == precondition_id), None)
        if updated and "definition" in updated:
            assert new_definition in updated["definition"]
    
    async def test_delete_precondition(
        self,
        precondition_tools,
        test_tools,
        test_data_tracker,
        cleanup_helper,
        generate_test_name
    ):
        """Validate deleting precondition."""
        # Create test and precondition
        test_result = await test_tools.create_test(
            project_key=INTEGRATION_PROJECT_KEY,
            summary=generate_test_name("ForDelete"),
            test_type="Generic"
        )
        test_id = test_result["test"]["issueId"]
        test_data_tracker.add_test(test_id)
        
        create_input = {
            "jira": {
                "fields": {
                    "summary": generate_test_name("ToDelete"),
                "project": {"key": INTEGRATION_PROJECT_KEY}
                }
            },
            "definition": "This precondition will be deleted"
        }
        
        create_result = await precondition_tools.create_precondition(test_id, create_input)
        precondition_id = create_result["precondition"]["issueId"]
        
        await wait_for_consistency()
        
        # Delete the precondition
        delete_result = await precondition_tools.delete_precondition(precondition_id)
        
        # Validate deletion response
        assert delete_result["success"] is True
        assert delete_result["deletedPreconditionId"] == precondition_id
        
        # Don't track for cleanup since it's already deleted
        
        # Verify it's removed from test
        await wait_for_consistency()
        preconditions = await precondition_tools.get_preconditions(test_id)
        
        # Should not find deleted precondition
        found = any(p["issueId"] == precondition_id for p in preconditions["results"])
        assert not found, f"Deleted precondition {precondition_id} still appears in test"


@pytest.mark.integration
class TestPreconditionValidation:
    """Test validation and error handling with real API."""
    
    async def test_create_without_required_jira_field(self, precondition_tools, test_tools, test_data_tracker, cleanup_helper):
        """Validate error when missing required jira field."""
        # Create test first
        test_result = await test_tools.create_test(
            project_key=INTEGRATION_PROJECT_KEY,
            summary=f"{INTEGRATION_TEST_PREFIX}_ValidationTest",
            test_type="Generic"
        )
        test_id = test_result["test"]["issueId"]
        test_data_tracker.add_test(test_id)
        
        # Try to create without jira field
        invalid_input = {
            "definition": "Missing jira field"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            await precondition_tools.create_precondition(test_id, invalid_input)
        
        assert "jira" in str(exc_info.value).lower()
    
    async def test_get_preconditions_limit_validation(self, precondition_tools):
        """Validate limit exceeding 100 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            await precondition_tools.get_preconditions("TEST-123", limit=101)
        
        assert "100" in str(exc_info.value) or "limit" in str(exc_info.value).lower()
    
    async def test_string_to_object_type_conversion(
        self,
        precondition_tools,
        test_tools,
        test_data_tracker,
        cleanup_helper,
        generate_test_name
    ):
        """Validate string preconditionType is converted to object."""
        # Create test
        test_result = await test_tools.create_test(
            project_key=INTEGRATION_PROJECT_KEY,
            summary=generate_test_name("TypeConversion"),
            test_type="Generic"
        )
        test_id = test_result["test"]["issueId"]
        test_data_tracker.add_test(test_id)
        
        # Create with string type (should be converted internally)
        input_data = {
            "jira": {
                "fields": {
                    "summary": generate_test_name("StringType"),
                "project": {"key": INTEGRATION_PROJECT_KEY}
                }
            },
            "preconditionType": "Manual"  # String instead of object
        }
        
        result = await precondition_tools.create_precondition(test_id, input_data)
        
        # Should succeed - string was converted to {"name": "Manual"}
        assert result["precondition"]["issueId"] is not None
        test_data_tracker.add_precondition(result["precondition"]["issueId"])
        
        # Verify type in response
        if "preconditionType" in result["precondition"]:
            assert result["precondition"]["preconditionType"]["name"] == "Manual"
    
    async def test_invalid_type_format(self, precondition_tools, test_tools, test_data_tracker, cleanup_helper):
        """Validate invalid preconditionType format is rejected."""
        # Create test
        test_result = await test_tools.create_test(
            project_key=INTEGRATION_PROJECT_KEY,
            summary=f"{INTEGRATION_TEST_PREFIX}_InvalidType",
            test_type="Generic"
        )
        test_id = test_result["test"]["issueId"]
        test_data_tracker.add_test(test_id)
        
        # Try with invalid type (number)
        invalid_input = {
            "jira": {
                "fields": {
                    "summary": f"{INTEGRATION_TEST_PREFIX}_InvalidTypePrecondition",
                "project": {"key": INTEGRATION_PROJECT_KEY}
                }
            },
            "preconditionType": 123  # Invalid - should be string or object
        }
        
        with pytest.raises(ValidationError) as exc_info:
            await precondition_tools.create_precondition(test_id, invalid_input)
        
        assert "preconditionType" in str(exc_info.value) or "string or object" in str(exc_info.value)


@pytest.mark.integration
class TestPreconditionEdgeCases:
    """Test edge cases and boundary conditions with real API."""
    
    async def test_empty_preconditions_list(self, precondition_tools, test_tools, test_data_tracker, cleanup_helper):
        """Validate handling of test with no preconditions."""
        # Create test without preconditions
        test_result = await test_tools.create_test(
            project_key=INTEGRATION_PROJECT_KEY,
            summary=f"{INTEGRATION_TEST_PREFIX}_NoPreconditions",
            test_type="Generic"
        )
        test_id = test_result["test"]["issueId"]
        test_data_tracker.add_test(test_id)
        
        # Get preconditions (should be empty)
        result = await precondition_tools.get_preconditions(test_id)
        
        assert result["total"] == 0
        assert result["results"] == []
        assert result["start"] == 0
    
    async def test_id_resolution_with_jira_key(
        self,
        precondition_tools,
        test_tools,
        test_data_tracker,
        cleanup_helper,
        generate_test_name
    ):
        """Validate ID resolution works with Jira keys."""
        # Create test and get its Jira key
        test_result = await test_tools.create_test(
            project_key=INTEGRATION_PROJECT_KEY,
            summary=generate_test_name("IDResolution"),
            test_type="Generic"
        )
        test_id = test_result["test"]["issueId"]
        test_jira_key = test_result["test"]["jira"]["key"]  # e.g., "FTEST-123"
        test_data_tracker.add_test(test_id)
        
        # Create precondition
        input_data = {
            "jira": {
                "fields": {
                    "summary": generate_test_name("ForIDResolution"),
                "project": {"key": INTEGRATION_PROJECT_KEY}
                }
            }
        }
        
        create_result = await precondition_tools.create_precondition(test_id, input_data)
        precondition_id = create_result["precondition"]["issueId"]
        test_data_tracker.add_precondition(precondition_id)
        
        await wait_for_consistency()
        
        # Get preconditions using Jira key instead of internal ID
        result = await precondition_tools.get_preconditions(test_jira_key)
        
        # Should resolve key and return preconditions
        assert result["total"] >= 1
        found = any(p["issueId"] == precondition_id for p in result["results"])
        assert found, "Should find precondition when using Jira key"
    
    async def test_partial_update(
        self,
        precondition_tools,
        test_tools,
        test_data_tracker,
        cleanup_helper,
        generate_test_name
    ):
        """Validate partial updates only change specified fields."""
        # Create test and precondition
        test_result = await test_tools.create_test(
            project_key=INTEGRATION_PROJECT_KEY,
            summary=generate_test_name("PartialUpdate"),
            test_type="Generic"
        )
        test_id = test_result["test"]["issueId"]
        test_data_tracker.add_test(test_id)
        
        original_definition = "Original definition"
        create_input = {
            "jira": {
                "fields": {
                    "summary": generate_test_name("PartialUpdatePrecondition"),
                "project": {"key": INTEGRATION_PROJECT_KEY}
                }
            },
            "definition": original_definition,
            "preconditionType": {"name": "Generic"}
        }
        
        create_result = await precondition_tools.create_precondition(test_id, create_input)
        precondition_id = create_result["precondition"]["issueId"]
        test_data_tracker.add_precondition(precondition_id)
        
        await wait_for_consistency()
        
        # Update only definition, not type
        new_definition = "Partially updated definition"
        update_result = await precondition_tools.update_precondition(
            precondition_id,
            {"definition": new_definition}
        )
        
        # Type should remain unchanged
        if "preconditionType" in update_result:
            assert update_result["preconditionType"]["name"] == "Generic"
        
        # Definition should be updated
        if "definition" in update_result:
            assert new_definition in update_result["definition"]
    
    async def test_concurrent_precondition_operations(
        self,
        precondition_tools,
        test_tools,
        test_data_tracker,
        cleanup_helper,
        generate_test_name
    ):
        """Test concurrent precondition operations."""
        # Create test
        test_result = await test_tools.create_test(
            project_key=INTEGRATION_PROJECT_KEY,
            summary=generate_test_name("ConcurrentOps"),
            test_type="Generic"
        )
        test_id = test_result["test"]["issueId"]
        test_data_tracker.add_test(test_id)
        
        # Create multiple preconditions concurrently
        create_tasks = []
        for i in range(3):
            input_data = {
                "jira": {
                "fields": {
                    "summary": generate_test_name(f"Concurrent_{i}"),
                    "project": {"key": INTEGRATION_PROJECT_KEY}
                    }
                },
                "definition": f"Concurrent precondition {i}"
            }
            create_tasks.append(
                precondition_tools.create_precondition(test_id, input_data)
            )
        
        # Execute concurrently
        results = await asyncio.gather(*create_tasks, return_exceptions=True)
        
        # Track created IDs for cleanup
        created_ids = []
        for result in results:
            if not isinstance(result, Exception):
                if "precondition" in result and "issueId" in result["precondition"]:
                    created_ids.append(result["precondition"]["issueId"])
                    test_data_tracker.add_precondition(result["precondition"]["issueId"])
        
        # All should succeed
        assert len(created_ids) == 3, f"Expected 3 preconditions created, got {len(created_ids)}"
        
        # Verify all were added to test
        await wait_for_consistency()
        preconditions = await precondition_tools.get_preconditions(test_id)
        
        for created_id in created_ids:
            found = any(p["issueId"] == created_id for p in preconditions["results"])
            assert found, f"Concurrent precondition {created_id} not found"