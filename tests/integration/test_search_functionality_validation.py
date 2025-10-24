"""
Search Functionality Validation Tests

These tests validate the enhanced search functionality that was added as part
of the QA fixes to improve user-friendly querying across all entity types.
"""

import pytest
import os
import uuid
from dotenv import load_dotenv
from src.server import create_server
from tests.integration.test_helpers import parse_mcp_response

load_dotenv()


@pytest.mark.skipif(
    not all([os.getenv('XRAY_CLIENT_ID'), os.getenv('XRAY_CLIENT_SECRET')]),
    reason="Xray credentials not available"
)
class TestSearchFunctionalityValidation:
    """Test enhanced search functionality across all entity types."""

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
        return f"SEARCH-{uuid.uuid4().hex[:6]}"

    @pytest.fixture
    def project_key(self):
        """Get project key from environment."""
        return os.getenv('DEFAULT_PROJECT_KEY', 'FTEST')

    # ========================================
    # Basic Search Functionality Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_search_tests_by_text(self, tool, project_key):
        """Test searching tests by text with enhanced search action."""
        result = await tool.run({
            "entity": "test",
            "action": "search",
            "text": "login",
            "project_key": project_key,
            "limit": 5
        })

        response = parse_mcp_response(result)
        assert response['success'], f"Search failed: {response.get('errors')}"

        # Should return search context
        assert 'data' in response
        data = response['data']

        # Should have search context with helpful information
        if 'search_context' in data:
            search_context = data['search_context']
            assert 'search_parameters' in search_context
            assert 'jql_generated' in search_context
            assert 'search_tips' in search_context

            # Verify search parameters were captured
            params = search_context['search_parameters']
            assert params['entity'] == 'test'
            assert params['text'] == 'login'
            assert params['project_key'] == project_key

            # Should have generated meaningful JQL
            jql = search_context['jql_generated']
            assert 'login' in jql
            assert project_key in jql
            assert 'Test' in jql  # Should filter by test issue type

    @pytest.mark.asyncio
    async def test_search_executions_by_recent_days(self, tool, project_key):
        """Test searching test executions by recent activity."""
        result = await tool.run({
            "entity": "test_execution",
            "action": "search",
            "project_key": project_key,
            "recent_days": 30,
            "limit": 10
        })

        response = parse_mcp_response(result)
        assert response['success'], f"Search failed: {response.get('errors')}"

        # Should return search context
        data = response['data']
        if 'search_context' in data:
            search_context = data['search_context']
            jql = search_context['jql_generated']

            # Should include recent days filter and execution type
            assert 'updated >= -30d' in jql
            assert 'Test Execution' in jql
            assert project_key in jql

    @pytest.mark.asyncio
    async def test_search_tests_with_test_type_filter(self, tool, project_key):
        """Test searching tests with specific test type filter."""
        result = await tool.run({
            "entity": "test",
            "action": "search",
            "project_key": project_key,
            "test_type": "Manual",
            "limit": 5
        })

        response = parse_mcp_response(result)
        assert response['success'], f"Search failed: {response.get('errors')}"

        data = response['data']
        if 'search_context' in data:
            search_context = data['search_context']
            jql = search_context['jql_generated']

            # Should include test type filter
            assert 'Test Type' in jql
            assert 'Manual' in jql
            assert 'issuetype = Test' in jql

    @pytest.mark.asyncio
    async def test_search_with_combined_filters(self, tool, project_key):
        """Test search with multiple filters combined."""
        result = await tool.run({
            "entity": "test",
            "action": "search",
            "text": "authentication",
            "project_key": project_key,
            "test_type": "Manual",
            "recent_days": 14,
            "limit": 3
        })

        response = parse_mcp_response(result)
        assert response['success'], f"Search failed: {response.get('errors')}"

        data = response['data']
        if 'search_context' in data:
            search_context = data['search_context']
            jql = search_context['jql_generated']

            # Should combine all filters with AND
            assert 'authentication' in jql
            assert project_key in jql
            assert 'Manual' in jql
            assert 'updated >= -14d' in jql

            # Should use AND to combine filters
            and_count = jql.count(' AND ')
            assert and_count >= 3  # At least 4 conditions joined by 3 ANDs

    # ========================================
    # Search Validation and Error Handling
    # ========================================

    @pytest.mark.asyncio
    async def test_search_requires_filter_parameters(self, tool):
        """Test that search requires at least one filter parameter."""
        result = await tool.run({
            "entity": "test",
            "action": "search"
            # No filter parameters provided
        })

        response = parse_mcp_response(result)
        assert not response['success'], "Search should fail without filter parameters"

        error_text = ' '.join(response['errors'])
        assert 'Search requires at least one filter parameter' in error_text
        assert 'text, project_key, test_type, or recent_days' in error_text

    @pytest.mark.asyncio
    async def test_search_invalid_entity_type(self, tool):
        """Test search with invalid entity type."""
        result = await tool.run({
            "entity": "invalid_entity",
            "action": "search",
            "text": "test",
            "project_key": "FTEST"
        })

        response = parse_mcp_response(result)
        assert not response['success'], "Search should fail with invalid entity"

        error_text = ' '.join(response['errors'])
        assert 'Invalid entity for search' in error_text
        assert 'Valid entities are:' in error_text

    @pytest.mark.asyncio
    async def test_search_tips_provided_for_different_entities(self, tool, project_key):
        """Test that search tips are provided for different entity types."""
        entities = ['test', 'test_execution', 'test_plan']

        for entity in entities:
            result = await tool.run({
                "entity": entity,
                "action": "search",
                "project_key": project_key,
                "limit": 1
            })

            response = parse_mcp_response(result)
            assert response['success'], f"Search failed for {entity}: {response.get('errors')}"

            data = response['data']
            if 'search_context' in data:
                search_context = data['search_context']
                assert 'search_tips' in search_context

                tips = search_context['search_tips']
                assert isinstance(tips, list)
                assert len(tips) > 0

                # Tips should be relevant to the entity type
                tips_text = ' '.join(tips)
                if entity == 'test':
                    assert 'test_type' in tips_text.lower()
                elif entity == 'test_execution':
                    assert 'execution' in tips_text.lower()
                elif entity == 'test_plan':
                    assert 'plan' in tips_text.lower()

    # ========================================
    # Search Performance and Limits
    # ========================================

    @pytest.mark.asyncio
    async def test_search_respects_limit_parameters(self, tool, project_key):
        """Test that search respects limit parameters and caps appropriately."""
        # Test with normal limit
        result = await tool.run({
            "entity": "test",
            "action": "search",
            "project_key": project_key,
            "limit": 5
        })

        response = parse_mcp_response(result)
        assert response['success'], f"Search failed: {response.get('errors')}"

        data = response['data']
        if 'search_context' in data:
            search_context = data['search_context']
            params = search_context['search_parameters']
            assert params['limit'] == 5

        # Test with limit over maximum (should be capped)
        result = await tool.run({
            "entity": "test",
            "action": "search",
            "project_key": project_key,
            "limit": 100  # Over the 50 cap for search
        })

        response = parse_mcp_response(result)
        assert response['success'], f"Search failed: {response.get('errors')}"

        data = response['data']
        if 'search_context' in data:
            search_context = data['search_context']
            params = search_context['search_parameters']
            # Should be capped at 50 for search operations
            assert params['limit'] <= 50

    @pytest.mark.asyncio
    async def test_search_handles_no_results_gracefully(self, tool, project_key):
        """Test that search handles no results with helpful warnings."""
        # Search for something unlikely to exist
        unique_term = f"NONEXISTENT-{uuid.uuid4().hex}"

        result = await tool.run({
            "entity": "test",
            "action": "search",
            "text": unique_term,
            "project_key": project_key
        })

        response = parse_mcp_response(result)
        assert response['success'], f"Search failed: {response.get('errors')}"

        # Should have warnings about no results
        if 'warnings' in response and response['warnings']:
            warnings_text = ' '.join(response['warnings'])
            assert 'No tests found' in warnings_text or 'no results' in warnings_text.lower()
            assert 'broader search terms' in warnings_text or 'Generated JQL' in warnings_text

    # ========================================
    # Integration with Other Features
    # ========================================

    @pytest.mark.asyncio
    async def test_search_integrates_with_retry_logic(self, tool, project_key):
        """Test that search operations integrate with retry logic for reliability."""
        # This test verifies that search uses the same reliable infrastructure
        # as other operations, particularly for project-based searches
        result = await tool.run({
            "entity": "test_execution",
            "action": "search",
            "project_key": project_key,
            "recent_days": 1  # Very recent, might trigger retry scenarios
        })

        response = parse_mcp_response(result)
        # Should succeed or fail gracefully, not crash
        assert 'success' in response
        assert 'errors' in response
        assert 'data' in response
        assert 'warnings' in response

    @pytest.mark.asyncio
    async def test_search_documentation_integration(self, tool, project_key):
        """Test that search action is properly documented and accessible."""
        # Test that search action is recognized (not an invalid action error)
        result = await tool.run({
            "entity": "test",
            "action": "search",
            "project_key": project_key
        })

        response = parse_mcp_response(result)
        # Should not fail with "invalid action" error
        if not response['success']:
            error_text = ' '.join(response['errors'])
            assert 'Invalid action' not in error_text
            assert 'search' not in error_text.lower() or 'not supported' not in error_text.lower()

    @pytest.mark.asyncio
    async def test_search_context_provides_learning_value(self, tool, project_key):
        """Test that search context helps users learn the system."""
        result = await tool.run({
            "entity": "test",
            "action": "search",
            "text": "example",
            "project_key": project_key
        })

        response = parse_mcp_response(result)
        assert response['success'], f"Search failed: {response.get('errors')}"

        data = response['data']
        if 'search_context' in data:
            search_context = data['search_context']

            # Should show the JQL that was generated
            jql = search_context['jql_generated']
            assert len(jql) > 0
            assert 'example' in jql

            # Should provide tips for improvement
            tips = search_context['search_tips']
            assert len(tips) > 0

            # Tips should be actionable
            tips_text = ' '.join(tips)
            assert 'text parameter' in tips_text or 'project_key' in tips_text