#!/usr/bin/env python3
"""
HTTP server wrapper for Xray MCP server.

This wrapper enables the MCP server to run in HTTP mode for E2E testing,
using FastMCP's built-in HTTP server capabilities with a health check endpoint.
"""

import asyncio
import argparse
import sys
from typing import Optional
from starlette.responses import JSONResponse
from starlette.requests import Request

from main import create_server_from_env


async def run_http_server(port: int = 8000, host: str = "localhost"):
    """Run the MCP server in HTTP mode with health check.
    
    Args:
        port: Port to listen on (default: 8000)
        host: Host to bind to (default: localhost)
    """
    try:
        # Create the server and initialize authentication
        server = create_server_from_env()
        await server.initialize()
        
        # Add health endpoint using FastMCP's custom_route decorator
        @server.mcp.custom_route("/health", methods=["GET"])
        async def health_check(request: Request):
            """Health check endpoint for the MCP server."""
            return JSONResponse({"status": "ok", "service": "xray-mcp"})
        
        print(f"Starting Xray MCP HTTP server on {host}:{port}")
        print(f"Health endpoint: http://{host}:{port}/health")
        print("Press Ctrl+C to stop the server")
        
        # Use FastMCP's built-in HTTP server capability
        await server.mcp.run_http_async(port=port, host=host)
    except KeyboardInterrupt:
        print(f"\nShutting down HTTP server on {host}:{port}")
        await server.shutdown()
    except Exception as e:
        print(f"Error running HTTP server: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for HTTP server mode."""
    parser = argparse.ArgumentParser(description="Xray MCP HTTP Server")
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to listen on (default: 8000)"
    )
    parser.add_argument(
        "--host", 
        type=str, 
        default="localhost", 
        help="Host to bind to (default: localhost)"
    )
    
    args = parser.parse_args()
    
    print(f"Starting Xray MCP HTTP server on {args.host}:{args.port}")
    print("Press Ctrl+C to stop the server")
    
    asyncio.run(run_http_server(port=args.port, host=args.host))


if __name__ == "__main__":
    main()