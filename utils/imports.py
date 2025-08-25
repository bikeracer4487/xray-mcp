"""Centralized import utilities for handling both package and direct execution modes.

This module eliminates code duplication by providing a single place to handle
the dual import patterns used throughout the codebase. It automatically detects
whether the code is running as a package or in direct execution mode and
imports accordingly.
"""

import importlib
import sys
from typing import Any, Dict, List, Optional

class ImportManager:
    """Manages imports for both package and direct execution modes.
    
    This class provides a centralized way to handle the dual import patterns
    that are used throughout the codebase to support both package imports
    (when installed/imported as a package) and direct execution imports
    (when running files directly with python).
    """
    
    def __init__(self, package_name: str = ""):
        """Initialize the import manager.
        
        Args:
            package_name: Name of the current package for relative imports
        """
        self.package_name = package_name
        self._cache: Dict[str, Any] = {}
    
    def safe_import(self, package_path: str, direct_path: str) -> Any:
        """Safely import a module using package or direct path.
        
        Args:
            package_path: Relative import path (e.g., "..client")
            direct_path: Direct import path (e.g., "client")
            
        Returns:
            The imported module
            
        Raises:
            ImportError: If neither import method works
        """
        # Check cache first
        cache_key = f"{package_path}|{direct_path}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # Try package-style import first
            if package_path.startswith('.'):
                # For relative imports, we need the package context
                module = importlib.import_module(package_path, package=self.package_name)
            else:
                module = importlib.import_module(package_path)
            self._cache[cache_key] = module
            return module
        except ImportError:
            try:
                # Fall back to direct import
                module = importlib.import_module(direct_path)
                self._cache[cache_key] = module
                return module
            except ImportError as e:
                raise ImportError(f"Could not import from {package_path} or {direct_path}: {e}")
    
    def import_from(self, package_path: str, direct_path: str, names: List[str]) -> Dict[str, Any]:
        """Import specific names from a module.
        
        Args:
            package_path: Relative import path
            direct_path: Direct import path
            names: List of names to import from the module
            
        Returns:
            Dictionary mapping names to imported objects
        """
        module = self.safe_import(package_path, direct_path)
        result = {}
        for name in names:
            if hasattr(module, name):
                result[name] = getattr(module, name)
            else:
                raise ImportError(f"Cannot import name '{name}' from {package_path or direct_path}")
        return result


# Global import manager instance
_import_manager = ImportManager(__name__.split('.')[0] if '.' in __name__ else '')

def safe_import(package_path: str, direct_path: str) -> Any:
    """Convenience function for safe importing.
    
    Args:
        package_path: Relative import path (e.g., "..client")
        direct_path: Direct import path (e.g., "client")
        
    Returns:
        The imported module
    """
    return _import_manager.safe_import(package_path, direct_path)

def import_from(package_path: str, direct_path: str, *names: str) -> Dict[str, Any]:
    """Convenience function for importing specific names.
    
    Args:
        package_path: Relative import path
        direct_path: Direct import path
        names: Names to import from the module
        
    Returns:
        Dictionary mapping names to imported objects
    """
    return _import_manager.import_from(package_path, direct_path, list(names))


# Common import patterns used throughout the codebase
def get_common_imports() -> Dict[str, Any]:
    """Get commonly used imports across the codebase.
    
    Returns:
        Dictionary of commonly imported objects
    """
    imports = {}
    
    # Client imports
    try:
        client_imports = import_from("..client", "client", "XrayGraphQLClient")
        imports.update(client_imports)
    except ImportError:
        pass
    
    # Exception imports
    try:
        exception_imports = import_from(
            "..exceptions", "exceptions", 
            "GraphQLError", "ValidationError", "XrayMCPError"
        )
        imports.update(exception_imports)
    except ImportError:
        pass
    
    # Validator imports
    try:
        validator_imports = import_from(
            "..validators", "validators",
            "validate_jql", "JQLValidator", "GraphQLValidator"
        )
        imports.update(validator_imports)
    except ImportError:
        pass
    
    # Utility imports
    try:
        utils_imports = import_from(
            "..utils", "utils",
            "IssueIdResolver"
        )
        imports.update(utils_imports)
    except ImportError:
        pass
    
    # Auth imports
    try:
        auth_imports = import_from(
            "..auth", "auth",
            "XrayAuthManager"
        )
        imports.update(auth_imports)
    except ImportError:
        pass
    
    return imports


def get_xray_imports() -> Dict[str, Any]:
    """Get standard Xray MCP imports for most modules.
    
    This is a convenience function that returns the most commonly needed
    imports for Xray MCP modules.
    
    Returns:
        Dictionary containing XrayGraphQLClient, common exceptions, and validators
    """
    return get_common_imports()


def get_tool_imports() -> Dict[str, Any]:
    """Get all tool class imports for the registry.
    
    This function handles the bulk import of all tool classes needed by
    the ToolRegistrar, eliminating the need for individual import statements.
    
    Returns:
        Dictionary containing all tool classes
    """
    imports = {}
    
    # Tool module definitions
    tool_modules = {
        "TestTools": ("..tools.tests", "tools.tests"),
        "TestExecutionTools": ("..tools.executions", "tools.executions"),
        "TestPlanTools": ("..tools.plans", "tools.plans"),
        "TestRunTools": ("..tools.runs", "tools.runs"),
        "UtilityTools": ("..tools.utils", "tools.utils"),
        "PreconditionTools": ("..tools.preconditions", "tools.preconditions"),
        "TestSetTools": ("..tools.testsets", "tools.testsets"),
        "TestVersioningTools": ("..tools.versioning", "tools.versioning"),
        "CoverageTools": ("..tools.coverage", "tools.coverage"),
        "HistoryTools": ("..tools.history", "tools.history"),
        "GherkinTools": ("..tools.gherkin", "tools.gherkin"),
        "OrganizationTools": ("..tools.organization", "tools.organization"),
    }
    
    # Import each tool class
    for class_name, (package_path, direct_path) in tool_modules.items():
        try:
            tool_imports = import_from(package_path, direct_path, class_name)
            imports.update(tool_imports)
        except ImportError:
            # Continue if a tool module is missing - allows partial functionality
            pass
    
    # Also import supporting classes
    try:
        client_imports = import_from("..client", "client", "XrayGraphQLClient")
        imports.update(client_imports)
    except ImportError:
        pass
        
    try:
        decorator_imports = import_from("..errors.mcp_decorator", "errors.mcp_decorator", "mcp_tool")
        imports.update(decorator_imports)
    except ImportError:
        pass
        
    try:
        validator_imports = import_from("..validators.tool_validators", "validators.tool_validators", "XrayToolValidators")
        imports.update(validator_imports)
    except ImportError:
        pass
    
    return imports