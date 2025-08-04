"""Xray history and attachment management tools for Xray MCP server.

This module provides functionality for managing Xray execution history
and file attachments, including retrieving execution history, uploading
attachments to test steps, and managing attachment lifecycle.

The HistoryTools class serves as the main interface for interacting
with Xray's history and attachment API through GraphQL queries and mutations.
"""

from typing import Dict, Any, List, Optional

try:
    from ..client import XrayGraphQLClient
    from ..exceptions import GraphQLError, ValidationError
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError


class HistoryTools:
    """Tools for managing Xray history and attachments.

    This class provides methods to interact with Xray execution history
    and file attachments. History tracking helps understand execution
    patterns while attachments provide evidence and documentation.

    Attributes:
        client (XrayGraphQLClient): GraphQL client for API communication

    Dependencies:
        - Requires authenticated XrayGraphQLClient instance
        - Depends on Xray GraphQL API for history and attachment operations

    Note:
        All methods return structured dictionaries compatible with MCP responses.
        Errors are propagated to calling code for centralized error handling.
    """

    def __init__(self, client: XrayGraphQLClient):
        """Initialize history tools with GraphQL client.

        Args:
            client (XrayGraphQLClient): Authenticated GraphQL client instance
        """
        self.client = client

    async def get_xray_history(
        self,
        issue_id: str,
        test_plan_id: Optional[str] = None,
        test_env_id: Optional[str] = None,
        start: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Retrieve Xray execution history for a test.

        Fetches the execution history of a specific test, optionally filtered
        by test plan and environment. History includes all past executions
        with their results, dates, and execution context.

        Args:
            issue_id: The Jira issue ID of the test
            test_plan_id: Optional test plan issue ID to filter history
            test_env_id: Optional test environment ID to filter history
            start: Starting index for pagination (0-based)
            limit: Maximum number of history entries to return (max 100)

        Returns:
            Dict containing:
                - total: Total number of history entries
                - start: Starting index of results
                - limit: Number of results requested
                - results: List of history entry objects with:
                    - executionId: Test execution ID
                    - testRunId: Test run ID
                    - status: Execution status
                    - executedBy: User who executed the test
                    - executedOn: Execution timestamp
                    - environment: Test environment
                    - testPlan: Associated test plan
                    - comment: Execution comment
                    - defects: Associated defects
                    - evidence: Attached evidence

        Raises:
            ValidationError: If issue_id is invalid or limit exceeds 100
            GraphQLError: If the GraphQL query fails
        """
        if limit > 100:
            raise ValidationError("Limit cannot exceed 100")

        query = """
        query GetXrayHistory(
            $issueId: String!,
            $testPlanId: String,
            $testEnvId: String,
            $start: Int!,
            $limit: Int!
        ) {
            getTest(issueId: $issueId) {
                history(
                    testPlanId: $testPlanId,
                    testEnvironmentId: $testEnvId,
                    start: $start,
                    limit: $limit
                ) {
                total
                start
                limit
                results {
                    executionId
                    testRunId
                    status {
                        name
                        color
                    }
                    executedBy {
                        displayName
                        emailAddress
                    }
                    executedOn
                    environment
                    testPlan {
                        issueId
                        summary
                    }
                    comment
                    defects {
                        issueId
                        summary
                        status {
                            name
                        }
                    }
                    evidence {
                        id
                        filename
                        url
                        mimeType
                        size
                        uploadedBy {
                            displayName
                        }
                        uploadedOn
                    }
                }
                }
            }
        }
        """

        variables = {
            "issueId": issue_id,
            "testPlanId": test_plan_id,
            "testEnvId": test_env_id,
            "start": start,
            "limit": limit,
        }

        result = await self.client.execute_query(query, variables)
        test_data = result.get("data", {}).get("getTest", {})
        return test_data.get("history", {})

    async def upload_attachment(
        self, step_id: str, file: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Upload an attachment to a test step.

        Uploads a file attachment to a specific test step. Attachments serve
        as evidence, documentation, or supporting materials for test execution.

        Args:
            step_id: The ID of the test step to attach the file to
            file: File information containing:
                - filename: Name of the file
                - content: File content (base64 encoded or binary)
                - mimeType: MIME type of the file
                - description: Optional description of the attachment

        Returns:
            Dict containing:
                - success: Boolean indicating successful upload
                - attachment: Details of the uploaded attachment with:
                    - id: Attachment ID
                    - filename: File name
                    - url: Access URL
                    - mimeType: File MIME type
                    - size: File size in bytes
                    - uploadedBy: User who uploaded the file
                    - uploadedOn: Upload timestamp

        Raises:
            ValidationError: If step_id or file information is invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation UploadAttachment($stepId: String!, $fileInput: AttachmentInput!) {
            uploadAttachment(stepId: $stepId, file: $fileInput) {
                success
                attachment {
                    id
                    filename
                    url
                    mimeType
                    size
                    uploadedBy {
                        displayName
                        emailAddress
                    }
                    uploadedOn
                    description
                }
            }
        }
        """

        variables = {
            "stepId": step_id,
            "fileInput": {
                "filename": file.get("filename"),
                "content": file.get("content"),
                "mimeType": file.get("mimeType"),
                "description": file.get("description"),
            },
        }

        result = await self.client.execute_query(mutation, variables)
        return result.get("data", {}).get("uploadAttachment", {})

    async def delete_attachment(self, attachment_id: str) -> Dict[str, Any]:
        """Delete an attachment from Xray.

        Removes an attachment from a test step or execution. This permanently
        deletes the file and removes it from the associated test context.

        Args:
            attachment_id: The ID of the attachment to delete

        Returns:
            Dict containing:
                - success: Boolean indicating successful deletion
                - deletedAttachmentId: ID of the deleted attachment

        Raises:
            ValidationError: If attachment_id is invalid
            GraphQLError: If the GraphQL mutation fails
        """
        mutation = """
        mutation DeleteAttachment($attachmentId: String!) {
            deleteAttachment(attachmentId: $attachmentId) {
                success
            }
        }
        """

        variables = {"attachmentId": attachment_id}
        result = await self.client.execute_query(mutation, variables)

        return {
            "success": result.get("data", {})
            .get("deleteAttachment", {})
            .get("success", False),
            "deletedAttachmentId": attachment_id,
        }
