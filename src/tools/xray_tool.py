"""Simplified Xray tool using manager pattern."""

from typing import Dict, Any
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
            return self._create_error_result(f"Invalid entity: {entity}")

        manager = self.managers[entity]

        # Simple dispatch using getattr
        if hasattr(manager, action):
            try:
                return await getattr(manager, action)(params)
            except Exception as e:
                return self._create_error_result(f"Failed to execute {action} on {entity}: {str(e)}")
        else:
            return self._create_error_result(f"Invalid action '{action}' for entity '{entity}'")

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            'success': False,
            'data': None,
            'warnings': [],
            'errors': [error_message]
        }