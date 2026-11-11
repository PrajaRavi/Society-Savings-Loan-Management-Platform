"""Exponential back-off retry utility with jitter for database and network resilience."""
import asyncio
import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Coroutine, Tuple, Type, Union

logger = logging.getLogger("society.resilience")

# Common transient database and network exceptions
TRANSIENT_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    ConnectionRefusedError,
    ConnectionResetError,
    TimeoutError,
    OSError,
)

# Dynamically add asyncpg or sqlalchemy exceptions if available
try:
    import asyncpg
    TRANSIENT_EXCEPTIONS = TRANSIENT_EXCEPTIONS + (
        asyncpg.PostgresConnectionError,
        asyncpg.CannotConnectNowError,
        asyncpg.TooManyConnectionsError,
        asyncpg.ConnectionDoesNotExistError,
    )
except ImportError:
    pass

try:
    from sqlalchemy.exc import (
        OperationalError,
        InterfaceError,
        DBAPIError,
    )
    TRANSIENT_EXCEPTIONS = TRANSIENT_EXCEPTIONS + (
        OperationalError,
        InterfaceError,
        DBAPIError,
    )
except ImportError:
    pass


def calculate_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 16.0,
    exponential_factor: float = 2.0,
    jitter: bool = True,
) -> float:
    """Calculate exponential back-off delay with randomized full jitter."""
    delay = min(max_delay, base_delay * (exponential_factor ** attempt))
    if jitter:
        # Full jitter prevents thundering herd on recovery
        delay = random.uniform(0, delay)
    return max(base_delay * 0.1, delay)


def retry_async(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 16.0,
    exponential_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = TRANSIENT_EXCEPTIONS,
    on_retry: Callable[[Exception, int, float], None] | None = None,
):
    """Decorator for async operations with exponential back-off retry."""
    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    if attempt == max_retries - 1:
                        logger.error(
                            f"[Retry Exhausted] Function '{func.__name__}' failed after {max_retries} attempts: {exc}"
                        )
                        raise
                    
                    delay = calculate_backoff(
                        attempt, base_delay, max_delay, exponential_factor, jitter=True
                    )
                    logger.warning(
                        f"[Retryable Error] Attempt {attempt + 1}/{max_retries} failed for '{func.__name__}': {exc}. Retrying in {delay:.2f}s..."
                    )
                    if on_retry:
                        on_retry(exc, attempt + 1, delay)
                    await asyncio.sleep(delay)
            if last_exception:
                raise last_exception
        return wrapper
    return decorator


def retry_sync(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 16.0,
    exponential_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = TRANSIENT_EXCEPTIONS,
    on_retry: Callable[[Exception, int, float], None] | None = None,
):
    """Decorator for synchronous operations with exponential back-off retry."""
    def decorator(func: Callable[..., Any]):
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    if attempt == max_retries - 1:
                        logger.error(
                            f"[Retry Exhausted] Function '{func.__name__}' failed after {max_retries} attempts: {exc}"
                        )
                        raise
                    
                    delay = calculate_backoff(
                        attempt, base_delay, max_delay, exponential_factor, jitter=True
                    )
                    logger.warning(
                        f"[Retryable Error] Attempt {attempt + 1}/{max_retries} failed for '{func.__name__}': {exc}. Retrying in {delay:.2f}s..."
                    )
                    if on_retry:
                        on_retry(exc, attempt + 1, delay)
                    time.sleep(delay)
            if last_exception:
                raise last_exception
        return wrapper
    return decorator
