"""Precondition management tools for Xray MCP server.

This module provides functionality for managing preconditions in Xray,
including creating, retrieving, updating, and deleting preconditions.
Preconditions are prerequisites that must be satisfied before test execution.

The PreconditionTools class serves as the main interface for interacting
with Xray's precondition API through GraphQL queries and mutations.
"""

from typing import Dict, Any, List, Optional

try:
    from ..client import XrayGraphQLClient
    from ..exceptions import GraphQLError, ValidationError
    from ..validators import validate_jql
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError
    from validators import validate_jql


class PreconditionTools:
    """Tools for managing preconditions in Xray.
    
    This class provides methods to interact with preconditions, which define
    prerequisites that must be met before test execution. Preconditions can
    be associated with multiple tests and help ensure consistent test setup.
    
    Attributes:
        client (XrayGraphQLClient): GraphQL client for API communication
    
    Dependencies:
        - Requires authenticated XrayGraphQLClient instance
        - Depends on Xray GraphQL API for precondition operations
    
    Note:
        All methods return structured dictionaries compatible with MCP responses.
        Errors are propagated to calling code for centralized error handling.
    """
    
    def __init__(self, client: XrayGraphQLClient):
        """Initialize precondition tools with GraphQL client.
        
        Args:
            client (XrayGraphQLClient): Authenticated GraphQL client instance
        """
        self.client = client
    
    async def get_preconditions(
        self, 
        issue_id: str, 
        start: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Retrieve preconditions for a given test issue.
        
        Fetches all preconditions associated with a specific test, with pagination
        support for handling large numbers of preconditions.
        
        Args:
            issue_id: The Jira issue ID of the test
            start: Starting index for pagination (0-based)
            limit: Maximum number of preconditions to return (max 100)
        
        Returns:
            Dict containing:
                - preconditions: List of precondition objects
                - total: Total number of preconditions
                - start: Starting index of results
                - limit: Number of results requested
        
        Raises:
            ValidationError: If issue_id is invalid or limit exceeds 100
            GraphQLError: If the GraphQL query fails
        """
        if limit > 100:
            raise ValidationError("Limit cannot exceed 100")
        
        query = """
        query GetPreconditions($issueId: String!, $start: Int!, $limit: Int!) {
            getTest(issueId: $issueId) {
                preconditions(start: $start, limit: $limit) {
                    total
                    start
                    limit
                    results {
                        issueId
                        projectId
                        summary
                        description
                        testType {
                            name
                            kind
                        }
                        status {
                            name
                            color
                        }
                        priority {
                            name
                        }
                        labels
                        created
                        updated
                    }
                }
            }
        }
        """
        
        variables = {
            "issueId": issue_id,
            "start": start,
            "limit": limit
        }
        
        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getTest", {}).get("preconditions", {})
    
    async def create_precondition(
        self, 
        issue_id: str, 
        precondition_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new precondition and associate it with a test.
        
        Creates a precondition issue in Jira and links it to the specified test.
        The precondition can be of type Manual, Generic, or Cucumber.
        
        Args:
            issue_id: The Jira issue ID of the test to associate the precondition with
            precondition_input: Dictionary containing precondition details:
                - projectKey: Project where precondition will be created
                - summary: Precondition title/summary
                - description: Optional detailed description
                - testType: Type of precondition (Manual, Generic, Cucumber)
                - steps: For Manual preconditions (list of step objects)
                - gherkin: For Cucumber preconditions (Gherkin scenario)
                - unstructured: For Generic preconditions (free text)
        
        Returns:
            Dict containing:
                - preconditionId: ID of created precondition
                - warnings: Any warnings from the operation
                - success: Boolean indicating operation success
        
        Raises:
            ValidationError: If required fields are missing or invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation CreatePrecondition($issueId: String!, $preconditionInput: CreatePreconditionInput!) {
            addPreconditionsToTest(issueId: $issueId, preconditions: [$preconditionInput]) {
                addedPreconditions {
                    issueId
                    summary
                    testType {
                        name
                    }
                }
                warnings
            }
        }
        """
        
        variables = {
            "issueId": issue_id,
            "preconditionInput": precondition_input
        }
        
        result = await self.client.execute_query(mutation, variables)
        return result.get("data", {}).get("addPreconditionsToTest", {})
    
    async def update_precondition(
        self, 
        precondition_id: str, 
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing precondition.
        
        Modifies the properties of an existing precondition. Supports updating
        summary, description, test type, steps, and other precondition attributes.
        
        Args:
            precondition_id: The Jira issue ID of the precondition to update
            updates: Dictionary containing fields to update:
                - summary: New summary/title
                - description: New description
                - testType: New test type
                - steps: New steps for Manual preconditions
                - gherkin: New Gherkin scenario for Cucumber preconditions
                - unstructured: New content for Generic preconditions
        
        Returns:
            Dict containing:
                - precondition: Updated precondition object
                - success: Boolean indicating operation success
        
        Raises:
            ValidationError: If precondition_id is invalid or updates are malformed
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation UpdatePrecondition($preconditionId: String!, $updates: UpdatePreconditionInput!) {
            updatePrecondition(issueId: $preconditionId, precondition: $updates) {
                precondition {
                    issueId
                    summary
                    description
                    testType {
                        name
                        kind
                    }
                    updated
                }
            }
        }
        """
        
        variables = {
            "preconditionId": precondition_id,
            "updates": updates
        }
        
        result = await self.client.execute_query(mutation, variables)
        return result.get("data", {}).get("updatePrecondition", {})
    
    async def delete_precondition(self, precondition_id: str) -> Dict[str, Any]:
        """Delete a precondition from Xray.
        
        Removes the precondition issue from Jira. This operation also removes
        the precondition from all associated tests.
        
        Args:
            precondition_id: The Jira issue ID of the precondition to delete
        
        Returns:
            Dict containing:
                - success: Boolean indicating successful deletion
                - deletedPreconditionId: ID of the deleted precondition
        
        Raises:
            ValidationError: If precondition_id is invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation DeletePrecondition($preconditionId: String!) {
            deletePrecondition(issueId: $preconditionId) {
                success
            }
        }
        """
        
        variables = {
            "preconditionId": precondition_id
        }
        
        result = await self.client.execute_query(mutation, variables)
        return {
            "success": result.get("data", {}).get("deletePrecondition", {}).get("success", False),
            "deletedPreconditionId": precondition_id
        }