"""Repository pattern implementation for data access.

This module provides an abstraction layer between the tools and the
GraphQL client, making it easier to test tools in isolation and
adapt to API changes without modifying tool logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

# Handle both package and direct execution import modes
try:
    from ..client import XrayGraphQLClient
    from ..exceptions import GraphQLError
except ImportError:
    from client import XrayGraphQLClient
    from exceptions import GraphQLError


class Repository(ABC):
    """Abstract base class for repository implementations.
    
    The repository pattern provides an abstraction layer between
    business logic (tools) and data access (GraphQL API). This makes
    it easier to:
    - Test tools without making actual API calls
    - Switch between different data sources
    - Cache results
    - Add logging/monitoring
    """
    
    @abstractmethod
    async def execute_query(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GraphQL query.
        
        Args:
            query: The GraphQL query string
            variables: Variables for the query
            
        Returns:
            The query results
            
        Raises:
            GraphQLError: If the query fails
        """
        pass
    
    @abstractmethod
    async def execute_mutation(self, mutation: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GraphQL mutation.
        
        Args:
            mutation: The GraphQL mutation string
            variables: Variables for the mutation
            
        Returns:
            The mutation results
            
        Raises:
            GraphQLError: If the mutation fails
        """
        pass


class GraphQLRepository(Repository):
    """Repository implementation using Xray's GraphQL API.
    
    This is the concrete implementation that actually communicates
    with the Xray API. It wraps the GraphQL client to provide a
    consistent interface that can be easily mocked for testing.
    """
    
    def __init__(self, graphql_client: XrayGraphQLClient):
        """Initialize the repository with a GraphQL client.
        
        Args:
            graphql_client: Configured GraphQL client instance
        """
        self.client = graphql_client
    
    async def execute_query(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GraphQL query using the client.
        
        Args:
            query: The GraphQL query string
            variables: Variables for the query
            
        Returns:
            The query results
            
        Raises:
            GraphQLError: If the query fails
        """
        return await self.client.execute_query(query, variables)
    
    async def execute_mutation(self, mutation: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GraphQL mutation using the client.
        
        Args:
            mutation: The GraphQL mutation string
            variables: Variables for the mutation
            
        Returns:
            The mutation results
            
        Raises:
            GraphQLError: If the mutation fails
        """
        # The GraphQL client uses execute_query for both queries and mutations
        return await self.client.execute_query(mutation, variables)


class CachedRepository(Repository):
    """Repository decorator that adds caching capabilities.
    
    This decorator can be used to wrap any repository implementation
    to add caching functionality. This is useful for reducing API calls
    and improving performance for frequently accessed data.
    """
    
    def __init__(self, repository: Repository, cache_ttl: int = 300):
        """Initialize the cached repository.
        
        Args:
            repository: The underlying repository to wrap
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        self.repository = repository
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Any] = {}
        self._cache_times: Dict[str, float] = {}
    
    def _get_cache_key(self, query: str, variables: Dict[str, Any]) -> str:
        """Generate a cache key from query and variables."""
        import json
        import hashlib
        
        # Create a deterministic string representation
        key_data = {
            "query": query,
            "variables": variables
        }
        key_str = json.dumps(key_data, sort_keys=True)
        
        # Hash it to get a fixed-size key
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if a cache entry is still valid."""
        import time
        
        if key not in self._cache_times:
            return False
        
        elapsed = time.time() - self._cache_times[key]
        return elapsed < self.cache_ttl
    
    async def execute_query(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a query with caching.
        
        Args:
            query: The GraphQL query string
            variables: Variables for the query
            
        Returns:
            The query results (from cache if available)
        """
        import time
        
        cache_key = self._get_cache_key(query, variables)
        
        # Return from cache if valid
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        # Execute query and cache result
        result = await self.repository.execute_query(query, variables)
        self._cache[cache_key] = result
        self._cache_times[cache_key] = time.time()
        
        return result
    
    async def execute_mutation(self, mutation: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a mutation (never cached).
        
        Mutations modify data and should never be cached.
        
        Args:
            mutation: The GraphQL mutation string
            variables: Variables for the mutation
            
        Returns:
            The mutation results
        """
        # Never cache mutations
        return await self.repository.execute_mutation(mutation, variables)
    
    def clear_cache(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._cache_times.clear()