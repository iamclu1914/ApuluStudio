"""
Centralized exception handling for the Apulu Suite API.

This module provides a comprehensive exception hierarchy for handling
errors throughout the application with proper context preservation.

Exception Hierarchy:
    ApuluError (base)
    ├── ApiError (HTTP API errors with status codes)
    │   ├── NotFoundError (404)
    │   ├── ValidationError (400)
    │   ├── UnauthorizedError (401)
    │   ├── ForbiddenError (403)
    │   ├── ConflictError (409)
    │   ├── RateLimitError (429)
    │   └── ExternalServiceError (502)
    ├── PlatformError (social platform specific)
    │   ├── PlatformAuthenticationError
    │   ├── PlatformRateLimitError
    │   └── PlatformAPIError
    ├── AuthenticationError (auth/token issues)
    ├── MediaProcessingError (image/video processing)
    ├── SchedulingError (post scheduling issues)
    └── NetworkError (HTTP/connection issues)
"""

from typing import Any


# =============================================================================
# Base Exception
# =============================================================================

class ApuluError(Exception):
    """
    Base exception for all Apulu Suite errors.

    All custom exceptions should inherit from this class to enable
    consistent error handling throughout the application.

    Attributes:
        message: Human-readable error description
        detail: Additional error context (dict, list, or string)
        is_operational: True if this is an expected/handled error
    """

    def __init__(
        self,
        message: str,
        detail: Any = None,
        is_operational: bool = True,
    ):
        self.message = message
        self.detail = detail
        self.is_operational = is_operational
        super().__init__(message)

    def to_dict(self) -> dict:
        """Convert exception to a dictionary for JSON serialization."""
        result = {
            "error": self.__class__.__name__,
            "message": self.message,
        }
        if self.detail:
            result["detail"] = self.detail
        return result


# =============================================================================
# HTTP API Exceptions
# =============================================================================

class ApiError(ApuluError):
    """
    Base API error with HTTP status code support.

    Use for errors that should be returned as HTTP responses.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        detail: Any = None,
        is_operational: bool = True,
    ):
        self.status_code = status_code
        super().__init__(message, detail, is_operational)

    def to_dict(self) -> dict:
        result = super().to_dict()
        result["status_code"] = self.status_code
        return result


class NotFoundError(ApiError):
    """Resource not found error (404)."""

    def __init__(self, resource: str, resource_id: str | None = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(404, message)
        self.resource = resource
        self.resource_id = resource_id


class ValidationError(ApiError):
    """
    Validation error (400).

    Use for invalid input data, missing required fields, or format errors.
    """

    def __init__(self, message: str, detail: Any = None, field: str | None = None):
        super().__init__(400, message, detail)
        self.field = field


class UnauthorizedError(ApiError):
    """Unauthorized error (401) - authentication required or failed."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(401, message)


class ForbiddenError(ApiError):
    """Forbidden error (403) - authenticated but insufficient permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(403, message)


class ConflictError(ApiError):
    """Conflict error (409) - resource conflict or duplicate."""

    def __init__(self, message: str):
        super().__init__(409, message)


class RateLimitError(ApiError):
    """
    Rate limit exceeded error (429).

    Attributes:
        retry_after: Seconds until the rate limit resets (if available)
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ):
        super().__init__(429, message)
        self.retry_after = retry_after

    def to_dict(self) -> dict:
        result = super().to_dict()
        if self.retry_after:
            result["retry_after"] = self.retry_after
        return result


class ExternalServiceError(ApiError):
    """
    External service error (502).

    Use when an external API or service fails.
    """

    def __init__(self, service: str, message: str | None = None):
        msg = f"External service error: {service}"
        if message:
            msg = f"{msg} - {message}"
        super().__init__(502, msg, is_operational=False)
        self.service = service


# =============================================================================
# Platform-Specific Exceptions
# =============================================================================

class PlatformError(ApuluError):
    """
    Base exception for social media platform errors.

    Use for errors returned by platform APIs (Instagram, Facebook, etc.)

    Attributes:
        platform: Name of the platform (e.g., "instagram", "facebook")
        platform_error_code: Error code from the platform's API
        status_code: HTTP status code from the platform's response
        raw_response: Raw response from the platform's API
    """

    def __init__(
        self,
        message: str,
        platform: str,
        platform_error_code: str | int | None = None,
        status_code: int | None = None,
        raw_response: dict | None = None,
    ):
        super().__init__(message, detail=raw_response)
        self.platform = platform
        self.platform_error_code = platform_error_code
        self.status_code = status_code
        self.raw_response = raw_response

    def to_dict(self) -> dict:
        result = super().to_dict()
        result["platform"] = self.platform
        if self.platform_error_code:
            result["platform_error_code"] = self.platform_error_code
        if self.status_code:
            result["status_code"] = self.status_code
        return result


class PlatformAuthenticationError(PlatformError):
    """
    Platform authentication/authorization error.

    Raised when platform credentials are invalid, expired, or revoked.
    """

    def __init__(
        self,
        platform: str,
        message: str | None = None,
        raw_response: dict | None = None,
    ):
        msg = message or f"{platform} authentication failed: Token may be expired or revoked"
        super().__init__(
            message=msg,
            platform=platform,
            status_code=401,
            raw_response=raw_response,
        )


class PlatformRateLimitError(PlatformError):
    """
    Platform-specific rate limit error.

    Raised when a platform's API rate limit is exceeded.
    """

    def __init__(
        self,
        platform: str,
        message: str | None = None,
        retry_after: int | None = None,
        raw_response: dict | None = None,
    ):
        msg = message or f"{platform} API rate limit exceeded"
        super().__init__(
            message=msg,
            platform=platform,
            status_code=429,
            raw_response=raw_response,
        )
        self.retry_after = retry_after


class PlatformAPIError(PlatformError):
    """
    Generic platform API error.

    Use for platform API errors that don't fit other categories.
    """

    def __init__(
        self,
        platform: str,
        message: str,
        platform_error_code: str | int | None = None,
        status_code: int | None = None,
        raw_response: dict | None = None,
    ):
        super().__init__(
            message=message,
            platform=platform,
            platform_error_code=platform_error_code,
            status_code=status_code,
            raw_response=raw_response,
        )


# =============================================================================
# Authentication Exceptions
# =============================================================================

class AuthenticationError(ApuluError):
    """
    Authentication/authorization error.

    Use for OAuth failures, token issues, or credential problems.

    Attributes:
        platform: Platform where auth failed (if applicable)
        error_code: Authentication error code
    """

    def __init__(
        self,
        message: str,
        platform: str | None = None,
        error_code: str | None = None,
    ):
        super().__init__(message)
        self.platform = platform
        self.error_code = error_code

    def to_dict(self) -> dict:
        result = super().to_dict()
        if self.platform:
            result["platform"] = self.platform
        if self.error_code:
            result["error_code"] = self.error_code
        return result


# =============================================================================
# Media Processing Exceptions
# =============================================================================

class MediaProcessingError(ApuluError):
    """
    Media (image/video) processing error.

    Raised when media fails validation, conversion, or optimization.

    Attributes:
        media_type: Type of media (image, video)
        operation: The operation that failed (resize, compress, convert, etc.)
        file_info: Information about the file being processed
    """

    def __init__(
        self,
        message: str,
        media_type: str | None = None,
        operation: str | None = None,
        file_info: dict | None = None,
    ):
        super().__init__(message, detail=file_info)
        self.media_type = media_type
        self.operation = operation
        self.file_info = file_info

    def to_dict(self) -> dict:
        result = super().to_dict()
        if self.media_type:
            result["media_type"] = self.media_type
        if self.operation:
            result["operation"] = self.operation
        return result


class MediaDownloadError(MediaProcessingError):
    """Failed to download media from URL."""

    def __init__(self, url: str, reason: str | None = None):
        msg = f"Failed to download media from URL"
        if reason:
            msg = f"{msg}: {reason}"
        super().__init__(msg, operation="download")
        self.url = url


# =============================================================================
# Scheduling Exceptions
# =============================================================================

class SchedulingError(ApuluError):
    """
    Post scheduling error.

    Raised when scheduling, publishing, or managing scheduled posts fails.

    Attributes:
        post_id: ID of the post being scheduled
        platform: Target platform (if applicable)
        scheduled_time: The scheduled time (if applicable)
    """

    def __init__(
        self,
        message: str,
        post_id: str | None = None,
        platform: str | None = None,
        scheduled_time: str | None = None,
    ):
        detail = {}
        if post_id:
            detail["post_id"] = post_id
        if platform:
            detail["platform"] = platform
        if scheduled_time:
            detail["scheduled_time"] = scheduled_time

        super().__init__(message, detail=detail if detail else None)
        self.post_id = post_id
        self.platform = platform
        self.scheduled_time = scheduled_time


# =============================================================================
# Network Exceptions
# =============================================================================

class NetworkError(ApuluError):
    """
    Network/HTTP communication error.

    Raised for connection failures, timeouts, DNS errors, etc.

    Attributes:
        url: The URL that failed
        error_type: Type of network error (timeout, connection, dns, etc.)
    """

    def __init__(
        self,
        message: str,
        url: str | None = None,
        error_type: str | None = None,
    ):
        super().__init__(message, is_operational=False)
        self.url = url
        self.error_type = error_type

    def to_dict(self) -> dict:
        result = super().to_dict()
        if self.url:
            result["url"] = self.url
        if self.error_type:
            result["error_type"] = self.error_type
        return result



