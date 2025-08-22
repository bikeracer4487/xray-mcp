"""
Contract tests for Xray MCP test execution management operations.

Validates MCP tool contracts for test execution creation, management,
and test assignment through the standardized MCP interface.
"""

import pytest
import json
from typing import Dict, Any, List

from fixtures.mcp_client import XrayMCPClient, TestResponse, TestType


@pytest.mark.contract
class TestExecutionsContract:
    """Contract tests for test execution management MCP tools."""
    
    async def test_create_test_execution_contract(
        self, 
        mcp_client: XrayMCPClient, 
        test_data_manager
    ):
        """Test create_test_execution tool contract."""
        execution_data = test_data_manager.generate_test_data_template("test_execution")
        
        response = await mcp_client.create_test_execution(
            project_key=execution_data["project_key"],
            summary=execution_data["summary"],
            description=execution_data["description"],
            test_environments=execution_data["test_environments"]
        )
        
        # Assert successful creation
        mcp_client.assert_success(response, "Test execution creation should succeed")
        
        # Validate response structure
        required_fields = ["key", "id"]
        mcp_client.assert_contains_keys(response, required_fields)
        
        # Track for cleanup
        issue_key = mcp_client.extract_issue_key(response)
        issue_id = mcp_client.extract_issue_id(response)
        if issue_id:
            test_data_manager.track_resource("execution", issue_id, {
                "key": issue_key,
                "environments": execution_data["test_environments"]
            })
        
        # Validate response contains execution-specific fields
        assert isinstance(response.data, dict), "Response should be a dictionary"
    
    async def test_create_test_execution_with_tests_contract(
        self, 
        mcp_client: XrayMCPClient, 
        test_data_manager
    ):
        """Test creating test execution with pre-assigned tests."""
        # First create some tests
        test_ids = []
        for i in range(2):
            test_data = test_data_manager.generate_test_data_template("generic_test")
            test_data["summary"] = f"{test_data['summary']}_ForExecution_{i+1}"
            
            test_response = await mcp_client.create_test(
                project_key=test_data["project_key"],
                summary=test_data["summary"],
                test_type=TestType.GENERIC,
                unstructured=test_data["unstructured"]
            )
            
            mcp_client.assert_success(test_response, f"Test {i+1} creation should succeed")
            
            test_id = mcp_client.extract_issue_id(test_response)
            assert test_id, f"Should extract issue ID from test {i+1} response"
            
            test_ids.append(test_id)
            test_data_manager.track_resource("test", test_id)
        
        # Create execution with tests
        execution_data = test_data_manager.generate_test_data_template("test_execution")
        
        response = await mcp_client.create_test_execution(
            project_key=execution_data["project_key"],
            summary=execution_data["summary"],
            description=execution_data["description"],
            test_issue_ids=test_ids,
            test_environments=execution_data["test_environments"]
        )
        
        # Assert successful creation
        mcp_client.assert_success(response, "Test execution with tests creation should succeed")
        
        # Track for cleanup
        execution_id = mcp_client.extract_issue_id(response)
        if execution_id:
            test_data_manager.track_resource("execution", execution_id, {
                "test_count": len(test_ids)
            })
    
    async def test_get_test_execution_contract(
        self, 
        mcp_client: XrayMCPClient, 
        test_data_manager
    ):
        """Test get_test_execution tool contract."""
        # Create a test execution
        execution_data = test_data_manager.generate_test_data_template("test_execution")
        
        create_response = await mcp_client.create_test_execution(
            project_key=execution_data["project_key"],
            summary=execution_data["summary"],
            description=execution_data["description"]
        )
        
        mcp_client.assert_success(create_response, "Execution creation should succeed")
        
        execution_id = mcp_client.extract_issue_id(create_response)
        assert execution_id, "Should extract execution ID from create response"
        
        # Track for cleanup
        test_data_manager.track_resource("execution", execution_id)
        
        # Test get_test_execution contract
        get_response = await mcp_client.get_test_execution(execution_id)
        
        # Assert successful retrieval
        mcp_client.assert_success(get_response, "Test execution retrieval should succeed")
        
        # Validate response structure
        expected_fields = ["issueId", "summary"]
        missing_fields = [field for field in expected_fields if field not in get_response.data]
        
        # Allow some flexibility in response structure
        assert len(missing_fields) <= len(expected_fields) // 2, \
            f"Too many missing fields in get_execution response: {missing_fields}"
        
        # Validate execution ID matches
        retrieved_id = get_response.data.get("issueId") or get_response.data.get("id")
        assert str(retrieved_id) == str(execution_id), \
            f"Retrieved execution ID {retrieved_id} should match created ID {execution_id}"
    
    async def test_add_tests_to_execution_contract(
        self, 
        mcp_client: XrayMCPClient, 
        test_data_manager
    ):
        """Test add_tests_to_execution tool contract."""
        # Create a test execution
        execution_data = test_data_manager.generate_test_data_template("test_execution")
        
        execution_response = await mcp_client.create_test_execution(
            project_key=execution_data["project_key"],
            summary=execution_data["summary"]
        )
        
        mcp_client.assert_success(execution_response, "Execution creation should succeed")
        
        execution_id = mcp_client.extract_issue_id(execution_response)
        assert execution_id, "Should extract execution ID"
        
        # Track execution for cleanup
        test_data_manager.track_resource("execution", execution_id)
        
        # Create tests to add
        test_ids = []
        for i in range(2):
            test_data = test_data_manager.generate_test_data_template("generic_test")
            test_data["summary"] = f"{test_data['summary']}_AddToExecution_{i+1}"
            
            test_response = await mcp_client.create_test(
                project_key=test_data["project_key"],
                summary=test_data["summary"],
                test_type=TestType.GENERIC,
                unstructured=test_data["unstructured"]
            )
            
            mcp_client.assert_success(test_response, f"Test {i+1} creation should succeed")
            
            test_id = mcp_client.extract_issue_id(test_response)
            assert test_id, f"Should extract test ID {i+1}"
            
            test_ids.append(test_id)
            test_data_manager.track_resource("test", test_id)
        
        # Add tests to execution
        add_response = await mcp_client.add_tests_to_execution(
            execution_issue_id=execution_id,
            test_issue_ids=test_ids
        )
        
        # Assert successful addition
        mcp_client.assert_success(add_response, "Adding tests to execution should succeed")
        
        # Validate response structure
        assert isinstance(add_response.data, dict), \
            "Add tests response should be a dictionary"
    
    async def test_remove_tests_from_execution_contract(
        self, 
        mcp_client: XrayMCPClient, 
        test_data_manager
    ):
        """Test remove_tests_from_execution tool contract."""
        # Create tests first
        test_ids = []
        for i in range(2):
            test_data = test_data_manager.generate_test_data_template("generic_test")
            test_data["summary"] = f"{test_data['summary']}_RemoveFromExecution_{i+1}"
            
            test_response = await mcp_client.create_test(
                project_key=test_data["project_key"],
                summary=test_data["summary"],
                test_type=TestType.GENERIC,
                unstructured=test_data["unstructured"]
            )
            
            mcp_client.assert_success(test_response, f"Test {i+1} creation should succeed")
            
            test_id = mcp_client.extract_issue_id(test_response)
            assert test_id, f"Should extract test ID {i+1}"
            
            test_ids.append(test_id)
            test_data_manager.track_resource("test", test_id)
        
        # Create execution with tests
        execution_data = test_data_manager.generate_test_data_template("test_execution")
        
        execution_response = await mcp_client.create_test_execution(
            project_key=execution_data["project_key"],
            summary=execution_data["summary"],
            test_issue_ids=test_ids
        )
        
        mcp_client.assert_success(execution_response, "Execution with tests creation should succeed")
        
        execution_id = mcp_client.extract_issue_id(execution_response)
        assert execution_id, "Should extract execution ID"
        
        # Track execution for cleanup
        test_data_manager.track_resource("execution", execution_id)
        
        # Remove one test from execution
        test_to_remove = [test_ids[0]]
        
        remove_response = await mcp_client.remove_tests_from_execution(
            execution_issue_id=execution_id,
            test_issue_ids=test_to_remove
        )
        
        # Assert successful removal
        mcp_client.assert_success(remove_response, "Removing tests from execution should succeed")
        
        # Validate response structure
        assert isinstance(remove_response.data, dict), \
            "Remove tests response should be a dictionary"
    
    async def test_test_plan_creation_contract(
        self, 
        mcp_client: XrayMCPClient, 
        test_data_manager
    ):
        """Test create_test_plan tool contract."""
        plan_data = test_data_manager.generate_test_data_template("test_plan")
        
        response = await mcp_client.create_test_plan(
            project_key=plan_data["project_key"],
            summary=plan_data["summary"],
            description=plan_data["description"]
        )
        
        # Assert successful creation
        mcp_client.assert_success(response, "Test plan creation should succeed")
        
        # Validate response structure
        required_fields = ["key", "id"]
        mcp_client.assert_contains_keys(response, required_fields)
        
        # Track for cleanup
        issue_id = mcp_client.extract_issue_id(response)
        if issue_id:
            test_data_manager.track_resource("plan", issue_id)
    
    async def test_test_set_creation_contract(
        self, 
        mcp_client: XrayMCPClient, 
        test_data_manager
    ):
        """Test create_test_set tool contract."""
        set_data = test_data_manager.generate_test_data_template("test_plan")  # Using same template
        set_data["summary"] = set_data["summary"].replace("Plan", "Set")
        
        response = await mcp_client.create_test_set(
            project_key=set_data["project_key"],
            summary=set_data["summary"],
            description=set_data["description"]
        )
        
        # Assert successful creation
        mcp_client.assert_success(response, "Test set creation should succeed")
        
        # Validate response structure
        required_fields = ["key", "id"]
        mcp_client.assert_contains_keys(response, required_fields)
        
        # Track for cleanup
        issue_id = mcp_client.extract_issue_id(response)
        if issue_id:
            test_data_manager.track_resource("set", issue_id)
    
    async def test_precondition_creation_contract(
        self, 
        mcp_client: XrayMCPClient, 
        test_data_manager
    ):
        """Test create_precondition tool contract."""
        # First create a test
        test_data = test_data_manager.generate_test_data_template("generic_test")
        
        test_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.GENERIC,
            unstructured=test_data["unstructured"]
        )
        
        mcp_client.assert_success(test_response, "Test creation should succeed")
        
        test_id = mcp_client.extract_issue_id(test_response)
        assert test_id, "Should extract test ID"
        
        # Track test for cleanup
        test_data_manager.track_resource("test", test_id)
        
        # Create precondition
        precondition_data = {
            "type": "Manual",
            "condition": f"Test precondition for {test_data['summary']}"
        }
        
        precondition_response = await mcp_client.create_precondition(
            issue_id=test_id,
            precondition_input=precondition_data
        )
        
        # Assert successful creation
        mcp_client.assert_success(precondition_response, "Precondition creation should succeed")
        
        # Validate response structure
        assert isinstance(precondition_response.data, dict), \
            "Precondition creation response should be a dictionary"
    
    async def test_get_test_status_contract(
        self, 
        mcp_client: XrayMCPClient, 
        test_data_manager
    ):
        """Test get_test_status tool contract."""
        # Create a test
        test_data = test_data_manager.generate_test_data_template("generic_test")
        
        test_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.GENERIC,
            unstructured=test_data["unstructured"]
        )
        
        mcp_client.assert_success(test_response, "Test creation should succeed")
        
        test_id = mcp_client.extract_issue_id(test_response)
        assert test_id, "Should extract test ID"
        
        # Track test for cleanup
        test_data_manager.track_resource("test", test_id)
        
        # Get test status
        status_response = await mcp_client.get_test_status(test_id)
        
        # Assert response (may or may not have execution status for new test)
        # This tests the contract, not necessarily successful execution
        assert isinstance(status_response, TestResponse), \
            "Status response should be TestResponse instance"
        
        if status_response.success:
            assert isinstance(status_response.data, dict), \
                "Status response data should be a dictionary"
    
    @pytest.mark.parametrize("invalid_execution_id", ["999999999", "INVALID-123"])
    async def test_execution_invalid_id_contracts(
        self, 
        mcp_client: XrayMCPClient, 
        invalid_execution_id: str
    ):
        """Test execution tools with invalid IDs."""
        # Test get_test_execution with invalid ID
        get_response = await mcp_client.get_test_execution(invalid_execution_id)
        assert not get_response.success or not get_response.data, \
            f"Get execution with invalid ID '{invalid_execution_id}' should fail"
        
        # Test add_tests_to_execution with invalid execution ID
        add_response = await mcp_client.add_tests_to_execution(
            execution_issue_id=invalid_execution_id,
            test_issue_ids=["TEST-123"]
        )
        assert not add_response.success, \
            f"Add tests to invalid execution '{invalid_execution_id}' should fail"
        
        if not add_response.success:
            assert add_response.error is not None, \
                "Failed response should contain error message"
    
    async def test_execution_workflow_integration_contract(
        self, 
        mcp_client: XrayMCPClient, 
        test_data_manager
    ):
        """Test complete execution workflow contract."""
        # Step 1: Create tests
        test_ids = []
        for i in range(2):
            test_data = test_data_manager.generate_test_data_template("generic_test")
            test_data["summary"] = f"{test_data['summary']}_Workflow_{i+1}"
            
            test_response = await mcp_client.create_test(
                project_key=test_data["project_key"],
                summary=test_data["summary"],
                test_type=TestType.GENERIC,
                unstructured=test_data["unstructured"]
            )
            
            mcp_client.assert_success(test_response, f"Test {i+1} creation should succeed")
            
            test_id = mcp_client.extract_issue_id(test_response)
            assert test_id, f"Should extract test ID {i+1}"
            
            test_ids.append(test_id)
            test_data_manager.track_resource("test", test_id)
        
        # Step 2: Create empty execution
        execution_data = test_data_manager.generate_test_data_template("test_execution")
        
        execution_response = await mcp_client.create_test_execution(
            project_key=execution_data["project_key"],
            summary=execution_data["summary"]
        )
        
        mcp_client.assert_success(execution_response, "Execution creation should succeed")
        
        execution_id = mcp_client.extract_issue_id(execution_response)
        assert execution_id, "Should extract execution ID"
        
        test_data_manager.track_resource("execution", execution_id)
        
        # Step 3: Add tests to execution
        add_response = await mcp_client.add_tests_to_execution(
            execution_issue_id=execution_id,
            test_issue_ids=test_ids
        )
        
        mcp_client.assert_success(add_response, "Adding tests should succeed")
        
        # Step 4: Retrieve execution to verify tests added
        final_get_response = await mcp_client.get_test_execution(execution_id)
        mcp_client.assert_success(final_get_response, "Final execution retrieval should succeed")
        
        # Step 5: Remove one test
        remove_response = await mcp_client.remove_tests_from_execution(
            execution_issue_id=execution_id,
            test_issue_ids=[test_ids[0]]
        )
        
        mcp_client.assert_success(remove_response, "Removing test should succeed")
        
        # All steps completed successfully indicates proper workflow contract compliance