import json
from typing import Optional, Dict, Any
import aiohttp
from src.auth import XrayAuth


class XrayGraphQLClient:
    """GraphQL client for Xray Cloud API."""
    
    def __init__(self, auth: XrayAuth):
        """Initialize GraphQL client with authentication handler.
        
        Args:
            auth: Authenticated XrayAuth instance
        """
        self.auth = auth
        self.graphql_url = f"{auth.base_url}/api/v2/graphql"
    
    async def execute(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query or mutation.
        
        Args:
            query: GraphQL query or mutation string
            variables: Optional variables dictionary for the query
            
        Returns:
            Dictionary containing the GraphQL response data
            
        Raises:
            Exception: If the request fails or contains GraphQL errors
        """
        headers = self.auth.get_headers()
        
        payload = {
            "query": query
        }
        
        if variables:
            payload["variables"] = variables
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.graphql_url,
                    json=payload,
                    headers=headers
                ) as response:
                    # Handle HTTP errors
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"GraphQL request failed: HTTP {response.status} - {error_text}")
                    
                    result = await response.json()
                    
                    # Handle GraphQL errors
                    if "errors" in result:
                        errors = result["errors"]
                        if errors:
                            error_messages = [error.get("message", str(error)) for error in errors]
                            raise Exception(f"GraphQL error: {'; '.join(error_messages)}")
                    
                    # Return the data portion of the response
                    return result.get("data", {})
                    
        except aiohttp.ClientError as e:
            raise Exception(f"GraphQL request failed: Network error - {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"GraphQL request failed: Invalid JSON response - {str(e)}")
        except Exception as e:
            # Re-raise known exceptions
            if any(phrase in str(e) for phrase in ["GraphQL", "HTTP", "Network"]):
                raise
            # Wrap unknown exceptions
            raise Exception(f"GraphQL request failed: {str(e)}")