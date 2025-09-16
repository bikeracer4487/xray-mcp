"""
Xray MCP Server implementation using FastMCP.

Provides MCP tools for interacting with Xray Cloud test management system.
"""

import os
from typing import Dict, Any, Literal, List
from dotenv import load_dotenv
from fastmcp import FastMCP
from .auth import XrayAuth
from .graphql_client import XrayGraphQLClient
from .tools.test_tool import TestTool
from .tools.unified_xray_tool import UnifiedXrayTool
from .schemas.base import ActionResult
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
    
    # Initialize both legacy and unified tools
    test_tool = TestTool(client)
    unified_tool = UnifiedXrayTool(client)

    # Register the unified xray_manage tool with minimal parameters
    @mcp.tool(description="Unified Xray management tool - handle all test operations efficiently")
    async def xray_manage(
        entity: Literal["test", "test_execution", "test_plan", "test_run"],
        action: str,
        issue_id: str = None,
        project_key: str = None,
        summary: str = None,
        test_type: Literal["Manual", "Generic", "Cucumber"] = None,
        test_issue_ids: List[str] = None,
        expand_details: bool = False,
        limit: int = 50,
        start: int = 0,
        jql: str = None,
        description: str = None,
        steps: List[Dict[str, str]] = None,
        gherkin: str = None,
        status: str = None,
        comment: str = None,
        test_environments: List[str] = None
    ) -> Dict[str, Any]:
        """
        Unified tool for managing all Xray entities with minimal schema footprint.

        Args:
            entity: Entity type (test, test_execution, test_plan, test_run)
            action: Action to perform (create, get, update, list, delete, etc.)
            issue_id: Issue ID for specific operations
            project_key: Jira project key
            summary: Summary/title for create operations
            test_type: Test type for test creation
            test_issue_ids: List of test issue IDs for associations
            expand_details: Include detailed information in responses
            limit: Maximum results for list operations (max 100)
            start: Starting index for pagination
            jql: Custom JQL query for filtering
            description: Additional description for entities
            steps: Test steps for Manual tests
            gherkin: Gherkin script for Cucumber tests
            status: Status for test run updates
            comment: Comment for test run updates
            test_environments: Test environments

        Returns:
            ActionResult with operation outcome
        """
        # Ensure authentication before executing tool
        await auth.authenticate()

        # Build parameters dictionary
        params = {
            'entity': entity,
            'action': action,
            'issue_id': issue_id,
            'project_key': project_key,
            'summary': summary,
            'test_type': test_type,
            'test_issue_ids': test_issue_ids or [],
            'expand_details': expand_details,
            'limit': min(limit, 100),
            'start': start,
            'jql': jql,
            'description': description,
            'steps': steps or [],
            'gherkin': gherkin,
            'status': status,
            'comment': comment,
            'test_environments': test_environments or []
        }

        # Remove None values to reduce payload
        params = {k: v for k, v in params.items() if v is not None}

        result = await unified_tool.execute(params)
        return result.model_dump()

    # Register specialized relationship management tool
    @mcp.tool(description="Manage relationships between Xray entities")
    async def xray_link(
        operation: Literal["add", "remove"],
        source_entity: Literal["test_execution", "test_plan"],
        target_entity: Literal["test", "test_execution", "environment"],
        source_id: str,
        target_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Manage relationships between Xray entities.

        Args:
            operation: Add or remove relationship
            source_entity: Source entity type
            target_entity: Target entity type
            source_id: Source entity issue ID
            target_ids: List of target entity IDs

        Returns:
            ActionResult with operation outcome
        """
        await auth.authenticate()

        # Map to unified tool actions
        action_map = {
            ('test_execution', 'test', 'add'): 'add_tests',
            ('test_execution', 'test', 'remove'): 'remove_tests',
            ('test_execution', 'environment', 'add'): 'add_environments',
            ('test_execution', 'environment', 'remove'): 'remove_environments',
            ('test_plan', 'test', 'add'): 'add_tests',
            ('test_plan', 'test', 'remove'): 'remove_tests',
        }

        action_key = (source_entity, target_entity, operation)
        if action_key not in action_map:
            return ActionResult(
                success=False,
                errors=[f"Unsupported relationship: {source_entity} -> {target_entity}"]
            ).dict()

        params = {
            'entity': source_entity,
            'action': action_map[action_key],
            'issue_id': source_id,
            f'{target_entity}_ids' if target_entity != 'environment' else 'test_environments': target_ids
        }

        result = await unified_tool.execute(params)
        return result.model_dump()

    # Register quick query tool for advanced operations
    @mcp.tool(description="Execute advanced Xray queries with custom field selection")
    async def xray_query(
        entity: Literal["test", "test_execution", "test_plan"],
        operation: Literal["search", "count"],
        jql: str = None,
        project_key: str = None,
        fields: List[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Execute advanced queries with custom field selection.

        Args:
            entity: Entity type to query
            operation: Search for results or count matches
            jql: Custom JQL query
            project_key: Project filter
            fields: Specific fields to return
            limit: Maximum results

        Returns:
            Query results with selected fields
        """
        await auth.authenticate()

        params = {
            'entity': entity,
            'action': 'list',
            'jql': jql,
            'project_key': project_key,
            'limit': limit,
            'custom_fields': fields,
            'expand_details': bool(fields)
        }

        result = await unified_tool.execute(params)

        if operation == 'count' and result.success:
            # Extract count from results
            data = result.data
            if isinstance(data, dict) and 'total' in data:
                result.data = {'count': data['total']}

        return result.model_dump()

    # Register legacy tools for backward compatibility
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
        Legacy Xray test management tool for backward compatibility.

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

    # Register placeholder legacy tools for compatibility
    @mcp.tool(description="Manage Xray test sets - create and manage collections of tests")
    async def xray_test_set(action: str = "list") -> Dict[str, Any]:
        """Legacy test set management placeholder."""
        return {"message": "Test set management not yet implemented", "action": action}

    @mcp.tool(description="Manage Xray test runs - execute tests and track results")
    async def xray_test_run(action: str = "list") -> Dict[str, Any]:
        """Legacy test run management placeholder."""
        return {"message": "Test run management not yet implemented", "action": action}

    @mcp.tool(description="Manage Xray test executions - track individual test execution results")
    async def xray_test_execution(action: str = "list") -> Dict[str, Any]:
        """Legacy test execution management placeholder."""
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