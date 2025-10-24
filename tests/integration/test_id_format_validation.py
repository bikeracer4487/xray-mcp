"""
ID Format Validation Tests

These tests specifically validate the critical ID format issue discovered in QA reports:
- Operations work with numeric IDs (e.g., "1192649")
- Operations fail with JIRA keys (e.g., "FTEST-1590")

This is the KEY DISCOVERY that explains why many operations appeared broken
but actually work correctly when using the proper ID format.
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
class TestIDFormatValidation:
    """Test that validates the critical ID format requirements for Xray operations."""

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
        return f"ID-FMT-{uuid.uuid4().hex[:6]}"

    @pytest.fixture
    def project_key(self):
        """Get project key from environment."""
        return os.getenv('DEFAULT_PROJECT_KEY', 'FTEST')

    @pytest.mark.asyncio
    async def test_id_format_discovery_get_operations(self, tool, unique_prefix, project_key):
        """
        Test the KEY DISCOVERY: Get operations work with numeric IDs but fail with JIRA keys.

        This reproduces the exact issue from the QA reports:
        - ✅ issue_id: "1192649" works
        - ❌ issue_id: "FTEST-1590" fails
        """
        print(f"\n🔍 Testing ID Format for Get Operations - {unique_prefix}")
        created_resources = []

        try:
            # Step 1: Create a test to get both ID formats
            create_result = await tool.run({
                "entity": "test",
                "action": "create",
                "project_key": project_key,
                "test_type": "Manual",
                "summary": f"{unique_prefix} ID Format Validation Test",
                "description": "Test to validate numeric ID vs JIRA key formats"
            })

            create_response = parse_mcp_response(create_result)
            assert create_response['success'], f"Create failed: {create_response.get('errors')}"

            numeric_id = create_response['data']['issueId']    # e.g., "1192649"
            jira_key = create_response['data']['issueKey']     # e.g., "FTEST-1590"
            created_resources.append(('test', numeric_id))

            print(f"   Created test with numeric ID: {numeric_id}")
            print(f"   Created test with JIRA key: {jira_key}")

            # Step 2: Test GET with numeric ID (should work)
            print(f"\n📊 Testing GET with numeric ID: {numeric_id}")
            get_numeric_result = await tool.run({
                "entity": "test",
                "action": "get",
                "issue_id": numeric_id
            })

            get_numeric_response = parse_mcp_response(get_numeric_result)
            numeric_success = get_numeric_response['success']

            print(f"   Result: {'✅ SUCCESS' if numeric_success else '❌ FAILED'}")
            if not numeric_success:
                print(f"   Error: {get_numeric_response.get('errors')}")

            # Step 3: Test GET with JIRA key (should fail)
            print(f"\n📊 Testing GET with JIRA key: {jira_key}")
            get_jira_result = await tool.run({
                "entity": "test",
                "action": "get",
                "issue_id": jira_key
            })

            get_jira_response = parse_mcp_response(get_jira_result)
            jira_success = get_jira_response['success']

            print(f"   Result: {'❌ FAILED' if not jira_success else '✅ UNEXPECTED SUCCESS'}")
            if not jira_success:
                print(f"   Error: {get_jira_response.get('errors')}")

            # Step 4: Validate the KEY DISCOVERY
            if numeric_success and not jira_success:
                print(f"\n🔑 KEY DISCOVERY CONFIRMED:")
                print(f"   ✅ Numeric ID works: {numeric_id}")
                print(f"   ❌ JIRA key fails: {jira_key}")
                print(f"   📋 Error with JIRA key: {get_jira_response.get('errors', ['Unknown error'])[0]}")

                # This confirms the discovery but should be fixed with better error messages
                error_msg = get_jira_response.get('errors', ['Unknown error'])[0]
                if "not found" in error_msg.lower():
                    pytest.fail(
                        f"ID FORMAT ISSUE CONFIRMED: JIRA key '{jira_key}' fails but numeric ID '{numeric_id}' works. "
                        f"Error message needs improvement: {error_msg}"
                    )
                else:
                    print(f"   📝 Error message seems improved: {error_msg}")

            elif not numeric_success and not jira_success:
                pytest.fail(f"Both ID formats failed - indexing delay or other issue: {get_numeric_response.get('errors')}")

            elif numeric_success and jira_success:
                print("✅ Both ID formats work - issue has been FIXED!")

            else:
                pytest.fail(f"Unexpected result: numeric failed but JIRA succeeded")

        finally:
            # Cleanup with numeric ID (more likely to work)
            for resource_type, resource_id in created_resources:
                for attempt in range(3):
                    try:
                        await tool.run({
                            'entity': resource_type,
                            'action': 'delete',
                            'issue_id': resource_id
                        })
                        break
                    except Exception:
                        if attempt < 2:
                            await asyncio.sleep(2)

    @pytest.mark.asyncio
    async def test_id_format_discovery_delete_operations(self, tool, unique_prefix, project_key):
        """
        Test the KEY DISCOVERY: Delete operations work with numeric IDs but fail with JIRA keys.

        This reproduces the delete operation failures from the QA reports.
        """
        print(f"\n🔍 Testing ID Format for Delete Operations - {unique_prefix}")
        created_resources = []

        try:
            # Create two identical tests for deletion testing
            for i in range(2):
                create_result = await tool.run({
                    "entity": "test",
                    "action": "create",
                    "project_key": project_key,
                    "test_type": "Manual",
                    "summary": f"{unique_prefix} Delete Test {i+1}",
                    "description": f"Test {i+1} for delete ID format validation"
                })

                create_response = parse_mcp_response(create_result)
                assert create_response['success'], f"Create {i+1} failed: {create_response.get('errors')}"

                numeric_id = create_response['data']['issueId']
                jira_key = create_response['data']['issueKey']
                created_resources.append((numeric_id, jira_key))

                print(f"   Created test {i+1}: numeric={numeric_id}, jira={jira_key}")

            # Test delete with JIRA key first (should fail)
            numeric_id_1, jira_key_1 = created_resources[0]
            print(f"\n📊 Testing DELETE with JIRA key: {jira_key_1}")

            delete_jira_result = await tool.run({
                "entity": "test",
                "action": "delete",
                "issue_id": jira_key_1
            })

            delete_jira_response = parse_mcp_response(delete_jira_result)
            jira_delete_success = delete_jira_response['success']

            print(f"   Result: {'❌ FAILED' if not jira_delete_success else '✅ UNEXPECTED SUCCESS'}")
            if not jira_delete_success:
                print(f"   Error: {delete_jira_response.get('errors')}")

            # Test delete with numeric ID (should work)
            numeric_id_2, jira_key_2 = created_resources[1]
            print(f"\n📊 Testing DELETE with numeric ID: {numeric_id_2}")

            delete_numeric_result = await tool.run({
                "entity": "test",
                "action": "delete",
                "issue_id": numeric_id_2
            })

            delete_numeric_response = parse_mcp_response(delete_numeric_result)
            numeric_delete_success = delete_numeric_response['success']

            print(f"   Result: {'✅ SUCCESS' if numeric_delete_success else '❌ FAILED'}")
            if not numeric_delete_success:
                print(f"   Error: {delete_numeric_response.get('errors')}")
            else:
                # Remove successfully deleted resource from cleanup list
                created_resources.remove((numeric_id_2, jira_key_2))

            # Validate the KEY DISCOVERY for delete operations
            if numeric_delete_success and not jira_delete_success:
                print(f"\n🔑 DELETE FORMAT DISCOVERY CONFIRMED:")
                print(f"   ✅ Numeric ID deletes successfully: {numeric_id_2}")
                print(f"   ❌ JIRA key delete fails: {jira_key_1}")

                error_msg = delete_jira_response.get('errors', ['Unknown error'])[0]
                if "not found" in error_msg.lower():
                    pytest.fail(
                        f"DELETE ID FORMAT ISSUE CONFIRMED: JIRA key '{jira_key_1}' fails but numeric ID '{numeric_id_2}' works. "
                        f"Error message needs improvement: {error_msg}"
                    )
                else:
                    print(f"   📝 Error message seems improved: {error_msg}")

            elif not numeric_delete_success and not jira_delete_success:
                pytest.fail(f"Both delete formats failed - may be indexing delay or other issue")

            elif numeric_delete_success and jira_delete_success:
                print("✅ Both delete ID formats work - issue has been FIXED!")

            else:
                pytest.fail(f"Unexpected delete result: numeric failed but JIRA succeeded")

        finally:
            # Cleanup remaining resources using numeric IDs
            for numeric_id, jira_key in created_resources:
                for attempt in range(3):
                    try:
                        await tool.run({
                            'entity': 'test',
                            'action': 'delete',
                            'issue_id': numeric_id  # Use numeric ID for cleanup
                        })
                        break
                    except Exception:
                        if attempt < 2:
                            await asyncio.sleep(2)

    @pytest.mark.asyncio
    async def test_id_format_discovery_update_operations(self, tool, unique_prefix, project_key):
        """
        Test the KEY DISCOVERY: Update operations work with numeric IDs but fail with JIRA keys.

        This tests the update_type operation that was mentioned in the reports.
        """
        print(f"\n🔍 Testing ID Format for Update Operations - {unique_prefix}")
        created_resources = []

        try:
            # Create a Generic test to update to Manual type
            create_result = await tool.run({
                "entity": "test",
                "action": "create",
                "project_key": project_key,
                "test_type": "Generic",
                "summary": f"{unique_prefix} Update Type Test",
                "description": "Test for update type ID format validation"
            })

            create_response = parse_mcp_response(create_result)
            assert create_response['success'], f"Create failed: {create_response.get('errors')}"

            numeric_id = create_response['data']['issueId']
            jira_key = create_response['data']['issueKey']
            created_resources.append(('test', numeric_id))

            print(f"   Created Generic test: numeric={numeric_id}, jira={jira_key}")

            # Test update_type with JIRA key (should fail)
            print(f"\n📊 Testing UPDATE_TYPE with JIRA key: {jira_key}")

            update_jira_result = await tool.run({
                "entity": "test",
                "action": "update_type",
                "issue_id": jira_key,
                "test_type": "Manual"
            })

            update_jira_response = parse_mcp_response(update_jira_result)
            jira_update_success = update_jira_response['success']

            print(f"   Result: {'❌ FAILED' if not jira_update_success else '✅ UNEXPECTED SUCCESS'}")
            if not jira_update_success:
                print(f"   Error: {update_jira_response.get('errors')}")

            # Test update_type with numeric ID (should work)
            print(f"\n📊 Testing UPDATE_TYPE with numeric ID: {numeric_id}")

            update_numeric_result = await tool.run({
                "entity": "test",
                "action": "update_type",
                "issue_id": numeric_id,
                "test_type": "Manual"
            })

            update_numeric_response = parse_mcp_response(update_numeric_result)
            numeric_update_success = update_numeric_response['success']

            print(f"   Result: {'✅ SUCCESS' if numeric_update_success else '❌ FAILED'}")
            if not numeric_update_success:
                print(f"   Error: {update_numeric_response.get('errors')}")

            # Validate the KEY DISCOVERY for update operations
            if numeric_update_success and not jira_update_success:
                print(f"\n🔑 UPDATE FORMAT DISCOVERY CONFIRMED:")
                print(f"   ✅ Numeric ID updates successfully: {numeric_id}")
                print(f"   ❌ JIRA key update fails: {jira_key}")

                error_msg = update_jira_response.get('errors', ['Unknown error'])[0]
                if "not valid" in error_msg.lower() or "not found" in error_msg.lower():
                    pytest.fail(
                        f"UPDATE ID FORMAT ISSUE CONFIRMED: JIRA key '{jira_key}' fails but numeric ID '{numeric_id}' works. "
                        f"Error message needs improvement: {error_msg}"
                    )
                else:
                    print(f"   📝 Error message seems improved: {error_msg}")

            elif not numeric_update_success and not jira_update_success:
                pytest.fail(f"Both update formats failed - may be indexing delay or other issue")

            elif numeric_update_success and jira_update_success:
                print("✅ Both update ID formats work - issue has been FIXED!")

            else:
                pytest.fail(f"Unexpected update result: numeric failed but JIRA succeeded")

        finally:
            # Cleanup using numeric IDs
            for resource_type, resource_id in created_resources:
                for attempt in range(3):
                    try:
                        await tool.run({
                            'entity': resource_type,
                            'action': 'delete',
                            'issue_id': resource_id
                        })
                        break
                    except Exception:
                        if attempt < 2:
                            await asyncio.sleep(2)

    @pytest.mark.asyncio
    async def test_id_format_across_all_entity_types(self, tool, unique_prefix, project_key):
        """
        Test ID format issue across all entity types: tests, test_executions, test_plans.

        This comprehensive test ensures the ID format issue affects all entity types consistently.
        """
        print(f"\n🔍 Testing ID Format Across All Entity Types - {unique_prefix}")
        created_resources = []

        try:
            # Create one of each entity type
            entity_configs = [
                {
                    "entity": "test",
                    "params": {
                        "project_key": project_key,
                        "test_type": "Manual",
                        "summary": f"{unique_prefix} Cross-Entity Test"
                    }
                },
                {
                    "entity": "test_execution",
                    "params": {
                        "project_key": project_key,
                        "summary": f"{unique_prefix} Cross-Entity Execution"
                    }
                },
                {
                    "entity": "test_plan",
                    "params": {
                        "project_key": project_key,
                        "summary": f"{unique_prefix} Cross-Entity Plan"
                    }
                }
            ]

            created_entities = []

            # Create all entities
            for config in entity_configs:
                create_result = await tool.run({
                    "entity": config["entity"],
                    "action": "create",
                    **config["params"]
                })

                create_response = parse_mcp_response(create_result)
                if create_response['success']:
                    numeric_id = create_response['data']['issueId']
                    jira_key = create_response['data']['issueKey']
                    created_entities.append((config["entity"], numeric_id, jira_key))
                    created_resources.append((config["entity"], numeric_id))
                    print(f"   Created {config['entity']}: {jira_key} ({numeric_id})")
                else:
                    print(f"   Failed to create {config['entity']}: {create_response.get('errors')}")

            # Test GET operations for each entity type with both ID formats
            format_results = {}

            for entity_type, numeric_id, jira_key in created_entities:
                print(f"\n📊 Testing {entity_type.upper()} GET operations:")

                # Test with numeric ID
                get_numeric_result = await tool.run({
                    "entity": entity_type,
                    "action": "get",
                    "issue_id": numeric_id
                })
                numeric_success = parse_mcp_response(get_numeric_result)['success']

                # Test with JIRA key
                get_jira_result = await tool.run({
                    "entity": entity_type,
                    "action": "get",
                    "issue_id": jira_key
                })
                jira_success = parse_mcp_response(get_jira_result)['success']

                format_results[entity_type] = {
                    'numeric_success': numeric_success,
                    'jira_success': jira_success,
                    'numeric_id': numeric_id,
                    'jira_key': jira_key
                }

                print(f"   Numeric ID {numeric_id}: {'✅ SUCCESS' if numeric_success else '❌ FAILED'}")
                print(f"   JIRA key {jira_key}: {'✅ SUCCESS' if jira_success else '❌ FAILED'}")

            # Analyze results across all entity types
            all_numeric_work = all(result['numeric_success'] for result in format_results.values())
            all_jira_fail = all(not result['jira_success'] for result in format_results.values())

            print(f"\n📋 CROSS-ENTITY ID FORMAT ANALYSIS:")
            print(f"   All numeric IDs work: {all_numeric_work}")
            print(f"   All JIRA keys fail: {all_jira_fail}")

            if all_numeric_work and all_jira_fail:
                print("🔑 ID FORMAT ISSUE CONFIRMED ACROSS ALL ENTITY TYPES")

                # Show examples of each failure
                for entity_type, results in format_results.items():
                    print(f"   {entity_type}: {results['jira_key']} fails, {results['numeric_id']} works")

                pytest.fail(
                    "ID FORMAT ISSUE CONFIRMED: All entity types require numeric IDs, JIRA keys fail consistently. "
                    "This is a systematic issue requiring documentation and validation improvements."
                )
            elif all_numeric_work and not all_jira_fail:
                print("✅ PARTIAL FIX: All numeric IDs work, some JIRA keys work - improvement detected!")
            elif not all_numeric_work and all_jira_fail:
                pytest.fail("Mixed results: Some numeric IDs fail - may be indexing delays or other issues")
            else:
                print("✅ Both ID formats work across all entity types - issue has been FIXED!")

        finally:
            # Cleanup all created resources using numeric IDs
            for entity_type, resource_id in created_resources:
                for attempt in range(3):
                    try:
                        await tool.run({
                            'entity': entity_type,
                            'action': 'delete',
                            'issue_id': resource_id
                        })
                        break
                    except Exception:
                        if attempt < 2:
                            await asyncio.sleep(2)

    @pytest.mark.asyncio
    async def test_error_message_quality_for_id_format(self, tool, project_key):
        """
        Test the quality of error messages when using JIRA keys instead of numeric IDs.

        This validates whether error messages help users understand the ID format requirement.
        """
        print(f"\n🔍 Testing Error Message Quality for ID Format Issues")

        # Test with a non-existent but valid JIRA key format
        fake_jira_key = f"{project_key}-99999"
        fake_numeric_id = "99999999"

        print(f"   Testing with fake JIRA key: {fake_jira_key}")
        print(f"   Testing with fake numeric ID: {fake_numeric_id}")

        # Test GET with fake JIRA key - should now be caught by validation
        jira_error = None
        try:
            get_jira_result = await tool.run({
                "entity": "test",
                "action": "get",
                "issue_id": fake_jira_key
            })
            # If we get here, validation didn't work
            jira_response = parse_mcp_response(get_jira_result)
            if not jira_response['success']:
                jira_error = jira_response.get('errors', ['Unknown error'])[0]
        except Exception as e:
            # This is expected - validation should catch JIRA keys immediately
            jira_error = str(e)
            # Remove "Operation failed: " prefix for cleaner error message
            if jira_error.startswith("Operation failed: "):
                jira_error = jira_error[len("Operation failed: "):]

        # Test GET with fake numeric ID - should reach the API and get "not found"
        numeric_error = None
        try:
            get_numeric_result = await tool.run({
                "entity": "test",
                "action": "get",
                "issue_id": fake_numeric_id
            })
            numeric_response = parse_mcp_response(get_numeric_result)
            if not numeric_response['success']:
                numeric_error = numeric_response.get('errors', ['Unknown error'])[0]
        except Exception as e:
            numeric_error = str(e)
            if numeric_error.startswith("Operation failed: "):
                numeric_error = numeric_error[len("Operation failed: "):]

        print(f"\n📋 Error Message Analysis:")
        print(f"   JIRA key error: {jira_error}")
        print(f"   Numeric ID error: {numeric_error}")

        # Evaluate error message quality
        if jira_error:
            # Check if JIRA key error mentions format requirements
            helpful_keywords = ['numeric', 'format', 'id format', 'use numeric', 'numeric id required', 'jira keys']
            jira_error_lower = jira_error.lower()

            is_helpful = any(keyword in jira_error_lower for keyword in helpful_keywords)

            print(f"\n📊 Error Message Quality Assessment:")
            print(f"   Error mentions format requirements: {is_helpful}")
            print(f"   JIRA key error is different from numeric error: {jira_error != numeric_error}")

            if is_helpful:
                print("✅ Error message provides helpful guidance about ID format requirements")
                
                # Verify specific helpful elements
                if 'jira keys' in jira_error_lower and 'numeric' in jira_error_lower:
                    print("✅ Error specifically mentions JIRA keys and numeric IDs")
                if 'example' in jira_error_lower or '1192649' in jira_error:
                    print("✅ Error provides concrete example")
                if 'list operation' in jira_error_lower:
                    print("✅ Error explains how to find numeric ID")
                    
            else:
                print("❌ Error message needs improvement to guide users to use numeric IDs")
                pytest.fail(
                    f"ERROR MESSAGE QUALITY ISSUE: JIRA key error '{jira_error}' doesn't mention format requirements. "
                    f"Should guide users to use numeric IDs instead of JIRA keys."
                )
        else:
            pytest.fail("No error message received for JIRA key - validation may not be working")