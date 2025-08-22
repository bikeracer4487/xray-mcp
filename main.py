"""Main Xray MCP Server implementation using FastMCP."""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, List, Optional, Union

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
    from .errors.mcp_decorator import mcp_tool
    from .validators.tool_validators import XrayToolValidators
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
    from errors.mcp_decorator import mcp_tool
    from validators.tool_validators import XrayToolValidators


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
            All tools use MCP error decorators that provide structured error responses
            with self-correction hints, field validation, and example usage patterns.
            Errors include 'error', 'message', 'hint', 'field', 'expected', 'got',
            'retriable', and 'example_call' fields for AI self-correction.

        Complexity: O(n) where n is the number of tools registered

        Note:
            Tools are registered as closures that capture self, allowing
            access to tool class instances.
        """

        # Test Management Tools
        @self.mcp.tool()
        @mcp_tool("get_test", docs_link="TOOLSET.md#get_test")
        async def get_test(issue_id: str) -> Dict[str, Any]:
            """Retrieve a single test by issue ID.

            Supports both numeric IDs (e.g., "1162822") and Jira keys (e.g., "PROJ-123").
            Returns detailed test information including steps, test type, and Jira metadata.

            Args:
                issue_id: The Jira issue ID or key of the test to retrieve (e.g., "PROJ-123" or "1162822")

            Returns:
                Test details including steps, type, and Jira information

            Examples:
                - get_test("PROJ-123") - Retrieve test by Jira key
                - get_test("1162822") - Retrieve test by numeric ID
            """
            # Validate issue_id parameter
            validation_error = XrayToolValidators.validate_issue_id(issue_id)
            if validation_error:
                return validation_error.to_dict()
                
            return await self.test_tools.get_test(issue_id)

        @self.mcp.tool()
        @mcp_tool("get_tests", docs_link="TOOLSET.md#get_tests")
        async def get_tests(
            jql: Optional[str] = None, limit: int = 100
        ) -> Dict[str, Any]:
            """Retrieve multiple tests with optional JQL filtering.

            Searches for tests using Jira Query Language (JQL). Supports filtering by project,
            status, assignee, labels, and other test attributes. Returns paginated results.

            Args:
                jql: Optional JQL query string to filter tests (e.g., "project = PROJ AND status = Open")
                limit: Maximum number of tests to return, between 1 and 100 (default: 100)

            Returns:
                Paginated list of tests with metadata, including total count and results

            Examples:
                All tests: get_tests()
                Project tests: get_tests("project = PROJ")
                Open tests: get_tests("project = PROJ AND status = Open", limit=50)
                By assignee: get_tests("assignee = currentUser() AND project = PROJ")
                Recent tests: get_tests("created >= -7d AND project = PROJ")
            """
            # Validate limit parameter
            validation_error = XrayToolValidators.validate_limit(limit, max_limit=100)
            if validation_error:
                return validation_error.to_dict()
            
            # Validate JQL if provided
            if jql is not None:
                validation_error = XrayToolValidators.validate_jql_query(jql, "jql")
                if validation_error:
                    return validation_error.to_dict()
            
            return await self.test_tools.get_tests(jql, limit)

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
        @mcp_tool("create_test", docs_link="TOOLSET.md#create_test")
        async def create_test(
            project_key: str,
            summary: str,
            test_type: str = "Generic",
            description: Optional[str] = None,
            steps: Optional[Union[str, List[Dict[str, str]]]] = None,
            gherkin: Optional[str] = None,
            unstructured: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Create a new test in Xray with comprehensive validation.

            Creates tests of different types: Manual (step-by-step), Cucumber (BDD with Gherkin),
            or Generic (unstructured). Each test type has specific requirements for content.

            Args:
                project_key: Uppercase Jira project key (e.g., "PROJ", "TEST", "DEV")
                summary: Descriptive test title/summary
                test_type: Test type - "Manual" (requires steps), "Cucumber" (requires gherkin), "Generic" (default)
                description: Optional test description or background information
                steps: For Manual tests - JSON string or list of steps with 'action', 'data', 'result' fields
                gherkin: For Cucumber tests - Gherkin scenario text (Feature, Scenario, Given, When, Then)
                unstructured: For Generic tests - Free-form test definition

            Returns:
                Created test information including issue ID, key, and validation results

            Examples:
                Manual test: create_test("PROJ", "Login test", "Manual", steps='[{"action": "Navigate to login", "data": "", "result": "Login page loads"}]')
                Cucumber test: create_test("PROJ", "Login feature", "Cucumber", gherkin="Feature: Login\\nScenario: Successful login\\nGiven user is on login page")
                Generic test: create_test("PROJ", "API test", "Generic", unstructured="Test POST /api/login endpoint")
            """
            # Validate all parameters
            validation_error = XrayToolValidators.validate_project_key(project_key)
            if validation_error:
                return validation_error.to_dict()
                
            validation_error = XrayToolValidators.validate_test_type(test_type)
            if validation_error:
                return validation_error.to_dict()
            
            validation_error = XrayToolValidators.validate_test_steps(steps)
            if validation_error:
                return validation_error.to_dict()
            
            validation_error = XrayToolValidators.validate_gherkin_content(gherkin)
            if validation_error:
                return validation_error.to_dict()
                
            # Handle steps parameter when passed as JSON string
            if steps is not None and isinstance(steps, str):
                import json
                try:
                    steps = json.loads(steps)
                except json.JSONDecodeError as e:
                    try:
                        from .errors.mcp_errors import MCPErrorBuilder
                    except ImportError:
                        from errors.mcp_errors import MCPErrorBuilder
                    return MCPErrorBuilder.invalid_parameter(
                        field="steps",
                        expected="valid JSON string",
                        got=f"Invalid JSON: {str(e)}",
                        hint="Use proper JSON format: '[{\"action\": \"Step\", \"data\": \"Input\", \"result\": \"Expected\"}]'",
                        example_call={"tool": "create_test", "arguments": {"project_key": "PROJ", "test_type": "Manual", "steps": '[{"action": "Click login", "data": "", "result": "Page loads"}]'}}
                    ).to_dict()
            
            return await self.test_tools.create_test(
                project_key,
                summary,
                test_type,
                description,
                steps,
                gherkin,
                unstructured,
            )

        @self.mcp.tool()
        @mcp_tool("delete_test", docs_link="TOOLSET.md#delete_test")
        async def delete_test(issue_id: str) -> Dict[str, Any]:
            """Delete a test from Xray.
            
            Permanently removes a test and all its associated data.
            Use with caution as this operation cannot be undone.

            Args:
                issue_id: The Jira issue ID or key of the test to delete (e.g., "PROJ-123" or "1162822")

            Returns:
                Confirmation of deletion with status and cleanup details
                
            Example:
                delete_test("PROJ-456") -> {"status": "deleted", "issue_id": "PROJ-456"}
            """
            # Validate issue_id parameter
            validation_error = XrayToolValidators.validate_issue_id(issue_id)
            if validation_error:
                return validation_error.to_dict()
                
            return await self.test_tools.delete_test(issue_id)

        @self.mcp.tool()
        @mcp_tool("update_test", docs_link="TOOLSET.md#update_test")
        async def update_test(
            issue_id: str,
            test_type: Optional[str] = None,
            gherkin: Optional[str] = None,
            unstructured: Optional[str] = None,
            steps: Optional[Union[str, List[Dict[str, str]]]] = None,
            jira_fields: Optional[Union[str, Dict[str, Any]]] = None,
            version_id: Optional[int] = None,
        ) -> Dict[str, Any]:
            """Update various aspects of an existing test.

            Comprehensive test update method that can modify test type, content,
            steps, and Jira fields in a single operation.

            Args:
                issue_id: Jira issue ID or key (e.g., "1162822" or "TEST-123")
                test_type: New test type ("Manual", "Cucumber", "Generic")
                gherkin: New Gherkin scenario (for Cucumber tests)
                unstructured: New unstructured content (for Generic tests)
                steps: New test steps (for Manual tests) - JSON string or list of dicts
                jira_fields: Jira fields to update (e.g., {"summary": "New title"}) - JSON string or dict
                version_id: Specific test version to update

            Returns:
                Combined update results with success status, updated fields, and warnings
                
            Example:
                update_test("PROJ-123", test_type="Manual", steps='[{"action":"Login","data":"","result":"Success"}]')
            """
            # Validate issue_id parameter
            validation_error = XrayToolValidators.validate_issue_id(issue_id)
            if validation_error:
                return validation_error.to_dict()
                
            # Validate test_type if provided
            if test_type is not None:
                validation_error = XrayToolValidators.validate_test_type(test_type)
                if validation_error:
                    return validation_error.to_dict()
                    
            # Validate gherkin content if provided
            if gherkin is not None:
                validation_error = XrayToolValidators.validate_gherkin_content(gherkin)
                if validation_error:
                    return validation_error.to_dict()
                
            # Handle steps parameter when passed as JSON string
            if steps is not None and isinstance(steps, str):
                import json
                try:
                    steps = json.loads(steps)
                except json.JSONDecodeError as e:
                    try:
                        from .errors.mcp_errors import MCPErrorBuilder
                    except ImportError:
                        from errors.mcp_errors import MCPErrorBuilder
                    return MCPErrorBuilder.invalid_parameter(
                        field="steps",
                        expected="valid JSON string",
                        got=f"Invalid JSON: {str(e)}",
                        hint="Use proper JSON format: '[{\"action\": \"Step\", \"data\": \"Input\", \"result\": \"Expected\"}]'",
                        example_call={"tool": "update_test", "arguments": {"issue_id": "PROJ-123", "steps": '[{"action": "Login", "data": "", "result": "Success"}]'}}
                    ).to_dict()
            
            # Handle jira_fields parameter when passed as JSON string
            if jira_fields is not None and isinstance(jira_fields, str):
                import json
                try:
                    jira_fields = json.loads(jira_fields)
                except json.JSONDecodeError as e:
                    try:
                        from .errors.mcp_errors import MCPErrorBuilder
                    except ImportError:
                        from errors.mcp_errors import MCPErrorBuilder
                    return MCPErrorBuilder.invalid_parameter(
                        field="jira_fields",
                        expected="valid JSON object",
                        got=f"Invalid JSON: {str(e)}",
                        hint="Use proper JSON format: '{\"summary\": \"New title\", \"priority\": {\"name\": \"High\"}}'",
                        example_call={"tool": "update_test", "arguments": {"issue_id": "PROJ-123", "jira_fields": '{"summary": "Updated test title"}'}}
                    ).to_dict()
            
            # Validate steps content if provided
            if steps is not None:
                validation_error = XrayToolValidators.validate_test_steps(steps)
                if validation_error:
                    return validation_error.to_dict()
            
            return await self.test_tools.update_test(
                issue_id, test_type, gherkin, unstructured, steps, jira_fields, version_id
            )

        @self.mcp.tool()
        @mcp_tool("update_test_type", docs_link="TOOLSET.md#update_test_type")
        async def update_test_type(issue_id: str, test_type: str) -> Dict[str, Any]:
            """Update the test type of an existing test.

            DEPRECATED: Use update_test() instead for more comprehensive updates.
            This tool only changes the test type and is maintained for backward compatibility.

            Args:
                issue_id: The Jira issue ID or key of the test (e.g., "PROJ-123" or "1162822")
                test_type: New test type ("Manual", "Cucumber", "Generic")

            Returns:
                Updated test information with new test type
                
            Example:
                update_test_type("PROJ-123", "Manual") -> {"status": "updated", "test_type": "Manual"}
            """
            # Validate issue_id parameter
            validation_error = XrayToolValidators.validate_issue_id(issue_id)
            if validation_error:
                return validation_error.to_dict()
                
            # Validate test_type parameter
            validation_error = XrayToolValidators.validate_test_type(test_type)
            if validation_error:
                return validation_error.to_dict()
                
            return await self.test_tools.update_test_type(issue_id, test_type)

        # Test Execution Tools
        @self.mcp.tool()
        @mcp_tool("get_test_execution", docs_link="TOOLSET.md#get_test_execution")
        async def get_test_execution(issue_id: str) -> Dict[str, Any]:
            """Retrieve a single test execution by issue ID.
            
            Returns comprehensive test execution information including associated tests,
            execution status, environments, and metadata.

            Args:
                issue_id: The Jira issue ID or key of the test execution (e.g., "PROJ-123" or "1162822")

            Returns:
                Test execution details including associated tests, status, and execution environment
                
            Example:
                get_test_execution("PROJ-456") -> {"id": 456, "summary": "Sprint 1 Tests", "tests": [...], "status": "Open"}
            """
            # Validate issue_id parameter
            validation_error = XrayToolValidators.validate_issue_id(issue_id)
            if validation_error:
                return validation_error.to_dict()
                
            return await self.execution_tools.get_test_execution(issue_id)

        @self.mcp.tool()
        @mcp_tool("get_test_executions", docs_link="TOOLSET.md#get_test_executions")
        async def get_test_executions(
            jql: Optional[str] = None, limit: int = 100
        ) -> Dict[str, Any]:
            """Retrieve multiple test executions with optional JQL filtering.
            
            Supports complex queries to find test executions by project, status, date,
            environment, or any Jira field using JQL syntax.

            Args:
                jql: Optional JQL query to filter test executions (e.g., "project = PROJ AND status = Open")
                limit: Maximum number of test executions to return (1-100, default: 100)

            Returns:
                Paginated list of test executions with metadata including total count and pagination info
                
            Examples:
                get_test_executions() -> All test executions (up to 100)
                get_test_executions("project = PROJ AND status = Open", 50) -> Open executions in project PROJ
                get_test_executions("created >= -7d", 25) -> Recent executions from last 7 days
            """
            # Validate JQL if provided
            if jql is not None:
                validation_error = XrayToolValidators.validate_jql_query(jql)
                if validation_error:
                    return validation_error.to_dict()
                    
            # Validate limit parameter
            validation_error = XrayToolValidators.validate_limit(limit, max_limit=100)
            if validation_error:
                return validation_error.to_dict()
                
            return await self.execution_tools.get_test_executions(jql, limit)

        @self.mcp.tool()
        @mcp_tool("create_test_execution", docs_link="TOOLSET.md#create_test_execution")
        async def create_test_execution(
            project_key: str,
            summary: str,
            test_issue_ids: Optional[List[str]] = None,
            test_environments: Optional[List[str]] = None,
            description: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Create a new test execution in Xray.
            
            Creates a test execution which can contain multiple tests and track their
            execution results across different environments.

            Args:
                project_key: Jira project key where the test execution will be created (e.g., "PROJ", "TEST")
                summary: Test execution summary/title (e.g., "Sprint 3 Regression Tests")
                test_issue_ids: Optional list of test issue IDs to include (e.g., ["PROJ-123", "PROJ-456"])
                test_environments: Optional list of test environments (e.g., ["Production", "Staging"])
                description: Optional test execution description

            Returns:
                Created test execution information including issue ID, key, and included tests
                
            Examples:
                create_test_execution("PROJ", "Sprint 1 Tests") -> Basic execution
                create_test_execution("PROJ", "Regression Suite", ["PROJ-123", "PROJ-456"], ["Staging"]) -> Full execution
            """
            # Validate project_key parameter
            validation_error = XrayToolValidators.validate_project_key(project_key)
            if validation_error:
                return validation_error.to_dict()
                
            # Validate test issue IDs if provided
            if test_issue_ids is not None:
                for issue_id in test_issue_ids:
                    validation_error = XrayToolValidators.validate_issue_id(issue_id)
                    if validation_error:
                        return validation_error.to_dict()
                        
            # Validate environments if provided
            if test_environments is not None:
                for env in test_environments:
                    validation_error = XrayToolValidators.validate_environment_name(env)
                    if validation_error:
                        return validation_error.to_dict()
                
            return await self.execution_tools.create_test_execution(
                project_key, summary, test_issue_ids, test_environments, description
            )

        # DISABLED: delete_test_execution tool commented out due to Cursor's 40-tool limit
        # @self.mcp.tool()
        # async def delete_test_execution(issue_id: str) -> Dict[str, Any]:
        #     """Delete a test execution from Xray.
        #
        #     Args:
        #         issue_id: The Jira issue ID of the test execution to delete
        #
        #     Returns:
        #         Confirmation of deletion
        #     """
        #     try:
        #         return await self.execution_tools.delete_test_execution(issue_id)
        #     except Exception as e:
        #         return {"error": str(e), "type": type(e).__name__}

        @self.mcp.tool()
        @mcp_tool("add_tests_to_execution", docs_link="TOOLSET.md#add_tests_to_execution")
        async def add_tests_to_execution(
            execution_issue_id: str, test_issue_ids: List[str]
        ) -> Dict[str, Any]:
            """Add tests to an existing test execution.
            
            Adds one or more tests to an existing test execution. The tests will be
            available for execution within that test execution context.

            Args:
                execution_issue_id: The Jira issue ID or key of the test execution (e.g., "PROJ-456")
                test_issue_ids: List of test issue IDs to add (e.g., ["PROJ-123", "PROJ-789"])

            Returns:
                Information about successfully added tests, any warnings, and execution summary
                
            Example:
                add_tests_to_execution("PROJ-456", ["PROJ-123", "PROJ-789"]) -> {"added": 2, "warnings": []}
            """
            # Validate execution issue ID
            validation_error = XrayToolValidators.validate_issue_id(execution_issue_id)
            if validation_error:
                return validation_error.to_dict()
                
            # Validate all test issue IDs
            for test_id in test_issue_ids:
                validation_error = XrayToolValidators.validate_issue_id(test_id)
                if validation_error:
                    return validation_error.to_dict()
                    
            return await self.execution_tools.add_tests_to_execution(
                execution_issue_id, test_issue_ids
            )

        @self.mcp.tool()
        @mcp_tool("remove_tests_from_execution", docs_link="TOOLSET.md#remove_tests_from_execution")
        async def remove_tests_from_execution(
            execution_issue_id: str, test_issue_ids: List[str]
        ) -> Dict[str, Any]:
            """Remove tests from an existing test execution.
            
            Removes one or more tests from a test execution. This does not delete
            the tests themselves, just removes them from the execution scope.

            Args:
                execution_issue_id: The Jira issue ID or key of the test execution (e.g., "PROJ-456")
                test_issue_ids: List of test issue IDs to remove (e.g., ["PROJ-123", "PROJ-789"])

            Returns:
                Confirmation of removal with count of successfully removed tests
                
            Example:
                remove_tests_from_execution("PROJ-456", ["PROJ-123"]) -> {"removed": 1, "status": "success"}
            """
            # Validate execution issue ID
            validation_error = XrayToolValidators.validate_issue_id(execution_issue_id)
            if validation_error:
                return validation_error.to_dict()
                
            # Validate all test issue IDs
            for test_id in test_issue_ids:
                validation_error = XrayToolValidators.validate_issue_id(test_id)
                if validation_error:
                    return validation_error.to_dict()
                    
            return await self.execution_tools.remove_tests_from_execution(
                execution_issue_id, test_issue_ids
            )

        # Utility Tools
        @self.mcp.tool()
        @mcp_tool("execute_jql_query", docs_link="TOOLSET.md#execute_jql_query")
        async def execute_jql_query(
            jql: str, entity_type: str = "test", limit: int = 100
        ) -> Dict[str, Any]:
            """Execute a custom JQL query for different Xray entity types.

            Executes Jira Query Language (JQL) queries against Xray entities. Supports filtering
            by any Jira/Xray field including custom fields, dates, and relationships.

            Args:
                jql: JQL query string (e.g., "project = PROJ AND status = Open AND created >= -30d")
                entity_type: Type of entity to query - "test" or "testexecution" (default: "test")
                limit: Maximum results to return, between 1 and 100 (default: 100)

            Returns:
                Query results with metadata, pagination info, and structured entity data

            Examples:
                Tests by project: execute_jql_query("project = PROJ")
                Recent executions: execute_jql_query("created >= -7d", "testexecution")
                Failed tests: execute_jql_query("project = PROJ AND 'Test Execution Status' = FAIL", "test")
                Complex query: execute_jql_query("assignee = currentUser() AND labels = smoke AND priority = High")
            """
            # Validate JQL query
            validation_error = XrayToolValidators.validate_jql_query(jql, "jql")
            if validation_error:
                return validation_error.to_dict()
            
            # Validate entity_type
            validation_error = XrayToolValidators.validate_entity_type(entity_type)
            if validation_error:
                return validation_error.to_dict()
            
            # Validate limit
            validation_error = XrayToolValidators.validate_limit(limit, max_limit=100)
            if validation_error:
                return validation_error.to_dict()
            
            return await self.utility_tools.execute_jql_query(jql, entity_type, limit)

        @self.mcp.tool()
        @mcp_tool("validate_connection", docs_link="TOOLSET.md#validate_connection")
        async def validate_connection() -> Dict[str, Any]:
            """Test connection and authentication with Xray API.
            
            Verifies that the Xray API credentials are valid and the service is reachable.
            Use this tool to diagnose authentication or connectivity issues.

            Returns:
                Connection status, authentication information, and API health details
                
            Example:
                validate_connection() -> {"status": "connected", "authenticated": true, "api_version": "v1"}
            """
            return await self.utility_tools.validate_connection()

        # Precondition Tools
        @self.mcp.tool()
        @mcp_tool("get_preconditions", docs_link="TOOLSET.md#get_preconditions")
        async def get_preconditions(
            issue_id: str, start: int = 0, limit: int = 100
        ) -> Dict[str, Any]:
            """Retrieve preconditions for a test.
            
            Returns all preconditions associated with a test, which define
            the required state or conditions before test execution.

            Args:
                issue_id: The Jira issue ID or key of the test (e.g., "PROJ-123" or "1162822")
                start: Starting index for pagination, 0-based (default: 0)
                limit: Maximum number of preconditions to return, 1-100 (default: 100)

            Returns:
                Paginated list of preconditions with condition text, type, and metadata
                
            Example:
                get_preconditions("PROJ-123", 0, 50) -> {"preconditions": [...], "total": 5, "start": 0}
            """
            # Validate issue ID
            validation_error = XrayToolValidators.validate_issue_id(issue_id)
            if validation_error:
                return validation_error.to_dict()
                
            # Validate limit parameter
            validation_error = XrayToolValidators.validate_limit(limit, max_limit=100)
            if validation_error:
                return validation_error.to_dict()
                
            return await self.precondition_tools.get_preconditions(
                issue_id, start, limit
            )

        @self.mcp.tool()
        @mcp_tool("create_precondition", docs_link="TOOLSET.md#create_precondition")
        async def create_precondition(
            issue_id: str, precondition_input: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Create a new precondition for a test.
            
            Creates a precondition that defines required state or setup
            before a test can be executed successfully.

            Args:
                issue_id: The Jira issue ID or key of the test (e.g., "PROJ-123")
                precondition_input: Precondition data with 'condition' text and 'type' fields

            Returns:
                Created precondition information including ID and content
                
            Example:
                create_precondition("PROJ-123", {"condition": "User must be logged in", "type": "Manual"})
            """
            # Validate issue ID
            validation_error = XrayToolValidators.validate_issue_id(issue_id)
            if validation_error:
                return validation_error.to_dict()
                
            return await self.precondition_tools.create_precondition(
                issue_id, precondition_input
            )

        @self.mcp.tool()
        @mcp_tool("update_precondition", docs_link="TOOLSET.md#update_precondition")
        async def update_precondition(
            precondition_id: str, precondition_input: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Update an existing precondition.
            
            Modifies the content or properties of an existing precondition
            while preserving its associations with tests.

            Args:
                precondition_id: The unique ID of the precondition to update (e.g., "12345")
                precondition_input: Updated precondition data with 'condition' text and 'type'

            Returns:
                Updated precondition information with new content and metadata
                
            Example:
                update_precondition("12345", {"condition": "User must have admin rights", "type": "Manual"})
            """
            return await self.precondition_tools.update_precondition(
                precondition_id, precondition_input
            )

        @self.mcp.tool()
        @mcp_tool("delete_precondition", docs_link="TOOLSET.md#delete_precondition")
        async def delete_precondition(precondition_id: str) -> Dict[str, Any]:
            """Delete a precondition.
            
            Permanently removes a precondition from the system.
            Use with caution as this cannot be undone.

            Args:
                precondition_id: The unique ID of the precondition to delete (e.g., "12345")

            Returns:
                Confirmation of deletion with status information
                
            Example:
                delete_precondition("12345") -> {"status": "deleted", "precondition_id": "12345"}
            """
            return await self.precondition_tools.delete_precondition(
                precondition_id
            )

        # Test Set Tools
        @self.mcp.tool()
        @mcp_tool("get_test_set", docs_link="TOOLSET.md#get_test_set")
        async def get_test_set(issue_id: str) -> Dict[str, Any]:
            """Retrieve a single test set by issue ID.
            
            Returns detailed information about a test set including all
            associated tests and organizational metadata.

            Args:
                issue_id: The Jira issue ID or key of the test set (e.g., "PROJ-123" or "1162822")

            Returns:
                Test set details including associated tests, summary, and metadata
                
            Example:
                get_test_set("PROJ-456") -> {"id": 456, "summary": "Smoke Tests", "tests": [...], "status": "Open"}
            """
            # Validate issue ID
            validation_error = XrayToolValidators.validate_issue_id(issue_id)
            if validation_error:
                return validation_error.to_dict()
                
            return await self.testset_tools.get_test_set(issue_id)

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
        @mcp_tool("create_test_set", docs_link="TOOLSET.md#create_test_set")
        async def create_test_set(
            project_key: str,
            summary: str,
            test_issue_ids: Optional[List[str]] = None,
            description: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Create a new test set in Xray.
            
            Creates a test set to organize and group related tests for better
            management and execution planning.

            Args:
                project_key: Jira project key where the test set will be created (e.g., "PROJ", "TEST")
                summary: Test set summary/title (e.g., "Smoke Test Suite", "Regression Tests")
                test_issue_ids: Optional list of test issue IDs to include (e.g., ["PROJ-123", "PROJ-456"])
                description: Optional test set description with additional context

            Returns:
                Created test set information including issue ID, key, and included tests
                
            Examples:
                create_test_set("PROJ", "Smoke Tests") -> Basic test set
                create_test_set("PROJ", "Login Suite", ["PROJ-123", "PROJ-456"]) -> Test set with tests
            """
            # Validate project_key parameter
            validation_error = XrayToolValidators.validate_project_key(project_key)
            if validation_error:
                return validation_error.to_dict()
                
            # Validate test issue IDs if provided
            if test_issue_ids is not None:
                for issue_id in test_issue_ids:
                    validation_error = XrayToolValidators.validate_issue_id(issue_id)
                    if validation_error:
                        return validation_error.to_dict()
                        
            return await self.testset_tools.create_test_set(
                project_key, summary, test_issue_ids, description
            )

        @self.mcp.tool()
        @mcp_tool("update_test_set", docs_link="TOOLSET.md#update_test_set")
        async def update_test_set(
            issue_id: str, summary: str, description: Optional[str] = None
        ) -> Dict[str, Any]:
            """Update an existing test set.
            
            Modifies the summary, description, or other properties of a test set
            while preserving its test associations.

            Args:
                issue_id: The Jira issue ID or key of the test set (e.g., "PROJ-123")
                summary: New test set summary/title (e.g., "Updated Smoke Tests")
                description: Optional new test set description with updated context

            Returns:
                Updated test set information with new properties and metadata
                
            Example:
                update_test_set("PROJ-456", "Enhanced Smoke Tests", "Updated for v2.0") -> Updated test set
            """
            # Validate issue ID
            validation_error = XrayToolValidators.validate_issue_id(issue_id)
            if validation_error:
                return validation_error.to_dict()
                
            return await self.testset_tools.update_test_set(
                issue_id, summary, description
            )

        # DISABLED: delete_test_set tool commented out due to Cursor's 40-tool limit
        # @self.mcp.tool()
        # async def delete_test_set(issue_id: str) -> Dict[str, Any]:
        #     """Delete a test set from Xray.
        #
        #     Args:
        #         issue_id: The Jira issue ID of the test set to delete
        #
        #     Returns:
        #         Confirmation of deletion
        #     """
        #     try:
        #         return await self.testset_tools.delete_test_set(issue_id)
        #     except Exception as e:
        #         return {"error": str(e), "type": type(e).__name__}

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

        # DISABLED: delete_test_plan tool commented out due to Cursor's 40-tool limit
        # @self.mcp.tool()
        # async def delete_test_plan(issue_id: str) -> Dict[str, Any]:
        #     """Delete a test plan from Xray.
        #
        #     Args:
        #         issue_id: The Jira issue ID of the test plan to delete
        #
        #     Returns:
        #         Confirmation of deletion
        #     """
        #     try:
        #         return await self.plan_tools.delete_test_plan(issue_id)
        #     except Exception as e:
        #         return {"error": str(e), "type": type(e).__name__}

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

        # DISABLED: delete_test_run tool commented out due to Cursor's 40-tool limit
        # @self.mcp.tool()
        # async def delete_test_run(issue_id: str) -> Dict[str, Any]:
        #     """Delete a test run from Xray.
        #
        #     Args:
        #         issue_id: The Jira issue ID of the test run to delete
        #
        #     Returns:
        #         Confirmation of deletion
        #     """
        #     try:
        #         return await self.run_tools.delete_test_run(issue_id)
        #     except Exception as e:
        #         return {"error": str(e), "type": type(e).__name__}

        # Test Versioning Tools
        # DISABLED: get_test_versions tool commented out due to Cursor's 40-tool limit
        # @self.mcp.tool()
        # async def get_test_versions(issue_id: str) -> Dict[str, Any]:
        #     """Retrieve all versions of a test.
        #
        #     Args:
        #         issue_id: The Jira issue ID of the test
        #
        #     Returns:
        #         List of test versions with version details and metadata
        #     """
        #     try:
        #         return await self.versioning_tools.get_test_versions(issue_id)
        #     except Exception as e:
        #         return {"error": str(e), "type": type(e).__name__}

        # DISABLED: archive_test_version tool commented out due to Cursor's 40-tool limit
        # @self.mcp.tool()
        # async def archive_test_version(
        #     issue_id: str, version_id: int
        # ) -> Dict[str, Any]:
        #     """Archive a specific version of a test.
        #
        #     Args:
        #         issue_id: The Jira issue ID of the test
        #         version_id: The version ID to archive
        #
        #     Returns:
        #         Confirmation of archival with archived version details
        #     """
        #     try:
        #         return await self.versioning_tools.archive_test_version(
        #             issue_id, version_id
        #         )
        #     except Exception as e:
        #         return {"error": str(e), "type": type(e).__name__}

        # DISABLED: restore_test_version tool commented out due to Cursor's 40-tool limit
        # @self.mcp.tool()
        # async def restore_test_version(
        #     issue_id: str, version_id: int
        # ) -> Dict[str, Any]:
        #     """Restore an archived version of a test.
        #
        #     Args:
        #         issue_id: The Jira issue ID of the test
        #         version_id: The version ID to restore
        #
        #     Returns:
        #         Confirmation of restoration with restored version details
        #     """
        #     try:
        #         return await self.versioning_tools.restore_test_version(
        #             issue_id, version_id
        #         )
        #     except Exception as e:
        #         return {"error": str(e), "type": type(e).__name__}

        # DISABLED: create_test_version_from tool commented out due to Cursor's 40-tool limit
        # @self.mcp.tool()
        # async def create_test_version_from(
        #     issue_id: str, source_version_id: int, version_name: str
        # ) -> Dict[str, Any]:
        #     """Create a new test version from an existing version.
        #
        #     Args:
        #         issue_id: The Jira issue ID of the test
        #         source_version_id: The version ID to copy from
        #         version_name: Name for the new version
        #
        #     Returns:
        #         Created version information with details and metadata
        #     """
        #     try:
        #         return await self.versioning_tools.create_test_version_from(
        #             issue_id, source_version_id, version_name
        #         )
        #     except Exception as e:
        #         return {"error": str(e), "type": type(e).__name__}

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
                Dict with 'dataset' (object or None) and 'found' (boolean)
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
                Dict with 'datasets' key containing list of dataset objects
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
