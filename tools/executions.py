"""Test execution management tools for Xray MCP server."""

from typing import Dict, Any, List, Optional

try:
    from ..client import XrayGraphQLClient
    from ..exceptions import GraphQLError, ValidationError
    from ..validators import validate_jql
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError, ValidationError
    from validators import validate_jql


class TestExecutionTools:
    """Tools for managing test executions in Xray."""
    
    def __init__(self, graphql_client: XrayGraphQLClient):
        self.client = graphql_client
    
    async def get_test_execution(self, issue_id: str) -> Dict[str, Any]:
        """Retrieve a single test execution by issue ID."""
        query = """
        query GetTestExecution($issueId: String!) {
            getTestExecution(issueId: $issueId) {
                issueId
                tests(limit: 100) {
                    total
                    start
                    limit
                    results {
                        issueId
                        testType {
                            name
                        }
                    }
                }
                jira(fields: ["key", "summary", "assignee", "reporter", "status", "priority"])
            }
        }
        """
        
        variables = {"issueId": issue_id}
        result = await self.client.execute_query(query, variables)
        
        if "data" in result and "getTestExecution" in result["data"]:
            return result["data"]["getTestExecution"]
        else:
            raise GraphQLError(f"Failed to retrieve test execution {issue_id}")
    
    async def get_test_executions(self, jql: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Retrieve multiple test executions with optional JQL filtering."""
        if limit > 100:
            raise ValidationError("Limit cannot exceed 100 due to Xray API restrictions")
        
        # Validate JQL if provided to prevent injection
        if jql:
            jql = validate_jql(jql)
        
        query = """
        query GetTestExecutions($jql: String, $limit: Int!) {
            getTestExecutions(jql: $jql, limit: $limit) {
                total
                start
                limit
                results {
                    issueId
                    tests(limit: 10) {
                        total
                        start
                        limit
                        results {
                            issueId
                            testType {
                                name
                            }
                        }
                    }
                    jira(fields: ["key", "summary", "assignee", "status"])
                }
            }
        }
        """
        
        variables = {"jql": jql, "limit": limit}
        result = await self.client.execute_query(query, variables)
        
        if "data" in result and "getTestExecutions" in result["data"]:
            return result["data"]["getTestExecutions"]
        else:
            raise GraphQLError("Failed to retrieve test executions")
    
    async def create_test_execution(
        self,
        project_key: str,
        summary: str,
        test_issue_ids: Optional[List[str]] = None,
        test_environments: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new test execution."""
        # Build the jira fields
        jira_fields = {
            "summary": summary,
            "project": {"key": project_key}
        }
        
        if description:
            jira_fields["description"] = description
        
        mutation = """
        mutation CreateTestExecution($testIssueIds: [String!], $testEnvironments: [String!], $jira: JiraFieldsInput!) {
            createTestExecution(testIssueIds: $testIssueIds, testEnvironments: $testEnvironments, jira: $jira) {
                testExecution {
                    issueId
                    jira(fields: ["key", "summary"])
                }
                warnings
                createdTestEnvironments
            }
        }
        """
        
        variables = {
            "testIssueIds": test_issue_ids or [],
            "testEnvironments": test_environments or [],
            "jira": {"fields": jira_fields}
        }
        
        result = await self.client.execute_mutation(mutation, variables)
        
        if "data" in result and "createTestExecution" in result["data"]:
            return result["data"]["createTestExecution"]
        else:
            raise GraphQLError("Failed to create test execution")
    
    async def delete_test_execution(self, issue_id: str) -> Dict[str, Any]:
        """Delete a test execution."""
        mutation = """
        mutation DeleteTestExecution($issueId: String!) {
            deleteTestExecution(issueId: $issueId)
        }
        """
        
        variables = {"issueId": issue_id}
        result = await self.client.execute_mutation(mutation, variables)
        
        if "data" in result and "deleteTestExecution" in result["data"]:
            return {"success": result["data"]["deleteTestExecution"], "issueId": issue_id}
        else:
            raise GraphQLError(f"Failed to delete test execution {issue_id}")
    
    async def add_tests_to_execution(self, execution_issue_id: str, test_issue_ids: List[str]) -> Dict[str, Any]:
        """Add tests to a test execution."""
        mutation = """
        mutation AddTestsToTestExecution($issueId: String!, $testIssueIds: [String!]!) {
            addTestsToTestExecution(issueId: $issueId, testIssueIds: $testIssueIds) {
                addedTests
                warning
            }
        }
        """
        
        variables = {
            "issueId": execution_issue_id,
            "testIssueIds": test_issue_ids
        }
        
        result = await self.client.execute_mutation(mutation, variables)
        
        if "data" in result and "addTestsToTestExecution" in result["data"]:
            return result["data"]["addTestsToTestExecution"]
        else:
            raise GraphQLError(f"Failed to add tests to execution {execution_issue_id}")
    
    async def remove_tests_from_execution(self, execution_issue_id: str, test_issue_ids: List[str]) -> Dict[str, Any]:
        """Remove tests from a test execution."""
        mutation = """
        mutation RemoveTestsFromTestExecution($issueId: String!, $testIssueIds: [String!]!) {
            removeTestsFromTestExecution(issueId: $issueId, testIssueIds: $testIssueIds)
        }
        """
        
        variables = {
            "issueId": execution_issue_id,
            "testIssueIds": test_issue_ids
        }
        
        result = await self.client.execute_mutation(mutation, variables)
        
        if "data" in result and "removeTestsFromTestExecution" in result["data"]:
            return {"success": result["data"]["removeTestsFromTestExecution"], "executionId": execution_issue_id}
        else:
            raise GraphQLError(f"Failed to remove tests from execution {execution_issue_id}")
    
    async def add_test_environments(self, execution_issue_id: str, test_environments: List[str]) -> Dict[str, Any]:
        """Add test environments to a test execution."""
        mutation = """
        mutation AddTestEnvironmentsToTestExecution($issueId: String!, $testEnvironments: [String!]!) {
            addTestEnvironmentsToTestExecution(issueId: $issueId, testEnvironments: $testEnvironments) {
                associatedTestEnvironments
                createdTestEnvironments
            }
        }
        """
        
        variables = {
            "issueId": execution_issue_id,
            "testEnvironments": test_environments
        }
        
        result = await self.client.execute_mutation(mutation, variables)
        
        if "data" in result and "addTestEnvironmentsToTestExecution" in result["data"]:
            return result["data"]["addTestEnvironmentsToTestExecution"]
        else:
            raise GraphQLError(f"Failed to add test environments to execution {execution_issue_id}")
    
    async def remove_test_environments(self, execution_issue_id: str, test_environments: List[str]) -> Dict[str, Any]:
        """Remove test environments from a test execution."""
        mutation = """
        mutation RemoveTestEnvironmentsFromTestExecution($issueId: String!, $testEnvironments: [String!]!) {
            removeTestEnvironmentsFromTestExecution(issueId: $issueId, testEnvironments: $testEnvironments)
        }
        """
        
        variables = {
            "issueId": execution_issue_id,
            "testEnvironments": test_environments
        }
        
        result = await self.client.execute_mutation(mutation, variables)
        
        if "data" in result and "removeTestEnvironmentsFromTestExecution" in result["data"]:
            return {"success": result["data"]["removeTestEnvironmentsFromTestExecution"], "executionId": execution_issue_id}
        else:
            raise GraphQLError(f"Failed to remove test environments from execution {execution_issue_id}")

