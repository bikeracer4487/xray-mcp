"""MCP tool error handling decorator.

This module provides a decorator that wraps MCP tool methods to provide
standardized error handling and response formatting. It automatically
converts various exception types into structured MCP error responses.
"""

import functools
import asyncio
import json
from typing import Dict, Any, Callable, TypeVar, Union, Optional
import logging

# Centralized import handling
try:
    from ..utils.imports import import_from
    error_imports = import_from(".mcp_errors", "errors.mcp_errors", 
        "MCPErrorResponse", "MCPErrorBuilder", "MCPErrorName")
    exception_imports = import_from("..exceptions", "exceptions",
        "XrayMCPError", "AuthenticationError", "GraphQLError", "ValidationError", 
        "ConnectionError", "RateLimitError")
    
    MCPErrorResponse = error_imports['MCPErrorResponse']
    MCPErrorBuilder = error_imports['MCPErrorBuilder']
    MCPErrorName = error_imports['MCPErrorName']
    XrayMCPError = exception_imports['XrayMCPError']
    AuthenticationError = exception_imports['AuthenticationError']
    GraphQLError = exception_imports['GraphQLError']
    ValidationError = exception_imports['ValidationError']
    ConnectionError = exception_imports['ConnectionError']
    RateLimitError = exception_imports['RateLimitError']
except ImportError:
    # Fallback for direct execution
    try:
        from mcp_errors import MCPErrorResponse, MCPErrorBuilder, MCPErrorName
        from exceptions import (
            XrayMCPError,
            AuthenticationError,
            GraphQLError,
            ValidationError,
            ConnectionError,
            RateLimitError
        )
    except ImportError:
        # Handle direct execution from any directory
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from errors.mcp_errors import MCPErrorResponse, MCPErrorBuilder, MCPErrorName
        from exceptions import (
            XrayMCPError,
            AuthenticationError,
            GraphQLError,
            ValidationError,
            ConnectionError,
            RateLimitError
        )

logger = logging.getLogger(__name__)

T = TypeVar('T')


class MCPToolDecorator:
    """Decorator for standardized MCP tool error handling."""
    
    @staticmethod
    def handle_errors(
        tool_name: Optional[str] = None,
        docs_link: Optional[str] = None
    ) -> Callable:
        """Decorator that provides standardized error handling for MCP tools.
        
        This decorator automatically converts various exception types into
        structured MCP error responses that help AI callers understand and
        correct their requests.
        
        Args:
            tool_name: Name of the tool for error context
            docs_link: Link to tool documentation
            
        Returns:
            Decorated function that returns structured error responses
        """
        
        def decorator(func: Callable[..., T]) -> Callable[..., Union[T, Dict[str, Any]]]:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Union[T, Dict[str, Any]]:
                try:
                    # Execute the wrapped function
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
                except ValidationError as e:
                    return MCPToolDecorator._handle_validation_error(
                        e, tool_name, docs_link
                    ).to_dict()
                    
                except AuthenticationError as e:
                    return MCPToolDecorator._handle_authentication_error(
                        e, tool_name
                    ).to_dict()
                    
                except GraphQLError as e:
                    return MCPToolDecorator._handle_graphql_error(
                        e, tool_name, docs_link
                    ).to_dict()
                    
                except RateLimitError as e:
                    return MCPToolDecorator._handle_rate_limit_error(
                        e, tool_name
                    ).to_dict()
                    
                except ConnectionError as e:
                    return MCPToolDecorator._handle_connection_error(
                        e, tool_name
                    ).to_dict()
                    
                except TimeoutError as e:
                    return MCPToolDecorator._handle_timeout_error(
                        e, tool_name
                    ).to_dict()
                    
                except json.JSONDecodeError as e:
                    return MCPToolDecorator._handle_json_error(
                        e, tool_name, docs_link
                    ).to_dict()
                    
                except ValueError as e:
                    return MCPToolDecorator._handle_value_error(
                        e, tool_name, docs_link
                    ).to_dict()
                    
                except KeyError as e:
                    return MCPToolDecorator._handle_key_error(
                        e, tool_name, docs_link
                    ).to_dict()
                    
                except Exception as e:
                    # Log unexpected errors for debugging
                    logger.error(f"Unexpected error in {tool_name or func.__name__}: {str(e)}", exc_info=True)
                    return MCPErrorBuilder.internal_error(
                        context=f"Unexpected error in {tool_name or func.__name__}",
                        hint="Review the request parameters; if the error persists, file an issue."
                    ).to_dict()
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Union[T, Dict[str, Any]]:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Same error handling as async version
                    if isinstance(e, ValidationError):
                        return MCPToolDecorator._handle_validation_error(
                            e, tool_name, docs_link
                        ).to_dict()
                    # ... (same pattern for other exception types)
                    else:
                        logger.error(f"Unexpected error in {tool_name or func.__name__}: {str(e)}", exc_info=True)
                        return MCPErrorBuilder.internal_error(
                            context=f"Unexpected error in {tool_name or func.__name__}",
                            hint="Review the request parameters; if the error persists, file an issue."
                        ).to_dict()
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        
        return decorator
    
    @staticmethod
    def _handle_validation_error(
        error: ValidationError,
        tool_name: Optional[str],
        docs_link: Optional[str]
    ) -> MCPErrorResponse:
        """Handle validation errors with specific guidance."""
        error_msg = str(error).lower()
        
        # Parse common validation error patterns
        if "required" in error_msg and "missing" in error_msg:
            # Extract field name if possible
            field = MCPToolDecorator._extract_field_name(str(error))
            return MCPErrorBuilder.missing_required(
                field=field or "unknown",
                hint="All required parameters must be provided.",
                example_call=MCPToolDecorator._generate_example_call(tool_name)
            )
        elif "limit" in error_msg and "exceed" in error_msg:
            return MCPErrorBuilder.invalid_parameter(
                field="limit",
                expected="integer between 1 and 100",
                got="exceeded maximum",
                hint="Use limit=100 or less. For more results, implement pagination.",
                example_call=MCPToolDecorator._generate_example_call(tool_name, {"limit": 50})
            )
        elif "test type" in error_msg:
            return MCPErrorBuilder.invalid_parameter(
                field="test_type",
                expected="one of: Manual, Cucumber, Generic",
                got=MCPToolDecorator._extract_got_value(str(error)),
                hint="Use 'Manual' for step-by-step tests, 'Cucumber' for BDD, or 'Generic' for unstructured.",
                example_call=MCPToolDecorator._generate_example_call(tool_name, {"test_type": "Manual"})
            )
        elif "project key" in error_msg:
            return MCPErrorBuilder.invalid_parameter(
                field="project_key",
                expected="uppercase alphanumeric string",
                got=MCPToolDecorator._extract_got_value(str(error)),
                hint="Project key should be uppercase letters/numbers only (e.g., 'PROJ', 'TEST123').",
                example_call=MCPToolDecorator._generate_example_call(tool_name, {"project_key": "PROJ"})
            )
        else:
            # Generic validation error
            return MCPErrorResponse(
                name=MCPErrorName.INVALID_PARAMETER.value,
                message=str(error),
                hint="Check the parameter format and try again.",
                retriable=False,
                docs=docs_link,
                example_call=MCPToolDecorator._generate_example_call(tool_name)
            )
    
    @staticmethod
    def _handle_authentication_error(
        error: AuthenticationError,
        tool_name: Optional[str]
    ) -> MCPErrorResponse:
        """Handle authentication errors with specific guidance."""
        return MCPErrorBuilder.authentication_failed(
            hint="Verify XRAY_CLIENT_ID and XRAY_CLIENT_SECRET are correct and the Xray license is active."
        )
    
    @staticmethod
    def _handle_graphql_error(
        error: GraphQLError,
        tool_name: Optional[str],
        docs_link: Optional[str]
    ) -> MCPErrorResponse:
        """Handle GraphQL errors with specific guidance."""
        error_msg = str(error).lower()
        
        if "not found" in error_msg or "does not exist" in error_msg:
            # Extract identifier if possible
            identifier = MCPToolDecorator._extract_identifier(str(error))
            resource_type = "resource"
            
            if "test" in error_msg:
                resource_type = "test"
            elif "execution" in error_msg:
                resource_type = "test execution"
            elif "plan" in error_msg:
                resource_type = "test plan"
                
            return MCPErrorBuilder.not_found(
                resource=resource_type,
                identifier=identifier or "unknown",
                hint=f"Verify the {resource_type} ID or key exists and you have permission to access it.",
                example_call=MCPToolDecorator._generate_example_call(tool_name)
            )
        elif "unauthorized" in error_msg or "permission" in error_msg:
            return MCPErrorResponse(
                name=MCPErrorName.PERMISSION_DENIED.value,
                message="Permission denied for this operation.",
                hint="Verify you have the required permissions in Xray and the project.",
                retriable=False
            )
        else:
            # Generic GraphQL error
            return MCPErrorResponse(
                name=MCPErrorName.DEPENDENCY_UNAVAILABLE.value,
                message=f"Xray API error: {str(error)}",
                hint="Check the request parameters and try again. If the error persists, Xray API may be unavailable.",
                retriable=True,
                docs=docs_link
            )
    
    @staticmethod
    def _handle_rate_limit_error(
        error: RateLimitError,
        tool_name: Optional[str]
    ) -> MCPErrorResponse:
        """Handle rate limit errors with retry guidance."""
        # Try to extract retry-after from error message
        retry_after = None
        error_str = str(error)
        if "retry after" in error_str.lower():
            try:
                # Extract number from "retry after X seconds"
                import re
                match = re.search(r'retry after (\d+)', error_str.lower())
                if match:
                    retry_after = int(match.group(1))
            except:
                pass
        
        return MCPErrorBuilder.rate_limited(
            retry_after=retry_after,
            hint="Reduce request frequency, use smaller page sizes, or implement exponential backoff."
        )
    
    @staticmethod
    def _handle_connection_error(
        error: ConnectionError,
        tool_name: Optional[str]
    ) -> MCPErrorResponse:
        """Handle connection errors with retry guidance."""
        return MCPErrorBuilder.dependency_unavailable(
            service="Xray API",
            hint="Check your network connection and try again. The Xray service may be temporarily unavailable."
        )
    
    @staticmethod
    def _handle_timeout_error(
        error: TimeoutError,
        tool_name: Optional[str]
    ) -> MCPErrorResponse:
        """Handle timeout errors with optimization guidance."""
        return MCPErrorBuilder.timeout(
            operation=tool_name or "operation",
            hint="Try reducing the query scope, using smaller limits, or narrowing the date range."
        )
    
    @staticmethod
    def _handle_json_error(
        error: json.JSONDecodeError,
        tool_name: Optional[str],
        docs_link: Optional[str]
    ) -> MCPErrorResponse:
        """Handle JSON parsing errors with specific guidance."""
        return MCPErrorBuilder.invalid_parameter(
            field="JSON parameter",
            expected="valid JSON string",
            got=f"Invalid JSON at line {error.lineno}, column {error.colno}",
            hint=f"JSON syntax error: {error.msg}. Use proper JSON format with quoted strings.",
            example_call=MCPToolDecorator._generate_example_call(tool_name)
        )
    
    @staticmethod
    def _handle_value_error(
        error: ValueError,
        tool_name: Optional[str],
        docs_link: Optional[str]
    ) -> MCPErrorResponse:
        """Handle value errors with specific guidance."""
        return MCPErrorBuilder.invalid_parameter(
            field="parameter",
            expected="valid value",
            got=str(error),
            hint="Check the parameter format and allowed values.",
            example_call=MCPToolDecorator._generate_example_call(tool_name)
        )
    
    @staticmethod
    def _handle_key_error(
        error: KeyError,
        tool_name: Optional[str],
        docs_link: Optional[str]
    ) -> MCPErrorResponse:
        """Handle key errors (missing dictionary keys)."""
        missing_key = str(error).strip("'\"")
        return MCPErrorBuilder.missing_required(
            field=missing_key,
            hint=f"The '{missing_key}' field is required in the request.",
            example_call=MCPToolDecorator._generate_example_call(tool_name)
        )
    
    @staticmethod
    def _extract_field_name(error_message: str) -> Optional[str]:
        """Extract field name from error message."""
        import re
        # Look for patterns like "field 'fieldname'" or "'fieldname' is required"
        patterns = [
            r"field '([^']+)'",
            r"'([^']+)' is required",
            r"parameter '([^']+)'",
            r"`([^`]+)` is missing"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_message.lower())
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def _extract_got_value(error_message: str) -> Optional[str]:
        """Extract the received value from error message."""
        import re
        # Look for patterns like "got: value" or "received: value"
        patterns = [
            r"got:?\s*([^,\n]+)",
            r"received:?\s*([^,\n]+)",
            r"but was:?\s*([^,\n]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_message.lower())
            if match:
                return match.group(1).strip()
        
        return None
    
    @staticmethod
    def _extract_identifier(error_message: str) -> Optional[str]:
        """Extract identifier from error message."""
        import re
        # Look for patterns like "test 'TEST-123'" or "ID 12345"
        patterns = [
            r"'([^']+)'",
            r"id:?\s*([A-Z]+-\d+)",
            r"key:?\s*([A-Z]+-\d+)",
            r"\b(\d+)\b"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_message)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def _generate_example_call(
        tool_name: Optional[str],
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate an example call for the tool."""
        if not tool_name:
            return None
        
        # Basic examples for common tools
        examples = {
            "get_test": {"tool": "get_test", "arguments": {"issue_id": "TEST-123"}},
            "get_tests": {"tool": "get_tests", "arguments": {"jql": "project = PROJ", "limit": 50}},
            "create_test": {
                "tool": "create_test", 
                "arguments": {
                    "project_key": "PROJ", 
                    "summary": "Test login functionality",
                    "test_type": "Manual"
                }
            },
            "create_test_execution": {
                "tool": "create_test_execution",
                "arguments": {
                    "project_key": "PROJ",
                    "summary": "Sprint 1 Execution"
                }
            },
            "execute_jql_query": {
                "tool": "execute_jql_query",
                "arguments": {
                    "jql": "project = PROJ AND status = Open",
                    "entity_type": "test",
                    "limit": 50
                }
            }
        }
        
        example = examples.get(tool_name, {
            "tool": tool_name,
            "arguments": params or {}
        })
        
        # Override with provided params
        if params and "arguments" in example:
            example["arguments"].update(params)
        
        return example


# Convenience decorator function
def mcp_tool(tool_name: Optional[str] = None, docs_link: Optional[str] = None):
    """Convenience decorator for MCP tools.
    
    Usage:
        @mcp_tool("get_test", docs_link="TOOLSET.md#get_test")
        async def get_test(issue_id: str):
            # tool implementation
    """
    return MCPToolDecorator.handle_errors(tool_name, docs_link)