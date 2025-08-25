"""Advanced cross-field and context-aware validators for Xray MCP tools.

This module provides sophisticated validation that considers relationships
between fields and context-specific validation rules for Xray operations.
"""

from typing import Dict, Any, List, Optional, Union, Set
from enum import Enum

try:
    from ..exceptions import ValidationError
    from .tool_validators import XrayToolValidators
    from ..errors.mcp_errors import MCPErrorBuilder, MCPErrorResponse
except ImportError:
    from exceptions import ValidationError
    from validators.tool_validators import XrayToolValidators
    from errors.mcp_errors import MCPErrorBuilder, MCPErrorResponse


class TestType(Enum):
    """Supported Xray test types."""
    MANUAL = "Manual"
    CUCUMBER = "Cucumber" 
    GENERIC = "Generic"


class IssueType(Enum):
    """Xray issue types."""
    TEST = "Test"
    TEST_EXECUTION = "Test Execution"
    TEST_PLAN = "Test Plan"
    TEST_SET = "Test Set"
    PRECONDITION = "Precondition"


class CrossFieldValidator:
    """Advanced validator for cross-field validation and context-aware checks."""
    
    def __init__(self):
        """Initialize the cross-field validator."""
        # Test type specific field requirements
        self.test_type_requirements = {
            TestType.MANUAL: {
                "required_fields": ["steps"],
                "forbidden_fields": ["gherkin", "unstructured"],
                "step_fields": ["action", "data", "result"]
            },
            TestType.CUCUMBER: {
                "required_fields": ["gherkin"],
                "forbidden_fields": ["steps", "unstructured"],
                "gherkin_keywords": ["Given", "When", "Then", "And", "But", "Scenario", "Feature"]
            },
            TestType.GENERIC: {
                "required_fields": ["unstructured"],
                "forbidden_fields": ["steps", "gherkin"],
                "min_description_length": 10
            }
        }
        
        # Issue type specific validation rules
        self.issue_type_rules = {
            IssueType.TEST_EXECUTION: {
                "required_fields": ["test_issue_ids"],
                "optional_fields": ["test_environments"],
                "max_tests_per_execution": 1000
            },
            IssueType.TEST_PLAN: {
                "optional_fields": ["test_issue_ids"],
                "max_tests_per_plan": 10000
            },
            IssueType.TEST_SET: {
                "optional_fields": ["test_issue_ids"],
                "max_tests_per_set": 5000
            }
        }
        
        # Environment specific validation
        self.valid_environments = {
            "development", "dev", "staging", "stage", "production", "prod",
            "qa", "test", "uat", "integration", "int", "demo", "sandbox"
        }

    def validate_test_creation(self, data: Dict[str, Any]) -> Optional[MCPErrorResponse]:
        """Validate test creation with cross-field awareness.
        
        Args:
            data: Test creation data including project_key, test_type, etc.
            
        Returns:
            MCPErrorResponse if validation fails, None if valid
        """
        # Extract key fields
        project_key = data.get("project_key")
        test_type_str = data.get("test_type", "Generic")
        summary = data.get("summary")
        
        # Basic field validation first
        if not project_key:
            return MCPErrorBuilder.missing_required(
                field="project_key",
                hint="Specify the Jira project key where the test will be created",
                example_call={"tool": "create_test", "arguments": {"project_key": "PROJ", "summary": "Test Title", "test_type": "Manual"}}
            )
        
        if not summary:
            return MCPErrorBuilder.missing_required(
                field="summary", 
                hint="Provide a descriptive title for the test",
                example_call={"tool": "create_test", "arguments": {"project_key": "PROJ", "summary": "Test Login Functionality", "test_type": "Manual"}}
            )
        
        # Validate test type
        try:
            test_type = TestType(test_type_str)
        except ValueError:
            return MCPErrorBuilder.invalid_parameter(
                field="test_type",
                expected=f"one of {[t.value for t in TestType]}",
                got=test_type_str,
                hint="Use a supported test type",
                example_call={"tool": "create_test", "arguments": {"project_key": "PROJ", "summary": "Test Title", "test_type": "Manual"}}
            )
        
        # Cross-field validation based on test type
        validation_error = self._validate_test_type_fields(test_type, data)
        if validation_error:
            return validation_error
            
        # Environment validation
        if "test_environments" in data:
            validation_error = self._validate_test_environments(data["test_environments"])
            if validation_error:
                return validation_error
        
        return None

    def validate_test_execution_creation(self, data: Dict[str, Any]) -> Optional[MCPErrorResponse]:
        """Validate test execution creation with context awareness.
        
        Args:
            data: Test execution creation data
            
        Returns:
            MCPErrorResponse if validation fails, None if valid
        """
        project_key = data.get("project_key")
        summary = data.get("summary")
        test_issue_ids = data.get("test_issue_ids", [])
        test_environments = data.get("test_environments", [])
        
        # Basic validation
        if not project_key:
            return MCPErrorBuilder.missing_required(
                field="project_key",
                hint="Specify the project key for the test execution",
                example_call={"tool": "create_test_execution", "arguments": {"project_key": "PROJ", "summary": "Sprint 1 Testing"}}
            )
        
        if not summary:
            return MCPErrorBuilder.missing_required(
                field="summary",
                hint="Provide a descriptive title for the test execution",
                example_call={"tool": "create_test_execution", "arguments": {"project_key": "PROJ", "summary": "Sprint 1 Regression Testing"}}
            )
        
        # Validate test count limits
        if test_issue_ids and len(test_issue_ids) > self.issue_type_rules[IssueType.TEST_EXECUTION]["max_tests_per_execution"]:
            return MCPErrorBuilder.invalid_parameter(
                field="test_issue_ids",
                expected=f"maximum {self.issue_type_rules[IssueType.TEST_EXECUTION]['max_tests_per_execution']} tests",
                got=f"{len(test_issue_ids)} tests",
                hint="Consider creating multiple test executions for large test suites",
                example_call={"tool": "create_test_execution", "arguments": {"project_key": "PROJ", "summary": "Execution 1", "test_issue_ids": ["TEST-1", "TEST-2"]}}
            )
        
        # Validate environments
        if test_environments:
            validation_error = self._validate_test_environments(test_environments)
            if validation_error:
                return validation_error
        
        # Validate issue IDs format
        for issue_id in test_issue_ids:
            validation_error = XrayToolValidators.validate_issue_id(issue_id)
            if validation_error:
                return validation_error
                
        return None

    def validate_bulk_operations(self, data: Dict[str, Any], operation_type: str) -> Optional[MCPErrorResponse]:
        """Validate bulk operations like adding/removing tests from sets/plans/executions.
        
        Args:
            data: Operation data
            operation_type: Type of operation (add_tests_to_set, remove_tests_from_execution, etc.)
            
        Returns:
            MCPErrorResponse if validation fails, None if valid
        """
        # Common bulk operation fields
        test_issue_ids = data.get("test_issue_ids", [])
        
        if not test_issue_ids:
            return MCPErrorBuilder.missing_required(
                field="test_issue_ids",
                hint="Provide a list of test issue IDs or keys",
                example_call={"tool": operation_type, "arguments": {"test_issue_ids": ["PROJ-123", "PROJ-124"]}}
            )
        
        # Validate individual issue IDs
        for issue_id in test_issue_ids:
            validation_error = XrayToolValidators.validate_issue_id(issue_id)
            if validation_error:
                return validation_error
        
        # Check for reasonable batch sizes
        if len(test_issue_ids) > 100:
            return MCPErrorBuilder.invalid_parameter(
                field="test_issue_ids",
                expected="maximum 100 tests per operation",
                got=f"{len(test_issue_ids)} tests",
                hint="Split large operations into smaller batches for better performance",
                example_call={"tool": operation_type, "arguments": {"test_issue_ids": ["PROJ-1", "PROJ-2", "..."]}}
            )
        
        # Check for duplicates
        if len(test_issue_ids) != len(set(test_issue_ids)):
            return MCPErrorBuilder.invalid_parameter(
                field="test_issue_ids", 
                expected="unique issue IDs",
                got="duplicate entries found",
                hint="Remove duplicate issue IDs from the list",
                example_call={"tool": operation_type, "arguments": {"test_issue_ids": ["PROJ-123", "PROJ-124"]}}
            )
        
        return None

    def validate_jql_context(self, jql: str, context: Dict[str, Any]) -> Optional[MCPErrorResponse]:
        """Validate JQL query in context of expected usage.
        
        Args:
            jql: JQL query string
            context: Context information (expected_issue_type, project_filter, etc.)
            
        Returns:
            MCPErrorResponse if validation fails, None if valid
        """
        if not jql or not jql.strip():
            return MCPErrorBuilder.invalid_parameter(
                field="jql",
                expected="non-empty JQL query",
                got="empty string",
                hint="Provide a valid JQL query to filter results",
                example_call={"tool": "execute_jql_query", "arguments": {"jql": "project = 'PROJ' AND issuetype = 'Test'"}}
            )
        
        # Basic JQL validation using existing validator
        try:
            from .jql_validator import validate_jql
            validate_jql(jql)
        except ValidationError as e:
            return MCPErrorBuilder.invalid_parameter(
                field="jql",
                expected="valid JQL syntax",
                got="invalid JQL",
                hint=f"JQL validation failed: {str(e)}",
                example_call={"tool": "execute_jql_query", "arguments": {"jql": "project = 'PROJ' AND status = 'Open'"}}
            )
        
        # Context-aware suggestions
        expected_type = context.get("expected_issue_type")
        if expected_type and expected_type.lower() == "test":
            if "issuetype" not in jql.lower():
                # This is just a suggestion, not an error
                pass
        
        return None

    def _validate_test_type_fields(self, test_type: TestType, data: Dict[str, Any]) -> Optional[MCPErrorResponse]:
        """Validate fields specific to test type.
        
        Args:
            test_type: The test type
            data: Test creation data
            
        Returns:
            MCPErrorResponse if validation fails, None if valid
        """
        requirements = self.test_type_requirements[test_type]
        
        # Check required fields
        for required_field in requirements.get("required_fields", []):
            if required_field not in data or not data[required_field]:
                return MCPErrorBuilder.missing_required(
                    field=required_field,
                    hint=f"{required_field} is required for {test_type.value} tests",
                    example_call=self._get_test_type_example(test_type)
                )
        
        # Check forbidden fields
        for forbidden_field in requirements.get("forbidden_fields", []):
            if forbidden_field in data and data[forbidden_field]:
                return MCPErrorBuilder.invalid_parameter(
                    field=forbidden_field,
                    expected="not provided",
                    got=f"{forbidden_field} field present",
                    hint=f"{forbidden_field} is not used with {test_type.value} tests",
                    example_call=self._get_test_type_example(test_type)
                )
        
        # Test type specific validation
        if test_type == TestType.MANUAL:
            return self._validate_manual_test_steps(data.get("steps", []))
        elif test_type == TestType.CUCUMBER:
            return self._validate_gherkin_content(data.get("gherkin", ""))
        elif test_type == TestType.GENERIC:
            return self._validate_generic_test_content(data.get("unstructured", ""))
        
        return None

    def _validate_manual_test_steps(self, steps: List[Dict[str, str]]) -> Optional[MCPErrorResponse]:
        """Validate manual test steps structure.
        
        Args:
            steps: List of test steps
            
        Returns:
            MCPErrorResponse if validation fails, None if valid
        """
        if not steps:
            return MCPErrorBuilder.invalid_parameter(
                field="steps",
                expected="at least one test step",
                got="empty steps list",
                hint="Manual tests require at least one step with action, data, and expected result",
                example_call={"tool": "create_test", "arguments": {"test_type": "Manual", "steps": [{"action": "Open login page", "data": "Navigate to /login", "result": "Login form displayed"}]}}
            )
        
        required_step_fields = ["action", "data", "result"]
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                return MCPErrorBuilder.invalid_parameter(
                    field="steps",
                    expected="list of step objects",
                    got=f"step {i+1} is not an object",
                    hint="Each step must be an object with action, data, and result fields",
                    example_call={"tool": "create_test", "arguments": {"steps": [{"action": "Click login", "data": "username/password", "result": "User logged in"}]}}
                )
            
            for field in required_step_fields:
                if field not in step or not step[field].strip():
                    return MCPErrorBuilder.invalid_parameter(
                        field="steps",
                        expected=f"step {i+1} to have '{field}' field",
                        got=f"missing or empty '{field}'",
                        hint=f"Each test step must include action, data, and expected result",
                        example_call={"tool": "create_test", "arguments": {"steps": [{"action": "Click button", "data": "Submit form", "result": "Form submitted successfully"}]}}
                    )
        
        return None

    def _validate_gherkin_content(self, gherkin: str) -> Optional[MCPErrorResponse]:
        """Validate Gherkin/BDD content structure.
        
        Args:
            gherkin: Gherkin scenario content
            
        Returns:
            MCPErrorResponse if validation fails, None if valid
        """
        if not gherkin or not gherkin.strip():
            return MCPErrorBuilder.invalid_parameter(
                field="gherkin",
                expected="Gherkin scenario content",
                got="empty string",
                hint="Cucumber tests require Gherkin scenario definition",
                example_call={"tool": "create_test", "arguments": {"test_type": "Cucumber", "gherkin": "Feature: Login\n  Scenario: Valid login\n    Given I am on login page\n    When I enter valid credentials\n    Then I should be logged in"}}
            )
        
        # Check for basic Gherkin keywords
        gherkin_lower = gherkin.lower()
        required_keywords = ["scenario", "given", "when", "then"]
        missing_keywords = [kw for kw in required_keywords if kw not in gherkin_lower]
        
        if missing_keywords:
            return MCPErrorBuilder.invalid_parameter(
                field="gherkin",
                expected=f"Gherkin with {', '.join(required_keywords)} keywords",
                got=f"missing {', '.join(missing_keywords)}",
                hint="Ensure your Gherkin follows the Given-When-Then pattern",
                example_call={"tool": "create_test", "arguments": {"gherkin": "Scenario: Test case\n  Given precondition\n  When action\n  Then expected result"}}
            )
        
        return None

    def _validate_generic_test_content(self, unstructured: str) -> Optional[MCPErrorResponse]:
        """Validate generic test content.
        
        Args:
            unstructured: Unstructured test content
            
        Returns:
            MCPErrorResponse if validation fails, None if valid
        """
        if not unstructured or not unstructured.strip():
            return MCPErrorBuilder.invalid_parameter(
                field="unstructured",
                expected="test description or content",
                got="empty string", 
                hint="Generic tests require descriptive content explaining the test",
                example_call={"tool": "create_test", "arguments": {"test_type": "Generic", "unstructured": "This test verifies the user login functionality by checking authentication flow and session management."}}
            )
        
        min_length = self.test_type_requirements[TestType.GENERIC]["min_description_length"]
        if len(unstructured.strip()) < min_length:
            return MCPErrorBuilder.invalid_parameter(
                field="unstructured",
                expected=f"at least {min_length} characters of description",
                got=f"{len(unstructured.strip())} characters",
                hint="Provide a more detailed description of what the test covers",
                example_call={"tool": "create_test", "arguments": {"unstructured": "Comprehensive test of login functionality including validation, authentication, and error handling"}}
            )
        
        return None

    def _validate_test_environments(self, environments: List[str]) -> Optional[MCPErrorResponse]:
        """Validate test environment names.
        
        Args:
            environments: List of environment names
            
        Returns:
            MCPErrorResponse if validation fails, None if valid
        """
        if not environments:
            return None
            
        # Check for reasonable environment names
        invalid_envs = []
        for env in environments:
            if not env or not env.strip():
                invalid_envs.append("empty environment name")
            elif len(env.strip()) < 2:
                invalid_envs.append(f"'{env}' (too short)")
            elif not env.replace("-", "").replace("_", "").isalnum():
                invalid_envs.append(f"'{env}' (invalid characters)")
        
        if invalid_envs:
            return MCPErrorBuilder.invalid_parameter(
                field="test_environments",
                expected="valid environment names",
                got=f"invalid environments: {', '.join(invalid_envs)}",
                hint="Use alphanumeric names for environments (underscores and hyphens allowed)",
                example_call={"tool": "create_test_execution", "arguments": {"test_environments": ["staging", "production"]}}
            )
        
        return None

    def _get_test_type_example(self, test_type: TestType) -> Dict[str, Any]:
        """Get example call for specific test type.
        
        Args:
            test_type: The test type
            
        Returns:
            Example call dictionary
        """
        examples = {
            TestType.MANUAL: {
                "tool": "create_test",
                "arguments": {
                    "project_key": "PROJ",
                    "summary": "Test Login Functionality", 
                    "test_type": "Manual",
                    "steps": [
                        {"action": "Navigate to login page", "data": "/login", "result": "Login form displayed"},
                        {"action": "Enter credentials", "data": "valid username/password", "result": "User successfully logged in"}
                    ]
                }
            },
            TestType.CUCUMBER: {
                "tool": "create_test", 
                "arguments": {
                    "project_key": "PROJ",
                    "summary": "Login Feature Test",
                    "test_type": "Cucumber",
                    "gherkin": "Feature: User Login\n  Scenario: Valid login\n    Given I am on the login page\n    When I enter valid credentials\n    Then I should be logged in successfully"
                }
            },
            TestType.GENERIC: {
                "tool": "create_test",
                "arguments": {
                    "project_key": "PROJ", 
                    "summary": "API Authentication Test",
                    "test_type": "Generic",
                    "unstructured": "This test validates the API authentication flow, including token generation, validation, and expiration handling."
                }
            }
        }
        return examples.get(test_type, {})


# Convenience functions for common validations
def validate_test_creation_data(data: Dict[str, Any]) -> Optional[MCPErrorResponse]:
    """Validate test creation data with cross-field checks.
    
    Args:
        data: Test creation parameters
        
    Returns:
        MCPErrorResponse if validation fails, None if valid
    """
    validator = CrossFieldValidator()
    return validator.validate_test_creation(data)


def validate_test_execution_data(data: Dict[str, Any]) -> Optional[MCPErrorResponse]:
    """Validate test execution creation data.
    
    Args:
        data: Test execution parameters
        
    Returns:
        MCPErrorResponse if validation fails, None if valid
    """
    validator = CrossFieldValidator()
    return validator.validate_test_execution_creation(data)


def validate_bulk_operation_data(data: Dict[str, Any], operation_type: str) -> Optional[MCPErrorResponse]:
    """Validate bulk operation data.
    
    Args:
        data: Operation parameters
        operation_type: Type of bulk operation
        
    Returns:
        MCPErrorResponse if validation fails, None if valid
    """
    validator = CrossFieldValidator()
    return validator.validate_bulk_operations(data, operation_type)