"""Parameter validators for MCP tools.

This module provides comprehensive validation for MCP tool parameters,
ensuring requests are valid before making API calls and providing
clear error messages for AI callers.
"""

import re
import json
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

# Handle both package and direct execution import modes
try:
    from ..errors.mcp_errors import MCPErrorResponse, MCPErrorBuilder, MCPValidationHelper
    from ..exceptions import ValidationError
    from .jql_validator import validate_jql as validate_jql_safe
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from errors.mcp_errors import MCPErrorResponse, MCPErrorBuilder, MCPValidationHelper
    from exceptions import ValidationError
    from validators.jql_validator import validate_jql as validate_jql_safe


class XrayToolValidators:
    """Validators for Xray MCP tool parameters."""
    
    @staticmethod
    def validate_issue_id(issue_id: str, field_name: str = "issue_id") -> Optional[MCPErrorResponse]:
        """Validate Jira issue ID or key format.
        
        Args:
            issue_id: The issue ID or key to validate
            field_name: Name of the field for error reporting
            
        Returns:
            MCPErrorResponse if invalid, None if valid
        """
        if not issue_id:
            return MCPErrorBuilder.missing_required(
                field=field_name,
                hint="Issue ID can be numeric (e.g., '12345') or Jira key (e.g., 'TEST-123').",
                example_call={"tool": "get_test", "arguments": {"issue_id": "TEST-123"}}
            )
        
        if not isinstance(issue_id, str):
            return MCPErrorBuilder.invalid_parameter(
                field=field_name,
                expected="string",
                got=str(type(issue_id).__name__),
                hint="Issue ID must be a string like '12345' or 'TEST-123'.",
                example_call={"tool": "get_test", "arguments": {"issue_id": "TEST-123"}}
            )
        
        # Allow numeric IDs or Jira key format (PROJECT-NUMBER)
        if not (issue_id.isdigit() or re.match(r'^[A-Z][A-Z0-9]*-\d+$', issue_id)):
            return MCPErrorBuilder.invalid_parameter(
                field=field_name,
                expected="numeric ID or Jira key (e.g., 'TEST-123')",
                got=issue_id,
                hint="Use numeric ID like '12345' or Jira key like 'TEST-123'.",
                example_call={"tool": "get_test", "arguments": {"issue_id": "TEST-123"}}
            )
        
        return None
    
    @staticmethod
    def validate_summary(summary: str) -> Optional[MCPErrorResponse]:
        """Validate summary/title parameter.
        
        Args:
            summary: The summary to validate
            
        Returns:
            MCPErrorResponse if invalid, None if valid
        """
        if not summary:
            return MCPErrorBuilder.missing_required(
                field="summary",
                hint="Summary is required to identify the test or execution.",
                example_call={"tool": "create_test", "arguments": {"summary": "Test login functionality"}}
            )
        
        if not isinstance(summary, str):
            return MCPErrorBuilder.invalid_parameter(
                field="summary",
                expected="string",
                got=str(type(summary).__name__),
                hint="Summary must be a descriptive string.",
                example_call={"tool": "create_test", "arguments": {"summary": "Test login functionality"}}
            )
        
        if len(summary.strip()) < 5:
            return MCPErrorBuilder.invalid_parameter(
                field="summary",
                expected="string with at least 5 characters",
                got=f"'{summary}' ({len(summary.strip())} chars)",
                hint="Summary should be descriptive enough to identify the test/execution.",
                example_call={"tool": "create_test", "arguments": {"summary": "Test login functionality"}}
            )
        
        if len(summary) > 255:
            return MCPErrorBuilder.invalid_parameter(
                field="summary",
                expected="string with at most 255 characters",
                got=f"{len(summary)} characters",
                hint="Summary is too long. Keep it under 255 characters.",
                example_call={"tool": "create_test", "arguments": {"summary": summary[:200] + "..."}}
            )
        
        return None
    
    @staticmethod
    def validate_jql(jql: Optional[str]) -> Optional[MCPErrorResponse]:
        """Validate JQL query parameter.
        
        Args:
            jql: The JQL query to validate
            
        Returns:
            MCPErrorResponse if invalid, None if valid
        """
        if jql is None:
            return None
        
        if not isinstance(jql, str):
            return MCPErrorBuilder.invalid_parameter(
                field="jql",
                expected="string or null",
                got=str(type(jql).__name__),
                hint="JQL must be a valid query string like 'project = PROJ'.",
                example_call={"tool": "get_tests", "arguments": {"jql": "project = PROJ AND status = Open"}}
            )
        
        if len(jql.strip()) == 0:
            return MCPErrorBuilder.invalid_parameter(
                field="jql",
                expected="non-empty string",
                got="empty string",
                hint="JQL query cannot be empty. Use null for no filtering.",
                example_call={"tool": "get_tests", "arguments": {"jql": "project = PROJ"}}
            )
        
        # Use existing JQL validator for injection prevention
        try:
            validate_jql_safe(jql)
        except ValidationError as e:
            return MCPErrorBuilder.invalid_parameter(
                field="jql",
                expected="safe JQL query",
                got=jql,
                hint=f"JQL validation failed: {str(e)}. Use simple queries like 'project = PROJ'.",
                example_call={"tool": "get_tests", "arguments": {"jql": "project = PROJ AND status = Open"}}
            )
        
        return None
    
    @staticmethod
    def validate_test_steps(steps: Optional[Union[str, List[Dict[str, str]]]]) -> Optional[MCPErrorResponse]:
        """Validate test steps for Manual tests.
        
        Args:
            steps: The test steps to validate
            
        Returns:
            MCPErrorResponse if invalid, None if valid
        """
        if steps is None:
            return None
        
        # Handle JSON string format
        if isinstance(steps, str):
            try:
                steps_parsed = json.loads(steps)
            except json.JSONDecodeError as e:
                return MCPErrorBuilder.invalid_parameter(
                    field="steps",
                    expected="valid JSON array",
                    got=steps[:50] + "..." if len(steps) > 50 else steps,
                    hint=f"JSON syntax error: {e.msg}. Use proper JSON array format.",
                    example_call={
                        "tool": "create_test",
                        "arguments": {
                            "steps": '[{"action": "Open login page", "result": "Page loads", "data": "URL: /login"}]'
                        }
                    }
                )
            steps = steps_parsed
        
        if not isinstance(steps, list):
            return MCPErrorBuilder.invalid_parameter(
                field="steps",
                expected="array of step objects",
                got=str(type(steps).__name__),
                hint="Steps must be an array of objects with 'action' and 'result' fields.",
                example_call={
                    "tool": "create_test",
                    "arguments": {
                        "steps": [{"action": "Open login page", "result": "Page loads"}]
                    }
                }
            )
        
        if len(steps) > 50:
            return MCPErrorBuilder.invalid_parameter(
                field="steps",
                expected="array with at most 50 steps",
                got=f"{len(steps)} steps",
                hint="Too many steps. Break large tests into smaller, focused tests.",
                example_call={
                    "tool": "create_test",
                    "arguments": {
                        "steps": [{"action": "Step 1", "result": "Result 1"}]
                    }
                }
            )
        
        # Validate each step
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                return MCPErrorBuilder.invalid_parameter(
                    field="steps",
                    expected="array of objects",
                    got=f"step[{i}] is {type(step).__name__}",
                    hint="Each step must be an object with 'action' and 'result' fields.",
                    example_call={
                        "tool": "create_test",
                        "arguments": {
                            "steps": [{"action": "Step action", "result": "Expected result"}]
                        }
                    }
                )
            
            # Validate required fields
            if "action" not in step:
                return MCPErrorBuilder.missing_required(
                    field="steps[].action",
                    hint="Each step must have an 'action' field describing what to do.",
                    example_call={
                        "tool": "create_test",
                        "arguments": {
                            "steps": [{"action": "Click login button", "result": "User is logged in"}]
                        }
                    }
                )
            
            if "result" not in step:
                return MCPErrorBuilder.missing_required(
                    field="steps[].result",
                    hint="Each step must have a 'result' field describing the expected outcome.",
                    example_call={
                        "tool": "create_test",
                        "arguments": {
                            "steps": [{"action": "Click login button", "result": "User is logged in"}]
                        }
                    }
                )
            
            # Validate field types and lengths
            if not isinstance(step["action"], str) or len(step["action"].strip()) < 3:
                return MCPErrorBuilder.invalid_parameter(
                    field=f"steps[{i}].action",
                    expected="string with at least 3 characters",
                    got=str(step.get("action", "")),
                    hint="Step action must be a descriptive string.",
                    example_call={
                        "tool": "create_test",
                        "arguments": {
                            "steps": [{"action": "Click login button", "result": "User is logged in"}]
                        }
                    }
                )
            
            if not isinstance(step["result"], str) or len(step["result"].strip()) < 3:
                return MCPErrorBuilder.invalid_parameter(
                    field=f"steps[{i}].result",
                    expected="string with at least 3 characters",
                    got=str(step.get("result", "")),
                    hint="Step result must be a descriptive string.",
                    example_call={
                        "tool": "create_test",
                        "arguments": {
                            "steps": [{"action": "Click login button", "result": "User is logged in"}]
                        }
                    }
                )
            
            # Validate optional data field
            if "data" in step and step["data"] is not None and not isinstance(step["data"], str):
                return MCPErrorBuilder.invalid_parameter(
                    field=f"steps[{i}].data",
                    expected="string or null",
                    got=str(type(step["data"]).__name__),
                    hint="Step data must be a string or omitted.",
                    example_call={
                        "tool": "create_test",
                        "arguments": {
                            "steps": [{"action": "Enter username", "result": "Username accepted", "data": "testuser"}]
                        }
                    }
                )
        
        return None
    
    @staticmethod
    def validate_gherkin(gherkin: Optional[str]) -> Optional[MCPErrorResponse]:
        """Validate Gherkin scenario for Cucumber tests.
        
        Args:
            gherkin: The Gherkin scenario to validate
            
        Returns:
            MCPErrorResponse if invalid, None if valid
        """
        if gherkin is None:
            return None
        
        if not isinstance(gherkin, str):
            return MCPErrorBuilder.invalid_parameter(
                field="gherkin",
                expected="string",
                got=str(type(gherkin).__name__),
                hint="Gherkin must be a string containing the scenario definition.",
                example_call={
                    "tool": "create_test",
                    "arguments": {
                        "gherkin": "Feature: Login\\nScenario: Valid login\\nGiven I am on the login page\\nWhen I enter valid credentials\\nThen I should be logged in"
                    }
                }
            )
        
        if len(gherkin.strip()) < 10:
            return MCPErrorBuilder.invalid_parameter(
                field="gherkin",
                expected="non-empty Gherkin scenario",
                got=f"'{gherkin[:50]}...' ({len(gherkin.strip())} chars)",
                hint="Gherkin scenario must contain Feature, Scenario, and steps (Given/When/Then).",
                example_call={
                    "tool": "create_test",
                    "arguments": {
                        "gherkin": "Feature: Login\\nScenario: Valid login\\nGiven I am on the login page\\nWhen I enter valid credentials\\nThen I should be logged in"
                    }
                }
            )
        
        # Basic Gherkin structure validation
        required_keywords = ["Feature:", "Scenario:"]
        step_keywords = ["Given ", "When ", "Then ", "And ", "But "]
        
        has_required = all(keyword in gherkin for keyword in required_keywords)
        has_steps = any(keyword in gherkin for keyword in step_keywords)
        
        if not has_required:
            return MCPErrorBuilder.invalid_parameter(
                field="gherkin",
                expected="valid Gherkin with Feature and Scenario",
                got=gherkin[:100] + "..." if len(gherkin) > 100 else gherkin,
                hint="Gherkin must include 'Feature:' and 'Scenario:' declarations.",
                example_call={
                    "tool": "create_test",
                    "arguments": {
                        "gherkin": "Feature: Login\\nScenario: Valid login\\nGiven I am on the login page\\nWhen I enter valid credentials\\nThen I should be logged in"
                    }
                }
            )
        
        if not has_steps:
            return MCPErrorBuilder.invalid_parameter(
                field="gherkin",
                expected="Gherkin with test steps (Given/When/Then)",
                got=gherkin[:100] + "..." if len(gherkin) > 100 else gherkin,
                hint="Gherkin scenario must include test steps like 'Given', 'When', and 'Then'.",
                example_call={
                    "tool": "create_test",
                    "arguments": {
                        "gherkin": "Feature: Login\\nScenario: Valid login\\nGiven I am on the login page\\nWhen I enter valid credentials\\nThen I should be logged in"
                    }
                }
            )
        
        return None
    
    @staticmethod
    def validate_test_issue_ids(test_issue_ids: Optional[List[str]]) -> Optional[MCPErrorResponse]:
        """Validate array of test issue IDs.
        
        Args:
            test_issue_ids: List of test issue IDs to validate
            
        Returns:
            MCPErrorResponse if invalid, None if valid
        """
        if test_issue_ids is None:
            return None
        
        if not isinstance(test_issue_ids, list):
            return MCPErrorBuilder.invalid_parameter(
                field="test_issue_ids",
                expected="array of strings",
                got=str(type(test_issue_ids).__name__),
                hint="Test issue IDs must be an array of issue IDs or keys.",
                example_call={
                    "tool": "add_tests_to_execution",
                    "arguments": {
                        "test_issue_ids": ["TEST-123", "TEST-124"]
                    }
                }
            )
        
        if len(test_issue_ids) == 0:
            return MCPErrorBuilder.invalid_parameter(
                field="test_issue_ids",
                expected="non-empty array",
                got="empty array",
                hint="At least one test issue ID must be provided.",
                example_call={
                    "tool": "add_tests_to_execution",
                    "arguments": {
                        "test_issue_ids": ["TEST-123"]
                    }
                }
            )
        
        if len(test_issue_ids) > 100:
            return MCPErrorBuilder.invalid_parameter(
                field="test_issue_ids",
                expected="array with at most 100 items",
                got=f"{len(test_issue_ids)} items",
                hint="Too many test IDs. Process in batches of 100 or less.",
                example_call={
                    "tool": "add_tests_to_execution",
                    "arguments": {
                        "test_issue_ids": ["TEST-123", "TEST-124"]
                    }
                }
            )
        
        # Validate each ID
        for i, issue_id in enumerate(test_issue_ids):
            validation_error = XrayToolValidators.validate_issue_id(issue_id, f"test_issue_ids[{i}]")
            if validation_error:
                return validation_error
        
        return None
    
    @staticmethod
    def validate_environment_names(environments: Optional[List[str]]) -> Optional[MCPErrorResponse]:
        """Validate test environment names.
        
        Args:
            environments: List of environment names to validate
            
        Returns:
            MCPErrorResponse if invalid, None if valid
        """
        if environments is None:
            return None
        
        if not isinstance(environments, list):
            return MCPErrorBuilder.invalid_parameter(
                field="test_environments",
                expected="array of strings",
                got=str(type(environments).__name__),
                hint="Environment names must be an array of strings.",
                example_call={
                    "tool": "create_test_execution",
                    "arguments": {
                        "test_environments": ["staging", "production"]
                    }
                }
            )
        
        if len(environments) > 10:
            return MCPErrorBuilder.invalid_parameter(
                field="test_environments",
                expected="array with at most 10 environments",
                got=f"{len(environments)} environments",
                hint="Too many environments. Use the most relevant ones.",
                example_call={
                    "tool": "create_test_execution",
                    "arguments": {
                        "test_environments": ["staging", "production"]
                    }
                }
            )
        
        # Validate each environment name
        for i, env_name in enumerate(environments):
            if not isinstance(env_name, str):
                return MCPErrorBuilder.invalid_parameter(
                    field=f"test_environments[{i}]",
                    expected="string",
                    got=str(type(env_name).__name__),
                    hint="Each environment name must be a string.",
                    example_call={
                        "tool": "create_test_execution",
                        "arguments": {
                            "test_environments": ["staging", "production"]
                        }
                    }
                )
            
            if len(env_name.strip()) < 2:
                return MCPErrorBuilder.invalid_parameter(
                    field=f"test_environments[{i}]",
                    expected="string with at least 2 characters",
                    got=f"'{env_name}'",
                    hint="Environment name must be descriptive (e.g., 'staging', 'prod').",
                    example_call={
                        "tool": "create_test_execution",
                        "arguments": {
                            "test_environments": ["staging", "production"]
                        }
                    }
                )
        
        return None
    
    @staticmethod
    def validate_folder_path(folder_path: str) -> Optional[MCPErrorResponse]:
        """Validate test repository folder path.
        
        Args:
            folder_path: The folder path to validate
            
        Returns:
            MCPErrorResponse if invalid, None if valid
        """
        if not isinstance(folder_path, str):
            return MCPErrorBuilder.invalid_parameter(
                field="folder_path",
                expected="string",
                got=str(type(folder_path).__name__),
                hint="Folder path must be a string like '/Component/UI' or '/'.",
                example_call={
                    "tool": "move_test_to_folder",
                    "arguments": {
                        "folder_path": "/Component/UI"
                    }
                }
            )
        
        if not folder_path.startswith('/'):
            return MCPErrorBuilder.invalid_parameter(
                field="folder_path",
                expected="path starting with '/'",
                got=folder_path,
                hint="Folder path must start with '/' for absolute path (e.g., '/Component/UI').",
                example_call={
                    "tool": "move_test_to_folder",
                    "arguments": {
                        "folder_path": "/Component/UI"
                    }
                }
            )
        
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in invalid_chars:
            if char in folder_path:
                return MCPErrorBuilder.invalid_parameter(
                    field="folder_path",
                    expected="path without special characters",
                    got=folder_path,
                    hint=f"Folder path cannot contain '{char}'. Use standard folder names.",
                    example_call={
                        "tool": "move_test_to_folder",
                        "arguments": {
                            "folder_path": "/Component/UI"
                        }
                    }
                )
        
        # Check path depth (reasonable limit)
        path_parts = [part for part in folder_path.split('/') if part]
        if len(path_parts) > 10:
            return MCPErrorBuilder.invalid_parameter(
                field="folder_path",
                expected="path with at most 10 levels",
                got=f"{len(path_parts)} levels",
                hint="Folder path is too deep. Use a simpler folder structure.",
                example_call={
                    "tool": "move_test_to_folder",
                    "arguments": {
                        "folder_path": "/Component/UI"
                    }
                }
            )
        
        return None
    
    @staticmethod
    def validate_entity_type(entity_type: str) -> Optional[MCPErrorResponse]:
        """Validate entity type for JQL queries.
        
        Args:
            entity_type: The entity type to validate
            
        Returns:
            MCPErrorResponse if invalid, None if valid
        """
        valid_types = ["test", "testexecution"]
        
        if not isinstance(entity_type, str):
            return MCPErrorBuilder.invalid_parameter(
                field="entity_type",
                expected="string",
                got=str(type(entity_type).__name__),
                hint=f"Entity type must be one of: {', '.join(valid_types)}",
                example_call={"tool": "execute_jql_query", "arguments": {"entity_type": "test"}}
            )
        
        if entity_type not in valid_types:
            return MCPErrorBuilder.invalid_parameter(
                field="entity_type",
                expected=f"one of: {', '.join(valid_types)}",
                got=entity_type,
                hint="Use 'test' for test entities or 'testexecution' for execution entities",
                example_call={"tool": "execute_jql_query", "arguments": {"entity_type": "test"}}
            )
        
        return None


# Convenience validation functions using the class methods
validate_project_key = MCPValidationHelper.validate_project_key
validate_limit = MCPValidationHelper.validate_limit
validate_test_type = MCPValidationHelper.validate_test_type
validate_json_string = MCPValidationHelper.validate_json_string

validate_issue_id = XrayToolValidators.validate_issue_id
validate_summary = XrayToolValidators.validate_summary
validate_jql = XrayToolValidators.validate_jql
validate_test_steps = XrayToolValidators.validate_test_steps
validate_gherkin = XrayToolValidators.validate_gherkin
validate_test_issue_ids = XrayToolValidators.validate_test_issue_ids
validate_environment_names = XrayToolValidators.validate_environment_names
validate_folder_path = XrayToolValidators.validate_folder_path