"""Retry utilities with exponential backoff."""

import asyncio
from functools import wraps
from typing import Any, Callable, TypeVar

from app.core.logger import logger

T = TypeVar("T")


async def retry_async(
    fn: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """
    Retry an async function with exponential backoff.

    Args:
        fn: Async function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Result of the function call

    Raises:
        The last exception if all retries fail
    """
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            return await fn()
        except exceptions as e:
            last_error = e

            if attempt < max_retries - 1:
                # Exponential backoff: 1s, 2s, 4s, 8s... capped at max_delay
                delay = min(base_delay * (2 ** attempt), max_delay)

                logger.warn(
                    f"Retry attempt {attempt + 1}/{max_retries}",
                    error=str(e),
                    delay_seconds=delay,
                    function=fn.__name__ if hasattr(fn, "__name__") else "unknown",
                )

                await asyncio.sleep(delay)

    if last_error:
        raise last_error
    raise RuntimeError("Unexpected retry state")


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """
    Decorator for retrying async functions with exponential backoff.

    Usage:
        @with_retry(max_retries=3)
        async def fetch_data():
            ...
    """
    def decorator(fn: Callable[..., Any]):
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any):
            async def call():
                return await fn(*args, **kwargs)

            return await retry_async(
                call,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                exceptions=exceptions,
            )
        return wrapper
    return decorator
