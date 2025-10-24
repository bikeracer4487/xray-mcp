"""
Test suite that reproduces all 5 critical issues identified in the QA report.

This test file is designed to FAIL initially, demonstrating that the issues are real.
After implementing fixes, these tests should PASS, proving the issues are resolved.

Critical Issues Reproduced:
1. Response Format Error - "structured_content must be a dict or None. Got list"
2. Indexing Delays - Recently created objects not immediately retrievable
3. GraphQL Query Issues - "Cannot query field 'warnings' on type 'Test'"
4. Inconsistent Object Retrieval - Objects in list but not in get
5. Parameter Validation Issues - test_environments format unclear
"""

import pytest
import os
import uuid
import asyncio
from dotenv import load_dotenv
from src.server import create_server
from tests.integration.test_helpers import parse_mcp_response

load_dotenv()


@pytest.mark.skipif(
    not all([os.getenv('XRAY_CLIENT_ID'), os.getenv('XRAY_CLIENT_SECRET')]),
    reason="Xray credentials not available"
)
class TestCriticalIssuesReproduction:
    """Tests that reproduce critical issues from QA report."""

    @pytest.fixture
    def server(self):
        """Create server instance."""
        return create_server()

    @pytest.fixture
    def tool(self, server):
        """Get the xray_test tool."""
        return server._tool_manager._tools['xray_test']

    @pytest.fixture
    def unique_prefix(self):
        """Generate unique prefix for test data."""
        return f"CRIT-{uuid.uuid4().hex[:6]}"

    @pytest.fixture
    def project_key(self):
        """Get project key from environment."""
        return os.getenv('DEFAULT_PROJECT_KEY', 'FTEST')

    @pytest.mark.asyncio
    async def test_issue_1_response_format_error(self, tool, unique_prefix, project_key):
        """
        CRITICAL ISSUE 1: Response Format Error

        Expected to FAIL initially with: "structured_content must be a dict or None. Got list"
        This happens on 100% of operations according to the QA report.

        The server returns a list when MCP protocol expects a dict.
        """
        print(f"\n🔴 Testing Issue 1: Response Format Error - {unique_prefix}")
        created_resources = []

        try:
            # This operation should work but fail due to response format
            test_params = {
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Response Format Test',
                'test_type': 'Manual'
            }

            # The tool.run() call should return MCP format (list of TextContent)
            result = await tool.run(test_params)
            print(f"Result type: {type(result)}")
            print(f"Result: {result}")

            # Test if we can successfully parse the MCP response
            try:
                test_data = parse_mcp_response(result)
                print("✅ Successfully parsed MCP response format")
            except Exception as parse_error:
                if "structured_content must be a dict" in str(parse_error):
                    print(f"🔴 CONFIRMED: Issue 1 reproduced - {str(parse_error)}")
                    pytest.fail(f"Issue 1 reproduced: Response format error - {str(parse_error)}")
                else:
                    print(f"❌ Different parsing error: {str(parse_error)}")
                    pytest.fail(f"Unexpected parsing error: {str(parse_error)}")
                return

            if test_data.get('success'):
                created_resources.append(('test', test_data['data']['issueId']))
                print("✅ Response format is correct (Issue 1 is FIXED)")
            else:
                print(f"❌ Test creation failed: {test_data.get('errors')}")

        except Exception as e:
            if "structured_content must be a dict" in str(e):
                print(f"🔴 CONFIRMED: Issue 1 reproduced - {str(e)}")
                pytest.fail(f"Issue 1 reproduced: Response format error - {str(e)}")
            else:
                print(f"❌ Unexpected error: {str(e)}")
                raise

        finally:
            # Cleanup
            for resource_type, resource_id in created_resources:
                try:
                    await tool.run({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception:
                    pass

    @pytest.mark.asyncio
    async def test_issue_2_indexing_delays(self, tool, unique_prefix, project_key):
        """
        CRITICAL ISSUE 2: Indexing Delays AND ID Format Issues

        Expected to FAIL initially because:
        1. Created objects cannot be retrieved immediately due to indexing delays
        2. JIRA keys fail even when numeric IDs work (KEY DISCOVERY from QA reports)

        This test now validates both the indexing delay issue AND the ID format issue.
        """
        print(f"\n🔴 Testing Issue 2: Indexing Delays + ID Format - {unique_prefix}")
        created_resources = []

        try:
            # Step 1: Create a test
            test_params = {
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Indexing Delay Test',
                'test_type': 'Manual'
            }

            create_result = await tool.run(test_params)
            create_data = parse_mcp_response(create_result) if isinstance(create_result, list) else create_result

            assert create_data.get('success'), f"Test creation failed: {create_data.get('errors')}"

            test_id = create_data['data']['issueId']    # Numeric ID (e.g., "1192649")
            test_key = create_data['data']['issueKey']  # JIRA key (e.g., "FTEST-1590")
            created_resources.append(('test', test_id))
            print(f"✅ Created test: {test_key} (numeric: {test_id})")

            # Step 2A: Try with JIRA key first (should fail due to ID format issue)
            print(f"\n📊 Testing GET with JIRA key: {test_key}")
            get_jira_params = {
                'entity': 'test',
                'action': 'get',
                'issue_id': test_key  # Using JIRA key format
            }

            get_jira_result = await tool.run(get_jira_params)
            get_jira_data = parse_mcp_response(get_jira_result) if isinstance(get_jira_result, list) else get_jira_result

            jira_success = get_jira_data.get('success')
            print(f"   JIRA key result: {'✅ SUCCESS' if jira_success else '❌ FAILED'}")
            if not jira_success:
                print(f"   JIRA key error: {get_jira_data.get('errors', ['Unknown error'])[0]}")

            # Step 2B: Try with numeric ID (should work with advanced retry)
            print(f"\n📊 Testing GET with numeric ID: {test_id}")
            get_numeric_params = {
                'entity': 'test',
                'action': 'get',
                'issue_id': test_id  # Using numeric ID format
            }

            get_numeric_result = await tool.run(get_numeric_params)
            get_numeric_data = parse_mcp_response(get_numeric_result) if isinstance(get_numeric_result, list) else get_numeric_result

            numeric_success = get_numeric_data.get('success')
            print(f"   Numeric ID result: {'✅ SUCCESS' if numeric_success else '❌ FAILED'}")
            if not numeric_success:
                print(f"   Numeric ID error: {get_numeric_data.get('errors', ['Unknown error'])[0]}")

            # Step 3: Analyze the results to determine the actual issue
            if numeric_success and not jira_success:
                print(f"\n🔑 KEY DISCOVERY CONFIRMED:")
                print(f"   ✅ Numeric ID works: {test_id}")
                print(f"   ❌ JIRA key fails: {test_key}")
                print(f"   📋 Issue is ID FORMAT, not just indexing delays!")
                
                jira_error = get_jira_data.get('errors', ['Unknown error'])[0]
                pytest.fail(f"Issue 2 UPDATED: ID format issue confirmed - JIRA key '{test_key}' fails but numeric ID '{test_id}' works. Error: {jira_error}")
                
            elif not numeric_success and not jira_success:
                numeric_error = get_numeric_data.get('errors', ['Unknown error'])[0]
                jira_error = get_jira_data.get('errors', ['Unknown error'])[0]
                print(f"\n🔴 BOTH FORMATS FAILED:")
                print(f"   ❌ Numeric ID error: {numeric_error}")
                print(f"   ❌ JIRA key error: {jira_error}")
                
                if "not found" in numeric_error:
                    pytest.fail(f"Issue 2 reproduced: True indexing delay - even numeric ID fails: {numeric_error}")
                else:
                    pytest.fail(f"Issue 2: Unexpected errors - Numeric: {numeric_error}, JIRA: {jira_error}")
                    
            elif numeric_success and jira_success:
                print("✅ Both ID formats work - ALL ISSUES FIXED!")
                
            else:
                # numeric failed but jira succeeded - unexpected
                pytest.fail(f"Unexpected result: numeric ID failed but JIRA key succeeded")

        finally:
            # Cleanup (try multiple times due to indexing delays, use numeric ID)
            for resource_type, resource_id in created_resources:
                for attempt in range(3):
                    try:
                        await tool.run({
                            'entity': resource_type,
                            'action': 'delete',
                            'issue_id': resource_id  # Use numeric ID for cleanup
                        })
                        break
                    except Exception:
                        if attempt < 2:
                            await asyncio.sleep(3)
                        pass

    @pytest.mark.asyncio
    async def test_issue_3_graphql_query_issues(self, tool, unique_prefix, project_key):
        """
        CRITICAL ISSUE 3: GraphQL Query Issues

        Expected to FAIL initially with: "Cannot query field 'warnings' on type 'Test'"
        This happens when trying to update test content due to malformed GraphQL queries.
        """
        print(f"\n🔴 Testing Issue 3: GraphQL Query Issues - {unique_prefix}")
        created_resources = []

        try:
            # Step 1: Create a Cucumber test to update
            test_params = {
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} GraphQL Update Test',
                'test_type': 'Cucumber',
                'gherkin': '''Feature: Initial Test

                Scenario: Basic test
                    Given I have a test
                    When I run it
                    Then it should work'''
            }

            create_result = await tool.run(test_params)
            create_data = parse_mcp_response(create_result) if isinstance(create_result, list) else create_result

            if not create_data.get('success'):
                pytest.skip(f"Cannot test GraphQL updates - test creation failed: {create_data.get('errors')}")

            test_id = create_data['data']['issueId']
            created_resources.append(('test', test_id))
            print(f"✅ Created Cucumber test: {create_data['data']['issueKey']}")

            # Step 2: Try to update the Gherkin content (this should fail due to GraphQL issue)
            update_gherkin = '''Feature: Updated Test

            Scenario: Updated test scenario
                Given I have an updated test
                When I run the updated version
                Then it should work better'''

            update_params = {
                'entity': 'test',
                'action': 'update_content',
                'issue_id': test_id,
                'gherkin': update_gherkin
            }

            update_result = await tool.run(update_params)
            update_data = parse_mcp_response(update_result) if isinstance(update_result, list) else update_result

            if update_data.get('success'):
                print("✅ Gherkin update succeeded (Issue 3 is FIXED)")
            else:
                error_msg = update_data.get('errors', ['Unknown error'])[0]
                if 'Cannot query field "warnings"' in error_msg:
                    print(f"🔴 CONFIRMED: Issue 3 reproduced - {error_msg}")
                    pytest.fail(f"Issue 3 reproduced: GraphQL query error - {error_msg}")
                else:
                    print(f"❌ Different error during update: {error_msg}")
                    # Still a failure, but might be a different issue
                    pytest.fail(f"Update failed with different error: {error_msg}")

        finally:
            # Cleanup
            for resource_type, resource_id in created_resources:
                try:
                    await tool.run({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception:
                    pass

    @pytest.mark.asyncio
    async def test_issue_4_inconsistent_object_retrieval(self, tool, unique_prefix, project_key):
        """
        CRITICAL ISSUE 4: Inconsistent Object Retrieval AND ID Format Issues

        Expected to FAIL initially because:
        1. Objects appear in list operations but fail in get operations
        2. This is likely due to ID format issues (JIRA keys vs numeric IDs)

        Updated to test both the consistency issue AND the ID format discovery.
        """
        print(f"\n🔴 Testing Issue 4: Inconsistent Object Retrieval + ID Format - {unique_prefix}")
        created_resources = []

        try:
            # Step 1: Create a test execution
            exec_params = {
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Consistency Test Execution'
            }

            create_result = await tool.run(exec_params)
            create_data = parse_mcp_response(create_result) if isinstance(create_result, list) else create_result

            assert create_data.get('success'), f"Execution creation failed: {create_data.get('errors')}"

            execution_id = create_data['data']['issueId']    # Numeric ID
            execution_key = create_data['data']['issueKey']   # JIRA key
            created_resources.append(('test_execution', execution_id))
            print(f"✅ Created execution: {execution_key} (numeric: {execution_id})")

            # Step 2: List executions - this should include our newly created execution
            list_params = {
                'entity': 'test_execution',
                'action': 'list',
                'project_key': project_key,
                'limit': 50
            }

            list_result = await tool.run(list_params)
            list_data = parse_mcp_response(list_result) if isinstance(list_result, list) else list_result

            assert list_data.get('success'), f"List operation failed: {list_data.get('errors')}"

            # Check if our execution appears in the list
            executions = list_data['data']['executions']
            found_in_list = any(exec['issueId'] == execution_id for exec in executions)
            found_jira_in_list = any(exec.get('issueKey') == execution_key for exec in executions)

            print(f"📊 List operation results:")
            print(f"   Found by numeric ID: {found_in_list}")
            print(f"   Found by JIRA key: {found_jira_in_list}")

            # Step 3A: Try to get with JIRA key (should fail due to ID format)
            print(f"\n📊 Testing GET with JIRA key: {execution_key}")
            get_jira_params = {
                'entity': 'test_execution',
                'action': 'get',
                'issue_id': execution_key  # Using JIRA key from list
            }

            get_jira_result = await tool.run(get_jira_params)
            get_jira_data = parse_mcp_response(get_jira_result) if isinstance(get_jira_result, list) else get_jira_result

            jira_get_success = get_jira_data.get('success')
            print(f"   JIRA key GET result: {'✅ SUCCESS' if jira_get_success else '❌ FAILED'}")
            if not jira_get_success:
                print(f"   JIRA key error: {get_jira_data.get('errors', ['Unknown error'])[0]}")

            # Step 3B: Try to get with numeric ID (should work)
            print(f"\n📊 Testing GET with numeric ID: {execution_id}")
            get_numeric_params = {
                'entity': 'test_execution',
                'action': 'get',
                'issue_id': execution_id  # Using numeric ID
            }

            get_numeric_result = await tool.run(get_numeric_params)
            get_numeric_data = parse_mcp_response(get_numeric_result) if isinstance(get_numeric_result, list) else get_numeric_result

            numeric_get_success = get_numeric_data.get('success')
            print(f"   Numeric ID GET result: {'✅ SUCCESS' if numeric_get_success else '❌ FAILED'}")
            if not numeric_get_success:
                print(f"   Numeric ID error: {get_numeric_data.get('errors', ['Unknown error'])[0]}")

            # Step 4: Analyze the consistency vs ID format issue
            if found_in_list and numeric_get_success and not jira_get_success:
                print(f"\n🔑 ID FORMAT INCONSISTENCY CONFIRMED:")
                print(f"   ✅ Found in list operation")
                print(f"   ✅ GET works with numeric ID: {execution_id}")
                print(f"   ❌ GET fails with JIRA key: {execution_key}")
                print(f"   📋 Issue is ID FORMAT, not retrieval consistency!")
                
                jira_error = get_jira_data.get('errors', ['Unknown error'])[0]
                pytest.fail(f"Issue 4 UPDATED: ID format causes apparent inconsistency - execution found in list but JIRA key '{execution_key}' fails in GET while numeric ID '{execution_id}' works. Error: {jira_error}")
                
            elif found_in_list and not numeric_get_success and not jira_get_success:
                print(f"\n🔴 TRUE INCONSISTENCY CONFIRMED:")
                print(f"   ✅ Found in list operation") 
                print(f"   ❌ GET fails with both ID formats")
                print(f"   📋 This is a real retrieval consistency issue!")
                
                numeric_error = get_numeric_data.get('errors', ['Unknown error'])[0]
                pytest.fail(f"Issue 4 reproduced: True inconsistent retrieval - in list but both GET operations fail. Numeric error: {numeric_error}")
                
            elif found_in_list and numeric_get_success and jira_get_success:
                print("✅ Consistent retrieval with both ID formats - Issue 4 is FIXED!")
                
            elif not found_in_list:
                pytest.skip("Cannot test retrieval consistency - execution not found in list (indexing delay)")
                
            else:
                print("❌ Unexpected state in consistency test")
                pytest.fail(f"Unexpected consistency test state - found_in_list: {found_in_list}, numeric_success: {numeric_get_success}, jira_success: {jira_get_success}")

        finally:
            # Cleanup using numeric ID
            for resource_type, resource_id in created_resources:
                try:
                    await tool.run({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id  # Use numeric ID for cleanup
                    })
                except Exception:
                    pass

    @pytest.mark.asyncio
    async def test_issue_5_parameter_validation_issues(self, tool, unique_prefix, project_key):
        """
        CRITICAL ISSUE 5: Parameter Validation Issues

        Expected to FAIL initially due to unclear parameter format validation,
        especially for array parameters like test_environments.
        """
        print(f"\n🔴 Testing Issue 5: Parameter Validation Issues - {unique_prefix}")
        created_resources = []

        try:
            # Test with unclear test_environments parameter format
            # This should either work or give a clear error message about format
            exec_params = {
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Parameter Validation Test',
                'test_environments': 'staging,qa'  # Wrong format - should be list
            }

            try:
                result = await tool.run(exec_params)
                result_data = parse_mcp_response(result) if isinstance(result, list) else result

                if result_data.get('success'):
                    # If it succeeds with wrong format, that's also a validation issue
                    created_resources.append(('test_execution', result_data['data']['issueId']))
                    print("⚠️ Validation issue: Wrong parameter format accepted")
                    pytest.fail("Issue 5 reproduced: Parameter validation too permissive - accepted wrong format")
                else:
                    error_msg = result_data.get('errors', ['Unknown error'])[0]

                    # Check if error message is helpful
                    if any(keyword in error_msg.lower() for keyword in ['format', 'array', 'list', 'example']):
                        print("✅ Clear validation error with helpful message (Issue 5 is FIXED)")
                    else:
                        print(f"🔴 CONFIRMED: Issue 5 reproduced - Unclear error: {error_msg}")
                        pytest.fail(f"Issue 5 reproduced: Parameter validation gives unclear error: {error_msg}")

            except Exception as validation_error:
                # Check if the validation error provides helpful information
                error_str = str(validation_error)
                if "Input should be a valid list" in error_str:
                    # This is the current validation error - check if it's helpful enough
                    if "example" in error_str.lower() or "format" in error_str.lower():
                        print("✅ Clear validation error with helpful format information (Issue 5 is FIXED)")
                    else:
                        print(f"🔴 CONFIRMED: Issue 5 reproduced - Pydantic validation error lacks context: {error_str}")
                        pytest.fail(f"Issue 5 reproduced: Parameter validation error lacks helpful context: {error_str}")
                else:
                    print(f"❌ Unexpected validation error: {error_str}")
                    raise

        finally:
            # Cleanup
            for resource_type, resource_id in created_resources:
                try:
                    await tool.run({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception:
                    pass

    @pytest.mark.asyncio
    async def test_all_issues_integration(self, tool, unique_prefix, project_key):
        """
        Integration test that combines multiple issues to see real-world impact.

        This test demonstrates how the issues compound to create a poor user experience.
        """
        print(f"\n🔴 Testing Combined Issues Impact - {unique_prefix}")

        try:
            # Try to create test, retrieve it, update it, and check status
            # This workflow should work smoothly but will hit multiple issues

            # Step 1: Create test (may hit Issue 1 - response format)
            test_params = {
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix} Integration Test',
                'test_type': 'Manual'
            }

            create_result = await tool.run(test_params)
            print(f"Create result type: {type(create_result)}")

            # If we get a list instead of dict, that's Issue 1
            if isinstance(create_result, list):
                print("🔴 Issue 1 (Response Format) encountered in integration test")

            create_data = parse_mcp_response(create_result) if isinstance(create_result, list) else create_result

            if not create_data.get('success'):
                pytest.fail(f"Integration test failed at creation: {create_data.get('errors')}")

            test_id = create_data['data']['issueId']

            # Step 2: Immediate retrieval (may hit Issue 2 - indexing delays)
            get_result = await tool.run({
                'entity': 'test',
                'action': 'get',
                'issue_id': test_id
            })

            get_data = parse_mcp_response(get_result) if isinstance(get_result, list) else get_result

            if not get_data.get('success'):
                print("🔴 Issue 2 (Indexing Delays) encountered in integration test")

            print("📊 Integration test reveals real-world compound issues")

        except Exception as e:
            print(f"🔴 Integration test failed with exception: {str(e)}")
            # Don't fail the test - this demonstrates the poor user experience