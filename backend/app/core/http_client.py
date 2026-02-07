"""
Shared HTTP client with connection pooling for efficient external API calls.

This module provides a singleton httpx.AsyncClient instance that enables:
- Connection reuse across requests (connection pooling)
- Configurable timeouts
- Automatic retry with exponential backoff
- Proper lifecycle management for FastAPI applications
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import httpx

from app.core.logger import logger
from app.core.exceptions import (
    PlatformError,
    RateLimitError,
    AuthenticationError,
    NetworkError,
)


# Default timeout configuration
DEFAULT_CONNECT_TIMEOUT = 10.0  # seconds
DEFAULT_READ_TIMEOUT = 30.0  # seconds
DEFAULT_WRITE_TIMEOUT = 30.0  # seconds
DEFAULT_POOL_TIMEOUT = 10.0  # seconds

# Connection pool limits
DEFAULT_MAX_CONNECTIONS = 100
DEFAULT_MAX_KEEPALIVE_CONNECTIONS = 20

# Retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_DELAY = 1.0  # seconds
DEFAULT_RETRY_MAX_DELAY = 30.0  # seconds

# Status codes that should trigger a retry
RETRYABLE_STATUS_CODES = {502, 503, 504, 429}


class HTTPClientManager:
    """
    Manages a shared httpx.AsyncClient instance with connection pooling.

    This class implements the singleton pattern to ensure a single HTTP client
    is shared across the application for efficient connection reuse.
    """

    _instance: "HTTPClientManager | None" = None
    _client: httpx.AsyncClient | None = None
    _lock: asyncio.Lock | None = None

    def __new__(cls) -> "HTTPClientManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._lock = asyncio.Lock()
        return cls._instance

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client, raising an error if not initialized."""
        if self._client is None:
            raise RuntimeError(
                "HTTP client not initialized. Call await init_client() first or use get_http_client() dependency."
            )
        return self._client

    async def init_client(
        self,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
        read_timeout: float = DEFAULT_READ_TIMEOUT,
        write_timeout: float = DEFAULT_WRITE_TIMEOUT,
        pool_timeout: float = DEFAULT_POOL_TIMEOUT,
        max_connections: int = DEFAULT_MAX_CONNECTIONS,
        max_keepalive_connections: int = DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
    ) -> httpx.AsyncClient:
        """
        Initialize the shared HTTP client with connection pooling.

        Args:
            connect_timeout: Timeout for establishing connections
            read_timeout: Timeout for reading response data
            write_timeout: Timeout for writing request data
            pool_timeout: Timeout for acquiring a connection from the pool
            max_connections: Maximum number of connections in the pool
            max_keepalive_connections: Maximum number of idle keepalive connections

        Returns:
            The initialized AsyncClient instance
        """
        async with self._lock:
            if self._client is not None:
                return self._client

            timeout = httpx.Timeout(
                connect=connect_timeout,
                read=read_timeout,
                write=write_timeout,
                pool=pool_timeout,
            )

            limits = httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections,
            )

            self._client = httpx.AsyncClient(
                timeout=timeout,
                limits=limits,
                follow_redirects=True,
                http2=True,  # Enable HTTP/2 for better multiplexing
            )

            logger.info(
                "HTTP client initialized",
                max_connections=max_connections,
                max_keepalive=max_keepalive_connections,
            )

            return self._client

    async def close_client(self) -> None:
        """Close the HTTP client and release all connections."""
        async with self._lock:
            if self._client is not None:
                await self._client.aclose()
                self._client = None
                logger.info("HTTP client closed")

    def is_initialized(self) -> bool:
        """Check if the HTTP client is initialized."""
        return self._client is not None


# Global manager instance
_manager = HTTPClientManager()


async def init_http_client(**kwargs: Any) -> httpx.AsyncClient:
    """
    Initialize the global HTTP client.

    Should be called during application startup (e.g., in FastAPI lifespan).
    """
    return await _manager.init_client(**kwargs)


async def close_http_client() -> None:
    """
    Close the global HTTP client.

    Should be called during application shutdown (e.g., in FastAPI lifespan).
    """
    await _manager.close_client()


def get_http_client() -> httpx.AsyncClient:
    """
    Get the shared HTTP client instance.

    Use this as a FastAPI dependency for routes that need HTTP client access.

    Example:
        @router.get("/fetch")
        async def fetch_data(client: httpx.AsyncClient = Depends(get_http_client)):
            response = await client.get("https://api.example.com/data")
            return response.json()
    """
    return _manager.client


@asynccontextmanager
async def get_http_client_context() -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Context manager for getting the HTTP client.

    Creates a temporary client if the global one isn't initialized.
    Useful for standalone scripts or tests.
    """
    if _manager.is_initialized():
        yield _manager.client
    else:
        # Create a temporary client
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=DEFAULT_CONNECT_TIMEOUT,
                read=DEFAULT_READ_TIMEOUT,
                write=DEFAULT_WRITE_TIMEOUT,
            ),
            follow_redirects=True,
        ) as client:
            yield client


async def request_with_retry(
    method: str,
    url: str,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_RETRY_BASE_DELAY,
    max_delay: float = DEFAULT_RETRY_MAX_DELAY,
    client: httpx.AsyncClient | None = None,
    **kwargs: Any,
) -> httpx.Response:
    """
    Make an HTTP request with automatic retry and exponential backoff.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        client: Optional HTTP client (uses global client if not provided)
        **kwargs: Additional arguments passed to the request

    Returns:
        httpx.Response object

    Raises:
        PlatformError: If all retries fail
        RateLimitError: If rate limit exceeded and retries exhausted
        AuthenticationError: If authentication fails (401/403)
        NetworkError: If network connection fails
    """
    http_client = client or _manager.client
    last_error: Exception | None = None
    last_response: httpx.Response | None = None

    for attempt in range(max_retries):
        try:
            response = await http_client.request(method, url, **kwargs)

            # Check for authentication errors (don't retry)
            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed: Invalid or expired credentials",
                    platform="unknown",
                )
            if response.status_code == 403:
                raise AuthenticationError(
                    "Authorization failed: Insufficient permissions",
                    platform="unknown",
                )

            # Check for rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if attempt < max_retries - 1:
                    delay = float(retry_after) if retry_after else min(base_delay * (2 ** attempt), max_delay)
                    logger.warn(
                        f"Rate limited, retrying in {delay}s",
                        attempt=attempt + 1,
                        url=url,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise RateLimitError(
                    f"Rate limit exceeded for {url}",
                    retry_after=int(retry_after) if retry_after else None,
                )

            # Check for retryable server errors
            if response.status_code in RETRYABLE_STATUS_CODES:
                last_response = response
                if attempt < max_retries - 1:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warn(
                        f"Server error {response.status_code}, retrying in {delay}s",
                        attempt=attempt + 1,
                        url=url,
                    )
                    await asyncio.sleep(delay)
                    continue

            return response

        except httpx.ConnectError as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warn(
                    f"Connection error, retrying in {delay}s",
                    attempt=attempt + 1,
                    url=url,
                    error=str(e),
                )
                await asyncio.sleep(delay)
                continue
            raise NetworkError(f"Failed to connect to {url}: {e}")

        except httpx.TimeoutException as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warn(
                    f"Request timeout, retrying in {delay}s",
                    attempt=attempt + 1,
                    url=url,
                )
                await asyncio.sleep(delay)
                continue
            raise NetworkError(f"Request to {url} timed out after {max_retries} attempts")

        except (AuthenticationError, RateLimitError):
            # Don't retry auth errors
            raise

        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warn(
                    f"Request failed, retrying in {delay}s",
                    attempt=attempt + 1,
                    url=url,
                    error=str(e),
                )
                await asyncio.sleep(delay)
                continue

    # All retries exhausted
    if last_response is not None:
        raise PlatformError(
            f"Request failed after {max_retries} attempts: HTTP {last_response.status_code}",
            platform="unknown",
            status_code=last_response.status_code,
        )
    if last_error is not None:
        raise NetworkError(f"Request failed after {max_retries} attempts: {last_error}")

    raise PlatformError(f"Request to {url} failed after {max_retries} attempts", platform="unknown")
