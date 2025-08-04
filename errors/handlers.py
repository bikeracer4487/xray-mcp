"""Standardized error handling implementation.

This module provides a consistent approach to error handling throughout
the application, eliminating inconsistencies between raising exceptions
and returning error dictionaries.
"""

from typing import Dict, Any, Optional, TypeVar, Callable, Union
from enum import Enum
import functools
import logging
import traceback
from datetime import datetime, timezone

# Handle imports for both package and direct execution
try:
    from ..exceptions import (
        AuthenticationError,
        ValidationError,
        GraphQLError,
        ConnectionError,
        RateLimitError,
    )
except ImportError:
    import sys

    sys.path.append("..")
    from exceptions import (
        AuthenticationError,
        ValidationError,
        GraphQLError,
        ConnectionError,
        RateLimitError,
    )

logger = logging.getLogger(__name__)

T = TypeVar("T")
P = TypeVar("P")


class ErrorCode(Enum):
    """Standardized error codes for consistent error identification."""

    # Authentication errors
    AUTH_FAILED = "AUTH_001"
    AUTH_EXPIRED = "AUTH_002"
    AUTH_INVALID = "AUTH_003"

    # Validation errors
    VALIDATION_FAILED = "VAL_001"
    INVALID_INPUT = "VAL_002"
    MISSING_REQUIRED = "VAL_003"

    # GraphQL errors
    GRAPHQL_ERROR = "GQL_001"
    QUERY_FAILED = "GQL_002"
    MUTATION_FAILED = "GQL_003"

    # Connection errors
    CONNECTION_FAILED = "CONN_001"
    TIMEOUT = "CONN_002"
    NETWORK_ERROR = "CONN_003"

    # Rate limiting
    RATE_LIMIT = "RATE_001"
    QUOTA_EXCEEDED = "RATE_002"

    # Generic errors
    INTERNAL_ERROR = "INT_001"
    UNKNOWN_ERROR = "UNK_001"


class ErrorContext:
    """Context information for error tracking and debugging."""

    def __init__(
        self,
        operation: str,
        tool: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        """Initialize error context.

        Args:
            operation: The operation being performed
            tool: Optional tool name
            user_id: Optional user identifier
            request_id: Optional request identifier
        """
        self.operation = operation
        self.tool = tool
        self.user_id = user_id
        self.request_id = request_id
        self.timestamp = datetime.now(timezone.utc).isoformat()


class ErrorResponse:
    """Standardized error response structure."""

    def __init__(
        self,
        error: Exception,
        code: ErrorCode,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize error response.

        Args:
            error: The exception that occurred
            code: Error code for categorization
            context: Optional context information
            details: Optional additional details
        """
        self.error = error
        self.code = code
        self.context = context
        self.details = details or {}

    def to_dict(self, include_trace: bool = False) -> Dict[str, Any]:
        """Convert to dictionary format.

        Args:
            include_trace: Whether to include stack trace

        Returns:
            Dictionary representation of the error
        """
        response = {
            "error": {
                "message": str(self.error),
                "type": type(self.error).__name__,
                "code": self.code.value,
            }
        }

        if self.context:
            response["error"]["context"] = {
                "operation": self.context.operation,
                "timestamp": self.context.timestamp,
            }
            if self.context.tool:
                response["error"]["context"]["tool"] = self.context.tool
            if self.context.request_id:
                response["error"]["context"]["request_id"] = self.context.request_id

        if self.details:
            response["error"]["details"] = self.details

        if include_trace:
            response["error"]["trace"] = traceback.format_exc()

        return response


def get_error_code(error: Exception) -> ErrorCode:
    """Map exception types to error codes.

    Args:
        error: The exception to map

    Returns:
        Appropriate error code
    """
    error_mapping = {
        AuthenticationError: ErrorCode.AUTH_FAILED,
        ValidationError: ErrorCode.VALIDATION_FAILED,
        GraphQLError: ErrorCode.GRAPHQL_ERROR,
        ConnectionError: ErrorCode.CONNECTION_FAILED,
        RateLimitError: ErrorCode.RATE_LIMIT,
        TimeoutError: ErrorCode.TIMEOUT,
        ValueError: ErrorCode.INVALID_INPUT,
        KeyError: ErrorCode.MISSING_REQUIRED,
    }

    for error_type, code in error_mapping.items():
        if isinstance(error, error_type):
            return code

    return ErrorCode.UNKNOWN_ERROR


def standardize_error_response(
    error: Exception,
    context: Optional[ErrorContext] = None,
    include_trace: bool = False,
) -> Dict[str, Any]:
    """Convert any exception to standardized error response.

    Args:
        error: The exception to standardize
        context: Optional error context
        include_trace: Whether to include stack trace

    Returns:
        Standardized error dictionary
    """
    code = get_error_code(error)
    error_response = ErrorResponse(error, code, context)

    # Log the error
    log_level = (
        logging.ERROR if code != ErrorCode.VALIDATION_FAILED else logging.WARNING
    )
    logger.log(
        log_level,
        f"Error in {context.operation if context else 'unknown operation'}: "
        f"{type(error).__name__}: {str(error)}",
    )

    return error_response.to_dict(include_trace)


def error_handler(
    operation: Optional[str] = None,
    raise_on_error: bool = False,
    include_trace: bool = False,
) -> Callable:
    """Decorator for standardized error handling.

    This decorator ensures consistent error handling across all functions.
    It can either raise exceptions or return error dictionaries based on
    configuration.

    Args:
        operation: Optional operation name for context
        raise_on_error: Whether to raise exceptions or return error dicts
        include_trace: Whether to include stack traces in responses

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, Dict[str, Any]]]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Union[T, Dict[str, Any]]:
            context = ErrorContext(
                operation=operation or func.__name__,
                tool=(
                    args[0].__class__.__name__
                    if args and hasattr(args[0], "__class__")
                    else None
                ),
            )

            try:
                return func(*args, **kwargs)
            except Exception as e:
                if raise_on_error:
                    raise

                return standardize_error_response(e, context, include_trace)

        return wrapper

    return decorator


def async_error_handler(
    operation: Optional[str] = None,
    raise_on_error: bool = False,
    include_trace: bool = False,
) -> Callable:
    """Async version of error_handler decorator.

    Args:
        operation: Optional operation name for context
        raise_on_error: Whether to raise exceptions or return error dicts
        include_trace: Whether to include stack traces in responses

    Returns:
        Decorated async function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, Dict[str, Any]]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Union[T, Dict[str, Any]]:
            context = ErrorContext(
                operation=operation or func.__name__,
                tool=(
                    args[0].__class__.__name__
                    if args and hasattr(args[0], "__class__")
                    else None
                ),
            )

            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if raise_on_error:
                    raise

                return standardize_error_response(e, context, include_trace)

        return wrapper

    return decorator
