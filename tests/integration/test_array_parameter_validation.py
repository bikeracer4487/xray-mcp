"""Test array parameter validation for Xray MCP server operations.

This test suite validates the critical QA fix for array parameter validation,
ensuring that arrays of IDs are properly validated with helpful error messages.
"""

import os
import json
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from src.server import create_server
from tests.integration.test_helpers import parse_mcp_response

# Load environment for authentication
load_dotenv()

@pytest.mark.skipif(
    not all([os.getenv('XRAY_CLIENT_ID'), os.getenv('XRAY_CLIENT_SECRET')]),
    reason="Xray credentials not available"
)
class TestArrayParameterValidation:
    """Test array parameter validation and error messaging."""

    @pytest_asyncio.fixture
    async def server(self):
        """Create MCP server instance."""
        return create_server()

    @pytest_asyncio.fixture
    async def tool(self, server):
        """Get the xray_test tool."""
        tools = await server.get_tools()
        return tools['xray_test']

    # ========================================
    # Test Execution Array Validation Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_execution_create_valid_numeric_test_ids(self, tool):
        """Test creating execution with valid numeric test IDs array."""
        params = {
            'entity': 'test_execution',
            'action': 'create',
            'project_key': 'FTEST',
            'summary': 'Array validation test execution',
            'test_issue_ids': ['1192649', '1192650']  # Valid numeric IDs
        }

        result = await tool.run(params)
        data = parse_mcp_response(result)

        # Should succeed or fail for non-validation reasons
        if not data['success']:
            # If it fails, should not be due to array validation
            error_text = ' '.join(data['errors']).lower()
            assert 'jira keys' not in error_text
            assert 'invalid ids in array' not in error_text

    @pytest.mark.asyncio
    async def test_execution_create_invalid_jira_keys_array(self, tool):
        """Test creating execution with JIRA keys fails with helpful error."""
        params = {
            'entity': 'test_execution',
            'action': 'create',
            'project_key': 'FTEST',
            'summary': 'Invalid array test execution',
            'test_issue_ids': ['FTEST-1590', 'FTEST-1591']  # Invalid JIRA keys
        }

        result = await tool.run(params)
        data = parse_mcp_response(result)

        assert not data['success'], "Should fail with JIRA keys in array"
        error_text = ' '.join(data['errors'])

        # Should contain helpful error message
        assert 'Invalid test_issue_ids' in error_text
        assert 'JIRA keys found' in error_text
        assert 'FTEST-1590' in error_text
        assert 'Use list operations' in error_text

    @pytest.mark.asyncio
    async def test_execution_create_mixed_valid_invalid_array(self, tool):
        """Test creating execution with mixed valid/invalid IDs."""
        params = {
            'entity': 'test_execution',
            'action': 'create',
            'project_key': 'FTEST',
            'summary': 'Mixed array test execution',
            'test_issue_ids': ['1192649', 'FTEST-1590', '1192650']  # Mixed valid/invalid
        }

        result = await tool.run(params)
        data = parse_mcp_response(result)

        assert not data['success'], "Should fail with mixed array"
        error_text = ' '.join(data['errors'])

        # Should identify the problem IDs and valid ones
        assert 'Invalid test_issue_ids' in error_text
        assert '1/3 invalid' in error_text or '1 invalid' in error_text
        assert 'FTEST-1590' in error_text
        assert 'Valid IDs: [\'1192649\', \'1192650\']' in error_text

    @pytest.mark.asyncio
    async def test_execution_create_empty_array(self, tool):
        """Test creating execution with empty test_issue_ids array."""
        params = {
            'entity': 'test_execution',
            'action': 'create',
            'project_key': 'FTEST',
            'summary': 'Empty array test execution',
            'test_issue_ids': []  # Empty array
        }

        result = await tool.run(params)
        data = parse_mcp_response(result)

        # Should succeed (empty arrays are valid for creation)
        # If it fails, should not be due to array validation
        if not data['success']:
            error_text = ' '.join(data['errors']).lower()
            assert 'issue id array is empty' not in error_text

    @pytest.mark.asyncio
    async def test_execution_add_tests_non_array_parameter(self, tool):
        """Test add_tests with non-array test_issue_ids parameter."""
        params = {
            'entity': 'test_execution',
            'action': 'add_tests',
            'issue_id': '1192649',
            'test_issue_ids': 'not_an_array'  # String instead of array
        }

        result = await tool.run(params)
        data = parse_mcp_response(result)

        assert not data['success'], "Should fail with non-array parameter"
        error_text = ' '.join(data['errors'])

        assert 'must be provided as a list' in error_text
        assert 'got str' in error_text

    @pytest.mark.asyncio
    async def test_execution_add_tests_with_invalid_execution_id(self, tool):
        """Test add_tests with invalid execution ID format."""
        params = {
            'entity': 'test_execution',
            'action': 'add_tests',
            'issue_id': 'FTEST-1590',  # JIRA key instead of numeric ID
            'test_issue_ids': ['1192649', '1192650']
        }

        result = await tool.run(params)
        data = parse_mcp_response(result)

        assert not data['success'], "Should fail with JIRA key execution ID"
        error_text = ' '.join(data['errors'])

        # Should identify the execution ID format issue
        assert 'Invalid execution issue_id' in error_text
        assert 'JIRA keys' in error_text
        assert 'FTEST-1590' in error_text

    # ========================================
    # Test Plan Array Validation Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_plan_add_tests_valid_array(self, tool):
        """Test adding tests to plan with valid numeric IDs."""
        params = {
            'entity': 'test_plan',
            'action': 'add_tests',
            'issue_id': '1192649',
            'test_issue_ids': ['1192650', '1192651']
        }

        result = await tool.run(params)
        data = parse_mcp_response(result)

        # Should succeed or fail for non-validation reasons
        if not data['success']:
            error_text = ' '.join(data['errors']).lower()
            assert 'jira keys' not in error_text
            assert 'invalid test_issue_ids' not in error_text

    @pytest.mark.asyncio
    async def test_plan_add_executions_invalid_array(self, tool):
        """Test adding executions to plan with invalid execution IDs."""
        params = {
            'entity': 'test_plan',
            'action': 'add_executions',
            'issue_id': '1192649',
            'test_exec_issue_ids': ['FTEST-EXE-123', 'FTEST-EXE-124']  # Invalid JIRA keys
        }

        result = await tool.run(params)
        data = parse_mcp_response(result)

        assert not data['success'], "Should fail with JIRA key execution IDs"
        error_text = ' '.join(data['errors'])

        assert 'Invalid test_exec_issue_ids' in error_text
        assert 'JIRA keys found' in error_text
        assert 'FTEST-EXE-123' in error_text

    @pytest.mark.asyncio
    async def test_plan_remove_executions_mixed_array(self, tool):
        """Test removing executions from plan with mixed valid/invalid IDs."""
        params = {
            'entity': 'test_plan',
            'action': 'remove_executions',
            'issue_id': '1192649',
            'test_exec_issue_ids': ['1192700', 'FTEST-EXE-123', '1192701']
        }

        result = await tool.run(params)
        data = parse_mcp_response(result)

        assert not data['success'], "Should fail with mixed execution IDs"
        error_text = ' '.join(data['errors'])

        assert 'Invalid test_exec_issue_ids' in error_text
        assert '1/3 invalid' in error_text or '1 invalid' in error_text
        assert 'FTEST-EXE-123' in error_text

    # ========================================
    # Array Validation Utility Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_array_validation_with_non_string_items(self, tool):
        """Test array validation with non-string items in array."""
        params = {
            'entity': 'test_execution',
            'action': 'create',
            'project_key': 'FTEST',
            'summary': 'Non-string items test',
            'test_issue_ids': ['1192649', 123, None, '1192650']  # Mixed types
        }

        result = await tool.run(params)
        data = parse_mcp_response(result)

        assert not data['success'], "Should fail with non-string items"
        error_text = ' '.join(data['errors'])

        assert 'Invalid test_issue_ids' in error_text
        assert 'Issue ID must be a string' in error_text

    @pytest.mark.asyncio
    async def test_comprehensive_array_error_messaging(self, tool):
        """Test that array validation provides comprehensive error messages."""
        params = {
            'entity': 'test_execution',
            'action': 'create',
            'project_key': 'FTEST',
            'summary': 'Comprehensive error test',
            'test_issue_ids': [
                '1192649',         # Valid
                'FTEST-1590',      # JIRA key
                'invalid-format',  # Unknown format
                123,               # Wrong type
                '1192650'          # Valid
            ]
        }

        result = await tool.run(params)
        data = parse_mcp_response(result)

        assert not data['success'], "Should fail with multiple validation issues"
        error_text = ' '.join(data['errors'])

        # Should mention all types of issues
        assert 'Invalid test_issue_ids' in error_text
        assert '3/5 invalid' in error_text or '3 invalid' in error_text
        assert 'JIRA keys found' in error_text
        assert 'FTEST-1590' in error_text
        assert 'Invalid formats' in error_text
        assert 'invalid-format' in error_text
        assert 'Valid IDs: [\'1192649\', \'1192650\']' in error_text

    # ========================================
    # Cross-Entity Validation Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_different_entity_types_array_validation(self, tool):
        """Test array validation works consistently across entity types."""
        test_cases = [
            {
                'entity': 'test_execution',
                'action': 'create',
                'project_key': 'FTEST',
                'summary': 'Cross-entity test',
                'test_issue_ids': ['FTEST-1590'],
                'expected_error': 'Invalid test_issue_ids'
            },
            {
                'entity': 'test_plan',
                'action': 'add_tests',
                'issue_id': '1192649',
                'test_issue_ids': ['FTEST-1590'],
                'expected_error': 'Invalid test_issue_ids'
            },
            {
                'entity': 'test_plan',
                'action': 'add_executions',
                'issue_id': '1192649',
                'test_exec_issue_ids': ['FTEST-EXE-123'],
                'expected_error': 'Invalid test_exec_issue_ids'
            }
        ]

        for case in test_cases:
            result = await tool.run(case)
            data = parse_mcp_response(result)

            assert not data['success'], f"Should fail for {case['entity']}.{case['action']}"
            error_text = ' '.join(data['errors'])
            assert case['expected_error'] in error_text
            assert 'JIRA keys' in error_text

    # ========================================
    # Edge Case Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_very_large_array_validation(self, tool):
        """Test validation performance with large arrays."""
        # Create array with 50 items (mix of valid and invalid)
        large_array = []
        for i in range(25):
            large_array.append(f'119{2649 + i}')  # Valid numeric IDs
            large_array.append(f'FTEST-{1590 + i}')  # Invalid JIRA keys

        params = {
            'entity': 'test_execution',
            'action': 'create',
            'project_key': 'FTEST',
            'summary': 'Large array test',
            'test_issue_ids': large_array
        }

        result = await tool.run(params)
        data = parse_mcp_response(result)

        assert not data['success'], "Should fail with large mixed array"
        error_text = ' '.join(data['errors'])

        assert 'Invalid test_issue_ids' in error_text
        assert '25/50 invalid' in error_text or '25 invalid' in error_text
        assert 'JIRA keys found' in error_text

    @pytest.mark.asyncio
    async def test_array_validation_performance_timing(self, tool):
        """Test that array validation doesn't add significant performance overhead."""
        import time

        # Test with moderately sized valid array
        valid_array = [f'119{2649 + i}' for i in range(20)]

        params = {
            'entity': 'test_execution',
            'action': 'create',
            'project_key': 'FTEST',
            'summary': 'Performance timing test',
            'test_issue_ids': valid_array
        }

        start_time = time.time()
        result = await tool.run(params)
        end_time = time.time()

        # Validation should complete quickly (under 1 second for 20 items)
        validation_time = end_time - start_time
        assert validation_time < 1.0, f"Array validation took too long: {validation_time}s"

    @pytest.mark.asyncio
    async def test_array_validation_error_format_consistency(self, tool):
        """Test that all array validation errors follow consistent format."""
        test_cases = [
            {
                'entity': 'test_execution',
                'action': 'create',
                'project_key': 'FTEST',
                'summary': 'Format test 1',
                'test_issue_ids': ['FTEST-1590']
            },
            {
                'entity': 'test_plan',
                'action': 'add_tests',
                'issue_id': '1192649',
                'test_issue_ids': ['FTEST-1590']
            },
            {
                'entity': 'test_execution',
                'action': 'add_tests',
                'issue_id': '1192649',
                'test_issue_ids': ['FTEST-1590']
            }
        ]

        for case in test_cases:
            result = await tool.run(case)
            data = parse_mcp_response(result)

            # All responses should have consistent structure
            assert 'success' in data
            assert 'errors' in data
            assert 'data' in data
            assert 'warnings' in data

            assert not data['success']
            assert isinstance(data['errors'], list)
            assert len(data['errors']) > 0

            # Error messages should be helpful and consistent
            error_text = ' '.join(data['errors'])
            assert 'Invalid' in error_text
            assert 'JIRA keys' in error_text
            assert 'Use list operations' in error_text or 'numeric' in error_text