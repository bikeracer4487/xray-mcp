"""Tests for standardized error handling system.

This module tests the error handling implementation to ensure
consistent behavior across the application.
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, patch
import asyncio

# Handle imports
try:
    from errors import (
        ErrorCode, ErrorResponse, ErrorContext,
        error_handler, async_error_handler,
        standardize_error_response, get_error_code
    )
    from exceptions import (
        AuthenticationError, ValidationError, GraphQLError,
        ConnectionError, RateLimitError
    )
except ImportError:
    import sys
    sys.path.append('..')
    from errors import (
        ErrorCode, ErrorResponse, ErrorContext,
        error_handler, async_error_handler,
        standardize_error_response, get_error_code
    )
    from exceptions import (
        AuthenticationError, ValidationError, GraphQLError,
        ConnectionError, RateLimitError
    )


class TestErrorCode:
    """Test error code enumeration."""
    
    def test_error_codes_have_unique_values(self):
        """Test that all error codes have unique values."""
        values = [code.value for code in ErrorCode]
        assert len(values) == len(set(values))
        
    def test_error_code_format(self):
        """Test that error codes follow the expected format."""
        for code in ErrorCode:
            assert "_" in code.value
            prefix, number = code.value.split("_")
            assert prefix.isalpha() and prefix.isupper()
            assert number.isdigit() and len(number) == 3


class TestErrorContext:
    """Test error context functionality."""
    
    def test_context_initialization(self):
        """Test that context is properly initialized."""
        context = ErrorContext(
            operation="test_operation",
            tool="TestTool",
            user_id="user123",
            request_id="req456"
        )
        
        assert context.operation == "test_operation"
        assert context.tool == "TestTool"
        assert context.user_id == "user123"
        assert context.request_id == "req456"
        assert context.timestamp is not None
        
    def test_context_minimal(self):
        """Test context with minimal information."""
        context = ErrorContext(operation="test")
        
        assert context.operation == "test"
        assert context.tool is None
        assert context.user_id is None
        assert context.request_id is None


class TestErrorResponse:
    """Test error response functionality."""
    
    def test_error_response_basic(self):
        """Test basic error response creation."""
        error = ValueError("Test error")
        response = ErrorResponse(error, ErrorCode.INVALID_INPUT)
        
        result = response.to_dict()
        
        assert result["error"]["message"] == "Test error"
        assert result["error"]["type"] == "ValueError"
        assert result["error"]["code"] == "VAL_002"
        
    def test_error_response_with_context(self):
        """Test error response with context."""
        error = ValidationError("Missing field")
        context = ErrorContext(
            operation="create_test",
            tool="TestTools"
        )
        response = ErrorResponse(error, ErrorCode.VALIDATION_FAILED, context)
        
        result = response.to_dict()
        
        assert result["error"]["context"]["operation"] == "create_test"
        assert result["error"]["context"]["tool"] == "TestTools"
        assert "timestamp" in result["error"]["context"]
        
    def test_error_response_with_details(self):
        """Test error response with additional details."""
        error = GraphQLError("Query failed")
        details = {
            "query": "getTests",
            "variables": {"jql": "project = TEST"},
            "response_code": 400
        }
        response = ErrorResponse(
            error,
            ErrorCode.QUERY_FAILED,
            details=details
        )
        
        result = response.to_dict()
        
        assert result["error"]["details"]["query"] == "getTests"
        assert result["error"]["details"]["response_code"] == 400
        
    def test_error_response_with_trace(self):
        """Test error response with stack trace."""
        try:
            raise RuntimeError("Test error with trace")
        except RuntimeError as e:
            response = ErrorResponse(e, ErrorCode.INTERNAL_ERROR)
            result = response.to_dict(include_trace=True)
            
            assert "trace" in result["error"]
            assert "RuntimeError: Test error with trace" in result["error"]["trace"]


class TestGetErrorCode:
    """Test error code mapping."""
    
    def test_known_error_types(self):
        """Test mapping of known error types."""
        test_cases = [
            (AuthenticationError("auth"), ErrorCode.AUTH_FAILED),
            (ValidationError("val"), ErrorCode.VALIDATION_FAILED),
            (GraphQLError("gql"), ErrorCode.GRAPHQL_ERROR),
            (ConnectionError("conn"), ErrorCode.CONNECTION_FAILED),
            (RateLimitError("rate"), ErrorCode.RATE_LIMIT),
            (TimeoutError("timeout"), ErrorCode.TIMEOUT),
            (ValueError("value"), ErrorCode.INVALID_INPUT),
            (KeyError("key"), ErrorCode.MISSING_REQUIRED)
        ]
        
        for error, expected_code in test_cases:
            assert get_error_code(error) == expected_code
            
    def test_unknown_error_type(self):
        """Test mapping of unknown error types."""
        error = RuntimeError("Unknown error")
        assert get_error_code(error) == ErrorCode.UNKNOWN_ERROR


class TestStandardizeErrorResponse:
    """Test error standardization."""
    
    @patch('errors.handlers.logger')
    def test_standardize_basic_error(self, mock_logger):
        """Test standardizing a basic error."""
        error = ValueError("Invalid input")
        result = standardize_error_response(error)
        
        assert result["error"]["message"] == "Invalid input"
        assert result["error"]["type"] == "ValueError"
        assert result["error"]["code"] == "VAL_002"
        
        # Verify logging
        mock_logger.log.assert_called_once()
        
    @patch('errors.handlers.logger')
    def test_standardize_with_context(self, mock_logger):
        """Test standardizing error with context."""
        error = GraphQLError("Query failed")
        context = ErrorContext(
            operation="execute_query",
            tool="TestTools",
            request_id="req123"
        )
        
        result = standardize_error_response(error, context)
        
        assert result["error"]["context"]["operation"] == "execute_query"
        assert result["error"]["context"]["tool"] == "TestTools"
        assert result["error"]["context"]["request_id"] == "req123"
        
    @patch('errors.handlers.logger')
    def test_standardize_validation_error_logging(self, mock_logger):
        """Test that validation errors are logged as warnings."""
        error = ValidationError("Missing field")
        standardize_error_response(error)
        
        # Should log as WARNING, not ERROR
        from unittest.mock import ANY
        mock_logger.log.assert_called_with(
            ANY,  # logging.WARNING
            ANY
        )
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == 30  # logging.WARNING = 30


class TestErrorHandler:
    """Test error handler decorator."""
    
    def test_sync_error_handler_returns_error_dict(self):
        """Test sync error handler returning error dict."""
        @error_handler()
        def failing_function():
            raise ValueError("Test error")
            
        result = failing_function()
        
        assert isinstance(result, dict)
        assert result["error"]["message"] == "Test error"
        assert result["error"]["type"] == "ValueError"
        
    def test_sync_error_handler_raises_on_error(self):
        """Test sync error handler raising exceptions."""
        @error_handler(raise_on_error=True)
        def failing_function():
            raise ValueError("Test error")
            
        with pytest.raises(ValueError, match="Test error"):
            failing_function()
            
    def test_sync_error_handler_success(self):
        """Test sync error handler with successful execution."""
        @error_handler()
        def successful_function():
            return {"result": "success"}
            
        result = successful_function()
        
        assert result == {"result": "success"}
        
    def test_sync_error_handler_with_operation(self):
        """Test sync error handler with custom operation name."""
        @error_handler(operation="custom_operation")
        def failing_function():
            raise RuntimeError("Test error")
            
        result = failing_function()
        
        assert result["error"]["context"]["operation"] == "custom_operation"
        
    def test_sync_error_handler_with_class_method(self):
        """Test sync error handler with class methods."""
        class TestClass:
            @error_handler()
            def failing_method(self):
                raise ValueError("Method error")
                
        instance = TestClass()
        result = instance.failing_method()
        
        assert result["error"]["context"]["tool"] == "TestClass"


class TestAsyncErrorHandler:
    """Test async error handler decorator."""
    
    @pytest.mark.asyncio
    async def test_async_error_handler_returns_error_dict(self):
        """Test async error handler returning error dict."""
        @async_error_handler()
        async def failing_function():
            raise ValueError("Async test error")
            
        result = await failing_function()
        
        assert isinstance(result, dict)
        assert result["error"]["message"] == "Async test error"
        assert result["error"]["type"] == "ValueError"
        
    @pytest.mark.asyncio
    async def test_async_error_handler_raises_on_error(self):
        """Test async error handler raising exceptions."""
        @async_error_handler(raise_on_error=True)
        async def failing_function():
            raise ValueError("Async test error")
            
        with pytest.raises(ValueError, match="Async test error"):
            await failing_function()
            
    @pytest.mark.asyncio
    async def test_async_error_handler_success(self):
        """Test async error handler with successful execution."""
        @async_error_handler()
        async def successful_function():
            return {"result": "async success"}
            
        result = await successful_function()
        
        assert result == {"result": "async success"}
        
    @pytest.mark.asyncio
    async def test_async_error_handler_with_trace(self):
        """Test async error handler including stack trace."""
        @async_error_handler(include_trace=True)
        async def failing_function():
            raise RuntimeError("Trace test")
            
        result = await failing_function()
        
        assert "trace" in result["error"]
        assert "RuntimeError: Trace test" in result["error"]["trace"]


class TestIntegration:
    """Integration tests for error handling system."""
    
    def test_consistent_error_format(self):
        """Test that all error types produce consistent format."""
        error_types = [
            (AuthenticationError("auth"), "AUTH_001"),
            (ValidationError("val"), "VAL_001"),
            (GraphQLError("gql"), "GQL_001"),
            (ValueError("value"), "VAL_002"),
            (RuntimeError("runtime"), "UNK_001")
        ]
        
        for error, expected_code in error_types:
            @error_handler()
            def test_function():
                raise error
                
            result = test_function()
            
            # All should have the same structure
            assert "error" in result
            assert "message" in result["error"]
            assert "type" in result["error"]
            assert "code" in result["error"]
            assert result["error"]["code"] == expected_code
            assert "context" in result["error"]
            
    @pytest.mark.asyncio
    async def test_mixed_sync_async_consistency(self):
        """Test that sync and async handlers produce same format."""
        test_error = GraphQLError("Test consistency")
        
        @error_handler(operation="sync_test")
        def sync_function():
            raise test_error
            
        @async_error_handler(operation="async_test")
        async def async_function():
            raise test_error
            
        sync_result = sync_function()
        async_result = await async_function()
        
        # Both should have same error structure
        assert sync_result["error"]["message"] == async_result["error"]["message"]
        assert sync_result["error"]["type"] == async_result["error"]["type"]
        assert sync_result["error"]["code"] == async_result["error"]["code"]
        
        # Only operation name should differ
        assert sync_result["error"]["context"]["operation"] == "sync_test"
        assert async_result["error"]["context"]["operation"] == "async_test"