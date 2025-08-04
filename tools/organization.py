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
    
    async def get_folder_contents(self, folder_id: str) -> Dict[str, Any]:
        """Retrieve contents of a test repository folder.
        
        Fetches all items (tests, subfolders) contained within a specific
        folder in the Xray test repository. Provides hierarchical view
        of test organization.
        
        Args:
            folder_id: The ID of the folder to retrieve contents from
        
        Returns:
            Dict containing:
                - folderId: The folder ID
                - folderName: Name of the folder
                - parentFolderId: ID of the parent folder (if any)
                - path: Full path to the folder
                - contents: List of folder contents with:
                    - type: Item type (test, folder)
                    - id: Item ID
                    - name: Item name/summary
                    - testType: Test type (for test items)
                    - itemCount: Number of items (for folder items)
                - totalItems: Total number of items in the folder
        
        Raises:
            ValidationError: If folder_id is invalid
            GraphQLError: If the GraphQL query fails
        """
        query = """
        query GetFolderContents($folderId: String!) {
            getFolder(folderId: $folderId) {
                id
                name
                parentFolderId
                path
                contents {
                    type
                    id
                    name
                    ... on Test {
                        summary
                        testType {
                            name
                        }
                        status {
                            name
                        }
                    }
                    ... on Folder {
                        itemCount
                        subfolderCount
                    }
                }
                totalItems
                created
                updated
            }
        }
        """
        
        variables = {"folderId": folder_id}
        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getFolder", {})
    
    async def move_test_to_folder(
        self,
        issue_id: str,
        folder_id: str
    ) -> Dict[str, Any]:
        """Move a test to a different folder in the test repository.
        
        Moves a test from its current location to a new folder, helping
        reorganize tests within the repository hierarchy.
        
        Args:
            issue_id: The Jira issue ID of the test to move
            folder_id: The ID of the destination folder
        
        Returns:
            Dict containing:
                - success: Boolean indicating successful move
                - test: Updated test information with:
                    - issueId: Test issue ID
                    - summary: Test summary
                    - newFolder: Details of the new folder
                    - previousFolder: Details of the previous folder
                - moved: Timestamp of the move operation
        
        Raises:
            ValidationError: If issue_id or folder_id is invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation MoveTestToFolder($issueId: String!, $folderId: String!) {
            moveTestToFolder(testId: $issueId, folderId: $folderId) {
                success
                test {
                    issueId
                    summary
                    folder {
                        id
                        name
                        path
                    }
                }
                previousFolder {
                    id
                    name
                    path
                }
                moved
            }
        }
        """
        
        variables = {
            "issueId": issue_id,
            "folderId": folder_id
        }
        
        result = await self.client.execute_query(mutation, variables)
        return result.get("data", {}).get("moveTestToFolder", {})
    
    async def get_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """Retrieve a specific dataset for data-driven testing.
        
        Fetches detailed information about a test dataset including its
        structure, data entries, and associated tests.
        
        Args:
            dataset_id: The ID of the dataset to retrieve
        
        Returns:
            Dict containing:
                - datasetId: Dataset ID
                - name: Dataset name
                - description: Dataset description
                - parameters: List of parameter definitions
                - data: List of data rows/entries
                - associatedTests: Tests using this dataset
                - created: Creation timestamp
                - updated: Last update timestamp
        
        Raises:
            ValidationError: If dataset_id is invalid
            GraphQLError: If the GraphQL query fails
        """
        query = """
        query GetDataset($datasetId: String!) {
            getDataset(datasetId: $datasetId) {
                id
                name
                description
                parameters {
                    name
                    type
                    description
                }
                data {
                    rowId
                    values {
                        parameter
                        value
                    }
                }
                associatedTests {
                    issueId
                    summary
                    testType {
                        name
                    }
                }
                created
                updated
            }
        }
        """
        
        variables = {"datasetId": dataset_id}
        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getDataset", {})
    
    async def get_datasets(self, project_key: str) -> Dict[str, Any]:
        """Retrieve all datasets for a specific project.
        
        Fetches all available datasets within a project for data-driven
        testing purposes. Provides overview of available test data.
        
        Args:
            project_key: The Jira project key to retrieve datasets from
        
        Returns:
            Dict containing:
                - projectKey: The project key
                - datasets: List of dataset objects with:
                    - datasetId: Dataset ID
                    - name: Dataset name
                    - description: Dataset description
                    - parameterCount: Number of parameters
                    - dataRowCount: Number of data rows
                    - associatedTestsCount: Number of tests using this dataset
                    - created: Creation timestamp
                    - updated: Last update timestamp
        
        Raises:
            ValidationError: If project_key is invalid
            GraphQLError: If the GraphQL query fails
        """
        query = """
        query GetDatasets($projectKey: String!) {
            getDatasets(projectKey: $projectKey) {
                projectKey
                datasets {
                    id
                    name
                    description
                    parameterCount
                    dataRowCount
                    associatedTestsCount
                    created
                    updated
                }
            }
        }
        """
        
        variables = {"projectKey": project_key}
        result = await self.client.execute_query(query, variables)
        return result.get("data", {}).get("getDatasets", {})