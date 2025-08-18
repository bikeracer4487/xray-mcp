"""Comprehensive tests for XrayAuthManager authentication lifecycle.

Tests cover token management, expiry handling, error scenarios, and race conditions.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta, timezone
import jwt
import aiohttp

from auth.manager import XrayAuthManager
from exceptions import AuthenticationError


@pytest.mark.asyncio
@pytest.mark.unit
class TestAuthenticateSuccess:
    """Test successful authentication scenarios."""

    async def test_authenticate_200_response_strips_quotes(self, mocker):
        """Test successful auth returns stripped token and sets expiry from JWT."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='"mock_jwt_token_with_quotes"')
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        expiry_time = datetime.now(timezone.utc) + timedelta(hours=1)
        with patch('jwt.decode', return_value={"exp": int(expiry_time.timestamp())}):
            manager = XrayAuthManager("test_id", "test_secret")
            token = await manager.authenticate()
        
        assert token == "mock_jwt_token_with_quotes"
        assert manager.token == "mock_jwt_token_with_quotes"
        assert manager.token_expiry is not None
        assert manager.token_expiry <= expiry_time + timedelta(seconds=1)

    async def test_authenticate_jwt_decode_fallback(self, mocker):
        """Test fallback to 1-hour expiry when JWT decode fails."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='"invalid_jwt_token"')
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        with patch('jwt.decode', side_effect=jwt.InvalidTokenError):
            manager = XrayAuthManager("test_id", "test_secret")
            now = datetime.now(timezone.utc)
            with patch('datetime.datetime') as mock_dt:
                mock_dt.now.return_value = now
                mock_dt.fromtimestamp = datetime.fromtimestamp
                token = await manager.authenticate()
        
        assert token == "invalid_jwt_token"
        assert manager.token_expiry is not None
        # Should be approximately 1 hour from now
        diff = manager.token_expiry - now
        assert timedelta(minutes=59) < diff < timedelta(minutes=61)


@pytest.mark.asyncio
@pytest.mark.unit
class TestAuthenticateErrors:
    """Test authentication error scenarios."""

    async def test_authenticate_400_bad_request(self, mocker):
        """Test 400 status raises AuthenticationError with specific message."""
        mock_session = AsyncMock()
        mock_response = AsyncMock(status=400, text=AsyncMock(return_value="bad syntax"))
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        manager = XrayAuthManager("test_id", "test_secret")
        with pytest.raises(AuthenticationError, match="Bad request: Wrong request syntax"):
            await manager.authenticate()

    async def test_authenticate_401_unauthorized(self, mocker):
        """Test 401 status raises AuthenticationError for invalid credentials."""
        mock_session = AsyncMock()
        mock_response = AsyncMock(status=401, text=AsyncMock(return_value="unauthorized"))
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        manager = XrayAuthManager("test_id", "test_secret")
        with pytest.raises(AuthenticationError, match="Unauthorized: Invalid Xray license or credentials"):
            await manager.authenticate()

    async def test_authenticate_500_server_error(self, mocker):
        """Test 500 status raises AuthenticationError for server error."""
        mock_session = AsyncMock()
        mock_response = AsyncMock(status=500, text=AsyncMock(return_value="internal error"))
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        manager = XrayAuthManager("test_id", "test_secret")
        with pytest.raises(AuthenticationError, match="Internal server error during authentication"):
            await manager.authenticate()

    async def test_authenticate_unexpected_status(self, mocker):
        """Test unexpected status code includes status and text in error."""
        mock_session = AsyncMock()
        mock_response = AsyncMock(status=429, text=AsyncMock(return_value="rate limited"))
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        manager = XrayAuthManager("test_id", "test_secret")
        with pytest.raises(AuthenticationError, match="Authentication failed with status 429: rate limited"):
            await manager.authenticate()

    async def test_authenticate_network_error(self, mocker):
        """Test network errors are properly wrapped."""
        mock_session = AsyncMock()
        mock_session.post.side_effect = aiohttp.ClientError("Connection refused")
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        manager = XrayAuthManager("test_id", "test_secret")
        with pytest.raises(AuthenticationError, match="Network error during authentication: Connection refused"):
            await manager.authenticate()

    async def test_authenticate_timeout_error(self, mocker):
        """Test timeout errors are handled properly."""
        mock_session = AsyncMock()
        mock_session.post.side_effect = asyncio.TimeoutError()
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        manager = XrayAuthManager("test_id", "test_secret")
        with pytest.raises(AuthenticationError, match="Network error during authentication"):
            await manager.authenticate()


@pytest.mark.asyncio
@pytest.mark.unit
class TestGetValidToken:
    """Test token validation and refresh logic."""

    async def test_get_valid_token_returns_cached_when_valid(self, mocker):
        """Test cached token is returned when still valid."""
        manager = XrayAuthManager("test_id", "test_secret")
        manager.token = "cached_token"
        manager.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        
        mock_auth = mocker.patch.object(manager, 'authenticate', AsyncMock())
        
        token = await manager.get_valid_token()
        assert token == "cached_token"
        mock_auth.assert_not_called()

    async def test_get_valid_token_refreshes_when_expired(self, mocker):
        """Test expired token triggers refresh."""
        manager = XrayAuthManager("test_id", "test_secret")
        manager.token = "old_token"
        manager.token_expiry = datetime.now(timezone.utc) - timedelta(minutes=1)
        
        mocker.patch.object(manager, 'authenticate', AsyncMock(return_value="new_token"))
        
        token = await manager.get_valid_token()
        assert token == "new_token"
        manager.authenticate.assert_called_once()

    async def test_get_valid_token_refreshes_when_null(self, mocker):
        """Test null token triggers authentication."""
        manager = XrayAuthManager("test_id", "test_secret")
        manager.token = None
        manager.token_expiry = None
        
        mocker.patch.object(manager, 'authenticate', AsyncMock(return_value="new_token"))
        
        token = await manager.get_valid_token()
        assert token == "new_token"
        manager.authenticate.assert_called_once()

    async def test_get_valid_token_refreshes_within_buffer(self, mocker):
        """Test token refreshes when within 5-minute buffer."""
        manager = XrayAuthManager("test_id", "test_secret")
        manager.token = "soon_expired"
        # Set expiry to 4 minutes from now (within 5-minute buffer)
        manager.token_expiry = datetime.now(timezone.utc) + timedelta(minutes=4)
        
        mocker.patch.object(manager, 'authenticate', AsyncMock(return_value="refreshed_token"))
        
        token = await manager.get_valid_token()
        assert token == "refreshed_token"
        manager.authenticate.assert_called_once()

    async def test_concurrent_get_valid_token_single_auth(self, mocker):
        """Test concurrent calls only trigger one authentication."""
        manager = XrayAuthManager("test_id", "test_secret")
        manager.token = None
        auth_call_count = 0
        
        async def mock_authenticate():
            nonlocal auth_call_count
            auth_call_count += 1
            await asyncio.sleep(0.05)  # Simulate network delay
            manager.token = "authenticated_token"
            manager.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
            return "authenticated_token"
        
        mocker.patch.object(manager, 'authenticate', mock_authenticate)
        
        # Launch 5 concurrent calls
        tasks = [manager.get_valid_token() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert all(r == "authenticated_token" for r in results)
        assert auth_call_count == 1  # Only one auth despite concurrent calls


@pytest.mark.asyncio
@pytest.mark.unit
class TestTokenExpiry:
    """Test token expiry logic with buffer."""

    def test_is_token_expired_null_expiry(self):
        """Test null expiry is considered expired."""
        manager = XrayAuthManager("test_id", "test_secret")
        manager.token_expiry = None
        assert manager._is_token_expired() is True

    def test_is_token_expired_past_expiry(self):
        """Test past expiry is considered expired."""
        manager = XrayAuthManager("test_id", "test_secret")
        manager.token_expiry = datetime.now(timezone.utc) - timedelta(minutes=1)
        assert manager._is_token_expired() is True

    def test_is_token_expired_within_buffer(self):
        """Test expiry within 5-minute buffer is considered expired."""
        manager = XrayAuthManager("test_id", "test_secret")
        now = datetime.now(timezone.utc)
        
        # Test at exactly 5 minutes
        manager.token_expiry = now + timedelta(minutes=5)
        with patch('auth.manager.datetime') as mock_dt:
            mock_dt.now.return_value = now
            mock_dt.timezone = timezone
            assert manager._is_token_expired() is True
        
        # Test at 4 minutes 59 seconds
        manager.token_expiry = now + timedelta(minutes=4, seconds=59)
        with patch('auth.manager.datetime') as mock_dt:
            mock_dt.now.return_value = now
            mock_dt.timezone = timezone
            assert manager._is_token_expired() is True

    def test_is_token_expired_outside_buffer(self):
        """Test expiry outside buffer is not considered expired."""
        manager = XrayAuthManager("test_id", "test_secret")
        now = datetime.now(timezone.utc)
        
        # Test at 5 minutes 1 second
        manager.token_expiry = now + timedelta(minutes=5, seconds=1)
        with patch('auth.manager.datetime') as mock_dt:
            mock_dt.now.return_value = now
            mock_dt.timezone = timezone
            assert manager._is_token_expired() is False
        
        # Test at 1 hour
        manager.token_expiry = now + timedelta(hours=1)
        with patch('auth.manager.datetime') as mock_dt:
            mock_dt.now.return_value = now
            mock_dt.timezone = timezone
            assert manager._is_token_expired() is False


@pytest.mark.asyncio
@pytest.mark.integration
class TestAuthManagerIntegration:
    """Integration tests for auth manager with realistic scenarios."""

    async def test_auth_refresh_cycle(self, mocker):
        """Test complete authentication and refresh cycle."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        
        # First auth returns token expiring in 10 minutes
        first_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
        first_token = '"first_token"'
        
        # Second auth returns token expiring in 1 hour
        second_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        second_token = '"second_token"'
        
        mock_response.text = AsyncMock(side_effect=[first_token, second_token])
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        with patch('jwt.decode', side_effect=[
            {"exp": int(first_expiry.timestamp())},
            {"exp": int(second_expiry.timestamp())}
        ]):
            manager = XrayAuthManager("test_id", "test_secret")
            
            # First call authenticates
            token1 = await manager.get_valid_token()
            assert token1 == "first_token"
            
            # Fast forward to within buffer (triggers refresh)
            manager.token_expiry = datetime.now(timezone.utc) + timedelta(minutes=3)
            token2 = await manager.get_valid_token()
            assert token2 == "second_token"

    async def test_auth_with_custom_base_url(self, mocker):
        """Test authentication with custom server URL."""
        custom_url = "https://jira.company.com"
        mock_session = AsyncMock()
        mock_response = AsyncMock(status=200, text=AsyncMock(return_value='"token"'))
        post_mock = mock_session.post
        post_mock.return_value.__aenter__.return_value = mock_response
        mocker.patch('aiohttp.ClientSession', return_value=mock_session)
        
        with patch('jwt.decode', return_value={"exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())}):
            manager = XrayAuthManager("id", "secret", base_url=custom_url)
            await manager.authenticate()
        
        # Verify correct URL was used
        post_mock.assert_called_once()
        call_args = post_mock.call_args
        assert call_args[0][0] == f"{custom_url}/api/v2/authenticate"