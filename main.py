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

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.server import create_server


def create_mcp():
    """Create MCP server instance for FastMCP CLI usage.

    Returns:
        FastMCP: Configured server instance
    """
    return create_server()


if __name__ == "__main__":
    try:
        # Create the FastMCP server
        server = create_server()

        # Run with stdio transport for MCP compatibility
        # This enables the server to work with Claude Desktop, Cursor IDE, and other MCP clients
        server.run(transport="stdio")

    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Failed to start Xray MCP Server: {e}", file=sys.stderr)
        sys.exit(1)