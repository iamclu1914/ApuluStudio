from datetime import datetime, date
from pydantic import BaseModel

from app.models.social_account import Platform


class PlatformStats(BaseModel):
    """Stats for a single platform."""
    platform: Platform
    followers: int
    following: int
    posts_count: int
    engagement_rate: float


class OverviewStats(BaseModel):
    """High-level dashboard statistics."""
    total_followers: int
    total_engagement: int  # likes + comments
    posts_this_week: int
    engagement_rate: float  # percentage
    platforms: list[PlatformStats]


class GrowthDataPoint(BaseModel):
    """Single data point for growth chart."""
    date: date
    followers: int
    engagement: int


class GrowthData(BaseModel):
    """Follower growth over time."""
    platform: Platform | None  # None for aggregate
    data_points: list[GrowthDataPoint]
    period_start: date
    period_end: date
    net_change: int
    percent_change: float


class TopPost(BaseModel):
    """Top performing post."""
    id: str
    platform: Platform
    content: str
    thumbnail_url: str | None
    likes_count: int
    comments_count: int
    shares_count: int
    engagement_score: int
    published_at: datetime
    post_url: str | None


class WeeklyReport(BaseModel):
    """Weekly analytics summary."""
    week_start: date
    week_end: date
    overview: OverviewStats
    growth: list[GrowthData]
    top_posts: list[TopPost]
    best_posting_times: list[str]
