"""Security and DoS protection for Xray MCP Server."""

import asyncio
import time
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque
from dataclasses import dataclass

from .config import config


@dataclass
class ValidationError:
    """Represents a validation error with details."""
    field: str
    message: str
    value_length: Optional[int] = None
    limit: Optional[int] = None


class PayloadValidator:
    """Validates request payloads for size and content limits."""

    def validate_request(self, params: Dict[str, Any]) -> List[ValidationError]:
        """Validate request parameters against security limits.

        Args:
            params: Request parameters dictionary

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate string field lengths
        if 'summary' in params and params['summary']:
            summary_len = len(str(params['summary']))
            if summary_len > config.security.max_summary_length:
                errors.append(ValidationError(
                    field='summary',
                    message=f'Summary exceeds maximum length',
                    value_length=summary_len,
                    limit=config.security.max_summary_length
                ))

        if 'description' in params and params['description']:
            desc_len = len(str(params['description']))
            if desc_len > config.security.max_description_length:
                errors.append(ValidationError(
                    field='description',
                    message=f'Description exceeds maximum length',
                    value_length=desc_len,
                    limit=config.security.max_description_length
                ))

        # Validate array sizes
        array_fields = [
            ('test_issue_ids', 'test_issue_ids', config.security.max_test_ids_array_size),
            ('test_exec_issue_ids', 'test_exec_issue_ids', config.security.max_test_ids_array_size),
            ('defects', 'defects', config.security.max_test_ids_array_size),
            ('environments', 'environments', config.security.max_test_ids_array_size),
        ]

        for field_name, display_name, max_size in array_fields:
            if field_name in params and isinstance(params[field_name], (list, tuple)):
                array_len = len(params[field_name])
                if array_len > max_size:
                    errors.append(ValidationError(
                        field=field_name,
                        message=f'{display_name} array exceeds maximum size',
                        value_length=array_len,
                        limit=max_size
                    ))

        # Validate steps array if present
        if 'steps' in params and isinstance(params['steps'], (list, str)):
            if isinstance(params['steps'], str):
                # JSON string - validate length first
                steps_len = len(params['steps'])
                if steps_len > config.security.max_description_length:
                    errors.append(ValidationError(
                        field='steps',
                        message=f'Steps JSON string exceeds maximum length',
                        value_length=steps_len,
                        limit=config.security.max_description_length
                    ))
            elif isinstance(params['steps'], list):
                steps_count = len(params['steps'])
                if steps_count > config.security.max_steps_array_size:
                    errors.append(ValidationError(
                        field='steps',
                        message=f'Steps array exceeds maximum size',
                        value_length=steps_count,
                        limit=config.security.max_steps_array_size
                    ))

        return errors


class RateLimiter:
    """Token bucket rate limiter for DoS protection."""

    def __init__(self):
        self._buckets: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                'tokens': config.rate_limits.burst_size,
                'last_refill': time.time(),
                'requests': deque()
            }
        )
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, client_id: str) -> tuple[bool, Optional[str]]:
        """Check if request is within rate limits.

        Args:
            client_id: Unique identifier for the client

        Returns:
            Tuple of (allowed: bool, error_message: Optional[str])
        """
        async with self._lock:
            now = time.time()
            bucket = self._buckets[client_id]

            # Refill tokens based on elapsed time
            elapsed = now - bucket['last_refill']
            tokens_to_add = elapsed * config.rate_limits.requests_per_second
            bucket['tokens'] = min(
                config.rate_limits.burst_size,
                bucket['tokens'] + tokens_to_add
            )
            bucket['last_refill'] = now

            # Clean old requests for hourly limit
            requests = bucket['requests']
            hour_ago = now - 3600
            while requests and requests[0] < hour_ago:
                requests.popleft()

            # Check hourly limit
            if len(requests) >= config.rate_limits.requests_per_hour:
                return False, f"Hourly rate limit exceeded ({config.rate_limits.requests_per_hour}/hour)"

            # Check per-second limit (token bucket)
            if bucket['tokens'] < 1:
                return False, f"Rate limit exceeded ({config.rate_limits.requests_per_second}/second)"

            # Allow request
            bucket['tokens'] -= 1
            requests.append(now)
            return True, None


class RequestValidator:
    """Complete request validation and security checking."""

    def __init__(self):
        self.payload_validator = PayloadValidator()
        self.rate_limiter = RateLimiter()

    async def validate_request(self, client_id: str, params: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate complete request for security and rate limiting.

        Args:
            client_id: Client identifier for rate limiting
            params: Request parameters

        Returns:
            Tuple of (valid: bool, error_messages: List[str])
        """
        errors = []

        # Check rate limits first
        rate_allowed, rate_error = await self.rate_limiter.check_rate_limit(client_id)
        if not rate_allowed:
            errors.append(rate_error)
            return False, errors

        # Validate payload
        validation_errors = self.payload_validator.validate_request(params)
        for error in validation_errors:
            if error.value_length and error.limit:
                errors.append(
                    f"{error.message}: {error.value_length} > {error.limit} characters/items"
                )
            else:
                errors.append(error.message)

        return len(errors) == 0, errors


# Global validator instance
request_validator = RequestValidator()