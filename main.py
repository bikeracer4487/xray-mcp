"""Main Xray MCP Server implementation using FastMCP."""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, List, Optional

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
    from .tools.tests import TestTools
    from .tools.executions import TestExecutionTools
    from .tools.plans import TestPlanTools
    from .tools.runs import TestRunTools
    from .tools.utils import UtilityTools
    from .tools.preconditions import PreconditionTools
    from .tools.testsets import TestSetTools
    from .tools.versioning import TestVersioningTools
    from .tools.coverage import CoverageTools
    from .tools.history import HistoryTools
    from .tools.gherkin import GherkinTools
    from .tools.organization import OrganizationTools
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
    from tools.tests import TestTools
    from tools.executions import TestExecutionTools
    from tools.plans import TestPlanTools
    from tools.runs import TestRunTools
    from tools.utils import UtilityTools
    from tools.preconditions import PreconditionTools
    from tools.testsets import TestSetTools
    from tools.versioning import TestVersioningTools
    from tools.coverage import CoverageTools
    from tools.history import HistoryTools
    from tools.gherkin import GherkinTools
    from tools.organization import OrganizationTools
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
        - Instantiates all tool classes with dependency injection
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

        # Initialize tool classes with dependency injection
        self.test_tools = TestTools(self.graphql_client)
        self.execution_tools = TestExecutionTools(self.graphql_client)
        self.plan_tools = TestPlanTools(self.graphql_client)
        self.run_tools = TestRunTools(self.graphql_client)
        self.utility_tools = UtilityTools(self.graphql_client)
        self.precondition_tools = PreconditionTools(self.graphql_client)
        self.testset_tools = TestSetTools(self.graphql_client)
        self.versioning_tools = TestVersioningTools(self.graphql_client)
        self.coverage_tools = CoverageTools(self.graphql_client)
        self.history_tools = HistoryTools(self.graphql_client)
        self.gherkin_tools = GherkinTools(self.graphql_client)
        self.organization_tools = OrganizationTools(self.graphql_client)

        # Register all tools with FastMCP
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

        This method uses FastMCP's @tool decorator to register async functions
        as MCP tools. Each tool wraps calls to the appropriate tool class
        methods and handles exceptions by returning structured error responses.

        Tool Categories:
        1. Test Management Tools:
           - get_test: Retrieve single test
           - get_tests: Retrieve multiple tests with JQL
           - get_expanded_test: Get detailed test with version support
           - create_test: Create new test (Manual, Cucumber, Generic)
           - delete_test: Delete existing test
           - update_test_type: Change test type

        2. Test Execution Tools:
           - get_test_execution: Retrieve single execution
           - get_test_executions: Retrieve multiple executions
           - create_test_execution: Create new execution
           - delete_test_execution: Delete execution
           - add_tests_to_execution: Add tests to execution
           - remove_tests_from_execution: Remove tests from execution

        3. Precondition Management Tools:
           - get_preconditions: Retrieve test preconditions
           - create_precondition: Create new precondition
           - update_precondition: Update existing precondition
           - delete_precondition: Delete precondition

        4. Test Set Operations:
           - get_test_set: Retrieve single test set
           - get_test_sets: Retrieve multiple test sets
           - create_test_set: Create new test set
           - update_test_set: Update test set
           - delete_test_set: Delete test set
           - add_tests_to_set: Add tests to test set
           - remove_tests_from_set: Remove tests from test set

        5. Test Plan Operations:
           - get_test_plan: Retrieve single test plan
           - get_test_plans: Retrieve multiple test plans
           - create_test_plan: Create new test plan
           - update_test_plan: Update test plan
           - delete_test_plan: Delete test plan
           - add_tests_to_plan: Add tests to test plan
           - remove_tests_from_plan: Remove tests from test plan

        6. Test Run Management:
           - get_test_run: Retrieve single test run
           - get_test_runs: Retrieve multiple test runs
           - create_test_run: Create new test run
           - delete_test_run: Delete test run

        7. Test Versioning:
           - get_test_versions: Retrieve test versions
           - archive_test_version: Archive test version
           - restore_test_version: Restore archived version
           - create_test_version_from: Create version from existing

        8. Status & Coverage Queries:
           - get_test_status: Get test execution status
           - get_coverable_issues: Get issues that can be covered by tests

        9. Xray History & Attachments:
           - get_xray_history: Retrieve execution history
           - upload_attachment: Upload file attachment
           - delete_attachment: Delete attachment

        10. Gherkin & Unstructured Updates:
            - update_gherkin_definition: Update Gherkin scenario

        11. Folder & Dataset Management:
            - get_folder_contents: Retrieve folder contents
            - move_test_to_folder: Move test to folder
            - get_dataset: Retrieve specific dataset
            - get_datasets: Retrieve all project datasets

        12. Utility Tools:
            - execute_jql_query: Run custom JQL queries
            - validate_connection: Test API connection

        Error Handling:
            All tools catch exceptions and return:
            {"error": str(exception), "type": exception_class_name}

        Complexity: O(n) where n is the number of tools registered

        Note:
            Tools are registered as closures that capture self, allowing
            access to tool class instances.
        """

        # Test Management Tools
        @self.mcp.tool()
        async def get_test(issue_id: str) -> Dict[str, Any]:
            """Retrieve a single test by issue ID.

            Args:
                issue_id: The Jira issue ID of the test to retrieve

            Returns:
                Test details including steps, type, and Jira information
            """
            try:
                return await self.test_tools.get_test(issue_id)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
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
            try:
                return await self.test_tools.get_tests(jql, limit)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def get_expanded_test(
            issue_id: str, test_version_id: Optional[int] = None
        ) -> Dict[str, Any]:
            """Retrieve detailed information for a single test with version support.

            Args:
                issue_id: The Jira issue ID of the test
                test_version_id: Optional specific version ID of the test

            Returns:
                Detailed test information including all steps and metadata
            """
            try:
                return await self.test_tools.get_expanded_test(
                    issue_id, test_version_id
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def create_test(
            project_key: str,
            summary: str,
            test_type: str = "Generic",
            description: Optional[str] = None,
            steps: Optional[List[Dict[str, str]]] = None,
            gherkin: Optional[str] = None,
            unstructured: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Create a new test in Xray.

            Args:
                project_key: Jira project key where the test will be created
                summary: Test summary/title
                test_type: Type of test (Generic, Manual, Cucumber, etc.)
                description: Optional test description
                steps: List of test steps for Manual tests (each step should have 'action', 'data', 'result')
                gherkin: Gherkin scenario for Cucumber tests
                unstructured: Unstructured test definition for Generic tests

            Returns:
                Created test information including issue ID and key
            """
            try:
                return await self.test_tools.create_test(
                    project_key,
                    summary,
                    test_type,
                    description,
                    steps,
                    gherkin,
                    unstructured,
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def delete_test(issue_id: str) -> Dict[str, Any]:
            """Delete a test from Xray.

            Args:
                issue_id: The Jira issue ID of the test to delete

            Returns:
                Confirmation of deletion
            """
            try:
                return await self.test_tools.delete_test(issue_id)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def update_test_type(issue_id: str, test_type: str) -> Dict[str, Any]:
            """Update the test type of an existing test.

            Args:
                issue_id: The Jira issue ID of the test
                test_type: New test type (Generic, Manual, Cucumber, etc.)

            Returns:
                Updated test information
            """
            try:
                return await self.test_tools.update_test_type(issue_id, test_type)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        # Test Execution Tools
        @self.mcp.tool()
        async def get_test_execution(issue_id: str) -> Dict[str, Any]:
            """Retrieve a single test execution by issue ID.

            Args:
                issue_id: The Jira issue ID of the test execution

            Returns:
                Test execution details including associated tests
            """
            try:
                return await self.execution_tools.get_test_execution(issue_id)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def get_test_executions(
            jql: Optional[str] = None, limit: int = 100
        ) -> Dict[str, Any]:
            """Retrieve multiple test executions with optional JQL filtering.

            Args:
                jql: Optional JQL query to filter test executions
                limit: Maximum number of test executions to return (max 100)

            Returns:
                Paginated list of test executions matching the criteria
            """
            try:
                return await self.execution_tools.get_test_executions(jql, limit)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def create_test_execution(
            project_key: str,
            summary: str,
            test_issue_ids: Optional[List[str]] = None,
            test_environments: Optional[List[str]] = None,
            description: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Create a new test execution in Xray.

            Args:
                project_key: Jira project key where the test execution will be created
                summary: Test execution summary/title
                test_issue_ids: Optional list of test issue IDs to include
                test_environments: Optional list of test environments
                description: Optional test execution description

            Returns:
                Created test execution information including issue ID and key
            """
            try:
                return await self.execution_tools.create_test_execution(
                    project_key, summary, test_issue_ids, test_environments, description
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def delete_test_execution(issue_id: str) -> Dict[str, Any]:
            """Delete a test execution from Xray.

            Args:
                issue_id: The Jira issue ID of the test execution to delete

            Returns:
                Confirmation of deletion
            """
            try:
                return await self.execution_tools.delete_test_execution(issue_id)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def add_tests_to_execution(
            execution_issue_id: str, test_issue_ids: List[str]
        ) -> Dict[str, Any]:
            """Add tests to an existing test execution.

            Args:
                execution_issue_id: The Jira issue ID of the test execution
                test_issue_ids: List of test issue IDs to add to the execution

            Returns:
                Information about added tests and any warnings
            """
            try:
                return await self.execution_tools.add_tests_to_execution(
                    execution_issue_id, test_issue_ids
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def remove_tests_from_execution(
            execution_issue_id: str, test_issue_ids: List[str]
        ) -> Dict[str, Any]:
            """Remove tests from an existing test execution.

            Args:
                execution_issue_id: The Jira issue ID of the test execution
                test_issue_ids: List of test issue IDs to remove from the execution

            Returns:
                Confirmation of removal
            """
            try:
                return await self.execution_tools.remove_tests_from_execution(
                    execution_issue_id, test_issue_ids
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        # Utility Tools
        @self.mcp.tool()
        async def execute_jql_query(
            jql: str, entity_type: str = "test", limit: int = 100
        ) -> Dict[str, Any]:
            """Execute a custom JQL query for different entity types.

            Args:
                jql: JQL query string
                entity_type: Type of entity to query (test, testexecution)
                limit: Maximum number of results to return (max 100)

            Returns:
                Query results matching the JQL criteria
            """
            try:
                return await self.utility_tools.execute_jql_query(
                    jql, entity_type, limit
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def validate_connection() -> Dict[str, Any]:
            """Test connection and authentication with Xray API.

            Returns:
                Connection status and authentication information
            """
            try:
                return await self.utility_tools.validate_connection()
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        # Precondition Tools
        @self.mcp.tool()
        async def get_preconditions(
            issue_id: str, start: int = 0, limit: int = 100
        ) -> Dict[str, Any]:
            """Retrieve preconditions for a test.

            Args:
                issue_id: The Jira issue ID of the test
                start: Starting index for pagination (0-based)
                limit: Maximum number of preconditions to return (max 100)

            Returns:
                Paginated list of preconditions for the test
            """
            try:
                return await self.precondition_tools.get_preconditions(
                    issue_id, start, limit
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def create_precondition(
            issue_id: str, precondition_input: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Create a new precondition for a test.

            Args:
                issue_id: The Jira issue ID of the test
                precondition_input: Precondition data containing condition and type information

            Returns:
                Created precondition information
            """
            try:
                return await self.precondition_tools.create_precondition(
                    issue_id, precondition_input
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def update_precondition(
            precondition_id: str, precondition_input: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Update an existing precondition.

            Args:
                precondition_id: The ID of the precondition to update
                precondition_input: Updated precondition data

            Returns:
                Updated precondition information
            """
            try:
                return await self.precondition_tools.update_precondition(
                    precondition_id, precondition_input
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def delete_precondition(precondition_id: str) -> Dict[str, Any]:
            """Delete a precondition.

            Args:
                precondition_id: The ID of the precondition to delete

            Returns:
                Confirmation of deletion
            """
            try:
                return await self.precondition_tools.delete_precondition(
                    precondition_id
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        # Test Set Tools
        @self.mcp.tool()
        async def get_test_set(issue_id: str) -> Dict[str, Any]:
            """Retrieve a single test set by issue ID.

            Args:
                issue_id: The Jira issue ID of the test set

            Returns:
                Test set details including associated tests
            """
            try:
                return await self.testset_tools.get_test_set(issue_id)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def get_test_sets(
            jql: Optional[str] = None, limit: int = 100
        ) -> Dict[str, Any]:
            """Retrieve multiple test sets with optional JQL filtering.

            Args:
                jql: Optional JQL query to filter test sets
                limit: Maximum number of test sets to return (max 100)

            Returns:
                Paginated list of test sets matching the criteria
            """
            try:
                return await self.testset_tools.get_test_sets(jql, limit)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def create_test_set(
            project_key: str,
            summary: str,
            test_issue_ids: Optional[List[str]] = None,
            description: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Create a new test set in Xray.

            Args:
                project_key: Jira project key where the test set will be created
                summary: Test set summary/title
                test_issue_ids: Optional list of test issue IDs to include
                description: Optional test set description

            Returns:
                Created test set information including issue ID and key
            """
            try:
                return await self.testset_tools.create_test_set(
                    project_key, summary, test_issue_ids, description
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def update_test_set(
            issue_id: str, summary: str, description: Optional[str] = None
        ) -> Dict[str, Any]:
            """Update an existing test set.

            Args:
                issue_id: The Jira issue ID of the test set
                summary: New test set summary/title
                description: Optional new test set description

            Returns:
                Updated test set information
            """
            try:
                return await self.testset_tools.update_test_set(
                    issue_id, summary, description
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def delete_test_set(issue_id: str) -> Dict[str, Any]:
            """Delete a test set from Xray.

            Args:
                issue_id: The Jira issue ID of the test set to delete

            Returns:
                Confirmation of deletion
            """
            try:
                return await self.testset_tools.delete_test_set(issue_id)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def add_tests_to_set(
            set_issue_id: str, test_issue_ids: List[str]
        ) -> Dict[str, Any]:
            """Add tests to an existing test set.

            Args:
                set_issue_id: The Jira issue ID of the test set
                test_issue_ids: List of test issue IDs to add to the set

            Returns:
                Information about added tests and any warnings
            """
            try:
                return await self.testset_tools.add_tests_to_set(
                    set_issue_id, test_issue_ids
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def remove_tests_from_set(
            set_issue_id: str, test_issue_ids: List[str]
        ) -> Dict[str, Any]:
            """Remove tests from an existing test set.

            Args:
                set_issue_id: The Jira issue ID of the test set
                test_issue_ids: List of test issue IDs to remove from the set

            Returns:
                Confirmation of removal
            """
            try:
                return await self.testset_tools.remove_tests_from_set(
                    set_issue_id, test_issue_ids
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        # Test Plan Tools
        @self.mcp.tool()
        async def get_test_plan(issue_id: str) -> Dict[str, Any]:
            """Retrieve a single test plan by issue ID.

            Args:
                issue_id: The Jira issue ID of the test plan

            Returns:
                Test plan details including associated tests
            """
            try:
                return await self.plan_tools.get_test_plan(issue_id)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def get_test_plans(
            jql: Optional[str] = None, limit: int = 100
        ) -> Dict[str, Any]:
            """Retrieve multiple test plans with optional JQL filtering.

            Args:
                jql: Optional JQL query to filter test plans
                limit: Maximum number of test plans to return (max 100)

            Returns:
                Paginated list of test plans matching the criteria
            """
            try:
                return await self.plan_tools.get_test_plans(jql, limit)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def create_test_plan(
            project_key: str,
            summary: str,
            test_issue_ids: Optional[List[str]] = None,
            description: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Create a new test plan in Xray.

            Args:
                project_key: Jira project key where the test plan will be created
                summary: Test plan summary/title
                test_issue_ids: Optional list of test issue IDs to include
                description: Optional test plan description

            Returns:
                Created test plan information including issue ID and key
            """
            try:
                return await self.plan_tools.create_test_plan(
                    project_key, summary, test_issue_ids, description
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def update_test_plan(
            issue_id: str, summary: str, description: Optional[str] = None
        ) -> Dict[str, Any]:
            """Update an existing test plan.

            Args:
                issue_id: The Jira issue ID of the test plan
                summary: New test plan summary/title
                description: Optional new test plan description

            Returns:
                Updated test plan information
            """
            try:
                return await self.plan_tools.update_test_plan(
                    issue_id, summary, description
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def delete_test_plan(issue_id: str) -> Dict[str, Any]:
            """Delete a test plan from Xray.

            Args:
                issue_id: The Jira issue ID of the test plan to delete

            Returns:
                Confirmation of deletion
            """
            try:
                return await self.plan_tools.delete_test_plan(issue_id)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def add_tests_to_plan(
            plan_issue_id: str, test_issue_ids: List[str]
        ) -> Dict[str, Any]:
            """Add tests to an existing test plan.

            Args:
                plan_issue_id: The Jira issue ID of the test plan
                test_issue_ids: List of test issue IDs to add to the plan

            Returns:
                Information about added tests and any warnings
            """
            try:
                return await self.plan_tools.add_tests_to_plan(
                    plan_issue_id, test_issue_ids
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def remove_tests_from_plan(
            plan_issue_id: str, test_issue_ids: List[str]
        ) -> Dict[str, Any]:
            """Remove tests from an existing test plan.

            Args:
                plan_issue_id: The Jira issue ID of the test plan
                test_issue_ids: List of test issue IDs to remove from the plan

            Returns:
                Confirmation of removal
            """
            try:
                return await self.plan_tools.remove_tests_from_plan(
                    plan_issue_id, test_issue_ids
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        # Test Run Tools
        @self.mcp.tool()
        async def get_test_run(issue_id: str) -> Dict[str, Any]:
            """Retrieve a single test run by issue ID.

            Args:
                issue_id: The Jira issue ID of the test run

            Returns:
                Test run details including associated tests and execution status
            """
            try:
                return await self.run_tools.get_test_run(issue_id)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def get_test_runs(
            jql: Optional[str] = None, limit: int = 100
        ) -> Dict[str, Any]:
            """Retrieve multiple test runs with optional JQL filtering.

            Args:
                jql: Optional JQL query to filter test runs
                limit: Maximum number of test runs to return (max 100)

            Returns:
                Paginated list of test runs matching the criteria
            """
            try:
                return await self.run_tools.get_test_runs(jql, limit)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def create_test_run(
            project_key: str,
            summary: str,
            test_environments: Optional[List[str]] = None,
            description: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Create a new test run in Xray.

            Args:
                project_key: Jira project key where the test run will be created
                summary: Test run summary/title
                test_environments: Optional list of test environments
                description: Optional test run description

            Returns:
                Created test run information including issue ID and key
            """
            try:
                return await self.run_tools.create_test_run(
                    project_key, summary, test_environments, description
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def delete_test_run(issue_id: str) -> Dict[str, Any]:
            """Delete a test run from Xray.

            Args:
                issue_id: The Jira issue ID of the test run to delete

            Returns:
                Confirmation of deletion
            """
            try:
                return await self.run_tools.delete_test_run(issue_id)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        # Test Versioning Tools
        @self.mcp.tool()
        async def get_test_versions(issue_id: str) -> Dict[str, Any]:
            """Retrieve all versions of a test.

            Args:
                issue_id: The Jira issue ID of the test

            Returns:
                List of test versions with version details and metadata
            """
            try:
                return await self.versioning_tools.get_test_versions(issue_id)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def archive_test_version(
            issue_id: str, version_id: int
        ) -> Dict[str, Any]:
            """Archive a specific version of a test.

            Args:
                issue_id: The Jira issue ID of the test
                version_id: The version ID to archive

            Returns:
                Confirmation of archival with archived version details
            """
            try:
                return await self.versioning_tools.archive_test_version(
                    issue_id, version_id
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def restore_test_version(
            issue_id: str, version_id: int
        ) -> Dict[str, Any]:
            """Restore an archived version of a test.

            Args:
                issue_id: The Jira issue ID of the test
                version_id: The version ID to restore

            Returns:
                Confirmation of restoration with restored version details
            """
            try:
                return await self.versioning_tools.restore_test_version(
                    issue_id, version_id
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def create_test_version_from(
            issue_id: str, source_version_id: int, version_name: str
        ) -> Dict[str, Any]:
            """Create a new test version from an existing version.

            Args:
                issue_id: The Jira issue ID of the test
                source_version_id: The version ID to copy from
                version_name: Name for the new version

            Returns:
                Created version information with details and metadata
            """
            try:
                return await self.versioning_tools.create_test_version_from(
                    issue_id, source_version_id, version_name
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        # Coverage Tools
        @self.mcp.tool()
        async def get_test_status(
            issue_id: str,
            environment: Optional[str] = None,
            version: Optional[str] = None,
            test_plan: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Get test execution status for a specific test.

            Args:
                issue_id: The Jira issue ID of the test
                environment: Optional test environment to filter by
                version: Optional version to filter by
                test_plan: Optional test plan issue ID to filter by

            Returns:
                Test execution status and coverage information
            """
            try:
                return await self.coverage_tools.get_test_status(
                    issue_id, environment, version, test_plan
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def get_coverable_issues(
            jql: Optional[str] = None, limit: int = 100
        ) -> Dict[str, Any]:
            """Retrieve issues that can be covered by tests.

            Args:
                jql: Optional JQL query to filter coverable issues
                limit: Maximum number of issues to return (max 100)

            Returns:
                Paginated list of coverable issues with coverage information
            """
            try:
                return await self.coverage_tools.get_coverable_issues(jql, limit)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        # History Tools
        @self.mcp.tool()
        async def get_xray_history(
            issue_id: str,
            test_plan_id: Optional[str] = None,
            test_env_id: Optional[str] = None,
            start: int = 0,
            limit: int = 100,
        ) -> Dict[str, Any]:
            """Retrieve Xray execution history for a test.

            Args:
                issue_id: The Jira issue ID of the test
                test_plan_id: Optional test plan issue ID to filter history
                test_env_id: Optional test environment ID to filter history
                start: Starting index for pagination (0-based)
                limit: Maximum number of history entries to return (max 100)

            Returns:
                Paginated list of execution history entries
            """
            try:
                return await self.history_tools.get_xray_history(
                    issue_id, test_plan_id, test_env_id, start, limit
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def upload_attachment(
            step_id: str, file: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Upload an attachment to a test step.

            Args:
                step_id: The ID of the test step to attach the file to
                file: File information containing filename, content, mimeType, and optional description

            Returns:
                Details of the uploaded attachment
            """
            try:
                return await self.history_tools.upload_attachment(step_id, file)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def delete_attachment(attachment_id: str) -> Dict[str, Any]:
            """Delete an attachment from Xray.

            Args:
                attachment_id: The ID of the attachment to delete

            Returns:
                Confirmation of deletion
            """
            try:
                return await self.history_tools.delete_attachment(attachment_id)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        # Gherkin Tools
        @self.mcp.tool()
        async def update_gherkin_definition(
            issue_id: str, gherkin_text: str
        ) -> Dict[str, Any]:
            """Update the Gherkin scenario definition for a Cucumber test.

            Args:
                issue_id: The Jira issue ID of the Cucumber test
                gherkin_text: The new Gherkin scenario content in standard format

            Returns:
                Updated test information with validation results
            """
            try:
                return await self.gherkin_tools.update_gherkin_definition(
                    issue_id, gherkin_text
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        # Organization Tools
        @self.mcp.tool()
        async def get_folder_contents(
            project_id: str, folder_path: str = "/"
        ) -> Dict[str, Any]:
            """Retrieve contents of a test repository folder.

            Args:
                project_id: The project ID where the folder exists
                folder_path: The path of the folder (defaults to root "/")

            Returns:
                Folder details and contents including tests and subfolders
            """
            try:
                return await self.organization_tools.get_folder_contents(
                    project_id, folder_path
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def move_test_to_folder(
            issue_id: str, folder_path: str
        ) -> Dict[str, Any]:
            """Move a test to a different folder in the test repository.

            Args:
                issue_id: The Jira issue ID of the test to move
                folder_path: The path of the destination folder (e.g., "/Component/UI")

            Returns:
                Confirmation of move with previous and new folder information
            """
            try:
                return await self.organization_tools.move_test_to_folder(
                    issue_id, folder_path
                )
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def get_dataset(test_issue_id: str) -> Dict[str, Any]:
            """Retrieve a specific dataset for data-driven testing.

            Args:
                test_issue_id: The test issue ID to retrieve dataset for

            Returns:
                Dataset details including parameters, data, and associated context
            """
            try:
                return await self.organization_tools.get_dataset(test_issue_id)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        async def get_datasets(test_issue_ids: List[str]) -> Dict[str, Any]:
            """Retrieve datasets for multiple tests.

            Args:
                test_issue_ids: List of test issue IDs to retrieve datasets for

            Returns:
                List of dataset objects with parameters and data rows
            """
            try:
                return await self.organization_tools.get_datasets(test_issue_ids)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}

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
        # Create server from environment variables (XRAY_CLIENT_ID, XRAY_CLIENT_SECRET)
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

        # Create server and expose only the mcp instance for FastMCP
        # FastMCP will handle initialization and running
        mcp = create_server_from_env().mcp
    except Exception:
        # Graceful fallback when environment variables are missing
        # Creates a non-functional placeholder to avoid import errors
        logging.warning(
            "Environment variables not set. Please configure XRAY_CLIENT_ID and XRAY_CLIENT_SECRET."
        )
        mcp = FastMCP("Xray MCP Server - Not Configured")
