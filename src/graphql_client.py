import json
import asyncio
from typing import Optional, Dict, Any
import aiohttp
from src.auth import XrayAuth
from .circuit_breaker import get_circuit_breaker, CircuitBreakerOpenError
from .config import config


class XrayGraphQLClient:
    """GraphQL client for Xray Cloud API."""
    
    def __init__(self, auth: XrayAuth):
        """Initialize GraphQL client with authentication handler.

        Args:
            auth: Authenticated XrayAuth instance
        """
        self.auth = auth
        self.graphql_url = f"{auth.base_url}/api/v2/graphql"
        self.circuit_breaker = get_circuit_breaker("xray_graphql")
    
    async def execute(self, query: str, variables: Optional[Dict[str, Any]] = None, retry_count: int = 0) -> Dict[str, Any]:
        """Execute a GraphQL query through circuit breaker with comprehensive error handling.

        Args:
            query: GraphQL query or mutation string
            variables: Optional variables dictionary for the query
            retry_count: Internal retry counter to prevent infinite loops

        Returns:
            Dictionary containing the GraphQL response data

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            Exception: If the request fails or contains GraphQL errors
        """
        try:
            # Execute through circuit breaker for resilience
            return await self.circuit_breaker.call(
                self._execute_request, query, variables, retry_count
            )
        except CircuitBreakerOpenError:
            # Re-raise circuit breaker errors as-is
            raise
        except Exception as e:
            # Log error for monitoring (will be enhanced with logging module)
            raise

    async def _execute_request(self, query: str, variables: Optional[Dict[str, Any]], retry_count: int) -> Dict[str, Any]:
        """Internal method to execute GraphQL request with retries."""
        max_retries = config.retry.max_retries

        # Ensure we have a valid authentication token
        await self.auth.authenticate()

        try:
            headers = self.auth.get_headers()
        except ValueError as e:
            # Token expired or invalid, force refresh
            if retry_count < max_retries:
                await self.auth.force_refresh()
                return await self._execute_request(query, variables, retry_count + 1)
            raise Exception(f"Authentication failed after retries: {str(e)}")

        payload = {
            "query": query
        }

        if variables:
            payload["variables"] = variables

        try:
            timeout = aiohttp.ClientTimeout(total=config.security.max_request_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.graphql_url,
                    json=payload,
                    headers=headers
                ) as response:
                    # Handle different HTTP status codes
                    if response.status == 401:
                        # Unauthorized - token might be expired
                        if retry_count < max_retries:
                            await self.auth.force_refresh()
                            return await self._execute_request(query, variables, retry_count + 1)
                        error_text = await response.text()
                        raise Exception(f"Authentication failed after retries: HTTP 401 - {error_text}")

                    elif response.status == 403:
                        # Forbidden - likely permissions issue
                        error_text = await response.text()
                        raise Exception(f"Access forbidden: HTTP 403 - {error_text}")

                    elif response.status == 429:
                        # Too Many Requests - rate limited
                        retry_after = response.headers.get('Retry-After', '60')
                        if retry_count < max_retries:
                            try:
                                delay = min(int(retry_after), config.retry.max_delay)
                            except ValueError:
                                delay = config.retry.base_delay * (config.retry.backoff_multiplier ** retry_count)
                            await asyncio.sleep(delay)
                            return await self._execute_request(query, variables, retry_count + 1)
                        error_text = await response.text()
                        raise Exception(f"Rate limited: HTTP 429 - {error_text}")

                    elif response.status >= 500:
                        # Server errors - might be temporary, retry with backoff
                        if retry_count < max_retries:
                            delay = config.retry.base_delay * (config.retry.backoff_multiplier ** retry_count)
                            await asyncio.sleep(min(delay, config.retry.max_delay))
                            return await self._execute_request(query, variables, retry_count + 1)
                        error_text = await response.text()
                        raise Exception(f"Server error: HTTP {response.status} - {error_text}")

                    elif response.status != 200:
                        # Other client errors - don't retry
                        error_text = await response.text()
                        raise Exception(f"GraphQL request failed: HTTP {response.status} - {error_text}")

                    result = await response.json()

                    # Handle GraphQL errors
                    if "errors" in result:
                        errors = result["errors"]
                        if errors:
                            error_messages = [error.get("message", str(error)) for error in errors]

                            # Check if any errors are authentication-related
                            auth_keywords = ["authentication", "unauthorized", "token", "expired"]
                            if any(keyword in msg.lower() for msg in error_messages for keyword in auth_keywords):
                                if retry_count < max_retries:
                                    await self.auth.force_refresh()
                                    return await self._execute_request(query, variables, retry_count + 1)

                            raise Exception(f"GraphQL error: {'; '.join(error_messages)}")

                    # Return the data portion of the response
                    return result.get("data", {})

        except asyncio.TimeoutError:
            raise Exception(f"GraphQL request timed out after {config.security.max_request_timeout} seconds")
        except aiohttp.ClientError as e:
            raise Exception(f"GraphQL request failed: Network error - {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"GraphQL request failed: Invalid JSON response - {str(e)}")
        except Exception as e:
            # Re-raise known exceptions
            if any(phrase in str(e) for phrase in ["GraphQL", "HTTP", "Network", "Authentication", "Rate limited", "Server error", "Access forbidden"]):
                raise
            # Wrap unknown exceptions
            raise Exception(f"GraphQL request failed: {str(e)}")