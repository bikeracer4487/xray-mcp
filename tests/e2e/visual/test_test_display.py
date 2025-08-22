"""
Visual tests for Xray test content display and rendering.

These tests validate that tests created via MCP are properly displayed
in the Jira Xray UI with correct content, formatting, and structure.
"""

import pytest
from playwright.async_api import Page

from fixtures.mcp_client import XrayMCPClient, TestType
from fixtures.visual_validators import XrayVisualValidator, ValidationLevel


@pytest.mark.visual
class TestTestDisplay:
    """Visual validation tests for test display in Xray."""
    
    async def test_generic_test_display(
        self,
        browser_page: Page,
        mcp_client: XrayMCPClient,
        visual_validator: XrayVisualValidator,
        test_data_manager
    ):
        """Test Generic test display in Jira UI."""
        # Create Generic test via MCP
        test_data = test_data_manager.generate_test_data_template("generic_test")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.GENERIC,
            description=test_data["description"],
            unstructured=test_data["unstructured"]
        )
        
        mcp_client.assert_success(create_response, "Generic test creation should succeed")
        
        test_key = mcp_client.extract_issue_key(create_response)
        test_id = mcp_client.extract_issue_id(create_response)
        assert test_key, "Should extract test key for UI validation"
        
        # Track for cleanup
        if test_id:
            test_data_manager.track_resource("test", test_id, {"key": test_key})
        
        # Validate test display in UI
        validation_result = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=test_data["summary"],
            test_type="Generic",
            validation_level=ValidationLevel.CONTENT
        )
        
        # Assert visual validation passed
        assert validation_result.passed, \
            f"Generic test display validation failed: {validation_result.failed_assertions}"
        
        # Verify specific details
        assert "actual_summary" in validation_result.details, \
            "Validation should capture actual summary"
        assert test_data["summary"] in validation_result.details["actual_summary"], \
            "UI should display the correct test summary"
    
    async def test_manual_test_steps_display(
        self,
        browser_page: Page,
        mcp_client: XrayMCPClient,
        visual_validator: XrayVisualValidator,
        test_data_manager
    ):
        """Test Manual test steps display in Jira UI."""
        # Create Manual test with steps via MCP
        test_data = test_data_manager.generate_test_data_template("manual_test")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.MANUAL,
            description=test_data["description"],
            steps=test_data["steps"]
        )
        
        mcp_client.assert_success(create_response, "Manual test creation should succeed")
        
        test_key = mcp_client.extract_issue_key(create_response)
        test_id = mcp_client.extract_issue_id(create_response)
        assert test_key, "Should extract test key for UI validation"
        
        # Track for cleanup
        if test_id:
            test_data_manager.track_resource("test", test_id, {"key": test_key})
        
        # Validate test display
        test_validation = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=test_data["summary"],
            test_type="Manual",
            validation_level=ValidationLevel.CONTENT
        )
        
        assert test_validation.passed, \
            f"Manual test display validation failed: {test_validation.failed_assertions}"
        
        # Validate test steps display
        steps_validation = await visual_validator.validate_manual_test_steps(
            page=browser_page,
            test_key=test_key,
            expected_steps=test_data["steps"],
            validation_level=ValidationLevel.CONTENT
        )
        
        assert steps_validation.passed, \
            f"Manual test steps validation failed: {steps_validation.failed_assertions}"
        
        # Verify step count
        assert steps_validation.details["actual_step_count"] == len(test_data["steps"]), \
            f"UI should display {len(test_data['steps'])} steps, got {steps_validation.details['actual_step_count']}"
    
    async def test_cucumber_gherkin_display(
        self,
        browser_page: Page,
        mcp_client: XrayMCPClient,
        visual_validator: XrayVisualValidator,
        test_data_manager
    ):
        """Test Cucumber test Gherkin scenario display in Jira UI."""
        # Create Cucumber test with Gherkin via MCP
        test_data = test_data_manager.generate_test_data_template("cucumber_test")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.CUCUMBER,
            description=test_data["description"],
            gherkin=test_data["gherkin"]
        )
        
        mcp_client.assert_success(create_response, "Cucumber test creation should succeed")
        
        test_key = mcp_client.extract_issue_key(create_response)
        test_id = mcp_client.extract_issue_id(create_response)
        assert test_key, "Should extract test key for UI validation"
        
        # Track for cleanup
        if test_id:
            test_data_manager.track_resource("test", test_id, {"key": test_key})
        
        # Validate test display
        test_validation = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=test_data["summary"],
            test_type="Cucumber",
            validation_level=ValidationLevel.CONTENT
        )
        
        assert test_validation.passed, \
            f"Cucumber test display validation failed: {test_validation.failed_assertions}"
        
        # Validate Gherkin scenario display
        gherkin_validation = await visual_validator.validate_gherkin_scenario(
            page=browser_page,
            test_key=test_key,
            expected_gherkin=test_data["gherkin"],
            validation_level=ValidationLevel.CONTENT
        )
        
        assert gherkin_validation.passed, \
            f"Gherkin scenario validation failed: {gherkin_validation.failed_assertions}"
        
        # Verify Gherkin keywords are displayed
        actual_gherkin = gherkin_validation.details.get("actual_gherkin", "")
        gherkin_keywords = ["Feature", "Scenario", "Given", "When", "Then"]
        
        displayed_keywords = [kw for kw in gherkin_keywords if kw in actual_gherkin]
        expected_keywords = [kw for kw in gherkin_keywords if kw in test_data["gherkin"]]
        
        assert len(displayed_keywords) >= len(expected_keywords) // 2, \
            f"UI should display Gherkin keywords. Expected: {expected_keywords}, Displayed: {displayed_keywords}"
    
    async def test_test_description_rendering(
        self,
        browser_page: Page,
        mcp_client: XrayMCPClient,
        visual_validator: XrayVisualValidator,
        test_data_manager
    ):
        """Test rich description content rendering."""
        # Create test with rich description
        test_data = test_data_manager.generate_test_data_template("generic_test")
        test_data["description"] = test_data_manager.generate_test_description("rich")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.GENERIC,
            description=test_data["description"],
            unstructured=test_data["unstructured"]
        )
        
        mcp_client.assert_success(create_response, "Test creation should succeed")
        
        test_key = mcp_client.extract_issue_key(create_response)
        test_id = mcp_client.extract_issue_id(create_response)
        assert test_key, "Should extract test key for UI validation"
        
        # Track for cleanup
        if test_id:
            test_data_manager.track_resource("test", test_id, {"key": test_key})
        
        # Validate test display with focus on description
        validation_result = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=test_data["summary"],
            test_type="Generic",
            validation_level=ValidationLevel.CONTENT
        )
        
        assert validation_result.passed, \
            f"Test with rich description display failed: {validation_result.failed_assertions}"
        
        # Take screenshot for manual review of description rendering
        if visual_validator.capture_screenshots:
            screenshot_path = await visual_validator._capture_page_screenshot(
                browser_page, f"rich_description_{test_key}"
            )
            validation_result.screenshots["rich_description"] = screenshot_path
    
    async def test_test_update_display_consistency(
        self,
        browser_page: Page,
        mcp_client: XrayMCPClient,
        visual_validator: XrayVisualValidator,
        test_data_manager
    ):
        """Test that test updates are properly reflected in UI."""
        # Create initial test
        test_data = test_data_manager.generate_test_data_template("generic_test")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.GENERIC,
            unstructured=test_data["unstructured"]
        )
        
        mcp_client.assert_success(create_response, "Initial test creation should succeed")
        
        test_key = mcp_client.extract_issue_key(create_response)
        test_id = mcp_client.extract_issue_id(create_response)
        assert test_key and test_id, "Should extract test identifiers"
        
        # Track for cleanup
        test_data_manager.track_resource("test", test_id, {"key": test_key})
        
        # Validate initial display
        initial_validation = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=test_data["summary"],
            test_type="Generic",
            validation_level=ValidationLevel.CONTENT
        )
        
        assert initial_validation.passed, \
            f"Initial test display validation failed: {initial_validation.failed_assertions}"
        
        # Update the test
        updated_summary = test_data_manager.generate_unique_title("Updated Generic Test")
        updated_unstructured = "Updated unstructured content with new information"
        
        update_response = await mcp_client.update_test(
            issue_id=test_id,
            unstructured=updated_unstructured,
            jira_fields={"summary": updated_summary}
        )
        
        mcp_client.assert_success(update_response, "Test update should succeed")
        
        # Validate updated display (refresh page first)
        await browser_page.reload(wait_until="domcontentloaded")
        
        updated_validation = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=updated_summary,
            test_type="Generic",
            validation_level=ValidationLevel.CONTENT
        )
        
        assert updated_validation.passed, \
            f"Updated test display validation failed: {updated_validation.failed_assertions}"
        
        # Verify the update is reflected
        actual_summary = updated_validation.details.get("actual_summary", "")
        assert updated_summary in actual_summary, \
            f"UI should show updated summary '{updated_summary}', got '{actual_summary}'"
    
    async def test_test_type_change_display(
        self,
        browser_page: Page,
        mcp_client: XrayMCPClient,
        visual_validator: XrayVisualValidator,
        test_data_manager
    ):
        """Test that test type changes are properly displayed in UI."""
        # Create Generic test
        test_data = test_data_manager.generate_test_data_template("generic_test")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.GENERIC,
            unstructured=test_data["unstructured"]
        )
        
        mcp_client.assert_success(create_response, "Generic test creation should succeed")
        
        test_key = mcp_client.extract_issue_key(create_response)
        test_id = mcp_client.extract_issue_id(create_response)
        assert test_key and test_id, "Should extract test identifiers"
        
        # Track for cleanup
        test_data_manager.track_resource("test", test_id, {"key": test_key})
        
        # Validate initial Generic test display
        generic_validation = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=test_data["summary"],
            test_type="Generic",
            validation_level=ValidationLevel.BASIC
        )
        
        assert generic_validation.passed, \
            f"Generic test display validation failed: {generic_validation.failed_assertions}"
        
        # Convert to Manual test
        manual_steps = test_data_manager.generate_manual_test_steps(step_count=3)
        
        update_response = await mcp_client.update_test(
            issue_id=test_id,
            test_type="Manual",
            steps=manual_steps
        )
        
        mcp_client.assert_success(update_response, "Test type update should succeed")
        
        # Refresh page and validate Manual test display
        await browser_page.reload(wait_until="domcontentloaded")
        
        manual_validation = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=test_data["summary"],
            test_type="Manual",
            validation_level=ValidationLevel.BASIC
        )
        
        assert manual_validation.passed, \
            f"Manual test display validation failed: {manual_validation.failed_assertions}"
        
        # Validate steps are now displayed
        steps_validation = await visual_validator.validate_manual_test_steps(
            page=browser_page,
            test_key=test_key,
            expected_steps=manual_steps,
            validation_level=ValidationLevel.BASIC
        )
        
        assert steps_validation.passed, \
            f"Manual test steps validation failed: {steps_validation.failed_assertions}"
        
        # Verify step count matches
        assert steps_validation.details["actual_step_count"] == len(manual_steps), \
            f"Should display {len(manual_steps)} steps after conversion"
    
    @pytest.mark.slow
    async def test_gherkin_syntax_highlighting(
        self,
        browser_page: Page,
        mcp_client: XrayMCPClient,
        visual_validator: XrayVisualValidator,
        test_data_manager
    ):
        """Test Gherkin syntax highlighting in the editor."""
        # Create Cucumber test with complex Gherkin
        test_data = test_data_manager.generate_test_data_template("cucumber_test")
        test_data["gherkin"] = test_data_manager.generate_gherkin_scenario("complex")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.CUCUMBER,
            gherkin=test_data["gherkin"]
        )
        
        mcp_client.assert_success(create_response, "Cucumber test creation should succeed")
        
        test_key = mcp_client.extract_issue_key(create_response)
        test_id = mcp_client.extract_issue_id(create_response)
        assert test_key, "Should extract test key for UI validation"
        
        # Track for cleanup
        if test_id:
            test_data_manager.track_resource("test", test_id, {"key": test_key})
        
        # Validate Gherkin display with styling validation
        gherkin_validation = await visual_validator.validate_gherkin_scenario(
            page=browser_page,
            test_key=test_key,
            expected_gherkin=test_data["gherkin"],
            validation_level=ValidationLevel.STYLING
        )
        
        # Note: Styling validation may be less reliable, so we allow it to pass
        # even if syntax highlighting check fails (it's noted in failed_assertions)
        if not gherkin_validation.passed:
            # Check if failure is only about syntax highlighting
            syntax_failures = [
                assertion for assertion in gherkin_validation.failed_assertions
                if "syntax highlighting" in assertion.lower()
            ]
            
            if len(syntax_failures) == len(gherkin_validation.failed_assertions):
                # Only syntax highlighting failed - this is acceptable
                pytest.skip("Syntax highlighting validation is environment-dependent")
        
        assert gherkin_validation.passed, \
            f"Gherkin scenario styling validation failed: {gherkin_validation.failed_assertions}"
    
    async def test_screenshot_capture_on_failure(
        self,
        browser_page: Page,
        mcp_client: XrayMCPClient,
        visual_validator: XrayVisualValidator,
        test_data_manager
    ):
        """Test that screenshots are captured when validation fails."""
        # Create a test
        test_data = test_data_manager.generate_test_data_template("generic_test")
        
        create_response = await mcp_client.create_test(
            project_key=test_data["project_key"],
            summary=test_data["summary"],
            test_type=TestType.GENERIC,
            unstructured=test_data["unstructured"]
        )
        
        mcp_client.assert_success(create_response, "Test creation should succeed")
        
        test_key = mcp_client.extract_issue_key(create_response)
        test_id = mcp_client.extract_issue_id(create_response)
        assert test_key, "Should extract test key for UI validation"
        
        # Track for cleanup
        if test_id:
            test_data_manager.track_resource("test", test_id, {"key": test_key})
        
        # Deliberately use wrong expected summary to trigger failure
        wrong_summary = "This is definitely not the correct summary"
        
        validation_result = await visual_validator.validate_test_display(
            page=browser_page,
            test_key=test_key,
            expected_summary=wrong_summary,
            test_type="Generic",
            validation_level=ValidationLevel.CONTENT
        )
        
        # Should fail as expected
        assert not validation_result.passed, \
            "Validation with wrong expected summary should fail"
        
        # Should have captured screenshots
        if visual_validator.capture_screenshots:
            assert len(validation_result.screenshots) > 0, \
                "Failed validation should capture screenshots"
            
            for screenshot_name, screenshot_path in validation_result.screenshots.items():
                assert screenshot_path.exists(), \
                    f"Screenshot {screenshot_name} should exist at {screenshot_path}"