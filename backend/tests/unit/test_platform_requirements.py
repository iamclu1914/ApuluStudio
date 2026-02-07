"""
Unit tests for platform requirements validation.

Tests cover:
- Content length validation
- Media requirement validation
- Mixed media type detection
- Platform-specific rules
"""

import pytest

from app.models.social_account import Platform
from app.services.platforms.requirements import (
    PLATFORM_REQUIREMENTS,
    ValidationError,
    ValidationResult,
    get_all_requirements,
    get_platform_requirements,
    validate_content_for_platform,
)


class TestContentLengthValidation:
    """Tests for content/caption length validation."""

    @pytest.mark.unit
    def test_valid_instagram_caption(self):
        """Instagram allows up to 2200 characters."""
        result = validate_content_for_platform(
            platform=Platform.INSTAGRAM,
            content="A" * 2000,
            media_urls=["https://example.com/image.jpg"],
            media_types=["image"],
        )

        assert result.valid is True
        assert len(result.errors) == 0

    @pytest.mark.unit
    def test_instagram_caption_too_long(self):
        """Instagram should reject captions over 2200 chars."""
        result = validate_content_for_platform(
            platform=Platform.INSTAGRAM,
            content="A" * 2500,
            media_urls=["https://example.com/image.jpg"],
            media_types=["image"],
        )

        assert result.valid is False
        assert any("Caption too long" in e.message for e in result.errors)

    @pytest.mark.unit
    def test_twitter_280_char_limit(self):
        """X/Twitter should enforce 280 character limit."""
        result = validate_content_for_platform(
            platform=Platform.X,
            content="A" * 300,
        )

        assert result.valid is False
        assert any("Tweet too long" in e.message for e in result.errors)

    @pytest.mark.unit
    def test_threads_500_char_limit(self):
        """Threads should allow up to 500 characters."""
        result = validate_content_for_platform(
            platform=Platform.THREADS,
            content="A" * 500,
        )

        assert result.valid is True

    @pytest.mark.unit
    def test_bluesky_300_char_limit(self):
        """Bluesky should allow up to 300 characters."""
        result = validate_content_for_platform(
            platform=Platform.BLUESKY,
            content="A" * 301,
        )

        assert result.valid is False
        assert any("Caption too long" in e.message for e in result.errors)


class TestMediaRequirementValidation:
    """Tests for media requirement validation."""

    @pytest.mark.unit
    def test_instagram_requires_media(self):
        """Instagram should require at least one media item."""
        result = validate_content_for_platform(
            platform=Platform.INSTAGRAM,
            content="Text only post",
            media_urls=[],
        )

        assert result.valid is False
        assert any("requires media" in e.message.lower() for e in result.errors)

    @pytest.mark.unit
    def test_tiktok_requires_media(self):
        """TikTok should require media."""
        result = validate_content_for_platform(
            platform=Platform.TIKTOK,
            content="Text only",
            media_urls=[],
        )

        assert result.valid is False
        assert any("requires media" in e.message.lower() for e in result.errors)

    @pytest.mark.unit
    def test_twitter_allows_text_only(self):
        """X/Twitter should allow text-only posts."""
        result = validate_content_for_platform(
            platform=Platform.X,
            content="Just text, no media",
            media_urls=[],
        )

        assert result.valid is True

    @pytest.mark.unit
    def test_threads_allows_text_only(self):
        """Threads should allow text-only posts."""
        result = validate_content_for_platform(
            platform=Platform.THREADS,
            content="Text without media",
            media_urls=[],
        )

        assert result.valid is True

    @pytest.mark.unit
    def test_linkedin_allows_text_only(self):
        """LinkedIn should allow text-only posts."""
        result = validate_content_for_platform(
            platform=Platform.LINKEDIN,
            content="Professional update without media",
            media_urls=[],
        )

        assert result.valid is True


class TestMediaCountValidation:
    """Tests for media count limits."""

    @pytest.mark.unit
    def test_instagram_max_10_images(self):
        """Instagram carousel should allow max 10 images."""
        result = validate_content_for_platform(
            platform=Platform.INSTAGRAM,
            content="Carousel post",
            media_urls=["img.jpg"] * 11,
            media_types=["image"] * 11,
        )

        assert result.valid is False
        assert any("Too many images" in e.message for e in result.errors)

    @pytest.mark.unit
    def test_twitter_max_4_images(self):
        """X/Twitter should allow max 4 images."""
        result = validate_content_for_platform(
            platform=Platform.X,
            content="Tweet with images",
            media_urls=["img.jpg"] * 5,
            media_types=["image"] * 5,
        )

        assert result.valid is False
        assert any("Too many images" in e.message for e in result.errors)

    @pytest.mark.unit
    def test_bluesky_max_4_images(self):
        """Bluesky should allow max 4 images."""
        result = validate_content_for_platform(
            platform=Platform.BLUESKY,
            content="Post with images",
            media_urls=["img.jpg"] * 4,
            media_types=["image"] * 4,
        )

        assert result.valid is True


class TestMixedMediaValidation:
    """Tests for mixed media type validation."""

    @pytest.mark.unit
    def test_twitter_cannot_mix_media(self):
        """X/Twitter should not allow mixing images and videos."""
        result = validate_content_for_platform(
            platform=Platform.X,
            content="Mixed media tweet",
            media_urls=["img.jpg", "video.mp4"],
            media_types=["image", "video"],
        )

        assert result.valid is False
        assert any("cannot mix" in e.message.lower() for e in result.errors)

    @pytest.mark.unit
    def test_tiktok_cannot_mix_media(self):
        """TikTok should not allow mixing photos and videos."""
        result = validate_content_for_platform(
            platform=Platform.TIKTOK,
            content="Mixed post",
            media_urls=["img.jpg", "video.mp4"],
            media_types=["image", "video"],
        )

        assert result.valid is False
        assert any("cannot mix" in e.message.lower() for e in result.errors)

    @pytest.mark.unit
    def test_instagram_allows_carousel_mixing(self):
        """Instagram carousel can mix media types."""
        # Instagram allows mixing in carousels
        reqs = get_platform_requirements(Platform.INSTAGRAM)
        assert reqs.media.can_mix_media_types is True


class TestTikTokSpecificWarnings:
    """Tests for TikTok-specific warnings."""

    @pytest.mark.unit
    def test_tiktok_photo_caption_warning(self):
        """TikTok photo carousel should warn about 90 char caption limit."""
        result = validate_content_for_platform(
            platform=Platform.TIKTOK,
            content="A" * 100,  # Over 90 chars
            media_urls=["img.jpg"],
            media_types=["image"],
        )

        assert any("90 characters" in w for w in result.warnings)


class TestRequirementsData:
    """Tests to verify requirements data integrity."""

    @pytest.mark.unit
    def test_all_platforms_have_requirements(self):
        """All Platform enum values should have requirements defined."""
        for platform in Platform:
            reqs = get_platform_requirements(platform)
            assert reqs is not None, f"Missing requirements for {platform}"

    @pytest.mark.unit
    def test_get_all_requirements_returns_all(self):
        """get_all_requirements should return all platform requirements."""
        all_reqs = get_all_requirements()

        assert len(all_reqs) == len(Platform)
        for platform in Platform:
            assert platform in all_reqs

    @pytest.mark.unit
    def test_requirements_have_display_names(self):
        """All requirements should have display names."""
        for platform, reqs in PLATFORM_REQUIREMENTS.items():
            assert reqs.display_name is not None
            assert len(reqs.display_name) > 0

    @pytest.mark.unit
    def test_requirements_have_notes(self):
        """All requirements should have at least one note."""
        for platform, reqs in PLATFORM_REQUIREMENTS.items():
            assert reqs.notes is not None
            assert len(reqs.notes) > 0, f"No notes for {platform}"


class TestValidationResult:
    """Tests for ValidationResult structure."""

    @pytest.mark.unit
    def test_valid_result_has_no_errors(self):
        """Valid result should have empty errors list."""
        result = validate_content_for_platform(
            platform=Platform.FACEBOOK,
            content="Simple post",
        )

        assert result.valid is True
        assert len(result.errors) == 0

    @pytest.mark.unit
    def test_invalid_result_has_errors(self):
        """Invalid result should have populated errors list."""
        result = validate_content_for_platform(
            platform=Platform.INSTAGRAM,
            content="No media",
            media_urls=[],
        )

        assert result.valid is False
        assert len(result.errors) > 0
        assert all(isinstance(e, ValidationError) for e in result.errors)

    @pytest.mark.unit
    def test_validation_error_has_platform(self):
        """ValidationError should include the platform."""
        result = validate_content_for_platform(
            platform=Platform.X,
            content="A" * 300,
        )

        for error in result.errors:
            assert error.platform == Platform.X
