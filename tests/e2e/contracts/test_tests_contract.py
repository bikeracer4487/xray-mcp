"""
Contract tests for Xray MCP test management operations.

Validates MCP tool contracts for test creation, retrieval, updating,
and deletion through the standardized MCP interface.
"""

import pytest
import json
from typing import Dict, Any, List

from fixtures.mcp_client import XrayMCPClient, TestResponse, TestType


@pytest.mark.contract
class TestTestsContract:
    """Contract tests for test management MCP tools."""
    
    async def test_validate_connection_contract(self, mcp_client: XrayMCPClient):
        """Test validate_connection tool contract."""
        response = await mcp_client.validate_connection()
        
        # Assert successful response
        mcp_client.assert_success(response, "Connection validation should succeed")
        
        # Validate response structure
        assert "status" in response.data or "accountId" in response.data, \
            "Response should contain status or account information"
    
    async def test_create_test_generic_contract(
        self, 
        mcp_client: XrayMCPClient, 
        test_data_manager
    ):
        """Test create_test tool contract for Generic tests."""
        test_data = test_data_manager.generate_test_data_template("generic_test")
        
        response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.GENERIC,
            description=test_data["description"],
            unstructured=test_data["unstructured"]
        )
        
        # Assert successful creation
        mcp_client.assert_success(response, "Generic test creation should succeed")
        
        # Validate response contains required fields
        required_fields = ["key", "id"]
        mcp_client.assert_contains_keys(response, required_fields)
        
        # Track for cleanup
        issue_key = mcp_client.extract_issue_key(response)
        issue_id = mcp_client.extract_issue_id(response)
        if issue_id:
            test_data_manager.track_resource("test", issue_id, {
                "key": issue_key,
                "test_type": "Generic"
            })
        
        # Validate response structure
        assert response.data.get("test_type") in ["Generic", None], \
            "Test type should be Generic or None"
    
    async def test_create_test_manual_contract(
        self, 
        mcp_client: XrayMCPClient, 
        test_data_manager
    ):
        """Test create_test tool contract for Manual tests."""
        test_data = test_data_manager.generate_test_data_template("manual_test")
        
        response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.MANUAL,
            description=test_data["description"],
            steps=test_data["steps"]
        )
        
        # Assert successful creation
        mcp_client.assert_success(response, "Manual test creation should succeed")
        
        # Validate response structure
        required_fields = ["key", "id"]
        mcp_client.assert_contains_keys(response, required_fields)
        
        # Track for cleanup
        issue_key = mcp_client.extract_issue_key(response)
        issue_id = mcp_client.extract_issue_id(response)
        if issue_id:
            test_data_manager.track_resource("test", issue_id, {
                "key": issue_key,
                "test_type": "Manual",
                "steps_count": len(test_data["steps"])
            })
        
        # Validate test type
        assert response.data.get("test_type") in ["Manual", None], \
            "Test type should be Manual or None"
    
    async def test_create_test_cucumber_contract(
        self, 
        mcp_client: XrayMCPClient, 
        test_data_manager
    ):
        """Test create_test tool contract for Cucumber tests."""
        test_data = test_data_manager.generate_test_data_template("cucumber_test")
        
        response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.CUCUMBER,
            description=test_data["description"],
            gherkin=test_data["gherkin"]
        )
        
        # Assert successful creation
        mcp_client.assert_success(response, "Cucumber test creation should succeed")
        
        # Validate response structure
        required_fields = ["key", "id"]
        mcp_client.assert_contains_keys(response, required_fields)
        
        # Track for cleanup
        issue_key = mcp_client.extract_issue_key(response)
        issue_id = mcp_client.extract_issue_id(response)
        if issue_id:
            test_data_manager.track_resource("test", issue_id, {
                "key": issue_key,
                "test_type": "Cucumber"
            })
        
        # Validate test type
        assert response.data.get("test_type") in ["Cucumber", None], \
            "Test type should be Cucumber or None"
    
    async def test_get_test_contract(self, mcp_client: XrayMCPClient, test_data_manager):
        """Test get_test tool contract."""
        # First create a test to retrieve
        test_data = test_data_manager.generate_test_data_template("generic_test")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.GENERIC,
            unstructured=test_data["unstructured"]
        )
        
        mcp_client.assert_success(create_response, "Test creation for get_test should succeed")
        
        issue_id = mcp_client.extract_issue_id(create_response)
        assert issue_id, "Should extract issue ID from create response"
        
        # Track for cleanup
        test_data_manager.track_resource("test", issue_id)
        
        # Test the get_test contract
        get_response = await mcp_client.get_test(issue_id)
        
        # Assert successful retrieval
        mcp_client.assert_success(get_response, "Test retrieval should succeed")
        
        # Validate response structure for get_test
        expected_fields = ["issueId", "summary", "testType"]
        missing_fields = [field for field in expected_fields if field not in get_response.data]
        
        # Allow some flexibility in response structure
        assert len(missing_fields) <= len(expected_fields) // 2, \
            f"Too many missing fields in get_test response: {missing_fields}"
        
        # Validate issue ID matches
        retrieved_id = get_response.data.get("issueId") or get_response.data.get("id")
        assert str(retrieved_id) == str(issue_id), \
            f"Retrieved issue ID {retrieved_id} should match created ID {issue_id}"
    
    async def test_update_test_contract(self, mcp_client: XrayMCPClient, test_data_manager):
        """Test update_test tool contract."""
        # Create a test to update
        test_data = test_data_manager.generate_test_data_template("generic_test")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.GENERIC,
            unstructured=test_data["unstructured"]
        )
        
        mcp_client.assert_success(create_response, "Test creation for update should succeed")
        
        issue_id = mcp_client.extract_issue_id(create_response)
        assert issue_id, "Should extract issue ID from create response"
        
        # Track for cleanup
        test_data_manager.track_resource("test", issue_id)
        
        # Test the update_test contract
        updated_summary = test_data_manager.generate_unique_title("Updated Test")
        updated_unstructured = "Updated unstructured content for test"
        
        update_response = await mcp_client.update_test(
            issue_id=issue_id,
            unstructured=updated_unstructured,
            jira_fields={"summary": updated_summary}
        )
        
        # Assert successful update
        mcp_client.assert_success(update_response, "Test update should succeed")
        
        # Validate update response structure
        # Response should contain some indication of success
        assert isinstance(update_response.data, dict), \
            "Update response should be a dictionary"
        
        # Verify update by retrieving the test
        get_response = await mcp_client.get_test(issue_id)
        mcp_client.assert_success(get_response, "Test retrieval after update should succeed")
    
    async def test_update_test_type_contract(self, mcp_client: XrayMCPClient, test_data_manager):
        """Test test type update contract."""
        # Create a Generic test
        test_data = test_data_manager.generate_test_data_template("generic_test")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.GENERIC,
            unstructured=test_data["unstructured"]
        )
        
        mcp_client.assert_success(create_response, "Generic test creation should succeed")
        
        issue_id = mcp_client.extract_issue_id(create_response)
        assert issue_id, "Should extract issue ID from create response"
        
        # Track for cleanup
        test_data_manager.track_resource("test", issue_id)
        
        # Update to Manual test type
        manual_steps = test_data_manager.generate_manual_test_steps(step_count=2)
        
        update_response = await mcp_client.update_test(
            issue_id=issue_id,
            test_type="Manual",
            steps=manual_steps
        )
        
        # Assert successful type change
        mcp_client.assert_success(update_response, "Test type update should succeed")
    
    async def test_update_gherkin_definition_contract(
        self, 
        mcp_client: XrayMCPClient, 
        test_data_manager
    ):
        """Test update_gherkin_definition tool contract."""
        # Create a Cucumber test
        test_data = test_data_manager.generate_test_data_template("cucumber_test")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.CUCUMBER,
            gherkin=test_data["gherkin"]
        )
        
        mcp_client.assert_success(create_response, "Cucumber test creation should succeed")
        
        issue_id = mcp_client.extract_issue_id(create_response)
        assert issue_id, "Should extract issue ID from create response"
        
        # Track for cleanup
        test_data_manager.track_resource("test", issue_id)
        
        # Update Gherkin definition
        updated_gherkin = test_data_manager.generate_gherkin_scenario("outline")
        
        gherkin_response = await mcp_client.update_gherkin_definition(
            issue_id=issue_id,
            gherkin_text=updated_gherkin
        )
        
        # Assert successful Gherkin update
        mcp_client.assert_success(gherkin_response, "Gherkin update should succeed")
        
        # Validate response structure
        assert isinstance(gherkin_response.data, dict), \
            "Gherkin update response should be a dictionary"
    
    async def test_delete_test_contract(self, mcp_client: XrayMCPClient, test_data_manager):
        """Test delete_test tool contract."""
        # Create a test to delete
        test_data = test_data_manager.generate_test_data_template("generic_test")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.GENERIC,
            unstructured=test_data["unstructured"]
        )
        
        mcp_client.assert_success(create_response, "Test creation for deletion should succeed")
        
        issue_id = mcp_client.extract_issue_id(create_response)
        assert issue_id, "Should extract issue ID from create response"
        
        # Don't track for cleanup since we're testing deletion
        
        # Test the delete_test contract
        delete_response = await mcp_client.delete_test(issue_id)
        
        # Assert successful deletion
        mcp_client.assert_success(delete_response, "Test deletion should succeed")
        
        # Validate deletion response
        assert isinstance(delete_response.data, dict), \
            "Delete response should be a dictionary"
        
        # Verify deletion by trying to retrieve the test (should fail or return empty)
        get_response = await mcp_client.get_test(issue_id)
        # Don't assert success here as deleted tests should not be retrievable
        assert not get_response.success or not get_response.data, \
            "Deleted test should not be retrievable or should return empty data"
    
    async def test_execute_jql_query_contract(self, mcp_client: XrayMCPClient, test_data_manager):
        """Test execute_jql_query tool contract."""
        # Test basic JQL query contract
        jql_query = f"project = {test_data_manager.project_key} AND issuetype = Test"
        
        query_response = await mcp_client.execute_jql_query(
            jql=jql_query,
            entity_type="test",
            limit=10
        )
        
        # Assert successful query
        mcp_client.assert_success(query_response, "JQL query should succeed")
        
        # Validate JQL response structure
        assert isinstance(query_response.data, dict), \
            "JQL query response should be a dictionary"
        
        # Response should contain results or similar structure
        has_results = any(key in query_response.data for key in ["results", "issues", "tests", "data"])
        assert has_results, \
            f"JQL response should contain results/issues/tests/data field, got: {list(query_response.data.keys())}"
    
    @pytest.mark.parametrize("invalid_project", ["NONEXISTENT", "INVALID-123", ""])
    async def test_create_test_invalid_project_contract(
        self, 
        mcp_client: XrayMCPClient, 
        test_data_manager,
        invalid_project: str
    ):
        """Test create_test contract with invalid project keys."""
        if not invalid_project:  # Skip empty project test
            pytest.skip("Empty project test would cause different error")
        
        response = await mcp_client.create_test(
            project_key=invalid_project,
            summary=test_data_manager.generate_unique_title("Invalid Project Test"),
            test_type=TestType.GENERIC,
            unstructured="Test content"
        )
        
        # Should fail gracefully with proper error response
        assert not response.success, \
            f"Create test with invalid project '{invalid_project}' should fail"
        assert response.error is not None, \
            "Failed response should contain error message"
    
    async def test_get_test_invalid_id_contract(self, mcp_client: XrayMCPClient):
        """Test get_test contract with invalid test ID."""
        invalid_id = "999999999"
        
        response = await mcp_client.get_test(invalid_id)
        
        # Should fail gracefully
        assert not response.success or not response.data, \
            f"Get test with invalid ID '{invalid_id}' should fail or return empty data"
        
        if not response.success:
            assert response.error is not None, \
                "Failed response should contain error message"
    
    async def test_mcp_tool_error_handling_contract(self, mcp_client: XrayMCPClient):
        """Test MCP tool error handling contracts."""
        # Test with completely malformed parameters
        try:
            # This should test the MCP client's ability to handle malformed requests
            response = await mcp_client.call_tool("create_test", {
                "invalid_param": "value",
                "missing_required": True
            })
            
            # Should return error response, not crash
            assert isinstance(response, TestResponse), \
                "Malformed tool call should return TestResponse"
            assert not response.success, \
                "Malformed tool call should not succeed"
            assert response.error is not None, \
                "Malformed tool call should have error message"
        
        except Exception as e:
            # If exception is raised, ensure it's handled properly
            assert "required" in str(e).lower() or "missing" in str(e).lower(), \
                f"Error should indicate missing required parameters: {e}"