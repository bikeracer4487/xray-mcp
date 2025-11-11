"""Circuit breaker pattern for resilient error handling."""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Callable, Any
from dataclasses import dataclass

from .config import config


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open" # Testing recovery


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring."""
    state: CircuitState
    failure_count: int
    success_count: int
    last_failure_time: Optional[datetime]
    last_state_change: datetime
    total_requests: int
    rejected_requests: int


class CircuitBreaker:
    """Circuit breaker for protecting against cascading failures."""

    def __init__(self, name: str = "default"):
        """Initialize circuit breaker.

        Args:
            name: Name for logging/monitoring purposes
        """
        self.name = name
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._last_state_change = datetime.now()
        self._half_open_calls = 0
        self._total_requests = 0
        self._rejected_requests = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Current circuit breaker state."""
        return self._state

    @property
    def stats(self) -> CircuitBreakerStats:
        """Get current circuit breaker statistics."""
        return CircuitBreakerStats(
            state=self._state,
            failure_count=self._failure_count,
            success_count=self._success_count,
            last_failure_time=self._last_failure_time,
            last_state_change=self._last_state_change,
            total_requests=self._total_requests,
            rejected_requests=self._rejected_requests
        )

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result if successful

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Original exception from function if it fails
        """
        async with self._lock:
            self._total_requests += 1

            # Check if circuit should transition to half-open
            if self._state == CircuitState.OPEN and self._should_attempt_reset():
                self._transition_to_half_open()

            # Reject request if circuit is open
            if self._state == CircuitState.OPEN:
                self._rejected_requests += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Last failure: {self._last_failure_time}, "
                    f"Failures: {self._failure_count}"
                )

            # Limit calls in half-open state
            if (self._state == CircuitState.HALF_OPEN and
                self._half_open_calls >= config.circuit_breaker.half_open_max_calls):
                self._rejected_requests += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is HALF_OPEN with max calls reached"
                )

        # Execute the function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Record success
            await self._record_success()
            return result

        except Exception as e:
            # Record failure
            await self._record_failure()
            raise

    async def _record_success(self):
        """Record successful operation."""
        async with self._lock:
            self._success_count += 1

            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                # If we've had enough successful calls, close the circuit
                if self._half_open_calls >= config.circuit_breaker.half_open_max_calls:
                    self._transition_to_closed()

    async def _record_failure(self):
        """Record failed operation."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now()

            # Open circuit if failure threshold is reached
            if (self._state == CircuitState.CLOSED and
                self._failure_count >= config.circuit_breaker.failure_threshold):
                self._transition_to_open()
            elif self._state == CircuitState.HALF_OPEN:
                # Go back to open on any failure in half-open state
                self._transition_to_open()

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset to half-open."""
        if not self._last_failure_time:
            return True

        elapsed = datetime.now() - self._last_failure_time
        return elapsed.total_seconds() >= config.circuit_breaker.recovery_timeout

    def _transition_to_closed(self):
        """Transition circuit to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._half_open_calls = 0
        self._last_state_change = datetime.now()

    def _transition_to_open(self):
        """Transition circuit to OPEN state."""
        self._state = CircuitState.OPEN
        self._half_open_calls = 0
        self._last_state_change = datetime.now()

    def _transition_to_half_open(self):
        """Transition circuit to HALF_OPEN state."""
        self._state = CircuitState.HALF_OPEN
        self._half_open_calls = 0
        self._last_state_change = datetime.now()

    async def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        async with self._lock:
            self._transition_to_closed()


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and rejecting requests."""
    pass


# Global circuit breakers for different services
_circuit_breakers = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker instance.

    Args:
        name: Circuit breaker name

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name)
    return _circuit_breakers[name]