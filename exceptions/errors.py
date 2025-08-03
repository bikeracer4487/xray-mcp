"""Custom exceptions for Xray MCP server.

This module defines a hierarchy of custom exceptions used throughout
the Xray MCP server. All exceptions inherit from XrayMCPError, allowing
for both specific and general exception handling.

The exception hierarchy provides clear error categorization:
- AuthenticationError: JWT token and credential issues
- GraphQLError: API communication and query errors
- ValidationError: Input validation and data format errors

These exceptions are used to provide structured error responses
in the MCP tools, ensuring consistent error handling across the server.
"""


class XrayMCPError(Exception):
    """Base exception for all Xray MCP server errors.
    
    This is the root exception class for the Xray MCP server.
    All custom exceptions inherit from this class, allowing
    catch-all error handling when needed.
    
    The exception hierarchy enables:
    - Specific error handling for different failure types
    - Consistent error response format in MCP tools
    - Clear error categorization for debugging
    
    Example:
        try:
            # Some Xray operation
            pass
        except XrayMCPError as e:
            # Catches any Xray-related error
            return {"error": str(e), "type": type(e).__name__}
    """
    pass


class AuthenticationError(XrayMCPError):
    """Raised when authentication with Xray API fails.
    
    This exception indicates issues with:
    - Invalid client credentials (client_id/client_secret)
    - Expired or invalid Xray license
    - Network issues during authentication
    - JWT token refresh failures
    
    Common causes:
    - Wrong credentials in environment variables
    - Xray license expiration
    - API endpoint unreachable
    - Clock skew between client and server
    
    Example:
        if response.status == 401:
            raise AuthenticationError(
                "Unauthorized: Invalid Xray license or credentials"
            )
    """
    pass


class GraphQLError(XrayMCPError):
    """Raised when GraphQL operations fail.
    
    This exception covers both GraphQL-level and HTTP-level
    errors during API communication:
    - GraphQL syntax errors
    - GraphQL validation errors
    - GraphQL execution errors
    - HTTP errors (4xx, 5xx)
    - Network connectivity issues
    
    The error message typically includes:
    - Specific GraphQL error messages
    - HTTP status codes and responses
    - Network error details
    
    Example:
        if "errors" in result:
            error_messages = [e["message"] for e in result["errors"]]
            raise GraphQLError(f"GraphQL errors: {'; '.join(error_messages)}")
    """
    pass


class ValidationError(XrayMCPError):
    """Raised when input validation fails.
    
    This exception indicates problems with:
    - Missing required parameters
    - Invalid parameter values
    - Incorrect data types
    - Business rule violations
    
    Used by tool classes to validate input before
    making API calls, preventing invalid requests.
    
    Example:
        if not project_key:
            raise ValidationError("Project key is required")
        
        if test_type not in ["Manual", "Cucumber", "Generic"]:
            raise ValidationError(f"Invalid test type: {test_type}")
    """
    pass


class ConnectionError(XrayMCPError):
    """Raised when network connection issues occur.
    
    This exception indicates network-level problems:
    - Connection timeouts
    - DNS resolution failures
    - Network unreachable
    - Connection refused
    
    Example:
        try:
            response = await session.post(url, ...)
        except aiohttp.ClientConnectionError as e:
            raise ConnectionError(f"Failed to connect to Xray API: {e}")
    """
    pass


class RateLimitError(XrayMCPError):
    """Raised when API rate limits are exceeded.
    
    This exception indicates:
    - API quota exhaustion
    - Too many requests in time window
    - Need for backoff/retry logic
    
    The error should include information about:
    - Rate limit threshold
    - Reset time if available
    - Retry-after duration
    
    Example:
        if response.status == 429:
            retry_after = response.headers.get('Retry-After', '60')
            raise RateLimitError(
                f"Rate limit exceeded. Retry after {retry_after} seconds"
            )
    """
    pass

