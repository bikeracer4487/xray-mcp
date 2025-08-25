"""Response size limiting for Xray MCP server.

This module provides response size limiting capabilities to prevent
potential DoS attacks and memory exhaustion from extremely large API responses.
It includes configurable limits and helpful error messages for size violations.
"""

import asyncio
import aiohttp
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class ResponseLimits:
    """Configuration for response size limits.
    
    Attributes:
        max_response_size: Maximum size in bytes for HTTP responses (default: 10MB)
        max_json_size: Maximum size in bytes for JSON parsing (default: 5MB)
        max_text_size: Maximum size in bytes for text responses (default: 1MB)
        timeout_seconds: Request timeout in seconds (default: 30)
    """
    max_response_size: int = 10 * 1024 * 1024  # 10MB
    max_json_size: int = 5 * 1024 * 1024       # 5MB  
    max_text_size: int = 1 * 1024 * 1024       # 1MB
    timeout_seconds: int = 30


class ResponseSizeLimitError(Exception):
    """Raised when response size limits are exceeded."""
    pass


class ResponseLimiter:
    """Manages response size limits and safe response reading.
    
    This class provides safe methods for reading HTTP responses with
    configurable size limits to prevent memory exhaustion attacks.
    """
    
    def __init__(self, limits: Optional[ResponseLimits] = None):
        """Initialize response limiter with optional custom limits.
        
        Args:
            limits: Optional custom limits, uses defaults if not provided
        """
        self.limits = limits or ResponseLimits()
        self.logger = logging.getLogger(__name__)
    
    async def read_json_response(
        self, 
        response: aiohttp.ClientResponse,
        max_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Safely read JSON response with size limits.
        
        Args:
            response: aiohttp response to read from
            max_size: Optional override for max JSON size
            
        Returns:
            Parsed JSON response
            
        Raises:
            ResponseSizeLimitError: If response exceeds size limits
            ValueError: If JSON parsing fails
        """
        effective_limit = max_size or self.limits.max_json_size
        
        # Check content-length header if available
        content_length = response.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                if size > effective_limit:
                    raise ResponseSizeLimitError(
                        f"Response size ({self._format_size(size)}) exceeds JSON limit "
                        f"({self._format_size(effective_limit)}). This may indicate "
                        f"an overly broad query or potential DoS attack."
                    )
            except ValueError:
                # Invalid content-length header, continue with streaming read
                pass
        
        # Stream response with size checking
        content = bytearray()
        
        async for chunk in response.content.iter_chunked(8192):  # 8KB chunks
            content.extend(chunk)
            
            if len(content) > effective_limit:
                raise ResponseSizeLimitError(
                    f"Response size ({self._format_size(len(content))}) exceeds JSON limit "
                    f"({self._format_size(effective_limit)}). Consider using pagination, "
                    f"reducing query scope, or increasing limits if this is expected."
                )
        
        # Log response size for monitoring
        size = len(content)
        if size > effective_limit * 0.8:  # Warn at 80% of limit
            self.logger.warning(
                f"Large JSON response: {self._format_size(size)} "
                f"({(size / effective_limit * 100):.1f}% of limit)"
            )
        
        # Parse JSON
        try:
            return response._loop.run_in_executor(
                None, 
                lambda: __import__('json').loads(content.decode('utf-8'))
            ) if len(content) > 1024 * 1024 else response._loop.run_in_executor(
                None,
                lambda: __import__('json').loads(content.decode('utf-8'))
            )
        except Exception:
            # Synchronous fallback for smaller responses
            import json
            return json.loads(content.decode('utf-8'))
    
    async def read_text_response(
        self,
        response: aiohttp.ClientResponse,
        max_size: Optional[int] = None
    ) -> str:
        """Safely read text response with size limits.
        
        Args:
            response: aiohttp response to read from
            max_size: Optional override for max text size
            
        Returns:
            Response text content
            
        Raises:
            ResponseSizeLimitError: If response exceeds size limits
        """
        effective_limit = max_size or self.limits.max_text_size
        
        # Check content-length header if available
        content_length = response.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                if size > effective_limit:
                    raise ResponseSizeLimitError(
                        f"Response size ({self._format_size(size)}) exceeds text limit "
                        f"({self._format_size(effective_limit)})"
                    )
            except ValueError:
                pass
        
        # Stream response with size checking
        content = bytearray()
        
        async for chunk in response.content.iter_chunked(8192):  # 8KB chunks
            content.extend(chunk)
            
            if len(content) > effective_limit:
                # Truncate and return partial content with warning
                truncated_content = content[:effective_limit].decode('utf-8', errors='ignore')
                raise ResponseSizeLimitError(
                    f"Response truncated at {self._format_size(effective_limit)}. "
                    f"Partial content: {truncated_content[:500]}..."
                )
        
        return content.decode('utf-8')
    
    def get_timeout(self) -> aiohttp.ClientTimeout:
        """Get configured timeout for aiohttp requests.
        
        Returns:
            ClientTimeout object with configured timeout
        """
        return aiohttp.ClientTimeout(
            total=self.limits.timeout_seconds,
            connect=min(10, self.limits.timeout_seconds // 3)  # Connect timeout is 1/3 of total
        )
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format byte size in human readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string (e.g., "1.5MB", "512KB")
        """
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f}MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"


# Global response limiter instance with default limits
_default_limiter = ResponseLimiter()

def get_response_limiter() -> ResponseLimiter:
    """Get the default response limiter instance.
    
    Returns:
        Default ResponseLimiter instance
    """
    return _default_limiter


def create_custom_limiter(
    max_response_size: int = 10 * 1024 * 1024,
    max_json_size: int = 5 * 1024 * 1024,
    max_text_size: int = 1 * 1024 * 1024,
    timeout_seconds: int = 30
) -> ResponseLimiter:
    """Create a ResponseLimiter with custom limits.
    
    Args:
        max_response_size: Maximum HTTP response size in bytes
        max_json_size: Maximum JSON response size in bytes
        max_text_size: Maximum text response size in bytes
        timeout_seconds: Request timeout in seconds
        
    Returns:
        ResponseLimiter with custom configuration
    """
    limits = ResponseLimits(
        max_response_size=max_response_size,
        max_json_size=max_json_size,
        max_text_size=max_text_size,
        timeout_seconds=timeout_seconds
    )
    return ResponseLimiter(limits)