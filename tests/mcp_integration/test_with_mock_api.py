"""
Tests for MCP server functionality with mocked Xray API.

These tests mock the Xray API responses to provide deterministic testing
without requiring real Xray credentials or hitting the live API.
"""

import pytest
import json
from typing import Dict, Any
from unittest.mock import patch, AsyncMock
from fastmcp import Client
from mcp import types
from tests.mcp_protocol import BaseMCPTest


@pytest.mark.mcp_integration
@pytest.mark.mcp_client
class TestMCPWithMockAPI(BaseMCPTest):
    """Test MCP server with mocked Xray API responses."""

    @pytest.fixture
    def comprehensive_mock_responses(self):
        """Comprehensive mock responses for various Xray operations."""
        return {
            'auth_success': {
                'access_token': 'mock_bearer_token_12345',
                'token_type': 'Bearer',
                'expires_in': 3600
            },
            'test_list_response': {
                'data': {
                    'getTests': {
                        'results': [
                            {
                                'issueId': '10001',
                                'jira': {
                                    'key': 'FTEST-100',
                                    'summary': 'User Login Test',
                                    'description': 'Test user authentication functionality'
                                },
                                'testType': {'name': 'Manual'},
                                'steps': [
                                    {
                                        'action': 'Navigate to login page',
                                        'data': 'Open https://app.example.com/login',
                                        'result': 'Login page displays correctly'
                                    },
                                    {
                                        'action': 'Enter credentials',
                                        'data': 'Username: test@example.com, Password: Test123!',
                                        'result': 'User is logged in successfully'
                                    }
                                ]
                            },
                            {
                                'issueId': '10002',
                                'jira': {
                                    'key': 'FTEST-101',
                                    'summary': 'API Endpoint Test',
                                    'description': 'Test REST API functionality'
                                },
                                'testType': {'name': 'Cucumber'},
                                'gherkin': '''Feature: API Testing
  Scenario: Get user data
    Given the API is available
    When I request user data
    Then I should receive valid JSON response'''
                            }
                        ]
                    }
                }
            },
            'test_create_response': {
                'data': {
                    'createTest': {
                        'test': {
                            'issueId': '10003',
                            'jira': {
                                'key': 'FTEST-102',
                                'summary': 'New Test Case',
                                'description': 'Newly created test case'
                            },
                            'testType': {'name': 'Manual'},
                            'steps': []
                        }
                    }
                }
            },
            'execution_list_response': {
                'data': {
                    'getTestExecutions': {
                        'results': [
                            {
                                'issueId': '20001',
                                'jira': {
                                    'key': 'EXEC-500',
                                    'summary': 'Sprint 1 Testing',
                                    'description': 'Test execution for sprint 1'
                                },
                                'testEnvironments': ['staging', 'production']
                            }
                        ]
                    }
                }
            },
            'execution_create_response': {
                'data': {
                    'createTestExecution': {
                        'testExecution': {
                            'issueId': '20002',
                            'jira': {
                                'key': 'EXEC-501',
                                'summary': 'New Test Execution',
                                'description': 'Newly created test execution'
                            },
                            'testEnvironments': []
                        }
                    }
                }
            },
            'plan_list_response': {
                'data': {
                    'getTestPlans': {
                        'results': [
                            {
                                'issueId': '30001',
                                'jira': {
                                    'key': 'PLAN-100',
                                    'summary': 'Release Testing Plan',
                                    'description': 'Comprehensive testing plan for release'
                                }
                            }
                        ]
                    }
                }
            },
            'plan_create_response': {
                'data': {
                    'createTestPlan': {
                        'testPlan': {
                            'issueId': '30002',
                            'jira': {
                                'key': 'PLAN-101',
                                'summary': 'New Test Plan',
                                'description': 'Newly created test plan'
                            }
                        }
                    }
                }
            },
            'run_get_response': {
                'data': {
                    'getTestRun': {
                        'testRun': {
                            'id': '40001',
                            'status': {'name': 'PASS'},
                            'test': {
                                'issueId': '10001',
                                'jira': {'key': 'FTEST-100'}
                            },
                            'testExecution': {
                                'issueId': '20001',
                                'jira': {'key': 'EXEC-500'}
                            }
                        }
                    }
                }
            },
            'error_response_unauthorized': {
                'errors': [
                    {
                        'message': 'Unauthorized access',
                        'extensions': {
                            'code': 'UNAUTHORIZED'
                        }
                    }
                ]
            },
            'error_response_not_found': {
                'errors': [
                    {
                        'message': 'Entity not found',
                        'extensions': {
                            'code': 'NOT_FOUND'
                        }
                    }
                ]
            }
        }

    @pytest.mark.asyncio
    async def test_test_operations_with_mock_api(self, mcp_client: Client, comprehensive_mock_responses):
        """Test all test entity operations with mocked API."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock) as mock_auth:
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                mock_auth.return_value = None

                # Test list operation
                mock_execute.return_value = comprehensive_mock_responses['test_list_response']
                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='list',
                    project_key='FTEST',
                    limit=10
                )

                await self.assert_mcp_tool_result(result)

                # Verify response contains expected data
                content_text = result.content[0].text
                data = json.loads(content_text)
                assert 'results' in data
                assert len(data['results']) == 2
                assert data['results'][0]['jira']['key'] == 'FTEST-100'

                # Test create operation
                mock_execute.return_value = comprehensive_mock_responses['test_create_response']
                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='create',
                    project_key='FTEST',
                    summary='New Test Case',
                    test_type='Manual',
                    description='Test description'
                )

                await self.assert_mcp_tool_result(result)
                content_text = result.content[0].text
                data = json.loads(content_text)
                assert 'test' in data
                assert data['test']['jira']['key'] == 'FTEST-102'

    @pytest.mark.asyncio
    async def test_execution_operations_with_mock_api(self, mcp_client: Client, comprehensive_mock_responses):
        """Test test execution operations with mocked API."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock) as mock_auth:
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                mock_auth.return_value = None

                # Test list executions
                mock_execute.return_value = comprehensive_mock_responses['execution_list_response']
                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test_execution',
                    action='list',
                    project_key='FTEST'
                )

                await self.assert_mcp_tool_result(result)
                content_text = result.content[0].text
                data = json.loads(content_text)
                assert 'results' in data
                assert data['results'][0]['jira']['key'] == 'EXEC-500'

                # Test create execution
                mock_execute.return_value = comprehensive_mock_responses['execution_create_response']
                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test_execution',
                    action='create',
                    project_key='FTEST',
                    summary='New Test Execution',
                    test_issue_ids=['FTEST-100', 'FTEST-101']
                )

                await self.assert_mcp_tool_result(result)
                content_text = result.content[0].text
                data = json.loads(content_text)
                assert 'testExecution' in data
                assert data['testExecution']['jira']['key'] == 'EXEC-501'

    @pytest.mark.asyncio
    async def test_plan_operations_with_mock_api(self, mcp_client: Client, comprehensive_mock_responses):
        """Test test plan operations with mocked API."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock) as mock_auth:
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                mock_auth.return_value = None

                # Test list plans
                mock_execute.return_value = comprehensive_mock_responses['plan_list_response']
                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test_plan',
                    action='list',
                    project_key='FTEST'
                )

                await self.assert_mcp_tool_result(result)
                content_text = result.content[0].text
                data = json.loads(content_text)
                assert 'results' in data
                assert data['results'][0]['jira']['key'] == 'PLAN-100'

                # Test create plan
                mock_execute.return_value = comprehensive_mock_responses['plan_create_response']
                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test_plan',
                    action='create',
                    project_key='FTEST',
                    summary='New Test Plan',
                    test_issue_ids=['FTEST-100', 'FTEST-101']
                )

                await self.assert_mcp_tool_result(result)
                content_text = result.content[0].text
                data = json.loads(content_text)
                assert 'testPlan' in data
                assert data['testPlan']['jira']['key'] == 'PLAN-101'

    @pytest.mark.asyncio
    async def test_run_operations_with_mock_api(self, mcp_client: Client, comprehensive_mock_responses):
        """Test test run operations with mocked API."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock) as mock_auth:
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                mock_auth.return_value = None

                # Test get run
                mock_execute.return_value = comprehensive_mock_responses['run_get_response']
                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test_run',
                    action='get',
                    id='40001'
                )

                await self.assert_mcp_tool_result(result)
                content_text = result.content[0].text
                data = json.loads(content_text)
                assert 'testRun' in data
                assert data['testRun']['status']['name'] == 'PASS'

    @pytest.mark.asyncio
    async def test_manual_test_with_steps(self, mcp_client: Client, comprehensive_mock_responses):
        """Test creating manual test with steps using mocked API."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock) as mock_auth:
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                mock_auth.return_value = None

                # Mock response for creating test with steps
                create_response = comprehensive_mock_responses['test_create_response'].copy()
                create_response['data']['createTest']['test']['steps'] = [
                    {
                        'action': 'Navigate to page',
                        'data': 'Open https://example.com',
                        'result': 'Page loads successfully'
                    }
                ]
                mock_execute.return_value = create_response

                steps_json = '[{"action": "Navigate to page", "data": "Open https://example.com", "result": "Page loads successfully"}]'

                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='create',
                    project_key='FTEST',
                    summary='Manual Test with Steps',
                    test_type='Manual',
                    steps=steps_json
                )

                await self.assert_mcp_tool_result(result)
                content_text = result.content[0].text
                data = json.loads(content_text)
                assert 'test' in data
                assert 'steps' in data['test']
                assert len(data['test']['steps']) == 1

    @pytest.mark.asyncio
    async def test_cucumber_test_with_gherkin(self, mcp_client: Client, comprehensive_mock_responses):
        """Test creating Cucumber test with Gherkin using mocked API."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock) as mock_auth:
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                mock_auth.return_value = None

                # Mock response for creating Cucumber test
                create_response = comprehensive_mock_responses['test_create_response'].copy()
                create_response['data']['createTest']['test']['testType'] = {'name': 'Cucumber'}
                create_response['data']['createTest']['test']['gherkin'] = 'Feature: Test\nScenario: Test scenario'
                mock_execute.return_value = create_response

                gherkin_script = '''Feature: User Authentication
  Scenario: Successful login
    Given I am on the login page
    When I enter valid credentials
    Then I should be logged in'''

                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='create',
                    project_key='FTEST',
                    summary='Cucumber Test',
                    test_type='Cucumber',
                    gherkin=gherkin_script
                )

                await self.assert_mcp_tool_result(result)
                content_text = result.content[0].text
                data = json.loads(content_text)
                assert 'test' in data
                assert data['test']['testType']['name'] == 'Cucumber'

    @pytest.mark.asyncio
    async def test_error_handling_with_mock_api(self, mcp_client: Client, comprehensive_mock_responses):
        """Test error handling with mocked API errors."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock) as mock_auth:
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                mock_auth.return_value = None

                # Test unauthorized error
                mock_execute.return_value = comprehensive_mock_responses['error_response_unauthorized']

                with pytest.raises(Exception) as exc_info:
                    await self.call_xray_tool(
                        mcp_client,
                        entity='test',
                        action='list',
                        project_key='UNAUTHORIZED_PROJECT'
                    )

                assert 'unauthorized' in str(exc_info.value).lower() or 'operation failed' in str(exc_info.value).lower()

                # Test not found error
                mock_execute.return_value = comprehensive_mock_responses['error_response_not_found']

                with pytest.raises(Exception) as exc_info:
                    await self.call_xray_tool(
                        mcp_client,
                        entity='test',
                        action='get',
                        issue_id='NONEXISTENT-999'
                    )

                assert 'not found' in str(exc_info.value).lower() or 'operation failed' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_search_operations_with_mock_api(self, mcp_client: Client, comprehensive_mock_responses):
        """Test search operations with mocked API."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock) as mock_auth:
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                mock_auth.return_value = None

                # Mock search results
                search_response = {
                    'data': {
                        'getTests': {
                            'results': [
                                {
                                    'issueId': '10001',
                                    'jira': {
                                        'key': 'FTEST-100',
                                        'summary': 'Login Test - User Authentication',
                                        'description': 'Test login functionality for users'
                                    },
                                    'testType': {'name': 'Manual'}
                                }
                            ]
                        }
                    }
                }
                mock_execute.return_value = search_response

                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='search',
                    text='login',
                    project_key='FTEST'
                )

                await self.assert_mcp_tool_result(result)
                content_text = result.content[0].text
                data = json.loads(content_text)
                assert 'results' in data
                assert 'login' in data['results'][0]['jira']['summary'].lower()

    @pytest.mark.asyncio
    async def test_array_parameter_handling(self, mcp_client: Client, comprehensive_mock_responses):
        """Test proper handling of array parameters with mocked API."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock) as mock_auth:
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                mock_auth.return_value = None
                mock_execute.return_value = comprehensive_mock_responses['execution_create_response']

                # Test with multiple test IDs and environments
                result = await self.call_xray_tool(
                    mcp_client,
                    entity='test_execution',
                    action='create',
                    project_key='FTEST',
                    summary='Multi-Test Execution',
                    test_issue_ids=['FTEST-100', 'FTEST-101', 'FTEST-102'],
                    test_environments=['dev', 'staging', 'production']
                )

                await self.assert_mcp_tool_result(result)

                # Verify the mock was called with the right parameters
                mock_execute.assert_called_once()
                call_args = mock_execute.call_args[0][0]  # Get the GraphQL query/variables

                # The exact structure depends on implementation, but verify arrays were passed
                assert 'FTEST-100' in str(call_args) or 'FTEST-100' in str(mock_execute.call_args)
                assert 'staging' in str(call_args) or 'staging' in str(mock_execute.call_args)

    @pytest.mark.asyncio
    async def test_complex_workflow_with_mock_api(self, mcp_client: Client, comprehensive_mock_responses):
        """Test complex workflow scenarios with mocked API."""
        with patch('src.auth.XrayAuth.authenticate', new_callable=AsyncMock) as mock_auth:
            with patch('src.graphql_client.XrayGraphQLClient.execute', new_callable=AsyncMock) as mock_execute:
                mock_auth.return_value = None

                # Step 1: Create a test
                mock_execute.return_value = comprehensive_mock_responses['test_create_response']
                test_result = await self.call_xray_tool(
                    mcp_client,
                    entity='test',
                    action='create',
                    project_key='FTEST',
                    summary='Workflow Test Case',
                    test_type='Manual'
                )
                await self.assert_mcp_tool_result(test_result)

                # Step 2: Create an execution with the test
                mock_execute.return_value = comprehensive_mock_responses['execution_create_response']
                execution_result = await self.call_xray_tool(
                    mcp_client,
                    entity='test_execution',
                    action='create',
                    project_key='FTEST',
                    summary='Workflow Execution',
                    test_issue_ids=['FTEST-102']  # Using the created test
                )
                await self.assert_mcp_tool_result(execution_result)

                # Step 3: Create a plan
                mock_execute.return_value = comprehensive_mock_responses['plan_create_response']
                plan_result = await self.call_xray_tool(
                    mcp_client,
                    entity='test_plan',
                    action='create',
                    project_key='FTEST',
                    summary='Workflow Test Plan',
                    test_issue_ids=['FTEST-102']
                )
                await self.assert_mcp_tool_result(plan_result)

                # All operations should have succeeded
                assert all(result.content for result in [test_result, execution_result, plan_result])