"""Utility tools for Xray MCP server."""

from typing import Dict, Any, Optional

try:
    from ..client import XrayGraphQLClient
    from ..exceptions import GraphQLError
    from ..validators import validate_jql
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError
    from validators import validate_jql


class UtilityTools:
    """Utility tools for Xray operations."""
    
    def __init__(self, graphql_client: XrayGraphQLClient):
        self.client = graphql_client
    
    async def execute_jql_query(self, jql: str, entity_type: str = "test", limit: int = 100) -> Dict[str, Any]:
        """Execute a custom JQL query for different entity types.
        
        Validates the JQL query to prevent injection attacks before execution.
        
        Args:
            jql: JQL query string (validated against whitelist)
            entity_type: Type of entity to query ("test" or "testexecution")
            limit: Maximum number of results (default 100)
            
        Returns:
            Query results with pagination info
            
        Raises:
            ValidationError: If JQL contains dangerous patterns
            GraphQLError: If query execution fails
        """
        # Validate and sanitize JQL to prevent injection
        safe_jql = validate_jql(jql)
        
        if entity_type.lower() == "test":
            return await self._execute_test_jql(safe_jql, limit)
        elif entity_type.lower() == "testexecution":
            return await self._execute_test_execution_jql(safe_jql, limit)
        else:
            raise GraphQLError(f"Unsupported entity type: {entity_type}")
    
    async def _execute_test_jql(self, jql: str, limit: int) -> Dict[str, Any]:
        """Execute JQL query for tests."""
        query = """
        query ExecuteTestJQL($jql: String!, $limit: Int!) {
            getTests(jql: $jql, limit: $limit) {
                total
                start
                limit
                results {
                    issueId
                    testType {
                        name
                    }
                    jira(fields: ["key", "summary", "status", "assignee"])
                }
            }
        }
        """
        
        variables = {"jql": jql, "limit": limit}
        result = await self.client.execute_query(query, variables)
        
        if "data" in result and "getTests" in result["data"]:
            return result["data"]["getTests"]
        else:
            raise GraphQLError("Failed to execute JQL query for tests")
    
    async def _execute_test_execution_jql(self, jql: str, limit: int) -> Dict[str, Any]:
        """Execute JQL query for test executions."""
        query = """
        query ExecuteTestExecutionJQL($jql: String!, $limit: Int!) {
            getTestExecutions(jql: $jql, limit: $limit) {
                total
                start
                limit
                results {
                    issueId
                    jira(fields: ["key", "summary", "status", "assignee"])
                }
            }
        }
        """
        
        variables = {"jql": jql, "limit": limit}
        result = await self.client.execute_query(query, variables)
        
        if "data" in result and "getTestExecutions" in result["data"]:
            return result["data"]["getTestExecutions"]
        else:
            raise GraphQLError("Failed to execute JQL query for test executions")
    
    async def validate_connection(self) -> Dict[str, Any]:
        """Test connection and authentication with Xray."""
        try:
            # Try to get a simple query to validate connection
            query = """
            query ValidateConnection {
                getTests(limit: 1) {
                    total
                }
            }
            """
            
            result = await self.client.execute_query(query)
            
            if "data" in result:
                return {
                    "status": "connected",
                    "message": "Successfully connected to Xray API",
                    "authenticated": True
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to validate connection",
                    "authenticated": False
                }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection validation failed: {str(e)}",
                "authenticated": False
            }

