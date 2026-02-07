# Posts API routes
from datetime import datetime
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.post import Post, PostPlatform, PostStatus, PostType
from app.models.social_account import Platform, SocialAccount
from app.schemas.post import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PostListResponse,
    PostCursorResponse,
)
from app.services.scheduler_service import SchedulerService
from app.services.storage_service import StorageService
from app.services.platforms.requirements import (
    validate_content_for_platform,
    PLATFORM_REQUIREMENTS,
)
from app.services.media_utils import get_default_aspect_ratio
from app.api.deps import CurrentActiveUser
from app.core.utils import detect_media_types

router = APIRouter()


@router.get("", response_model=PostListResponse)
async def list_posts(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status: PostStatus | None = None,
    platform: Platform | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List all posts with optional filtering."""
    query = (
        select(Post)
        .where(Post.user_id == current_user.id)
        .options(selectinload(Post.platforms).selectinload(PostPlatform.social_account))
        .order_by(Post.created_at.desc())
    )

    if status:
        query = query.where(Post.status == status)

    # Count total
    count_query = select(func.count(Post.id)).where(Post.user_id == current_user.id)
    if status:
        count_query = count_query.where(Post.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    posts = list(result.scalars().all())

    return PostListResponse(
        posts=[_post_to_response(p) for p in posts],
        total=total,
        page=page,
        per_page=per_page,
        has_next=offset + len(posts) < total,
    )


@router.get("/cursor", response_model=PostCursorResponse)
async def list_posts_cursor(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status: PostStatus | None = None,
    cursor: str | None = Query(None, description="Last post ID from previous page"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    List posts with cursor-based pagination.

    O(1) performance vs O(n) for offset pagination.
    Use this for infinite scroll or large datasets.

    Pass the `next_cursor` from the response as `cursor` to get the next page.
    """
    query = (
        select(Post)
        .where(Post.user_id == current_user.id)
        .options(selectinload(Post.platforms).selectinload(PostPlatform.social_account))
    )

    if status:
        query = query.where(Post.status == status)

    # Apply cursor filter manually since we need relationship loading
    if cursor:
        query = query.where(Post.id < cursor)

    query = query.order_by(desc(Post.id)).limit(limit + 1)

    result = await db.execute(query)
    posts = list(result.scalars().all())

    has_more = len(posts) > limit
    if has_more:
        posts = posts[:limit]

    next_cursor = posts[-1].id if posts and has_more else None

    return PostCursorResponse(
        posts=[_post_to_response(p) for p in posts],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.get("/calendar")
async def get_calendar_posts(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: datetime,
    end_date: datetime,
):
    """Get posts for calendar view."""
    query = (
        select(Post)
        .where(
            and_(
                Post.user_id == current_user.id,
                Post.scheduled_at >= start_date,
                Post.scheduled_at <= end_date,
            )
        )
        .options(selectinload(Post.platforms).selectinload(PostPlatform.social_account))
        .order_by(Post.scheduled_at)
    )

    result = await db.execute(query)
    posts = list(result.scalars().all())

    return [_post_to_response(p) for p in posts]


@router.get("/requirements")
async def get_all_platform_requirements():
    """Get posting requirements for all platforms."""
    result = {}
    for platform, req in PLATFORM_REQUIREMENTS.items():
        result[platform.value] = {
            "displayName": req.display_name,
            "media": {
                "mediaRequired": req.media.media_required,
                "maxImages": req.media.max_images,
                "maxVideos": req.media.max_videos,
                "maxImageSizeMb": req.media.max_image_size_mb,
                "maxVideoSizeMb": req.media.max_video_size_mb,
                "maxVideoDurationSeconds": req.media.max_video_duration_seconds,
                "supportedImageFormats": req.media.supported_image_formats,
                "supportedVideoFormats": req.media.supported_video_formats,
                "canMixMediaTypes": req.media.can_mix_media_types,
                "recommendedImageSize": f"{req.media.recommended_image_width}x{req.media.recommended_image_height}",
            },
            "content": {
                "maxCaptionLength": req.content.max_caption_length,
                "supportsHashtags": req.content.supports_hashtags,
                "supportsMentions": req.content.supports_mentions,
                "supportsLinks": req.content.supports_links,
            },
            "notes": req.notes,
        }
    return result


@router.get("/requirements/{platform}")
async def get_platform_requirement(platform: Platform):
    """Get posting requirements for a specific platform."""
    req = PLATFORM_REQUIREMENTS.get(platform)
    if not req:
        raise HTTPException(status_code=404, detail=f"Platform not found: {platform}")

    return {
        "platform": platform.value,
        "displayName": req.display_name,
        "media": {
            "mediaRequired": req.media.media_required,
            "maxImages": req.media.max_images,
            "maxVideos": req.media.max_videos,
            "maxImageSizeMb": req.media.max_image_size_mb,
            "maxVideoSizeMb": req.media.max_video_size_mb,
            "maxVideoDurationSeconds": req.media.max_video_duration_seconds,
            "supportedImageFormats": req.media.supported_image_formats,
            "supportedVideoFormats": req.media.supported_video_formats,
            "canMixMediaTypes": req.media.can_mix_media_types,
            "recommendedImageSize": f"{req.media.recommended_image_width}x{req.media.recommended_image_height}",
        },
        "content": {
            "maxCaptionLength": req.content.max_caption_length,
            "supportsHashtags": req.content.supports_hashtags,
            "supportsMentions": req.content.supports_mentions,
            "supportsLinks": req.content.supports_links,
        },
        "notes": req.notes,
    }


@router.post("/validate")
async def validate_post_content(
    content: str = "",
    platforms: list[Platform] = [],
    media_urls: list[str] = [],
):
    """Validate content against platform requirements before posting."""
    if not platforms:
        raise HTTPException(status_code=400, detail="At least one platform is required")

    # Determine media types
    media_types = detect_media_types(media_urls)

    results = {}
    all_valid = True

    for platform in platforms:
        validation = validate_content_for_platform(
            platform=platform,
            content=content,
            media_urls=media_urls,
            media_types=media_types,
        )

        results[platform.value] = {
            "valid": validation.valid,
            "errors": [{"field": e.field, "message": e.message} for e in validation.errors],
            "warnings": validation.warnings,
        }

        if not validation.valid:
            all_valid = False

    return {
        "valid": all_valid,
        "platforms": results,
    }


@router.get("/smart-slots/{platform}")
async def get_smart_slots(
    platform: Platform,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get suggested best times to post."""
    scheduler = SchedulerService(db)
    return scheduler.get_smart_slots(platform)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a single post by ID."""
    query = (
        select(Post)
        .where(and_(Post.id == post_id, Post.user_id == current_user.id))
        .options(selectinload(Post.platforms).selectinload(PostPlatform.social_account))
    )

    result = await db.execute(query)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return _post_to_response(post)


@router.post("", response_model=PostResponse)
async def create_post(
    data: PostCreate,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new post (draft or scheduled)."""
    scheduler = SchedulerService(db)

    # Check if user has connected accounts for the platforms
    accounts_query = select(SocialAccount).where(
        and_(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform.in_(data.platforms),
            SocialAccount.is_active == True,
        )
    )
    result = await db.execute(accounts_query)
    accounts = {acc.platform: acc for acc in result.scalars().all()}

    missing = [p for p in data.platforms if p not in accounts]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"No connected accounts for: {', '.join(p.value for p in missing)}",
        )

    # Validate content for each platform
    validation_errors = []
    validation_warnings = []

    # Determine media types from URLs
    media_types = detect_media_types(data.media_urls) if data.media_urls else []

    for platform in data.platforms:
        validation = validate_content_for_platform(
            platform=platform,
            content=data.content or "",
            media_urls=data.media_urls,
            media_types=media_types,
        )

        if not validation.valid:
            for error in validation.errors:
                validation_errors.append(f"{error.platform.value}: {error.message}")

        validation_warnings.extend(validation.warnings)

    if validation_errors:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Content validation failed",
                "errors": validation_errors,
                "warnings": validation_warnings,
            },
        )

    # Create the post
    status = PostStatus.SCHEDULED if data.scheduled_at else PostStatus.DRAFT

    # Convert timezone-aware datetime to naive UTC for database storage
    scheduled_at_naive = None
    if data.scheduled_at:
        if data.scheduled_at.tzinfo is not None:
            # Convert to UTC and remove timezone info
            from datetime import timezone
            scheduled_at_naive = data.scheduled_at.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            scheduled_at_naive = data.scheduled_at

    post = Post(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        content=data.content,
        post_type=data.post_type,
        media_urls=data.media_urls,
        hashtags=data.hashtags,
        scheduled_at=scheduled_at_naive,
        status=status,
        ai_generated=data.ai_generated,
        ai_prompt=data.ai_prompt,
    )
    db.add(post)

    # Create platform entries
    for platform in data.platforms:
        account = accounts[platform]
        post_platform = PostPlatform(
            id=str(uuid.uuid4()),
            post_id=post.id,
            social_account_id=account.id,
            status=status,
        )
        db.add(post_platform)

    await db.commit()
    await db.refresh(post)

    # Reload with relationships
    query = (
        select(Post)
        .where(Post.id == post.id)
        .options(selectinload(Post.platforms).selectinload(PostPlatform.social_account))
    )
    result = await db.execute(query)
    post = result.scalar_one()

    return _post_to_response(post)


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    data: PostUpdate,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a post."""
    query = (
        select(Post)
        .where(and_(Post.id == post_id, Post.user_id == current_user.id))
        .options(selectinload(Post.platforms).selectinload(PostPlatform.social_account))
    )
    result = await db.execute(query)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.status == PostStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="Cannot edit published posts")

    # Update fields
    if data.content is not None:
        post.content = data.content
    if data.hashtags is not None:
        post.hashtags = data.hashtags
    if data.scheduled_at is not None:
        # Convert timezone-aware datetime to naive UTC
        from datetime import timezone
        if data.scheduled_at.tzinfo is not None:
            post.scheduled_at = data.scheduled_at.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            post.scheduled_at = data.scheduled_at
        post.status = PostStatus.SCHEDULED
        for pp in post.platforms:
            pp.status = PostStatus.SCHEDULED
    if data.status is not None:
        post.status = data.status

    await db.commit()

    # Reload with relationships
    query = (
        select(Post)
        .where(Post.id == post.id)
        .options(selectinload(Post.platforms).selectinload(PostPlatform.social_account))
    )
    result = await db.execute(query)
    post = result.scalar_one()

    return _post_to_response(post)


@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a post."""
    query = select(Post).where(
        and_(Post.id == post_id, Post.user_id == current_user.id)
    )
    result = await db.execute(query)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    await db.delete(post)
    await db.commit()

    return {"success": True}


@router.post("/{post_id}/publish")
async def publish_now(
    post_id: str,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Publish a post immediately."""
    query = (
        select(Post)
        .where(
            and_(
                Post.id == post_id,
                Post.user_id == current_user.id,
                Post.status.in_([PostStatus.DRAFT, PostStatus.SCHEDULED, PostStatus.FAILED]),
            )
        )
        .options(selectinload(Post.platforms).selectinload(PostPlatform.social_account))
    )
    result = await db.execute(query)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found or already published")

    # Set to scheduled with current time to trigger publish
    post.scheduled_at = datetime.utcnow()
    post.status = PostStatus.SCHEDULED
    for pp in post.platforms:
        pp.status = PostStatus.SCHEDULED

    await db.commit()

    # Publish
    scheduler = SchedulerService(db)
    results = await scheduler.publish_post(post)

    return {
        "success": True,
        "results": results,
    }


@router.post("/upload")
async def upload_media(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
    platforms: str = Query(None, description="Comma-separated platform names for auto-crop"),
    aspect_ratio: str = Query(None, description="Force aspect ratio: 1:1, 4:5, 16:9, 9:16"),
):
    """
    Upload media for a post.

    If platforms are specified, will auto-crop to the first platform's preferred aspect ratio.
    You can also force a specific aspect ratio with the aspect_ratio parameter.
    """
    storage = StorageService()

    content = await file.read()
    content_type = file.content_type or "application/octet-stream"

    # Determine aspect ratios to use
    target_ratio = None
    variant_targets: dict[str, str] = {}

    # Priority 1: Explicit aspect_ratio parameter
    valid_ratios = ["1:1", "4:5", "16:9", "9:16", "original"]
    if aspect_ratio and aspect_ratio in valid_ratios:
        target_ratio = aspect_ratio

    if platforms and content_type.startswith("image/"):
        platform_list = [p.strip().upper() for p in platforms.split(",") if p.strip()]
        if platform_list:
            # Fetch account preferences for these platforms
            platform_enums = []
            for p in platform_list:
                try:
                    platform_enums.append(Platform(p))
                except ValueError:
                    continue

            accounts_query = select(SocialAccount).where(
                and_(
                    SocialAccount.user_id == current_user.id,
                    SocialAccount.platform.in_(platform_enums),
                    SocialAccount.is_active == True,
                )
            )
            accounts_result = await db.execute(accounts_query)
            accounts = {acc.platform: acc for acc in accounts_result.scalars().all()}

            for platform in platform_enums:
                account = accounts.get(platform)
                ratio = None
                if account and account.preferred_aspect_ratio and account.preferred_aspect_ratio != "original":
                    ratio = account.preferred_aspect_ratio
                else:
                    ratio = get_default_aspect_ratio(platform)

                if target_ratio and target_ratio != "original":
                    ratio = target_ratio

                if ratio:
                    variant_targets[platform.value.lower()] = ratio

    if content_type.startswith("image/"):
        if variant_targets:
            result = await storage.upload_image_with_variants(
                file_data=content,
                file_name=file.filename,
                content_type=content_type,
                user_id=current_user.id,
                primary_aspect_ratio=target_ratio,
                variants=variant_targets,
            )
        else:
            result = await storage.upload_image(
                file_data=content,
                file_name=file.filename,
                content_type=content_type,
                user_id=current_user.id,
                aspect_ratio=target_ratio,
            )
    elif content_type.startswith("video/"):
        result = await storage.upload_video(
            file_data=content,
            file_name=file.filename,
            content_type=content_type,
            user_id=current_user.id,
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Upload failed"))

    return result


@router.get("/schedule/suggestions")
async def get_schedule_suggestions(
    platforms: str = Query(..., description="Comma-separated platform names"),
):
    """
    Get AI-powered optimal posting time suggestions.

    Returns the best times to post for each platform based on
    engagement patterns and industry best practices.
    """
    from app.services.smart_scheduler import get_smart_suggestions

    # Parse platforms
    platform_list = []
    for p in platforms.split(","):
        p = p.strip().upper()
        try:
            platform_list.append(Platform(p))
        except ValueError:
            # Try lowercase
            try:
                platform_list.append(Platform[p])
            except KeyError:
                continue

    if not platform_list:
        raise HTTPException(status_code=400, detail="No valid platforms specified")

    suggestions = get_smart_suggestions(platform_list)

    return {
        "suggestions": suggestions,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/schedule/optimal-time")
async def get_optimal_cross_platform_time(
    platforms: str = Query(..., description="Comma-separated platform names"),
):
    """
    Get the single best time to post across multiple platforms.

    Useful when cross-posting to find a time that works well for all platforms.
    """
    from app.services.smart_scheduler import get_optimal_cross_platform_time as get_optimal

    # Parse platforms
    platform_list = []
    for p in platforms.split(","):
        p = p.strip().upper()
        try:
            platform_list.append(Platform(p))
        except ValueError:
            try:
                platform_list.append(Platform[p])
            except KeyError:
                continue

    if not platform_list:
        raise HTTPException(status_code=400, detail="No valid platforms specified")

    optimal = get_optimal(platform_list)

    return {
        "optimal_time": optimal,
        "generated_at": datetime.utcnow().isoformat(),
    }


def _post_to_response(post: Post) -> PostResponse:
    """Convert Post model to response schema."""
    from app.schemas.post import PlatformPostResponse

    return PostResponse(
        id=post.id,
        content=post.content,
        post_type=post.post_type,
        media_urls=post.media_urls,
        thumbnail_url=post.thumbnail_url,
        hashtags=post.hashtags,
        status=post.status,
        scheduled_at=post.scheduled_at,
        published_at=post.published_at,
        ai_generated=post.ai_generated,
        created_at=post.created_at,
        updated_at=post.updated_at,
        platforms=[
            PlatformPostResponse(
                id=pp.id,
                platform=pp.social_account.platform,
                username=pp.social_account.username,
                status=pp.status,
                content=pp.content,
                platform_post_url=pp.platform_post_url,
                likes_count=pp.likes_count,
                comments_count=pp.comments_count,
                shares_count=pp.shares_count,
                published_at=pp.published_at,
                error_message=pp.error_message,
            )
            for pp in post.platforms
        ],
    )
