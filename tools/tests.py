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
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError
    from validators import validate_jql


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

    async def _resolve_issue_id(self, identifier: str) -> str:
        """Resolve a Jira key or issue ID to a numeric issue ID.

        Args:
            identifier: Either a Jira key (e.g., "TEST-123") or numeric issue ID (e.g., "1162822")

        Returns:
            str: Numeric issue ID that can be used with GraphQL queries

        Raises:
            GraphQLError: If the identifier cannot be resolved
        """
        # If it's already numeric, return as-is
        if identifier.isdigit():
            return identifier

        # If it looks like a Jira key (contains dash), try to resolve it
        if "-" in identifier:
            # Use JQL query to find the issue ID for this key
            query = """
            query GetTestByKey($jql: String!, $limit: Int!) {
                getTests(jql: $jql, limit: $limit) {
                    results {
                        issueId
                        jira(fields: ["key"])
                    }
                }
            }
            """

            variables = {"jql": f'key = "{identifier}"', "limit": 1}
            result = await self.client.execute_query(query, variables)

            if (
                "data" in result
                and "getTests" in result["data"]
                and result["data"]["getTests"]["results"]
            ):
                return result["data"]["getTests"]["results"][0]["issueId"]
            else:
                raise GraphQLError(
                    f"Could not resolve Jira key {identifier} to issue ID"
                )

        # If it's neither numeric nor contains dash, assume it's already an issue ID
        return identifier

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
        resolved_id = await self._resolve_issue_id(issue_id)

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
        resolved_id = await self._resolve_issue_id(issue_id)

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
            mutation CreateTest($testType: UpdateTestTypeInput!, $steps: [CreateStepInput!]!, $jira: JSON!) {
                createTest(testType: $testType, steps: $steps, jira: $jira) {
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
                "jira": {"fields": jira_fields},
            }

        elif test_type.lower() == "manual":
            # Manual test without steps (empty steps array)
            mutation = """
            mutation CreateTest($testType: UpdateTestTypeInput!, $jira: JSON!) {
                createTest(testType: $testType, jira: $jira) {
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
                "jira": {"fields": jira_fields},
            }

        elif test_type.lower() == "cucumber" and gherkin:
            # Cucumber test requires Gherkin scenario text
            # Uses a different mutation that accepts gherkin parameter
            mutation = """
            mutation CreateTest($testType: UpdateTestTypeInput!, $gherkin: String!, $jira: JSON!) {
                createTest(testType: $testType, gherkin: $gherkin, jira: $jira) {
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
                "jira": {"fields": jira_fields},
            }

        else:
            # Generic test or fallback for other test types
            # Uses unstructured field for free-form test content
            mutation = """
            mutation CreateTest($testType: UpdateTestTypeInput!, $unstructured: String, $jira: JSON!) {
                createTest(testType: $testType, unstructured: $unstructured, jira: $jira) {
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
                "jira": {"fields": jira_fields},
            }

        result = await self.client.execute_mutation(mutation, variables)

        if "data" in result and "createTest" in result["data"]:
            return result["data"]["createTest"]
        else:
            raise GraphQLError("Failed to create test")

    async def delete_test(self, issue_id: str) -> Dict[str, Any]:
        """Delete a test from Xray.

        Permanently deletes a test and all its associated data including
        steps, executions history, and attachments.

        Args:
            issue_id (str): Jira issue ID of the test to delete

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

        variables = {"issueId": issue_id}
        result = await self.client.execute_mutation(mutation, variables)

        if "data" in result and "deleteTest" in result["data"]:
            return {"success": result["data"]["deleteTest"], "issueId": issue_id}
        else:
            raise GraphQLError(f"Failed to delete test {issue_id}")

    async def update_test_type(self, issue_id: str, test_type: str) -> Dict[str, Any]:
        """Update the test type of an existing test.

        Changes the test type while preserving as much content as possible.
        Note that changing test types may result in data loss if the new
        type doesn't support the existing content format.

        Args:
            issue_id (str): Jira issue ID of the test to update
            test_type (str): New test type ("Manual", "Cucumber", or "Generic")

        Returns:
            Dict[str, Any]: Update result containing:
                - test: Updated test object with new type
                - warnings: Any warnings about potential data loss

        Raises:
            GraphQLError: If update fails or test doesn't exist

        Complexity: O(1) - Single GraphQL mutation

        Warning:
            Changing test types may result in content loss:
            - Manual → Cucumber: Steps will be lost
            - Cucumber → Manual: Gherkin will be lost
            - Any → Generic: Structure will be flattened

        Example:
            # Convert a Generic test to Manual
            result = await tools.update_test_type("TEST-123", "Manual")
            if result["warnings"]:
                print(f"Warnings: {result['warnings']}")
        """
        mutation = """
        mutation UpdateTestType($issueId: String!, $testType: UpdateTestTypeInput!) {
            updateTestType(issueId: $issueId, testType: $testType) {
                issueId
                testType {
                    name
                    kind
                }
            }
        }
        """

        variables = {"issueId": issue_id, "testType": {"name": test_type}}

        result = await self.client.execute_mutation(mutation, variables)

        if "data" in result and "updateTestType" in result["data"]:
            return result["data"]["updateTestType"]
        else:
            raise GraphQLError(f"Failed to update test type for {issue_id}")
