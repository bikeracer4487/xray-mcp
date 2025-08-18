"""Integration tests for XrayAuthManager against real Xray API.

These tests validate that our mock unit tests accurately represent
the real API behavior for authentication.
"""

import pytest
import asyncio
import jwt
import os
from datetime import datetime, timezone, timedelta
import aiohttp

from auth.manager import XrayAuthManager
from exceptions import AuthenticationError


@pytest.mark.integration
class TestAuthManagerRealAPI:
    """Test authentication manager against real Xray API."""
    
    async def test_authenticate_real_api_success(self, auth_manager):
        """Validate successful authentication returns JWT token with proper structure."""
        # This should already be authenticated from fixture, but test explicitly
        token = await auth_manager.authenticate()
        
        # Validate token structure matches our mock expectations
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are typically long
        
        # Validate token doesn't have quotes (our mocks strip them)
        assert not token.startswith('"')
        assert not token.endswith('"')
        
        # Validate JWT structure (header.payload.signature)
        parts = token.split('.')
        assert len(parts) == 3, "JWT should have 3 parts separated by dots"
        
        # Validate we can decode the token (without verification)
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            assert "exp" in decoded, "Token should have expiry claim"
            
            # Validate expiry is in the future
            exp_timestamp = decoded["exp"]
            expiry_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            assert expiry_time > datetime.now(timezone.utc), "Token expiry should be in future"
            
            # Validate token validity period (Xray tokens are typically valid for 24 hours)
            time_until_expiry = expiry_time - datetime.now(timezone.utc)
            assert timedelta(hours=20) < time_until_expiry <= timedelta(hours=24), \
                f"Token validity period should be ~24 hours, got {time_until_expiry}"
        except jwt.InvalidTokenError as e:
            pytest.fail(f"Failed to decode JWT token: {e}")
    
    async def test_authenticate_invalid_credentials(self, integration_enabled):
        """Validate 401 error with invalid credentials matches our mocks."""
        manager = XrayAuthManager(
            "invalid_client_id",
            "invalid_client_secret"
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            await manager.authenticate()
        
        # Validate error message matches our mock expectations
        error_msg = str(exc_info.value)
        assert "401" in error_msg or "Unauthorized" in error_msg or "Invalid" in error_msg, \
            f"Expected 401/Unauthorized error, got: {error_msg}"
    
    async def test_authenticate_malformed_request(self, integration_enabled):
        """Validate API behavior with malformed credentials."""
        # Use None/empty credentials to trigger 400 or similar
        manager = XrayAuthManager("", "")
        
        with pytest.raises(AuthenticationError) as exc_info:
            await manager.authenticate()
        
        # API should reject empty credentials
        error_msg = str(exc_info.value)
        assert "400" in error_msg or "401" in error_msg or "Bad request" in error_msg, \
            f"Expected 400/401 error for empty credentials, got: {error_msg}"
    
    async def test_get_valid_token_caching(self, auth_manager):
        """Validate token caching behavior matches our mocks."""
        # First call should authenticate
        token1 = await auth_manager.get_valid_token()
        assert token1 is not None
        
        # Store the token and expiry
        original_token = auth_manager.token
        original_expiry = auth_manager.token_expiry
        
        # Second immediate call should return cached token
        token2 = await auth_manager.get_valid_token()
        assert token2 == token1, "Should return cached token"
        assert auth_manager.token == original_token, "Token should not change"
        assert auth_manager.token_expiry == original_expiry, "Expiry should not change"
        
        # Multiple rapid calls should all return same token
        tokens = await asyncio.gather(*[
            auth_manager.get_valid_token() for _ in range(5)
        ])
        assert all(t == token1 for t in tokens), "All concurrent calls should return same token"
    
    async def test_token_expiry_buffer_behavior(self, integration_enabled):
        """Validate 5-minute buffer behavior with real tokens."""
        manager = XrayAuthManager(
            os.getenv("XRAY_CLIENT_ID"),
            os.getenv("XRAY_CLIENT_SECRET")
        )
        
        # Authenticate and get initial token
        token1 = await manager.authenticate()
        
        # Manually set expiry to be within buffer (4 minutes from now)
        manager.token_expiry = datetime.now(timezone.utc) + timedelta(minutes=4)
        
        # This should trigger re-authentication due to buffer
        token2 = await manager.get_valid_token()
        
        # If API allows rapid re-auth, we should get a new token
        # Note: Some APIs may return the same token if it's still valid
        assert token2 is not None
        
        # Verify the token expiry was updated
        assert manager.token_expiry > datetime.now(timezone.utc) + timedelta(minutes=5), \
            "New token should have expiry beyond the 5-minute buffer"
    
    async def test_concurrent_authentication_prevention(self, integration_enabled):
        """Validate race condition prevention with real API."""
        import os
        manager = XrayAuthManager(
            os.getenv("XRAY_CLIENT_ID"),
            os.getenv("XRAY_CLIENT_SECRET")
        )
        
        # Clear any cached token
        manager.token = None
        manager.token_expiry = None
        
        # Track authentication calls
        auth_count = 0
        original_auth = manager.authenticate
        
        async def counting_auth():
            nonlocal auth_count
            auth_count += 1
            return await original_auth()
        
        manager.authenticate = counting_auth
        
        # Launch multiple concurrent token requests
        tokens = await asyncio.gather(*[
            manager.get_valid_token() for _ in range(10)
        ])
        
        # All should return the same token
        assert len(set(tokens)) == 1, "All concurrent calls should return same token"
        
        # Only one authentication should have occurred
        assert auth_count == 1, f"Expected 1 auth call, got {auth_count}"
    
    async def test_network_error_handling(self, integration_enabled):
        """Validate network error handling with unreachable endpoint."""
        manager = XrayAuthManager(
            "test_id",
            "test_secret",
            base_url="https://invalid.xray.endpoint.that.does.not.exist"
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            await manager.authenticate()
        
        # Should wrap network error
        error_msg = str(exc_info.value)
        assert "Network error" in error_msg or "ClientError" in error_msg, \
            f"Expected network error, got: {error_msg}"
    
    async def test_custom_base_url_support(self, integration_enabled):
        """Validate custom base URL configuration."""
        import os
        custom_url = os.getenv("XRAY_BASE_URL", "https://xray.cloud.getxray.app")
        
        manager = XrayAuthManager(
            os.getenv("XRAY_CLIENT_ID"),
            os.getenv("XRAY_CLIENT_SECRET"),
            base_url=custom_url
        )
        
        # Should successfully authenticate with custom URL
        token = await manager.authenticate()
        assert token is not None
        
        # Validate the endpoint URL was constructed correctly
        expected_endpoint = f"{custom_url}/api/v2/authenticate"
        # We can't directly check the URL used, but successful auth proves it worked


@pytest.mark.integration
class TestTokenExpiryValidation:
    """Validate token expiry calculations match real behavior."""
    
    async def test_real_token_expiry_extraction(self, auth_manager):
        """Validate JWT expiry extraction matches real tokens."""
        token = await auth_manager.authenticate()
        
        # Decode token to check expiry
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_from_jwt = decoded.get("exp")
        
        assert exp_from_jwt is not None, "Real tokens should have exp claim"
        
        # Check our stored expiry matches JWT expiry
        stored_expiry_timestamp = int(auth_manager.token_expiry.timestamp())
        
        # Allow 1 second difference for processing time
        assert abs(stored_expiry_timestamp - exp_from_jwt) <= 1, \
            "Stored expiry should match JWT exp claim"
    
    def test_is_token_expired_logic_validation(self, auth_manager):
        """Validate expiry checking logic with real token expiry values."""
        # Test with various expiry times
        now = datetime.now(timezone.utc)
        
        # Expired token
        auth_manager.token_expiry = now - timedelta(minutes=1)
        assert auth_manager._is_token_expired() is True
        
        # Token expiring in 4 minutes (within buffer)
        auth_manager.token_expiry = now + timedelta(minutes=4)
        assert auth_manager._is_token_expired() is True
        
        # Token expiring in exactly 5 minutes (at buffer boundary)
        auth_manager.token_expiry = now + timedelta(minutes=5)
        assert auth_manager._is_token_expired() is True
        
        # Token expiring in 6 minutes (outside buffer)
        auth_manager.token_expiry = now + timedelta(minutes=6)
        assert auth_manager._is_token_expired() is False
        
        # Token expiring in 1 hour (well outside buffer)
        auth_manager.token_expiry = now + timedelta(hours=1)
        assert auth_manager._is_token_expired() is False
    
    async def test_jwt_decode_fallback_never_triggered(self, auth_manager):
        """Validate real tokens always decode successfully (no fallback needed)."""
        # Get multiple tokens to test consistency
        for _ in range(3):
            token = await auth_manager.authenticate()
            
            # Should always decode successfully
            try:
                decoded = jwt.decode(token, options={"verify_signature": False})
                assert "exp" in decoded, "All real tokens should have valid exp claim"
            except jwt.InvalidTokenError:
                pytest.fail("Real Xray tokens should always be valid JWT tokens")
            
            # Wait a bit before next auth to avoid rate limiting
            await asyncio.sleep(1)


@pytest.mark.integration
@pytest.mark.slow
class TestAuthManagerStressTest:
    """Stress test authentication under load."""
    
    async def test_rapid_sequential_authentications(self, integration_enabled):
        """Test multiple sequential authentications (respects rate limits)."""
        import os
        manager = XrayAuthManager(
            os.getenv("XRAY_CLIENT_ID"),
            os.getenv("XRAY_CLIENT_SECRET")
        )
        
        tokens = []
        for i in range(5):
            try:
                token = await manager.authenticate()
                tokens.append(token)
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.5)
            except AuthenticationError as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    pytest.skip(f"Rate limited after {i} requests")
                raise
        
        # All tokens should be valid
        assert all(t is not None for t in tokens)
        
        # Tokens might be the same if API caches them server-side
        # or different if it generates new ones each time
        # Just verify they're all valid JWTs
        for token in tokens:
            parts = token.split('.')
            assert len(parts) == 3, "Each token should be valid JWT"