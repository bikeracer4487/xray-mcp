"""Main Xray MCP Server implementation using FastMCP."""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, List, Optional, Union

# Path manipulation for direct execution support
# Ensures imports work when running as: python main.py
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastmcp import FastMCP

# Dual import strategy to support both package and direct execution modes
try:
    # Package mode: When installed or imported as a module
    # Uses relative imports (e.g., from xray_mcp_server.main import ...)
    from .config import XrayConfig
    from .auth import XrayAuthManager
    from .client import XrayGraphQLClient
    from .registry import ToolRegistrar
    from .exceptions import (
        XrayMCPError,
        AuthenticationError,
        GraphQLError,
        ValidationError,
    )
except ImportError:
    # Direct execution mode: When running as a script (python main.py)
    # Uses absolute imports from the current directory
    from config import XrayConfig
    from auth import XrayAuthManager
    from client import XrayGraphQLClient
    from registry import ToolRegistrar
    from exceptions import (
        XrayMCPError,
        AuthenticationError,
        GraphQLError,
        ValidationError,
    )


class XrayMCPServer:
    """Jira Xray MCP Server using FastMCP.

    This server provides a Model Context Protocol (MCP) interface to Jira Xray's
    test management capabilities. It handles authentication, GraphQL communication,
    and exposes various test management operations as MCP tools.

    The server follows a modular architecture with:
    - Authentication management via XrayAuthManager
    - GraphQL API communication via XrayGraphQLClient
    - Tool classes for different Xray entities (tests, executions, etc.)
    - Error handling with structured responses

    Attributes:
        config (XrayConfig): Server configuration containing API credentials
        mcp (FastMCP): FastMCP instance for MCP protocol handling
        auth_manager (XrayAuthManager): Handles JWT authentication with Xray
        graphql_client (XrayGraphQLClient): Manages GraphQL API communication
        test_tools (TestTools): Tools for test management operations
        execution_tools (TestExecutionTools): Tools for test execution operations
        plan_tools (TestPlanTools): Tools for test plan operations
        run_tools (TestRunTools): Tools for test run operations
        utility_tools (UtilityTools): Utility tools for validation and queries
        precondition_tools (PreconditionTools): Tools for test precondition management
        testset_tools (TestSetTools): Tools for test set operations
        versioning_tools (TestVersioningTools): Tools for test version management
        coverage_tools (CoverageTools): Tools for test status and coverage queries
        history_tools (HistoryTools): Tools for execution history and attachments
        gherkin_tools (GherkinTools): Tools for Gherkin scenario updates
        organization_tools (OrganizationTools): Tools for folder and dataset management

    Dependencies:
        - Requires valid Xray API credentials (client_id and client_secret)
        - Depends on FastMCP for MCP protocol implementation
        - Uses aiohttp for async HTTP communication

    Call Flow:
        1. Server initialization with config
        2. Authentication via initialize()
        3. Tool registration via _register_tools()
        4. Server run via run() or FastMCP CLI
    """

    def __init__(self, config: XrayConfig):
        """Initialize the Xray MCP Server.

        Sets up all components required for the server:
        - Creates FastMCP instance for MCP protocol handling
        - Initializes authentication manager with API credentials
        - Creates GraphQL client for API communication
        - Creates tool registrar for clean tool management
        - Registers all tools with the MCP server

        Args:
            config (XrayConfig): Configuration object containing:
                - client_id: Xray API client ID
                - client_secret: Xray API client secret
                - base_url: Xray instance URL (defaults to cloud)

        Complexity: O(1) - Simple initialization of components

        Note:
            The server is not authenticated at this point. Call initialize()
            to authenticate with Xray before using any tools.
        """
        self.config = config
        self.mcp = FastMCP("Jira Xray MCP Server")
        self.auth_manager = XrayAuthManager(
            config.client_id, config.client_secret, config.base_url
        )
        self.graphql_client = XrayGraphQLClient(self.auth_manager)
        
        # Create tool registrar and register all tools
        self.tool_registrar = ToolRegistrar(self.mcp, self.graphql_client)
        self._register_tools()

    async def initialize(self):
        """Initialize the server by authenticating with Xray.

        Performs initial authentication with Xray API to obtain a JWT token.
        This method must be called before using any tools that require
        authentication. The token will be automatically refreshed by the
        auth_manager when it expires.

        Raises:
            AuthenticationError: If authentication fails due to:
                - Invalid credentials
                - Network issues
                - Xray API unavailability

        Complexity: O(1) - Single API call for authentication

        Call Flow:
            1. Calls auth_manager.authenticate()
            2. Obtains JWT token from Xray
            3. Stores token in auth_manager for future use

        Example:
            server = XrayMCPServer(config)
            await server.initialize()  # Must authenticate before using tools
        """
        try:
            await self.auth_manager.authenticate()
            logging.info("Successfully authenticated with Xray API")
        except AuthenticationError as e:
            logging.error(f"Failed to authenticate with Xray: {e}")
            raise

    def _register_tools(self):
        """Register all MCP tools with the FastMCP instance.

        Uses the ToolRegistrar to cleanly organize and register all tools
        by functional category, replacing the previous monolithic approach
        with a modular, maintainable system.
        """
        self.tool_registrar.register_all_tools()

    def run(self):
        """Run the MCP server using stdio transport.

        Starts the FastMCP server which listens for MCP protocol messages
        on standard input/output. This is the standard way to expose an
        MCP server to clients.

        The server will run indefinitely until interrupted (Ctrl+C) or
        terminated by the client.

        Call Flow:
            1. FastMCP sets up stdio transport
            2. Listens for incoming MCP messages
            3. Routes tool calls to registered functions
            4. Returns responses via stdout

        Note:
            - Must call initialize() before run() for authenticated operations
            - Server runs synchronously, blocking until terminated
            - All logging goes to stderr to avoid interfering with MCP protocol
        """
        self.mcp.run()

    async def shutdown(self):
        """Shutdown the server and cleanup resources.

        Performs cleanup operations including:
        - Closing HTTP connection pools
        - Cleaning up authentication resources
        - Logging shutdown completion

        This method should be called during graceful shutdown to prevent
        resource leaks and ensure proper cleanup of network connections.

        Complexity: O(1) - Simple cleanup operations

        Example:
            server = XrayMCPServer(config)
            await server.initialize()
            # ... server usage ...
            await server.shutdown()  # Cleanup before exit
        """
        try:
            # Import cleanup function from connection pool
            if __name__ == "__main__":
                from utils.connection_pool import close_connection_pool
            else:
                from .utils.connection_pool import close_connection_pool
            
            await close_connection_pool()
            logging.info("Server shutdown completed successfully")
        except Exception as e:
            logging.warning(f"Error during server shutdown: {e}")


def create_server(
    client_id: str, client_secret: str, base_url: Optional[str] = None
) -> XrayMCPServer:
    """Create and initialize an Xray MCP server.

    Args:
        client_id: Xray API client ID
        client_secret: Xray API client secret
        base_url: Optional Xray base URL (defaults to cloud instance)

    Returns:
        Configured XrayMCPServer instance
    """
    config = XrayConfig.from_params(client_id, client_secret, base_url)
    server = XrayMCPServer(config)
    return server


def create_server_from_env() -> XrayMCPServer:
    """Create and initialize an Xray MCP server from environment variables.

    Environment variables required:
        XRAY_CLIENT_ID: Xray API client ID
        XRAY_CLIENT_SECRET: Xray API client secret
        XRAY_BASE_URL: Optional Xray base URL

    Returns:
        Configured XrayMCPServer instance
    """
    config = XrayConfig.from_env()
    server = XrayMCPServer(config)
    return server


def create_secure_server_from_env() -> XrayMCPServer:
    """Create an Xray MCP server using secure credential management.

    This function provides enhanced security features including:
    - Credential validation and sanitization
    - Security pattern detection
    - Secure logging with credential masking
    - Enhanced error messages for security issues

    Environment variables required:
        XRAY_CLIENT_ID: Xray API client ID
        XRAY_CLIENT_SECRET: Xray API client secret
        XRAY_BASE_URL: Optional Xray base URL

    Returns:
        Configured XrayMCPServer instance with secure credentials

    Raises:
        ValueError: If credentials are invalid or missing
        SecurityError: If potential security issues are detected
    """
    config = XrayConfig.from_secure_env()
    server = XrayMCPServer(config)
    return server


# Module execution handling - supports both direct execution and FastMCP CLI
if __name__ == "__main__":
    # Direct execution path: python main.py
    import os
    from dotenv import load_dotenv

    # Load environment variables from .env file if present
    load_dotenv()

    # Configure logging to stderr to avoid interfering with MCP protocol on stdout
    logging.basicConfig(level=logging.INFO)

    try:
        # Create server using secure credential management
        # Falls back to standard method if security features fail
        try:
            server = create_secure_server_from_env()
            logging.info("Server initialized with secure credential management")
        except Exception as secure_error:
            logging.warning(f"Secure credentials failed, falling back to standard: {secure_error}")
            server = create_server_from_env()

        # Initialize (authenticate) and run the server
        # Authentication must complete before server can handle requests
        asyncio.run(server.initialize())
        server.run()

    except Exception as e:
        logging.error(f"Failed to start Xray MCP server: {e}")
        exit(1)

else:
    # FastMCP CLI path: fastmcp run main.py:mcp
    # This branch executes when the module is imported by FastMCP
    try:
        from dotenv import load_dotenv

        load_dotenv()

        # Create server using secure credentials with fallback
        # FastMCP will handle initialization and running
        try:
            mcp = create_secure_server_from_env().mcp
        except Exception:
            # Fallback to standard credential loading
            mcp = create_server_from_env().mcp
    except Exception:
        # Graceful fallback when environment variables are missing
        # Creates a non-functional placeholder to avoid import errors
        logging.warning(
            "Environment variables not set. Please configure XRAY_CLIENT_ID and XRAY_CLIENT_SECRET."
        )
        mcp = FastMCP("Xray MCP Server - Not Configured")
