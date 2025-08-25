"""Tool registration system for Xray MCP server.

This module provides a clean, modular approach to registering MCP tools,
breaking down the massive _register_tools method into manageable components
organized by functional areas.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from fastmcp import FastMCP

# Centralized import handling
try:
    from ..utils.imports import get_tool_imports
    tool_imports = get_tool_imports()
    
    # Extract all needed classes
    TestTools = tool_imports['TestTools']
    TestExecutionTools = tool_imports['TestExecutionTools']
    TestPlanTools = tool_imports['TestPlanTools']
    TestRunTools = tool_imports['TestRunTools']
    UtilityTools = tool_imports['UtilityTools']
    PreconditionTools = tool_imports['PreconditionTools']
    TestSetTools = tool_imports['TestSetTools']
    TestVersioningTools = tool_imports['TestVersioningTools']
    CoverageTools = tool_imports['CoverageTools']
    HistoryTools = tool_imports['HistoryTools']
    GherkinTools = tool_imports['GherkinTools']
    OrganizationTools = tool_imports['OrganizationTools']
    XrayGraphQLClient = tool_imports['XrayGraphQLClient']
    mcp_tool = tool_imports['mcp_tool']
    XrayToolValidators = tool_imports['XrayToolValidators']
except ImportError:
    # Fallback for direct execution
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
    from client import XrayGraphQLClient
    from errors.mcp_decorator import mcp_tool
    from validators.tool_validators import XrayToolValidators


class ToolRegistrar:
    """Manages registration of MCP tools organized by functional category.
    
    This class breaks down the massive tool registration process into
    smaller, manageable methods organized by functionality, improving
    maintainability and testability.
    
    Attributes:
        mcp (FastMCP): The FastMCP instance to register tools with
        client (XrayGraphQLClient): GraphQL client for API communication
        validators (XrayToolValidators): Parameter validators
    """

    def __init__(self, mcp: FastMCP, client: XrayGraphQLClient):
        """Initialize the tool registrar.
        
        Args:
            mcp: FastMCP instance for tool registration
            client: GraphQL client for API communication
        """
        self.mcp = mcp
        self.client = client
        self.validators = XrayToolValidators()
        
        # Initialize tool instances
        self.test_tools = TestTools(client)
        self.execution_tools = TestExecutionTools(client)
        self.plan_tools = TestPlanTools(client)
        self.run_tools = TestRunTools(client)
        self.utility_tools = UtilityTools(client)
        self.precondition_tools = PreconditionTools(client)
        self.testset_tools = TestSetTools(client)
        self.versioning_tools = TestVersioningTools(client)
        self.coverage_tools = CoverageTools(client)
        self.history_tools = HistoryTools(client)
        self.gherkin_tools = GherkinTools(client)
        self.organization_tools = OrganizationTools(client)

    def register_all_tools(self):
        """Register all MCP tools organized by category."""
        try:
            self.register_test_management_tools()
            self.register_test_execution_tools()
            self.register_utility_tools()
            self.register_precondition_tools()
            self.register_test_set_tools()
            self.register_test_plan_tools()
            self.register_test_run_tools()
            self.register_coverage_and_history_tools()
            self.register_gherkin_tools()
            self.register_organization_tools()
            
            logging.info("Successfully registered all MCP tools")
        except Exception as e:
            logging.error(f"Failed to register tools: {e}")
            raise

    def register_test_management_tools(self):
        """Register core test management tools (CRUD operations)."""
        
        @mcp_tool("get_test", docs_link="TOOLSET.md#get_test")
        async def get_test(
            issue_id: str,
        ) -> Dict[str, Any]:
            """Retrieve a single test by issue ID."""
            try:
                return await self.test_tools.get_test(issue_id)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("get_tests", docs_link="TOOLSET.md#get_tests")
        async def get_tests(
            jql: Optional[str] = None,
            limit: int = 100,
        ) -> Dict[str, Any]:
            """Retrieve multiple tests with optional JQL filtering."""
            try:
                validation_error = self.validators.validate_limit(limit)
                if validation_error:
                    return validation_error.to_dict()
                return await self.test_tools.get_tests(jql, limit)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("get_expanded_test")
        async def get_expanded_test(
            issue_id: str,
            test_version_id: Optional[int] = None,
        ) -> Dict[str, Any]:
            """Retrieve detailed information for a single test with version support."""
            try:
                return await self.test_tools.get_expanded_test(issue_id, test_version_id)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("create_test", docs_link="TOOLSET.md#create_test")
        async def create_test(
            project_key: str,
            summary: str,
            test_type: str = "Generic",
            description: Optional[str] = None,
            steps: Union[str, List[Dict[str, str]], None] = None,
            gherkin: Optional[str] = None,
            unstructured: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Create a new test in Xray with comprehensive validation."""
            try:
                # Validate project key
                validation_error = self.validators.validate_project_key(project_key)
                if validation_error:
                    return validation_error.to_dict()
                
                # Validate test type
                validation_error = self.validators.validate_test_type(test_type)
                if validation_error:
                    return validation_error.to_dict()
                    
                return await self.test_tools.create_test(
                    project_key, summary, test_type, description, steps, gherkin, unstructured
                )
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("delete_test", docs_link="TOOLSET.md#delete_test")
        async def delete_test(
            issue_id: str,
        ) -> Dict[str, Any]:
            """Delete a test from Xray."""
            try:
                return await self.test_tools.delete_test(issue_id)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("update_test", docs_link="TOOLSET.md#update_test")
        async def update_test(
            issue_id: str,
            test_type: Optional[str] = None,
            gherkin: Optional[str] = None,
            unstructured: Optional[str] = None,
            steps: Union[str, List[Dict[str, str]], None] = None,
            jira_fields: Union[str, Dict[str, Any], None] = None,
            version_id: Optional[int] = None,
        ) -> Dict[str, Any]:
            """Update various aspects of an existing test."""
            try:
                # Validate test type if provided
                if test_type:
                    validation_error = self.validators.validate_test_type(test_type)
                    if validation_error:
                        return validation_error.to_dict()
                        
                return await self.test_tools.update_test(
                    issue_id, test_type, gherkin, unstructured, steps, jira_fields, version_id
                )
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("update_test_type", docs_link="TOOLSET.md#update_test_type")
        async def update_test_type(
            issue_id: str,
            test_type: str,
        ) -> Dict[str, Any]:
            """Update the test type of an existing test."""
            try:
                validation_error = self.validators.validate_test_type(test_type)
                if validation_error:
                    return validation_error.to_dict()
                    
                return await self.test_tools.update_test_type(issue_id, test_type)
            except Exception as e:
                return {"error": str(e)}

        # Register the tools with FastMCP
        for tool_func in [get_test, get_tests, get_expanded_test, create_test, 
                         delete_test, update_test, update_test_type]:
            self.mcp.tool(tool_func.__name__)(tool_func)

    def register_test_execution_tools(self):
        """Register test execution management tools."""
        
        @mcp_tool("get_test_execution", docs_link="TOOLSET.md#get_test_execution")
        async def get_test_execution(
            issue_id: str,
        ) -> Dict[str, Any]:
            """Retrieve a single test execution by issue ID."""
            try:
                return await self.execution_tools.get_test_execution(issue_id)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("get_test_executions", docs_link="TOOLSET.md#get_test_executions")
        async def get_test_executions(
            jql: Optional[str] = None,
            limit: int = 100,
        ) -> Dict[str, Any]:
            """Retrieve multiple test executions with optional JQL filtering."""
            try:
                validation_error = self.validators.validate_limit(limit)
                if validation_error:
                    return validation_error.to_dict()
                return await self.execution_tools.get_test_executions(jql, limit)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("create_test_execution", docs_link="TOOLSET.md#create_test_execution")
        async def create_test_execution(
            project_key: str,
            summary: str,
            test_issue_ids: Optional[List[str]] = None,
            test_environments: Optional[List[str]] = None,
            description: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Create a new test execution in Xray."""
            try:
                validation_error = self.validators.validate_project_key(project_key)
                if validation_error:
                    return validation_error.to_dict()
                    
                return await self.execution_tools.create_test_execution(
                    project_key, summary, test_issue_ids, test_environments, description
                )
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("add_tests_to_execution", docs_link="TOOLSET.md#add_tests_to_execution")
        async def add_tests_to_execution(
            execution_issue_id: str,
            test_issue_ids: List[str],
        ) -> Dict[str, Any]:
            """Add tests to an existing test execution."""
            try:
                return await self.execution_tools.add_tests_to_execution(
                    execution_issue_id, test_issue_ids
                )
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("remove_tests_from_execution", docs_link="TOOLSET.md#remove_tests_from_execution")
        async def remove_tests_from_execution(
            execution_issue_id: str,
            test_issue_ids: List[str],
        ) -> Dict[str, Any]:
            """Remove tests from an existing test execution."""
            try:
                return await self.execution_tools.remove_tests_from_execution(
                    execution_issue_id, test_issue_ids
                )
            except Exception as e:
                return {"error": str(e)}

        # Register the tools
        for tool_func in [get_test_execution, get_test_executions, create_test_execution,
                         add_tests_to_execution, remove_tests_from_execution]:
            self.mcp.tool(tool_func.__name__)(tool_func)

    def register_utility_tools(self):
        """Register utility and validation tools."""
        
        @mcp_tool("execute_jql_query", docs_link="TOOLSET.md#execute_jql_query")
        async def execute_jql_query(
            jql: str,
            entity_type: str = "test",
            limit: int = 100,
        ) -> Dict[str, Any]:
            """Execute a custom JQL query for different Xray entity types."""
            try:
                validation_error = self.validators.validate_limit(limit)
                if validation_error:
                    return validation_error.to_dict()
                return await self.utility_tools.execute_jql_query(jql, entity_type, limit)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("validate_connection", docs_link="TOOLSET.md#validate_connection")
        async def validate_connection() -> Dict[str, Any]:
            """Test connection and authentication with Xray API."""
            try:
                return await self.utility_tools.validate_connection()
            except Exception as e:
                return {"error": str(e)}

        # Register the tools
        for tool_func in [execute_jql_query, validate_connection]:
            self.mcp.tool(tool_func.__name__)(tool_func)

    def register_precondition_tools(self):
        """Register precondition management tools."""
        
        @mcp_tool("get_preconditions", docs_link="TOOLSET.md#get_preconditions")
        async def get_preconditions(
            issue_id: str,
            start: int = 0,
            limit: int = 100,
        ) -> Dict[str, Any]:
            """Retrieve preconditions for a test."""
            try:
                validation_error = self.validators.validate_limit(limit)
                if validation_error:
                    return validation_error.to_dict()
                return await self.precondition_tools.get_preconditions(issue_id, start, limit)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("create_precondition", docs_link="TOOLSET.md#create_precondition")
        async def create_precondition(
            issue_id: str,
            precondition_input: Dict[str, Any],
        ) -> Dict[str, Any]:
            """Create a new precondition for a test."""
            try:
                return await self.precondition_tools.create_precondition(issue_id, precondition_input)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("update_precondition", docs_link="TOOLSET.md#update_precondition")
        async def update_precondition(
            precondition_id: str,
            precondition_input: Dict[str, Any],
        ) -> Dict[str, Any]:
            """Update an existing precondition."""
            try:
                return await self.precondition_tools.update_precondition(precondition_id, precondition_input)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("delete_precondition", docs_link="TOOLSET.md#delete_precondition")
        async def delete_precondition(
            precondition_id: str,
        ) -> Dict[str, Any]:
            """Delete a precondition."""
            try:
                return await self.precondition_tools.delete_precondition(precondition_id)
            except Exception as e:
                return {"error": str(e)}

        # Register the tools
        for tool_func in [get_preconditions, create_precondition, update_precondition, delete_precondition]:
            self.mcp.tool(tool_func.__name__)(tool_func)

    def register_test_set_tools(self):
        """Register test set management tools."""
        
        @mcp_tool("get_test_set", docs_link="TOOLSET.md#get_test_set")
        async def get_test_set(
            issue_id: str,
        ) -> Dict[str, Any]:
            """Retrieve a single test set by issue ID."""
            try:
                return await self.testset_tools.get_test_set(issue_id)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("get_test_sets")
        async def get_test_sets(
            jql: Optional[str] = None,
            limit: int = 100,
        ) -> Dict[str, Any]:
            """Retrieve multiple test sets with optional JQL filtering."""
            try:
                validation_error = self.validators.validate_limit(limit)
                if validation_error:
                    return validation_error.to_dict()
                return await self.testset_tools.get_test_sets(jql, limit)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("create_test_set", docs_link="TOOLSET.md#create_test_set")
        async def create_test_set(
            project_key: str,
            summary: str,
            test_issue_ids: Optional[List[str]] = None,
            description: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Create a new test set in Xray."""
            try:
                validation_error = self.validators.validate_project_key(project_key)
                if validation_error:
                    return validation_error.to_dict()
                return await self.testset_tools.create_test_set(
                    project_key, summary, test_issue_ids, description
                )
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("update_test_set", docs_link="TOOLSET.md#update_test_set")
        async def update_test_set(
            issue_id: str,
            summary: str,
            description: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Update an existing test set."""
            try:
                return await self.testset_tools.update_test_set(issue_id, summary, description)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("add_tests_to_set")
        async def add_tests_to_set(
            set_issue_id: str,
            test_issue_ids: List[str],
        ) -> Dict[str, Any]:
            """Add tests to an existing test set."""
            try:
                return await self.testset_tools.add_tests_to_set(set_issue_id, test_issue_ids)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("remove_tests_from_set")
        async def remove_tests_from_set(
            set_issue_id: str,
            test_issue_ids: List[str],
        ) -> Dict[str, Any]:
            """Remove tests from an existing test set."""
            try:
                return await self.testset_tools.remove_tests_from_set(set_issue_id, test_issue_ids)
            except Exception as e:
                return {"error": str(e)}

        # Register the tools
        for tool_func in [get_test_set, get_test_sets, create_test_set, update_test_set,
                         add_tests_to_set, remove_tests_from_set]:
            self.mcp.tool(tool_func.__name__)(tool_func)

    def register_test_plan_tools(self):
        """Register test plan management tools."""
        
        @mcp_tool("get_test_plan")
        async def get_test_plan(
            issue_id: str,
        ) -> Dict[str, Any]:
            """Retrieve a single test plan by issue ID."""
            try:
                return await self.plan_tools.get_test_plan(issue_id)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("get_test_plans")
        async def get_test_plans(
            jql: Optional[str] = None,
            limit: int = 100,
        ) -> Dict[str, Any]:
            """Retrieve multiple test plans with optional JQL filtering."""
            try:
                validation_error = self.validators.validate_limit(limit)
                if validation_error:
                    return validation_error.to_dict()
                return await self.plan_tools.get_test_plans(jql, limit)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("create_test_plan")
        async def create_test_plan(
            project_key: str,
            summary: str,
            test_issue_ids: Optional[List[str]] = None,
            description: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Create a new test plan in Xray."""
            try:
                validation_error = self.validators.validate_project_key(project_key)
                if validation_error:
                    return validation_error.to_dict()
                return await self.plan_tools.create_test_plan(
                    project_key, summary, test_issue_ids, description
                )
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("update_test_plan")
        async def update_test_plan(
            issue_id: str,
            summary: str,
            description: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Update an existing test plan."""
            try:
                return await self.plan_tools.update_test_plan(issue_id, summary, description)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("add_tests_to_plan")
        async def add_tests_to_plan(
            plan_issue_id: str,
            test_issue_ids: List[str],
        ) -> Dict[str, Any]:
            """Add tests to an existing test plan."""
            try:
                return await self.plan_tools.add_tests_to_plan(plan_issue_id, test_issue_ids)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("remove_tests_from_plan")
        async def remove_tests_from_plan(
            plan_issue_id: str,
            test_issue_ids: List[str],
        ) -> Dict[str, Any]:
            """Remove tests from an existing test plan."""
            try:
                return await self.plan_tools.remove_tests_from_plan(plan_issue_id, test_issue_ids)
            except Exception as e:
                return {"error": str(e)}

        # Register the tools
        for tool_func in [get_test_plan, get_test_plans, create_test_plan, update_test_plan,
                         add_tests_to_plan, remove_tests_from_plan]:
            self.mcp.tool(tool_func.__name__)(tool_func)

    def register_test_run_tools(self):
        """Register test run management tools."""
        
        @mcp_tool("get_test_run")
        async def get_test_run(
            issue_id: str,
        ) -> Dict[str, Any]:
            """Retrieve a single test run by issue ID."""
            try:
                return await self.run_tools.get_test_run(issue_id)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("get_test_runs")
        async def get_test_runs(
            jql: Optional[str] = None,
            limit: int = 100,
        ) -> Dict[str, Any]:
            """Retrieve multiple test runs with optional JQL filtering."""
            try:
                validation_error = self.validators.validate_limit(limit)
                if validation_error:
                    return validation_error.to_dict()
                return await self.run_tools.get_test_runs(jql, limit)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("create_test_run")
        async def create_test_run(
            project_key: str,
            summary: str,
            test_environments: Optional[List[str]] = None,
            description: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Create a new test run in Xray."""
            try:
                validation_error = self.validators.validate_project_key(project_key)
                if validation_error:
                    return validation_error.to_dict()
                return await self.run_tools.create_test_run(
                    project_key, summary, test_environments, description
                )
            except Exception as e:
                return {"error": str(e)}

        # Register the tools
        for tool_func in [get_test_run, get_test_runs, create_test_run]:
            self.mcp.tool(tool_func.__name__)(tool_func)

    def register_coverage_and_history_tools(self):
        """Register coverage and history tools."""
        
        @mcp_tool("get_test_status")
        async def get_test_status(
            issue_id: str,
            environment: Optional[str] = None,
            version: Optional[str] = None,
            test_plan: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Get test execution status for a specific test."""
            try:
                return await self.coverage_tools.get_test_status(issue_id, environment, version, test_plan)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("get_coverable_issues")
        async def get_coverable_issues(
            jql: Optional[str] = None,
            limit: int = 100,
        ) -> Dict[str, Any]:
            """Retrieve issues that can be covered by tests."""
            try:
                validation_error = self.validators.validate_limit(limit)
                if validation_error:
                    return validation_error.to_dict()
                return await self.coverage_tools.get_coverable_issues(jql, limit)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("get_xray_history")
        async def get_xray_history(
            issue_id: str,
            test_plan_id: Optional[str] = None,
            test_env_id: Optional[str] = None,
            start: int = 0,
            limit: int = 100,
        ) -> Dict[str, Any]:
            """Retrieve Xray execution history for a test."""
            try:
                validation_error = self.validators.validate_limit(limit)
                if validation_error:
                    return validation_error.to_dict()
                return await self.history_tools.get_xray_history(
                    issue_id, test_plan_id, test_env_id, start, limit
                )
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("upload_attachment")
        async def upload_attachment(
            step_id: str,
            file: Dict[str, Any],
        ) -> Dict[str, Any]:
            """Upload an attachment to a test step."""
            try:
                return await self.history_tools.upload_attachment(step_id, file)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("delete_attachment")
        async def delete_attachment(
            attachment_id: str,
        ) -> Dict[str, Any]:
            """Delete an attachment from Xray."""
            try:
                return await self.history_tools.delete_attachment(attachment_id)
            except Exception as e:
                return {"error": str(e)}

        # Register the tools
        for tool_func in [get_test_status, get_coverable_issues, get_xray_history,
                         upload_attachment, delete_attachment]:
            self.mcp.tool(tool_func.__name__)(tool_func)

    def register_gherkin_tools(self):
        """Register Gherkin/BDD tools."""
        
        @mcp_tool("update_gherkin_definition")
        async def update_gherkin_definition(
            issue_id: str,
            gherkin_text: str,
        ) -> Dict[str, Any]:
            """Update the Gherkin scenario definition for a Cucumber test."""
            try:
                return await self.gherkin_tools.update_gherkin_definition(issue_id, gherkin_text)
            except Exception as e:
                return {"error": str(e)}

        # Register the tools
        self.mcp.tool("update_gherkin_definition")(update_gherkin_definition)

    def register_organization_tools(self):
        """Register organization and folder management tools."""
        
        @mcp_tool("get_folder_contents")
        async def get_folder_contents(
            project_id: str,
            folder_path: str = "/",
        ) -> Dict[str, Any]:
            """Retrieve contents of a test repository folder."""
            try:
                return await self.organization_tools.get_folder_contents(project_id, folder_path)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("move_test_to_folder")
        async def move_test_to_folder(
            issue_id: str,
            folder_path: str,
        ) -> Dict[str, Any]:
            """Move a test to a different folder in the test repository."""
            try:
                return await self.organization_tools.move_test_to_folder(issue_id, folder_path)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("get_dataset")
        async def get_dataset(
            test_issue_id: str,
        ) -> Dict[str, Any]:
            """Retrieve a specific dataset for data-driven testing."""
            try:
                return await self.organization_tools.get_dataset(test_issue_id)
            except Exception as e:
                return {"error": str(e)}

        @mcp_tool("get_datasets")
        async def get_datasets(
            test_issue_ids: List[str],
        ) -> Dict[str, Any]:
            """Retrieve datasets for multiple tests."""
            try:
                return await self.organization_tools.get_datasets(test_issue_ids)
            except Exception as e:
                return {"error": str(e)}

        # Register the tools
        for tool_func in [get_folder_contents, move_test_to_folder, get_dataset, get_datasets]:
            self.mcp.tool(tool_func.__name__)(tool_func)