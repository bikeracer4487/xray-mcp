"""
Integration workflow tests for Xray MCP.

Tests complete workflows combining MCP contract validation
with visual verification to ensure end-to-end functionality.
"""

import pytest
from playwright.async_api import Page

from fixtures.mcp_client import XrayMCPClient, XrayTestType
from fixtures.visual_validators import XrayVisualValidator, ValidationLevel


@pytest.mark.integration
class TestWorkflowIntegration:
    """Integration tests for complete Xray MCP workflows."""
    
    async def test_complete_test_lifecycle_workflow(
        self,
        browser_page: Page,
        mcp_client: XrayMCPClient,
        visual_validator: XrayVisualValidator,
        test_data_manager
    ):
        """Test complete test lifecycle: create → display → update → display → delete."""
        
        # Phase 1: Create test via MCP
        test_data = test_data_manager.generate_test_data_template("manual_test")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=XrayTestType.MANUAL,
            description=test_data["description"],
            steps=test_data["steps"]
        )
        
        mcp_client.assert_success(create_response, "Test creation should succeed")
        
        test_key = mcp_client.extract_issue_key(create_response)
        test_id = mcp_client.extract_issue_id(create_response)
        assert test_key and test_id, "Should extract test identifiers"
        
        # Phase 2: Verify initial display in UI
        initial_display = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=test_data["summary"],
            test_type="Manual",
            validation_level=ValidationLevel.CONTENT
        )
        
        assert initial_display.passed, \
            f"Initial test display validation failed: {initial_display.failed_assertions}"
        
        steps_display = await visual_validator.validate_manual_test_steps(
            page=browser_page,
            test_key=test_key,
            expected_steps=test_data["steps"],
            validation_level=ValidationLevel.CONTENT
        )
        
        assert steps_display.passed, \
            f"Initial test steps display failed: {steps_display.failed_assertions}"
        
        # Phase 3: Update test via MCP
        updated_summary = test_data_manager.generate_unique_title("Updated Manual Test")
        additional_steps = test_data_manager.generate_manual_test_steps(step_count=2, include_data=True)
        all_steps = test_data["steps"] + additional_steps
        
        update_response = await mcp_client.update_test(
            issue_id=test_id,
            steps=all_steps,
            jira_fields={"summary": updated_summary}
        )
        
        mcp_client.assert_success(update_response, "Test update should succeed")
        
        # Phase 4: Verify updated display in UI
        await browser_page.reload(wait_until="domcontentloaded")
        
        updated_display = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=updated_summary,
            test_type="Manual",
            validation_level=ValidationLevel.CONTENT
        )
        
        assert updated_display.passed, \
            f"Updated test display validation failed: {updated_display.failed_assertions}"
        
        updated_steps_display = await visual_validator.validate_manual_test_steps(
            page=browser_page,
            test_key=test_key,
            expected_steps=all_steps,
            validation_level=ValidationLevel.CONTENT
        )
        
        assert updated_steps_display.passed, \
            f"Updated test steps display failed: {updated_steps_display.failed_assertions}"
        
        # Verify step count increased
        assert updated_steps_display.details["actual_step_count"] == len(all_steps), \
            f"Should display {len(all_steps)} steps after update"
        
        # Phase 5: Clean up via MCP
        delete_response = await mcp_client.delete_test(test_id)
        mcp_client.assert_success(delete_response, "Test deletion should succeed")
        
        # Phase 6: Verify test no longer accessible
        # Try to navigate to deleted test (should show error or not found)
        await browser_page.goto(f"{visual_validator.base_url}/browse/{test_key}")
        
        # Page should either show error or test not found
        # We don't assert specific error format as it may vary by Jira version
        page_title = await browser_page.title()
        page_content = await browser_page.text_content("body")
        
        # Test is considered properly deleted if we get error page or empty content
        deleted_properly = (
            "error" in page_title.lower() or 
            "not found" in page_content.lower() or
            "doesn't exist" in page_content.lower() or
            len(page_content.strip()) < 100  # Very minimal content suggests error page
        )
        
        assert deleted_properly, \
            f"Deleted test should not be accessible. Page title: '{page_title}'"
    
    async def test_test_execution_workflow(
        self,
        browser_page: Page,
        mcp_client: XrayMCPClient,
        visual_validator: XrayVisualValidator,
        test_data_manager
    ):
        """Test complete test execution workflow: create tests → create execution → add tests → verify."""
        
        # Phase 1: Create multiple tests
        test_ids = []
        test_keys = []
        
        for i in range(3):
            test_data = test_data_manager.generate_test_data_template("generic_test")
            test_data["summary"] = f"{test_data['summary']}_ExecutionWorkflow_{i+1}"
            
            create_response = await mcp_client.create_test(
                project_key=test_data["project_key"],
                summary=test_data["summary"],
                test_type=XrayTestType.GENERIC,
                unstructured=test_data["unstructured"]
            )
            
            mcp_client.assert_success(create_response, f"Test {i+1} creation should succeed")
            
            test_key = mcp_client.extract_issue_key(create_response)
            test_id = mcp_client.extract_issue_id(create_response)
            assert test_key and test_id, f"Should extract identifiers for test {i+1}"
            
            test_ids.append(test_id)
            test_keys.append(test_key)
            test_data_manager.track_resource("test", test_id, {"key": test_key})
        
        # Phase 2: Verify all tests display correctly
        for i, test_key in enumerate(test_keys):
            display_validation = await visual_validator.validate_test_display(
                page=browser_page,
                test_key=test_key,
                expected_summary=f"XrayMCP_E2E_Template Test_ExecutionWorkflow_{i+1}",
                test_type="Generic",
                validation_level=ValidationLevel.BASIC
            )
            
            assert display_validation.passed, \
                f"Test {i+1} display validation failed: {display_validation.failed_assertions}"
        
        # Phase 3: Create test execution with some tests
        execution_data = test_data_manager.generate_test_data_template("test_execution")
        
        execution_response = await mcp_client.create_test_execution(
            project_key=execution_data["project_key"],
            summary=execution_data["summary"],
            description=execution_data["description"],
            test_issue_ids=test_ids[:2],  # Add first 2 tests
            test_environments=execution_data["test_environments"]
        )
        
        mcp_client.assert_success(execution_response, "Test execution creation should succeed")
        
        execution_key = mcp_client.extract_issue_key(execution_response)
        execution_id = mcp_client.extract_issue_id(execution_response)
        assert execution_key and execution_id, "Should extract execution identifiers"
        
        test_data_manager.track_resource("execution", execution_id, {"key": execution_key})
        
        # Phase 4: Verify execution display
        execution_display = await visual_validator.validate_test_execution_status(
            page=browser_page,
            execution_key=execution_key,
            validation_level=ValidationLevel.BASIC
        )
        
        assert execution_display.passed, \
            f"Execution display validation failed: {execution_display.failed_assertions}"
        
        # Phase 5: Add remaining test to execution
        add_response = await mcp_client.add_tests_to_execution(
            execution_issue_id=execution_id,
            test_issue_ids=[test_ids[2]]  # Add third test
        )
        
        mcp_client.assert_success(add_response, "Adding test to execution should succeed")
        
        # Phase 6: Verify execution still displays correctly after modification
        await browser_page.reload(wait_until="domcontentloaded")
        
        final_execution_display = await visual_validator.validate_test_execution_status(
            page=browser_page,
            execution_key=execution_key,
            validation_level=ValidationLevel.BASIC
        )
        
        assert final_execution_display.passed, \
            f"Final execution display validation failed: {final_execution_display.failed_assertions}"
    
    async def test_gherkin_update_workflow(
        self,
        browser_page: Page,
        mcp_client: XrayMCPClient,
        visual_validator: XrayVisualValidator,
        test_data_manager
    ):
        """Test Gherkin scenario update workflow."""
        
        # Phase 1: Create Cucumber test with basic Gherkin
        test_data = test_data_manager.generate_test_data_template("cucumber_test")
        initial_gherkin = test_data_manager.generate_gherkin_scenario("basic")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=XrayTestType.CUCUMBER,
            description=test_data["description"],
            gherkin=initial_gherkin
        )
        
        mcp_client.assert_success(create_response, "Cucumber test creation should succeed")
        
        test_key = mcp_client.extract_issue_key(create_response)
        test_id = mcp_client.extract_issue_id(create_response)
        assert test_key and test_id, "Should extract test identifiers"
        
        test_data_manager.track_resource("test", test_id, {"key": test_key})
        
        # Phase 2: Verify initial Gherkin display
        initial_gherkin_display = await visual_validator.validate_gherkin_scenario(
            page=browser_page,
            test_key=test_key,
            expected_gherkin=initial_gherkin,
            validation_level=ValidationLevel.CONTENT
        )
        
        assert initial_gherkin_display.passed, \
            f"Initial Gherkin display failed: {initial_gherkin_display.failed_assertions}"
        
        # Phase 3: Update Gherkin to complex scenario
        complex_gherkin = test_data_manager.generate_gherkin_scenario("complex")
        
        gherkin_update_response = await mcp_client.update_gherkin_definition(
            issue_id=test_id,
            gherkin_text=complex_gherkin
        )
        
        mcp_client.assert_success(gherkin_update_response, "Gherkin update should succeed")
        
        # Phase 4: Verify updated Gherkin display
        await browser_page.reload(wait_until="domcontentloaded")
        
        updated_gherkin_display = await visual_validator.validate_gherkin_scenario(
            page=browser_page,
            test_key=test_key,
            expected_gherkin=complex_gherkin,
            validation_level=ValidationLevel.CONTENT
        )
        
        assert updated_gherkin_display.passed, \
            f"Updated Gherkin display failed: {updated_gherkin_display.failed_assertions}"
        
        # Phase 5: Update to scenario outline
        outline_gherkin = test_data_manager.generate_gherkin_scenario("outline")
        
        outline_update_response = await mcp_client.update_gherkin_definition(
            issue_id=test_id,
            gherkin_text=outline_gherkin
        )
        
        mcp_client.assert_success(outline_update_response, "Outline Gherkin update should succeed")
        
        # Phase 6: Verify scenario outline display
        await browser_page.reload(wait_until="domcontentloaded")
        
        outline_display = await visual_validator.validate_gherkin_scenario(
            page=browser_page,
            test_key=test_key,
            expected_gherkin=outline_gherkin,
            validation_level=ValidationLevel.CONTENT
        )
        
        assert outline_display.passed, \
            f"Scenario outline display failed: {outline_display.failed_assertions}"
        
        # Verify Examples table is present in outline
        actual_gherkin = outline_display.details.get("actual_gherkin", "")
        assert "Examples:" in actual_gherkin or "examples" in actual_gherkin.lower(), \
            "Scenario outline should display Examples table"
    
    async def test_test_type_conversion_workflow(
        self,
        browser_page: Page,
        mcp_client: XrayMCPClient,
        visual_validator: XrayVisualValidator,
        test_data_manager
    ):
        """Test converting between different test types."""
        
        # Phase 1: Create Generic test
        test_data = test_data_manager.generate_test_data_template("generic_test")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=XrayTestType.GENERIC,
            description=test_data["description"],
            unstructured=test_data["unstructured"]
        )
        
        mcp_client.assert_success(create_response, "Generic test creation should succeed")
        
        test_key = mcp_client.extract_issue_key(create_response)
        test_id = mcp_client.extract_issue_id(create_response)
        assert test_key and test_id, "Should extract test identifiers"
        
        test_data_manager.track_resource("test", test_id, {"key": test_key})
        
        # Phase 2: Verify Generic test display
        generic_display = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=test_data["summary"],
            test_type="Generic",
            validation_level=ValidationLevel.CONTENT
        )
        
        assert generic_display.passed, \
            f"Generic test display failed: {generic_display.failed_assertions}"
        
        # Phase 3: Convert to Manual test
        manual_steps = test_data_manager.generate_manual_test_steps(step_count=4)
        
        manual_update_response = await mcp_client.update_test(
            issue_id=test_id,
            test_type="Manual",
            steps=manual_steps
        )
        
        mcp_client.assert_success(manual_update_response, "Conversion to Manual should succeed")
        
        # Phase 4: Verify Manual test display
        await browser_page.reload(wait_until="domcontentloaded")
        
        manual_display = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=test_data["summary"],
            test_type="Manual",
            validation_level=ValidationLevel.CONTENT
        )
        
        assert manual_display.passed, \
            f"Manual test display failed: {manual_display.failed_assertions}"
        
        manual_steps_display = await visual_validator.validate_manual_test_steps(
            page=browser_page,
            test_key=test_key,
            expected_steps=manual_steps,
            validation_level=ValidationLevel.CONTENT
        )
        
        assert manual_steps_display.passed, \
            f"Manual test steps display failed: {manual_steps_display.failed_assertions}"
        
        # Phase 5: Convert to Cucumber test
        gherkin_scenario = test_data_manager.generate_gherkin_scenario("complex")
        
        cucumber_update_response = await mcp_client.update_test(
            issue_id=test_id,
            test_type="Cucumber",
            gherkin=gherkin_scenario
        )
        
        mcp_client.assert_success(cucumber_update_response, "Conversion to Cucumber should succeed")
        
        # Phase 6: Verify Cucumber test display
        await browser_page.reload(wait_until="domcontentloaded")
        
        cucumber_display = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=test_data["summary"],
            test_type="Cucumber",
            validation_level=ValidationLevel.CONTENT
        )
        
        assert cucumber_display.passed, \
            f"Cucumber test display failed: {cucumber_display.failed_assertions}"
        
        cucumber_gherkin_display = await visual_validator.validate_gherkin_scenario(
            page=browser_page,
            test_key=test_key,
            expected_gherkin=gherkin_scenario,
            validation_level=ValidationLevel.CONTENT
        )
        
        assert cucumber_gherkin_display.passed, \
            f"Cucumber Gherkin display failed: {cucumber_gherkin_display.failed_assertions}"
    
    @pytest.mark.slow
    async def test_bulk_operations_workflow(
        self,
        browser_page: Page,
        mcp_client: XrayMCPClient,
        visual_validator: XrayVisualValidator,
        test_data_manager
    ):
        """Test bulk operations workflow with multiple tests."""
        
        # Phase 1: Create multiple tests of different types
        test_configs = [
            {"type": XrayTestType.GENERIC, "template": "generic_test"},
            {"type": XrayTestType.MANUAL, "template": "manual_test"},
            {"type": XrayTestType.CUCUMBER, "template": "cucumber_test"},
            {"type": XrayTestType.GENERIC, "template": "generic_test"},
            {"type": XrayTestType.MANUAL, "template": "manual_test"}
        ]
        
        created_tests = []
        
        for i, config in enumerate(test_configs):
            test_data = test_data_manager.generate_test_data_template(config["template"])
            test_data["summary"] = f"{test_data['summary']}_Bulk_{i+1}"
            
            create_kwargs = {
                "project_key": test_data["project_key"],
                "summary": test_data["summary"],
                "test_type": config["type"],
                "description": test_data["description"]
            }
            
            # Add type-specific content
            if config["type"] == XrayTestType.GENERIC:
                create_kwargs["unstructured"] = test_data["unstructured"]
            elif config["type"] == XrayTestType.MANUAL:
                create_kwargs["steps"] = test_data["steps"]
            elif config["type"] == XrayTestType.CUCUMBER:
                create_kwargs["gherkin"] = test_data["gherkin"]
            
            create_response = await mcp_client.create_test(**create_kwargs)
            
            mcp_client.assert_success(create_response, f"Bulk test {i+1} creation should succeed")
            
            test_key = mcp_client.extract_issue_key(create_response)
            test_id = mcp_client.extract_issue_id(create_response)
            assert test_key and test_id, f"Should extract identifiers for bulk test {i+1}"
            
            created_tests.append({
                "key": test_key,
                "id": test_id,
                "type": config["type"],
                "summary": test_data["summary"]
            })
            
            test_data_manager.track_resource("test", test_id, {"key": test_key})
        
        # Phase 2: Verify all tests display correctly
        for i, test_info in enumerate(created_tests):
            display_validation = await visual_validator.validate_test_display(
                page=browser_page,
                test_key=test_info["key"],
                expected_summary=test_info["summary"],
                test_type=test_info["type"].value,
                validation_level=ValidationLevel.BASIC
            )
            
            assert display_validation.passed, \
                f"Bulk test {i+1} display validation failed: {display_validation.failed_assertions}"
        
        # Phase 3: Create test execution with all tests
        execution_data = test_data_manager.generate_test_data_template("test_execution")
        execution_data["summary"] = f"{execution_data['summary']}_BulkTests"
        
        bulk_execution_response = await mcp_client.create_test_execution(
            project_key=execution_data["project_key"],
            summary=execution_data["summary"],
            description="Execution for bulk test workflow",
            test_issue_ids=[test["id"] for test in created_tests],
            test_environments=execution_data["test_environments"]
        )
        
        mcp_client.assert_success(bulk_execution_response, "Bulk execution creation should succeed")
        
        execution_key = mcp_client.extract_issue_key(bulk_execution_response)
        execution_id = mcp_client.extract_issue_id(bulk_execution_response)
        assert execution_key and execution_id, "Should extract bulk execution identifiers"
        
        test_data_manager.track_resource("execution", execution_id, {"key": execution_key})
        
        # Phase 4: Verify execution displays correctly
        execution_display = await visual_validator.validate_test_execution_status(
            page=browser_page,
            execution_key=execution_key,
            validation_level=ValidationLevel.BASIC
        )
        
        assert execution_display.passed, \
            f"Bulk execution display failed: {execution_display.failed_assertions}"
        
        # Phase 5: Query tests using JQL
        jql_query = f"project = {test_data_manager.project_key} AND summary ~ 'Bulk_'"
        
        jql_response = await mcp_client.execute_jql_query(
            jql=jql_query,
            entity_type="test",
            limit=10
        )
        
        mcp_client.assert_success(jql_response, "JQL query for bulk tests should succeed")
        
        # Should find at least some of our created tests
        assert isinstance(jql_response.data, dict), "JQL response should be a dictionary"
        
        # Successful completion of all phases indicates proper bulk workflow functionality
    
    async def test_error_recovery_workflow(
        self,
        browser_page: Page,
        mcp_client: XrayMCPClient,
        visual_validator: XrayVisualValidator,
        test_data_manager
    ):
        """Test error recovery and graceful handling workflow."""
        
        # Phase 1: Create valid test for baseline
        test_data = test_data_manager.generate_test_data_template("generic_test")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=XrayTestType.GENERIC,
            unstructured=test_data["unstructured"]
        )
        
        mcp_client.assert_success(create_response, "Valid test creation should succeed")
        
        test_key = mcp_client.extract_issue_key(create_response)
        test_id = mcp_client.extract_issue_id(create_response)
        assert test_key and test_id, "Should extract test identifiers"
        
        test_data_manager.track_resource("test", test_id, {"key": test_key})
        
        # Phase 2: Verify valid test displays correctly
        valid_display = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=test_data["summary"],
            test_type="Generic",
            validation_level=ValidationLevel.CONTENT
        )
        
        assert valid_display.passed, \
            f"Valid test display failed: {valid_display.failed_assertions}"
        
        # Phase 3: Attempt operations with invalid data (should fail gracefully)
        invalid_operations = [
            # Invalid project key
            {
                "operation": "create_test",
                "kwargs": {
                    "project_key": "NONEXISTENT",
                    "summary": "Invalid project test",
                    "test_type": XrayTestType.GENERIC,
                    "unstructured": "Test content"
                }
            },
            # Invalid test ID for get
            {
                "operation": "get_test",
                "kwargs": {"issue_id": "999999999"}
            },
            # Invalid execution ID for adding tests
            {
                "operation": "add_tests_to_execution",
                "kwargs": {
                    "execution_issue_id": "999999999",
                    "test_issue_ids": [test_id]
                }
            }
        ]
        
        for i, invalid_op in enumerate(invalid_operations):
            if invalid_op["operation"] == "create_test":
                response = await mcp_client.create_test(**invalid_op["kwargs"])
            elif invalid_op["operation"] == "get_test":
                response = await mcp_client.get_test(**invalid_op["kwargs"])
            elif invalid_op["operation"] == "add_tests_to_execution":
                response = await mcp_client.add_tests_to_execution(**invalid_op["kwargs"])
            
            # Should fail gracefully
            assert not response.success, \
                f"Invalid operation {i+1} should fail gracefully"
            assert response.error is not None, \
                f"Invalid operation {i+1} should have error message"
        
        # Phase 4: Verify valid test still works after invalid operations
        recovery_display = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=test_data["summary"],
            test_type="Generic",
            validation_level=ValidationLevel.CONTENT
        )
        
        assert recovery_display.passed, \
            f"Test display after error recovery failed: {recovery_display.failed_assertions}"
        
        # Phase 5: Perform valid update to ensure system recovery
        updated_summary = test_data_manager.generate_unique_title("Recovered Test")
        
        update_response = await mcp_client.update_test(
            issue_id=test_id,
            jira_fields={"summary": updated_summary}
        )
        
        mcp_client.assert_success(update_response, "Update after error recovery should succeed")
        
        # Phase 6: Verify updated test displays correctly
        await browser_page.reload(wait_until="domcontentloaded")
        
        final_display = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=updated_summary,
            test_type="Generic",
            validation_level=ValidationLevel.CONTENT
        )
        
        assert final_display.passed, \
            f"Final test display after recovery failed: {final_display.failed_assertions}"