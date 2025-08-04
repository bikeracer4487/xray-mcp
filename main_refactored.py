"""Refactored main module demonstrating abstraction layer usage.

This module shows how the abstraction layer simplifies the main.py file
by eliminating repetitive code and improving maintainability.
"""

import os
import logging
from typing import Optional

from fastmcp import FastMCP
from pydantic import BaseModel

# Import abstractions
from abstractions import GraphQLRepository, CachedRepository, create_tool_registry
from auth import XrayAuthManager
from client import XrayGraphQLClient
from config import XrayConfig

# Import refactored tools
from tools.tests_refactored import TestToolsRefactored

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Dependencies(BaseModel):
    """Dependencies for the Xray MCP server."""

    xray_client_id: str
    xray_client_secret: str
    xray_base_url: str = "https://xray.cloud.getxray.app"


class XrayMCPServerRefactored:
    """Refactored Xray MCP Server using abstraction layer.

    This implementation demonstrates how the abstraction layer
    reduces code duplication and improves maintainability.
    """

    def __init__(self, config: XrayConfig):
        """Initialize the server with configuration."""
        self.config = config
        self.mcp = FastMCP(
            name="xray-mcp-server-refactored",
            dependencies=[
                Dependencies(
                    xray_client_id=config.client_id,
                    xray_client_secret=config.client_secret,
                    xray_base_url=config.base_url,
                )
            ],
        )

        # Initialize components
        self.auth_manager = XrayAuthManager(
            config.client_id, config.client_secret, config.base_url
        )
        self.graphql_client = XrayGraphQLClient(self.auth_manager, config.base_url)

        # Create repository with optional caching
        base_repository = GraphQLRepository(self.graphql_client)

        # Add caching if enabled
        if config.enable_cache:
            self.repository = CachedRepository(
                base_repository, cache_ttl=config.cache_ttl
            )
        else:
            self.repository = base_repository

        # Create tool registry
        self.tool_factory = create_tool_registry(self.mcp, self.repository)

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register all tools using the factory.

        This method replaces the hundreds of lines of repetitive
        @self.mcp.tool decorators and try/except blocks.
        """
        # Register refactored tools that use the abstraction layer
        self.tool_factory.register_tool_class(TestToolsRefactored, name="test")

        # For tools that haven't been refactored yet, we can use legacy registration
        # This provides a migration path - we don't need to refactor everything at once

        # Example of registering a legacy tool (if we had one):
        # from tools import TestPlans
        # test_plans = TestPlans(self.graphql_client)
        # self.tool_factory.register_legacy_tool(
        #     "get_test_plan",
        #     test_plans,
        #     "get_test_plan",
        #     doc="Get a test plan by issue ID"
        # )

        logger.info(f"Registered {len(self.tool_factory.list_tools())} tools")

    async def serve(self):
        """Start the MCP server."""
        logger.info("Starting Xray MCP Server (Refactored)")
        logger.info(f"Available tools: {list(self.tool_factory.list_tools().keys())}")

        # The FastMCP server handles the actual serving
        await self.mcp.serve()


def create_server_refactored() -> XrayMCPServerRefactored:
    """Create and configure the refactored server instance.

    This function demonstrates the simplified initialization
    compared to the original implementation.
    """
    # Load configuration
    config = XrayConfig.from_env()

    # Create server
    server = XrayMCPServerRefactored(config)

    return server


# Example of how much simpler the code is:
# Original main.py had ~530 lines with repetitive patterns like:
#
# @self.mcp.tool
# async def get_test(issue_id: str) -> Dict[str, Any]:
#     """Get a test by issue ID."""
#     try:
#         return await self.test_tools.get_test(issue_id)
#     except Exception as e:
#         return {"error": str(e), "type": type(e).__name__}
#
# This pattern was repeated 20+ times!
#
# With the abstraction layer, all of this is handled automatically
# by the ToolFactory, reducing code by ~70% and eliminating duplication.


if __name__ == "__main__":
    import asyncio

    # Create and run server
    server = create_server_refactored()
    asyncio.run(server.serve())
