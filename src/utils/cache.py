"""Simple in-memory caching for GraphQL responses."""

import time
from typing import Any, Optional, Dict
from threading import Lock


class SimpleCache:
    """Thread-safe in-memory cache with TTL support."""

    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        with self._lock:
            if key not in self.cache:
                return None

            entry = self.cache[key]
            if time.time() > entry['expires_at']:
                del self.cache[key]
                return None

            return entry['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Cache a value with optional TTL."""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl

        with self._lock:
            self.cache[key] = {
                'value': value,
                'expires_at': expires_at
            }

    def delete(self, key: str) -> bool:
        """Delete a cached value."""
        with self._lock:
            return self.cache.pop(key, None) is not None

    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self.cache.clear()

    def cleanup(self) -> int:
        """Remove expired entries and return count removed."""
        current_time = time.time()
        expired_keys = []

        with self._lock:
            for key, entry in self.cache.items():
                if current_time > entry['expires_at']:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.cache[key]

        return len(expired_keys)

    def stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        with self._lock:
            return {
                'total_entries': len(self.cache),
                'expired_count': self.cleanup()
            }


def generate_cache_key(operation: str, **params) -> str:
    """Generate a cache key from operation and parameters."""
    # Sort parameters for consistent key generation
    sorted_params = sorted(params.items())
    param_str = '_'.join(f"{k}:{v}" for k, v in sorted_params if v is not None)
    return f"{operation}_{param_str}".replace(' ', '_').replace('"', '')


# Global cache instance
_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get the global cache instance."""
    return _cache