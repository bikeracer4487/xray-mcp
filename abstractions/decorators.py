"""Decorators for standardizing tool behavior.

This module provides decorators that can be applied to tool methods
to standardize error handling, logging, and other cross-cutting concerns.
"""

import functools
import inspect
from typing import Callable, Any, Dict, TypeVar, ParamSpec
import logging

# Type variables for better type hints
P = ParamSpec('P')
T = TypeVar('T')

logger = logging.getLogger(__name__)


def tool_error_handler(func: Callable[P, T]) -> Callable[P, Dict[str, Any]]:
    """Decorator to standardize error handling for tool methods.
    
    This decorator catches exceptions from tool methods and returns
    them in a standardized error format. This eliminates the need
    for repetitive try/except blocks in tool implementations.
    
    Args:
        func: The tool method to wrap
        
    Returns:
        Wrapped function that returns standardized error responses
        
    Example:
        @tool_error_handler
        async def get_test(self, test_id: str) -> Dict[str, Any]:
            # Method implementation
            return result
    """
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Dict[str, Any]:
        try:
            # Handle both sync and async functions
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Ensure result is a dictionary
            if not isinstance(result, dict):
                return {"result": result}
            
            return result
            
        except Exception as e:
            # Log the error for debugging
            logger.error(
                f"Error in {func.__name__}: {type(e).__name__}: {str(e)}",
                exc_info=True
            )
            
            # Return standardized error response
            return {
                "error": str(e),
                "type": type(e).__name__,
                "function": func.__name__
            }
    
    return wrapper


def validate_required(*required_params: str) -> Callable:
    """Decorator to validate required parameters.
    
    This decorator checks that all required parameters are provided
    and are not None before calling the decorated function.
    
    Args:
        *required_params: Names of required parameters
        
    Returns:
        Decorator function
        
    Example:
        @validate_required('project_key', 'summary')
        async def create_test(self, project_key: str, summary: str, **kwargs):
            # Method implementation
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Get function signature to map args to param names
            sig = inspect.signature(func)
            
            # Check if we're dealing with a method (has self)
            is_method = 'self' in sig.parameters
            provided_args = list(args)
            
            # If it's a method, skip 'self' when binding
            if is_method and provided_args:
                provided_args = provided_args[1:]
            
            # Check each required parameter in kwargs
            missing = []
            for param in required_params:
                if param not in kwargs or kwargs[param] is None:
                    missing.append(param)
            
            if missing:
                from exceptions import ValidationError
                raise ValidationError(f"Missing required parameters: {', '.join(missing)}")
            
            # Call the original function
            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def log_execution(level: str = "INFO") -> Callable:
    """Decorator to log function execution.
    
    This decorator logs when a function is called and when it completes,
    including execution time and any errors.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Decorator function
        
    Example:
        @log_execution(level="DEBUG")
        async def get_test(self, test_id: str):
            # Method implementation
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            import time
            
            start_time = time.time()
            func_name = func.__name__
            log_level = getattr(logging, level.upper(), logging.INFO)
            
            # Log function call
            logger.log(log_level, f"Calling {func_name} with args={args[1:]} kwargs={kwargs}")
            
            try:
                # Execute function
                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Log successful completion
                elapsed = time.time() - start_time
                logger.log(log_level, f"Completed {func_name} in {elapsed:.3f}s")
                
                return result
                
            except Exception as e:
                # Log error
                elapsed = time.time() - start_time
                logger.error(
                    f"Error in {func_name} after {elapsed:.3f}s: {type(e).__name__}: {str(e)}"
                )
                raise
        
        return wrapper
    
    return decorator


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0) -> Callable:
    """Decorator to retry failed operations.
    
    This decorator automatically retries operations that fail with
    temporary errors, using exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff: Backoff multiplier for each retry (default: 2.0)
        
    Returns:
        Decorator function
        
    Example:
        @retry(max_attempts=3, delay=1.0)
        async def fetch_data(self):
            # Method that might fail temporarily
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            import asyncio
            
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    # Try to execute the function
                    if inspect.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Don't retry on the last attempt
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: "
                            f"{type(e).__name__}: {str(e)}. Retrying in {current_delay}s..."
                        )
                        
                        # Wait before retrying
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )
            
            # If we get here, all attempts failed
            raise last_exception
        
        return wrapper
    
    return decorator