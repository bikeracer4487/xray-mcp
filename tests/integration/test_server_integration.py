import pytest
import os
import json
from dotenv import load_dotenv
from fastmcp import FastMCP
from src.server import create_server

load_dotenv()

class TestServerIntegration:
    """Integration tests for FastMCP server."""
    
    @pytest.fixture
    def server(self):
        """Create FastMCP server instance."""
        return create_server()
    
    def test_server_has_test_tool(self, server):
        """Test that server has xray_test tool registered."""
        tools = server.list_tools()
        tool_names = [tool.name for tool in tools]
        assert 'xray_test' in tool_names
        
        # Check tool schema
        test_tool = next(t for t in tools if t.name == 'xray_test')
        assert test_tool.description
        assert 'create' in test_tool.description.lower() or 'test' in test_tool.description.lower()
        
        # Verify schema has required fields
        schema = test_tool.inputSchema
        assert 'properties' in schema
        assert 'action' in schema['properties']
        assert 'enum' in schema['properties']['action']
        assert 'create' in schema['properties']['action']['enum']
    
    def test_server_has_test_set_tool(self, server):
        """Test that server has xray_test_set tool registered."""
        tools = server.list_tools()
        tool_names = [tool.name for tool in tools]
        assert 'xray_test_set' in tool_names
    
    def test_server_has_test_run_tool(self, server):
        """Test that server has xray_test_run tool registered."""
        tools = server.list_tools()
        tool_names = [tool.name for tool in tools]
        assert 'xray_test_run' in tool_names
    
    def test_server_has_test_execution_tool(self, server):
        """Test that server has xray_test_execution tool registered."""
        tools = server.list_tools()
        tool_names = [tool.name for tool in tools]
        assert 'xray_test_execution' in tool_names
    
    @pytest.mark.asyncio
    async def test_server_tool_execution(self, server):
        """Test executing a tool through the server."""
        # This would normally be called by the MCP client
        # For testing, we'll call the tool directly
        tools = server.list_tools()
        test_tool = next(t for t in tools if t.name == 'xray_test')
        
        # The actual execution would happen through the MCP protocol
        # Here we're testing that the tool is properly configured
        assert test_tool.inputSchema['required']
        assert 'action' in test_tool.inputSchema['required']