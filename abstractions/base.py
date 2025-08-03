"""Base interfaces and abstract classes for tools.

This module defines the contracts that all tool implementations must follow,
ensuring consistency and making it easier to test and extend the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Protocol, runtime_checkable


@runtime_checkable
class ToolInterface(Protocol):
    """Protocol defining the interface that all tools must implement.
    
    This protocol ensures consistency across tool implementations and
    makes it easier to create mock implementations for testing.
    """
    
    @property
    def name(self) -> str:
        """Return the name of the tool."""
        ...
    
    @property
    def description(self) -> str:
        """Return a description of what the tool does."""
        ...


class BaseTool(ABC):
    """Abstract base class for all tool implementations.
    
    This class provides common functionality and enforces a consistent
    interface for all tools in the system. It helps reduce code duplication
    and ensures all tools follow the same patterns.
    
    Attributes:
        repository: The repository instance for data access
        name: The name of the tool
        description: A description of what the tool does
    """
    
    def __init__(self, repository: 'Repository'):
        """Initialize the tool with a repository.
        
        Args:
            repository: Repository instance for data access
        """
        self.repository = repository
        self._name = self.__class__.__name__
        self._description = self.__doc__ or "No description available"
    
    @property
    def name(self) -> str:
        """Return the name of the tool."""
        return self._name
    
    @property
    def description(self) -> str:
        """Return a description of what the tool does."""
        return self._description
    
    async def validate_input(self, **kwargs) -> None:
        """Validate input parameters before processing.
        
        This method should be overridden by subclasses to provide
        specific validation logic. By default, it does nothing.
        
        Args:
            **kwargs: The input parameters to validate
            
        Raises:
            ValidationError: If validation fails
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool's main functionality.
        
        This method must be implemented by all concrete tool classes.
        It should contain the main business logic of the tool.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Dict containing the tool's results
            
        Raises:
            Exception: Tool-specific exceptions
        """
        pass
    
    async def __call__(self, **kwargs) -> Dict[str, Any]:
        """Make the tool callable, with validation.
        
        This method provides a consistent interface for calling tools,
        ensuring validation happens before execution.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Dict containing the tool's results
        """
        await self.validate_input(**kwargs)
        return await self.execute(**kwargs)