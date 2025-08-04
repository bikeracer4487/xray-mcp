#!/usr/bin/env python3
"""Comprehensive tests for Xray MCP server.

This test suite validates the key functionality identified in the QA report
to ensure ≥95% pass rate. It covers:
- GraphQL schema compliance
- ID resolution functionality
- Array parameter validation
- Manual test creation with steps
- Error handling and edge cases
"""

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client.graphql import XrayGraphQLClient
from auth.manager import XrayAuthManager
from tools.tests import TestTools
from tools.executions import TestExecutionTools
from tools.testsets import TestSetTools
from tools.plans import TestPlanTools
from utils.id_resolver import IssueIdResolver
from exceptions import GraphQLError, ValidationError


class MockAuthManager:
    """Mock authentication manager for testing."""

    async def get_valid_token(self):
        return "mock_token"

    async def refresh_token(self):
        return "refreshed_token"


class ComprehensiveTests:
    """Comprehensive test suite for Xray MCP server."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.test_results = []

    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        self.test_results.append(
            {"test": test_name, "passed": passed, "details": details}
        )
        if passed:
            self.passed += 1
            print(f"✅ {test_name}")
        else:
            self.failed += 1
            print(f"❌ {test_name}: {details}")

    async def test_id_resolution(self):
        """Test ID resolution functionality."""
        mock_client = AsyncMock()
        resolver = IssueIdResolver(mock_client)

        # Test numeric ID (should pass through)
        try:
            result = await resolver.resolve_issue_id("12345")
            assert result == "12345"
            self.log_test("ID Resolution - Numeric ID", True)
        except Exception as e:
            self.log_test("ID Resolution - Numeric ID", False, str(e))

        # Test Jira key resolution (mock successful lookup)
        mock_client.execute_query.return_value = {
            "data": {
                "getTests": {
                    "results": [{"issueId": "98765", "jira": {"key": "TEST-123"}}]
                }
            }
        }

        try:
            result = await resolver.resolve_issue_id("TEST-123")
            assert result == "98765"
            self.log_test("ID Resolution - Jira Key Success", True)
        except Exception as e:
            self.log_test("ID Resolution - Jira Key Success", False, str(e))

        # Test failed Jira key resolution
        mock_client.execute_query.return_value = {"data": {"getTests": {"results": []}}}

        try:
            await resolver.resolve_issue_id("NOTFOUND-999")
            self.log_test(
                "ID Resolution - Failed Key", False, "Should have raised GraphQLError"
            )
        except GraphQLError:
            self.log_test("ID Resolution - Failed Key", True)
        except Exception as e:
            self.log_test("ID Resolution - Failed Key", False, f"Wrong exception: {e}")

    async def test_manual_test_creation(self):
        """Test manual test creation with proper steps structure."""
        mock_client = AsyncMock()
        test_tools = TestTools(mock_client)

        # Mock successful creation response
        mock_client.execute_mutation.return_value = {
            "data": {
                "createTest": {
                    "test": {
                        "issueId": "12345",
                        "testType": {"name": "Manual"},
                        "steps": [
                            {
                                "action": "Login",
                                "data": "user/pass",
                                "result": "Dashboard shown",
                            }
                        ],
                        "jira": {"key": "TEST-123", "summary": "Login Test"},
                    },
                    "warnings": [],
                }
            }
        }

        try:
            steps = [
                {
                    "action": "Login to system",
                    "data": "username/password",
                    "result": "User logged in",
                },
                {
                    "action": "Navigate to dashboard",
                    "data": "",
                    "result": "Dashboard displayed",
                },
            ]

            result = await test_tools.create_test(
                project_key="TEST",
                summary="Manual Login Test",
                test_type="Manual",
                steps=steps,
            )

            assert "test" in result
            assert result["test"]["testType"]["name"] == "Manual"
            self.log_test("Manual Test Creation - Success", True)
        except Exception as e:
            self.log_test("Manual Test Creation - Success", False, str(e))

    async def test_array_parameter_validation(self):
        """Test array parameter validation for test environments."""
        mock_client = AsyncMock()
        execution_tools = TestExecutionTools(mock_client)

        # Mock successful execution creation with test environments
        mock_client.execute_mutation.return_value = {
            "data": {
                "createTestExecution": {
                    "testExecution": {
                        "issueId": "54321",
                        "jira": {"key": "EXEC-100", "summary": "Test Execution"},
                    },
                    "warnings": [],
                    "createdTestEnvironments": ["Chrome", "Firefox"],
                }
            }
        }

        try:
            result = await execution_tools.create_test_execution(
                project_key="TEST",
                summary="Browser Testing Execution",
                test_environments=["Chrome", "Firefox", "Safari"],
            )

            assert "testExecution" in result
            self.log_test("Array Parameter Validation - Test Environments", True)
        except Exception as e:
            self.log_test(
                "Array Parameter Validation - Test Environments", False, str(e)
            )

    async def test_graphql_schema_compliance(self):
        """Test GraphQL schema compliance for key operations."""
        mock_client = AsyncMock()

        # Test execution creation schema
        execution_tools = TestExecutionTools(mock_client)
        mock_client.execute_mutation.return_value = {
            "data": {
                "createTestExecution": {
                    "testExecution": {"issueId": "123", "jira": {"key": "EXEC-1"}},
                    "warnings": [],
                }
            }
        }

        try:
            await execution_tools.create_test_execution("TEST", "Test Execution")
            # Check that the mutation was called with correct schema
            call_args = mock_client.execute_mutation.call_args
            mutation = call_args[0][0]
            assert "createTestExecution" in mutation
            assert "testEnvironments" in mutation
            assert "testIssueIds" in mutation
            self.log_test("GraphQL Schema - Test Execution Creation", True)
        except Exception as e:
            self.log_test("GraphQL Schema - Test Execution Creation", False, str(e))

        # Test set creation schema
        testset_tools = TestSetTools(mock_client)
        mock_client.execute_query.return_value = {
            "data": {
                "createTestSet": {
                    "testSet": {"issueId": "456", "jira": {"key": "SET-1"}},
                    "warnings": [],
                }
            }
        }

        try:
            await testset_tools.create_test_set("TEST", "Test Set")
            call_args = mock_client.execute_query.call_args
            mutation = call_args[0][0]
            assert "createTestSet" in mutation
            assert "testIssueIds" in mutation
            self.log_test("GraphQL Schema - Test Set Creation", True)
        except Exception as e:
            self.log_test("GraphQL Schema - Test Set Creation", False, str(e))

    async def test_error_handling(self):
        """Test error handling scenarios."""
        mock_client = AsyncMock()
        test_tools = TestTools(mock_client)

        # Test GraphQL error handling
        mock_client.execute_query.side_effect = Exception("GraphQL error")

        try:
            await test_tools.get_test("INVALID-123")
            self.log_test(
                "Error Handling - GraphQL Exception",
                False,
                "Should have raised exception",
            )
        except Exception:
            self.log_test("Error Handling - GraphQL Exception", True)

        # Test validation error handling
        try:
            await test_tools.get_tests(limit=150)  # Exceeds limit
            self.log_test(
                "Error Handling - Validation Error",
                False,
                "Should have raised ValidationError",
            )
        except ValidationError:
            self.log_test("Error Handling - Validation Error", True)
        except Exception as e:
            self.log_test(
                "Error Handling - Validation Error", False, f"Wrong exception: {e}"
            )

    async def test_tool_integration(self):
        """Test integration between different tools."""
        mock_client = AsyncMock()
        execution_tools = TestExecutionTools(mock_client)

        # Mock ID resolver
        mock_client.execute_query.return_value = {
            "data": {
                "getTests": {
                    "results": [{"issueId": "11111", "jira": {"key": "TEST-100"}}]
                }
            }
        }

        # Mock add tests mutation
        mock_client.execute_mutation.return_value = {
            "data": {
                "addTestsToTestExecution": {"addedTests": ["11111"], "warning": ""}
            }
        }

        try:
            # Test adding tests with Jira key resolution
            result = await execution_tools.add_tests_to_execution(
                "EXEC-200", ["TEST-100", "TEST-101"]
            )

            # Verify ID resolver was used
            assert mock_client.execute_query.called
            assert mock_client.execute_mutation.called
            self.log_test("Tool Integration - ID Resolution in Execution", True)
        except Exception as e:
            self.log_test(
                "Tool Integration - ID Resolution in Execution", False, str(e)
            )

    async def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        mock_client = AsyncMock()

        # Test empty arrays
        execution_tools = TestExecutionTools(mock_client)
        mock_client.execute_mutation.return_value = {
            "data": {
                "createTestExecution": {
                    "testExecution": {"issueId": "999", "jira": {"key": "EXEC-999"}},
                    "warnings": [],
                }
            }
        }

        try:
            result = await execution_tools.create_test_execution(
                "TEST", "Empty Execution", test_issue_ids=[], test_environments=[]
            )
            assert "testExecution" in result
            self.log_test("Edge Cases - Empty Arrays", True)
        except Exception as e:
            self.log_test("Edge Cases - Empty Arrays", False, str(e))

        # Test None values
        try:
            result = await execution_tools.create_test_execution(
                "TEST", "Null Values Test", test_issue_ids=None, test_environments=None
            )
            assert "testExecution" in result
            self.log_test("Edge Cases - None Values", True)
        except Exception as e:
            self.log_test("Edge Cases - None Values", False, str(e))

    async def run_all_tests(self):
        """Run all comprehensive tests."""
        print("🚀 Starting Comprehensive Xray MCP Server Tests\n")

        test_methods = [
            self.test_id_resolution,
            self.test_manual_test_creation,
            self.test_array_parameter_validation,
            self.test_graphql_schema_compliance,
            self.test_error_handling,
            self.test_tool_integration,
            self.test_edge_cases,
        ]

        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                self.log_test(f"FATAL - {test_method.__name__}", False, str(e))

        # Calculate pass rate
        total_tests = self.passed + self.failed
        pass_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0

        print(f"\n📊 Test Results Summary:")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Pass Rate: {pass_rate:.1f}%")

        if pass_rate >= 95:
            print("🎉 SUCCESS: Achieved ≥95% pass rate!")
        else:
            print("⚠️  ATTENTION: Pass rate below 95% target")
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['details']}")

        return pass_rate >= 95


async def main():
    """Run comprehensive tests."""
    test_suite = ComprehensiveTests()
    success = await test_suite.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
