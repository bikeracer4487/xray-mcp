"""Factory pattern for creating and registering tools.

This module provides a factory that simplifies the process of creating
tool instances and registering them with the MCP server, eliminating
code duplication in main.py.
"""

from typing import Dict, Any, Callable, Type, Optional
import inspect
from functools import wraps

from .base import BaseTool
from .repository import Repository
from .decorators import tool_error_handler


class ToolFactory:
    """Factory for creating and registering tools with MCP.

    This factory eliminates the repetitive try/except blocks in main.py
    by providing a standardized way to register tools with automatic
    error handling.
    """

    def __init__(self, mcp_server: Any, repository: Repository):
        """Initialize the factory.

        Args:
            mcp_server: The MCP server instance
            repository: Repository instance for data access
        """
        self.mcp = mcp_server
        self.repository = repository
        self._tools: Dict[str, BaseTool] = {}

    def register_tool_class(
        self, tool_class: Type[BaseTool], name: Optional[str] = None
    ) -> None:
        """Register all methods of a tool class as MCP tools.

        This method introspects the tool class and automatically registers
        all public async methods (excluding execute and validate_input) as
        MCP tools with standardized error handling.

        Args:
            tool_class: The tool class to register
            name: Optional name prefix for the tools
        """
        # Create tool instance
        tool_instance = tool_class(self.repository)
        tool_name = name or tool_instance.name

        # Store the tool instance
        self._tools[tool_name] = tool_instance

        # Get all public methods that should be exposed as tools
        for method_name in dir(tool_instance):
            # Skip private methods and special methods
            if method_name.startswith("_"):
                continue

            # Skip base class methods that shouldn't be exposed
            if method_name in ["execute", "validate_input", "name", "description"]:
                continue

            method = getattr(tool_instance, method_name)

            # Only register async methods
            if inspect.iscoroutinefunction(method):
                # Create MCP tool name
                mcp_tool_name = f"{tool_name.lower()}_{method_name}"

                # Register the method as an MCP tool
                self._register_method(mcp_tool_name, method)

    def _register_method(self, tool_name: str, method: Callable) -> None:
        """Register a single method as an MCP tool.

        Args:
            tool_name: Name for the MCP tool
            method: The method to register
        """
        # Get method signature for parameter information
        sig = inspect.signature(method)

        # Create wrapper function with standardized error handling
        @wraps(method)
        async def tool_wrapper(**kwargs):
            """Auto-generated MCP tool wrapper."""
            try:
                # If the method is already decorated with tool_error_handler,
                # it will handle its own errors
                return await method(**kwargs)
            except Exception as e:
                # Fallback error handling
                return {"error": str(e), "type": type(e).__name__, "tool": tool_name}

        # Copy docstring and signature
        tool_wrapper.__doc__ = method.__doc__
        tool_wrapper.__name__ = tool_name

        # Register with MCP
        self.mcp.tool(tool_wrapper)

    def register_legacy_tool(
        self, name: str, tool_instance: Any, method_name: str, doc: Optional[str] = None
    ) -> None:
        """Register a legacy tool that doesn't use the BaseTool interface.

        This method provides backward compatibility for existing tools
        that haven't been refactored to use the abstraction layer yet.

        Args:
            name: Name for the MCP tool
            tool_instance: The tool instance
            method_name: Name of the method to call
            doc: Optional documentation string
        """
        method = getattr(tool_instance, method_name)

        @wraps(method)
        @self.mcp.tool
        async def legacy_wrapper(**kwargs):
            """Legacy tool wrapper."""
            try:
                return await method(**kwargs)
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__, "tool": name}

        # Set name and documentation
        legacy_wrapper.__name__ = name
        if doc:
            legacy_wrapper.__doc__ = doc
        elif hasattr(method, "__doc__"):
            legacy_wrapper.__doc__ = method.__doc__

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a registered tool instance by name.

        Args:
            name: The tool name

        Returns:
            The tool instance or None if not found
        """
        return self._tools.get(name)

    def list_tools(self) -> Dict[str, str]:
        """List all registered tools with their descriptions.

        Returns:
            Dictionary mapping tool names to descriptions
        """
        return {name: tool.description for name, tool in self._tools.items()}


def create_tool_registry(mcp_server: Any, repository: Repository) -> ToolFactory:
    """Create a tool registry with standard configuration.

    This is a convenience function for creating a properly configured
    tool factory instance.

    Args:
        mcp_server: The MCP server instance
        repository: Repository instance for data access

    Returns:
        Configured ToolFactory instance
    """
    return ToolFactory(mcp_server, repository)
