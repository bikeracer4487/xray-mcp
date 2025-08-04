"""Test versioning management tools for Xray MCP server.

This module provides functionality for managing test versions in Xray,
including retrieving, archiving, restoring, and creating new versions.
Test versioning allows maintaining multiple versions of tests for different
releases or iterations.

The TestVersioningTools class serves as the main interface for interacting
with Xray's test versioning API through GraphQL queries and mutations.
"""

from typing import Dict, Any, List, Optional

try:
    from ..client import XrayGraphQLClient
    from ..exceptions import GraphQLError, ValidationError
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError


class TestVersioningTools:
    """Tools for managing test versions in Xray.

    This class provides methods to interact with test versions, which allow
    maintaining multiple versions of tests for different releases, iterations,
    or development cycles. Test versions help track test evolution over time.

    Attributes:
        client (XrayGraphQLClient): GraphQL client for API communication

    Dependencies:
        - Requires authenticated XrayGraphQLClient instance
        - Depends on Xray GraphQL API for test versioning operations

    Note:
        All methods return structured dictionaries compatible with MCP responses.
        Errors are propagated to calling code for centralized error handling.
    """

    def __init__(self, client: XrayGraphQLClient):
        """Initialize test versioning tools with GraphQL client.

        Args:
            client (XrayGraphQLClient): Authenticated GraphQL client instance
        """
        self.client = client

    async def get_test_versions(self, issue_id: str) -> Dict[str, Any]:
        """Retrieve all versions of a test.

        Fetches all available versions of a specific test, including archived
        versions. Each version contains the test definition at that point in time.

        Args:
            issue_id: The Jira issue ID of the test

        Returns:
            Dict containing:
                - versions: List of test version objects with:
                    - id: Unique version identifier
                    - name: Version name
                    - default: Whether this is the default version
                    - archived: Whether this version is archived
                    - testType: Test type at this version
                    - lastModified: When this version was last modified

        Raises:
            ValidationError: If issue_id is invalid
            GraphQLError: If the GraphQL query fails
        """
        query = """
        query GetTestVersions($issueId: String!) {
            getTest(issueId: $issueId) {
                testVersions(limit: 100) {
                    results {
                        id
                        name
                        default
                        archived
                        testType {
                            name
                            kind
                        }
                        lastModified
                        steps {
                            action
                            data
                            result
                        }
                        gherkin
                        unstructured
                        scenarioType
                    }
                }
            }
        }
        """

        variables = {"issueId": issue_id}
        result = await self.client.execute_query(query, variables)
        test_data = result.get("data", {}).get("getTest", {})
        test_versions_data = test_data.get("testVersions", {})
        return {"versions": test_versions_data.get("results", [])}

    async def archive_test_version(
        self, issue_id: str, version_id: int
    ) -> Dict[str, Any]:
        """Archive a specific version of a test.

        Archives a test version, making it read-only and removing it from
        active use. Archived versions can still be viewed and restored.

        Args:
            issue_id: The Jira issue ID of the test
            version_id: The version ID to archive

        Returns:
            Dict containing:
                - success: Boolean indicating successful archival
                - archivedVersion: Details of the archived version with id, name, archived status

        Raises:
            ValidationError: If issue_id or version_id is invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation ArchiveTestVersion($issueId: String!, $versionId: Int!) {
            archiveTestVersion(issueId: $issueId, versionId: $versionId) {
                success
                archivedVersion {
                    id
                    name
                    archived
                    lastModified
                }
            }
        }
        """

        variables = {"issueId": issue_id, "versionId": version_id}

        result = await self.client.execute_query(mutation, variables)
        return result.get("data", {}).get("archiveTestVersion", {})

    async def restore_test_version(
        self, issue_id: str, version_id: int
    ) -> Dict[str, Any]:
        """Restore an archived version of a test.

        Restores an archived test version, making it active and usable again.
        The restored version becomes the current active version of the test.

        Args:
            issue_id: The Jira issue ID of the test
            version_id: The version ID to restore

        Returns:
            Dict containing:
                - success: Boolean indicating successful restoration
                - restoredVersion: Details of the restored version with id, name, archived status
                - currentVersion: The version that is now current with id, name, default status

        Raises:
            ValidationError: If issue_id or version_id is invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation RestoreTestVersion($issueId: String!, $versionId: Int!) {
            restoreTestVersion(issueId: $issueId, versionId: $versionId) {
                success
                restoredVersion {
                    id
                    name
                    archived
                    lastModified
                }
                currentVersion {
                    id
                    name
                    default
                    testType {
                        name
                    }
                }
            }
        }
        """

        variables = {"issueId": issue_id, "versionId": version_id}

        result = await self.client.execute_query(mutation, variables)
        return result.get("data", {}).get("restoreTestVersion", {})

    async def create_test_version_from(
        self, issue_id: str, version_id: int
    ) -> Dict[str, Any]:
        """Create a new version from an existing version.

        Creates a new test version based on an existing version. This is useful
        for branching test definitions or creating variants for different releases.

        Args:
            issue_id: The Jira issue ID of the test
            version_id: The version ID to use as the source

        Returns:
            Dict containing:
                - success: Boolean indicating successful creation
                - newVersion: Details of the newly created version with id, name, default status
                - sourceVersion: Details of the source version used with id, name, default status

        Raises:
            ValidationError: If issue_id or version_id is invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation CreateTestVersionFrom($issueId: String!, $sourceVersionId: Int!) {
            createTestVersionFrom(issueId: $issueId, sourceVersionId: $sourceVersionId) {
                success
                newVersion {
                    id
                    name
                    default
                    archived
                    testType {
                        name
                    }
                    lastModified
                }
                sourceVersion {
                    id
                    name
                    default
                }
            }
        }
        """

        variables = {"issueId": issue_id, "sourceVersionId": version_id}

        result = await self.client.execute_query(mutation, variables)
        return result.get("data", {}).get("createTestVersionFrom", {})
