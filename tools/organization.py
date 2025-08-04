"""Folder and dataset management tools for Xray MCP server.

This module provides functionality for managing test organization through
folders and datasets in Xray, including retrieving folder contents,
moving tests between folders, and managing test data sets.

The OrganizationTools class serves as the main interface for interacting
with Xray's test organization API through GraphQL queries and mutations.
"""

from typing import Dict, Any, List, Optional

try:
    from ..client import XrayGraphQLClient
    from ..exceptions import GraphQLError, ValidationError
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError


class OrganizationTools:
    """Tools for managing test organization through folders and datasets.

    This class provides methods to interact with Xray's test repository
    organization features, including folder hierarchy management and
    dataset management for data-driven testing.

    Attributes:
        client (XrayGraphQLClient): GraphQL client for API communication

    Dependencies:
        - Requires authenticated XrayGraphQLClient instance
        - Depends on Xray GraphQL API for organization operations

    Note:
        All methods return structured dictionaries compatible with MCP responses.
        Errors are propagated to calling code for centralized error handling.
    """

    def __init__(self, client: XrayGraphQLClient):
        """Initialize organization tools with GraphQL client.

        Args:
            client (XrayGraphQLClient): Authenticated GraphQL client instance
        """
        self.client = client

    async def get_folder_contents(
        self, project_id: str, folder_path: str = "/"
    ) -> Dict[str, Any]:
        """Retrieve contents of a test repository folder.

        Fetches folder information including child folders and test counts.
        Note: Based on the actual GraphQL schema, getFolder takes projectId
        and path parameters, not a folderId.

        Args:
            project_id: The project ID where the folder exists
            folder_path: The path of the folder (defaults to root "/")

        Returns:
            Dict containing:
                - name: Folder name
                - path: Folder path
                - testsCount: Number of tests in the folder
                - issuesCount: Number of issues in the folder
                - preconditionsCount: Number of preconditions in the folder
                - folders: Child folders (JSON structure)

        Raises:
            ValidationError: If project_id is invalid
            GraphQLError: If the GraphQL query fails
        """
        query = """
        query GetFolder($projectId: String!, $path: String!) {
            getFolder(projectId: $projectId, path: $path) {
                name
                path
                testsCount
                issuesCount
                preconditionsCount
                folders
            }
        }
        """

        variables = {"projectId": project_id, "path": folder_path}
        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getFolder", {})

    async def move_test_to_folder(
        self, issue_id: str, folder_path: str
    ) -> Dict[str, Any]:
        """Move a test to a different folder in the test repository.

        Moves a test from its current location to a new folder path.
        Based on the actual GraphQL schema, uses updateTestFolder mutation
        which takes issue ID and folder path.

        Args:
            issue_id: The Jira issue ID of the test to move
            folder_path: The path of the destination folder (e.g., "/Component/UI")

        Returns:
            Dict containing:
                - success: Boolean indicating successful move (returns null on success)

        Raises:
            ValidationError: If issue_id or folder_path is invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation UpdateTestFolder($issueId: String!, $folderPath: String!) {
            updateTestFolder(issueId: $issueId, folderPath: $folderPath)
        }
        """

        variables = {"issueId": issue_id, "folderPath": folder_path}

        result = await self.client.execute_query(mutation, variables)
        # updateTestFolder returns null on success
        return {
            "success": "errors" not in result,
            "movedTestId": issue_id,
            "newFolderPath": folder_path,
        }

    async def get_dataset(self, test_issue_id: str) -> Dict[str, Any]:
        """Retrieve a specific dataset for data-driven testing.

        Fetches detailed information about a test dataset including its
        structure, data entries, and associated context. Based on the actual
        GraphQL schema, getDataset takes testIssueId parameter, not datasetId.

        Args:
            test_issue_id: The test issue ID to retrieve dataset for

        Returns:
            Dict containing:
                - id: Dataset ID
                - testIssueId: Associated test issue ID
                - testExecIssueId: Associated test execution issue ID (if any)
                - testPlanIssueId: Associated test plan issue ID (if any)
                - parameters: List of parameter definitions with name, type, listValues
                - rows: List of data rows with order and Values array

        Raises:
            ValidationError: If test_issue_id is invalid
            GraphQLError: If the GraphQL query fails
        """
        query = """
        query GetDataset($testIssueId: String!) {
            getDataset(testIssueId: $testIssueId) {
                id
                testIssueId
                testExecIssueId
                testPlanIssueId
                parameters {
                    name
                    type
                    listValues
                }
                rows {
                    order
                    Values
                }
            }
        }
        """

        variables = {"testIssueId": test_issue_id}
        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getDataset", {})

    async def get_datasets(self, test_issue_ids: List[str]) -> Dict[str, Any]:
        """Retrieve datasets for multiple tests.

        Fetches datasets for specified test issues, including their metadata,
        parameters, and data rows. Based on the actual GraphQL schema,
        getDatasets takes testIssueIds array parameter, not project_key.

        Args:
            test_issue_ids: List of test issue IDs to retrieve datasets for

        Returns:
            Dict containing list of dataset objects with:
                - id: Dataset ID
                - testIssueId: Associated test issue ID
                - testExecIssueId: Associated test execution issue ID (if any)
                - testPlanIssueId: Associated test plan issue ID (if any)
                - parameters: List of parameter definitions with name, type, listValues
                - rows: List of data rows with order and Values array

        Raises:
            ValidationError: If test_issue_ids is invalid or empty
            GraphQLError: If the GraphQL query fails
        """
        if not test_issue_ids:
            raise ValidationError("test_issue_ids cannot be empty")

        query = """
        query GetDatasets($testIssueIds: [String!]!) {
            getDatasets(testIssueIds: $testIssueIds) {
                id
                testIssueId
                testExecIssueId
                testPlanIssueId
                parameters {
                    name
                    type
                    listValues
                }
                rows {
                    order
                    Values
                }
            }
        }
        """

        variables = {"testIssueIds": test_issue_ids}
        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getDatasets", [])
