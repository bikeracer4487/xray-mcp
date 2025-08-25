"""Authentication manager for Xray API.

This module handles JWT token-based authentication with Jira Xray's API.
It manages token lifecycle including initial authentication, expiry tracking,
and automatic refresh when needed.

The authentication flow follows Xray's API v2 authentication endpoint,
which exchanges client credentials for a JWT token that must be included
in subsequent API requests.
"""

import json
import jwt
import aiohttp
import asyncio
from datetime import datetime, timezone
from typing import Optional

# Centralized import handling
try:
    from ..utils.imports import import_from
    imports = import_from("..exceptions", "exceptions", "AuthenticationError")
    pool_imports = import_from("..utils.connection_pool", "utils.connection_pool", "get_connection_pool")
    AuthenticationError = imports['AuthenticationError']
    get_connection_pool = pool_imports['get_connection_pool']
except ImportError:
    # Fallback for direct execution
    from exceptions import AuthenticationError
    from utils.connection_pool import get_connection_pool


class XrayAuthManager:
    """Manages JWT authentication with Xray API.

    This class handles the complete authentication lifecycle for Xray API access:
    - Initial authentication using client credentials
    - JWT token storage and expiry tracking
    - Automatic token refresh when expired or near expiry
    - Error handling for various authentication failure scenarios

    The manager uses a 5-minute expiry buffer to ensure tokens are refreshed
    before they expire, preventing authentication failures during API calls.

    Attributes:
        client_id (str): Xray API client ID from Xray global settings
        client_secret (str): Xray API client secret
        base_url (str): Base URL for Xray instance (cloud or server)
        token (Optional[str]): Current JWT token, None if not authenticated
        token_expiry (Optional[datetime]): Token expiration time in UTC

    Example:
        auth_manager = XrayAuthManager("client_id", "client_secret")
        token = await auth_manager.authenticate()
        # Token is automatically refreshed when needed
        valid_token = await auth_manager.get_valid_token()
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = "https://xray.cloud.getxray.app",
    ):
        """Initialize the authentication manager.

        Args:
            client_id (str): Xray API client ID obtained from Xray Global Settings
            client_secret (str): Xray API client secret
            base_url (str, optional): Base URL for Xray instance.
                Defaults to "https://xray.cloud.getxray.app" for cloud instances.
                For server instances, use your Jira server URL.

        Note:
            The manager starts in an unauthenticated state. Call authenticate()
            or get_valid_token() to obtain a JWT token.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self._token_lock = (
            asyncio.Lock()
        )  # Prevents race conditions during token refresh
        self._pool_manager = None

    async def _get_pool_manager(self):
        """Get connection pool manager, initializing if needed."""
        if self._pool_manager is None:
            self._pool_manager = await get_connection_pool()
        return self._pool_manager

    async def authenticate(self) -> str:
        """Authenticate with Xray API and obtain a JWT token.

        Exchanges client credentials for a JWT token by calling Xray's
        authentication endpoint. The token is stored internally along with
        its expiration time extracted from the JWT claims.

        Returns:
            str: JWT token for use in API requests

        Raises:
            AuthenticationError: If authentication fails due to:
                - Invalid credentials (401)
                - Invalid request format (400)
                - Server errors (500)
                - Network connectivity issues

        Complexity: O(1) - Single HTTP request

        Call Flow:
            1. POST credentials to /api/v2/authenticate
            2. Parse JWT token from response
            3. Decode token to extract expiry time
            4. Store token and expiry for future use

        Note:
            The token is returned as a quoted JSON string by Xray API,
            so quotes are stripped before storage.
        """
        auth_url = f"{self.base_url}/api/v2/authenticate"

        payload = {"client_id": self.client_id, "client_secret": self.client_secret}

        try:
            # Use connection pool for improved performance
            pool_manager = await self._get_pool_manager()
            async with pool_manager.session_context() as session:
                async with session.post(
                    auth_url, json=payload, headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        # Xray returns the token as a JSON string with quotes
                        token_response = await response.text()
                        # Strip the surrounding quotes from the token
                        self.token = token_response.strip('"')

                        # Extract expiry time from JWT claims without verifying signature
                        # We don't have the signing key, so verification is not possible
                        try:
                            decoded = jwt.decode(
                                self.token, options={"verify_signature": False}
                            )
                            if "exp" in decoded:
                                self.token_expiry = datetime.fromtimestamp(
                                    decoded["exp"], tz=timezone.utc
                                )
                        except jwt.InvalidTokenError:
                            # Fallback: If token decode fails, assume 1-hour validity
                            # This is a conservative estimate for Xray tokens
                            from datetime import timedelta

                            self.token_expiry = datetime.now(timezone.utc) + timedelta(
                                hours=1
                            )

                        return self.token
                    # Handle specific error responses with meaningful messages
                    elif response.status == 400:
                        raise AuthenticationError("Bad request: Wrong request syntax")
                    elif response.status == 401:
                        raise AuthenticationError(
                            "Unauthorized: Invalid Xray license or credentials"
                        )
                    elif response.status == 500:
                        raise AuthenticationError(
                            "Internal server error during authentication"
                        )
                    else:
                        # Catch-all for unexpected status codes
                        error_text = await response.text()
                        raise AuthenticationError(
                            f"Authentication failed with status {response.status}: {error_text}"
                        )

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            # Network-level errors (connection refused, timeout, DNS failure)
            raise AuthenticationError(f"Network error during authentication: {str(e)}")

    async def get_valid_token(self) -> str:
        """Get a valid token, refreshing if necessary.

        This is the primary method for obtaining tokens in the application.
        It checks if a token exists and is still valid, automatically
        refreshing it if needed. This ensures API calls always have a
        valid token without manual token management.

        The method uses an async lock to prevent race conditions where
        multiple concurrent calls could trigger multiple authentication
        requests, which could lead to rate limiting or unnecessary API calls.

        Returns:
            str: Valid JWT token ready for API use

        Raises:
            AuthenticationError: If token refresh fails

        Complexity: O(1) - Returns cached token or single auth request

        Call Flow:
            1. Acquire async lock to prevent concurrent auth attempts
            2. Check if token exists and is not expired
            3. If invalid/expired, call authenticate()
            4. Return the valid token

        Example:
            # Always use this method instead of accessing token directly
            token = await auth_manager.get_valid_token()
            headers = {"Authorization": f"Bearer {token}"}
        """
        async with self._token_lock:
            if self.token is None or self._is_token_expired():
                await self.authenticate()

            return self.token

    def _is_token_expired(self) -> bool:
        """Check if the current token is expired or near expiry.

        Implements a proactive expiry check with a 5-minute buffer to
        prevent using tokens that might expire during an API call. This
        reduces the chance of authentication failures mid-operation.

        Returns:
            bool: True if token is expired or will expire within 5 minutes,
                  False if token is valid for at least 5 more minutes

        Complexity: O(1) - Simple datetime comparison

        Note:
            The 5-minute buffer is a conservative approach to handle:
            - Clock skew between client and server
            - Long-running API operations
            - Network latency
        """
        if self.token_expiry is None:
            return True

        # Check if token expires within the next 5 minutes
        # This buffer prevents auth failures during long operations
        from datetime import timedelta

        buffer_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        return self.token_expiry <= buffer_time
