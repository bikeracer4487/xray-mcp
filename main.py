#!/usr/bin/env python3
"""Main entry point for Xray MCP Server.

This file provides the main entry point for the Xray MCP Server, which integrates
with Xray Cloud's test management system via GraphQL API. The server follows the
Model Context Protocol (MCP) specification and uses FastMCP framework.

Usage:
    python main.py                    # Run server with stdio transport
    fastmcp run main.py:create_mcp    # Alternative FastMCP CLI approach
"""

import sys
import os
import logging
from datetime import datetime

# Setup logging to file for diagnostic purposes
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'xray_mcp_server.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info(f"Xray MCP Server starting at {datetime.now()}")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Script location: {os.path.abspath(__file__)}")
logger.info("=" * 80)

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.server import create_server


def create_mcp():
    """Create MCP server instance for FastMCP CLI usage.

    Returns:
        FastMCP: Configured server instance
    """
    logger.info("create_mcp() called for FastMCP CLI usage")
    try:
        server = create_server()
        logger.info("Server created successfully for FastMCP CLI")
        return server
    except Exception as e:
        logger.error(f"Failed to create server for FastMCP CLI: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        logger.info("Main execution started")

        # Check for environment variables
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_file):
            logger.info(f".env file found at: {env_file}")
        else:
            logger.warning(f".env file NOT found at: {env_file}")

        # Check for required environment variables
        client_id = os.getenv('XRAY_CLIENT_ID')
        client_secret = os.getenv('XRAY_CLIENT_SECRET')
        logger.info(f"XRAY_CLIENT_ID present: {bool(client_id)}")
        logger.info(f"XRAY_CLIENT_SECRET present: {bool(client_secret)}")

        # Create the FastMCP server
        logger.info("Calling create_server()...")
        server = create_server()
        logger.info("Server created successfully")

        # Log server details
        logger.info(f"Server name: {server.name}")
        logger.info(f"Server has tools: {hasattr(server, '_tool_manager')}")

        if hasattr(server, '_tool_manager'):
            tools = getattr(server._tool_manager, '_tools', {})
            logger.info(f"Registered tools count: {len(tools)}")
            for tool_name in tools.keys():
                logger.info(f"  - Tool registered: {tool_name}")

        # Run with stdio transport for MCP compatibility
        # This enables the server to work with Claude Desktop, Cursor IDE, and other MCP clients
        logger.info("Starting server with stdio transport...")
        server.run(transport="stdio")

    except KeyboardInterrupt:
        logger.info("Server stopped by user (KeyboardInterrupt)")
        print("\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start Xray MCP Server: {e}", exc_info=True)
        print(f"Failed to start Xray MCP Server: {e}", file=sys.stderr)
        sys.exit(1)