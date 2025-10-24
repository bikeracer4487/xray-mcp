"""Base manager class for Xray entity operations."""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from src.graphql_client import XrayGraphQLClient


class XrayEntityManager(ABC):
    """Base class for Xray entity managers with common functionality."""

    def __init__(self, client: XrayGraphQLClient):
        """Initialize manager with GraphQL client.

        Args:
            client: Authenticated XrayGraphQLClient instance
        """
        self.client = client

    async def execute_query(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GraphQL query with error handling.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Query result data

        Raises:
            Exception: If query execution fails
        """
        try:
            return await self.client.execute(query, variables)
        except Exception as e:
            error_msg = str(e)

            # Handle specific Xray indexing issues
            if "project may need to be re-indexed" in error_msg.lower():
                raise Exception(
                    f"Xray indexing issue: {error_msg}. "
                    "This is a temporary Xray Cloud service issue. "
                    "Please try again in a few moments or contact Xray support if this persists."
                )

            raise Exception(f"GraphQL query failed: {error_msg}")

    def build_jql(self, project_key: Optional[str] = None, custom_jql: Optional[str] = None,
                  entity_type: Optional[str] = None) -> str:
        """Build JQL query string for entity filtering.

        Args:
            project_key: Jira project key
            custom_jql: Custom JQL query
            entity_type: Entity type for issuetype filter

        Returns:
            JQL query string
        """
        if custom_jql:
            return custom_jql

        parts = []
        if project_key:
            parts.append(f"project = \"{project_key}\"")
        if entity_type:
            parts.append(f"issuetype = '{entity_type}'")

        if not parts:
            parts.append(f"issuetype = '{entity_type or 'Test'}'")

        return " AND ".join(parts) + " ORDER BY created DESC"

    def extract_jira_data(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and flatten Jira data from GraphQL response.

        Args:
            item: GraphQL response item with jira field

        Returns:
            Flattened data with issueKey, summary, etc.
        """
        result = {
            'issueId': item.get('issueId'),
            'projectId': item.get('projectId')
        }

        if 'jira' in item and item['jira']:
            jira_data = item['jira']
            if jira_data.get('key'):
                result['issueKey'] = jira_data['key']
            if jira_data.get('summary'):
                result['summary'] = jira_data['summary']
            if jira_data.get('description'):
                result['description'] = jira_data['description']
            if jira_data.get('assignee'):
                result['assignee'] = jira_data['assignee']
            if jira_data.get('reporter'):
                result['reporter'] = jira_data['reporter']
            if jira_data.get('created'):
                result['created'] = jira_data['created']
            if jira_data.get('updated'):
                result['updated'] = jira_data['updated']

        return result

    def create_success_result(self, data: Any, warnings: list = None) -> Dict[str, Any]:
        """Create standardized success response.

        Args:
            data: Response data
            warnings: Optional warning messages

        Returns:
            Standardized success response
        """
        return {
            'success': True,
            'data': data,
            'warnings': warnings or [],
            'errors': []
        }

    def create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response.

        Args:
            error_message: Error message

        Returns:
            Standardized error response
        """
        return {
            'success': False,
            'data': None,
            'warnings': [],
            'errors': [error_message]
        }

    @abstractmethod
    async def create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create new entity."""
        pass

    @abstractmethod
    async def get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List entities with optional filtering."""
        pass

    @abstractmethod
    async def delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete entity by ID."""
        pass