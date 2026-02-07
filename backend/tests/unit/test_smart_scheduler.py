"""
Unit tests for SmartScheduler service.

Tests cover:
- Engagement level calculation
- Best time suggestions
- Cross-platform optimization
- Fallback behavior for unknown platforms
"""

from datetime import datetime, timedelta

import pytest

from app.models.social_account import Platform
from app.services.smart_scheduler import (
    EngagementLevel,
    SmartScheduler,
    TimeSlot,
    get_optimal_cross_platform_time,
    get_smart_suggestions,
    ENGAGEMENT_PATTERNS,
    PLATFORM_INSIGHTS,
)


class TestEngagementLevelCalculation:
    """Tests for engagement level determination."""

    @pytest.fixture
    def scheduler(self):
        return SmartScheduler()

    @pytest.mark.unit
    def test_peak_engagement_level(self, scheduler):
        """Scores >= 90 should return PEAK engagement level."""
        assert scheduler._get_engagement_level(100) == EngagementLevel.PEAK
        assert scheduler._get_engagement_level(95) == EngagementLevel.PEAK
        assert scheduler._get_engagement_level(90) == EngagementLevel.PEAK

    @pytest.mark.unit
    def test_high_engagement_level(self, scheduler):
        """Scores 75-89 should return HIGH engagement level."""
        assert scheduler._get_engagement_level(89) == EngagementLevel.HIGH
        assert scheduler._get_engagement_level(80) == EngagementLevel.HIGH
        assert scheduler._get_engagement_level(75) == EngagementLevel.HIGH

    @pytest.mark.unit
    def test_moderate_engagement_level(self, scheduler):
        """Scores 60-74 should return MODERATE engagement level."""
        assert scheduler._get_engagement_level(74) == EngagementLevel.MODERATE
        assert scheduler._get_engagement_level(65) == EngagementLevel.MODERATE
        assert scheduler._get_engagement_level(60) == EngagementLevel.MODERATE

    @pytest.mark.unit
    def test_low_engagement_level(self, scheduler):
        """Scores < 60 should return LOW engagement level."""
        assert scheduler._get_engagement_level(59) == EngagementLevel.LOW
        assert scheduler._get_engagement_level(30) == EngagementLevel.LOW
        assert scheduler._get_engagement_level(0) == EngagementLevel.LOW


class TestBestTimeSuggestions:
    """Tests for best time suggestion generation."""

    @pytest.fixture
    def scheduler(self):
        return SmartScheduler()

    @pytest.mark.unit
    def test_get_best_times_returns_suggestion(self, scheduler):
        """Should return a SmartScheduleSuggestion for valid platform."""
        suggestion = scheduler.get_best_times(
            Platform.INSTAGRAM,
            from_date=datetime(2024, 1, 15, 8, 0),  # Monday 8 AM
            days_ahead=7,
        )

        assert suggestion.platform == Platform.INSTAGRAM
        assert suggestion.best_time is not None
        assert isinstance(suggestion.best_time, TimeSlot)
        assert len(suggestion.alternative_times) > 0
        assert len(suggestion.insights) > 0

    @pytest.mark.unit
    def test_best_time_is_in_future(self, scheduler):
        """Best time should always be after the from_date."""
        from_date = datetime(2024, 1, 15, 12, 0)

        suggestion = scheduler.get_best_times(
            Platform.FACEBOOK,
            from_date=from_date,
            days_ahead=7,
        )

        assert suggestion.best_time.datetime > from_date

    @pytest.mark.unit
    def test_alternative_times_are_sorted_by_score(self, scheduler):
        """Alternative times should be sorted by engagement score (descending)."""
        suggestion = scheduler.get_best_times(
            Platform.X,
            from_date=datetime(2024, 1, 15, 0, 0),
            days_ahead=7,
            num_suggestions=5,
        )

        # Best time should have highest score
        if suggestion.alternative_times:
            assert suggestion.best_time.score >= suggestion.alternative_times[0].score

    @pytest.mark.unit
    def test_num_suggestions_limits_alternatives(self, scheduler):
        """num_suggestions should limit the number of alternative times."""
        suggestion = scheduler.get_best_times(
            Platform.LINKEDIN,
            from_date=datetime(2024, 1, 15, 0, 0),
            days_ahead=14,
            num_suggestions=3,
        )

        # Should have at most (num_suggestions - 1) alternatives
        assert len(suggestion.alternative_times) <= 2

    @pytest.mark.unit
    def test_days_ahead_limits_range(self, scheduler):
        """Suggestions should not exceed days_ahead range."""
        from_date = datetime(2024, 1, 15, 0, 0)
        days_ahead = 3

        suggestion = scheduler.get_best_times(
            Platform.TIKTOK,
            from_date=from_date,
            days_ahead=days_ahead,
        )

        max_date = from_date + timedelta(days=days_ahead)

        assert suggestion.best_time.datetime <= max_date
        for alt in suggestion.alternative_times:
            assert alt.datetime <= max_date


class TestCrossPlatformOptimization:
    """Tests for cross-platform time optimization."""

    @pytest.fixture
    def scheduler(self):
        return SmartScheduler()

    @pytest.mark.unit
    def test_optimal_single_time_returns_timeslot(self, scheduler):
        """Should return a single TimeSlot for multiple platforms."""
        platforms = [Platform.INSTAGRAM, Platform.FACEBOOK, Platform.X]

        slot = scheduler.get_optimal_single_time(
            platforms,
            from_date=datetime(2024, 1, 15, 8, 0),
            days_ahead=7,
        )

        assert isinstance(slot, TimeSlot)
        assert slot.datetime is not None
        assert slot.score > 0

    @pytest.mark.unit
    def test_optimal_time_considers_all_platforms(self, scheduler):
        """Optimal time reason should mention all platforms."""
        platforms = [Platform.INSTAGRAM, Platform.LINKEDIN]

        slot = scheduler.get_optimal_single_time(
            platforms,
            from_date=datetime(2024, 1, 15, 8, 0),
        )

        assert "2 platforms" in slot.reason

    @pytest.mark.unit
    def test_suggestions_for_multiple_platforms(self, scheduler):
        """Should return suggestions for each platform."""
        platforms = [Platform.INSTAGRAM, Platform.THREADS, Platform.BLUESKY]

        suggestions = scheduler.get_suggestions_for_platforms(
            platforms,
            from_date=datetime(2024, 1, 15, 8, 0),
        )

        assert len(suggestions) == len(platforms)
        for platform in platforms:
            assert platform in suggestions


class TestFallbackBehavior:
    """Tests for fallback behavior with unknown/missing data."""

    @pytest.fixture
    def scheduler(self):
        return SmartScheduler()

    @pytest.mark.unit
    def test_generic_suggestion_for_empty_patterns(self, scheduler):
        """Should return generic suggestion when no pattern data exists."""
        from_date = datetime(2024, 1, 15, 8, 0)

        # Test the internal fallback method
        suggestion = scheduler._get_generic_suggestion(Platform.INSTAGRAM, from_date)

        assert suggestion is not None
        assert suggestion.best_time is not None
        assert "experimenting" in suggestion.insights[0].lower()


class TestPublicAPIFunctions:
    """Tests for public API helper functions."""

    @pytest.mark.unit
    def test_get_smart_suggestions_returns_dict(self):
        """get_smart_suggestions should return properly formatted dict."""
        platforms = [Platform.INSTAGRAM, Platform.X]

        result = get_smart_suggestions(platforms)

        assert isinstance(result, dict)
        assert "instagram" in result
        assert "x" in result

    @pytest.mark.unit
    def test_get_smart_suggestions_structure(self):
        """Result should have correct structure for each platform."""
        result = get_smart_suggestions([Platform.FACEBOOK])

        facebook_data = result.get("facebook")
        assert facebook_data is not None
        assert "platform" in facebook_data
        assert "best_time" in facebook_data
        assert "alternative_times" in facebook_data
        assert "insights" in facebook_data

        # Check best_time structure
        best_time = facebook_data["best_time"]
        assert "datetime" in best_time
        assert "engagement_level" in best_time
        assert "score" in best_time
        assert "reason" in best_time

    @pytest.mark.unit
    def test_get_optimal_cross_platform_time_structure(self):
        """get_optimal_cross_platform_time should return correct structure."""
        platforms = [Platform.INSTAGRAM, Platform.THREADS]

        result = get_optimal_cross_platform_time(platforms)

        assert "datetime" in result
        assert "engagement_level" in result
        assert "score" in result
        assert "reason" in result
        assert "platforms" in result
        assert set(result["platforms"]) == {"INSTAGRAM", "THREADS"}


class TestEngagementPatterns:
    """Tests to verify engagement pattern data integrity."""

    @pytest.mark.unit
    def test_all_platforms_have_patterns(self):
        """All main platforms should have engagement patterns."""
        expected_platforms = [
            Platform.INSTAGRAM,
            Platform.FACEBOOK,
            Platform.X,
            Platform.LINKEDIN,
            Platform.TIKTOK,
            Platform.THREADS,
            Platform.BLUESKY,
        ]

        for platform in expected_platforms:
            assert platform in ENGAGEMENT_PATTERNS, f"Missing pattern for {platform}"

    @pytest.mark.unit
    def test_all_platforms_have_insights(self):
        """All main platforms should have insights."""
        expected_platforms = [
            Platform.INSTAGRAM,
            Platform.FACEBOOK,
            Platform.X,
            Platform.LINKEDIN,
            Platform.TIKTOK,
            Platform.THREADS,
            Platform.BLUESKY,
        ]

        for platform in expected_platforms:
            assert platform in PLATFORM_INSIGHTS, f"Missing insights for {platform}"
            assert len(PLATFORM_INSIGHTS[platform]) > 0

    @pytest.mark.unit
    def test_engagement_scores_are_valid(self):
        """All engagement scores should be between 0 and 100."""
        for platform, days in ENGAGEMENT_PATTERNS.items():
            for day, hours in days.items():
                for hour, score in hours.items():
                    assert 0 <= score <= 100, (
                        f"Invalid score {score} for {platform} day {day} hour {hour}"
                    )
