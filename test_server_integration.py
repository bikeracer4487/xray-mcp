#!/usr/bin/env python3
"""Test MCP server integration with new error handling."""

import asyncio
import sys
import os
import json
from unittest.mock import AsyncMock, MagicMock

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import XrayMCPServer
from config import XrayConfig


async def test_tool_validation():
    """Test that tools properly validate parameters."""
    print("Testing MCP server tool validation...")
    
    # Create a mock config
    config = XrayConfig(
        client_id="test_id",
        client_secret="test_secret",
        base_url="https://xray.cloud.getxray.app"
    )
    
    # Create server
    server = XrayMCPServer(config)
    
    # Mock the GraphQL client to avoid real API calls
    server.test_tools.get_test = AsyncMock(return_value={"status": "success"})
    server.test_tools.create_test = AsyncMock(return_value={"status": "success"})
    server.utility_tools.execute_jql_query = AsyncMock(return_value={"status": "success"})
    
    # Get the tool functions from the server
    tools = {}
    for attr_name in dir(server):
        if not attr_name.startswith('_') and hasattr(server, attr_name):
            attr = getattr(server, attr_name)
            if hasattr(attr, 'mcp') and hasattr(attr.mcp, '_tools'):
                for tool_name, tool_func in attr.mcp._tools.items():
                    tools[tool_name] = tool_func
    
    # Test get_test with invalid issue_id (should fail validation)
    print("Testing get_test with empty issue_id...")
    try:
        # Find the get_test tool
        get_test_func = None
        for name, func in server.mcp._tools.items():
            if name == "get_test":
                get_test_func = func
                break
        
        if get_test_func:
            result = await get_test_func("")  # Empty issue_id should fail
            if isinstance(result, dict) and "error" in result:
                print(f"✓ Validation caught empty issue_id: {result.get('message', result.get('error'))}")
            else:
                print("✗ Empty issue_id should have been caught by validation")
        else:
            print("✗ get_test tool not found")
    except Exception as e:
        print(f"✗ Error testing get_test: {e}")
    
    # Test create_test with invalid project_key
    print("Testing create_test with invalid project_key...")
    try:
        create_test_func = None
        for name, func in server.mcp._tools.items():
            if name == "create_test":
                create_test_func = func
                break
        
        if create_test_func:
            result = await create_test_func("invalid-key", "Test Summary")  # lowercase project key should fail
            if isinstance(result, dict) and "error" in result:
                print(f"✓ Validation caught invalid project_key: {result.get('message', result.get('error'))}")
            else:
                print("✗ Invalid project_key should have been caught by validation")
        else:
            print("✗ create_test tool not found")
    except Exception as e:
        print(f"✗ Error testing create_test: {e}")
    
    # Test execute_jql_query with invalid limit
    print("Testing execute_jql_query with invalid limit...")
    try:
        jql_func = None
        for name, func in server.mcp._tools.items():
            if name == "execute_jql_query":
                jql_func = func
                break
        
        if jql_func:
            result = await jql_func("project = PROJ", "test", 101)  # limit > 100 should fail
            if isinstance(result, dict) and "error" in result:
                print(f"✓ Validation caught invalid limit: {result.get('message', result.get('error'))}")
            else:
                print("✗ Invalid limit should have been caught by validation")
        else:
            print("✗ execute_jql_query tool not found")
    except Exception as e:
        print(f"✗ Error testing execute_jql_query: {e}")


async def main():
    """Run integration tests."""
    print("🚀 Testing MCP Server Integration with Error Handling\n")
    
    await test_tool_validation()
    
    print("\n✅ MCP server integration tests completed!")


if __name__ == "__main__":
    asyncio.run(main())