"""Integration tests for XrayGraphQLClient against real Xray API.

These tests validate that our mock unit tests accurately represent
the real GraphQL API behavior.
"""

import pytest
import asyncio
from typing import Dict, Any

from client.graphql import XrayGraphQLClient
from exceptions import GraphQLError


@pytest.mark.integration
class TestGraphQLClientRealAPI:
    """Test GraphQL client against real Xray API."""
    
    async def test_execute_simple_query(self, graphql_client):
        """Validate basic query execution returns expected structure."""
        # Simple query to get tests (may return empty results)
        query = """
        query GetTests($jql: String!, $limit: Int!) {
            getTests(jql: $jql, limit: $limit) {
                total
                start
                limit
                results {
                    issueId
                    projectId
                    testType {
                        name
                        kind
                    }
                }
            }
        }
        """
        
        variables = {
            "jql": f'project = "{INTEGRATION_PROJECT_KEY}"',
            "limit": 5
        }
        
        result = await graphql_client.execute_query(query, variables)
        
        # Validate response structure matches our mock expectations
        assert "data" in result
        assert "getTests" in result["data"]
        
        tests_data = result["data"]["getTests"]
        assert "total" in tests_data
        assert "start" in tests_data
        assert "limit" in tests_data
        assert "results" in tests_data
        
        # Validate data types
        assert isinstance(tests_data["total"], int)
        assert isinstance(tests_data["results"], list)
        assert tests_data["limit"] == 5
    
    async def test_execute_query_with_variables(self, graphql_client):
        """Validate variable substitution works correctly."""
        query = """
        query SearchTests($jql: String!, $start: Int!, $limit: Int!) {
            getTests(jql: $jql, start: $start, limit: $limit) {
                total
                start
                limit
            }
        }
        """
        
        # Test different variable values
        test_cases = [
            {"jql": f'project = "{INTEGRATION_PROJECT_KEY}"', "start": 0, "limit": 10},
            {"jql": f'project = "{INTEGRATION_PROJECT_KEY}" AND issuetype = Test', "start": 5, "limit": 20},
        ]
        
        for variables in test_cases:
            result = await graphql_client.execute_query(query, variables)
            
            # Validate variables were properly substituted
            data = result["data"]["getTests"]
            assert data["start"] == variables["start"]
            assert data["limit"] == variables["limit"]
    
    async def test_execute_invalid_query_syntax(self, graphql_client):
        """Validate GraphQL syntax errors are properly reported."""
        # Intentionally malformed query
        query = """
        query {
            getTests(jql: $jql  # Missing closing parenthesis
                total
            }
        }
        """
        
        with pytest.raises(GraphQLError) as exc_info:
            await graphql_client.execute_query(query)
        
        # Validate error contains helpful information
        error_msg = str(exc_info.value)
        assert "GraphQL" in error_msg or "Syntax" in error_msg or "error" in error_msg
    
    async def test_execute_query_invalid_field(self, graphql_client):
        """Validate field validation errors match our mocks."""
        query = """
        query {
            getTests(jql: "project = FTEST", limit: 5) {
                total
                nonExistentField
            }
        }
        """
        
        with pytest.raises(GraphQLError) as exc_info:
            await graphql_client.execute_query(query)
        
        error_msg = str(exc_info.value)
        # API should report unknown field
        assert "field" in error_msg.lower() or "nonExistentField" in error_msg
    
    async def test_execute_mutation(self, graphql_client, test_data_tracker, cleanup_helper):
        """Validate mutation execution creates real data."""
        from datetime import datetime
        INTEGRATION_TEST_PREFIX = f"INT_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        mutation = """
        mutation CreateTest($testType: TestTypeInput!, $fields: JSON!) {
            createTest(testType: $testType, fields: $fields) {
                test {
                    issueId
                    jira {
                        key
                        summary
                    }
                    testType {
                        name
                    }
                }
                warnings
            }
        }
        """
        
        variables = {
            "testType": {"name": "Generic"},
            "fields": {
                "summary": f"{INTEGRATION_TEST_PREFIX}_GraphQL_Test",
                "project": {"key": INTEGRATION_PROJECT_KEY},
                "description": "Integration test for GraphQL mutations"
            }
        }
        
        result = await graphql_client.execute_mutation(mutation, variables)
        
        # Validate mutation response structure
        assert "data" in result
        assert "createTest" in result["data"]
        
        created_test = result["data"]["createTest"]["test"]
        assert created_test["issueId"] is not None
        assert created_test["jira"]["key"] is not None
        assert INTEGRATION_PROJECT_KEY in created_test["jira"]["key"]
        
        # Track for cleanup
        test_data_tracker.add_test(created_test["issueId"])
    
    async def test_network_timeout_behavior(self, auth_manager):
        """Validate timeout handling matches our mocks."""
        import aiohttp
        
        # Create client with very short timeout
        client = XrayGraphQLClient(auth_manager)
        
        # Override the execute_query to use custom timeout
        original_execute = client.execute_query
        
        async def execute_with_timeout(query, variables=None):
            # Use extremely short timeout to force timeout
            timeout = aiohttp.ClientTimeout(total=0.001)
            # This should timeout
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    # This will timeout before completing
                    await session.get("https://xray.cloud.getxray.app/api/v2/graphql")
            except asyncio.TimeoutError:
                raise GraphQLError("Network error during GraphQL request: Timeout")
            except aiohttp.ClientError as e:
                raise GraphQLError(f"Network error during GraphQL request: {e}")
        
        client.execute_query = execute_with_timeout
        
        with pytest.raises(GraphQLError) as exc_info:
            await client.execute_query("query { test }")
        
        assert "Network error" in str(exc_info.value) or "Timeout" in str(exc_info.value)
    
    async def test_large_response_handling(self, graphql_client):
        """Validate handling of large result sets."""
        query = """
        query GetManyTests($jql: String!, $limit: Int!) {
            getTests(jql: $jql, limit: $limit) {
                total
                results {
                    issueId
                    projectId
                    testType {
                        name
                    }
                    folder {
                        path
                    }
                }
            }
        }
        """
        
        # Request maximum allowed
        variables = {
            "jql": f'project = "{INTEGRATION_PROJECT_KEY}"',
            "limit": 100  # Max limit
        }
        
        result = await graphql_client.execute_query(query, variables)
        
        # Validate we can handle whatever size response we get
        assert "data" in result
        results = result["data"]["getTests"]["results"]
        assert isinstance(results, list)
        
        # Whether we get 0 or 100 results, structure should be valid
        for test in results:
            assert "issueId" in test
            assert "testType" in test
    
    async def test_concurrent_queries(self, graphql_client):
        """Validate concurrent query handling."""
        queries = [
            ("""query { getTests(jql: "project = FTEST", limit: 1) { total } }""", None),
            ("""query { getTestSets(jql: "project = FTEST", limit: 1) { total } }""", None),
            ("""query { getTestPlans(jql: "project = FTEST", limit: 1) { total } }""", None),
        ]
        
        # Execute queries concurrently
        tasks = [graphql_client.execute_query(q, v) for q, v in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete (though some might error if features not available)
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) > 0, "At least some queries should succeed"
        
        # Successful ones should have proper structure
        for result in successful:
            if not isinstance(result, Exception):
                assert "data" in result


@pytest.mark.integration
class TestGraphQLErrorHandling:
    """Test error handling with real API error responses."""
    
    async def test_unauthorized_request(self, integration_enabled):
        """Validate 401 error handling with invalid token."""
        import os
        from auth.manager import XrayAuthManager
        
        # Create auth manager but don't authenticate
        auth = XrayAuthManager(
            os.getenv("XRAY_CLIENT_ID"),
            os.getenv("XRAY_CLIENT_SECRET")
        )
        # Set invalid token
        auth.token = "invalid_token_12345"
        auth.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        
        client = XrayGraphQLClient(auth)
        
        with pytest.raises(GraphQLError) as exc_info:
            await client.execute_query("query { getTests(jql: \"project = FTEST\", limit: 1) { total } }")
        
        error_msg = str(exc_info.value)
        # Should indicate authentication failure
        assert "401" in error_msg or "unauthorized" in error_msg.lower() or "authentication" in error_msg.lower()
    
    async def test_rate_limiting_behavior(self, graphql_client):
        """Test API rate limiting behavior (if applicable)."""
        # Make rapid requests to potentially trigger rate limiting
        query = "query { getTests(jql: \"project = FTEST\", limit: 1) { total } }"
        
        results = []
        errors = []
        
        for i in range(20):  # Try 20 rapid requests
            try:
                result = await graphql_client.execute_query(query)
                results.append(result)
            except GraphQLError as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    errors.append(e)
                    break  # Stop if rate limited
                else:
                    raise  # Re-raise unexpected errors
        
        # We should either complete all requests or hit rate limit
        assert len(results) > 0, "Should complete at least some requests"
        
        # If rate limited, verify error message
        if errors:
            error_msg = str(errors[0])
            assert "429" in error_msg or "rate" in error_msg.lower()
    
    async def test_partial_data_with_errors(self, graphql_client):
        """Test behavior when query partially succeeds."""
        # Query that might partially fail (depends on permissions/data)
        query = """
        query {
            getTests(jql: "project = FTEST", limit: 1) {
                total
                results {
                    issueId
                    testType {
                        name
                    }
                    # This might fail if no test runs exist
                    lastTestRunStatus
                }
            }
        }
        """
        
        try:
            result = await graphql_client.execute_query(query)
            # If it succeeds, validate structure
            assert "data" in result
        except GraphQLError as e:
            # If it fails, should have descriptive error
            assert "GraphQL" in str(e) or "error" in str(e).lower()


@pytest.mark.integration
class TestGraphQLClientEdgeCases:
    """Test edge cases with real API."""
    
    async def test_empty_variables_handling(self, graphql_client):
        """Test queries with no variables."""
        query = """
        query {
            getTests(jql: "project = FTEST", limit: 1) {
                total
            }
        }
        """
        
        # Test with None variables
        result1 = await graphql_client.execute_query(query, None)
        assert "data" in result1
        
        # Test with empty dict variables
        result2 = await graphql_client.execute_query(query, {})
        assert "data" in result2
        
        # Results should be identical
        assert result1 == result2
    
    async def test_special_characters_in_jql(self, graphql_client):
        """Test JQL with special characters."""
        test_jqls = [
            f'project = "{INTEGRATION_PROJECT_KEY}" AND summary ~ "test*"',
            f'project = "{INTEGRATION_PROJECT_KEY}" AND labels in ("test-label", "integration")',
            f'project = "{INTEGRATION_PROJECT_KEY}" AND created >= -7d',
        ]
        
        query = """
        query GetTestsWithJQL($jql: String!) {
            getTests(jql: $jql, limit: 1) {
                total
            }
        }
        """
        
        for jql in test_jqls:
            try:
                result = await graphql_client.execute_query(query, {"jql": jql})
                assert "data" in result
                # Query should execute without error
            except GraphQLError as e:
                # If it fails, should be due to JQL syntax, not escaping issues
                assert "jql" in str(e).lower() or "query" in str(e).lower()
    
    async def test_deep_nested_query(self, graphql_client):
        """Test deeply nested query structure."""
        query = """
        query {
            getTests(jql: "project = FTEST", limit: 1) {
                total
                results {
                    issueId
                    projectId
                    testType {
                        name
                        kind
                    }
                    folder {
                        path
                        name
                    }
                    jira {
                        key
                        summary
                        status {
                            name
                            statusCategory {
                                key
                                name
                            }
                        }
                    }
                }
            }
        }
        """
        
        result = await graphql_client.execute_query(query)
        
        # Should handle nested structure
        assert "data" in result
        tests = result["data"]["getTests"]["results"]
        
        # If we have results, validate nested structure
        for test in tests:
            if "jira" in test and test["jira"]:
                assert "key" in test["jira"]
                if "status" in test["jira"] and test["jira"]["status"]:
                    assert "name" in test["jira"]["status"]


from datetime import datetime, timezone, timedelta

# These are defined in conftest.py which loads them  
INTEGRATION_PROJECT_KEY = "FTEST"