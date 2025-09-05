import json
from typing import Optional, Dict
import aiohttp


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
    
    async def authenticate(self) -> str:
        """Authenticate with Xray API and return JWT token.
        
        Returns:
            JWT token string for API authentication
            
        Raises:
            Exception: If authentication fails
        """
        # Return existing token if available (token reuse)
        if self.token:
            return self.token
            
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
                        return self.token
                    else:
                        error_text = await response.text()
                        raise Exception(f"Authentication failed: HTTP {response.status} - {error_text}")
                        
        except aiohttp.ClientError as e:
            raise Exception(f"Authentication failed: Network error - {str(e)}")
        except Exception as e:
            if "Authentication failed" in str(e):
                raise
            raise Exception(f"Authentication failed: {str(e)}")
    
    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authentication token.
        
        Returns:
            Dictionary with Authorization and Content-Type headers
            
        Raises:
            ValueError: If no token is available
        """
        if not self.token:
            raise ValueError("No authentication token available. Call authenticate() first.")
            
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }