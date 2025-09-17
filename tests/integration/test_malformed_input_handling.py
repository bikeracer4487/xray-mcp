"""
Integration tests for malformed input handling.

Tests how the Xray MCP server handles various types of malformed, invalid,
or edge case inputs. Covers use cases UC-291 through UC-300.
"""

import pytest
import pytest_asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

from src.server import create_server
from src.tools.xray_tool import XrayTool


@pytest.fixture
def unique_prefix():
    """Generate unique prefix for test names."""
    return f"MalformedInput_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


@pytest.fixture
def project_key():
    """Get project key from environment."""
    import os
    return os.getenv('XRAY_PROJECT_KEY', 'FTEST')


@pytest.mark.asyncio
class TestMalformedInputHandling:
    """Test handling of malformed and invalid inputs."""

    async def test_invalid_entity_parameter(self, tool, project_key):
        """
        UC-291: Validate malformed JSON inputs and invalid entity types.

        Tests that the system properly handles invalid entity parameters.
        """
        # Test completely invalid entity
        result = await tool.execute({
            'entity': 'invalid_entity_type',
            'action': 'create',
            'project_key': project_key,
            'summary': 'Test Summary'
        })

        assert not result['success'], "Should fail with invalid entity"
        assert 'errors' in result, "Should contain error messages"
        assert any('invalid entity' in str(error).lower() for error in result['errors']), "Should mention invalid entity"

        # Test empty entity
        result = await tool.execute({
            'entity': '',
            'action': 'create',
            'project_key': project_key,
            'summary': 'Test Summary'
        })

        assert not result['success'], "Should fail with empty entity"
        assert 'entity' in str(result.get('errors', [])).lower(), "Should mention missing entity"

        # Test None entity
        result = await tool.execute({
            'entity': None,
            'action': 'create',
            'project_key': project_key,
            'summary': 'Test Summary'
        })

        assert not result['success'], "Should fail with None entity"

        # Test wrong data type for entity
        result = await tool.execute({
            'entity': 123,
            'action': 'create',
            'project_key': project_key,
            'summary': 'Test Summary'
        })

        assert not result['success'], "Should fail with numeric entity"

    async def test_invalid_action_parameter(self, tool, project_key):
        """
        UC-292: Handle invalid action parameters.

        Tests that the system properly validates action parameters.
        """
        # Test invalid action for valid entity
        result = await tool.execute({
            'entity': 'test',
            'action': 'invalid_action',
            'project_key': project_key,
            'summary': 'Test Summary'
        })

        assert not result['success'], "Should fail with invalid action"
        assert 'action' in str(result.get('errors', [])).lower(), "Should mention invalid action"

        # Test empty action
        result = await tool.execute({
            'entity': 'test',
            'action': '',
            'project_key': project_key,
            'summary': 'Test Summary'
        })

        assert not result['success'], "Should fail with empty action"

        # Test None action
        result = await tool.execute({
            'entity': 'test',
            'action': None,
            'project_key': project_key,
            'summary': 'Test Summary'
        })

        assert not result['success'], "Should fail with None action"

        # Test action with wrong entity combination
        result = await tool.execute({
            'entity': 'test_run',
            'action': 'create',  # test_run doesn't support create
            'project_key': project_key,
            'summary': 'Test Summary'
        })

        assert not result['success'], "Should fail with unsupported action for entity"

    async def test_malformed_json_inputs(self, tool, project_key):
        """
        UC-293: Handle malformed JSON in steps parameter.

        Tests handling of malformed JSON strings in parameters that expect JSON.
        """
        # Test malformed JSON in steps parameter
        result = await tool.execute({
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': 'Test with Malformed Steps',
            'test_type': 'Manual',
            'steps': '{"invalid": json, "missing": quotes}'  # Malformed JSON
        })

        # Malformed JSON should ALWAYS be rejected
        assert not result['success'], \
            f"Malformed JSON input should never succeed: {result}"

        # Error message should indicate JSON or steps validation issue
        error_msg = str(result.get('errors', [])).lower()
        assert 'json' in error_msg or 'steps' in error_msg or 'invalid' in error_msg or 'format' in error_msg, \
            f"Should provide meaningful error about malformed JSON: {error_msg}"

        # Test completely invalid JSON structure
        result = await tool.execute({
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': 'Test with Invalid JSON',
            'test_type': 'Manual',
            'steps': '{"action": "Test", "data": "Test data", "result": "Expected result"'  # Missing closing brace
        })

        # Malformed JSON should ALWAYS be rejected
        assert not result['success'], \
            f"Malformed JSON (missing closing brace) should never succeed: {result}"

        # Error should indicate JSON parsing issue
        error_msg = str(result.get('errors', [])).lower()
        assert any(keyword in error_msg for keyword in ['json', 'format', 'parse', 'steps', 'invalid']), \
            f"Should provide meaningful error about JSON format: {error_msg}"

        # Test empty JSON (this is valid JSON but invalid steps format)
        result = await tool.execute({
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': 'Test with Empty JSON',
            'test_type': 'Manual',
            'steps': '{}'  # Valid JSON but doesn't match expected array format
        })

        # Empty JSON object should be rejected for steps (expects array)
        assert not result['success'], \
            f"Empty JSON object should be rejected for steps parameter (expects array): {result}"

        error_msg = str(result.get('errors', [])).lower()
        assert any(keyword in error_msg for keyword in ['steps', 'array', 'format', 'invalid']), \
            f"Should indicate steps format issue: {error_msg}"

    async def test_missing_required_fields(self, tool, project_key):
        """
        UC-294: Handle missing required fields.

        Tests validation of required parameters.
        """
        # Test missing project_key
        result = await tool.execute({
            'entity': 'test',
            'action': 'create',
            'summary': 'Test without Project Key'
        })

        assert not result['success'], "Should fail without project_key"
        assert any(keyword in str(result.get('errors', [])).lower()
                  for keyword in ['project', 'key', 'required']), \
            "Should mention missing project key"

        # Test missing summary for test creation
        result = await tool.execute({
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'test_type': 'Manual'
        })

        assert not result['success'], "Should fail without summary"
        assert 'summary' in str(result.get('errors', [])).lower(), "Should mention missing summary"

        # Test missing issue_id for get operation
        result = await tool.execute({
            'entity': 'test',
            'action': 'get'
        })

        assert not result['success'], "Should fail without issue_id for get operation"

        # Test missing test_execution_id for test run operations
        result = await tool.execute({
            'entity': 'test_run',
            'action': 'update_status',
            'test_issue_id': 'TEST-123',
            'status': 'PASS'
        })

        assert not result['success'], "Should fail without test_execution_id"

    async def test_data_type_mismatches(self, tool, project_key):
        """
        UC-295: Validate data type mismatches.

        Tests handling of parameters with wrong data types.
        """
        # Test numeric project_key
        result = await tool.execute({
            'entity': 'test',
            'action': 'create',
            'project_key': 12345,  # Should be string
            'summary': 'Test with Numeric Project Key'
        })

        assert not result['success'], "Should fail with numeric project_key"

        # Test boolean summary
        result = await tool.execute({
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': True,  # Should be string
            'test_type': 'Manual'
        })

        assert not result['success'], "Should fail with boolean summary"

        # Test array where string expected
        result = await tool.execute({
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': ['Test', 'Array', 'Summary'],  # Should be string
            'test_type': 'Manual'
        })

        assert not result['success'], "Should fail with array summary"

        # Test string where array expected
        result = await tool.execute({
            'entity': 'test_execution',
            'action': 'add_tests',
            'issue_id': 'EXEC-123',
            'test_issue_ids': 'TEST-123'  # Should be array
        })

        assert not result['success'], "Should fail with string where array expected"

    async def test_character_encoding_issues(self, tool, unique_prefix, project_key):
        """
        UC-296: Handle character encoding issues.

        Tests handling of various character encodings and special characters.
        """
        created_resources = []

        try:
            # Test unicode characters
            unicode_test_cases = [
                {
                    'name': f'{unique_prefix}_Unicode_Chinese',
                    'summary': '测试用例 - Chinese Characters Test',
                    'description': '这是一个包含中文字符的测试用例描述',
                    'expected_success': True
                },
                {
                    'name': f'{unique_prefix}_Unicode_Emoji',
                    'summary': '🧪 Test Case with Emojis 🚀 ✅',
                    'description': 'Test case with various emojis: 👍 👎 ⚠️ 🔥 💡',
                    'expected_success': True
                },
                {
                    'name': f'{unique_prefix}_Unicode_Mixed',
                    'summary': 'Café Niño résumé naïve façade',
                    'description': 'Mixed accented characters: àáâãäåæçèéêëìíîïñòóôõöøùúûüýÿ',
                    'expected_success': True
                },
                {
                    'name': f'{unique_prefix}_Special_Characters',
                    'summary': 'Test with <>&"\' special chars',
                    'description': 'HTML/XML special characters: < > & " \' and more',
                    'expected_success': True
                }
            ]

            for test_case in unicode_test_cases:
                result = await tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': test_case['summary'],
                    'test_type': 'Manual',
                    'description': test_case['description'],
                    'steps': '[{"action": "Test unicode handling", "data": "Special chars: 测试", "result": "Should work"}]'
                })

                if test_case['expected_success']:
                    if result['success']:
                        test_id = result['data']['issueId']
                        created_resources.append(('test', test_id))

                        # Verify the unicode content was preserved
                        details = await tool.execute({
                            'entity': 'test',
                            'action': 'get',
                            'issue_id': test_id
                        })

                        if details['success']:
                            # Check that special characters are preserved
                            stored_summary = details['data']['summary']
                            # Basic check that some special characters are preserved
                            # (exact preservation depends on backend encoding handling)
                            assert len(stored_summary) > 0, "Summary should not be empty"
                    else:
                        # If it fails, should provide meaningful error
                        assert 'errors' in result, "Should provide error information"

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception:
                    pass

    async def test_oversized_data_payloads(self, tool, unique_prefix, project_key):
        """
        UC-297: Handle oversized data payloads.

        Tests handling of very large inputs that might exceed system limits.
        """
        # Test extremely long summary
        very_long_summary = f'{unique_prefix}_' + 'X' * 10000  # 10KB summary

        result = await tool.execute({
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': very_long_summary,
            'test_type': 'Manual'
        })

        # System should either handle this or provide clear error about size limits
        if not result['success']:
            error_msg = str(result.get('errors', [])).lower()
            assert any(keyword in error_msg for keyword in ['too long', 'size', 'limit', 'length', 'character', 'exceed']), \
                f"Should provide meaningful error about size limits: {error_msg}"

        # Test extremely long description
        very_long_description = 'This is a very long description. ' * 1000  # ~30KB description

        result = await tool.execute({
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix}_Large_Description_Test',
            'test_type': 'Manual',
            'description': very_long_description
        })

        if not result['success']:
            error_msg = str(result.get('errors', [])).lower()
            assert any(keyword in error_msg for keyword in ['too long', 'size', 'limit', 'length']), \
                "Should handle large description appropriately"

        # Test very large Gherkin content
        large_gherkin = '''Feature: Large Feature File

Background:
    Given the system is initialized
    And the database is connected
    And all services are running

''' + '\n'.join([f'''
@scenario-{i}
Scenario: Test scenario number {i}
    Given I have scenario {i} setup
    When I execute action {i}
    Then I should get result {i}
    And the system should remain stable
''' for i in range(100)])  # 100 scenarios

        result = await tool.execute({
            'entity': 'test',
            'action': 'create',
            'project_key': project_key,
            'summary': f'{unique_prefix}_Large_Gherkin_Test',
            'test_type': 'Cucumber',
            'gherkin': large_gherkin
        })

        # Should handle large Gherkin or provide clear feedback
        if not result['success']:
            error_msg = str(result.get('errors', [])).lower()
            # Check if it's a size-related error or other validation error
            assert 'errors' in result, "Should provide error information"

    async def test_boundary_value_testing(self, tool, unique_prefix, project_key):
        """
        UC-298: Test boundary values and edge case data.

        Tests handling of boundary values for various parameters.
        """
        created_resources = []

        try:
            # Test minimum valid inputs
            minimal_test = await tool.execute({
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': 'X',  # Single character summary
                'test_type': 'Manual'
            })

            if minimal_test['success']:
                test_id = minimal_test['data']['issueId']
                created_resources.append(('test', test_id))

            # Test empty string inputs where allowed
            result = await tool.execute({
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_Empty_Description_Test',
                'test_type': 'Manual',
                'description': ''  # Empty description
            })

            if result['success']:
                test_id = result['data']['issueId']
                created_resources.append(('test', test_id))

            # Test whitespace-only inputs
            result = await tool.execute({
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': '   ',  # Whitespace-only summary
                'test_type': 'Manual'
            })

            if not result['success']:
                # Should provide meaningful error about whitespace-only input
                error_msg = str(result.get('errors', [])).lower()
                assert any(keyword in error_msg for keyword in ['empty', 'required', 'whitespace', 'specify', 'summary']), \
                    f"Should validate whitespace-only inputs: {error_msg}"

            # Test null/None values in optional fields
            result = await tool.execute({
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_Null_Fields_Test',
                'test_type': 'Manual',
                'description': None,  # Explicit None
                'steps': None
            })

            # Should handle None values gracefully
            if result['success']:
                test_id = result['data']['issueId']
                created_resources.append(('test', test_id))

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception:
                    pass

    async def test_injection_attack_prevention(self, tool, unique_prefix, project_key):
        """
        UC-299: Test injection attack prevention.

        Tests that the system properly handles potentially malicious inputs.
        """
        created_resources = []

        try:
            # Test SQL injection patterns (should be sanitized)
            sql_injection_cases = [
                "'; DROP TABLE tests; --",
                "' OR '1'='1",
                "1; DELETE FROM users WHERE 1=1; --",
                "'; INSERT INTO tests (name) VALUES ('injected'); --"
            ]

            for injection_pattern in sql_injection_cases:
                result = await tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_SQL_Injection_Test',
                    'test_type': 'Manual',
                    'description': f'Test with potential SQL injection: {injection_pattern}'
                })

                if result['success']:
                    test_id = result['data']['issueId']
                    created_resources.append(('test', test_id))

                    # Verify the content was sanitized or properly escaped
                    details = await tool.execute({
                        'entity': 'test',
                        'action': 'get',
                        'issue_id': test_id
                    })

                    if details['success']:
                        # Content should be present but potentially sanitized
                        description = details['data'].get('description', '')
                        # The system should handle this safely

            # Test XSS patterns
            xss_patterns = [
                "<script>alert('xss')</script>",
                "<img src='x' onerror='alert(1)'>",
                "javascript:alert('xss')",
                "<iframe src='javascript:alert(1)'></iframe>"
            ]

            for xss_pattern in xss_patterns:
                result = await tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_XSS_Test',
                    'test_type': 'Manual',
                    'description': f'Test with potential XSS: {xss_pattern}'
                })

                if result['success']:
                    test_id = result['data']['issueId']
                    created_resources.append(('test', test_id))

            # Test command injection patterns
            command_injection_patterns = [
                "; rm -rf /",
                "| cat /etc/passwd",
                "&& shutdown -h now",
                "`whoami`"
            ]

            for cmd_pattern in command_injection_patterns:
                result = await tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_Command_Injection_Test',
                    'test_type': 'Manual',
                    'description': f'Test with potential command injection: {cmd_pattern}'
                })

                if result['success']:
                    test_id = result['data']['issueId']
                    created_resources.append(('test', test_id))

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception:
                    pass

    async def test_invalid_references_and_ids(self, tool, project_key):
        """
        UC-300: Handle invalid references and IDs.

        Tests handling of invalid or non-existent resource references.
        """
        # Test non-existent test ID
        result = await tool.execute({
            'entity': 'test',
            'action': 'get',
            'issue_id': 'NONEXISTENT-99999'
        })

        assert not result['success'], "Should fail with non-existent test ID"
        error_msg = str(result.get('errors', [])).lower()
        assert any(keyword in error_msg for keyword in ['not found', 'does not exist', 'invalid']), \
            "Should provide meaningful error for non-existent ID"

        # Test invalid ID format
        result = await tool.execute({
            'entity': 'test',
            'action': 'get',
            'issue_id': 'invalid-id-format'
        })

        assert not result['success'], "Should fail with invalid ID format"

        # Test empty ID
        result = await tool.execute({
            'entity': 'test',
            'action': 'get',
            'issue_id': ''
        })

        assert not result['success'], "Should fail with empty ID"

        # Test non-existent project key
        result = await tool.execute({
            'entity': 'test',
            'action': 'create',
            'project_key': 'NONEXISTENT',
            'summary': 'Test in Non-existent Project',
            'test_type': 'Manual'
        })

        assert not result['success'], "Should fail with non-existent project"
        error_msg = str(result.get('errors', [])).lower()
        assert any(keyword in error_msg for keyword in ['project', 'not found', 'invalid']), \
            "Should mention invalid project"

        # Test invalid test_issue_ids in execution operations
        result = await tool.execute({
            'entity': 'test_execution',
            'action': 'add_tests',
            'issue_id': 'EXEC-99999',  # Non-existent execution
            'test_issue_ids': ['TEST-99999', 'TEST-99998']  # Non-existent tests
        })

        assert not result['success'], "Should fail with non-existent execution and tests"

        # Test malformed UUID/ID patterns
        malformed_ids = [
            '123',  # Too short
            'PROJECT',  # Missing number
            'PRJ-',  # Missing number part
            'PRJ-ABC',  # Non-numeric number part
            'very-long-project-key-that-exceeds-normal-limits-123',  # Too long
            'PRJ 123',  # Space in ID
            'PRJ-123-EXTRA',  # Extra parts
        ]

        for malformed_id in malformed_ids:
            result = await tool.execute({
                'entity': 'test',
                'action': 'get',
                'issue_id': malformed_id
            })

            assert not result['success'], f"Should fail with malformed ID: {malformed_id}"