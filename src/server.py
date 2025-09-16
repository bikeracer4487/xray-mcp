"""Simplified Xray MCP Server following FastMCP best practices."""

import os
from typing import Dict, Any, Literal, List, Optional
from dotenv import load_dotenv
from fastmcp import FastMCP
from .auth import XrayAuth
from .graphql_client import XrayGraphQLClient
from .tools.xray_tool import XrayTool

# Load environment variables
load_dotenv()


def create_server() -> FastMCP:
    """Create simplified FastMCP server with single tool registration.

    Returns:
        FastMCP: Configured server instance following FastMCP best practices

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
    mcp = FastMCP("Xray Test Management")

    # Initialize authentication and GraphQL client
    auth = XrayAuth(client_id, client_secret, base_url)
    client = XrayGraphQLClient(auth)
    xray_tool = XrayTool(client)

    # Single tool registration following FastMCP patterns
    @mcp.tool(description="Manage Xray tests, executions, plans, and runs with unified interface")
    async def xray_test(
        entity: Literal["test", "test_execution", "test_plan", "test_run"],
        action: str,
        issue_id: Optional[str] = None,
        project_key: Optional[str] = None,
        summary: Optional[str] = None,
        test_type: Optional[Literal["Manual", "Generic", "Cucumber"]] = None,
        test_issue_ids: Optional[List[str]] = None,
        test_issue_id: Optional[str] = None,  # For test run operations (singular)
        test_exec_issue_ids: Optional[List[str]] = None,  # For plan execution associations
        limit: int = 50,
        start: int = 0,
        jql: Optional[str] = None,
        description: Optional[str] = None,
        steps: Optional[List[Dict[str, str]]] = None,
        gherkin: Optional[str] = None,
        status: Optional[str] = None,
        comment: Optional[str] = None,
        test_environments: Optional[List[str]] = None,
        test_execution_id: Optional[str] = None,
        defects: Optional[List[str]] = None,
        environments: Optional[List[str]] = None,
        id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Unified Xray tool for managing all entities with FastMCP simplicity.

        Args:
            entity: Entity type (test, test_execution, test_plan, test_run)
            action: Action to perform (create, get, update_status, list, delete, etc.)
            issue_id: Issue ID for specific operations
            project_key: Jira project key for create/list operations
            summary: Summary/title for create operations
            test_type: Test type for test creation (Manual, Generic, Cucumber)
            test_issue_ids: List of test issue IDs for associations
            test_issue_id: Single test issue ID for test run operations
            test_exec_issue_ids: List of test execution IDs for plan associations
            limit: Maximum results for list operations (max 100)
            start: Starting index for pagination
            jql: Custom JQL query for filtering
            description: Additional description for entities
            steps: Test steps for Manual tests
            gherkin: Gherkin script for Cucumber tests
            status: Status for test run updates
            comment: Comment for test run updates
            test_environments: Test environments for executions
            test_execution_id: Test execution ID for test run operations
            defects: Defect list for test run operations

        Returns:
            Operation result with success status, data, warnings, and errors
        """
        # Ensure authentication before executing
        await auth.authenticate()

        # Build parameters dictionary - let managers handle validation
        params = {
            'entity': entity,
            'action': action,
            'issue_id': issue_id,
            'project_key': project_key,
            'summary': summary,
            'test_type': test_type,
            'test_issue_ids': test_issue_ids or [],
            'test_issue_id': test_issue_id,  # For test run operations (singular)
            'test_exec_issue_ids': test_exec_issue_ids or [],  # For plan execution associations
            'limit': min(limit, 100),
            'start': start,
            'jql': jql,
            'description': description,
            'steps': steps or [],
            'gherkin': gherkin,
            'status': status,
            'comment': comment,
            'test_environments': test_environments or [],
            'test_execution_id': test_execution_id,
            'defects': defects or [],
            'environments': environments or [],
            'id': id
        }

        # Remove None values to reduce payload
        params = {k: v for k, v in params.items() if v is not None}

        # Execute using xray tool
        return await xray_tool.execute(params)

    return mcp


# Alias for any existing references
create_simplified_server = create_server


if __name__ == "__main__":
    # Run the server
    server = create_server()
    # In production, you'd use uvicorn or similar to run this
    print("Simplified Xray MCP Server created successfully!")
    print("Available tools:", [tool.name for tool in server._tool_manager._tools.values()])