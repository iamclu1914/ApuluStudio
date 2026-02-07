from datetime import datetime, date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.social_account import SocialAccount, Platform
from app.models.post import Post, PostPlatform, PostStatus
from app.schemas.analytics import (
    OverviewStats,
    PlatformStats,
    GrowthData,
    GrowthDataPoint,
    TopPost,
    WeeklyReport,
)
from app.api.deps import CurrentActiveUser

router = APIRouter()


@router.get("/overview", response_model=OverviewStats)
async def get_overview(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get high-level dashboard statistics."""
    # Get all connected accounts
    accounts_query = select(SocialAccount).where(
        and_(
            SocialAccount.user_id == current_user.id,
            SocialAccount.is_active == True,
        )
    )
    accounts_result = await db.execute(accounts_query)
    accounts = list(accounts_result.scalars().all())

    # Calculate totals
    total_followers = sum(acc.follower_count for acc in accounts)

    # Get posts from this week
    week_ago = datetime.utcnow() - timedelta(days=7)
    posts_query = select(Post).where(
        and_(
            Post.user_id == current_user.id,
            Post.status == PostStatus.PUBLISHED,
            Post.published_at >= week_ago,
        )
    )
    posts_result = await db.execute(posts_query)
    recent_posts = list(posts_result.scalars().all())
    posts_this_week = len(recent_posts)

    # Get engagement from post platforms
    post_ids = [p.id for p in recent_posts]
    total_engagement = 0

    if post_ids:
        engagement_query = select(
            func.sum(PostPlatform.likes_count + PostPlatform.comments_count)
        ).where(PostPlatform.post_id.in_(post_ids))
        engagement_result = await db.execute(engagement_query)
        total_engagement = engagement_result.scalar() or 0

    # Calculate engagement rate (simplified)
    engagement_rate = 0.0
    if total_followers > 0 and posts_this_week > 0:
        engagement_rate = (total_engagement / (total_followers * posts_this_week)) * 100

    # Per-platform stats
    platform_stats = []
    for account in accounts:
        # Get posts count for this platform
        platform_posts_query = select(func.count(PostPlatform.id)).where(
            and_(
                PostPlatform.social_account_id == account.id,
                PostPlatform.status == PostStatus.PUBLISHED,
            )
        )
        platform_posts_result = await db.execute(platform_posts_query)
        platform_posts_count = platform_posts_result.scalar() or 0

        # Get engagement for this platform
        platform_engagement_query = select(
            func.sum(PostPlatform.likes_count + PostPlatform.comments_count)
        ).where(
            and_(
                PostPlatform.social_account_id == account.id,
                PostPlatform.status == PostStatus.PUBLISHED,
            )
        )
        platform_engagement_result = await db.execute(platform_engagement_query)
        platform_engagement = platform_engagement_result.scalar() or 0

        platform_rate = 0.0
        if account.follower_count > 0 and platform_posts_count > 0:
            platform_rate = (platform_engagement / (account.follower_count * platform_posts_count)) * 100

        platform_stats.append(PlatformStats(
            platform=account.platform,
            followers=account.follower_count,
            following=account.following_count,
            posts_count=platform_posts_count,
            engagement_rate=round(platform_rate, 2),
        ))

    return OverviewStats(
        total_followers=total_followers,
        total_engagement=int(total_engagement),
        posts_this_week=posts_this_week,
        engagement_rate=round(engagement_rate, 2),
        platforms=platform_stats,
    )


@router.get("/growth", response_model=GrowthData)
async def get_growth(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    platform: Platform | None = None,
    days: int = Query(30, ge=7, le=90),
):
    """Get follower growth over time."""
    # Note: In a real implementation, you'd store historical follower counts
    # For MVP, we'll generate simulated data based on current followers

    accounts_query = select(SocialAccount).where(
        SocialAccount.user_id == current_user.id
    )
    if platform:
        accounts_query = accounts_query.where(SocialAccount.platform == platform)

    accounts_result = await db.execute(accounts_query)
    accounts = list(accounts_result.scalars().all())

    if not accounts:
        return GrowthData(
            platform=platform,
            data_points=[],
            period_start=date.today() - timedelta(days=days),
            period_end=date.today(),
            net_change=0,
            percent_change=0.0,
        )

    current_followers = sum(acc.follower_count for acc in accounts)

    # Generate simulated historical data
    # In production, this would come from a follower_history table
    data_points = []
    today = date.today()

    # Simulate a growth trend (random walk around 0.1% daily growth)
    import random
    random.seed(42)  # Consistent results

    followers = int(current_followers * 0.95)  # Start 5% lower
    daily_growth_rate = 0.001  # 0.1% average daily growth

    for i in range(days, -1, -1):
        day = today - timedelta(days=i)

        # Add some randomness
        variation = random.uniform(-0.002, 0.003)
        followers = int(followers * (1 + daily_growth_rate + variation))

        # Cap at current followers on last day
        if i == 0:
            followers = current_followers

        data_points.append(GrowthDataPoint(
            date=day,
            followers=followers,
            engagement=int(followers * random.uniform(0.01, 0.05)),
        ))

    # Calculate changes
    start_followers = data_points[0].followers if data_points else 0
    net_change = current_followers - start_followers
    percent_change = (net_change / start_followers * 100) if start_followers > 0 else 0

    return GrowthData(
        platform=platform,
        data_points=data_points,
        period_start=today - timedelta(days=days),
        period_end=today,
        net_change=net_change,
        percent_change=round(percent_change, 2),
    )


@router.get("/top-posts", response_model=list[TopPost])
async def get_top_posts(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    platform: Platform | None = None,
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(5, ge=1, le=20),
):
    """Get top performing posts."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Build query with eager loading to avoid N+1 queries
    query = (
        select(Post)
        .where(
            and_(
                Post.user_id == current_user.id,
                Post.status == PostStatus.PUBLISHED,
                Post.published_at >= cutoff,
            )
        )
        .options(
            selectinload(Post.platforms).selectinload(PostPlatform.social_account)
        )
    )

    # Filter by platform if specified
    if platform:
        query = query.join(Post.platforms).join(PostPlatform.social_account).where(
            SocialAccount.platform == platform
        ).distinct()

    result = await db.execute(query)
    posts = list(result.scalars().all())

    # Calculate engagement scores and build response
    top_posts = []

    for post in posts:
        # Filter platforms if a specific platform was requested
        post_platforms = post.platforms
        if platform:
            post_platforms = [
                pp for pp in post_platforms
                if pp.social_account and pp.social_account.platform == platform
            ]

        if not post_platforms:
            continue

        # Aggregate engagement
        total_likes = sum(pp.likes_count for pp in post_platforms)
        total_comments = sum(pp.comments_count for pp in post_platforms)
        total_shares = sum(pp.shares_count for pp in post_platforms)
        engagement_score = total_likes + (total_comments * 2) + (total_shares * 3)

        # Get the best performing platform version
        best_platform = max(post_platforms, key=lambda pp: pp.likes_count + pp.comments_count)

        # Get platform from already-loaded relationship
        account = best_platform.social_account

        top_posts.append(TopPost(
            id=post.id,
            platform=account.platform if account else Platform.INSTAGRAM,
            content=post.content[:200] + "..." if len(post.content) > 200 else post.content,
            thumbnail_url=post.thumbnail_url or (post.media_urls[0] if post.media_urls else None),
            likes_count=total_likes,
            comments_count=total_comments,
            shares_count=total_shares,
            engagement_score=engagement_score,
            published_at=post.published_at,
            post_url=best_platform.platform_post_url,
        ))

    # Sort by engagement score and limit
    top_posts.sort(key=lambda x: x.engagement_score, reverse=True)
    return top_posts[:limit]


@router.get("/weekly-report", response_model=WeeklyReport)
async def get_weekly_report(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a weekly analytics summary."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    # Get overview
    overview = await get_overview(current_user, db)

    # Get growth for each platform
    growth_data = []
    accounts_query = select(SocialAccount.platform).where(
        SocialAccount.user_id == current_user.id
    ).distinct()
    accounts_result = await db.execute(accounts_query)
    platforms = [row[0] for row in accounts_result.all()]

    for platform in platforms:
        platform_growth = await get_growth(current_user, db, platform=platform, days=7)
        growth_data.append(platform_growth)

    # Get top posts
    top_posts = await get_top_posts(current_user, db, days=7, limit=3)

    # Best posting times (simplified - would use actual engagement data)
    best_times = [
        "Tuesday 10:00 AM",
        "Wednesday 2:00 PM",
        "Thursday 11:00 AM",
    ]

    return WeeklyReport(
        week_start=week_start,
        week_end=week_end,
        overview=overview,
        growth=growth_data,
        top_posts=top_posts,
        best_posting_times=best_times,
    )
