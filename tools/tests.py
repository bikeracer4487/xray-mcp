"""Test management tools for Xray MCP server.

This module provides comprehensive test management capabilities for Jira Xray,
including creation, retrieval, update, and deletion of test cases. It supports
all Xray test types (Manual, Cucumber, Generic) and handles test versioning.

The tools in this module map directly to Xray's GraphQL API test operations,
providing a clean interface for test case management through the MCP protocol.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

# Handle both package and direct execution import modes
try:
    from ..client import XrayGraphQLClient
    from ..exceptions import GraphQLError, ValidationError
    from ..validators import validate_jql
    from ..utils import IssueIdResolver
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError
    from validators import validate_jql
    from utils import IssueIdResolver


@dataclass
class TestStep:
    """Test step for Manual tests.

    Represents a single step in a Manual test with action, data, and expected result.
    Maps to Xray's CreateStepInput GraphQL type.

    Attributes:
        action (str): The action to perform in this step
        result (str): The expected result of the action
        data (Optional[str]): Additional data or parameters for the step

    Example:
        step = TestStep(
            action="Navigate to login page",
            result="Login page is displayed",
            data="URL: /login"
        )
    """

    action: str
    result: str
    data: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary for GraphQL mutation.

        Returns:
            Dict[str, Any]: Step data in CreateStepInput format
        """
        step_dict = {"action": self.action, "result": self.result}
        if self.data:
            step_dict["data"] = self.data
        return step_dict


class TestTools:
    """Tools for managing tests in Xray.

    This class provides a comprehensive set of tools for test management
    in Xray, supporting all test types and operations. It handles:
    - Test retrieval (single, multiple, with versioning)
    - Test creation (Manual, Cucumber, Generic)
    - Test updates (type changes)
    - Test deletion

    All operations use Xray's GraphQL API and include proper error
    handling and validation.

    Attributes:
        client (XrayGraphQLClient): GraphQL client for API communication

    Example:
        tools = TestTools(graphql_client)
        test = await tools.get_test("TEST-123")
        new_test = await tools.create_test(
            project_key="PROJ",
            summary="Login test",
            test_type="Manual",
            steps=[
                {"action": "Open login page", "result": "Page loads"},
                {"action": "Enter credentials", "result": "Fields accept input"}
            ]
        )
    """

    def __init__(self, graphql_client: XrayGraphQLClient):
        """Initialize TestTools with a GraphQL client.

        Args:
            graphql_client (XrayGraphQLClient): Configured GraphQL client
                for Xray API communication
        """
        self.client = graphql_client
        self.id_resolver = IssueIdResolver(graphql_client)

    async def _resolve_issue_id(self, identifier: str) -> str:
        """Resolve Jira key or issue ID to numeric issue ID.

        Internal method that delegates to the id_resolver for backward
        compatibility with tests and internal usage patterns.

        Args:
            identifier: Either a Jira key (e.g., "TEST-123") or numeric issue ID

        Returns:
            str: Numeric issue ID for GraphQL operations

        Raises:
            GraphQLError: If identifier cannot be resolved
        """
        return await self.id_resolver.resolve_issue_id(identifier)


    async def get_test(self, issue_id: str) -> Dict[str, Any]:
        """Retrieve a single test by issue ID or Jira key.

        Fetches complete test information including test type, steps,
        Gherkin scenarios, and associated Jira fields. Accepts both
        numeric issue IDs and Jira keys for convenience.

        Args:
            issue_id (str): Jira issue ID or key (e.g., "1162822" or "TEST-123")

        Returns:
            Dict[str, Any]: Test data including:
                - issueId: Test issue ID
                - testType: Test type information (Manual, Cucumber, Generic)
                - steps: Test steps (for Manual tests)
                - gherkin: Gherkin scenario (for Cucumber tests)
                - unstructured: Unstructured content (for Generic tests)
                - jira: Jira fields (key, summary, assignee, etc.)

        Raises:
            GraphQLError: If test retrieval fails or test doesn't exist

        Complexity: O(1) - Single GraphQL query

        Call Flow:
            1. Constructs GraphQL query with requested fields
            2. Executes query with issue ID
            3. Returns test data or raises error
        """
        query = """
        query GetTest($issueId: String!) {
            getTest(issueId: $issueId) {
                issueId
                testType {
                    name
                }
                steps {
                    id
                    action
                    data
                    result
                    attachments {
                        id
                        filename
                    }
                }
                gherkin
                unstructured
                jira(fields: ["key", "summary", "assignee", "reporter", "status", "priority"])
            }
        }
        """

        # Resolve the identifier to a numeric issue ID
        resolved_id = await self.id_resolver.resolve_issue_id(issue_id)

        variables = {"issueId": resolved_id}
        result = await self.client.execute_query(query, variables)

        if (
            "data" in result
            and "getTest" in result["data"]
            and result["data"]["getTest"] is not None
        ):
            return result["data"]["getTest"]
        else:
            raise GraphQLError(f"Failed to retrieve test {issue_id}")

    async def get_tests(
        self, jql: Optional[str] = None, limit: int = 100
    ) -> Dict[str, Any]:
        """Retrieve multiple tests with optional JQL filtering.

        Fetches a paginated list of tests, optionally filtered by JQL query.
        Limited to 100 results per request due to Xray API restrictions.

        Args:
            jql (Optional[str]): JQL query to filter tests (e.g.,
                "project = TEST AND status = 'In Progress'")
            limit (int): Maximum number of tests to return (max 100)

        Returns:
            Dict[str, Any]: Paginated results containing:
                - total: Total number of tests matching the query
                - start: Starting index (0-based)
                - limit: Number of results returned
                - results: List of test objects with same fields as get_test

        Raises:
            ValidationError: If limit exceeds 100
            GraphQLError: If query execution fails

        Complexity: O(n) where n is the limit

        Example:
            # Get all tests in a project
            tests = await tools.get_tests(jql="project = 'PROJ'", limit=50)

            # Get all automated tests
            tests = await tools.get_tests(
                jql="project = 'PROJ' AND labels = 'automated'",
                limit=100
            )
        """
        # Validate limit to prevent API errors
        if limit > 100:
            raise ValidationError(
                "Limit cannot exceed 100 due to Xray API restrictions"
            )

        # Validate JQL if provided to prevent injection
        if jql:
            jql = validate_jql(jql)

        query = """
        query GetTests($jql: String, $limit: Int!) {
            getTests(jql: $jql, limit: $limit) {
                total
                start
                limit
                results {
                    issueId
                    testType {
                        name
                    }
                    steps {
                        id
                        action
                        data
                        result
                        attachments {
                            id
                            filename
                        }
                    }
                    gherkin
                    unstructured
                    jira(fields: ["key", "summary", "assignee", "status"])
                }
            }
        }
        """

        variables = {"jql": jql, "limit": limit}
        result = await self.client.execute_query(query, variables)

        if "data" in result and "getTests" in result["data"]:
            return result["data"]["getTests"]
        else:
            raise GraphQLError("Failed to retrieve tests")

    async def get_expanded_test(
        self, issue_id: str, test_version_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Retrieve detailed information for a single test with version support.

        Fetches expanded test information including version details, parent/child
        relationships, and additional metadata not available in get_test.
        Accepts both numeric issue IDs and Jira keys for convenience.

        Args:
            issue_id (str): Jira issue ID or key (e.g., "1162822" or "TEST-123")
            test_version_id (Optional[int]): Specific test version ID to retrieve.
                If None, returns the latest version.

        Returns:
            Dict[str, Any]: Expanded test data including:
                - issueId: Test issue ID
                - versionId: Version identifier
                - testType: Test type information
                - steps: Enhanced step data with parent/child relationships
                - warnings: Any warnings from the API
                - All fields from get_test plus additional metadata

        Raises:
            GraphQLError: If test retrieval fails

        Complexity: O(1) - Single GraphQL query

        Note:
            This method provides more detailed information than get_test,
            including test versioning and step relationships for modular tests.
        """
        query = """
        query GetExpandedTest($issueId: String!, $versionId: Int) {
            getExpandedTest(issueId: $issueId, versionId: $versionId) {
                issueId
                versionId
                testType {
                    name
                }
                steps {
                    id
                    action
                    data
                    result
                    parentTestIssueId
                    calledTestIssueId
                    attachments {
                        id
                        filename
                    }
                }
                gherkin
                unstructured
                warnings
                jira(fields: ["key", "summary", "assignee", "reporter", "status", "priority"])
            }
        }
        """

        # Resolve the identifier to a numeric issue ID
        resolved_id = await self.id_resolver.resolve_issue_id(issue_id)

        variables = {"issueId": resolved_id}
        if test_version_id is not None:
            variables["versionId"] = test_version_id

        result = await self.client.execute_query(query, variables)

        if (
            "data" in result
            and "getExpandedTest" in result["data"]
            and result["data"]["getExpandedTest"] is not None
        ):
            return result["data"]["getExpandedTest"]
        else:
            raise GraphQLError(f"Failed to retrieve expanded test {issue_id}")

    async def create_test(
        self,
        project_key: str,
        summary: str,
        test_type: str = "Generic",
        description: Optional[str] = None,
        steps: Optional[Union[List[Dict[str, str]], List[TestStep]]] = None,
        gherkin: Optional[str] = None,
        unstructured: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new test in Xray.

        Creates a test of the specified type with appropriate content.
        The method automatically selects the correct mutation based on
        test type and provided content.

        Args:
            project_key (str): Jira project key where test will be created
            summary (str): Test summary/title
            test_type (str): Type of test - "Manual", "Cucumber", or "Generic"
            description (Optional[str]): Test description in Jira
            steps (Optional[List[Dict[str, str]]]): For Manual tests, list of
                step dictionaries with keys:
                - action: Step action description
                - data: Test data for the step (optional)
                - result: Expected result
            gherkin (Optional[str]): For Cucumber tests, Gherkin scenario text
            unstructured (Optional[str]): For Generic tests, free-form content

        Returns:
            Dict[str, Any]: Created test information including:
                - test: The created test object
                - warnings: Any warnings from the creation process

        Raises:
            GraphQLError: If test creation fails

        Complexity: O(1) - Single GraphQL mutation

        Example:
            # Create a Manual test
            manual_test = await tools.create_test(
                project_key="PROJ",
                summary="Login functionality",
                test_type="Manual",
                description="Test user login flow",
                steps=[
                    {
                        "action": "Navigate to login page",
                        "data": "URL: /login",
                        "result": "Login page displayed"
                    },
                    {
                        "action": "Enter credentials",
                        "data": "user: test@example.com",
                        "result": "Credentials accepted"
                    }
                ]
            )

            # Create a Cucumber test
            cucumber_test = await tools.create_test(
                project_key="PROJ",
                summary="User authentication",
                test_type="Cucumber",
                gherkin=\"\"\"
                Scenario: Successful login
                    Given I am on the login page
                    When I enter valid credentials
                    Then I should be logged in
                \"\"\"
            )
        """
        # Construct Jira fields for the test issue
        jira_fields = {"summary": summary, "project": {"key": project_key}}

        if description:
            jira_fields["description"] = description

        # Select appropriate mutation based on test type and content
        # Different test types require different GraphQL mutations
        if test_type.lower() == "manual" and steps:
            # Manual test with steps - convert to proper format
            step_data = []
            for step in steps:
                if isinstance(step, TestStep):
                    step_data.append(step.to_dict())
                elif isinstance(step, dict):
                    # Validate required fields
                    if "action" not in step or "result" not in step:
                        raise ValidationError(
                            "Each step must have 'action' and 'result' fields"
                        )
                    step_dict = {"action": step["action"], "result": step["result"]}
                    if "data" in step and step["data"]:
                        step_dict["data"] = step["data"]
                    step_data.append(step_dict)
                else:
                    raise ValidationError(
                        "Steps must be either TestStep objects or dictionaries"
                    )

            # Based on actual createTest GraphQL schema from documentation
            mutation = """
            mutation CreateTest($testType: UpdateTestTypeInput!, $steps: [CreateStepInput!], $fields: JSON!) {
                createTest(testType: $testType, steps: $steps, jira: { fields: $fields }) {
                    test {
                        issueId
                        testType {
                            name
                        }
                        steps {
                            action
                            data
                            result
                        }
                        jira(fields: ["key", "summary"])
                    }
                    warnings
                }
            }
            """

            variables = {
                "testType": {"name": test_type},
                "steps": step_data,
                "fields": jira_fields,
            }

        elif test_type.lower() == "manual":
            # Manual test without steps (empty steps array)
            mutation = """
            mutation CreateTest($testType: UpdateTestTypeInput!, $fields: JSON!) {
                createTest(testType: $testType, jira: { fields: $fields }) {
                    test {
                        issueId
                        testType {
                            name
                        }
                        steps {
                            id
                            action
                            data
                            result
                        }
                        jira(fields: ["key", "summary"])
                    }
                    warnings
                }
            }
            """

            variables = {
                "testType": {"name": test_type},
                "fields": jira_fields,
            }

        elif test_type.lower() == "cucumber" and gherkin:
            # Cucumber test requires Gherkin scenario text
            # Uses a different mutation that accepts gherkin parameter
            mutation = """
            mutation CreateTest($testType: UpdateTestTypeInput!, $gherkin: String!, $fields: JSON!) {
                createTest(testType: $testType, gherkin: $gherkin, jira: { fields: $fields }) {
                    test {
                        issueId
                        testType {
                            name
                        }
                        gherkin
                        jira(fields: ["key", "summary"])
                    }
                    warnings
                }
            }
            """

            variables = {
                "testType": {"name": test_type},
                "gherkin": gherkin,
                "fields": jira_fields,
            }

        else:
            # Generic test or fallback for other test types
            # Uses unstructured field for free-form test content
            mutation = """
            mutation CreateTest($testType: UpdateTestTypeInput!, $unstructured: String, $fields: JSON!) {
                createTest(testType: $testType, unstructured: $unstructured, jira: { fields: $fields }) {
                    test {
                        issueId
                        testType {
                            name
                        }
                        unstructured
                        jira(fields: ["key", "summary"])
                    }
                    warnings
                }
            }
            """

            variables = {
                "testType": {"name": test_type},
                "unstructured": unstructured or "",
                "fields": jira_fields,
            }

        result = await self.client.execute_mutation(mutation, variables)

        if "data" in result and "createTest" in result["data"]:
            return result["data"]["createTest"]
        else:
            # Provide more detailed error context for test creation failures
            error_msg = "Failed to create test"
            if "errors" in result:
                error_details = result["errors"]
                if any("validation" in str(error).lower() for error in error_details):
                    if test_type.lower() == "manual" and steps:
                        error_msg += f". Manual test with {len(steps)} steps failed validation. " \
                                   "Ensure each step has 'action' and 'result' fields. " \
                                   "Example: {{'action': 'Navigate to page', 'result': 'Page loads', 'data': 'Optional data'}}"
                    else:
                        error_msg += f". Validation error for {test_type} test."
                error_msg += f" GraphQL errors: {error_details}"
            raise GraphQLError(error_msg)

    async def delete_test(self, issue_id: str) -> Dict[str, Any]:
        """Delete a test from Xray.

        Permanently deletes a test and all its associated data including
        steps, executions history, and attachments. Accepts both
        numeric issue IDs and Jira keys for convenience.

        Args:
            issue_id (str): Jira issue ID or key (e.g., "1162822" or "TEST-123")

        Returns:
            Dict[str, Any]: Deletion result containing:
                - success: Boolean indicating deletion success
                - issueId: The deleted test's issue ID

        Raises:
            GraphQLError: If deletion fails or test doesn't exist

        Complexity: O(1) - Single GraphQL mutation

        Warning:
            This operation is irreversible. The test and all its
            associated data will be permanently deleted.
        """
        mutation = """
        mutation DeleteTest($issueId: String!) {
            deleteTest(issueId: $issueId)
        }
        """

        # Resolve the identifier to a numeric issue ID
        resolved_id = await self.id_resolver.resolve_issue_id(issue_id)

        variables = {"issueId": resolved_id}
        result = await self.client.execute_mutation(mutation, variables)

        if "data" in result and "deleteTest" in result["data"]:
            return {"success": result["data"]["deleteTest"], "issueId": resolved_id}
        else:
            # Provide more context for deletion failures
            error_msg = f"Failed to delete test {issue_id}"
            if "errors" in result:
                error_details = result["errors"]
                if any("not found" in str(error).lower() for error in error_details):
                    error_msg += f". Test with ID/key '{issue_id}' not found. Verify the test exists and you have permission to delete it."
                error_msg += f" GraphQL errors: {error_details}"
            raise GraphQLError(error_msg)

    async def _update_gherkin_definition(
        self, issue_id: str, gherkin: str, version_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update the Gherkin definition of a Cucumber test.

        Args:
            issue_id (str): Resolved numeric issue ID
            gherkin (str): New Gherkin scenario content
            version_id (Optional[int]): Specific test version to update

        Returns:
            Dict[str, Any]: Update result from GraphQL

        Raises:
            GraphQLError: If update fails
        """
        mutation = """
        mutation UpdateGherkinTestDefinition($issueId: String!, $gherkin: String!, $versionId: Int) {
            updateGherkinTestDefinition(issueId: $issueId, gherkin: $gherkin, versionId: $versionId) {
                issueId
                gherkin
            }
        }
        """

        variables = {"issueId": issue_id, "gherkin": gherkin}
        if version_id is not None:
            variables["versionId"] = version_id

        result = await self.client.execute_mutation(mutation, variables)

        if "data" in result and "updateGherkinTestDefinition" in result["data"]:
            return result["data"]["updateGherkinTestDefinition"]
        else:
            error_msg = f"Failed to update Gherkin definition for test {issue_id}"
            if "errors" in result:
                error_msg += f". GraphQL errors: {result['errors']}"
            raise GraphQLError(error_msg)

    async def _update_unstructured_definition(
        self, issue_id: str, unstructured: str, version_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update the unstructured definition of a Generic test.

        Args:
            issue_id (str): Resolved numeric issue ID
            unstructured (str): New unstructured test content
            version_id (Optional[int]): Specific test version to update

        Returns:
            Dict[str, Any]: Update result from GraphQL

        Raises:
            GraphQLError: If update fails
        """
        mutation = """
        mutation UpdateUnstructuredTestDefinition($issueId: String!, $unstructured: String!, $versionId: Int) {
            updateUnstructuredTestDefinition(issueId: $issueId, unstructured: $unstructured, versionId: $versionId) {
                issueId
                unstructured
            }
        }
        """

        variables = {"issueId": issue_id, "unstructured": unstructured}
        if version_id is not None:
            variables["versionId"] = version_id

        result = await self.client.execute_mutation(mutation, variables)

        if "data" in result and "updateUnstructuredTestDefinition" in result["data"]:
            return result["data"]["updateUnstructuredTestDefinition"]
        else:
            error_msg = f"Failed to update unstructured definition for test {issue_id}"
            if "errors" in result:
                error_msg += f". GraphQL errors: {result['errors']}"
            raise GraphQLError(error_msg)

    async def update_test(
        self,
        issue_id: str,
        test_type: Optional[str] = None,
        gherkin: Optional[str] = None,
        unstructured: Optional[str] = None,
        steps: Optional[Union[List[Dict[str, str]], List[TestStep]]] = None,
        jira_fields: Optional[Dict[str, Any]] = None,
        version_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update various aspects of an existing test.

        Comprehensive test update method that can modify test type, content,
        steps, and Jira fields in a single operation. Updates are performed
        in sequence: test type first, then content, then Jira fields.

        Args:
            issue_id (str): Jira issue ID or key (e.g., "1162822" or "TEST-123")
            test_type (Optional[str]): New test type ("Manual", "Cucumber", "Generic")
            gherkin (Optional[str]): New Gherkin scenario (for Cucumber tests)
            unstructured (Optional[str]): New unstructured content (for Generic tests)
            steps (Optional[List]): New test steps (for Manual tests)
            jira_fields (Optional[Dict[str, Any]]): Jira fields to update
                (e.g., {"summary": "New title", "description": "New description"})
            version_id (Optional[int]): Specific test version to update

        Returns:
            Dict[str, Any]: Combined update results containing:
                - success: Overall success status
                - updated_fields: List of successfully updated fields
                - test: Final test state (if retrievable)
                - warnings: Any warnings from operations
                - errors: Any errors encountered

        Raises:
            ValidationError: If no update parameters provided or invalid parameters
            GraphQLError: If critical updates fail

        Complexity: O(k) where k is the number of update operations

        Example:
            # Update test type and content
            result = await tools.update_test(
                "TEST-123",
                test_type="Manual",
                steps=[
                    {"action": "Login", "result": "User logged in"},
                    {"action": "Navigate", "result": "Page loaded"}
                ]
            )

            # Update Gherkin scenario
            result = await tools.update_test(
                "TEST-456",
                gherkin="Scenario: Login\\nGiven I am on login page\\nWhen I enter credentials\\nThen I am logged in"
            )

            # Update Jira fields only
            result = await tools.update_test(
                "TEST-789",
                jira_fields={"summary": "Updated test title", "description": "New description"}
            )
        """
        # Validate that at least one update parameter is provided
        update_params = [test_type, gherkin, unstructured, steps, jira_fields]
        if not any(param is not None for param in update_params):
            raise ValidationError(
                "At least one update parameter must be provided: "
                "test_type, gherkin, unstructured, steps, or jira_fields"
            )

        # Resolve the identifier to a numeric issue ID
        resolved_id = await self.id_resolver.resolve_issue_id(issue_id)

        # Initialize result tracking
        updated_fields = []
        warnings = []
        errors = []
        test_result = None

        # Step 1: Update test type if specified
        if test_type is not None:
            try:
                type_result = await self._update_test_type_internal(
                    resolved_id, test_type, version_id
                )
                updated_fields.append("test_type")
                test_result = type_result
            except GraphQLError as e:
                errors.append(f"Test type update failed: {str(e)}")

        # Step 2: Update content based on test type
        current_test_type = test_type
        if current_test_type is None:
            # Need to get current test type to determine which content updates are valid
            try:
                current_test = await self.get_test(resolved_id)
                current_test_type = current_test.get("testType", {}).get("name", "").lower()
            except GraphQLError as e:
                errors.append(f"Could not determine current test type: {str(e)}")
                current_test_type = None

        # Update Gherkin definition (for Cucumber tests)
        if gherkin is not None:
            if current_test_type and current_test_type.lower() != "cucumber":
                warnings.append(
                    f"Gherkin update requested but test type is '{current_test_type}', not Cucumber"
                )
            try:
                await self._update_gherkin_definition(resolved_id, gherkin, version_id)
                updated_fields.append("gherkin")
            except GraphQLError as e:
                errors.append(f"Gherkin update failed: {str(e)}")

        # Update unstructured definition (for Generic tests)
        if unstructured is not None:
            if current_test_type and current_test_type.lower() != "generic":
                warnings.append(
                    f"Unstructured update requested but test type is '{current_test_type}', not Generic"
                )
            try:
                await self._update_unstructured_definition(resolved_id, unstructured, version_id)
                updated_fields.append("unstructured")
            except GraphQLError as e:
                errors.append(f"Unstructured content update failed: {str(e)}")

        # Update test steps (for Manual tests)
        if steps is not None:
            if current_test_type and current_test_type.lower() != "manual":
                warnings.append(
                    f"Steps update requested but test type is '{current_test_type}', not Manual"
                )
            else:
                # Note: Step updates require individual updateTestStep calls
                # This is a placeholder - actual implementation would need to handle
                # step creation, updates, and deletions individually
                warnings.append("Step updates not yet implemented - requires individual step management")

        # Step 3: Update Jira fields if specified
        if jira_fields is not None:
            # Xray GraphQL API does not provide a direct mutation for updating Jira fields
            # on existing tests. Jira field updates require direct Jira REST API integration.
            # Valid alternatives:
            # 1. Use Jira REST API: PUT /rest/api/2/issue/{issueKey}
            # 2. Use Atlassian MCP server for Jira field updates
            # 3. Create a new test with updated fields instead of updating existing one
            warnings.append(
                "Jira field updates not supported via Xray GraphQL API. "
                "Use Jira REST API or Atlassian MCP server for field updates like summary, description, etc."
            )

        # Get final test state if possible
        if not errors or updated_fields:
            try:
                test_result = await self.get_test(resolved_id)
            except GraphQLError as e:
                warnings.append(f"Could not retrieve updated test state: {str(e)}")

        return {
            "success": len(errors) == 0,
            "updated_fields": updated_fields,
            "test": test_result,
            "warnings": warnings,
            "errors": errors,
        }

    async def _update_test_type_internal(
        self, resolved_id: str, test_type: str, version_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Internal method to update test type.

        Args:
            resolved_id (str): Numeric issue ID
            test_type (str): New test type
            version_id (Optional[int]): Specific test version

        Returns:
            Dict[str, Any]: Update result from GraphQL

        Raises:
            GraphQLError: If update fails
        """
        mutation = """
        mutation UpdateTestType($issueId: String!, $testType: UpdateTestTypeInput!, $versionId: Int) {
            updateTestType(issueId: $issueId, testType: $testType, versionId: $versionId) {
                issueId
                testType {
                    name
                    kind
                }
            }
        }
        """

        variables = {"issueId": resolved_id, "testType": {"name": test_type}}
        if version_id is not None:
            variables["versionId"] = version_id

        result = await self.client.execute_mutation(mutation, variables)

        if "data" in result and "updateTestType" in result["data"]:
            return result["data"]["updateTestType"]
        else:
            error_msg = f"Failed to update test type to {test_type}"
            if "errors" in result:
                error_details = result["errors"]
                if any("not valid" in str(error).lower() for error in error_details):
                    error_msg += f". Test ID '{resolved_id}' is not valid or test type '{test_type}' is not supported."
                error_msg += f" GraphQL errors: {error_details}"
            raise GraphQLError(error_msg)

    async def update_test_type(self, issue_id: str, test_type: str) -> Dict[str, Any]:
        """Update the test type of an existing test.

        DEPRECATED: Use update_test() instead for more comprehensive updates.

        Changes the test type while preserving as much content as possible.
        Note that changing test types may result in data loss if the new
        type doesn't support the existing content format. Accepts both
        numeric issue IDs and Jira keys for convenience.

        Args:
            issue_id (str): Jira issue ID or key (e.g., "1162822" or "TEST-123")
            test_type (str): New test type ("Manual", "Cucumber", or "Generic")

        Returns:
            Dict[str, Any]: Update result containing:
                - issueId: Test issue ID
                - testType: Updated test type information

        Raises:
            GraphQLError: If update fails or test doesn't exist

        Complexity: O(1) - Single GraphQL mutation

        Warning:
            This method is deprecated. Use update_test() instead:
            update_test(issue_id, test_type=test_type)

        Example:
            # Deprecated usage
            result = await tools.update_test_type("TEST-123", "Manual")
            
            # Preferred usage
            result = await tools.update_test("TEST-123", test_type="Manual")
        """
        import warnings
        warnings.warn(
            "update_test_type is deprecated. Use update_test(issue_id, test_type=test_type) instead.",
            DeprecationWarning,
            stacklevel=2
        )

        # Use the new update_test method
        result = await self.update_test(issue_id, test_type=test_type)
        
        # Return the test type update result for backwards compatibility
        if result["success"] and result["test"]:
            return {
                "issueId": result["test"].get("issueId"),
                "testType": result["test"].get("testType")
            }
        elif result["errors"]:
            raise GraphQLError("; ".join(result["errors"]))
        else:
            raise GraphQLError("Test type update failed")
