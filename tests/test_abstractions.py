"""Tests for the abstraction layer.

This module tests the abstraction components and demonstrates how they
improve testability by allowing easy mocking and isolation of components.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Test imports
try:
    from abstractions import (
        BaseTool,
        Repository,
        GraphQLRepository,
        CachedRepository,
        tool_error_handler,
        validate_required,
        ToolFactory,
    )
    from abstractions.repository import Repository
    from exceptions import ValidationError, GraphQLError
except ImportError:
    import sys

    sys.path.append("..")
    from abstractions import (
        BaseTool,
        Repository,
        GraphQLRepository,
        CachedRepository,
        tool_error_handler,
        validate_required,
        ToolFactory,
    )
    from abstractions.repository import Repository
    from exceptions import ValidationError, GraphQLError


class MockRepository(Repository):
    """Mock repository for testing."""

    def __init__(self):
        self.queries = []
        self.mutations = []
        self.responses = {}

    async def execute_query(
        self, query: str, variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record query and return mock response."""
        self.queries.append((query, variables))

        # Return configured response or default
        def make_hashable(obj):
            if isinstance(obj, dict):
                return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
            elif isinstance(obj, list):
                return tuple(make_hashable(item) for item in obj)
            else:
                return obj

        key = (query.strip()[:50], make_hashable(variables))
        return self.responses.get(key, {"data": "mock"})

    async def execute_mutation(
        self, mutation: str, variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record mutation and return mock response."""
        self.mutations.append((mutation, variables))

        # Return configured response or default
        def make_hashable(obj):
            if isinstance(obj, dict):
                return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
            elif isinstance(obj, list):
                return tuple(make_hashable(item) for item in obj)
            else:
                return obj

        key = (mutation.strip()[:50], make_hashable(variables))
        return self.responses.get(key, {"success": True})

    def set_response(
        self, query_prefix: str, variables: Dict[str, Any], response: Dict[str, Any]
    ):
        """Configure a response for a specific query/variables combination."""

        # Convert nested dicts to tuples for hashability
        def make_hashable(obj):
            if isinstance(obj, dict):
                return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
            elif isinstance(obj, list):
                return tuple(make_hashable(item) for item in obj)
            else:
                return obj

        key = (query_prefix.strip()[:50], make_hashable(variables))
        self.responses[key] = response


class SampleTool(BaseTool):
    """Sample tool for testing."""

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool."""
        action = kwargs.get("action", "default")

        if action == "query":
            return await self.repository.execute_query(
                "query { test }", {"id": kwargs.get("id", "1")}
            )
        elif action == "mutate":
            return await self.repository.execute_mutation(
                "mutation { create }", {"data": kwargs.get("data", {})}
            )
        elif action == "error":
            raise ValueError("Test error")

        return {"action": action}

    @tool_error_handler
    async def safe_method(self, should_fail: bool = False) -> Dict[str, Any]:
        """Method with error handling decorator."""
        if should_fail:
            raise RuntimeError("Intentional failure")
        return {"status": "success"}

    @validate_required("required_param")
    async def validated_method(
        self, required_param: str, optional_param: str = None
    ) -> Dict[str, Any]:
        """Method with validation decorator."""
        return {"required": required_param, "optional": optional_param}


class TestBaseTool:
    """Test the BaseTool abstraction."""

    @pytest.fixture
    def mock_repo(self):
        """Create a mock repository."""
        return MockRepository()

    @pytest.fixture
    def sample_tool(self, mock_repo):
        """Create a sample tool with mock repository."""
        return SampleTool(mock_repo)

    @pytest.mark.asyncio
    async def test_tool_initialization(self, sample_tool):
        """Test that tools are properly initialized."""
        assert sample_tool.name == "SampleTool"
        assert sample_tool.description.startswith("Sample tool")
        assert isinstance(sample_tool.repository, MockRepository)

    @pytest.mark.asyncio
    async def test_tool_execute_query(self, sample_tool, mock_repo):
        """Test that tools can execute queries through repository."""
        # Configure expected response
        mock_repo.set_response("query { test }", {"id": "123"}, {"result": "test data"})

        # Execute tool
        result = await sample_tool(action="query", id="123")

        # Verify query was made
        assert len(mock_repo.queries) == 1
        query, variables = mock_repo.queries[0]
        assert "query { test }" in query
        assert variables["id"] == "123"

        # Verify result
        assert result == {"result": "test data"}

    @pytest.mark.asyncio
    async def test_tool_execute_mutation(self, sample_tool, mock_repo):
        """Test that tools can execute mutations through repository."""
        # Execute tool
        result = await sample_tool(action="mutate", data={"name": "test"})

        # Verify mutation was made
        assert len(mock_repo.mutations) == 1
        mutation, variables = mock_repo.mutations[0]
        assert "mutation { create }" in mutation
        assert variables["data"] == {"name": "test"}

    @pytest.mark.asyncio
    async def test_tool_validation(self, sample_tool):
        """Test that input validation works."""
        # Default validation does nothing
        await sample_tool.validate_input(test="data")

        # Subclasses can override to add validation
        class ValidatedTool(SampleTool):
            async def validate_input(self, **kwargs):
                if "invalid" in kwargs:
                    raise ValidationError("Invalid parameter detected")

        validated = ValidatedTool(MockRepository())

        # Valid input should pass
        await validated(action="default")

        # Invalid input should raise
        with pytest.raises(ValidationError, match="Invalid parameter detected"):
            await validated(invalid=True)


class TestDecorators:
    """Test the decorator functions."""

    @pytest.mark.asyncio
    async def test_tool_error_handler(self):
        """Test that error handler decorator catches and formats errors."""
        tool = SampleTool(MockRepository())

        # Success case
        result = await tool.safe_method(should_fail=False)
        assert result["status"] == "success"

        # Error case
        result = await tool.safe_method(should_fail=True)
        assert "error" in result
        assert result["error"] == "Intentional failure"
        assert result["type"] == "RuntimeError"
        assert result["function"] == "safe_method"

    @pytest.mark.asyncio
    async def test_validate_required(self):
        """Test that required parameter validation works."""
        tool = SampleTool(MockRepository())

        # Valid call with required parameter
        result = await tool.validated_method(required_param="test")
        assert result["required"] == "test"
        assert result["optional"] is None

        # Valid call with both parameters
        result = await tool.validated_method(
            required_param="test", optional_param="optional"
        )
        assert result["required"] == "test"
        assert result["optional"] == "optional"

        # Invalid call missing required parameter
        with pytest.raises(
            ValidationError, match="Missing required parameters: required_param"
        ):
            await tool.validated_method(optional_param="only optional")


class TestRepository:
    """Test the repository implementations."""

    @pytest.mark.asyncio
    async def test_graphql_repository(self):
        """Test that GraphQL repository delegates to client."""
        # Mock GraphQL client
        mock_client = AsyncMock()
        mock_client.execute_query.return_value = {"data": "result"}

        # Create repository
        repo = GraphQLRepository(mock_client)

        # Execute query
        result = await repo.execute_query("query", {"var": "value"})

        # Verify delegation
        mock_client.execute_query.assert_called_once_with("query", {"var": "value"})
        assert result == {"data": "result"}

    @pytest.mark.asyncio
    async def test_cached_repository(self):
        """Test that cached repository caches query results."""
        # Create base repository
        base_repo = MockRepository()
        base_repo.set_response("query { test }", {}, {"count": 1})

        # Create cached repository with short TTL for testing
        cached_repo = CachedRepository(base_repo, cache_ttl=1)

        # First call should hit base repository
        result1 = await cached_repo.execute_query("query { test }", {})
        assert result1 == {"count": 1}
        assert len(base_repo.queries) == 1

        # Second call should use cache
        result2 = await cached_repo.execute_query("query { test }", {})
        assert result2 == {"count": 1}
        assert len(base_repo.queries) == 1  # No new query

        # Wait for cache to expire
        import asyncio

        await asyncio.sleep(1.1)

        # Third call should hit base repository again
        base_repo.set_response("query { test }", {}, {"count": 2})
        result3 = await cached_repo.execute_query("query { test }", {})
        assert result3 == {"count": 2}
        assert len(base_repo.queries) == 2

    @pytest.mark.asyncio
    async def test_cached_repository_no_cache_mutations(self):
        """Test that mutations are never cached."""
        base_repo = MockRepository()
        cached_repo = CachedRepository(base_repo)

        # Execute same mutation twice
        await cached_repo.execute_mutation("mutation", {"data": "test"})
        await cached_repo.execute_mutation("mutation", {"data": "test"})

        # Both should hit base repository
        assert len(base_repo.mutations) == 2


class TestToolFactory:
    """Test the tool factory."""

    @pytest.fixture
    def mock_mcp(self):
        """Create a mock MCP server."""
        mock = Mock()
        mock.registered_tools = []

        def tool_decorator(func):
            mock.registered_tools.append(func)
            return func

        mock.tool = tool_decorator
        return mock

    @pytest.fixture
    def factory(self, mock_mcp):
        """Create a tool factory."""
        return ToolFactory(mock_mcp, MockRepository())

    def test_register_tool_class(self, factory, mock_mcp):
        """Test that tool classes can be registered."""
        # Register tool class
        factory.register_tool_class(SampleTool)

        # Verify tool was stored
        assert "SampleTool" in factory._tools

        # Verify methods were registered with MCP
        # Should register safe_method and validated_method
        assert len(mock_mcp.registered_tools) >= 2

        # Check registered tool names
        tool_names = [tool.__name__ for tool in mock_mcp.registered_tools]
        assert "sampletool_safe_method" in tool_names
        assert "sampletool_validated_method" in tool_names

    def test_get_tool(self, factory):
        """Test retrieving registered tools."""
        # Register tool
        factory.register_tool_class(SampleTool)

        # Retrieve tool
        tool = factory.get_tool("SampleTool")
        assert isinstance(tool, SampleTool)

        # Non-existent tool
        assert factory.get_tool("NonExistent") is None

    def test_list_tools(self, factory):
        """Test listing registered tools."""
        # Register tool
        factory.register_tool_class(SampleTool)

        # List tools
        tools = factory.list_tools()
        assert "SampleTool" in tools
        assert tools["SampleTool"].startswith("Sample tool")
