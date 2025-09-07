"""
Xray MCP Server implementation using FastMCP.

Provides MCP tools for interacting with Xray Cloud test management system.
"""

import os
from typing import Dict, Any, Literal
from dotenv import load_dotenv
from fastmcp import FastMCP
from .auth import XrayAuth  
from .graphql_client import XrayGraphQLClient
from .tools.test_tool import TestTool
import asyncio

# Load environment variables
load_dotenv()


class ToolWrapper:
    """Wrapper for FastMCP Tool to provide inputSchema interface for tests."""
    
    def __init__(self, tool):
        self._tool = tool
    
    @property
    def name(self):
        return self._tool.name
    
    @property
    def description(self):
        return self._tool.description
    
    @property
    def inputSchema(self):
        return self._tool.parameters
    
    def __getattr__(self, name):
        return getattr(self._tool, name)


class XrayMCPServer(FastMCP):
    """Extended FastMCP server with synchronous tool listing for testing."""
    
    def list_tools(self):
        """Synchronous wrapper for get_tools() method for test compatibility."""
        # Try to access internal tool manager directly to avoid async issues
        if hasattr(self, '_tool_manager') and self._tool_manager:
            tools = self._tool_manager._tools
            wrapped_tools = [ToolWrapper(tool) for tool in tools.values()] if tools else []
            return wrapped_tools
        
        # Fallback: try async method
        loop = None
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, we can't run async code synchronously
                # This is a limitation, but for tests we can work around it
                return []
        except RuntimeError:
            # No event loop running, we can create one
            pass
        
        # Create new event loop if none exists or if the current one isn't running
        try:
            if loop is None or not loop.is_running():
                tools_dict = asyncio.run(self.get_tools())
                wrapped_tools = [ToolWrapper(tool) for tool in tools_dict.values()] if tools_dict else []
                return wrapped_tools
        except RuntimeError:
            # Fallback: return empty list if we can't get tools synchronously
            return []


def create_server() -> XrayMCPServer:
    """Create and configure FastMCP server with Xray tools.
    
    Returns:
        FastMCP: Configured server instance with registered tools
        
    Raises:
        ValueError: If required environment variables are missing
        Exception: If authentication fails
    """
    # Get required environment variables
    client_id = os.getenv('XRAY_CLIENT_ID')
    client_secret = os.getenv('XRAY_CLIENT_SECRET')
    base_url = os.getenv('XRAY_BASE_URL', 'https://xray.cloud.getxray.app')
    
    if not client_id:
        raise ValueError("XRAY_CLIENT_ID environment variable is required")
    if not client_secret:
        raise ValueError("XRAY_CLIENT_SECRET environment variable is required")
    
    # Create FastMCP server instance
    mcp = XrayMCPServer("Xray Test Management")
    
    # Initialize authentication and GraphQL client
    auth = XrayAuth(client_id, client_secret, base_url)
    client = XrayGraphQLClient(auth)
    
    # Initialize tools
    test_tool = TestTool(client)
    
    # Register xray_test tool with comprehensive schema
    @mcp.tool(description="Manage Xray tests - create, get, update, list, and delete test cases")
    async def xray_test(
        action: Literal["create", "get", "update", "list", "delete"],
        test_type: str = None,
        project_key: str = None,
        summary: str = None,
        description: str = None,
        steps: list = None,
        gherkin: str = None,
        issue_id: str = None,
        limit: int = 50,
        start: int = 0,
        jql: str = None
    ) -> Dict[str, Any]:
        """
        Manage Xray test cases with various operations.
        
        Args:
            action: Action to perform (create, get, update, list, delete)
            test_type: Type of test (Manual, Generic, Cucumber) - required for create
            project_key: Jira project key - required for create and list
            summary: Test case summary - required for create
            description: Test case description
            steps: List of test steps for Manual tests
            gherkin: Gherkin script for Cucumber tests
            issue_id: Issue ID for get, update, delete operations
            limit: Maximum results to return for list (max 100)
            start: Starting index for list pagination
            jql: Custom JQL query for list operation
            
        Returns:
            Dict containing operation results
        """
        # Ensure authentication before executing tool
        await auth.authenticate()
        
        params = {
            'action': action,
            'test_type': test_type,
            'project_key': project_key,
            'summary': summary,
            'description': description,
            'steps': steps or [],
            'gherkin': gherkin,
            'issue_id': issue_id,
            'limit': limit,
            'start': start,
            'jql': jql
        }
        
        return await test_tool.execute(params)
    
    # Register placeholder tools for test sets, test runs, and test executions
    @mcp.tool(description="Manage Xray test sets - create and manage collections of tests")
    async def xray_test_set(action: str = "list") -> Dict[str, Any]:
        """
        Manage Xray test sets.
        
        Args:
            action: Action to perform (currently placeholder)
            
        Returns:
            Dict containing placeholder response
        """
        return {"message": "Test set management not yet implemented", "action": action}
    
    @mcp.tool(description="Manage Xray test runs - execute tests and track results")
    async def xray_test_run(action: str = "list") -> Dict[str, Any]:
        """
        Manage Xray test runs.
        
        Args:
            action: Action to perform (currently placeholder)
            
        Returns:
            Dict containing placeholder response
        """
        return {"message": "Test run management not yet implemented", "action": action}
    
    @mcp.tool(description="Manage Xray test executions - track individual test execution results")
    async def xray_test_execution(action: str = "list") -> Dict[str, Any]:
        """
        Manage Xray test executions.
        
        Args:
            action: Action to perform (currently placeholder)
            
        Returns:
            Dict containing placeholder response
        """
        return {"message": "Test execution management not yet implemented", "action": action}
    
    return mcp


if __name__ == "__main__":
    # For running the server directly
    import asyncio
    
    async def main():
        server = create_server()
        # Server would be started here in a real deployment
        print("Xray MCP Server created successfully")
        
    asyncio.run(main())