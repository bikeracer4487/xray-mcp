import json
import asyncio
from typing import Optional, Dict
from datetime import datetime, timedelta
import aiohttp

from .config import config


class XrayAuth:
    """Authentication handler for Xray Cloud API using OAuth 2.0 client credentials flow."""
    
    def __init__(self, client_id: str, client_secret: str, base_url: Optional[str] = None):
        """Initialize XrayAuth with client credentials.
        
        Args:
            client_id: Xray API client ID
            client_secret: Xray API client secret  
            base_url: Base URL for Xray API (defaults to cloud instance)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url or "https://xray.cloud.getxray.app"
        self.token: Optional[str] = None
        self.token_created_at: Optional[datetime] = None
        self.token_expiry_minutes = 55  # Refresh 5 minutes before Xray's 1-hour expiry

        # Thread safety and retry management
        self._refresh_lock = asyncio.Lock()
        self._refresh_in_progress = False
        self._failed_attempts = 0
        self._last_failure_time: Optional[datetime] = None
    
    async def authenticate(self) -> str:
        """Authenticate with Xray API and return JWT token (thread-safe).

        Returns:
            JWT token string for API authentication

        Raises:
            Exception: If authentication fails
        """
        # Quick check without lock for valid token
        if self.token and self.is_token_valid():
            return self.token

        # Use lock for token refresh to prevent concurrent refresh attempts
        async with self._refresh_lock:
            # Double-check pattern: token might have been refreshed while waiting for lock
            if self.token and self.is_token_valid():
                return self.token

            # Check if we should apply exponential backoff
            if self._should_backoff():
                backoff_seconds = self._calculate_backoff()
                raise Exception(
                    f"Authentication temporarily disabled due to repeated failures. "
                    f"Retry after {backoff_seconds} seconds."
                )

            return await self._refresh_token()

    async def _refresh_token(self) -> str:
        """Internal method to refresh authentication token."""
        auth_url = f"{self.base_url}/api/v2/authenticate"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    auth_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        # Response is a JSON string containing the JWT token
                        token = await response.text()
                        # Remove quotes if response is quoted JSON string
                        self.token = token.strip('"')
                        self.token_created_at = datetime.now()

                        # Reset failure tracking on success
                        self._failed_attempts = 0
                        self._last_failure_time = None

                        return self.token
                    else:
                        error_text = await response.text()
                        self._record_failure()
                        raise Exception(f"Authentication failed: HTTP {response.status} - {error_text}")

        except aiohttp.ClientError as e:
            self._record_failure()
            raise Exception(f"Authentication failed: Network error - {str(e)}")
        except Exception as e:
            if "Authentication failed" not in str(e):
                self._record_failure()
                raise Exception(f"Authentication failed: {str(e)}")
            raise

    def _record_failure(self):
        """Record authentication failure for backoff calculation."""
        self._failed_attempts += 1
        self._last_failure_time = datetime.now()

    def _should_backoff(self) -> bool:
        """Check if we should apply exponential backoff."""
        if self._failed_attempts < config.retry.max_retries:
            return False

        if not self._last_failure_time:
            return False

        backoff_seconds = self._calculate_backoff()
        elapsed = (datetime.now() - self._last_failure_time).total_seconds()
        return elapsed < backoff_seconds

    def _calculate_backoff(self) -> float:
        """Calculate exponential backoff delay."""
        if self._failed_attempts <= config.retry.max_retries:
            return 0

        # Exponential backoff: base_delay * (multiplier ^ (attempts - max_retries))
        excess_attempts = self._failed_attempts - config.retry.max_retries
        delay = config.retry.base_delay * (config.retry.backoff_multiplier ** excess_attempts)
        return min(delay, config.retry.max_delay)

    def is_token_valid(self) -> bool:
        """Check if current token is still valid (hasn't expired).

        Returns:
            True if token is valid and hasn't expired, False otherwise
        """
        if not self.token or not self.token_created_at:
            return False

        # Check if token is older than our expiry threshold
        age = datetime.now() - self.token_created_at
        return age < timedelta(minutes=self.token_expiry_minutes)

    async def force_refresh(self) -> str:
        """Force authentication refresh even if token exists (thread-safe).

        Returns:
            New JWT token string

        Raises:
            Exception: If authentication fails
        """
        async with self._refresh_lock:
            # Clear existing token to force refresh
            self.token = None
            self.token_created_at = None
            return await self._refresh_token()

    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authentication token.

        Returns:
            Dictionary with Authorization and Content-Type headers

        Raises:
            ValueError: If no valid token is available
        """
        if not self.token or not self.is_token_valid():
            raise ValueError(
                "No valid authentication token available. "
                "Token may have expired. Call authenticate() first."
            )

        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }