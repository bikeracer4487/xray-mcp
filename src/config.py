"""Production configuration for Xray MCP Server."""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class SecurityLimits:
    """Security and DoS protection limits."""
    max_summary_length: int = 1000
    max_description_length: int = 100000
    max_steps_array_size: int = 100
    max_test_ids_array_size: int = 100
    max_request_timeout: int = 30
    max_payload_size_mb: float = 1.0


@dataclass
class RateLimits:
    """Rate limiting configuration."""
    requests_per_second: int = 10
    requests_per_hour: int = 1000
    burst_size: int = 20


@dataclass
class RetryConfig:
    """Retry and backoff configuration."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 3


@dataclass
class XrayMCPConfig:
    """Complete configuration for Xray MCP Server."""
    security: SecurityLimits
    rate_limits: RateLimits
    retry: RetryConfig
    circuit_breaker: CircuitBreakerConfig

    # Environment-specific settings
    environment: str
    debug_mode: bool
    log_level: str

    @classmethod
    def from_environment(cls) -> 'XrayMCPConfig':
        """Create configuration from environment variables."""
        env = os.getenv('XRAY_MCP_ENV', 'production').lower()

        # Adjust limits based on environment
        if env == 'development':
            security = SecurityLimits(
                max_summary_length=2000,
                max_description_length=200000,
                max_request_timeout=60
            )
            rate_limits = RateLimits(
                requests_per_second=100,
                requests_per_hour=10000
            )
            debug_mode = True
            log_level = 'DEBUG'
        elif env == 'staging':
            security = SecurityLimits()
            rate_limits = RateLimits(
                requests_per_second=20,
                requests_per_hour=2000
            )
            debug_mode = True
            log_level = 'INFO'
        else:  # production
            security = SecurityLimits()
            rate_limits = RateLimits()
            debug_mode = False
            log_level = 'WARNING'

        return cls(
            security=security,
            rate_limits=rate_limits,
            retry=RetryConfig(),
            circuit_breaker=CircuitBreakerConfig(),
            environment=env,
            debug_mode=debug_mode,
            log_level=log_level
        )


# Global configuration instance
config = XrayMCPConfig.from_environment()