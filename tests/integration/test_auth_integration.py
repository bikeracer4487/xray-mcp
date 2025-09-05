import pytest
import os
from dotenv import load_dotenv
from src.auth import XrayAuth

# Load environment variables
load_dotenv()

class TestXrayAuthIntegration:
    """Integration tests for Xray authentication against live API."""
    
    @pytest.fixture
    def auth(self):
        """Create XrayAuth instance with real credentials."""
        return XrayAuth(
            client_id=os.getenv('XRAY_CLIENT_ID'),
            client_secret=os.getenv('XRAY_CLIENT_SECRET')
        )
    
    @pytest.mark.asyncio
    async def test_authenticate_with_real_api(self, auth):
        """Test authentication against live Xray API."""
        token = await auth.authenticate()
        
        # Token should be a non-empty string
        assert token
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are typically long
        
        # Should be stored in the auth object
        assert auth.token == token
        
        # Should be able to get headers
        headers = auth.get_headers()
        assert headers['Authorization'] == f'Bearer {token}'
        assert headers['Content-Type'] == 'application/json'
    
    @pytest.mark.asyncio
    async def test_token_reuse(self, auth):
        """Test that token can be reused for multiple requests."""
        token1 = await auth.authenticate()
        token2 = await auth.authenticate()
        
        # Should return the same token if not expired
        assert token1 == token2
    
    @pytest.mark.asyncio
    async def test_invalid_credentials(self):
        """Test authentication with invalid credentials."""
        auth = XrayAuth(
            client_id='invalid_id',
            client_secret='invalid_secret'
        )
        
        with pytest.raises(Exception) as exc_info:
            await auth.authenticate()
        
        assert 'Authentication failed' in str(exc_info.value)