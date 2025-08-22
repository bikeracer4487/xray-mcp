"""MCP-specific error handling for Xray tools.

This module provides a standardized error contract specifically designed for
MCP tool interactions, with AI-friendly error messages and self-correction hints.

The error format follows a consistent structure that helps AI callers understand
what went wrong and how to fix their requests automatically.
"""

from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, asdict
from enum import Enum
import json


class MCPErrorName(Enum):
    """Standardized error names for consistent identification."""
    
    # Parameter validation errors
    INVALID_PARAMETER = "InvalidParameter"
    MISSING_REQUIRED = "MissingRequired" 
    UNSUPPORTED_COMBINATION = "UnsupportedCombination"
    
    # Resource errors
    NOT_FOUND = "NotFound"
    CONFLICT = "Conflict"
    PRECONDITION_FAILED = "PreconditionFailed"
    
    # Permission and authentication
    PERMISSION_DENIED = "PermissionDenied"
    AUTHENTICATION_FAILED = "AuthenticationFailed"
    
    # Rate limiting and quotas
    RATE_LIMITED = "RateLimited"
    QUOTA_EXCEEDED = "QuotaExceeded"
    
    # External dependencies
    DEPENDENCY_UNAVAILABLE = "DependencyUnavailable"
    TIMEOUT = "Timeout"
    
    # Internal errors
    INTERNAL_ERROR = "InternalError"


@dataclass
class MCPErrorResponse:
    """Standardized MCP error response with self-correction guidance.
    
    This class provides a consistent error format that helps AI callers
    understand failures and correct their requests automatically.
    
    Attributes:
        name: Stable error identifier (e.g., "InvalidParameter")
        message: Human-friendly single-sentence diagnosis
        hint: Specific advice on how to fix the issue with example
        field: Parameter name for validation errors
        expected: Expected type/format for the field
        got: Actual value received (sanitized)
        retriable: Whether retrying the operation makes sense
        docs: Documentation reference for more help
        example_call: Valid tool call structure for self-correction
    """
    
    name: str
    message: str
    hint: Optional[str] = None
    field: Optional[str] = None
    expected: Optional[str] = None
    got: Optional[str] = None
    retriable: bool = False
    docs: Optional[str] = None
    example_call: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error response to dictionary format.
        
        Returns:
            Dictionary representation suitable for MCP responses
        """
        error_dict = {
            "error": self.name,
            "message": self.message
        }
        
        # Add optional fields if present
        if self.hint:
            error_dict["hint"] = self.hint
        if self.field:
            error_dict["field"] = self.field
        if self.expected:
            error_dict["expected"] = self.expected
        if self.got:
            error_dict["got"] = self.got
        if self.docs:
            error_dict["docs"] = self.docs
        if self.example_call:
            error_dict["example_call"] = self.example_call
            
        error_dict["retriable"] = self.retriable
        
        return error_dict


class MCPErrorBuilder:
    """Builder class for creating standardized MCP error responses."""
    
    @staticmethod
    def invalid_parameter(
        field: str,
        expected: str,
        got: Optional[str] = None,
        hint: Optional[str] = None,
        example_call: Optional[Dict[str, Any]] = None
    ) -> MCPErrorResponse:
        """Create an InvalidParameter error response.
        
        Args:
            field: Name of the invalid parameter
            expected: Description of expected format/value
            got: Actual value received (will be sanitized)
            hint: Specific correction advice
            example_call: Valid call example
            
        Returns:
            MCPErrorResponse for invalid parameter
        """
        # Sanitize the 'got' value to prevent information leakage
        got_str = None
        if got is not None:
            if isinstance(got, str) and len(got) > 100:
                got_str = f"{got[:97]}..."
            else:
                got_str = str(got)
                
        message = f"Parameter '{field}' must be {expected}."
        if got_str:
            message += f" Got: {got_str}"
            
        return MCPErrorResponse(
            name=MCPErrorName.INVALID_PARAMETER.value,
            message=message,
            hint=hint,
            field=field,
            expected=expected,
            got=got_str,
            retriable=False,
            example_call=example_call
        )
    
    @staticmethod
    def missing_required(
        field: str,
        hint: Optional[str] = None,
        example_call: Optional[Dict[str, Any]] = None
    ) -> MCPErrorResponse:
        """Create a MissingRequired error response.
        
        Args:
            field: Name of the missing parameter
            hint: Specific guidance on providing the parameter
            example_call: Valid call example
            
        Returns:
            MCPErrorResponse for missing required parameter
        """
        return MCPErrorResponse(
            name=MCPErrorName.MISSING_REQUIRED.value,
            message=f"Required parameter '{field}' is missing.",
            hint=hint,
            field=field,
            retriable=False,
            example_call=example_call
        )
    
    @staticmethod
    def not_found(
        resource: str,
        identifier: str,
        hint: Optional[str] = None,
        example_call: Optional[Dict[str, Any]] = None
    ) -> MCPErrorResponse:
        """Create a NotFound error response.
        
        Args:
            resource: Type of resource (test, execution, etc.)
            identifier: The identifier that wasn't found
            hint: Guidance on finding the correct identifier
            example_call: Valid call example
            
        Returns:
            MCPErrorResponse for not found resource
        """
        return MCPErrorResponse(
            name=MCPErrorName.NOT_FOUND.value,
            message=f"{resource.title()} '{identifier}' not found.",
            hint=hint or f"Verify the {resource} ID or key exists and you have permission to access it.",
            field="issue_id" if "test" in resource.lower() or "execution" in resource.lower() else None,
            retriable=False,
            example_call=example_call
        )
    
    @staticmethod
    def unsupported_combination(
        message: str,
        hint: str,
        example_call: Optional[Dict[str, Any]] = None
    ) -> MCPErrorResponse:
        """Create an UnsupportedCombination error response.
        
        Args:
            message: Description of the unsupported combination
            hint: How to fix the parameter combination
            example_call: Valid call example
            
        Returns:
            MCPErrorResponse for unsupported parameter combination
        """
        return MCPErrorResponse(
            name=MCPErrorName.UNSUPPORTED_COMBINATION.value,
            message=message,
            hint=hint,
            retriable=False,
            example_call=example_call
        )
    
    @staticmethod
    def rate_limited(
        retry_after: Optional[int] = None,
        hint: Optional[str] = None
    ) -> MCPErrorResponse:
        """Create a RateLimited error response.
        
        Args:
            retry_after: Seconds to wait before retrying
            hint: Guidance on avoiding rate limits
            
        Returns:
            MCPErrorResponse for rate limiting
        """
        message = "API rate limit exceeded."
        if retry_after:
            message += f" Retry after {retry_after} seconds."
            
        return MCPErrorResponse(
            name=MCPErrorName.RATE_LIMITED.value,
            message=message,
            hint=hint or "Reduce request frequency or use smaller page sizes.",
            retriable=True
        )
    
    @staticmethod
    def timeout(
        operation: str,
        hint: Optional[str] = None
    ) -> MCPErrorResponse:
        """Create a Timeout error response.
        
        Args:
            operation: The operation that timed out
            hint: Guidance on avoiding timeouts
            
        Returns:
            MCPErrorResponse for timeout
        """
        return MCPErrorResponse(
            name=MCPErrorName.TIMEOUT.value,
            message=f"Operation '{operation}' exceeded timeout limit.",
            hint=hint or "Try narrowing the query scope or reducing the result limit.",
            retriable=True
        )
    
    @staticmethod
    def authentication_failed(
        hint: Optional[str] = None
    ) -> MCPErrorResponse:
        """Create an AuthenticationFailed error response.
        
        Args:
            hint: Guidance on authentication issues
            
        Returns:
            MCPErrorResponse for authentication failure
        """
        return MCPErrorResponse(
            name=MCPErrorName.AUTHENTICATION_FAILED.value,
            message="Authentication with Xray API failed.",
            hint=hint or "Verify XRAY_CLIENT_ID and XRAY_CLIENT_SECRET are correct and the license is active.",
            retriable=False
        )
    
    @staticmethod
    def dependency_unavailable(
        service: str,
        hint: Optional[str] = None
    ) -> MCPErrorResponse:
        """Create a DependencyUnavailable error response.
        
        Args:
            service: Name of the unavailable service
            hint: Guidance on handling the outage
            
        Returns:
            MCPErrorResponse for dependency unavailability
        """
        return MCPErrorResponse(
            name=MCPErrorName.DEPENDENCY_UNAVAILABLE.value,
            message=f"{service} service is currently unavailable.",
            hint=hint or "Wait a few minutes and try again, or check service status.",
            retriable=True
        )
    
    @staticmethod
    def internal_error(
        context: Optional[str] = None,
        hint: Optional[str] = None
    ) -> MCPErrorResponse:
        """Create an InternalError error response.
        
        Args:
            context: Additional context about the error
            hint: Guidance on resolving the issue
            
        Returns:
            MCPErrorResponse for internal errors
        """
        message = "An internal error occurred."
        if context:
            message += f" Context: {context}"
            
        return MCPErrorResponse(
            name=MCPErrorName.INTERNAL_ERROR.value,
            message=message,
            hint=hint or "Review the request parameters; if the error persists, file an issue.",
            retriable=False
        )


class MCPValidationHelper:
    """Helper class for common validation patterns in MCP tools."""
    
    @staticmethod
    def validate_project_key(project_key: str) -> Optional[MCPErrorResponse]:
        """Validate a Jira project key format.
        
        Args:
            project_key: The project key to validate
            
        Returns:
            MCPErrorResponse if invalid, None if valid
        """
        if not project_key:
            return MCPErrorBuilder.missing_required(
                field="project_key",
                hint="Project key is required to identify the Jira project (e.g., 'PROJ', 'TEST').",
                example_call={"tool": "create_test", "arguments": {"project_key": "PROJ", "summary": "Test title"}}
            )
        
        if not isinstance(project_key, str):
            return MCPErrorBuilder.invalid_parameter(
                field="project_key",
                expected="string",
                got=str(type(project_key).__name__),
                hint="Project key must be a string like 'PROJ' or 'TEST'.",
                example_call={"tool": "create_test", "arguments": {"project_key": "PROJ", "summary": "Test title"}}
            )
        
        # Basic format validation
        if not project_key.isupper() or not project_key.isalnum():
            return MCPErrorBuilder.invalid_parameter(
                field="project_key",
                expected="uppercase alphanumeric string",
                got=project_key,
                hint="Project key should be uppercase letters/numbers only (e.g., 'PROJ', 'TEST123').",
                example_call={"tool": "create_test", "arguments": {"project_key": "PROJ", "summary": "Test title"}}
            )
        
        return None
    
    @staticmethod
    def validate_limit(limit: int, max_limit: int = 100) -> Optional[MCPErrorResponse]:
        """Validate a query limit parameter.
        
        Args:
            limit: The limit value to validate
            max_limit: Maximum allowed limit
            
        Returns:
            MCPErrorResponse if invalid, None if valid
        """
        if not isinstance(limit, int):
            return MCPErrorBuilder.invalid_parameter(
                field="limit",
                expected="integer",
                got=str(type(limit).__name__),
                hint=f"Limit must be an integer between 1 and {max_limit}."
            )
        
        if limit < 1:
            return MCPErrorBuilder.invalid_parameter(
                field="limit",
                expected=f"integer between 1 and {max_limit}",
                got=str(limit),
                hint="Limit must be at least 1 to return any results."
            )
        
        if limit > max_limit:
            return MCPErrorBuilder.invalid_parameter(
                field="limit",
                expected=f"integer between 1 and {max_limit}",
                got=str(limit),
                hint=f"Limit cannot exceed {max_limit} due to API restrictions. Use pagination for more results."
            )
        
        return None
    
    @staticmethod
    def validate_test_type(test_type: str) -> Optional[MCPErrorResponse]:
        """Validate a test type parameter.
        
        Args:
            test_type: The test type to validate
            
        Returns:
            MCPErrorResponse if invalid, None if valid
        """
        valid_types = ["Manual", "Cucumber", "Generic"]
        
        if not isinstance(test_type, str):
            return MCPErrorBuilder.invalid_parameter(
                field="test_type",
                expected="string",
                got=str(type(test_type).__name__),
                hint=f"Test type must be one of: {', '.join(valid_types)}.",
                example_call={"tool": "create_test", "arguments": {"test_type": "Manual"}}
            )
        
        if test_type not in valid_types:
            return MCPErrorBuilder.invalid_parameter(
                field="test_type",
                expected=f"one of: {', '.join(valid_types)}",
                got=test_type,
                hint="Use 'Manual' for step-by-step tests, 'Cucumber' for BDD, or 'Generic' for unstructured.",
                example_call={"tool": "create_test", "arguments": {"test_type": "Manual"}}
            )
        
        return None
    
    @staticmethod
    def validate_json_string(json_str: str, field_name: str) -> Optional[MCPErrorResponse]:
        """Validate that a string contains valid JSON.
        
        Args:
            json_str: The JSON string to validate
            field_name: Name of the field for error reporting
            
        Returns:
            MCPErrorResponse if invalid, None if valid
        """
        try:
            json.loads(json_str)
            return None
        except json.JSONDecodeError as e:
            return MCPErrorBuilder.invalid_parameter(
                field=field_name,
                expected="valid JSON string",
                got=json_str[:50] + "..." if len(json_str) > 50 else json_str,
                hint=f"JSON syntax error: {str(e)}. Use proper JSON format with quoted strings.",
                example_call={"tool": "create_test", "arguments": {field_name: '[{"action": "Click", "result": "Success"}]'}}
            )