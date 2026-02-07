"""
Smart Scheduling Service - AI-powered optimal posting time suggestions.

Provides intelligent scheduling recommendations based on:
- Platform-specific engagement patterns
- Day of week optimization
- Time zone awareness
- Historical best practices data
"""

from datetime import datetime, timedelta
from typing import Literal
from dataclasses import dataclass
from enum import Enum

from app.models.social_account import Platform


class EngagementLevel(str, Enum):
    """Engagement potential levels."""
    PEAK = "peak"          # Highest engagement potential
    HIGH = "high"          # Above average engagement
    MODERATE = "moderate"  # Average engagement
    LOW = "low"            # Below average engagement


@dataclass
class TimeSlot:
    """A suggested posting time slot."""
    datetime: datetime
    platform: Platform
    engagement_level: EngagementLevel
    score: float  # 0-100 engagement score
    reason: str   # Human-readable explanation


@dataclass
class SmartScheduleSuggestion:
    """Complete scheduling suggestion with multiple options."""
    platform: Platform
    best_time: TimeSlot
    alternative_times: list[TimeSlot]
    insights: list[str]


# Platform engagement patterns based on industry research
# Format: {day_of_week (0=Monday): {hour: score}}
ENGAGEMENT_PATTERNS = {
    Platform.INSTAGRAM: {
        # Monday
        0: {6: 45, 7: 55, 8: 60, 9: 65, 10: 70, 11: 85, 12: 75, 13: 70,
            14: 80, 15: 75, 16: 70, 17: 75, 18: 80, 19: 90, 20: 85, 21: 75, 22: 60},
        # Tuesday
        1: {6: 45, 7: 55, 8: 60, 9: 70, 10: 80, 11: 75, 12: 70, 13: 75,
            14: 85, 15: 80, 16: 75, 17: 80, 18: 85, 19: 90, 20: 80, 21: 70, 22: 55},
        # Wednesday
        2: {6: 50, 7: 60, 8: 65, 9: 70, 10: 75, 11: 90, 12: 80, 13: 75,
            14: 80, 15: 85, 16: 80, 17: 85, 18: 90, 19: 95, 20: 85, 21: 75, 22: 60},
        # Thursday
        3: {6: 45, 7: 55, 8: 60, 9: 65, 10: 80, 11: 85, 12: 75, 13: 70,
            14: 85, 15: 80, 16: 75, 17: 80, 18: 85, 19: 90, 20: 85, 21: 75, 22: 60},
        # Friday
        4: {6: 40, 7: 50, 8: 55, 9: 65, 10: 80, 11: 75, 12: 70, 13: 75,
            14: 85, 15: 80, 16: 75, 17: 90, 18: 85, 19: 80, 20: 70, 21: 60, 22: 50},
        # Saturday
        5: {8: 50, 9: 70, 10: 80, 11: 90, 12: 85, 13: 80, 14: 75, 15: 70,
            16: 65, 17: 70, 18: 75, 19: 85, 20: 80, 21: 70, 22: 55},
        # Sunday
        6: {8: 55, 9: 65, 10: 80, 11: 85, 12: 80, 13: 75, 14: 85, 15: 80,
            16: 75, 17: 80, 18: 85, 19: 95, 20: 85, 21: 75, 22: 60},
    },
    Platform.FACEBOOK: {
        0: {8: 60, 9: 75, 10: 70, 11: 65, 12: 70, 13: 85, 14: 75, 15: 70, 16: 80, 17: 75, 18: 70, 19: 65},
        1: {8: 65, 9: 80, 10: 75, 11: 70, 12: 75, 13: 85, 14: 80, 15: 75, 16: 85, 17: 80, 18: 75, 19: 70},
        2: {8: 70, 9: 85, 10: 80, 11: 75, 12: 80, 13: 90, 14: 85, 15: 90, 16: 85, 17: 80, 18: 75, 19: 70},
        3: {8: 65, 9: 80, 10: 75, 11: 70, 12: 85, 13: 80, 14: 85, 15: 90, 16: 85, 17: 80, 18: 75, 19: 70},
        4: {8: 60, 9: 75, 10: 70, 11: 80, 12: 75, 13: 70, 14: 85, 15: 80, 16: 75, 17: 70, 18: 65, 19: 60},
        5: {9: 70, 10: 75, 11: 80, 12: 90, 13: 85, 14: 80, 15: 85, 16: 80, 17: 75, 18: 70},
        6: {9: 75, 10: 80, 11: 85, 12: 90, 13: 85, 14: 80, 15: 85, 16: 80, 17: 75, 18: 70},
    },
    Platform.X: {
        0: {7: 60, 8: 80, 9: 85, 10: 75, 11: 70, 12: 90, 13: 85, 14: 75, 15: 70, 16: 75, 17: 85, 18: 80},
        1: {7: 65, 8: 85, 9: 90, 10: 80, 11: 75, 12: 85, 13: 80, 14: 75, 15: 75, 16: 80, 17: 90, 18: 85},
        2: {7: 70, 8: 85, 9: 90, 10: 85, 11: 80, 12: 90, 13: 85, 14: 80, 15: 80, 16: 85, 17: 90, 18: 85},
        3: {7: 65, 8: 80, 9: 85, 10: 80, 11: 75, 12: 85, 13: 80, 14: 75, 15: 75, 16: 80, 17: 85, 18: 80},
        4: {7: 60, 8: 75, 9: 80, 10: 75, 11: 70, 12: 80, 13: 75, 14: 70, 15: 70, 16: 75, 17: 80, 18: 75},
        5: {9: 70, 10: 75, 11: 80, 12: 85, 13: 80, 14: 75, 15: 80, 16: 75, 17: 70},
        6: {9: 75, 10: 80, 11: 85, 12: 90, 13: 85, 14: 80, 15: 85, 16: 80, 17: 75},
    },
    Platform.LINKEDIN: {
        0: {7: 75, 8: 90, 9: 85, 10: 95, 11: 85, 12: 90, 13: 80, 14: 75, 15: 70, 16: 65, 17: 80},
        1: {7: 80, 8: 95, 9: 90, 10: 95, 11: 85, 12: 90, 13: 80, 14: 75, 15: 70, 16: 65, 17: 85},
        2: {7: 85, 8: 95, 9: 90, 10: 100, 11: 90, 12: 95, 13: 85, 14: 80, 15: 75, 16: 70, 17: 85},
        3: {7: 80, 8: 90, 9: 85, 10: 95, 11: 85, 12: 90, 13: 80, 14: 85, 15: 80, 16: 70, 17: 85},
        4: {7: 70, 8: 80, 9: 75, 10: 85, 11: 80, 12: 75, 13: 70, 14: 65, 15: 60, 16: 55, 17: 70},
        # Weekend - lower engagement for B2B platform
        5: {10: 50, 11: 55, 12: 50},
        6: {10: 55, 11: 60, 12: 55, 17: 65, 18: 70},
    },
    Platform.TIKTOK: {
        0: {6: 55, 7: 70, 8: 65, 9: 60, 10: 65, 11: 70, 12: 85, 13: 80, 14: 75, 15: 90, 16: 85, 17: 80, 18: 85, 19: 95, 20: 90, 21: 100, 22: 90},
        1: {6: 50, 7: 65, 8: 60, 9: 75, 10: 70, 11: 75, 12: 85, 13: 80, 14: 75, 15: 85, 16: 80, 17: 85, 18: 90, 19: 100, 20: 95, 21: 95, 22: 85},
        2: {6: 55, 7: 70, 8: 65, 9: 70, 10: 75, 11: 80, 12: 90, 13: 85, 14: 80, 15: 90, 16: 85, 17: 90, 18: 95, 19: 100, 20: 95, 21: 90, 22: 80},
        3: {6: 50, 7: 65, 8: 60, 9: 65, 10: 70, 11: 75, 12: 85, 13: 80, 14: 75, 15: 90, 16: 85, 17: 90, 18: 95, 19: 100, 20: 95, 21: 100, 22: 90},
        4: {6: 45, 7: 60, 8: 55, 9: 60, 10: 65, 11: 70, 12: 80, 13: 75, 14: 80, 15: 95, 16: 90, 17: 100, 18: 95, 19: 95, 20: 90, 21: 100, 22: 95},
        5: {10: 75, 11: 90, 12: 85, 13: 80, 14: 85, 15: 90, 16: 95, 17: 95, 18: 100, 19: 100, 20: 95, 21: 100, 22: 95, 23: 85},
        6: {10: 80, 11: 90, 12: 85, 13: 85, 14: 90, 15: 95, 16: 90, 17: 95, 18: 100, 19: 100, 20: 95, 21: 95, 22: 90},
    },
    Platform.THREADS: {
        # Similar to Instagram but slightly different patterns
        0: {7: 55, 8: 65, 9: 70, 10: 80, 11: 85, 12: 80, 13: 85, 14: 80, 15: 75, 16: 70, 17: 75, 18: 85, 19: 90, 20: 85, 21: 75},
        1: {7: 60, 8: 70, 9: 75, 10: 85, 11: 80, 12: 75, 13: 85, 14: 85, 15: 80, 16: 75, 17: 80, 18: 90, 19: 95, 20: 85, 21: 75},
        2: {7: 65, 8: 75, 9: 80, 10: 85, 11: 90, 12: 85, 13: 90, 14: 85, 15: 85, 16: 80, 17: 85, 18: 90, 19: 100, 20: 90, 21: 80},
        3: {7: 60, 8: 70, 9: 75, 10: 85, 11: 85, 12: 80, 13: 85, 14: 80, 15: 80, 16: 75, 17: 80, 18: 90, 19: 95, 20: 85, 21: 75},
        4: {7: 55, 8: 65, 9: 70, 10: 80, 11: 80, 12: 75, 13: 80, 14: 85, 15: 80, 16: 75, 17: 85, 18: 85, 19: 85, 20: 75, 21: 65},
        5: {9: 70, 10: 80, 11: 85, 12: 90, 13: 85, 14: 80, 15: 75, 16: 80, 17: 85, 18: 90, 19: 95, 20: 85, 21: 75},
        6: {9: 75, 10: 85, 11: 90, 12: 90, 13: 85, 14: 90, 15: 85, 16: 85, 17: 90, 18: 95, 19: 100, 20: 90, 21: 80},
    },
    Platform.BLUESKY: {
        # Tech-savvy audience, similar to Twitter patterns
        0: {8: 70, 9: 85, 10: 80, 11: 75, 12: 90, 13: 85, 14: 75, 15: 70, 16: 75, 17: 80, 18: 90, 19: 85},
        1: {8: 75, 9: 90, 10: 85, 11: 80, 12: 90, 13: 85, 14: 80, 15: 75, 16: 80, 17: 85, 18: 95, 19: 90},
        2: {8: 80, 9: 90, 10: 90, 11: 85, 12: 95, 13: 90, 14: 85, 15: 80, 16: 85, 17: 90, 18: 95, 19: 90},
        3: {8: 75, 9: 85, 10: 85, 11: 80, 12: 90, 13: 85, 14: 80, 15: 75, 16: 80, 17: 85, 18: 90, 19: 85},
        4: {8: 70, 9: 80, 10: 80, 11: 75, 12: 85, 13: 80, 14: 75, 15: 70, 16: 75, 17: 85, 18: 85, 19: 80},
        5: {10: 70, 11: 80, 12: 85, 13: 80, 14: 75, 15: 80, 16: 75, 17: 80, 18: 85, 19: 80},
        6: {10: 75, 11: 85, 12: 90, 13: 85, 14: 80, 15: 85, 16: 80, 17: 85, 18: 90, 19: 85},
    },
}

# Platform-specific insights
PLATFORM_INSIGHTS = {
    Platform.INSTAGRAM: [
        "Instagram engagement peaks during lunch breaks and evening hours",
        "Wednesday and Sunday evenings see highest engagement",
        "Posting during commute times (7-9 AM, 5-7 PM) can boost visibility",
        "Stories perform best during evening hours",
    ],
    Platform.FACEBOOK: [
        "Facebook users are most active during midday and early afternoon",
        "Wednesday tends to be the highest engagement day",
        "Weekend posts often get more shares due to relaxed browsing",
        "Video content performs better in afternoon slots",
    ],
    Platform.X: [
        "X/Twitter sees high engagement during work breaks",
        "Weekday mornings and lunch hours are optimal",
        "News and trending topics perform best during business hours",
        "Threads and conversations peak during evening hours",
    ],
    Platform.LINKEDIN: [
        "LinkedIn is primarily active during business hours",
        "Tuesday through Thursday mornings see highest engagement",
        "Professional content performs best before 10 AM",
        "Avoid posting late evenings and weekends",
    ],
    Platform.TIKTOK: [
        "TikTok engagement peaks during evening and night hours",
        "Weekend evenings see the highest activity",
        "Younger audiences are most active after school/work hours",
        "Trending sounds and challenges boost visibility significantly",
    ],
    Platform.THREADS: [
        "Threads engagement follows Instagram patterns",
        "Text-based content performs well during commute times",
        "Evening hours see highest conversation rates",
        "Cross-posting from Instagram stories can boost reach",
    ],
    Platform.BLUESKY: [
        "Bluesky has a tech-savvy, early adopter audience",
        "Engagement patterns similar to Twitter",
        "Midday and evening posts perform well",
        "Long-form threads and discussions are well-received",
    ],
}


class SmartScheduler:
    """
    AI-powered smart scheduling service.

    Provides optimal posting time suggestions based on platform-specific
    engagement patterns and user behavior data.
    """

    def __init__(self):
        self.patterns = ENGAGEMENT_PATTERNS
        self.insights = PLATFORM_INSIGHTS

    def _get_engagement_level(self, score: float) -> EngagementLevel:
        """Convert numerical score to engagement level."""
        if score >= 90:
            return EngagementLevel.PEAK
        elif score >= 75:
            return EngagementLevel.HIGH
        elif score >= 60:
            return EngagementLevel.MODERATE
        else:
            return EngagementLevel.LOW

    def _get_reason(self, platform: Platform, day: int, hour: int, score: float) -> str:
        """Generate human-readable reason for the suggestion."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_name = days[day]

        level = self._get_engagement_level(score)

        if level == EngagementLevel.PEAK:
            return f"Peak engagement time for {platform.value} on {day_name}s"
        elif level == EngagementLevel.HIGH:
            return f"High engagement period - {day_name} {hour}:00 is popular"
        elif level == EngagementLevel.MODERATE:
            return f"Moderate engagement - good for consistent posting"
        else:
            return f"Lower engagement period - consider for less time-sensitive content"

    def get_best_times(
        self,
        platform: Platform,
        from_date: datetime | None = None,
        days_ahead: int = 7,
        num_suggestions: int = 5,
    ) -> SmartScheduleSuggestion:
        """
        Get the best posting times for a platform.

        Args:
            platform: Target social media platform
            from_date: Start date for suggestions (defaults to now)
            days_ahead: Number of days to look ahead
            num_suggestions: Number of time slots to suggest

        Returns:
            SmartScheduleSuggestion with best times and insights
        """
        if from_date is None:
            from_date = datetime.utcnow()

        platform_patterns = self.patterns.get(platform, {})
        if not platform_patterns:
            # Fallback to generic times if no pattern defined
            return self._get_generic_suggestion(platform, from_date)

        # Collect all possible time slots with scores
        slots: list[TimeSlot] = []

        for day_offset in range(days_ahead):
            check_date = from_date + timedelta(days=day_offset)
            day_of_week = check_date.weekday()

            day_patterns = platform_patterns.get(day_of_week, {})

            for hour, score in day_patterns.items():
                slot_datetime = check_date.replace(
                    hour=hour, minute=0, second=0, microsecond=0
                )

                # Skip times in the past
                if slot_datetime <= from_date:
                    continue

                slots.append(TimeSlot(
                    datetime=slot_datetime,
                    platform=platform,
                    engagement_level=self._get_engagement_level(score),
                    score=score,
                    reason=self._get_reason(platform, day_of_week, hour, score),
                ))

        # Sort by score (highest first)
        slots.sort(key=lambda x: x.score, reverse=True)

        if not slots:
            return self._get_generic_suggestion(platform, from_date)

        best_time = slots[0]
        alternative_times = slots[1:num_suggestions]

        return SmartScheduleSuggestion(
            platform=platform,
            best_time=best_time,
            alternative_times=alternative_times,
            insights=self.insights.get(platform, []),
        )

    def get_suggestions_for_platforms(
        self,
        platforms: list[Platform],
        from_date: datetime | None = None,
        days_ahead: int = 7,
    ) -> dict[Platform, SmartScheduleSuggestion]:
        """
        Get suggestions for multiple platforms.

        Args:
            platforms: List of platforms to get suggestions for
            from_date: Start date for suggestions
            days_ahead: Number of days to look ahead

        Returns:
            Dict mapping platform to its suggestion
        """
        return {
            platform: self.get_best_times(platform, from_date, days_ahead)
            for platform in platforms
        }

    def get_optimal_single_time(
        self,
        platforms: list[Platform],
        from_date: datetime | None = None,
        days_ahead: int = 7,
    ) -> TimeSlot:
        """
        Find the single best time to post across multiple platforms.

        Useful when cross-posting to find a time that works well for all.

        Args:
            platforms: List of platforms to optimize for
            from_date: Start date for suggestions
            days_ahead: Number of days to look ahead

        Returns:
            Single TimeSlot that's optimal across all platforms
        """
        if from_date is None:
            from_date = datetime.utcnow()

        # Collect scores for each time slot across all platforms
        time_scores: dict[datetime, list[float]] = {}

        for day_offset in range(days_ahead):
            check_date = from_date + timedelta(days=day_offset)
            day_of_week = check_date.weekday()

            for hour in range(6, 24):  # 6 AM to 11 PM
                slot_datetime = check_date.replace(
                    hour=hour, minute=0, second=0, microsecond=0
                )

                if slot_datetime <= from_date:
                    continue

                scores = []
                for platform in platforms:
                    platform_patterns = self.patterns.get(platform, {})
                    day_patterns = platform_patterns.get(day_of_week, {})
                    score = day_patterns.get(hour, 50)  # Default to 50 if not defined
                    scores.append(score)

                time_scores[slot_datetime] = scores

        # Calculate average score for each time
        best_time = None
        best_avg_score = 0

        for slot_datetime, scores in time_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score > best_avg_score:
                best_avg_score = avg_score
                best_time = slot_datetime

        if best_time is None:
            # Fallback
            best_time = from_date + timedelta(hours=2)
            best_avg_score = 50

        return TimeSlot(
            datetime=best_time,
            platform=platforms[0] if platforms else Platform.INSTAGRAM,
            engagement_level=self._get_engagement_level(best_avg_score),
            score=best_avg_score,
            reason=f"Optimal time across {len(platforms)} platforms",
        )

    def _get_generic_suggestion(
        self,
        platform: Platform,
        from_date: datetime,
    ) -> SmartScheduleSuggestion:
        """Fallback generic suggestion when no pattern data available."""
        # Default to tomorrow at 10 AM and 7 PM
        tomorrow_10am = (from_date + timedelta(days=1)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        tomorrow_7pm = (from_date + timedelta(days=1)).replace(
            hour=19, minute=0, second=0, microsecond=0
        )

        return SmartScheduleSuggestion(
            platform=platform,
            best_time=TimeSlot(
                datetime=tomorrow_10am,
                platform=platform,
                engagement_level=EngagementLevel.MODERATE,
                score=70,
                reason="Morning posts typically perform well",
            ),
            alternative_times=[
                TimeSlot(
                    datetime=tomorrow_7pm,
                    platform=platform,
                    engagement_level=EngagementLevel.HIGH,
                    score=80,
                    reason="Evening hours see increased engagement",
                ),
            ],
            insights=["Consider experimenting with different times to find your optimal schedule"],
        )


# Singleton instance
smart_scheduler = SmartScheduler()


def get_smart_suggestions(
    platforms: list[Platform],
    from_date: datetime | None = None,
) -> dict:
    """
    Get smart scheduling suggestions formatted for API response.

    Args:
        platforms: List of platforms to get suggestions for
        from_date: Start date (defaults to now)

    Returns:
        Dict with suggestions for each platform
    """
    suggestions = smart_scheduler.get_suggestions_for_platforms(platforms, from_date)

    result = {}
    for platform, suggestion in suggestions.items():
        result[platform.value.lower()] = {
            "platform": platform.value,
            "best_time": {
                "datetime": suggestion.best_time.datetime.isoformat(),
                "engagement_level": suggestion.best_time.engagement_level.value,
                "score": suggestion.best_time.score,
                "reason": suggestion.best_time.reason,
            },
            "alternative_times": [
                {
                    "datetime": slot.datetime.isoformat(),
                    "engagement_level": slot.engagement_level.value,
                    "score": slot.score,
                    "reason": slot.reason,
                }
                for slot in suggestion.alternative_times
            ],
            "insights": suggestion.insights,
        }

    return result


def get_optimal_cross_platform_time(
    platforms: list[Platform],
    from_date: datetime | None = None,
) -> dict:
    """
    Get the single best time to post across multiple platforms.

    Args:
        platforms: List of platforms to optimize for
        from_date: Start date (defaults to now)

    Returns:
        Dict with optimal time details
    """
    slot = smart_scheduler.get_optimal_single_time(platforms, from_date)

    return {
        "datetime": slot.datetime.isoformat(),
        "engagement_level": slot.engagement_level.value,
        "score": slot.score,
        "reason": slot.reason,
        "platforms": [p.value for p in platforms],
    }
