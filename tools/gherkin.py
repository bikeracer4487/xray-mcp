"""Gherkin and unstructured test update tools for Xray MCP server.

This module provides functionality for updating Gherkin scenarios and
unstructured test definitions in Xray, supporting Cucumber and Generic
test types respectively.

The GherkinTools class serves as the main interface for interacting
with Xray's test definition update API through GraphQL mutations.
"""

from typing import Dict, Any

try:
    from ..client import XrayGraphQLClient
    from ..exceptions import GraphQLError, ValidationError
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError


class GherkinTools:
    """Tools for updating Gherkin and unstructured test definitions.
    
    This class provides methods to update test definitions for Cucumber
    tests (Gherkin scenarios) and Generic tests (unstructured content).
    These updates modify the core test logic and behavior.
    
    Attributes:
        client (XrayGraphQLClient): GraphQL client for API communication
    
    Dependencies:
        - Requires authenticated XrayGraphQLClient instance
        - Depends on Xray GraphQL API for test definition updates
    
    Note:
        All methods return structured dictionaries compatible with MCP responses.
        Errors are propagated to calling code for centralized error handling.
    """
    
    def __init__(self, client: XrayGraphQLClient):
        """Initialize Gherkin tools with GraphQL client.
        
        Args:
            client (XrayGraphQLClient): Authenticated GraphQL client instance
        """
        self.client = client
    
    async def update_gherkin_definition(
        self,
        issue_id: str,
        gherkin_text: str
    ) -> Dict[str, Any]:
        """Update the Gherkin scenario definition for a Cucumber test.
        
        Updates the Gherkin scenario content for a Cucumber test. The Gherkin
        text should be properly formatted with Feature, Scenario, Given, When,
        Then steps following standard Gherkin syntax.
        
        Args:
            issue_id: The Jira issue ID of the Cucumber test
            gherkin_text: The new Gherkin scenario content in standard format
        
        Returns:
            Dict containing:
                - success: Boolean indicating successful update
                - test: Updated test information with:
                    - issueId: Test issue ID
                    - testType: Confirmed test type (should be Cucumber)
                    - gherkin: The updated Gherkin content
                    - updated: Timestamp of the update
                - validation: Any validation messages or warnings
        
        Raises:
            ValidationError: If issue_id is invalid or gherkin_text is malformed
            GraphQLError: If the GraphQL mutation fails
        
        Example:
            >>> gherkin = '''
            ... Feature: User Login
            ...   Scenario: Valid user login
            ...     Given I am on the login page
            ...     When I enter valid credentials
            ...     Then I should be logged in successfully
            ... '''
            >>> result = await gherkin_tools.update_gherkin_definition("TEST-123", gherkin)
        """
        if not gherkin_text.strip():
            raise ValidationError("gherkin_text cannot be empty")
        
        mutation = """
        mutation UpdateGherkinDefinition($issueId: String!, $gherkinText: String!) {
            updateGherkinTestDefinition(issueId: $issueId, gherkin: $gherkinText) {
                success
                test {
                    issueId
                    summary
                    testType {
                        name
                        kind
                    }
                    gherkin
                    updated
                }
                validation {
                    isValid
                    warnings
                    errors
                }
            }
        }
        """
        
        variables = {
            "issueId": issue_id,
            "gherkinText": gherkin_text
        }
        
        result = await self.client.execute_query(mutation, variables)
        return result.get("data", {}).get("updateGherkinTestDefinition", {})