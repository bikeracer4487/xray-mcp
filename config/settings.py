"""Configuration management for Xray MCP server.

This module provides configuration handling for the Xray MCP server,
supporting both environment variable and programmatic configuration.
It ensures all required settings are present and provides sensible
defaults where appropriate.

The configuration system supports multiple deployment scenarios:
- Local development with .env files
- Container deployments with environment variables
- Programmatic configuration for testing

Enhanced security features:
- Secure credential validation and sanitization
- Automatic credential masking in logs
- Security pattern detection
"""

import os
from dataclasses import dataclass
from typing import Optional

# Centralized import handling
try:
    from ..security.credential_manager import get_secure_credentials, SecureCredentials
except ImportError:
    from security.credential_manager import get_secure_credentials, SecureCredentials


@dataclass
class XrayConfig:
    """Configuration container for Xray MCP server settings.

    This dataclass holds all configuration required to connect to and
    authenticate with an Xray instance. It provides validation and
    multiple construction methods for flexibility.

    The configuration supports both Xray Cloud and Server instances
    through the configurable base_url parameter.

    Attributes:
        client_id (str): Xray API client ID from Global Settings > API Keys
        client_secret (str): Xray API client secret (keep secure!)
        base_url (str): Base URL for Xray instance, defaults to cloud URL
            - Cloud: https://xray.cloud.getxray.app
            - Server: Your Jira server URL (e.g., https://jira.company.com)

    Example:
        # From environment variables
        config = XrayConfig.from_env()

        # From parameters
        config = XrayConfig.from_params(
            client_id="abc123",
            client_secret="secret456",
            base_url="https://jira.company.com"
        )
    """

    client_id: str
    client_secret: str
    base_url: str = "https://xray.cloud.getxray.app"

    @classmethod
    def from_env(cls) -> "XrayConfig":
        """Create configuration from environment variables.

        Reads configuration from environment variables with validation.
        This is the primary method for production deployments where
        credentials are managed through environment configuration.

        Required Environment Variables:
            XRAY_CLIENT_ID: Xray API client ID
            XRAY_CLIENT_SECRET: Xray API client secret

        Optional Environment Variables:
            XRAY_BASE_URL: Custom Xray instance URL (defaults to cloud)

        Returns:
            XrayConfig: Validated configuration instance

        Raises:
            ValueError: If required environment variables are missing

        Complexity: O(1) - Simple environment lookups

        Example:
            # Set environment variables
            export XRAY_CLIENT_ID="your-client-id"
            export XRAY_CLIENT_SECRET="your-secret"

            # Create config
            config = XrayConfig.from_env()
        """
        client_id = os.getenv("XRAY_CLIENT_ID")
        client_secret = os.getenv("XRAY_CLIENT_SECRET")

        # Validate required fields with clear error messages
        if not client_id:
            raise ValueError("XRAY_CLIENT_ID environment variable is required")
        if not client_secret:
            raise ValueError("XRAY_CLIENT_SECRET environment variable is required")

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            base_url=os.getenv("XRAY_BASE_URL", "https://xray.cloud.getxray.app"),
        )

    @classmethod
    def from_secure_env(cls) -> "XrayConfig":
        """Create configuration using secure credential management.

        This method leverages the secure credential manager for enhanced
        security features including validation, sanitization, and secure
        logging. Recommended for production environments.

        Returns:
            XrayConfig: Securely validated configuration instance

        Raises:
            ValueError: If credentials are invalid or missing
            SecurityError: If potential security issues are detected

        Complexity: O(1) - Credential validation and creation

        Example:
            # Uses secure credential validation
            config = XrayConfig.from_secure_env()
        """
        # Get securely managed credentials
        secure_creds = get_secure_credentials()
        
        return cls(
            client_id=secure_creds.client_id,
            client_secret=secure_creds.client_secret,
            base_url=secure_creds.base_url,
        )

    def __str__(self) -> str:
        """String representation with masked credentials."""
        masked_secret = f"{self.client_secret[:4]}...{self.client_secret[-4:]}" if len(self.client_secret) > 8 else "***masked***"
        return f"XrayConfig(client_id={self.client_id[:8]}..., client_secret={masked_secret}, base_url={self.base_url})"

    def __repr__(self) -> str:
        """Representation with masked credentials."""
        return self.__str__()

    @classmethod
    def from_params(
        cls, client_id: str, client_secret: str, base_url: Optional[str] = None
    ) -> "XrayConfig":
        """Create configuration from explicit parameters.

        This method allows programmatic configuration, useful for:
        - Testing with mock credentials
        - Dynamic configuration from other sources
        - Temporary configurations for specific operations

        Args:
            client_id (str): Xray API client ID
            client_secret (str): Xray API client secret
            base_url (Optional[str]): Custom Xray instance URL.
                If None, defaults to Xray Cloud URL.

        Returns:
            XrayConfig: Configuration instance with provided values

        Complexity: O(1) - Simple object construction

        Example:
            # For Xray Cloud
            config = XrayConfig.from_params(
                "client-123",
                "secret-456"
            )

            # For Xray Server
            config = XrayConfig.from_params(
                "client-123",
                "secret-456",
                "https://jira.company.com"
            )
        """
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url or "https://xray.cloud.getxray.app",
        )
