"""
Media processing service for social media platform compliance.

Automatically resizes, crops, and optimizes images/videos to meet
each platform's specific requirements.
"""

import io
import httpx
from PIL import Image
from typing import Literal
from dataclasses import dataclass
from enum import Enum

from app.models.social_account import Platform


class AspectRatio(str, Enum):
    """Common social media aspect ratios."""
    SQUARE = "1:1"           # 1080x1080
    PORTRAIT = "4:5"         # 1080x1350 (Instagram/Facebook)
    LANDSCAPE = "1.91:1"     # 1080x566 (Facebook link preview)
    WIDE = "16:9"            # 1920x1080 (YouTube, Twitter)
    VERTICAL = "9:16"        # 1080x1920 (Stories, Reels, TikTok)


class InstagramPostType(str, Enum):
    """Instagram content types with different requirements."""
    FEED = "feed"            # Standard feed posts (square, portrait, landscape)
    STORY = "story"          # Stories (vertical 9:16)
    REEL = "reel"            # Reels (vertical 9:16, video)


@dataclass
class PlatformMediaSpec:
    """Media specifications for a platform."""
    max_width: int
    max_height: int
    max_file_size_mb: float
    preferred_aspect_ratio: AspectRatio
    supported_formats: list[str]
    min_width: int = 320
    min_height: int = 320


# Platform-specific media requirements
PLATFORM_SPECS: dict[Platform, PlatformMediaSpec] = {
    Platform.INSTAGRAM: PlatformMediaSpec(
        max_width=1080,
        max_height=1350,  # 4:5 portrait max for feed
        max_file_size_mb=8.0,
        preferred_aspect_ratio=AspectRatio.SQUARE,
        supported_formats=["jpeg", "jpg", "png"],
        min_width=320,
        min_height=320,
    ),
    Platform.FACEBOOK: PlatformMediaSpec(
        max_width=1200,
        max_height=1200,
        max_file_size_mb=8.0,
        preferred_aspect_ratio=AspectRatio.SQUARE,
        supported_formats=["jpeg", "jpg", "png", "gif"],
        min_width=200,
        min_height=200,
    ),
    Platform.THREADS: PlatformMediaSpec(
        max_width=1080,
        max_height=1350,
        max_file_size_mb=8.0,
        preferred_aspect_ratio=AspectRatio.SQUARE,
        supported_formats=["jpeg", "jpg", "png"],
        min_width=320,
        min_height=320,
    ),
    Platform.TIKTOK: PlatformMediaSpec(
        max_width=1080,
        max_height=1920,  # 9:16 vertical
        max_file_size_mb=10.0,
        preferred_aspect_ratio=AspectRatio.VERTICAL,
        supported_formats=["jpeg", "jpg", "png"],
        min_width=720,
        min_height=1280,
    ),
    Platform.X: PlatformMediaSpec(
        max_width=1200,
        max_height=1200,
        max_file_size_mb=5.0,
        preferred_aspect_ratio=AspectRatio.WIDE,
        supported_formats=["jpeg", "jpg", "png", "gif", "webp"],
        min_width=200,
        min_height=200,
    ),
    Platform.BLUESKY: PlatformMediaSpec(
        max_width=2000,
        max_height=2000,
        max_file_size_mb=1.0,  # Bluesky has 1MB limit
        preferred_aspect_ratio=AspectRatio.SQUARE,
        supported_formats=["jpeg", "jpg", "png"],
        min_width=200,
        min_height=200,
    ),
    Platform.LINKEDIN: PlatformMediaSpec(
        max_width=1200,
        max_height=1200,
        max_file_size_mb=8.0,
        preferred_aspect_ratio=AspectRatio.LANDSCAPE,
        supported_formats=["jpeg", "jpg", "png", "gif"],
        min_width=200,
        min_height=200,
    ),
}

# Instagram post type specific specs
INSTAGRAM_POST_TYPE_SPECS: dict[InstagramPostType, PlatformMediaSpec] = {
    InstagramPostType.FEED: PlatformMediaSpec(
        max_width=1080,
        max_height=1350,  # 4:5 portrait max
        max_file_size_mb=8.0,
        preferred_aspect_ratio=AspectRatio.SQUARE,
        supported_formats=["jpeg", "jpg", "png"],
        min_width=320,
        min_height=320,
    ),
    InstagramPostType.STORY: PlatformMediaSpec(
        max_width=1080,
        max_height=1920,  # 9:16 vertical
        max_file_size_mb=8.0,
        preferred_aspect_ratio=AspectRatio.VERTICAL,
        supported_formats=["jpeg", "jpg", "png"],
        min_width=720,
        min_height=1280,
    ),
    InstagramPostType.REEL: PlatformMediaSpec(
        max_width=1080,
        max_height=1920,  # 9:16 vertical
        max_file_size_mb=8.0,
        preferred_aspect_ratio=AspectRatio.VERTICAL,
        supported_formats=["jpeg", "jpg", "png", "mp4"],  # Reels are primarily video
        min_width=720,
        min_height=1280,
    ),
}


@dataclass
class ProcessedMedia:
    """Result of media processing."""
    data: bytes
    format: str
    width: int
    height: int
    file_size_bytes: int
    was_modified: bool
    modifications: list[str]


class MediaProcessor:
    """
    Processes media files to comply with social platform requirements.

    Features:
    - Automatic resizing to platform max dimensions
    - Smart cropping to maintain aspect ratio
    - Compression to meet file size limits
    - Format conversion when needed
    - Instagram post type support (Feed, Story, Reel)
    """

    def __init__(
        self,
        platform: Platform,
        instagram_post_type: InstagramPostType | None = None,
    ):
        """
        Initialize processor for a specific platform.

        Args:
            platform: Target social media platform
            instagram_post_type: For Instagram, specify Feed, Story, or Reel
        """
        self.platform = platform
        self.instagram_post_type = instagram_post_type

        # Use Instagram post type specs if applicable
        if platform == Platform.INSTAGRAM and instagram_post_type:
            self.spec = INSTAGRAM_POST_TYPE_SPECS.get(instagram_post_type)
        else:
            self.spec = PLATFORM_SPECS.get(platform)

        if not self.spec:
            raise ValueError(f"No media spec defined for platform: {platform}")

    async def process_image_from_url(self, image_url: str) -> ProcessedMedia:
        """
        Download and process an image from URL.

        Args:
            image_url: URL of the image to process

        Returns:
            ProcessedMedia with optimized image data
        """
        from app.core.http_client import get_http_client, get_http_client_context
        from app.core.exceptions import MediaDownloadError

        try:
            # Use shared HTTP client for connection pooling
            try:
                client = get_http_client()
                response = await client.get(image_url, timeout=60.0)
            except RuntimeError:
                # Fallback to temporary client if global client not initialized
                async with get_http_client_context() as client:
                    response = await client.get(image_url, timeout=60.0)

            response.raise_for_status()
            image_data = response.content
        except httpx.TimeoutException:
            raise MediaDownloadError(url=image_url, reason="Request timed out")
        except httpx.HTTPStatusError as e:
            raise MediaDownloadError(url=image_url, reason=f"HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            raise MediaDownloadError(url=image_url, reason=str(e))

        return self.process_image(image_data)

    def process_image(self, image_data: bytes) -> ProcessedMedia:
        """
        Process image data to comply with platform requirements.

        Args:
            image_data: Raw image bytes

        Returns:
            ProcessedMedia with optimized image data
        """
        modifications = []

        # Open image
        img = Image.open(io.BytesIO(image_data))
        original_format = img.format or "JPEG"
        original_size = len(image_data)

        # Convert to RGB if necessary (for JPEG output)
        if img.mode in ("RGBA", "P", "LA"):
            # Create white background for transparency
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background
            modifications.append("converted_to_rgb")
        elif img.mode != "RGB":
            img = img.convert("RGB")
            modifications.append("converted_to_rgb")

        # Resize if exceeds max dimensions
        if img.width > self.spec.max_width or img.height > self.spec.max_height:
            img = self._resize_image(img)
            modifications.append(f"resized_to_{img.width}x{img.height}")

        # Ensure minimum dimensions
        if img.width < self.spec.min_width or img.height < self.spec.min_height:
            img = self._upscale_image(img)
            modifications.append(f"upscaled_to_{img.width}x{img.height}")

        # Compress to meet file size limit
        output_data, output_format = self._compress_image(
            img,
            self.spec.max_file_size_mb
        )

        if len(output_data) < original_size:
            modifications.append(f"compressed_{original_size}b_to_{len(output_data)}b")

        return ProcessedMedia(
            data=output_data,
            format=output_format,
            width=img.width,
            height=img.height,
            file_size_bytes=len(output_data),
            was_modified=len(modifications) > 0,
            modifications=modifications,
        )

    def _resize_image(self, img: Image.Image) -> Image.Image:
        """
        Resize image to fit within max dimensions while maintaining aspect ratio.
        """
        # Calculate scale factor to fit within bounds
        width_ratio = self.spec.max_width / img.width
        height_ratio = self.spec.max_height / img.height
        scale = min(width_ratio, height_ratio)

        if scale < 1:
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return img

    def _upscale_image(self, img: Image.Image) -> Image.Image:
        """
        Upscale image to meet minimum dimensions.
        """
        width_ratio = self.spec.min_width / img.width
        height_ratio = self.spec.min_height / img.height
        scale = max(width_ratio, height_ratio)

        if scale > 1:
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return img

    def _compress_image(
        self,
        img: Image.Image,
        max_size_mb: float,
        min_quality: int = 60
    ) -> tuple[bytes, str]:
        """
        Compress image to meet file size limit.

        Uses progressive quality reduction to achieve target size.
        """
        max_size_bytes = int(max_size_mb * 1024 * 1024)

        # Start with high quality
        quality = 95
        output_format = "JPEG"

        while quality >= min_quality:
            buffer = io.BytesIO()
            img.save(
                buffer,
                format=output_format,
                quality=quality,
                optimize=True,
                progressive=True
            )
            data = buffer.getvalue()

            if len(data) <= max_size_bytes:
                return data, output_format.lower()

            quality -= 5

        # If still too large, resize further
        scale = 0.9
        resized_img = img
        while scale > 0.3:
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            resized_img.save(
                buffer,
                format=output_format,
                quality=min_quality,
                optimize=True,
                progressive=True
            )
            data = buffer.getvalue()

            if len(data) <= max_size_bytes:
                return data, output_format.lower()

            scale -= 0.1

        # Return best effort
        buffer = io.BytesIO()
        resized_img.save(buffer, format=output_format, quality=min_quality, optimize=True)
        return buffer.getvalue(), output_format.lower()

    def crop_to_aspect_ratio(
        self,
        img: Image.Image,
        aspect_ratio: AspectRatio
    ) -> Image.Image:
        """
        Crop image to a specific aspect ratio (center crop).
        """
        # Parse aspect ratio
        if aspect_ratio == AspectRatio.SQUARE:
            target_ratio = 1.0
        elif aspect_ratio == AspectRatio.PORTRAIT:
            target_ratio = 4 / 5
        elif aspect_ratio == AspectRatio.LANDSCAPE:
            target_ratio = 1.91
        elif aspect_ratio == AspectRatio.WIDE:
            target_ratio = 16 / 9
        elif aspect_ratio == AspectRatio.VERTICAL:
            target_ratio = 9 / 16
        else:
            return img

        current_ratio = img.width / img.height

        if abs(current_ratio - target_ratio) < 0.01:
            return img  # Already correct ratio

        if current_ratio > target_ratio:
            # Image is too wide, crop width
            new_width = int(img.height * target_ratio)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            # Image is too tall, crop height
            new_height = int(img.width / target_ratio)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))

        return img


async def process_media_for_platforms(
    image_url: str,
    platforms: list[Platform],
) -> dict[Platform, ProcessedMedia]:
    """
    Process a single image for multiple platforms.

    Args:
        image_url: URL of the source image
        platforms: List of target platforms

    Returns:
        Dict mapping platform to processed media
    """
    from app.core.http_client import get_http_client, get_http_client_context
    from app.core.exceptions import MediaDownloadError
    from app.core.logger import logger

    # Download image once using shared client
    try:
        try:
            client = get_http_client()
            response = await client.get(image_url, timeout=60.0)
        except RuntimeError:
            # Fallback to temporary client
            async with get_http_client_context() as client:
                response = await client.get(image_url, timeout=60.0)

        response.raise_for_status()
        image_data = response.content
    except httpx.TimeoutException:
        raise MediaDownloadError(url=image_url, reason="Request timed out")
    except httpx.HTTPStatusError as e:
        raise MediaDownloadError(url=image_url, reason=f"HTTP {e.response.status_code}")
    except httpx.RequestError as e:
        raise MediaDownloadError(url=image_url, reason=str(e))

    results = {}
    for platform in platforms:
        try:
            processor = MediaProcessor(platform)
            results[platform] = processor.process_image(image_data)
        except Exception as e:
            # Log error but continue with other platforms
            logger.error(f"Failed to process image for {platform}", error=str(e))

    return results


def get_platform_media_requirements(
    platform: Platform,
    instagram_post_type: InstagramPostType | None = None,
) -> dict:
    """
    Get human-readable media requirements for a platform.

    Useful for displaying to users in the UI.

    Args:
        platform: Target platform
        instagram_post_type: For Instagram, specify Feed, Story, or Reel
    """
    # Use Instagram post type specs if applicable
    if platform == Platform.INSTAGRAM and instagram_post_type:
        spec = INSTAGRAM_POST_TYPE_SPECS.get(instagram_post_type)
    else:
        spec = PLATFORM_SPECS.get(platform)

    if not spec:
        return {"error": f"Unknown platform: {platform}"}

    result = {
        "platform": platform.value,
        "max_dimensions": f"{spec.max_width}x{spec.max_height}",
        "max_file_size": f"{spec.max_file_size_mb}MB",
        "min_dimensions": f"{spec.min_width}x{spec.min_height}",
        "preferred_aspect_ratio": spec.preferred_aspect_ratio.value,
        "supported_formats": spec.supported_formats,
    }

    if instagram_post_type:
        result["instagram_post_type"] = instagram_post_type.value

    return result


def get_all_instagram_requirements() -> dict:
    """
    Get media requirements for all Instagram post types.

    Returns a dict with Feed, Story, and Reel requirements.
    """
    return {
        post_type.value: get_platform_media_requirements(
            Platform.INSTAGRAM, post_type
        )
        for post_type in InstagramPostType
    }
