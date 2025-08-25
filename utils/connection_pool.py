"""Connection pool manager for HTTP requests.

This module provides connection pooling functionality to improve performance
by reusing HTTP connections across multiple requests. It handles session
lifecycle management and provides safe cleanup on shutdown.
"""

import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from dataclasses import dataclass

# No additional imports needed - this module is self-contained


@dataclass
class ConnectionPoolConfig:
    """Configuration for HTTP connection pool.
    
    Attributes:
        connector_limit: Maximum number of connections in pool (default: 30)
        connector_limit_per_host: Maximum connections per host (default: 10)
        timeout_total: Total timeout for requests in seconds (default: 30)
        timeout_connect: Connection timeout in seconds (default: 10)
        enable_keepalive: Enable HTTP keep-alive (default: True)
        keepalive_timeout: Keep-alive timeout in seconds (default: 30)
    """
    connector_limit: int = 30
    connector_limit_per_host: int = 10
    timeout_total: float = 30.0
    timeout_connect: float = 10.0
    enable_keepalive: bool = True
    keepalive_timeout: float = 30.0


class ConnectionPoolManager:
    """Manages HTTP connection pools for efficient request handling.
    
    This manager provides a singleton session that can be shared across
    multiple clients to improve performance through connection reuse.
    It handles proper cleanup and provides thread-safe access.
    
    Features:
    - Singleton pattern for shared session access
    - Configurable connection limits and timeouts
    - Automatic cleanup on shutdown
    - Thread-safe session management
    
    Usage:
        pool = ConnectionPoolManager()
        async with pool.get_session() as session:
            async with session.get(url) as response:
                data = await response.json()
    """
    
    _instance: Optional['ConnectionPoolManager'] = None
    _lock = asyncio.Lock()
    
    def __init__(self, config: Optional[ConnectionPoolConfig] = None):
        """Initialize the connection pool manager.
        
        Args:
            config: Optional connection pool configuration
        """
        self.config = config or ConnectionPoolConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
        self._session_lock = asyncio.Lock()
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    async def get_instance(cls, config: Optional[ConnectionPoolConfig] = None) -> 'ConnectionPoolManager':
        """Get singleton instance of connection pool manager.
        
        Args:
            config: Optional configuration for first initialization
            
        Returns:
            Singleton ConnectionPoolManager instance
        """
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls(config)
            return cls._instance
    
    async def _create_session(self) -> aiohttp.ClientSession:
        """Create a new aiohttp ClientSession with optimized settings.
        
        Returns:
            Configured ClientSession with connection pooling
        """
        # Create TCP connector with connection pooling settings
        self._connector = aiohttp.TCPConnector(
            limit=self.config.connector_limit,
            limit_per_host=self.config.connector_limit_per_host,
            enable_cleanup_closed=True,
            keepalive_timeout=self.config.keepalive_timeout if self.config.enable_keepalive else 0,
            ttl_dns_cache=300,  # 5 minutes DNS cache
        )
        
        # Create timeout configuration
        timeout = aiohttp.ClientTimeout(
            total=self.config.timeout_total,
            connect=self.config.timeout_connect,
        )
        
        # Create session with connector and timeout
        session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Xray-MCP-Server/1.0',
            },
            raise_for_status=False,  # We handle status codes manually
        )
        
        self.logger.info(f"Created HTTP session with connection pool (limit: {self.config.connector_limit})")
        return session
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get the shared ClientSession, creating it if necessary.
        
        Returns:
            Shared aiohttp ClientSession for making requests
            
        Note:
            This method is thread-safe and ensures only one session
            is created even when called concurrently.
        """
        async with self._session_lock:
            if self._session is None or self._session.closed:
                self._session = await self._create_session()
            return self._session
    
    @asynccontextmanager
    async def session_context(self):
        """Async context manager for getting session safely.
        
        Yields:
            aiohttp.ClientSession: Configured session for HTTP requests
            
        Example:
            async with pool.session_context() as session:
                async with session.get(url) as response:
                    data = await response.json()
        """
        session = await self.get_session()
        try:
            yield session
        except Exception:
            # Log any errors but don't close session - it may be reused
            self.logger.exception("Error in session context")
            raise
    
    async def close(self):
        """Close the connection pool and cleanup resources.
        
        This should be called when the application shuts down to ensure
        proper cleanup of connections and prevent resource leaks.
        """
        async with self._session_lock:
            if self._session and not self._session.closed:
                await self._session.close()
                self.logger.info("Closed HTTP session and connection pool")
            self._session = None
            self._connector = None
    
    async def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics for monitoring.
        
        Returns:
            Dictionary with pool statistics including:
            - total_connections: Total connections in pool
            - available_connections: Available connections
            - acquired_connections: Currently acquired connections
            - configuration: Pool configuration settings
        """
        stats = {
            'configuration': {
                'connector_limit': self.config.connector_limit,
                'connector_limit_per_host': self.config.connector_limit_per_host,
                'timeout_total': self.config.timeout_total,
                'timeout_connect': self.config.timeout_connect,
                'enable_keepalive': self.config.enable_keepalive,
                'keepalive_timeout': self.config.keepalive_timeout,
            },
            'session_created': self._session is not None,
            'session_closed': self._session.closed if self._session else True,
        }
        
        # Add connector statistics if available
        if self._connector:
            stats.update({
                'total_connections': len(self._connector._conns),
                'available_connections': len([conn for conns in self._connector._conns.values() for conn in conns]),
            })
        
        return stats


# Global connection pool manager instance
_global_pool_manager: Optional[ConnectionPoolManager] = None

async def get_connection_pool(config: Optional[ConnectionPoolConfig] = None) -> ConnectionPoolManager:
    """Get the global connection pool manager instance.
    
    Args:
        config: Optional configuration for first initialization
        
    Returns:
        Global ConnectionPoolManager instance
    """
    global _global_pool_manager
    if _global_pool_manager is None:
        _global_pool_manager = await ConnectionPoolManager.get_instance(config)
    return _global_pool_manager


async def close_connection_pool():
    """Close the global connection pool manager.
    
    This should be called during application shutdown to ensure
    proper cleanup of HTTP connections.
    """
    global _global_pool_manager
    if _global_pool_manager:
        await _global_pool_manager.close()
        _global_pool_manager = None