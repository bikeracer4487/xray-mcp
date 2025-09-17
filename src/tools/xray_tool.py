"""Simplified Xray tool using manager pattern."""

from typing import Dict, Any, Union, List
from ..graphql_client import XrayGraphQLClient
from ..managers import TestManager, ExecutionManager, PlanManager, RunManager


class XrayTool:
    """Simplified Xray tool using focused manager classes."""

    def __init__(self, client: XrayGraphQLClient):
        """Initialize tool with managers.

        Args:
            client: Authenticated XrayGraphQLClient instance
        """
        self.client = client

        # Initialize managers
        self.managers = {
            'test': TestManager(client),
            'test_execution': ExecutionManager(client),
            'test_plan': PlanManager(client),
            'test_run': RunManager(client)
        }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute operation using appropriate manager.

        Args:
            params: Dictionary containing entity, action, and action-specific parameters

        Returns:
            Dictionary containing operation results

        Raises:
            ValueError: If entity or action is invalid
        """
        entity = params.get('entity')
        action = params.get('action')

        if not entity:
            return self._create_error_result("Missing required parameter: entity")
        if not action:
            return self._create_error_result("Missing required parameter: action")

        if entity not in self.managers:
            valid_entities = list(self.managers.keys())
            return self._create_error_result([
                f"Invalid entity: '{entity}'",
                f"Valid entities are: {', '.join(valid_entities)}",
                f"Example: entity='test' for test operations"
            ])

        manager = self.managers[entity]

        # Simple dispatch using getattr
        if hasattr(manager, action):
            try:
                return await getattr(manager, action)(params)
            except Exception as e:
                return self._create_error_result(f"Failed to execute {action} on {entity}: {str(e)}")
        else:
            available_actions = [method for method in dir(manager) if not method.startswith('_') and callable(getattr(manager, method))]
            # Filter out inherited methods
            available_actions = [a for a in available_actions if a in ['create', 'get', 'update', 'delete', 'list', 'update_status', 'update_type', 'update_content', 'add_tests', 'remove_tests', 'add_environments', 'remove_environments']]
            return self._create_error_result([
                f"Invalid action '{action}' for entity '{entity}'",
                f"Available actions for {entity}: {', '.join(available_actions) if available_actions else 'none implemented'}",
                f"Example: action='create' to create a new {entity}"
            ])

    def _create_error_result(self, error_message: Union[str, List[str]]) -> Dict[str, Any]:
        """Create standardized error response."""
        if isinstance(error_message, str):
            errors = [error_message]
        else:
            errors = error_message

        return {
            'success': False,
            'data': None,
            'warnings': [],
            'errors': errors
        }