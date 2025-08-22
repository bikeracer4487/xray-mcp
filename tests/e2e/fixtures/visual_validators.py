"""
Visual validation utilities for Xray MCP E2E tests using Playwright.

Provides browser-based verification of test content rendering and display
in Jira Xray to ensure created tests appear correctly in the UI.
"""

import asyncio
import base64
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from playwright.async_api import Page, Locator, expect


class ValidationLevel(Enum):
    """Validation levels for visual tests."""
    BASIC = "basic"          # Element existence only
    CONTENT = "content"      # Element content validation
    STYLING = "styling"      # Visual styling validation
    INTERACTION = "interaction"  # Interactive element testing


@dataclass
class VisualAssertion:
    """Visual assertion definition."""
    selector: str
    assertion_type: str
    expected_value: Any = None
    description: str = ""
    level: ValidationLevel = ValidationLevel.BASIC
    
    def __post_init__(self):
        if not self.description:
            self.description = f"{self.assertion_type} for {self.selector}"


@dataclass
class VisualValidationResult:
    """Result of visual validation."""
    passed: bool
    failed_assertions: List[str]
    screenshots: Dict[str, Path]
    details: Dict[str, Any]
    
    def __bool__(self) -> bool:
        return self.passed


class XrayVisualValidator:
    """Visual validator for Xray test content."""
    
    # Xray UI selectors
    XRAY_SELECTORS = {
        # Test view selectors
        "test_summary": "[data-testid='issue.views.issue-base.foundation.summary.heading']",
        "test_description": ".ak-renderer-document, [data-testid='issue.views.field.rich-text.description']",
        "test_type_field": "[data-testid='xray.testType']",
        "test_steps_table": "[data-testid='xray.manual-test.steps-table']",
        "test_step_row": "[data-testid='xray.manual-test.step-row']",
        "test_step_action": "[data-testid='xray.manual-test.step-action']",
        "test_step_data": "[data-testid='xray.manual-test.step-data']",
        "test_step_expected": "[data-testid='xray.manual-test.step-expected-result']",
        
        # Gherkin selectors
        "gherkin_editor": "[data-testid='xray.cucumber-test.gherkin-editor']",
        "gherkin_content": ".ace_content, .gherkin-content",
        "gherkin_scenario": ".ace_line, .gherkin-scenario",
        
        # Test execution selectors
        "execution_status": "[data-testid='xray.test-execution.status']",
        "execution_history": "[data-testid='xray.test-execution.history']",
        "execution_results": "[data-testid='xray.test-execution.results']",
        
        # Test repository selectors
        "test_repo_tree": "[data-testid='xray.test-repository.tree']",
        "test_repo_folder": "[data-testid='xray.test-repository.folder']",
        "test_repo_test": "[data-testid='xray.test-repository.test']",
        
        # General Jira selectors
        "issue_key": "[data-testid='issue.views.issue-base.foundation.breadcrumbs.current-issue.item']",
        "issue_status": "[data-testid='issue.views.issue-base.foundation.status.status-field-wrapper']",
        "issue_assignee": "[data-testid='issue.views.issue-base.foundation.assignee.assignee-field-wrapper']",
        "issue_priority": "[data-testid='issue.views.issue-base.foundation.priority.priority-field-wrapper']",
    }
    
    def __init__(
        self, 
        artifacts_dir: Path, 
        base_url: str = "https://your-instance.atlassian.net",
        capture_screenshots: bool = True
    ):
        """
        Initialize visual validator.
        
        Args:
            artifacts_dir: Directory to store screenshots and artifacts
            base_url: Base URL for Jira instance
            capture_screenshots: Whether to capture screenshots
        """
        self.artifacts_dir = artifacts_dir
        self.base_url = base_url.rstrip("/")
        self.capture_screenshots = capture_screenshots
        self.screenshots_dir = artifacts_dir / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async def authenticate(self, page: Page, username: str, api_token: str):
        """
        Authenticate with Jira using basic auth.
        
        Args:
            page: Playwright page
            username: Jira username/email
            api_token: Jira API token
        """
        # Set up basic auth headers
        auth_header = base64.b64encode(f"{username}:{api_token}".encode()).decode()
        await page.set_extra_http_headers({
            "Authorization": f"Basic {auth_header}"
        })
        
        # Navigate to Jira to establish session
        await page.goto(f"{self.base_url}/login")
        
        # Wait for authentication to complete
        try:
            await page.wait_for_url(f"{self.base_url}/jira/your-work", timeout=10000)
        except:
            # If direct redirect doesn't work, try navigating to a test page
            await page.goto(f"{self.base_url}/browse/TEST-1")
            # If we can see the issue, we're authenticated
            try:
                await page.wait_for_selector(self.XRAY_SELECTORS["issue_key"], timeout=5000)
            except:
                raise RuntimeError("Failed to authenticate with Jira")
    
    async def validate_test_display(
        self,
        page: Page,
        test_key: str,
        expected_summary: str,
        test_type: str = "Generic",
        validation_level: ValidationLevel = ValidationLevel.CONTENT
    ) -> VisualValidationResult:
        """
        Validate test display in Jira.
        
        Args:
            page: Playwright page
            test_key: Test issue key (e.g., TEST-123)
            expected_summary: Expected test summary
            test_type: Expected test type
            validation_level: Level of validation to perform
            
        Returns:
            VisualValidationResult with validation results
        """
        result = VisualValidationResult(True, [], {}, {})
        
        try:
            # Navigate to test
            test_url = f"{self.base_url}/browse/{test_key}"
            await page.goto(test_url)
            
            # Wait for page to load
            await page.wait_for_selector(self.XRAY_SELECTORS["test_summary"], timeout=15000)
            
            # Capture full page screenshot
            if self.capture_screenshots:
                screenshot_path = await self._capture_page_screenshot(
                    page, f"test_display_{test_key}"
                )
                result.screenshots["full_page"] = screenshot_path
            
            # Basic validation - check test exists
            test_summary_element = page.locator(self.XRAY_SELECTORS["test_summary"])
            await expect(test_summary_element).to_be_visible(timeout=5000)
            
            # Get actual summary text
            actual_summary = await test_summary_element.text_content()
            result.details["actual_summary"] = actual_summary
            
            if validation_level.value in ["content", "styling", "interaction"]:
                # Validate summary content
                if expected_summary not in actual_summary:
                    result.failed_assertions.append(
                        f"Summary mismatch: expected '{expected_summary}' in '{actual_summary}'"
                    )
                    result.passed = False
                
                # Validate test type if visible
                test_type_element = page.locator(self.XRAY_SELECTORS["test_type_field"])
                if await test_type_element.count() > 0:
                    actual_test_type = await test_type_element.text_content()
                    result.details["actual_test_type"] = actual_test_type
                    
                    if test_type not in actual_test_type:
                        result.failed_assertions.append(
                            f"Test type mismatch: expected '{test_type}' in '{actual_test_type}'"
                        )
                        result.passed = False
            
            result.details["test_key"] = test_key
            result.details["test_url"] = test_url
            
        except Exception as e:
            result.passed = False
            result.failed_assertions.append(f"Failed to validate test display: {e}")
        
        return result
    
    async def validate_manual_test_steps(
        self,
        page: Page,
        test_key: str,
        expected_steps: List[Dict[str, str]],
        validation_level: ValidationLevel = ValidationLevel.CONTENT
    ) -> VisualValidationResult:
        """
        Validate Manual test steps display.
        
        Args:
            page: Playwright page
            test_key: Test issue key
            expected_steps: Expected test steps with action/data/expected keys
            validation_level: Level of validation to perform
            
        Returns:
            VisualValidationResult with validation results
        """
        result = VisualValidationResult(True, [], {}, {})
        
        try:
            # Navigate to test if not already there
            if not await page.url == f"{self.base_url}/browse/{test_key}":
                await page.goto(f"{self.base_url}/browse/{test_key}")
                await page.wait_for_selector(self.XRAY_SELECTORS["test_summary"], timeout=10000)
            
            # Look for test steps table
            steps_table = page.locator(self.XRAY_SELECTORS["test_steps_table"])
            
            if await steps_table.count() == 0:
                result.failed_assertions.append("Test steps table not found")
                result.passed = False
                return result
            
            # Capture steps table screenshot
            if self.capture_screenshots:
                screenshot_path = await self._capture_element_screenshot(
                    steps_table, f"test_steps_{test_key}"
                )
                result.screenshots["test_steps"] = screenshot_path
            
            # Get all step rows
            step_rows = page.locator(self.XRAY_SELECTORS["test_step_row"])
            actual_step_count = await step_rows.count()
            expected_step_count = len(expected_steps)
            
            result.details["actual_step_count"] = actual_step_count
            result.details["expected_step_count"] = expected_step_count
            
            if actual_step_count != expected_step_count:
                result.failed_assertions.append(
                    f"Step count mismatch: expected {expected_step_count}, got {actual_step_count}"
                )
                result.passed = False
            
            if validation_level.value in ["content", "styling", "interaction"]:
                # Validate each step content
                for i, expected_step in enumerate(expected_steps):
                    if i >= actual_step_count:
                        break
                    
                    step_row = step_rows.nth(i)
                    
                    # Check action
                    if "action" in expected_step:
                        action_element = step_row.locator(self.XRAY_SELECTORS["test_step_action"])
                        if await action_element.count() > 0:
                            actual_action = await action_element.text_content()
                            if expected_step["action"] not in actual_action:
                                result.failed_assertions.append(
                                    f"Step {i+1} action mismatch: expected '{expected_step['action']}' in '{actual_action}'"
                                )
                                result.passed = False
                    
                    # Check test data
                    if "data" in expected_step:
                        data_element = step_row.locator(self.XRAY_SELECTORS["test_step_data"])
                        if await data_element.count() > 0:
                            actual_data = await data_element.text_content()
                            if expected_step["data"] not in actual_data:
                                result.failed_assertions.append(
                                    f"Step {i+1} data mismatch: expected '{expected_step['data']}' in '{actual_data}'"
                                )
                                result.passed = False
                    
                    # Check expected result
                    if "expected" in expected_step:
                        expected_element = step_row.locator(self.XRAY_SELECTORS["test_step_expected"])
                        if await expected_element.count() > 0:
                            actual_expected = await expected_element.text_content()
                            if expected_step["expected"] not in actual_expected:
                                result.failed_assertions.append(
                                    f"Step {i+1} expected result mismatch: expected '{expected_step['expected']}' in '{actual_expected}'"
                                )
                                result.passed = False
        
        except Exception as e:
            result.passed = False
            result.failed_assertions.append(f"Failed to validate manual test steps: {e}")
        
        return result
    
    async def validate_gherkin_scenario(
        self,
        page: Page,
        test_key: str,
        expected_gherkin: str,
        validation_level: ValidationLevel = ValidationLevel.CONTENT
    ) -> VisualValidationResult:
        """
        Validate Gherkin scenario display and syntax highlighting.
        
        Args:
            page: Playwright page
            test_key: Test issue key
            expected_gherkin: Expected Gherkin scenario text
            validation_level: Level of validation to perform
            
        Returns:
            VisualValidationResult with validation results
        """
        result = VisualValidationResult(True, [], {}, {})
        
        try:
            # Navigate to test if not already there
            if not await page.url == f"{self.base_url}/browse/{test_key}":
                await page.goto(f"{self.base_url}/browse/{test_key}")
                await page.wait_for_selector(self.XRAY_SELECTORS["test_summary"], timeout=10000)
            
            # Look for Gherkin editor
            gherkin_editor = page.locator(self.XRAY_SELECTORS["gherkin_editor"])
            
            if await gherkin_editor.count() == 0:
                # Try alternative selector
                gherkin_editor = page.locator(self.XRAY_SELECTORS["gherkin_content"])
            
            if await gherkin_editor.count() == 0:
                result.failed_assertions.append("Gherkin editor/content not found")
                result.passed = False
                return result
            
            # Capture Gherkin editor screenshot
            if self.capture_screenshots:
                screenshot_path = await self._capture_element_screenshot(
                    gherkin_editor, f"gherkin_scenario_{test_key}"
                )
                result.screenshots["gherkin_scenario"] = screenshot_path
            
            if validation_level.value in ["content", "styling", "interaction"]:
                # Get Gherkin content
                actual_gherkin = await gherkin_editor.text_content()
                result.details["actual_gherkin"] = actual_gherkin
                
                # Validate Gherkin content (basic keyword presence)
                gherkin_keywords = ["Given", "When", "Then", "And", "But", "Feature", "Scenario"]
                expected_keywords = [kw for kw in gherkin_keywords if kw in expected_gherkin]
                
                for keyword in expected_keywords:
                    if keyword not in actual_gherkin:
                        result.failed_assertions.append(
                            f"Gherkin keyword '{keyword}' not found in displayed content"
                        )
                        result.passed = False
                
                # Check for syntax highlighting if styling validation requested
                if validation_level == ValidationLevel.STYLING:
                    scenario_elements = page.locator(self.XRAY_SELECTORS["gherkin_scenario"])
                    if await scenario_elements.count() > 0:
                        # Check if syntax highlighting is applied (simplified check)
                        first_line = scenario_elements.first()
                        color = await first_line.evaluate("el => getComputedStyle(el).color")
                        result.details["syntax_highlighting_color"] = color
                        
                        # Basic check - syntax highlighted text shouldn't be default black
                        if color in ["rgb(0, 0, 0)", "black", ""]:
                            result.failed_assertions.append("Gherkin syntax highlighting may not be applied")
                            # Note: This is not a hard failure as styling can vary
        
        except Exception as e:
            result.passed = False
            result.failed_assertions.append(f"Failed to validate Gherkin scenario: {e}")
        
        return result
    
    async def validate_test_execution_status(
        self,
        page: Page,
        execution_key: str,
        expected_status: str = None,
        validation_level: ValidationLevel = ValidationLevel.BASIC
    ) -> VisualValidationResult:
        """
        Validate test execution status display.
        
        Args:
            page: Playwright page
            execution_key: Test execution issue key
            expected_status: Expected execution status
            validation_level: Level of validation to perform
            
        Returns:
            VisualValidationResult with validation results
        """
        result = VisualValidationResult(True, [], {}, {})
        
        try:
            # Navigate to test execution
            execution_url = f"{self.base_url}/browse/{execution_key}"
            await page.goto(execution_url)
            
            # Wait for page to load
            await page.wait_for_selector(self.XRAY_SELECTORS["test_summary"], timeout=15000)
            
            # Capture execution page screenshot
            if self.capture_screenshots:
                screenshot_path = await self._capture_page_screenshot(
                    page, f"test_execution_{execution_key}"
                )
                result.screenshots["execution_page"] = screenshot_path
            
            # Look for execution status elements
            status_element = page.locator(self.XRAY_SELECTORS["execution_status"])
            
            if await status_element.count() > 0:
                if validation_level.value in ["content", "styling", "interaction"]:
                    actual_status = await status_element.text_content()
                    result.details["actual_status"] = actual_status
                    
                    if expected_status and expected_status not in actual_status:
                        result.failed_assertions.append(
                            f"Execution status mismatch: expected '{expected_status}' in '{actual_status}'"
                        )
                        result.passed = False
            else:
                result.failed_assertions.append("Execution status element not found")
                result.passed = False
            
            # Check for execution results/history if present
            results_element = page.locator(self.XRAY_SELECTORS["execution_results"])
            history_element = page.locator(self.XRAY_SELECTORS["execution_history"])
            
            result.details["has_execution_results"] = await results_element.count() > 0
            result.details["has_execution_history"] = await history_element.count() > 0
        
        except Exception as e:
            result.passed = False
            result.failed_assertions.append(f"Failed to validate execution status: {e}")
        
        return result
    
    async def validate_test_repository_structure(
        self,
        page: Page,
        project_key: str,
        expected_folders: List[str] = None,
        validation_level: ValidationLevel = ValidationLevel.BASIC
    ) -> VisualValidationResult:
        """
        Validate test repository folder structure.
        
        Args:
            page: Playwright page
            project_key: Jira project key
            expected_folders: Expected folder names
            validation_level: Level of validation to perform
            
        Returns:
            VisualValidationResult with validation results
        """
        result = VisualValidationResult(True, [], {}, {})
        
        try:
            # Navigate to test repository
            repo_url = f"{self.base_url}/secure/Tests.jspa#/project/{project_key}"
            await page.goto(repo_url)
            
            # Wait for test repository to load
            await page.wait_for_selector(self.XRAY_SELECTORS["test_repo_tree"], timeout=15000)
            
            # Capture repository screenshot
            if self.capture_screenshots:
                screenshot_path = await self._capture_page_screenshot(
                    page, f"test_repository_{project_key}"
                )
                result.screenshots["repository"] = screenshot_path
            
            if validation_level.value in ["content", "styling", "interaction"]:
                # Check for expected folders
                if expected_folders:
                    folder_elements = page.locator(self.XRAY_SELECTORS["test_repo_folder"])
                    
                    for expected_folder in expected_folders:
                        folder_found = False
                        folder_count = await folder_elements.count()
                        
                        for i in range(folder_count):
                            folder = folder_elements.nth(i)
                            folder_text = await folder.text_content()
                            
                            if expected_folder in folder_text:
                                folder_found = True
                                break
                        
                        if not folder_found:
                            result.failed_assertions.append(f"Expected folder '{expected_folder}' not found")
                            result.passed = False
                
                # Count total folders and tests
                total_folders = await page.locator(self.XRAY_SELECTORS["test_repo_folder"]).count()
                total_tests = await page.locator(self.XRAY_SELECTORS["test_repo_test"]).count()
                
                result.details["total_folders"] = total_folders
                result.details["total_tests"] = total_tests
        
        except Exception as e:
            result.passed = False
            result.failed_assertions.append(f"Failed to validate test repository: {e}")
        
        return result
    
    async def _capture_element_screenshot(self, element: Locator, name: str) -> Path:
        """Capture screenshot of specific element."""
        screenshot_path = self.screenshots_dir / f"{name}.png"
        await element.screenshot(path=screenshot_path)
        return screenshot_path
    
    async def _capture_page_screenshot(self, page: Page, name: str) -> Path:
        """Capture full page screenshot."""
        screenshot_path = self.screenshots_dir / f"{name}_full.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        return screenshot_path
    
    async def cleanup(self):
        """Cleanup visual validator resources."""
        # Any cleanup needed for the validator
        pass