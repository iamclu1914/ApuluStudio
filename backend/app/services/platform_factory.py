"""
Platform Factory - Service instantiation for social media platforms.

Provides centralized platform service creation with configuration management
and connection pooling support.
"""

from app.models.social_account import Platform
from app.services.platforms.bluesky import BlueskyService
from app.services.platforms.meta import MetaService
from app.services.platforms.linkedin import LinkedInService
from app.services.platforms.late import LateService
from app.core.config import get_settings
from app.core.logger import logger


class PlatformFactory:
    """
    Factory for creating and managing platform service instances.

    Handles platform-specific configuration and provides a unified interface
    for obtaining platform services based on configuration settings.
    """

    _instance: "PlatformFactory | None" = None
    _services: dict[Platform, object] | None = None

    def __new__(cls) -> "PlatformFactory":
        """Singleton pattern for shared service instances."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services = None
        return cls._instance

    def __init__(self):
        """Initialize platform services if not already done."""
        if self._services is None:
            self._initialize_services()

    def _initialize_services(self) -> None:
        """
        Initialize all platform service instances based on configuration.

        Uses LATE API for supported platforms when configured,
        otherwise falls back to direct platform APIs.
        """
        settings = get_settings()
        use_late = bool(settings.late_api_key)

        self._services = {
            Platform.BLUESKY: BlueskyService(),
            Platform.LINKEDIN: LinkedInService(),
            # Facebook always uses direct Meta API (LATE doesn't support Facebook)
            Platform.FACEBOOK: MetaService(Platform.FACEBOOK),
        }

        # Instagram, Threads, TikTok, X: Use LATE if configured, else direct APIs
        if use_late:
            logger.info("Using LATE API for Instagram, Threads, TikTok, and X")
            self._services[Platform.INSTAGRAM] = LateService(Platform.INSTAGRAM)
            self._services[Platform.THREADS] = LateService(Platform.THREADS)
            self._services[Platform.TIKTOK] = LateService(Platform.TIKTOK)
            self._services[Platform.X] = LateService(Platform.X)
        else:
            logger.info("Using direct APIs for Instagram and Threads (LATE not configured)")
            # Fall back to direct APIs (requires verification/setup)
            self._services[Platform.INSTAGRAM] = MetaService(Platform.INSTAGRAM)
            self._services[Platform.THREADS] = MetaService(Platform.THREADS)
            # Note: TikTok and X require LATE API - no direct fallback available

    def get_service(self, platform: Platform) -> object | None:
        """
        Get the platform service for a specific platform.

        Args:
            platform: The target social media platform

        Returns:
            Platform service instance or None if platform not supported
        """
        return self._services.get(platform)

    def get_supported_platforms(self) -> list[Platform]:
        """
        Get list of all supported platforms.

        Returns:
            List of Platform enum values that have configured services
        """
        return list(self._services.keys())

    def is_platform_supported(self, platform: Platform) -> bool:
        """
        Check if a platform is supported.

        Args:
            platform: The platform to check

        Returns:
            True if the platform has a configured service
        """
        return platform in self._services

    def refresh_services(self) -> None:
        """
        Refresh all platform services (useful for configuration changes).

        Forces reinitialization of all platform service instances.
        """
        self._services = None
        self._initialize_services()
        logger.info("Platform services refreshed")
