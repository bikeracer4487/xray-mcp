"""
MCP client wrapper for Xray MCP E2E tests.

Provides a simplified interface for interacting with the Xray MCP server
with proper error handling, response parsing, and test-specific utilities.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import httpx
from fastmcp.client import Client


class XrayTestType(Enum):
    """Test types supported by Xray."""
    MANUAL = "Manual"
    CUCUMBER = "Cucumber"
    GENERIC = "Generic"


@dataclass
class MCPResponse:
    """Response from test operations."""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    
    def __bool__(self) -> bool:
        return self.success


class XrayMCPClient:
    """Enhanced MCP client for Xray testing."""
    
    def __init__(self, server_url: str, timeout: int = 30):
        """
        Initialize MCP client.
        
        Args:
            server_url: MCP server URL
            timeout: Request timeout in seconds
        """
        self.server_url = server_url
        self.timeout = timeout
        self.client: Optional[Client] = None
        self._session: Optional[httpx.AsyncClient] = None
    
    async def connect(self):
        """Connect to MCP server."""
        self._session = httpx.AsyncClient(timeout=self.timeout)
        self.client = Client(self.server_url, session=self._session)
        await self.client.connect()
    
    async def disconnect(self):
        """Disconnect from MCP server."""
        if self.client:
            await self.client.disconnect()
        if self._session:
            await self._session.aclose()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPResponse:
        """
        Call MCP tool with error handling.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            MCPResponse with results or error information
        """
        try:
            result = await self.client.call_tool(tool_name, arguments)
            
            # Parse the response based on MCP result format
            if hasattr(result, 'content'):
                # Handle FastMCP ToolResult format
                content_list = result.content if isinstance(result.content, list) else [result.content]
                
                for item in content_list:
                    if hasattr(item, 'text'):
                        try:
                            data = json.loads(item.text)
                            return MCPResponse(success=True, data=data)
                        except json.JSONDecodeError:
                            return MCPResponse(success=True, data={"raw": item.text})
                
                # Fallback for non-text content
                return MCPResponse(success=True, data={"content": str(result.content)})
            
            elif isinstance(result, dict):
                # Direct dictionary response
                return MCPResponse(success=True, data=result)
            
            else:
                # String or other response
                try:
                    data = json.loads(str(result))
                    return MCPResponse(success=True, data=data)
                except json.JSONDecodeError:
                    return MCPResponse(success=True, data={"raw": str(result)})
        
        except Exception as e:
            return MCPResponse(success=False, data={}, error=str(e))
    
    # Test management methods
    async def create_test(
        self,
        project_key: str,
        summary: str,
        test_type: Union[XrayTestType, str] = XrayTestType.GENERIC,
        description: Optional[str] = None,
        steps: Optional[List[Dict[str, str]]] = None,
        gherkin: Optional[str] = None,
        unstructured: Optional[str] = None
    ) -> MCPResponse:
        """
        Create a new test.
        
        Args:
            project_key: Jira project key
            summary: Test summary
            test_type: Type of test to create
            description: Optional test description
            steps: Manual test steps (for Manual tests)
            gherkin: Gherkin scenario (for Cucumber tests)
            unstructured: Unstructured test definition (for Generic tests)
            
        Returns:
            MCPResponse with created test information
        """
        test_type_str = test_type.value if isinstance(test_type, XrayTestType) else test_type
        
        args = {
            "project_key": project_key,
            "summary": summary,
            "test_type": test_type_str
        }
        
        if description:
            args["description"] = description
        if steps:
            args["steps"] = steps
        if gherkin:
            args["gherkin"] = gherkin
        if unstructured:
            args["unstructured"] = unstructured
        
        return await self.call_tool("create_test", args)
    
    async def get_test(self, issue_id: str) -> MCPResponse:
        """Get test details."""
        return await self.call_tool("get_test", {"issue_id": issue_id})
    
    async def update_test(
        self,
        issue_id: str,
        test_type: Optional[str] = None,
        gherkin: Optional[str] = None,
        unstructured: Optional[str] = None,
        steps: Optional[List[Dict[str, str]]] = None,
        jira_fields: Optional[Dict[str, Any]] = None
    ) -> MCPResponse:
        """Update an existing test."""
        args = {"issue_id": issue_id}
        
        if test_type:
            args["test_type"] = test_type
        if gherkin:
            args["gherkin"] = gherkin
        if unstructured:
            args["unstructured"] = unstructured
        if steps:
            args["steps"] = steps
        if jira_fields:
            args["jira_fields"] = jira_fields
        
        return await self.call_tool("update_test", args)
    
    async def delete_test(self, issue_id: str) -> MCPResponse:
        """Delete a test."""
        return await self.call_tool("delete_test", {"issue_id": issue_id})
    
    # Test execution methods
    async def create_test_execution(
        self,
        project_key: str,
        summary: str,
        test_issue_ids: Optional[List[str]] = None,
        test_environments: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> MCPResponse:
        """Create a new test execution."""
        args = {
            "project_key": project_key,
            "summary": summary
        }
        
        if test_issue_ids:
            args["test_issue_ids"] = test_issue_ids
        if test_environments:
            args["test_environments"] = test_environments
        if description:
            args["description"] = description
        
        return await self.call_tool("create_test_execution", args)
    
    async def add_tests_to_execution(
        self,
        execution_issue_id: str,
        test_issue_ids: List[str]
    ) -> MCPResponse:
        """Add tests to an execution."""
        return await self.call_tool("add_tests_to_execution", {
            "execution_issue_id": execution_issue_id,
            "test_issue_ids": test_issue_ids
        })
    
    async def get_test_execution(self, issue_id: str) -> MCPResponse:
        """Get test execution details."""
        return await self.call_tool("get_test_execution", {"issue_id": issue_id})
    
    # Test plan methods
    async def create_test_plan(
        self,
        project_key: str,
        summary: str,
        test_issue_ids: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> MCPResponse:
        """Create a new test plan."""
        args = {
            "project_key": project_key,
            "summary": summary
        }
        
        if test_issue_ids:
            args["test_issue_ids"] = test_issue_ids
        if description:
            args["description"] = description
        
        return await self.call_tool("create_test_plan", args)
    
    # Test set methods
    async def create_test_set(
        self,
        project_key: str,
        summary: str,
        test_issue_ids: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> MCPResponse:
        """Create a new test set."""
        args = {
            "project_key": project_key,
            "summary": summary
        }
        
        if test_issue_ids:
            args["test_issue_ids"] = test_issue_ids
        if description:
            args["description"] = description
        
        return await self.call_tool("create_test_set", args)
    
    # Precondition methods
    async def create_precondition(
        self,
        issue_id: str,
        precondition_input: Dict[str, Any]
    ) -> MCPResponse:
        """Create a precondition for a test."""
        return await self.call_tool("create_precondition", {
            "issue_id": issue_id,
            "precondition_input": precondition_input
        })
    
    # Gherkin methods
    async def update_gherkin_definition(
        self,
        issue_id: str,
        gherkin_text: str
    ) -> MCPResponse:
        """Update Gherkin definition for a Cucumber test."""
        return await self.call_tool("update_gherkin_definition", {
            "issue_id": issue_id,
            "gherkin_text": gherkin_text
        })
    
    # Query and utility methods
    async def execute_jql_query(
        self,
        jql: str,
        entity_type: str = "test",
        limit: int = 100
    ) -> MCPResponse:
        """Execute a JQL query."""
        return await self.call_tool("execute_jql_query", {
            "jql": jql,
            "entity_type": entity_type,
            "limit": limit
        })
    
    async def validate_connection(self) -> MCPResponse:
        """Validate connection to Xray API."""
        return await self.call_tool("validate_connection", {})
    
    async def get_test_status(
        self,
        issue_id: str,
        environment: Optional[str] = None,
        version: Optional[str] = None,
        test_plan: Optional[str] = None
    ) -> MCPResponse:
        """Get test execution status."""
        args = {"issue_id": issue_id}
        
        if environment:
            args["environment"] = environment
        if version:
            args["version"] = version
        if test_plan:
            args["test_plan"] = test_plan
        
        return await self.call_tool("get_test_status", args)
    
    # Utility methods for tests
    def extract_issue_key(self, response: MCPResponse) -> Optional[str]:
        """Extract issue key from response."""
        if not response.success:
            return None
        
        data = response.data
        
        # Try different possible locations for issue key
        for key_field in ["key", "issueKey", "issue_key", "id"]:
            if key_field in data:
                return data[key_field]
        
        # Try nested structures
        if "issue" in data and isinstance(data["issue"], dict):
            for key_field in ["key", "issueKey", "issue_key", "id"]:
                if key_field in data["issue"]:
                    return data["issue"][key_field]
        
        return None
    
    def extract_issue_id(self, response: MCPResponse) -> Optional[str]:
        """Extract issue ID from response."""
        if not response.success:
            return None
        
        data = response.data
        
        # Try different possible locations for issue ID
        for id_field in ["id", "issueId", "issue_id", "key"]:
            if id_field in data:
                return str(data[id_field])
        
        # Try nested structures
        if "issue" in data and isinstance(data["issue"], dict):
            for id_field in ["id", "issueId", "issue_id", "key"]:
                if id_field in data["issue"]:
                    return str(data["issue"][id_field])
        
        return None
    
    def assert_success(self, response: MCPResponse, message: str = ""):
        """Assert that response was successful."""
        if not response.success:
            error_msg = f"Operation failed: {response.error}"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)
    
    def assert_contains_keys(self, response: MCPResponse, required_keys: List[str]):
        """Assert that response contains required keys."""
        self.assert_success(response)
        
        missing_keys = [key for key in required_keys if key not in response.data]
        if missing_keys:
            raise AssertionError(f"Response missing required keys: {missing_keys}")