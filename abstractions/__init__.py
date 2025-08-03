"""Abstraction layer for Xray MCP Server.

This module provides abstractions and interfaces to reduce coupling,
improve testability, and standardize tool implementations.
"""

from .base import BaseTool, ToolInterface
from .repository import Repository, GraphQLRepository, CachedRepository
from .decorators import tool_error_handler, validate_required, log_execution, retry
from .factory import ToolFactory, create_tool_registry

__all__ = [
    "BaseTool",
    "ToolInterface",
    "Repository",
    "GraphQLRepository",
    "CachedRepository",
    "tool_error_handler",
    "validate_required",
    "log_execution",
    "retry",
    "ToolFactory",
    "create_tool_registry"
]