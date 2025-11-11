"""
Comprehensive test suite to reproduce all issues identified in the QA testing report.

This test file is designed to validate that the critical issues reported by QA are properly
addressed. Each test should initially FAIL to demonstrate the issue exists, then PASS after
the corresponding fix is implemented.

QA Report Issues Covered:
1. Response Format Error - "structured_content must be a dict or None. Got list"
2. Data Persistence/Retrieval - Entities created but cannot be retrieved
3. Parameter Validation - Array parameters fail validation
4. Configuration Issues - 'Server' object has no attribute 'lifespan_context'
5. Health Check Failure - Service showing as unhealthy

Test Environment: FTEST JIRA Project (matching QA report)
"""

import pytest
import os
import asyncio
import json
from typing import Dict, Any
from src.server import create_server
from tests.integration.test_helpers import parse_mcp_response


@pytest.mark.skipif(
    not all([os.getenv('XRAY_CLIENT_ID'), os.getenv('XRAY_CLIENT_SECRET')]),
    reason="Xray credentials not available"
)
class TestQAReportIssues:
    """Tests that reproduce specific issues from the QA testing report."""

    @pytest.fixture
    def server(self):
        """Create MCP server instance for testing."""
        return create_server()

    @pytest.fixture
    def tool(self, server):
        """Get the xray_test tool from the server."""
        # FastMCP server tool access
        return server._tool_manager._tools['xray_test']

    @pytest.fixture
    def project_key(self):
        """Get project key matching QA report environment."""
        return 'FTEST'  # Same project used in QA report

    @pytest.fixture
    def unique_prefix(self):
        """Generate unique prefix for test resources."""
        import uuid
        return f"QA-{str(uuid.uuid4())[:8]}"

    @pytest.mark.asyncio
    async def test_issue_response_format_error(self, tool, unique_prefix, project_key):
        """
        QA ISSUE: Response Format Error

        Error: "structured_content must be a dict or None. Got list"

        According to QA report, this affects 100% of successful operations.
        The server returns MCP format [{'type': 'text', 'text': '...'}]
        but clients expect a dict.
        """
        print(f"\n🔴 Testing QA Issue: Response Format Error - {unique_prefix}")
        created_resources = []

        try:
            # Create a test entity - this should succeed but have format issues
            test_params = {
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} QA Response Format Test',
                'test_type': 'Manual',
                'description': 'Testing response format issue from QA report'
            }

            # Execute the operation
            result = await tool.run(test_params)

            # Debug the response format
            print(f"Response type: {type(result)}")
            print(f"Response content: {result}")

            # Test if response format causes parsing issues
            try:
                if isinstance(result, list):
                    # This is the problematic format mentioned in QA report
                    for item in result:
                        # Handle both dict and TextContent objects
                        if hasattr(item, 'type') and item.type == 'text':
                            # TextContent object from FastMCP
                            content = json.loads(item.text)
                            print("✅ Successfully parsed TextContent format (format issue fixed)")
                            if 'issueId' in content:
                                created_resources.append(('test', content['issueId']))
                        elif isinstance(item, dict) and item.get('type') == 'text':
                            # Dict format
                            content = json.loads(item['text'])
                            print("✅ Successfully parsed dict format")
                            if 'issueId' in content:
                                created_resources.append(('test', content['issueId']))
                        else:
                            pytest.fail("Response contains unexpected content format")
                elif isinstance(result, dict):
                    print("✅ Response is dict format (format issue resolved)")
                    if result.get('issueId'):
                        created_resources.append(('test', result['issueId']))
                else:
                    pytest.fail(f"Unexpected response format: {type(result)}")

            except Exception as format_error:
                if "structured_content must be a dict" in str(format_error):
                    print(f"🔴 CONFIRMED: QA response format issue reproduced - {str(format_error)}")
                    pytest.fail(f"QA Issue reproduced: {str(format_error)}")
                else:
                    pytest.fail(f"Different format error: {str(format_error)}")

        finally:
            # Cleanup created resources
            await self._cleanup_resources(tool, created_resources)

    @pytest.mark.asyncio
    async def test_issue_data_retrieval_failure(self, tool, unique_prefix, project_key):
        """
        QA ISSUE: Data Persistence/Retrieval

        Issue: Entities appear to be created successfully but cannot be retrieved
        Examples from QA report: FTEST-1456, FTEST-1457, FTEST-1459

        This test reproduces the exact scenario from the QA report.
        """
        print(f"\n🔴 Testing QA Issue: Data Retrieval Failure - {unique_prefix}")
        created_resources = []

        try:
            # Step 1: Create a test (this should succeed according to QA report)
            test_params = {
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} QA Data Retrieval Test',
                'test_type': 'Manual',
                'description': 'Reproducing data retrieval issue from QA report'
            }

            create_result = await tool.run(test_params)
            create_data = parse_mcp_response(create_result) if isinstance(create_result, list) else create_result

            # Verify creation appears successful
            assert create_data.get('success'), f"Test creation failed: {create_data.get('errors')}"

            test_id = create_data['data']['issueId']
            test_key = create_data['data']['issueKey']
            created_resources.append(('test', test_id))

            print(f"✅ Created test: {test_key} (ID: {test_id})")

            # Step 2: Try to retrieve the created test (this should fail per QA report)
            get_params = {
                'entity': 'test',
                'action': 'get',
                'issue_id': test_id
            }

            get_result = await tool.run(get_params)
            get_data = parse_mcp_response(get_result) if isinstance(get_result, list) else get_result

            if get_data.get('success'):
                print("✅ Test retrieved successfully (retrieval issue resolved)")
                # Verify we got the same test back
                retrieved_id = get_data['data']['issueId']
                assert retrieved_id == test_id, f"Retrieved wrong test: {retrieved_id} != {test_id}"
            else:
                error_msg = get_data.get('errors', ['Unknown error'])[0]
                print(f"🔴 CONFIRMED: QA data retrieval issue reproduced - {error_msg}")
                pytest.fail(f"QA Issue reproduced: Cannot retrieve created entity - {error_msg}")

        finally:
            await self._cleanup_resources(tool, created_resources)

    @pytest.mark.asyncio
    async def test_issue_parameter_validation_arrays(self, tool, unique_prefix, project_key):
        """
        QA ISSUE: Parameter Validation Issues

        Issue: Array parameters fail validation inconsistently
        Example: test_environments array parameter rejection

        From QA report: "Array parameters fail validation inconsistently"
        """
        print(f"\n🔴 Testing QA Issue: Array Parameter Validation - {unique_prefix}")
        created_resources = []

        try:
            # First create a test to use in execution
            test_params = {
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Array Validation Test',
                'test_type': 'Manual'
            }

            test_result = await tool.run(test_params)
            test_data = parse_mcp_response(test_result) if isinstance(test_result, list) else test_result
            assert test_data.get('success'), "Test creation failed"

            test_id = test_data['data']['issueId']
            created_resources.append(('test', test_id))

            # Test execution creation with test_environments array (this should fail per QA report)
            exec_params = {
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Array Parameter Test',
                'test_issue_ids': [test_id],
                'test_environments': ['staging', 'qa', 'production']  # Array parameter
            }

            exec_result = await tool.run(exec_params)
            exec_data = parse_mcp_response(exec_result) if isinstance(exec_result, list) else exec_result

            if exec_data.get('success'):
                print("✅ Array parameter validation working (issue resolved)")
                created_resources.append(('test_execution', exec_data['data']['issueId']))
            else:
                error_msg = exec_data.get('errors', ['Unknown error'])[0]
                if 'validation' in error_msg.lower() or 'parameter' in error_msg.lower():
                    print(f"🔴 CONFIRMED: QA array validation issue reproduced - {error_msg}")
                    pytest.fail(f"QA Issue reproduced: Array parameter validation failed - {error_msg}")
                else:
                    pytest.fail(f"Different error (not validation): {error_msg}")

        finally:
            await self._cleanup_resources(tool, created_resources)

    @pytest.mark.asyncio
    async def test_issue_configuration_lifespan_context(self, tool, unique_prefix, project_key):
        """
        QA ISSUE: Configuration Issues

        Error: 'Server' object has no attribute 'lifespan_context'
        Status: Jira service status: unhealthy, Configuration status: invalid

        This test checks for configuration and server setup issues.
        """
        print(f"\n🔴 Testing QA Issue: Configuration/Lifespan Context - {unique_prefix}")

        try:
            # Test 1: Check if server has lifespan_context attribute
            server = create_server()

            if hasattr(server, 'lifespan_context'):
                print("✅ Server has lifespan_context attribute (issue resolved)")
            else:
                # This may not be an issue if FastMCP handles it differently
                print("⚠️ Server missing lifespan_context - checking if this causes problems")

            # Test 2: Try basic operation to see if configuration is valid
            test_params = {
                'entity': 'test',
                'action': 'list',
                'project_key': project_key,
                'limit': 1
            }

            result = await tool.run(test_params)
            data = parse_mcp_response(result) if isinstance(result, list) else result

            if data.get('success'):
                print("✅ Basic operations work despite configuration warnings")
            else:
                error_msg = data.get('errors', ['Unknown error'])[0]
                if 'configuration' in error_msg.lower() or 'lifespan' in error_msg.lower():
                    print(f"🔴 CONFIRMED: QA configuration issue reproduced - {error_msg}")
                    pytest.fail(f"QA Issue reproduced: Configuration error - {error_msg}")
                else:
                    print(f"Different error: {error_msg}")

        except AttributeError as e:
            if 'lifespan_context' in str(e):
                print(f"🔴 CONFIRMED: QA lifespan_context issue reproduced - {str(e)}")
                pytest.fail(f"QA Issue reproduced: {str(e)}")
            else:
                raise

    @pytest.mark.asyncio
    async def test_issue_health_check_failure(self, tool, unique_prefix, project_key):
        """
        QA ISSUE: Health Check Failure

        Issue: Connection Health Check Status: FAILED
        Details: Jira service status: unhealthy, Configuration status: invalid

        This test checks if there's a health check endpoint and if it works.
        """
        print(f"\n🔴 Testing QA Issue: Health Check Failure - {unique_prefix}")

        try:
            # Check if server has health check endpoint/functionality
            server = create_server()

            # Look for health check in server resources or tools
            resources = getattr(server, '_resource_manager', None)
            if resources:
                resource_names = [r.name for r in resources._resources.values()]
                print(f"Available resources: {resource_names}")

                if any('health' in name.lower() for name in resource_names):
                    print("✅ Health check resource found")
                else:
                    print("⚠️ No health check resource found")

            # Test authentication health by doing a simple operation
            test_params = {
                'entity': 'test',
                'action': 'list',
                'project_key': project_key,
                'limit': 1
            }

            result = await tool.run(test_params)
            data = parse_mcp_response(result) if isinstance(result, list) else result

            if data.get('success'):
                print("✅ Authentication and basic connectivity healthy")
            else:
                error_msg = data.get('errors', ['Unknown error'])[0]
                if any(keyword in error_msg.lower() for keyword in ['auth', 'unauthorized', 'forbidden', 'connection']):
                    print(f"🔴 CONFIRMED: QA health check issue reproduced - {error_msg}")
                    pytest.fail(f"QA Issue reproduced: Service unhealthy - {error_msg}")
                else:
                    print(f"Different error: {error_msg}")

        except Exception as e:
            if any(keyword in str(e).lower() for keyword in ['connection', 'auth', 'health']):
                print(f"🔴 CONFIRMED: QA health check issue reproduced - {str(e)}")
                pytest.fail(f"QA Issue reproduced: Health check failed - {str(e)}")
            else:
                raise

    async def _cleanup_resources(self, tool, resources):
        """Helper to clean up created test resources."""
        for resource_type, resource_id in reversed(resources):
            try:
                await tool.run({
                    'entity': resource_type,
                    'action': 'delete',
                    'issue_id': resource_id
                })
                print(f"   🧹 Cleaned up {resource_type}: {resource_id}")
            except Exception as e:
                print(f"   ⚠️ Cleanup failed for {resource_type} {resource_id}: {str(e)}")
                # Continue cleanup even if one fails
                pass

    @pytest.mark.asyncio
    async def test_comprehensive_qa_scenario(self, tool, unique_prefix, project_key):
        """
        QA COMPREHENSIVE TEST: Reproduce the exact workflow from QA report

        This test reproduces the sequence described in the QA report:
        1. Create test entities (should succeed)
        2. Try to retrieve them (should fail)
        3. Create execution with environments (should have validation issues)
        4. Overall experience matches QA report
        """
        print(f"\n🎯 Testing QA Comprehensive Scenario - {unique_prefix}")
        created_resources = []

        try:
            # Step 1: Create Manual Test (FTEST-1456 equivalent)
            manual_test = {
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Manual Test Case - Login Functionality',
                'test_type': 'Manual',
                'description': 'Comprehensive test reproducing QA workflow',
                'steps': '[{"action": "Navigate to login page", "data": "URL: /login", "result": "Login page displayed"}, {"action": "Enter credentials", "data": "user@test.com / password", "result": "Credentials accepted"}, {"action": "Click login", "data": "Submit button", "result": "User logged in successfully"}]'
            }

            manual_result = await tool.run(manual_test)
            manual_data = parse_mcp_response(manual_result) if isinstance(manual_result, list) else manual_result

            if manual_data.get('success'):
                manual_id = manual_data['data']['issueId']
                manual_key = manual_data['data']['issueKey']
                created_resources.append(('test', manual_id))
                print(f"✅ Created manual test: {manual_key}")
            else:
                pytest.fail(f"Manual test creation failed: {manual_data.get('errors')}")

            # Step 2: Create Test Execution (FTEST-1457 equivalent)
            execution_test = {
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Test Execution - Login Tests',
                'test_issue_ids': [manual_id],
                'test_environments': ['staging', 'production']  # Array that might fail validation
            }

            exec_result = await tool.run(execution_test)
            exec_data = parse_mcp_response(exec_result) if isinstance(exec_result, list) else exec_result

            if exec_data.get('success'):
                exec_id = exec_data['data']['issueId']
                exec_key = exec_data['data']['issueKey']
                created_resources.append(('test_execution', exec_id))
                print(f"✅ Created test execution: {exec_key}")
            else:
                print(f"⚠️ Test execution creation failed: {exec_data.get('errors')}")

            # Step 3: Create Test Plan (FTEST-1458 equivalent)
            plan_test = {
                'entity': 'test_plan',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Test Plan - Authentication Module',
                'test_issue_ids': [manual_id]
            }

            plan_result = await tool.run(plan_test)
            plan_data = parse_mcp_response(plan_result) if isinstance(plan_result, list) else plan_result

            if plan_data.get('success'):
                plan_id = plan_data['data']['issueId']
                plan_key = plan_data['data']['issueKey']
                created_resources.append(('test_plan', plan_id))
                print(f"✅ Created test plan: {plan_key}")
            else:
                print(f"⚠️ Test plan creation failed: {plan_data.get('errors')}")

            # Step 4: Try to retrieve entities (reproducing QA retrieval failures)
            retrieval_failures = 0

            for entity_type, entity_id in [('test', manual_id)]:
                get_result = await tool.run({
                    'entity': entity_type,
                    'action': 'get',
                    'issue_id': entity_id
                })
                get_data = parse_mcp_response(get_result) if isinstance(get_result, list) else get_result

                if not get_data.get('success'):
                    retrieval_failures += 1
                    print(f"❌ Failed to retrieve {entity_type}: {get_data.get('errors')}")
                else:
                    print(f"✅ Successfully retrieved {entity_type}")

            # Assess overall QA scenario result
            total_entities = len(created_resources)
            success_rate = ((total_entities - retrieval_failures) / total_entities) * 100 if total_entities > 0 else 0

            print(f"\n📊 QA Scenario Results:")
            print(f"   Entities created: {total_entities}")
            print(f"   Retrieval failures: {retrieval_failures}")
            print(f"   Success rate: {success_rate:.1f}%")

            if success_rate < 60:  # QA report showed 60% success rate
                pytest.fail(f"QA scenario reproduced: Low success rate ({success_rate:.1f}%) matches QA report")
            else:
                print("✅ QA scenario success rate improved")

        finally:
            await self._cleanup_resources(tool, created_resources)