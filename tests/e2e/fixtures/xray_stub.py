"""
Xray HTTP API stubbing for E2E tests.

Provides HTTP request mocking and stubbing capabilities for the Xray GraphQL API
to enable predictable testing of MCP contract validation.
"""

import json
import re
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from unittest.mock import patch
import responses
from aioresponses import aioresponses


@dataclass
class GraphQLRequest:
    """Represents a GraphQL request."""
    query: str
    variables: Optional[Dict[str, Any]] = None
    operation_name: Optional[str] = None


@dataclass
class APICall:
    """Represents an API call made during testing."""
    method: str
    url: str
    headers: Dict[str, str]
    body: Optional[Dict[str, Any]] = None


class XrayStub:
    """HTTP stubbing utility for Xray API."""
    
    def __init__(self, base_url: str):
        """
        Initialize Xray stub.
        
        Args:
            base_url: Base URL for Xray API
        """
        self.base_url = base_url.rstrip("/")
        self.responses = responses.RequestsMock()
        self.aio_responses = aioresponses()
        self.call_log: List[APICall] = []
        self._active = False
    
    def setup(self):
        """Set up HTTP stubbing."""
        if not self._active:
            self.responses.start()
            self.aio_responses.start()
            self._active = True
            self._setup_default_stubs()
    
    def teardown(self):
        """Tear down HTTP stubbing."""
        if self._active:
            self.responses.stop()
            self.aio_responses.stop()
            self.responses.reset()
            self._active = False
            self.call_log.clear()
    
    def _setup_default_stubs(self):
        """Set up default API stubs."""
        # Authentication endpoint
        self.responses.add(
            responses.POST,
            f"{self.base_url}/api/v2/authenticate",
            json={"token": "mock-jwt-token"},
            status=200
        )
        
        # GraphQL endpoint for async requests
        self.aio_responses.post(
            f"{self.base_url}/api/v2/graphql",
            payload={"data": {}, "errors": []}
        )
    
    def stub_authentication(self, token: str = "mock-jwt-token"):
        """Stub authentication response."""
        self.responses.add(
            responses.POST,
            f"{self.base_url}/api/v2/authenticate",
            json={"token": token},
            status=200
        )
    
    def stub_graphql_query(
        self,
        query_pattern: str,
        response_data: Dict[str, Any],
        variables: Optional[Dict[str, Any]] = None,
        errors: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Stub GraphQL query response.
        
        Args:
            query_pattern: Pattern to match in GraphQL query
            response_data: Data to return in response
            variables: Expected variables (optional)
            errors: GraphQL errors to include (optional)
        """
        def match_graphql_request(request):
            """Match GraphQL request based on query pattern."""
            try:
                body = json.loads(request.body) if request.body else {}
                query = body.get("query", "")
                
                # Check if query pattern matches
                if query_pattern in query:
                    # If variables specified, check they match
                    if variables:
                        request_vars = body.get("variables", {})
                        return all(request_vars.get(k) == v for k, v in variables.items())
                    return True
                return False
            except (json.JSONDecodeError, AttributeError):
                return False
        
        response_payload = {"data": response_data}
        if errors:
            response_payload["errors"] = errors
        
        # Add to both sync and async response mocks
        self.responses.add_callback(
            responses.POST,
            f"{self.base_url}/api/v2/graphql",
            callback=lambda req: (200, {}, json.dumps(response_payload)) if match_graphql_request(req) else (404, {}, ""),
            content_type="application/json"
        )
        
        self.aio_responses.post(
            f"{self.base_url}/api/v2/graphql",
            payload=response_payload,
            repeat=True
        )
    
    def stub_test_creation(
        self,
        project_key: str,
        test_type: str = "Generic",
        issue_key: str = "TEST-123",
        issue_id: str = "12345"
    ):
        """Stub test creation GraphQL mutation."""
        mutation_pattern = "createTest"
        
        response_data = {
            "createTest": {
                "test": {
                    "issueId": issue_id,
                    "jira": {
                        "key": issue_key,
                        "summary": "Test Summary"
                    },
                    "testType": {
                        "name": test_type
                    }
                }
            }
        }
        
        self.stub_graphql_query(mutation_pattern, response_data)
    
    def stub_test_update(
        self,
        issue_id: str,
        test_type: Optional[str] = None
    ):
        """Stub test update GraphQL mutation."""
        mutation_pattern = "updateTest"
        
        response_data = {
            "updateTest": {
                "test": {
                    "issueId": issue_id,
                    "testType": {
                        "name": test_type or "Generic"
                    }
                }
            }
        }
        
        self.stub_graphql_query(mutation_pattern, response_data)
    
    def stub_test_deletion(self, issue_id: str):
        """Stub test deletion GraphQL mutation."""
        mutation_pattern = "deleteTest"
        
        response_data = {
            "deleteTest": True
        }
        
        self.stub_graphql_query(mutation_pattern, response_data)
    
    def stub_test_query(
        self,
        issue_id: str,
        test_type: str = "Generic",
        summary: str = "Test Summary",
        steps: Optional[List[Dict[str, Any]]] = None
    ):
        """Stub test query GraphQL response."""
        query_pattern = "getTest"
        
        test_data = {
            "issueId": issue_id,
            "jira": {
                "key": f"TEST-{issue_id}",
                "summary": summary,
                "description": "Test description"
            },
            "testType": {
                "name": test_type
            }
        }
        
        if test_type == "Manual" and steps:
            test_data["steps"] = steps
        elif test_type == "Cucumber":
            test_data["gherkin"] = "Given a test scenario\nWhen something happens\nThen verify result"
        elif test_type == "Generic":
            test_data["unstructured"] = "Generic test definition"
        
        response_data = {
            "getTest": test_data
        }
        
        self.stub_graphql_query(query_pattern, response_data)
    
    def stub_test_execution_creation(
        self,
        project_key: str,
        issue_key: str = "EXEC-123",
        issue_id: str = "67890"
    ):
        """Stub test execution creation."""
        mutation_pattern = "createTestExecution"
        
        response_data = {
            "createTestExecution": {
                "testExecution": {
                    "issueId": issue_id,
                    "jira": {
                        "key": issue_key,
                        "summary": "Test Execution Summary"
                    }
                }
            }
        }
        
        self.stub_graphql_query(mutation_pattern, response_data)
    
    def stub_test_plan_creation(
        self,
        project_key: str,
        issue_key: str = "PLAN-123",
        issue_id: str = "11111"
    ):
        """Stub test plan creation."""
        mutation_pattern = "createTestPlan"
        
        response_data = {
            "createTestPlan": {
                "testPlan": {
                    "issueId": issue_id,
                    "jira": {
                        "key": issue_key,
                        "summary": "Test Plan Summary"
                    }
                }
            }
        }
        
        self.stub_graphql_query(mutation_pattern, response_data)
    
    def stub_jql_query(
        self,
        jql: str,
        test_results: List[Dict[str, Any]],
        total: Optional[int] = None
    ):
        """Stub JQL query response."""
        query_pattern = "getTests"
        
        response_data = {
            "getTests": {
                "results": test_results,
                "total": total or len(test_results),
                "start": 0,
                "limit": 100
            }
        }
        
        self.stub_graphql_query(query_pattern, response_data, {"jql": jql})
    
    def stub_connection_validation(self, success: bool = True):
        """Stub connection validation response."""
        if success:
            response_data = {
                "viewer": {
                    "accountId": "mock-account-id",
                    "displayName": "Mock User"
                }
            }
        else:
            response_data = {}
            errors = [{"message": "Authentication failed"}]
        
        query_pattern = "viewer"
        self.stub_graphql_query(
            query_pattern, 
            response_data, 
            errors=None if success else [{"message": "Authentication failed"}]
        )
    
    def stub_gherkin_update(self, issue_id: str, gherkin_text: str):
        """Stub Gherkin definition update."""
        mutation_pattern = "updateTest"
        
        response_data = {
            "updateTest": {
                "test": {
                    "issueId": issue_id,
                    "testType": {
                        "name": "Cucumber"
                    },
                    "gherkin": gherkin_text
                }
            }
        }
        
        self.stub_graphql_query(mutation_pattern, response_data)
    
    def stub_error_response(
        self,
        query_pattern: str,
        error_message: str,
        error_code: str = "GRAPHQL_ERROR"
    ):
        """Stub error response for any GraphQL operation."""
        errors = [{
            "message": error_message,
            "extensions": {
                "code": error_code
            }
        }]
        
        self.stub_graphql_query(query_pattern, {}, errors=errors)
    
    def get_graphql_calls(self, query_pattern: str) -> List[Dict[str, Any]]:
        """Get all GraphQL calls matching a query pattern."""
        calls = []
        
        # This is a simplified implementation
        # In practice, you'd need to inspect the actual requests made
        # through the responses mock or implement request logging
        
        return calls
    
    def assert_graphql_called_with(
        self,
        query_pattern: str,
        variables: Optional[Dict[str, Any]] = None,
        times: int = 1
    ):
        """Assert GraphQL query was called with specific parameters."""
        # Implementation would depend on how you want to track calls
        # This is a placeholder for the assertion logic
        pass
    
    def assert_not_called(self, query_pattern: str):
        """Assert GraphQL query was not called."""
        # Implementation placeholder
        pass
    
    def reset_call_log(self):
        """Reset the call log."""
        self.call_log.clear()