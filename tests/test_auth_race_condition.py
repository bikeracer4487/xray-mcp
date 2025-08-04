"""Tests for authentication race condition prevention.

This module tests that the authentication manager properly handles
concurrent calls to get_valid_token() without triggering multiple
authentication requests.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta

try:
    import jwt
except ImportError:
    # PyJWT might be installed as 'PyJWT' package
    from jose import jwt

from auth.manager import XrayAuthManager
from exceptions import AuthenticationError


class TestAuthRaceCondition:
    """Test suite for authentication race condition prevention."""

    @pytest.fixture
    def auth_manager(self):
        """Create an auth manager instance for testing."""
        return XrayAuthManager("test_client_id", "test_client_secret")

    @pytest.fixture
    def mock_token_data(self):
        """Create mock JWT token data."""
        # Create a token that expires in 1 hour
        expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = {
            "exp": int(expiry.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
        }
        # Create a dummy token (not cryptographically valid, but structurally correct)
        token = jwt.encode(payload, "dummy_secret", algorithm="HS256")
        return token, expiry

    @pytest.mark.asyncio
    async def test_concurrent_token_requests_single_auth(
        self, auth_manager, mock_token_data
    ):
        """Test that concurrent get_valid_token calls only trigger one authentication."""
        token, _ = mock_token_data
        auth_call_count = 0

        # Mock the authenticate method to track calls
        async def mock_authenticate():
            nonlocal auth_call_count
            auth_call_count += 1
            # Simulate network delay
            await asyncio.sleep(0.1)
            auth_manager.token = token
            auth_manager.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
            return token

        auth_manager.authenticate = mock_authenticate

        # Make 10 concurrent calls to get_valid_token
        tasks = [auth_manager.get_valid_token() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All calls should return the same token
        assert all(result == token for result in results)
        # Only one authentication call should have been made
        assert auth_call_count == 1

    @pytest.mark.asyncio
    async def test_sequential_calls_use_cached_token(
        self, auth_manager, mock_token_data
    ):
        """Test that sequential calls use cached token when valid."""
        token, expiry = mock_token_data
        auth_call_count = 0

        async def mock_authenticate():
            nonlocal auth_call_count
            auth_call_count += 1
            auth_manager.token = token
            auth_manager.token_expiry = expiry
            return token

        auth_manager.authenticate = mock_authenticate

        # First call should authenticate
        result1 = await auth_manager.get_valid_token()
        assert result1 == token
        assert auth_call_count == 1

        # Subsequent calls should use cached token
        for _ in range(5):
            result = await auth_manager.get_valid_token()
            assert result == token

        # Still only one authentication call
        assert auth_call_count == 1

    @pytest.mark.asyncio
    async def test_expired_token_triggers_new_auth(self, auth_manager):
        """Test that expired token triggers new authentication."""
        # Create an expired token
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_payload = {
            "exp": int(expired_time.timestamp()),
            "iat": int((expired_time - timedelta(hours=1)).timestamp()),
        }
        expired_token = jwt.encode(expired_payload, "dummy_secret", algorithm="HS256")

        # Create a new valid token
        valid_time = datetime.now(timezone.utc) + timedelta(hours=1)
        valid_payload = {
            "exp": int(valid_time.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
        }
        valid_token = jwt.encode(valid_payload, "dummy_secret", algorithm="HS256")

        auth_call_count = 0

        async def mock_authenticate():
            nonlocal auth_call_count
            auth_call_count += 1
            if auth_call_count == 1:
                # First auth returns expired token
                auth_manager.token = expired_token
                auth_manager.token_expiry = expired_time
                return expired_token
            else:
                # Second auth returns valid token
                auth_manager.token = valid_token
                auth_manager.token_expiry = valid_time
                return valid_token

        auth_manager.authenticate = mock_authenticate

        # First call gets expired token
        await auth_manager.get_valid_token()
        assert auth_call_count == 1

        # Second call should detect expiry and re-authenticate
        result = await auth_manager.get_valid_token()
        assert result == valid_token
        assert auth_call_count == 2

    @pytest.mark.asyncio
    async def test_auth_error_propagation_with_lock(self, auth_manager):
        """Test that authentication errors are properly propagated even with lock."""

        async def mock_authenticate():
            raise AuthenticationError("Invalid credentials")

        auth_manager.authenticate = mock_authenticate

        # Multiple concurrent calls should all receive the error
        tasks = [auth_manager.get_valid_token() for _ in range(5)]

        # All tasks should raise AuthenticationError
        for task in asyncio.as_completed(tasks):
            with pytest.raises(AuthenticationError, match="Invalid credentials"):
                await task

    @pytest.mark.asyncio
    async def test_token_refresh_near_expiry(self, auth_manager):
        """Test that token is refreshed when near expiry (within 5 minutes)."""
        # Create a token that expires in 4 minutes (should trigger refresh)
        near_expiry = datetime.now(timezone.utc) + timedelta(minutes=4)
        near_expiry_payload = {
            "exp": int(near_expiry.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
        }
        near_expiry_token = jwt.encode(
            near_expiry_payload, "dummy_secret", algorithm="HS256"
        )

        # Create a new token with longer expiry
        new_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        new_payload = {
            "exp": int(new_expiry.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
        }
        new_token = jwt.encode(new_payload, "dummy_secret", algorithm="HS256")

        auth_call_count = 0

        async def mock_authenticate():
            nonlocal auth_call_count
            auth_call_count += 1
            if auth_call_count == 1:
                auth_manager.token = near_expiry_token
                auth_manager.token_expiry = near_expiry
                return near_expiry_token
            else:
                auth_manager.token = new_token
                auth_manager.token_expiry = new_expiry
                return new_token

        auth_manager.authenticate = mock_authenticate

        # First call gets near-expiry token
        await auth_manager.get_valid_token()
        assert auth_call_count == 1

        # Second call should refresh due to near expiry
        result = await auth_manager.get_valid_token()
        assert result == new_token
        assert auth_call_count == 2

    @pytest.mark.asyncio
    async def test_lock_prevents_duplicate_auth_on_slow_network(
        self, auth_manager, mock_token_data
    ):
        """Test that lock prevents duplicate auth even with slow network responses."""
        token, _ = mock_token_data
        auth_call_count = 0
        auth_started_count = 0

        async def mock_authenticate():
            nonlocal auth_call_count, auth_started_count
            auth_started_count += 1
            # Simulate very slow network response
            await asyncio.sleep(0.5)
            auth_call_count += 1
            auth_manager.token = token
            auth_manager.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
            return token

        auth_manager.authenticate = mock_authenticate

        # Start multiple tasks while first auth is still in progress
        tasks = []
        for i in range(5):
            tasks.append(asyncio.create_task(auth_manager.get_valid_token()))
            # Small delay to ensure tasks start while first auth is running
            await asyncio.sleep(0.05)

        results = await asyncio.gather(*tasks)

        # All calls should return the same token
        assert all(result == token for result in results)
        # Only one authentication should have started and completed
        assert auth_started_count == 1
        assert auth_call_count == 1
