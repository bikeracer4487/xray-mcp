"""Main module with standardized error handling.

This version demonstrates how the standardized error handling system
eliminates repetitive try/except blocks while maintaining consistency.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastmcp import FastMCP
from pydantic import BaseModel

# Import error handling
from errors import async_error_handler, ErrorContext

# Import other components
from auth import XrayAuthManager
from client import XrayGraphQLClient
from config import XrayConfig
from tools import TestTools, TestPlans, TestRuns, TestExecutions, UtilityTools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Dependencies(BaseModel):
    """Dependencies for the Xray MCP server."""

    xray_client_id: str
    xray_client_secret: str
    xray_base_url: str = "https://xray.cloud.getxray.app"


class XrayMCPServerWithErrorHandling:
    """Xray MCP Server with standardized error handling.

    This implementation shows how error handling decorators eliminate
    repetitive try/except blocks while maintaining consistency.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = "https://xray.cloud.getxray.app",
    ):
        """Initialize the server with configuration."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url

        # Initialize MCP server
        self.mcp = FastMCP(
            name="xray-mcp-server",
            dependencies=[
                Dependencies(
                    xray_client_id=client_id,
                    xray_client_secret=client_secret,
                    xray_base_url=base_url,
                )
            ],
        )

        # Initialize components
        self.auth_manager = XrayAuthManager(client_id, client_secret, base_url)
        self.graphql_client = XrayGraphQLClient(self.auth_manager, base_url)

        # Initialize tools
        self.test_tools = TestTools(self.graphql_client)
        self.test_plans = TestPlans(self.graphql_client)
        self.test_runs = TestRuns(self.graphql_client)
        self.test_executions = TestExecutions(self.graphql_client)
        self.utility_tools = UtilityTools(self.graphql_client)

        # Register tools with standardized error handling
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all tools with standardized error handling.

        This method demonstrates how the error handling decorator
        eliminates the need for repetitive try/except blocks.
        """
        # Test Management Tools - with standardized error handling

        @self.mcp.tool
        @async_error_handler(operation="get_test")
        async def get_test(issue_id: str) -> Dict[str, Any]:
            """Retrieve detailed information for a single test.

            Args:
                issue_id: The Jira issue ID of the test

            Returns:
                Test details including steps, type, and Jira information
            """
            return await self.test_tools.get_test(issue_id)

        @self.mcp.tool
        @async_error_handler(operation="get_tests")
        async def get_tests(
            jql: Optional[str] = None, limit: int = 100
        ) -> Dict[str, Any]:
            """Retrieve multiple tests with optional JQL filtering.

            Args:
                jql: Optional JQL query to filter tests
                limit: Maximum number of tests to return (max 100)

            Returns:
                Paginated list of tests matching the criteria
            """
            return await self.test_tools.get_tests(jql, limit)

        @self.mcp.tool
        @async_error_handler(operation="get_expanded_test")
        async def get_expanded_test(
            issue_id: str, test_version_id: Optional[int] = None
        ) -> Dict[str, Any]:
            """Retrieve detailed information for a single test with version support.

            Args:
                issue_id: The Jira issue ID of the test
                test_version_id: Optional specific version ID of the test

            Returns:
                Test details including steps, type, and Jira information
            """
            return await self.test_tools.get_expanded_test(issue_id, test_version_id)

        @self.mcp.tool
        @async_error_handler(operation="create_test")
        async def create_test(
            project_key: str,
            summary: str,
            test_type: str,
            description: Optional[str] = None,
            labels: Optional[list] = None,
            components: Optional[list] = None,
            steps: Optional[list] = None,
            gherkin: Optional[str] = None,
            unstructured: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Create a new test case in Xray.

            Args:
                project_key: Jira project key where the test will be created
                summary: Test summary/title
                test_type: Type of test (Manual, Cucumber, or Generic)
                description: Optional test description
                labels: Optional list of Jira labels
                components: Optional list of Jira components
                steps: For Manual tests - list of test steps
                gherkin: For Cucumber tests - Gherkin content
                unstructured: For Generic tests - Unstructured content

            Returns:
                Created test information including issue ID and key
            """
            return await self.test_tools.create_test(
                project_key=project_key,
                summary=summary,
                test_type=test_type,
                description=description,
                labels=labels,
                components=components,
                steps=steps,
                gherkin=gherkin,
                unstructured=unstructured,
            )

        @self.mcp.tool
        @async_error_handler(operation="update_test")
        async def update_test(
            issue_id: str,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            labels: Optional[list] = None,
            components: Optional[list] = None,
            steps: Optional[list] = None,
            gherkin: Optional[str] = None,
            unstructured: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Update an existing test case.

            Args:
                issue_id: The Jira issue ID of the test to update
                summary: New test summary/title
                description: New test description
                labels: New list of Jira labels
                components: New list of Jira components
                steps: For Manual tests - updated test steps
                gherkin: For Cucumber tests - updated Gherkin content
                unstructured: For Generic tests - updated unstructured content

            Returns:
                Updated test information
            """
            return await self.test_tools.update_test(
                issue_id=issue_id,
                summary=summary,
                description=description,
                labels=labels,
                components=components,
                steps=steps,
                gherkin=gherkin,
                unstructured=unstructured,
            )

        # Test Plan Tools - all with standardized error handling

        @self.mcp.tool
        @async_error_handler(operation="get_test_plan")
        async def get_test_plan(issue_id: str) -> Dict[str, Any]:
            """Retrieve detailed information for a single test plan.

            Args:
                issue_id: The Jira issue ID of the test plan

            Returns:
                Test plan details including associated tests
            """
            return await self.test_plans.get_test_plan(issue_id)

        @self.mcp.tool
        @async_error_handler(operation="get_test_plans")
        async def get_test_plans(
            jql: Optional[str] = None, limit: int = 100
        ) -> Dict[str, Any]:
            """Retrieve multiple test plans with optional JQL filtering.

            Args:
                jql: Optional JQL query to filter test plans
                limit: Maximum number of test plans to return (max 100)

            Returns:
                Paginated list of test plans
            """
            return await self.test_plans.get_test_plans(jql, limit)

        # Test Run Tools

        @self.mcp.tool
        @async_error_handler(operation="get_test_run")
        async def get_test_run(issue_id: str) -> Dict[str, Any]:
            """Retrieve detailed information for a single test run.

            Args:
                issue_id: The Jira issue ID of the test run

            Returns:
                Test run details including execution status
            """
            return await self.test_runs.get_test_run(issue_id)

        @self.mcp.tool
        @async_error_handler(operation="get_test_runs")
        async def get_test_runs(
            jql: Optional[str] = None, limit: int = 100
        ) -> Dict[str, Any]:
            """Retrieve multiple test runs with optional JQL filtering.

            Args:
                jql: Optional JQL query to filter test runs
                limit: Maximum number of test runs to return (max 100)

            Returns:
                Paginated list of test runs
            """
            return await self.test_runs.get_test_runs(jql, limit)

        # Test Execution Tools

        @self.mcp.tool
        @async_error_handler(operation="get_test_execution")
        async def get_test_execution(test_exec_issue_id: str) -> Dict[str, Any]:
            """Retrieve information about a test execution.

            Args:
                test_exec_issue_id: The Jira issue ID of the test execution

            Returns:
                Test execution details
            """
            return await self.test_executions.get_test_execution(test_exec_issue_id)

        @self.mcp.tool
        @async_error_handler(operation="get_test_executions")
        async def get_test_executions(
            jql: Optional[str] = None, limit: int = 100
        ) -> Dict[str, Any]:
            """Retrieve multiple test executions with optional JQL filtering.

            Args:
                jql: Optional JQL query to filter test executions
                limit: Maximum number of test executions to return (max 100)

            Returns:
                Paginated list of test executions
            """
            return await self.test_executions.get_test_executions(jql, limit)

        @self.mcp.tool
        @async_error_handler(operation="get_test_run_details")
        async def get_test_run_details(
            test_exec_issue_id: str, test_issue_id: str
        ) -> Dict[str, Any]:
            """Get execution details for a specific test within a test execution.

            Args:
                test_exec_issue_id: The test execution issue ID
                test_issue_id: The test issue ID

            Returns:
                Detailed execution information for the specific test
            """
            return await self.test_executions.get_test_run_details(
                test_exec_issue_id, test_issue_id
            )

        @self.mcp.tool
        @async_error_handler(operation="update_test_run_status")
        async def update_test_run_status(
            test_exec_issue_id: str,
            test_issue_id: str,
            status: str,
            comment: Optional[str] = None,
            defects: Optional[list] = None,
            evidence: Optional[list] = None,
            actual_results: Optional[list] = None,
        ) -> Dict[str, Any]:
            """Update the execution status of a test within a test execution.

            Args:
                test_exec_issue_id: The test execution issue ID
                test_issue_id: The test issue ID
                status: New status (PASS, FAIL, TODO, EXECUTING, ABORTED)
                comment: Optional execution comment
                defects: Optional list of defect issue IDs
                evidence: Optional list of evidence items
                actual_results: Optional actual results for test steps

            Returns:
                Updated test run information
            """
            return await self.test_executions.update_test_run_status(
                test_exec_issue_id=test_exec_issue_id,
                test_issue_id=test_issue_id,
                status=status,
                comment=comment,
                defects=defects,
                evidence=evidence,
                actual_results=actual_results,
            )

        # Utility Tools

        @self.mcp.tool
        @async_error_handler(operation="search_jira_issues")
        async def search_jira_issues(
            jql: str, fields: Optional[list] = None, limit: int = 50
        ) -> Dict[str, Any]:
            """Search for Jira issues using JQL with field selection.

            Args:
                jql: JQL query to search for issues
                fields: Optional list of fields to return
                limit: Maximum number of results (max 100)

            Returns:
                List of Jira issues matching the query
            """
            return await self.utility_tools.search_jira_issues(jql, fields, limit)

        @self.mcp.tool
        @async_error_handler(operation="get_jira_projects")
        async def get_jira_projects(limit: int = 50) -> Dict[str, Any]:
            """Retrieve list of available Jira projects.

            Args:
                limit: Maximum number of projects to return

            Returns:
                List of accessible Jira projects
            """
            return await self.utility_tools.get_jira_projects(limit)

        @self.mcp.tool
        @async_error_handler(operation="export_test_cases")
        async def export_test_cases(
            jql: str,
            export_format: str = "json",
            include_steps: bool = True,
            include_attachments: bool = False,
        ) -> Dict[str, Any]:
            """Export test cases based on JQL query.

            Args:
                jql: JQL query to select test cases
                export_format: Export format (json, csv, xlsx)
                include_steps: Whether to include test steps
                include_attachments: Whether to include attachments

            Returns:
                Exported test case data in requested format
            """
            return await self.utility_tools.export_test_cases(
                jql=jql,
                export_format=export_format,
                include_steps=include_steps,
                include_attachments=include_attachments,
            )

        logger.info("All tools registered with standardized error handling")

    async def serve(self) -> None:
        """Start the MCP server."""
        logger.info("Starting Xray MCP Server with standardized error handling")
        logger.info(f"Server configured for: {self.base_url}")

        # Log available tools
        tool_count = len(
            [
                attr
                for attr in dir(self.mcp)
                if hasattr(getattr(self.mcp, attr), "_tool")
            ]
        )
        logger.info(f"Registered {tool_count} tools with error handling")

        await self.mcp.serve()


def create_server_from_env() -> XrayMCPServerWithErrorHandling:
    """Create server instance from environment variables.

    Returns:
        Configured server instance
    """
    client_id = os.environ.get("XRAY_CLIENT_ID")
    client_secret = os.environ.get("XRAY_CLIENT_SECRET")
    base_url = os.environ.get("XRAY_BASE_URL", "https://xray.cloud.getxray.app")

    if not client_id or not client_secret:
        raise ValueError(
            "XRAY_CLIENT_ID and XRAY_CLIENT_SECRET environment variables are required"
        )

    return XrayMCPServerWithErrorHandling(client_id, client_secret, base_url)


# Example showing the code reduction:
# Before (repeated 15+ times):
# @self.mcp.tool
# async def tool_name(...):
#     try:
#         return await self.tool_class.method(...)
#     except Exception as e:
#         return {"error": str(e), "type": type(e).__name__}
#
# After (with error handling decorator):
# @self.mcp.tool
# @async_error_handler(operation="tool_name")
# async def tool_name(...):
#     return await self.tool_class.method(...)
#
# This eliminates 3 lines of boilerplate per tool while providing:
# - Consistent error format
# - Proper error categorization
# - Automatic logging
# - Optional stack traces
# - Context tracking


if __name__ == "__main__":
    import asyncio

    server = create_server_from_env()
    asyncio.run(server.serve())
