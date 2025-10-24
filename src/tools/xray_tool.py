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

        # Handle special cross-entity search action
        if action == 'search':
            return await self._handle_search(params)

        # Simple dispatch using getattr
        if hasattr(manager, action):
            try:
                return await getattr(manager, action)(params)
            except Exception as e:
                return self._create_error_result(f"Failed to execute {action} on {entity}: {str(e)}")
        else:
            available_actions = [method for method in dir(manager) if not method.startswith('_') and callable(getattr(manager, method))]
            # Filter out inherited methods
            available_actions = [a for a in available_actions if a in ['create', 'get', 'update', 'delete', 'list', 'update_status', 'update_type', 'update_content', 'update_metadata', 'add_tests', 'remove_tests', 'add_environments', 'remove_environments', 'search']]
            return self._create_error_result([
                f"Invalid action '{action}' for entity '{entity}'",
                f"Available actions for {entity}: {', '.join(available_actions) if available_actions else 'none implemented'}",
                f"Example: action='create' to create a new {entity}, or action='search' for simplified searching"
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

    async def _handle_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle simplified search across entities with user-friendly parameters.

        Args:
            params: Search parameters including entity, text, project_key, etc.

        Returns:
            Unified search results with helpful suggestions
        """
        entity = params.get('entity')
        search_text = params.get('text', '').strip()
        project_key = params.get('project_key', '').strip()
        test_type = params.get('test_type', '').strip()
        recent_days = params.get('recent_days', 0)
        limit = min(params.get('limit', 20), 50)  # Cap at 50 for performance

        if not entity:
            return self._create_error_result("Missing required parameter: entity for search")

        if entity not in self.managers:
            valid_entities = list(self.managers.keys())
            return self._create_error_result([
                f"Invalid entity for search: '{entity}'",
                f"Valid entities are: {', '.join(valid_entities)}",
                f"Example: entity='test' to search tests"
            ])

        # Build JQL query based on user-friendly parameters
        jql_parts = []

        # Add project filter if specified
        if project_key:
            jql_parts.append(f"project = '{project_key}'")

        # Add entity-specific type filter
        if entity == 'test':
            jql_parts.append("issuetype = Test")
            if test_type:
                jql_parts.append(f"'Test Type' = '{test_type}'")
        elif entity == 'test_execution':
            jql_parts.append("issuetype = 'Test Execution'")
        elif entity == 'test_plan':
            jql_parts.append("issuetype = 'Test Plan'")

        # Add text search filter
        if search_text:
            # Search in summary and description
            jql_parts.append(f"(summary ~ '{search_text}' OR description ~ '{search_text}')")

        # Add recent activity filter
        if recent_days > 0:
            jql_parts.append(f"updated >= -{recent_days}d")

        # Combine JQL parts
        if jql_parts:
            jql_query = " AND ".join(jql_parts)
        else:
            # Default query to prevent returning everything
            if project_key:
                jql_query = f"project = '{project_key}'"
            else:
                return self._create_error_result([
                    "Search requires at least one filter parameter",
                    "Provide: text, project_key, test_type, or recent_days",
                    "Example: text='login test' or project_key='DEMO'"
                ])

        try:
            # Execute search using the appropriate manager
            manager = self.managers[entity]
            search_params = {
                'entity': entity,
                'action': 'list',
                'jql': jql_query,
                'limit': limit,
                'start': 0
            }

            result = await manager.list(search_params)

            if result['success']:
                # Enhance the result with search context
                search_context = {
                    'search_parameters': {
                        'entity': entity,
                        'text': search_text or 'any',
                        'project_key': project_key or 'any',
                        'test_type': test_type or 'any' if entity == 'test' else 'N/A',
                        'recent_days': recent_days or 'any',
                        'limit': limit
                    },
                    'jql_generated': jql_query,
                    'search_tips': self._get_search_tips(entity)
                }

                # Add search context to the result
                if 'data' in result and isinstance(result['data'], dict):
                    result['data']['search_context'] = search_context
                elif 'data' in result and isinstance(result['data'], list):
                    # For simple list results, wrap in a dict
                    result['data'] = {
                        'results': result['data'],
                        'search_context': search_context
                    }

                # Add helpful warnings if no results found
                if not result.get('data') or (isinstance(result['data'], dict) and not result['data'].get('results')):
                    result['warnings'] = result.get('warnings', []) + [
                        f"No {entity}s found matching your search criteria",
                        "Try broader search terms or check project key",
                        f"Generated JQL: {jql_query}"
                    ]

            return result

        except Exception as e:
            return self._create_error_result([
                f"Search failed for {entity}: {str(e)}",
                f"Generated JQL: {jql_query}",
                "Try simplifying your search parameters"
            ])

    def _get_search_tips(self, entity: str) -> List[str]:
        """Get entity-specific search tips for users."""
        base_tips = [
            "Use text parameter for keyword search in titles and descriptions",
            "Combine multiple filters for more specific results",
            "Use project_key to limit search to specific projects"
        ]

        entity_tips = {
            'test': [
                "Use test_type parameter: 'Manual', 'Generic', or 'Cucumber'",
                "Search test steps content with text parameter",
                "Use recent_days to find recently modified tests"
            ],
            'test_execution': [
                "Use recent_days to find recent test executions",
                "Search execution names and descriptions with text parameter",
                "Combine with project_key for project-specific executions"
            ],
            'test_plan': [
                "Search plan names and descriptions with text parameter",
                "Use recent_days to find recently updated plans",
                "Filter by project to find project-specific plans"
            ],
            'test_run': [
                "Search by test execution to find specific runs",
                "Use recent_days for recent test results",
                "Filter by status using JIRA status values"
            ]
        }

        return base_tips + entity_tips.get(entity, [])

    def _create_search_examples(self, entity: str) -> List[str]:
        """Create helpful search examples for each entity type."""
        examples = {
            'test': [
                "Search by keyword: text='login'",
                "Find manual tests: test_type='Manual'",
                "Recent tests: recent_days=7",
                "Project tests: project_key='DEMO'",
                "Combined: text='authentication' AND test_type='Cucumber' AND project_key='SECURITY'"
            ],
            'test_execution': [
                "Search executions: text='sprint'",
                "Recent executions: recent_days=14",
                "Project executions: project_key='DEMO'",
                "Combined: text='regression' AND recent_days=7"
            ],
            'test_plan': [
                "Search plans: text='release'",
                "Recent plans: recent_days=30",
                "Project plans: project_key='DEMO'",
                "Combined: text='milestone' AND project_key='RELEASE'"
            ]
        }
        return examples.get(entity, ["Use text, project_key, and recent_days parameters"])