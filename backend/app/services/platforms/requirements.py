"""
Platform-specific posting requirements and validation.

Each platform has specific requirements for:
- Media types (image/video/text-only support)
- Content length limits
- Media file size limits
- Aspect ratios
- Number of media items
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from app.models.social_account import Platform


@dataclass
class MediaRequirements:
    """Media requirements for a platform."""
    # Image requirements
    max_images: int = 0
    max_image_size_mb: float = 0
    supported_image_formats: tuple = ()
    min_aspect_ratio: float = 0
    max_aspect_ratio: float = 0
    recommended_image_width: int = 0
    recommended_image_height: int = 0

    # Video requirements
    max_videos: int = 0
    max_video_size_mb: float = 0
    max_video_duration_seconds: int = 0
    min_video_duration_seconds: int = 0
    supported_video_formats: tuple = ()

    # General
    media_required: bool = False
    can_mix_media_types: bool = True


@dataclass
class ContentRequirements:
    """Content/text requirements for a platform."""
    max_caption_length: int = 0
    max_title_length: int = 0
    supports_hashtags: bool = True
    supports_mentions: bool = True
    supports_links: bool = True


@dataclass
class PlatformRequirements:
    """Complete requirements for a platform."""
    platform: Platform
    display_name: str
    media: MediaRequirements
    content: ContentRequirements
    notes: list[str]


# Platform-specific requirements
PLATFORM_REQUIREMENTS: dict[Platform, PlatformRequirements] = {
    Platform.INSTAGRAM: PlatformRequirements(
        platform=Platform.INSTAGRAM,
        display_name="Instagram",
        media=MediaRequirements(
            max_images=10,  # Carousel
            max_image_size_mb=8,
            supported_image_formats=("jpeg", "jpg", "png"),
            min_aspect_ratio=0.8,  # 4:5 portrait (STRICT)
            max_aspect_ratio=1.91,  # Landscape (STRICT)
            recommended_image_width=1080,
            recommended_image_height=1350,  # 4:5 for best engagement
            max_videos=1,
            max_video_size_mb=300,  # Auto-compressed if larger
            max_video_duration_seconds=90,  # Reels, Feed up to 60min
            min_video_duration_seconds=3,
            supported_video_formats=("mp4", "mov"),
            media_required=True,  # Instagram requires media
            can_mix_media_types=True,  # Carousels can mix
        ),
        content=ContentRequirements(
            max_caption_length=2200,
            supports_hashtags=True,
            supports_mentions=True,
            supports_links=False,  # Links in bio only
        ),
        notes=[
            "Media REQUIRED - text-only posts not supported",
            "STRICT aspect ratio: 0.8 (4:5) to 1.91 (landscape)",
            "9:16 content must use Story, not Feed",
            "Best engagement: 4:5 portrait (1080x1350)",
            "Carousel: all items must have same aspect ratio",
            "Reels: up to 90 seconds, 9:16 aspect ratio",
            "Stories: 1080x1920, disappear after 24 hours",
            "Up to 3 collaborators on posts/Reels",
        ],
    ),

    Platform.TIKTOK: PlatformRequirements(
        platform=Platform.TIKTOK,
        display_name="TikTok",
        media=MediaRequirements(
            max_images=35,  # Photo carousel
            max_image_size_mb=20,
            supported_image_formats=("jpeg", "jpg", "png", "webp"),
            min_aspect_ratio=0.5,
            max_aspect_ratio=2.0,
            recommended_image_width=1080,
            recommended_image_height=1920,  # 9:16
            max_videos=1,
            max_video_size_mb=4000,  # 4GB
            max_video_duration_seconds=600,  # 10 minutes
            min_video_duration_seconds=3,
            supported_video_formats=("mp4", "mov", "webm"),
            media_required=True,  # TikTok requires media
            can_mix_media_types=False,  # Cannot mix photos and videos
        ),
        content=ContentRequirements(
            max_caption_length=2200,  # Video caption
            max_title_length=90,  # Photo carousel (auto-truncated, hashtags stripped)
            supports_hashtags=True,
            supports_mentions=True,
            supports_links=False,
        ),
        notes=[
            "Cannot mix photos and videos in the same post",
            "Photo carousels: max 35 images, 90 char caption (auto-truncated)",
            "Videos: 3-600 seconds, 2200 char caption",
            "Best format: 9:16 vertical (1080x1920)",
            "Required settings: privacy_level, allow_comment, allow_duet, allow_stitch",
            "Video: H.264, 24-60fps, 720p minimum",
        ],
    ),

    Platform.X: PlatformRequirements(
        platform=Platform.X,
        display_name="X (Twitter)",
        media=MediaRequirements(
            max_images=4,
            max_image_size_mb=5,  # 15MB for GIFs
            supported_image_formats=("jpeg", "jpg", "png", "webp", "gif"),
            min_aspect_ratio=0.5,
            max_aspect_ratio=3.0,
            recommended_image_width=1200,
            recommended_image_height=675,  # 16:9
            max_videos=1,
            max_video_size_mb=512,
            max_video_duration_seconds=140,  # 2:20
            min_video_duration_seconds=1,  # 0.5 sec actual minimum
            supported_video_formats=("mp4", "mov"),
            media_required=False,  # X supports text-only
            can_mix_media_types=False,  # Images OR video, not both
        ),
        content=ContentRequirements(
            max_caption_length=280,  # Standard tweet
            supports_hashtags=True,
            supports_mentions=True,
            supports_links=True,
        ),
        notes=[
            "Text-only posts supported",
            "Max 4 images OR 1 video (not both)",
            "280 character limit",
            "GIFs: max 15MB, 1280x1080, counts as all 4 image slots",
            "Threads supported (multi-tweet sequences)",
            "Video: max 720p recommended, 30fps, H.264",
        ],
    ),

    Platform.THREADS: PlatformRequirements(
        platform=Platform.THREADS,
        display_name="Threads",
        media=MediaRequirements(
            max_images=20,  # Up to 20 images per post/carousel
            max_image_size_mb=8,
            supported_image_formats=("jpeg", "jpg", "png", "webp", "gif"),
            min_aspect_ratio=0.5,  # More flexible than Instagram
            max_aspect_ratio=2.0,
            recommended_image_width=1080,
            recommended_image_height=1350,  # 4:5 portrait recommended
            max_videos=1,
            max_video_size_mb=1000,  # 1 GB
            max_video_duration_seconds=300,  # 5 minutes
            min_video_duration_seconds=0,
            supported_video_formats=("mp4", "mov"),
            media_required=False,  # Threads supports text-only
            can_mix_media_types=True,  # Can mix in thread sequences
        ),
        content=ContentRequirements(
            max_caption_length=500,
            supports_hashtags=True,
            supports_mentions=True,
            supports_links=True,
        ),
        notes=[
            "Text-only posts supported",
            "500 character limit",
            "Up to 20 images per carousel",
            "Thread sequences supported (multiple connected posts)",
            "Best aspect ratio: 4:5 (1080x1350)",
        ],
    ),

    Platform.BLUESKY: PlatformRequirements(
        platform=Platform.BLUESKY,
        display_name="Bluesky",
        media=MediaRequirements(
            max_images=4,
            max_image_size_mb=1,  # Auto-compressed to ~1MB, max 2000x2000
            supported_image_formats=("jpeg", "jpg", "png", "webp", "gif"),
            min_aspect_ratio=0.5,
            max_aspect_ratio=2.0,
            recommended_image_width=1200,
            recommended_image_height=675,  # 16:9 recommended
            max_videos=1,
            max_video_size_mb=50,
            max_video_duration_seconds=60,
            min_video_duration_seconds=1,
            supported_video_formats=("mp4",),
            media_required=False,
            can_mix_media_types=False,
        ),
        content=ContentRequirements(
            max_caption_length=300,
            supports_hashtags=True,
            supports_mentions=True,
            supports_links=True,
        ),
        notes=[
            "Text-only posts supported",
            "300 character limit",
            "Max 4 images (auto-compressed to ~1MB)",
            "Alt text supported: up to 1000 characters",
            "URLs auto-generate link cards",
        ],
    ),

    Platform.FACEBOOK: PlatformRequirements(
        platform=Platform.FACEBOOK,
        display_name="Facebook",
        media=MediaRequirements(
            max_images=10,
            max_image_size_mb=10,
            supported_image_formats=("jpeg", "jpg", "png", "gif"),
            min_aspect_ratio=0.5,
            max_aspect_ratio=2.0,
            recommended_image_width=1200,
            recommended_image_height=630,
            max_videos=1,
            max_video_size_mb=4000,  # 4GB
            max_video_duration_seconds=14400,  # 4 hours
            min_video_duration_seconds=1,
            supported_video_formats=("mp4", "mov"),
            media_required=False,
            can_mix_media_types=True,
        ),
        content=ContentRequirements(
            max_caption_length=63206,  # Very long
            supports_hashtags=True,
            supports_mentions=True,
            supports_links=True,
        ),
        notes=[
            "Text-only posts supported",
            "Very flexible with content and media",
        ],
    ),

    Platform.LINKEDIN: PlatformRequirements(
        platform=Platform.LINKEDIN,
        display_name="LinkedIn",
        media=MediaRequirements(
            max_images=20,
            max_image_size_mb=8,
            supported_image_formats=("jpeg", "jpg", "png", "gif"),
            min_aspect_ratio=0.5,
            max_aspect_ratio=2.0,
            recommended_image_width=1200,
            recommended_image_height=627,
            max_videos=1,
            max_video_size_mb=5000,  # 5GB
            max_video_duration_seconds=600,  # 10 minutes
            min_video_duration_seconds=3,
            supported_video_formats=("mp4", "mov"),
            media_required=False,
            can_mix_media_types=False,
        ),
        content=ContentRequirements(
            max_caption_length=3000,
            supports_hashtags=True,
            supports_mentions=True,
            supports_links=True,
        ),
        notes=[
            "Text-only posts supported",
            "Professional tone recommended",
            "Supports PDF documents up to 100MB",
        ],
    ),
}


@dataclass
class ValidationError:
    """Validation error details."""
    field: str
    message: str
    platform: Platform


@dataclass
class ValidationResult:
    """Result of content validation."""
    valid: bool
    errors: list[ValidationError]
    warnings: list[str]


def validate_content_for_platform(
    platform: Platform,
    content: str = "",
    media_urls: list[str] = None,
    media_types: list[str] = None,  # "image" or "video"
) -> ValidationResult:
    """
    Validate content against platform requirements.

    Args:
        platform: Target platform
        content: Text content/caption
        media_urls: List of media URLs
        media_types: List of media types ("image" or "video")

    Returns:
        ValidationResult with errors and warnings
    """
    requirements = PLATFORM_REQUIREMENTS.get(platform)
    if not requirements:
        return ValidationResult(
            valid=False,
            errors=[ValidationError("platform", f"Unknown platform: {platform}", platform)],
            warnings=[],
        )

    errors = []
    warnings = []
    media_urls = media_urls or []
    media_types = media_types or []

    # Check media requirement
    if requirements.media.media_required and not media_urls:
        errors.append(ValidationError(
            "media",
            f"{requirements.display_name} requires media - text-only posts not supported",
            platform,
        ))

    # Check content length
    if content and len(content) > requirements.content.max_caption_length:
        errors.append(ValidationError(
            "content",
            f"Caption too long: {len(content)} chars (max {requirements.content.max_caption_length})",
            platform,
        ))

    # Check media count
    image_count = media_types.count("image") if media_types else len(media_urls)
    video_count = media_types.count("video") if media_types else 0

    if image_count > requirements.media.max_images:
        errors.append(ValidationError(
            "media",
            f"Too many images: {image_count} (max {requirements.media.max_images})",
            platform,
        ))

    if video_count > requirements.media.max_videos:
        errors.append(ValidationError(
            "media",
            f"Too many videos: {video_count} (max {requirements.media.max_videos})",
            platform,
        ))

    # Check mixed media
    if not requirements.media.can_mix_media_types and image_count > 0 and video_count > 0:
        errors.append(ValidationError(
            "media",
            f"{requirements.display_name} cannot mix photos and videos in the same post",
            platform,
        ))

    # Add platform-specific warnings
    if platform == Platform.INSTAGRAM and not media_urls:
        pass  # Already covered by media_required
    elif platform == Platform.TIKTOK and image_count > 0 and len(content) > 90:
        warnings.append(f"TikTok photo carousel captions are limited to 90 characters (yours: {len(content)})")
    elif platform == Platform.X and len(content) > 280:
        errors.append(ValidationError(
            "content",
            f"Tweet too long: {len(content)} chars (max 280)",
            platform,
        ))

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def get_platform_requirements(platform: Platform) -> PlatformRequirements | None:
    """Get requirements for a specific platform."""
    return PLATFORM_REQUIREMENTS.get(platform)


def get_all_requirements() -> dict[Platform, PlatformRequirements]:
    """Get requirements for all platforms."""
    return PLATFORM_REQUIREMENTS.copy()
