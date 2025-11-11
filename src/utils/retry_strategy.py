"""Advanced retry strategy utilities for Xray MCP server with indexing delay mitigation."""

import asyncio
import random
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from enum import Enum
from dataclasses import dataclass
from ..config import config

T = TypeVar('T')


class RetryReason(Enum):
    """Different reasons for retrying operations."""
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "auth_error"
    RATE_LIMIT = "rate_limit"
    INDEXING_DELAY = "indexing_delay"
    SERVER_ERROR = "server_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class RetryResult:
    """Result of a retry operation."""
    success: bool
    result: Any = None
    attempts: int = 0
    total_delay: float = 0.0
    last_error: Optional[Exception] = None
    retry_reason: Optional[RetryReason] = None


class IndexingDelayMitigator:
    """Advanced retry strategy specifically designed for Xray indexing delays."""

    def __init__(self, retry_config: Optional[Dict[str, Any]] = None):
        """Initialize with configuration from global config or overrides."""
        self.config = config.retry
        if retry_config:
            # Allow runtime override of configuration
            for key, value in retry_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

    def calculate_delay(self, attempt: int, retry_reason: RetryReason) -> float:
        """Calculate delay with exponential backoff and jitter."""
        if retry_reason == RetryReason.INDEXING_DELAY:
            base_delay = self.config.indexing_base_delay
            max_delay = self.config.indexing_max_delay
        else:
            base_delay = self.config.base_delay
            max_delay = self.config.max_delay

        # Exponential backoff
        delay = base_delay * (self.config.backoff_multiplier ** attempt)
        delay = min(delay, max_delay)

        # Add jitter to prevent thundering herd
        if self.config.enable_jitter:
            jitter_range = delay * self.config.jitter_max_percent
            jitter = random.uniform(-jitter_range, jitter_range)
            delay = max(0.1, delay + jitter)  # Minimum 100ms delay

        return delay

    def get_max_retries(self, retry_reason: RetryReason) -> int:
        """Get maximum retries based on the reason."""
        if retry_reason == RetryReason.INDEXING_DELAY:
            return self.config.indexing_max_retries
        return self.config.max_retries

    def identify_retry_reason(self, error: Exception) -> RetryReason:
        """Identify the reason for retry based on error patterns."""
        error_str = str(error).lower()

        # Indexing delay patterns
        indexing_keywords = [
            'not found after', 'indexing delay', 'recently created',
            'not indexed', 'reindex', 'not available immediately'
        ]
        if any(keyword in error_str for keyword in indexing_keywords):
            return RetryReason.INDEXING_DELAY

        # Authentication errors
        auth_keywords = ['authentication', 'unauthorized', 'token', 'expired', '401']
        if any(keyword in error_str for keyword in auth_keywords):
            return RetryReason.AUTHENTICATION_ERROR

        # Rate limiting
        rate_limit_keywords = ['rate limit', 'too many requests', '429']
        if any(keyword in error_str for keyword in rate_limit_keywords):
            return RetryReason.RATE_LIMIT

        # Network errors
        network_keywords = ['network', 'connection', 'timeout', 'dns']
        if any(keyword in error_str for keyword in network_keywords):
            return RetryReason.NETWORK_ERROR

        # Server errors
        server_keywords = ['500', '502', '503', '504', 'internal server error', 'bad gateway']
        if any(keyword in error_str for keyword in server_keywords):
            return RetryReason.SERVER_ERROR

        return RetryReason.UNKNOWN

    async def execute_with_retry(
        self,
        operation: Callable[[], Any],
        operation_name: str = "operation",
        custom_retry_config: Optional[Dict[str, Any]] = None,
        expected_indexing_delay: bool = False
    ) -> RetryResult:
        """Execute an operation with intelligent retry logic.

        Args:
            operation: Async callable to execute
            operation_name: Human-readable name for logging
            custom_retry_config: Override default retry configuration
            expected_indexing_delay: Hint that operation may encounter indexing delays

        Returns:
            RetryResult with success status and details
        """
        start_time = time.time()
        attempts = 0
        total_delay = 0.0
        last_error = None
        retry_reason = RetryReason.UNKNOWN

        # If we expect indexing delays, start with that assumption
        if expected_indexing_delay:
            retry_reason = RetryReason.INDEXING_DELAY

        # Apply custom configuration if provided
        if custom_retry_config:
            original_config = self.config
            for key, value in custom_retry_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

        try:
            while attempts <= self.get_max_retries(retry_reason):
                try:
                    # Add predictive delay for create-then-read operations
                    if attempts == 0 and expected_indexing_delay:
                        initial_delay = self.config.create_then_read_delay
                        await asyncio.sleep(initial_delay)
                        total_delay += initial_delay

                    result = await operation()
                    return RetryResult(
                        success=True,
                        result=result,
                        attempts=attempts + 1,
                        total_delay=total_delay
                    )

                except Exception as e:
                    attempts += 1
                    last_error = e
                    retry_reason = self.identify_retry_reason(e)

                    # Don't retry certain types of errors
                    if retry_reason in [RetryReason.AUTHENTICATION_ERROR] and attempts > 1:
                        break

                    if attempts <= self.get_max_retries(retry_reason):
                        delay = self.calculate_delay(attempts - 1, retry_reason)
                        await asyncio.sleep(delay)
                        total_delay += delay

            # All retries exhausted
            return RetryResult(
                success=False,
                attempts=attempts,
                total_delay=total_delay,
                last_error=last_error,
                retry_reason=retry_reason
            )

        finally:
            # Restore original configuration if it was overridden
            if custom_retry_config:
                self.config = original_config

    async def create_then_read_with_mitigation(
        self,
        create_operation: Callable[[], Any],
        read_operation: Callable[[], Any],
        operation_name: str = "create_then_read"
    ) -> RetryResult:
        """Optimized pattern for create-then-read operations with indexing delay mitigation.

        This implements a hybrid approach:
        1. Execute create operation
        2. Wait a predictive delay
        3. Attempt read with progressive backoff

        Args:
            create_operation: Operation that creates an entity
            read_operation: Operation that reads the created entity
            operation_name: Human-readable name for logging

        Returns:
            RetryResult containing both create and read results
        """
        # Step 1: Execute create operation
        create_result = await self.execute_with_retry(
            create_operation,
            f"{operation_name}_create",
            expected_indexing_delay=False
        )

        if not create_result.success:
            return create_result

        # Step 2: Execute read with indexing delay mitigation
        read_result = await self.execute_with_retry(
            read_operation,
            f"{operation_name}_read",
            expected_indexing_delay=True
        )

        # Combine results
        if read_result.success:
            return RetryResult(
                success=True,
                result={
                    'create_result': create_result.result,
                    'read_result': read_result.result
                },
                attempts=create_result.attempts + read_result.attempts,
                total_delay=create_result.total_delay + read_result.total_delay
            )
        else:
            return RetryResult(
                success=False,
                result={'create_result': create_result.result},
                attempts=create_result.attempts + read_result.attempts,
                total_delay=create_result.total_delay + read_result.total_delay,
                last_error=read_result.last_error,
                retry_reason=read_result.retry_reason
            )


# Global instance for use across the application
indexing_mitigator = IndexingDelayMitigator()


# Convenience functions for common patterns
async def retry_with_indexing_delay(
    operation: Callable[[], Any],
    operation_name: str = "operation"
) -> RetryResult:
    """Convenience function for operations that may encounter indexing delays."""
    return await indexing_mitigator.execute_with_retry(
        operation,
        operation_name,
        expected_indexing_delay=True
    )


async def retry_create_then_read(
    create_operation: Callable[[], Any],
    read_operation: Callable[[], Any],
    operation_name: str = "create_then_read"
) -> RetryResult:
    """Convenience function for create-then-read patterns."""
    return await indexing_mitigator.create_then_read_with_mitigation(
        create_operation,
        read_operation,
        operation_name
    )