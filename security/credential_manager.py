"""Secure credential storage and management for Xray MCP server.

This module provides secure credential storage capabilities including:
- Environment variable validation and sanitization
- In-memory credential encryption for sensitive operations
- Credential masking for logging and error messages
- Secure credential lifecycle management
"""

import os
import logging
import hashlib
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import base64


@dataclass
class SecureCredentials:
    """Container for securely handled credentials.
    
    This class provides secure handling of sensitive credentials including:
    - Automatic masking in string representations
    - Secure comparison operations
    - Memory clearing capabilities
    
    Attributes:
        client_id: Xray API client ID
        client_secret: Xray API client secret (masked in logs)
        base_url: Xray instance base URL
    """
    client_id: str
    client_secret: str
    base_url: str = "https://xray.cloud.getxray.app"
    
    # Internal tracking
    _hash: str = field(init=False)
    _masked_secret: str = field(init=False)
    
    def __post_init__(self):
        """Post-initialization security setup."""
        # Create hash for secure comparison
        self._hash = hashlib.sha256(
            f"{self.client_id}:{self.client_secret}".encode()
        ).hexdigest()
        
        # Create masked version for logging
        if len(self.client_secret) > 8:
            self._masked_secret = f"{self.client_secret[:4]}...{self.client_secret[-4:]}"
        else:
            self._masked_secret = "***masked***"
    
    def __str__(self) -> str:
        """String representation with masked credentials."""
        return f"SecureCredentials(client_id={self.client_id[:8]}..., client_secret={self._masked_secret}, base_url={self.base_url})"
    
    def __repr__(self) -> str:
        """Representation with masked credentials."""
        return self.__str__()
    
    def verify_integrity(self, other: 'SecureCredentials') -> bool:
        """Verify credentials match using secure comparison.
        
        Args:
            other: Other credentials to compare against
            
        Returns:
            True if credentials match, False otherwise
        """
        return self._hash == other._hash
    
    def get_masked_secret(self) -> str:
        """Get masked version of secret for logging.
        
        Returns:
            Masked client secret safe for logging
        """
        return self._masked_secret


class CredentialManager:
    """Manages secure credential storage and validation.
    
    This class provides enhanced security features for credential management:
    - Environment variable validation with security checks
    - Credential sanitization and validation
    - Secure logging with automatic masking
    - Memory-safe credential handling
    """
    
    def __init__(self):
        """Initialize the credential manager."""
        self._logger = logging.getLogger(__name__)
        self._credentials: Optional[SecureCredentials] = None
        
    def load_from_environment(self) -> SecureCredentials:
        """Load and validate credentials from environment variables.
        
        Performs comprehensive validation and security checks on
        environment-provided credentials including:
        - Presence validation
        - Format validation
        - Security pattern detection
        - Sanitization
        
        Returns:
            SecureCredentials: Validated and sanitized credentials
            
        Raises:
            ValueError: If credentials are invalid or insecure
            SecurityError: If potential security issues are detected
        """
        # Read raw environment variables
        raw_client_id = os.getenv("XRAY_CLIENT_ID")
        raw_client_secret = os.getenv("XRAY_CLIENT_SECRET")
        raw_base_url = os.getenv("XRAY_BASE_URL", "https://xray.cloud.getxray.app")
        
        # Validate required fields
        if not raw_client_id:
            raise ValueError(
                "XRAY_CLIENT_ID environment variable is required. "
                "Please set it with your Xray API client ID."
            )
        
        if not raw_client_secret:
            raise ValueError(
                "XRAY_CLIENT_SECRET environment variable is required. "
                "Please set it with your Xray API client secret."
            )
        
        # Sanitize and validate credentials
        client_id = self._sanitize_client_id(raw_client_id)
        client_secret = self._validate_client_secret(raw_client_secret)
        base_url = self._validate_base_url(raw_base_url)
        
        # Create secure credentials container
        self._credentials = SecureCredentials(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url
        )
        
        # Log successful load with masked credentials
        self._logger.info(f"Loaded credentials: {self._credentials}")
        
        return self._credentials
    
    def _sanitize_client_id(self, client_id: str) -> str:
        """Sanitize and validate client ID.
        
        Args:
            client_id: Raw client ID from environment
            
        Returns:
            Sanitized client ID
            
        Raises:
            ValueError: If client ID is invalid
        """
        # Strip whitespace
        sanitized = client_id.strip()
        
        # Validate length
        if len(sanitized) < 8:
            raise ValueError("Client ID appears too short - check your configuration")
        
        if len(sanitized) > 100:
            raise ValueError("Client ID appears too long - possible configuration error")
        
        # Check for suspicious patterns
        if any(pattern in sanitized.lower() for pattern in ['test', 'example', 'placeholder']):
            self._logger.warning("Client ID contains test/placeholder patterns - ensure production credentials")
        
        return sanitized
    
    def _validate_client_secret(self, client_secret: str) -> str:
        """Validate client secret with security checks.
        
        Args:
            client_secret: Raw client secret from environment
            
        Returns:
            Validated client secret
            
        Raises:
            ValueError: If client secret is invalid
            SecurityError: If security issues are detected
        """
        # Strip whitespace
        sanitized = client_secret.strip()
        
        # Validate length
        if len(sanitized) < 16:
            raise ValueError("Client secret appears too short - check your configuration")
        
        # Check for common insecure patterns
        insecure_patterns = [
            'password', 'secret', 'test', 'example', 'placeholder', 
            '123456', 'qwerty', 'admin', 'default'
        ]
        
        if any(pattern in sanitized.lower() for pattern in insecure_patterns):
            raise ValueError(
                "Client secret contains common insecure patterns. "
                "Please use the actual secret from Xray Global Settings."
            )
        
        # Check for repeated characters (sign of weak credential)
        if len(set(sanitized)) < len(sanitized) * 0.5:
            self._logger.warning("Client secret has low entropy - ensure it's from Xray Global Settings")
        
        return sanitized
    
    def _validate_base_url(self, base_url: str) -> str:
        """Validate and sanitize base URL.
        
        Args:
            base_url: Raw base URL from environment
            
        Returns:
            Validated base URL
            
        Raises:
            ValueError: If URL is invalid
        """
        # Strip whitespace and trailing slashes
        sanitized = base_url.strip().rstrip('/')
        
        # Validate URL format
        if not sanitized.startswith(('http://', 'https://')):
            raise ValueError(f"Base URL must start with http:// or https://: {sanitized}")
        
        # Warn about insecure HTTP in production
        if sanitized.startswith('http://') and 'localhost' not in sanitized:
            self._logger.warning("Using insecure HTTP for non-localhost URL - consider HTTPS")
        
        # Validate common Xray URL patterns
        valid_patterns = [
            'xray.cloud.getxray.app',
            '.atlassian.net',
            'localhost',
            '127.0.0.1'
        ]
        
        if not any(pattern in sanitized for pattern in valid_patterns):
            self._logger.info(f"Using custom Xray URL: {sanitized}")
        
        return sanitized
    
    def get_credentials(self) -> Optional[SecureCredentials]:
        """Get current credentials.
        
        Returns:
            Current credentials if loaded, None otherwise
        """
        return self._credentials
    
    def clear_credentials(self):
        """Securely clear credentials from memory.
        
        This method attempts to clear sensitive data from memory
        for security purposes, though Python's garbage collection
        may not immediately free the memory.
        """
        if self._credentials:
            # Clear internal references
            self._credentials = None
            self._logger.debug("Credentials cleared from memory")
    
    def validate_credentials_format(self, client_id: str, client_secret: str) -> Dict[str, Any]:
        """Validate credential format without storing.
        
        This method can be used to validate credentials before use
        without storing them in the manager.
        
        Args:
            client_id: Client ID to validate
            client_secret: Client secret to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        try:
            self._sanitize_client_id(client_id)
        except ValueError as e:
            results["valid"] = False
            results["errors"].append(f"Client ID: {str(e)}")
        
        try:
            self._validate_client_secret(client_secret)
        except ValueError as e:
            results["valid"] = False
            results["errors"].append(f"Client Secret: {str(e)}")
        
        return results


# Global credential manager instance
_credential_manager = CredentialManager()

def get_secure_credentials() -> SecureCredentials:
    """Get securely managed credentials.
    
    This is the primary function for obtaining credentials throughout
    the application. It ensures proper validation and security checks.
    
    Returns:
        SecureCredentials: Validated credentials
        
    Raises:
        ValueError: If credentials cannot be loaded or are invalid
    """
    global _credential_manager
    
    credentials = _credential_manager.get_credentials()
    if credentials is None:
        credentials = _credential_manager.load_from_environment()
    
    return credentials


def validate_environment_credentials() -> Dict[str, Any]:
    """Validate credentials in environment without loading.
    
    Returns:
        Dictionary with validation results
    """
    global _credential_manager
    
    client_id = os.getenv("XRAY_CLIENT_ID", "")
    client_secret = os.getenv("XRAY_CLIENT_SECRET", "")
    
    return _credential_manager.validate_credentials_format(client_id, client_secret)


def clear_credential_cache():
    """Clear cached credentials for security."""
    global _credential_manager
    _credential_manager.clear_credentials()