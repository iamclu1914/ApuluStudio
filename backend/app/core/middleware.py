"""FastAPI middleware for logging, error handling, rate limiting, and security headers."""

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import (
    ApuluError,
    ApiError,
    PlatformError,
    PlatformRateLimitError,
    AuthenticationError,
    MediaProcessingError,
    SchedulingError,
    NetworkError,
    RateLimitError,
)
from app.core.logger import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses.

    Implements OWASP security header recommendations.
    See: https://owasp.org/www-project-secure-headers/
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS filter in older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information sent with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Prevent caching of sensitive data
        # Only apply to API responses, not static files
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        # Content Security Policy for API (restrictive since we don't serve HTML)
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"

        # Strict Transport Security (only effective over HTTPS)
        # max-age=31536000 = 1 year
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Permissions Policy - disable unnecessary browser features
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all HTTP requests with timing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        request_id = request.headers.get("X-Request-ID", "")

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log request (skip health checks to reduce noise)
        if request.url.path not in ("/health", "/"):
            logger.request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                request_id=request_id,
                client_ip=request.client.host if request.client else "unknown",
            )

        return response


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized exception handling with support for custom exception hierarchy."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)

        except ApiError as e:
            # HTTP API errors - return with appropriate status code
            if e.status_code >= 500:
                logger.error(
                    f"API Error: {e.message}",
                    status_code=e.status_code,
                    path=request.url.path,
                    error_type=e.__class__.__name__,
                )

            response_data = {
                "success": False,
                "error": e.message,
                "error_type": e.__class__.__name__,
            }
            if e.detail:
                response_data["detail"] = e.detail

            headers = {}
            if isinstance(e, RateLimitError) and e.retry_after:
                headers["Retry-After"] = str(e.retry_after)

            return JSONResponse(
                status_code=e.status_code,
                content=response_data,
                headers=headers if headers else None,
            )

        except PlatformError as e:
            # Social media platform errors
            logger.error(
                f"Platform Error: {e.message}",
                platform=e.platform,
                platform_error_code=e.platform_error_code,
                status_code=e.status_code,
                path=request.url.path,
            )

            response_data = {
                "success": False,
                "error": e.message,
                "error_type": e.__class__.__name__,
                "platform": e.platform,
            }
            if e.platform_error_code:
                response_data["platform_error_code"] = e.platform_error_code

            # Determine HTTP status code based on platform error type
            http_status = 502  # Default to bad gateway for platform errors
            headers = {}

            if isinstance(e, PlatformRateLimitError):
                http_status = 429
                if e.retry_after:
                    headers["Retry-After"] = str(e.retry_after)
            elif e.status_code == 401:
                http_status = 401
            elif e.status_code == 403:
                http_status = 403

            return JSONResponse(
                status_code=http_status,
                content=response_data,
                headers=headers if headers else None,
            )

        except AuthenticationError as e:
            # Authentication/authorization errors
            logger.warn(
                f"Authentication Error: {e.message}",
                platform=e.platform,
                error_code=e.error_code,
                path=request.url.path,
            )

            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "error": e.message,
                    "error_type": e.__class__.__name__,
                    "platform": e.platform,
                },
            )

        except MediaProcessingError as e:
            # Media processing errors
            logger.error(
                f"Media Processing Error: {e.message}",
                media_type=e.media_type,
                operation=e.operation,
                path=request.url.path,
            )

            response_data = {
                "success": False,
                "error": e.message,
                "error_type": e.__class__.__name__,
            }
            if e.media_type:
                response_data["media_type"] = e.media_type
            if e.operation:
                response_data["operation"] = e.operation

            return JSONResponse(
                status_code=422,  # Unprocessable Entity
                content=response_data,
            )

        except SchedulingError as e:
            # Scheduling errors
            logger.error(
                f"Scheduling Error: {e.message}",
                post_id=e.post_id,
                platform=e.platform,
                scheduled_time=e.scheduled_time,
                path=request.url.path,
            )

            response_data = {
                "success": False,
                "error": e.message,
                "error_type": e.__class__.__name__,
            }
            if e.detail:
                response_data["detail"] = e.detail

            return JSONResponse(
                status_code=400,
                content=response_data,
            )

        except NetworkError as e:
            # Network/connection errors
            logger.error(
                f"Network Error: {e.message}",
                url=e.url,
                error_type=e.error_type,
                path=request.url.path,
            )

            return JSONResponse(
                status_code=503,  # Service Unavailable
                content={
                    "success": False,
                    "error": e.message,
                    "error_type": e.__class__.__name__,
                },
            )

        except ApuluError as e:
            # Base Apulu errors (catch-all for custom exceptions)
            log_method = logger.error if not e.is_operational else logger.warn
            log_method(
                f"Apulu Error: {e.message}",
                error_type=e.__class__.__name__,
                path=request.url.path,
            )

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": e.message,
                    "error_type": e.__class__.__name__,
                    "detail": e.detail,
                },
            )

        except Exception as e:
            # Unexpected errors - log full details
            logger.error(
                "Unhandled exception",
                error=e,
                error_type=e.__class__.__name__,
                path=request.url.path,
                method=request.method,
            )

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Internal server error",
                },
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter middleware."""

    def __init__(
        self,
        app,
        max_requests: int = 100,
        window_seconds: int = 60,
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.exclude_paths = exclude_paths or ["/health", "/", "/api/docs", "/api/redoc"]
        self.requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier from request."""
        # Use X-Forwarded-For if behind proxy, otherwise client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit."""
        now = time.time()
        window_start = now - self.window_seconds

        # Get requests in current window
        client_requests = self.requests[client_id]
        recent_requests = [t for t in client_requests if t > window_start]

        # Update stored requests
        self.requests[client_id] = recent_requests

        if len(recent_requests) >= self.max_requests:
            return True

        # Add current request
        recent_requests.append(now)
        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        client_id = self._get_client_id(request)

        if self._is_rate_limited(client_id):
            logger.warn(
                "Rate limit exceeded",
                client_id=client_id,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Rate limit exceeded. Please try again later.",
                },
                headers={
                    "Retry-After": str(self.window_seconds),
                },
            )

        return await call_next(request)
