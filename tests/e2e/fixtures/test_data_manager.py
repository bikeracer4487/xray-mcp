"""
Test data lifecycle management for Xray MCP E2E tests.

Provides utilities for creating unique test data, tracking created resources,
and cleaning up test artifacts after test completion.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from pathlib import Path
import random
import string


@dataclass
class TrackedResource:
    """Represents a test resource that needs cleanup."""
    resource_type: str  # test, execution, plan, set, etc.
    resource_id: str    # Issue ID or key
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataLifecycleManager:
    """Manages test data lifecycle and cleanup."""
    
    def __init__(
        self,
        project_key: str,
        prefix: str = "XrayMCP_E2E",
        label: str = "xray-mcp-e2e-test",
        cleanup_on_success: bool = True,
        cleanup_on_failure: bool = False
    ):
        """
        Initialize test data manager.
        
        Args:
            project_key: Jira project key for test creation
            prefix: Prefix for all test titles/names
            label: Label to apply to created resources
            cleanup_on_success: Whether to cleanup on successful tests
            cleanup_on_failure: Whether to cleanup on failed tests
        """
        self.project_key = project_key
        self.prefix = prefix
        self.label = label
        self.cleanup_on_success = cleanup_on_success
        self.cleanup_on_failure = cleanup_on_failure
        
        # Generate unique session identifier
        self.session_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Track created resources
        self.created_resources: Dict[str, TrackedResource] = {}
        self.cleanup_queue: List[TrackedResource] = []
    
    def generate_unique_title(self, base_title: str) -> str:
        """
        Generate unique title for test resources.
        
        Args:
            base_title: Base title to make unique
            
        Returns:
            Unique title with timestamp and session ID
        """
        timestamp = datetime.now().strftime("%H%M%S")
        return f"{self.prefix}_{base_title}_{timestamp}_{self.session_id[:8]}"
    
    def generate_unique_key(self) -> str:
        """Generate unique key for test resources."""
        return f"{self.prefix}_{uuid.uuid4().hex[:12]}"
    
    def generate_test_description(self, content_type: str = "basic") -> str:
        """
        Generate test description content.
        
        Args:
            content_type: Type of content to generate
                - basic: Simple markdown content
                - rich: Rich markdown with formatting
                - html: HTML content
                - structured: Structured content with sections
                
        Returns:
            Generated description content
        """
        base_info = f"""
# Test Description

This is a test created by Xray MCP E2E tests.

**Session ID**: {self.session_id}
**Created**: {datetime.now().isoformat()}
**Project**: {self.project_key}
**Label**: {self.label}
"""
        
        if content_type == "basic":
            return base_info + """
## Purpose
This test validates the basic functionality of the Xray MCP server.

## Notes
- Automatically generated test data
- Will be cleaned up after test completion
"""
        
        elif content_type == "rich":
            return base_info + """
## Test Objectives
- **Primary**: Validate MCP contract functionality
- **Secondary**: Ensure proper UI rendering
- *Tertiary*: Verify data persistence

## Test Data
| Field | Value |
|-------|--------|
| Type | Automated E2E Test |
| Priority | Medium |
| Environment | Test |

## Code Example
```python
def test_example():
    assert True, "This is a sample test"
```

> **Note**: This content tests rich markdown rendering in Xray.

### Checklist
- [x] Test created
- [ ] Test executed  
- [ ] Results verified
"""
        
        elif content_type == "html":
            return f"""
<h1>HTML Test Description</h1>
<p>This test contains <strong>HTML content</strong> to verify rendering.</p>
<ul>
<li>Session: {self.session_id}</li>
<li>Project: {self.project_key}</li>
<li>Timestamp: {datetime.now().isoformat()}</li>
</ul>
<blockquote>
<p>This tests HTML content rendering in test descriptions.</p>
</blockquote>
"""
        
        elif content_type == "structured":
            return base_info + """
## Test Specification

### Prerequisites
1. Xray MCP server is running
2. Valid API credentials configured
3. Test project exists in Jira

### Test Environment
- **Browser**: Chromium (Playwright)
- **API**: Xray GraphQL
- **Authentication**: JWT tokens
- **Data Cleanup**: Automatic

### Expected Behavior
The system should:
1. Create test resources successfully
2. Render content properly in Xray UI
3. Handle validation correctly
4. Clean up resources after completion

### Success Criteria
✅ All MCP contract tests pass
✅ Visual validation succeeds  
✅ Resources created and accessible
✅ No data leakage between tests

### Failure Handling
- Screenshots captured for visual failures
- API response logs preserved
- Resource cleanup attempted regardless
"""
        
        return base_info
    
    def generate_manual_test_steps(
        self,
        step_count: int = 3,
        include_data: bool = True
    ) -> List[Dict[str, str]]:
        """
        Generate manual test steps.
        
        Args:
            step_count: Number of test steps to generate
            include_data: Whether to include test data fields
            
        Returns:
            List of test steps with action/data/expected fields
        """
        steps = []
        
        for i in range(step_count):
            step = {
                "action": f"Step {i+1}: Perform test action #{i+1}",
                "expected": f"Expected result for step {i+1}"
            }
            
            if include_data:
                step["data"] = f"Test data for step {i+1}"
            
            steps.append(step)
        
        # Add some variety to the steps
        if step_count >= 3:
            steps[0]["action"] = "Navigate to the test application"
            steps[0]["expected"] = "Application loads successfully"
            
            steps[1]["action"] = "Enter test credentials and login"
            steps[1]["data"] = "username: testuser, password: testpass"
            steps[1]["expected"] = "User is logged in and dashboard is displayed"
            
            if step_count > 2:
                steps[2]["action"] = "Verify core functionality works"
                steps[2]["expected"] = "All features function as expected"
        
        return steps
    
    def generate_gherkin_scenario(self, scenario_type: str = "basic") -> str:
        """
        Generate Gherkin scenario content.
        
        Args:
            scenario_type: Type of scenario to generate
                - basic: Simple Given/When/Then
                - complex: Multiple scenarios with examples
                - outline: Scenario outline with examples table
                
        Returns:
            Gherkin scenario text
        """
        if scenario_type == "basic":
            return f"""Feature: E2E Test Feature
  Background test scenario for Xray MCP validation
  
  Session: {self.session_id}

Scenario: Basic test validation
  Given I have a test application
  When I perform the test action
  Then the expected result should occur
  And the system should remain stable
"""
        
        elif scenario_type == "complex":
            return f"""Feature: Complex E2E Test Feature
  Comprehensive testing scenarios for Xray MCP
  
  Session: {self.session_id}
  
  Background:
    Given the test environment is prepared
    And all prerequisites are met

Scenario: User authentication
  Given I am on the login page
  When I enter valid credentials
  Then I should be logged in
  And I should see the dashboard

Scenario: Data validation
  Given I am logged in
  When I submit test data
  Then the data should be validated
  And appropriate feedback should be shown
  
Scenario: Error handling
  Given I am in the application
  When an error occurs
  Then the error should be handled gracefully
  And the user should see appropriate messaging
"""
        
        elif scenario_type == "outline":
            return f"""Feature: Parameterized E2E Tests
  Data-driven test scenarios for Xray MCP
  
  Session: {self.session_id}

Scenario Outline: Login with different users
  Given I am on the login page
  When I enter "<username>" and "<password>"
  Then I should see "<result>"
  
  Examples:
    | username | password | result |
    | admin    | admin123 | dashboard |
    | user     | user123  | user_page |
    | guest    | guest123 | limited_access |
    | invalid  | wrong    | error_message |
"""
        
        return f"""Feature: Default E2E Test
  Generated test scenario
  
Scenario: Default test case
  Given the system is ready
  When I run the test
  Then it should pass
"""
    
    def track_resource(
        self,
        resource_type: str,
        resource_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track a created resource for cleanup.
        
        Args:
            resource_type: Type of resource (test, execution, plan, etc.)
            resource_id: Resource ID or key
            metadata: Additional metadata about the resource
        """
        resource = TrackedResource(
            resource_type=resource_type,
            resource_id=resource_id,
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        self.created_resources[resource_id] = resource
        self.cleanup_queue.append(resource)
    
    def get_tracked_resources(self, resource_type: Optional[str] = None) -> List[TrackedResource]:
        """
        Get tracked resources, optionally filtered by type.
        
        Args:
            resource_type: Optional resource type filter
            
        Returns:
            List of tracked resources
        """
        if resource_type:
            return [r for r in self.created_resources.values() if r.resource_type == resource_type]
        return list(self.created_resources.values())
    
    def generate_test_data_template(self, template_type: str) -> Dict[str, Any]:
        """
        Generate structured test data templates.
        
        Args:
            template_type: Type of template to generate
                - manual_test: Manual test with steps
                - cucumber_test: Cucumber test with Gherkin
                - generic_test: Generic test with unstructured content
                - test_execution: Test execution data
                - test_plan: Test plan data
                
        Returns:
            Test data template dictionary
        """
        base_data = {
            "project_key": self.project_key,
            "summary": self.generate_unique_title("Template Test"),
            "description": self.generate_test_description("structured"),
            "labels": [self.label]
        }
        
        if template_type == "manual_test":
            return {
                **base_data,
                "test_type": "Manual",
                "steps": self.generate_manual_test_steps(step_count=4, include_data=True)
            }
        
        elif template_type == "cucumber_test":
            return {
                **base_data,
                "test_type": "Cucumber",
                "gherkin": self.generate_gherkin_scenario("complex")
            }
        
        elif template_type == "generic_test":
            return {
                **base_data,
                "test_type": "Generic",
                "unstructured": f"""Generic test definition for session {self.session_id}

Test Steps:
1. Initialize test environment
2. Execute test logic  
3. Validate results
4. Cleanup resources

Expected Results:
- All steps complete successfully
- No errors or exceptions
- Resources properly cleaned up
"""
            }
        
        elif template_type == "test_execution":
            return {
                **base_data,
                "test_environments": ["Test", "Development"],
                "summary": self.generate_unique_title("Test Execution")
            }
        
        elif template_type == "test_plan":
            return {
                **base_data,
                "summary": self.generate_unique_title("Test Plan")
            }
        
        return base_data
    
    async def cleanup(self, force: bool = False):
        """
        Clean up tracked resources.
        
        Args:
            force: Force cleanup regardless of settings
        """
        if not force and not (self.cleanup_on_success or self.cleanup_on_failure):
            return
        
        # Note: Actual cleanup would require access to MCP client
        # This is a placeholder for the cleanup logic
        # In practice, you'd pass the MCP client to the cleanup method
        
        cleanup_count = 0
        for resource in self.cleanup_queue:
            try:
                # Placeholder: actual cleanup would call MCP delete methods
                # await mcp_client.delete_resource(resource.resource_type, resource.resource_id)
                cleanup_count += 1
            except Exception as e:
                # Log cleanup failures but don't stop the process
                print(f"Warning: Failed to cleanup {resource.resource_type} {resource.resource_id}: {e}")
        
        print(f"Cleaned up {cleanup_count} test resources")
        self.cleanup_queue.clear()
        self.created_resources.clear()
    
    def save_test_session_info(self, artifacts_dir: Path):
        """
        Save test session information for debugging.
        
        Args:
            artifacts_dir: Directory to save session info
        """
        session_info = {
            "session_id": self.session_id,
            "project_key": self.project_key,
            "prefix": self.prefix,
            "label": self.label,
            "created_at": datetime.now().isoformat(),
            "resources_created": len(self.created_resources),
            "resources": [
                {
                    "type": r.resource_type,
                    "id": r.resource_id,
                    "created_at": r.created_at.isoformat(),
                    "metadata": r.metadata
                }
                for r in self.created_resources.values()
            ]
        }
        
        session_file = artifacts_dir / f"test_session_{self.session_id}.json"
        artifacts_dir.mkdir(exist_ok=True)
        
        with open(session_file, 'w') as f:
            json.dump(session_info, f, indent=2)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current test session."""
        return {
            "session_id": self.session_id,
            "project_key": self.project_key,
            "resources_created": len(self.created_resources),
            "resource_types": list(set(r.resource_type for r in self.created_resources.values())),
            "cleanup_pending": len(self.cleanup_queue)
        }