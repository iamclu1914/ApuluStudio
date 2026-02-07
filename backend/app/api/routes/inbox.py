from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, func, desc, literal_column, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.social_account import SocialAccount, Platform
from app.models.engagement import Comment, Mention
from app.schemas.engagement import (
    CommentResponse,
    CommentReply,
    MentionResponse,
    InboxItem,
    InboxResponse,
)
from app.services.platforms.bluesky import BlueskyService
from app.services.platforms.meta import MetaService
from app.api.deps import CurrentActiveUser

router = APIRouter()


@router.get("", response_model=InboxResponse)
async def get_inbox(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    platform: Platform | None = None,
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Get unified inbox with comments and mentions."""
    # Get user's social accounts
    accounts_query = select(SocialAccount).where(
        SocialAccount.user_id == current_user.id
    )
    if platform:
        accounts_query = accounts_query.where(SocialAccount.platform == platform)

    accounts_result = await db.execute(accounts_query)
    accounts = {acc.id: acc for acc in accounts_result.scalars().all()}
    account_ids = list(accounts.keys())

    if not account_ids:
        return InboxResponse(
            items=[],
            total=0,
            unread_count=0,
            page=page,
            per_page=per_page,
            has_next=False,
        )

    # Build base queries for comments and mentions
    comments_base = select(Comment).where(
        Comment.social_account_id.in_(account_ids)
    )
    mentions_base = select(Mention).where(
        Mention.social_account_id.in_(account_ids)
    )

    if unread_only:
        comments_base = comments_base.where(Comment.is_read == False)
        mentions_base = mentions_base.where(Mention.is_read == False)

    # Get total counts efficiently
    comments_count_query = select(func.count()).select_from(comments_base.subquery())
    mentions_count_query = select(func.count()).select_from(mentions_base.subquery())

    comments_count_result = await db.execute(comments_count_query)
    mentions_count_result = await db.execute(mentions_count_query)
    total = (comments_count_result.scalar() or 0) + (mentions_count_result.scalar() or 0)

    # Get unread counts efficiently
    unread_comments_query = select(func.count()).where(
        and_(
            Comment.social_account_id.in_(account_ids),
            Comment.is_read == False,
        )
    )
    unread_mentions_query = select(func.count()).where(
        and_(
            Mention.social_account_id.in_(account_ids),
            Mention.is_read == False,
        )
    )

    unread_comments_result = await db.execute(unread_comments_query)
    unread_mentions_result = await db.execute(unread_mentions_query)
    unread_count = (unread_comments_result.scalar() or 0) + (unread_mentions_result.scalar() or 0)

    # Calculate pagination
    offset = (page - 1) * per_page

    # Fetch paginated comments with DB-level sorting
    comments_query = (
        comments_base
        .order_by(desc(Comment.posted_at))
        .offset(offset)
        .limit(per_page)
    )
    comments_result = await db.execute(comments_query)
    comments = list(comments_result.scalars().all())

    # Fetch paginated mentions with DB-level sorting
    mentions_query = (
        mentions_base
        .order_by(desc(Mention.mentioned_at))
        .offset(offset)
        .limit(per_page)
    )
    mentions_result = await db.execute(mentions_query)
    mentions = list(mentions_result.scalars().all())

    # Convert to inbox items
    items: list[InboxItem] = []

    for comment in comments:
        account = accounts.get(comment.social_account_id)
        items.append(InboxItem(
            id=comment.id,
            type="comment",
            platform=account.platform if account else Platform.INSTAGRAM,
            content=comment.content,
            author_username=comment.author_username,
            author_avatar_url=comment.author_avatar_url,
            is_read=comment.is_read,
            timestamp=comment.posted_at,
            is_replied=comment.is_replied,
            likes_count=comment.likes_count,
        ))

    for mention in mentions:
        account = accounts.get(mention.social_account_id)
        items.append(InboxItem(
            id=mention.id,
            type="mention",
            platform=account.platform if account else Platform.INSTAGRAM,
            content=mention.content,
            author_username=mention.author_username,
            author_avatar_url=mention.author_avatar_url,
            is_read=mention.is_read,
            timestamp=mention.mentioned_at,
            post_url=mention.post_url,
        ))

    # Sort combined results by timestamp (newest first)
    # Note: This is still in-memory but only for the current page (max per_page*2 items)
    items.sort(key=lambda x: x.timestamp, reverse=True)
    items = items[:per_page]  # Trim to page size after combining

    return InboxResponse(
        items=items,
        total=total,
        unread_count=unread_count,
        page=page,
        per_page=per_page,
        has_next=offset + per_page < total,
    )


@router.post("/sync")
async def sync_inbox(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    platform: Platform | None = None,
):
    """Sync comments and mentions from connected accounts."""
    # Get user's social accounts
    accounts_query = select(SocialAccount).where(
        and_(
            SocialAccount.user_id == current_user.id,
            SocialAccount.is_active == True,
        )
    )
    if platform:
        accounts_query = accounts_query.where(SocialAccount.platform == platform)

    accounts_result = await db.execute(accounts_query)
    accounts = list(accounts_result.scalars().all())

    results = {}

    for account in accounts:
        try:
            # Get recent posts and their comments
            # This is simplified - in production, track which posts to check
            synced_count = 0

            if account.platform == Platform.BLUESKY:
                service = BlueskyService()
                # Bluesky notifications would need different handling
                results[account.id] = {
                    "platform": account.platform.value,
                    "synced": 0,
                    "note": "Bluesky notification sync not implemented in MVP",
                }
            elif account.platform in [Platform.INSTAGRAM, Platform.FACEBOOK]:
                # For Meta, we would need to iterate through recent posts
                # and fetch comments for each
                results[account.id] = {
                    "platform": account.platform.value,
                    "synced": 0,
                    "note": "Manual sync for Meta platforms",
                }
            else:
                results[account.id] = {
                    "platform": account.platform.value,
                    "synced": 0,
                }

        except Exception as e:
            results[account.id] = {
                "platform": account.platform.value,
                "error": str(e),
            }

    return {"success": True, "results": results}


@router.post("/comments/{comment_id}/read")
async def mark_comment_read(
    comment_id: str,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark a comment as read."""
    query = select(Comment).where(Comment.id == comment_id)
    result = await db.execute(query)
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Verify ownership through social account
    account_query = select(SocialAccount).where(
        and_(
            SocialAccount.id == comment.social_account_id,
            SocialAccount.user_id == current_user.id,
        )
    )
    account_result = await db.execute(account_query)
    if not account_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Comment not found")

    comment.is_read = True
    await db.commit()

    return {"success": True}


@router.post("/comments/{comment_id}/reply")
async def reply_to_comment(
    comment_id: str,
    data: CommentReply,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reply to a comment."""
    # Get the comment
    query = select(Comment).where(Comment.id == comment_id)
    result = await db.execute(query)
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Get the social account
    account_query = select(SocialAccount).where(
        and_(
            SocialAccount.id == comment.social_account_id,
            SocialAccount.user_id == current_user.id,
        )
    )
    account_result = await db.execute(account_query)
    account = account_result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Get appropriate service
    services = {
        Platform.BLUESKY: BlueskyService(),
        Platform.INSTAGRAM: MetaService(Platform.INSTAGRAM),
        Platform.FACEBOOK: MetaService(Platform.FACEBOOK),
    }

    service = services.get(account.platform)
    if not service:
        raise HTTPException(status_code=400, detail="Platform not supported for replies")

    # Send reply
    try:
        result = await service.reply_to_comment(
            comment_id=comment.platform_comment_id,
            content=data.content,
            access_token=account.access_token,
            handle=account.username,
        )

        if result.success:
            comment.is_replied = True
            comment.reply_id = result.comment_id
            comment.replied_at = datetime.utcnow()
            await db.commit()

            return {"success": True, "reply_id": result.comment_id}
        else:
            raise HTTPException(status_code=400, detail=result.error_message)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mentions/{mention_id}/read")
async def mark_mention_read(
    mention_id: str,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark a mention as read."""
    query = select(Mention).where(Mention.id == mention_id)
    result = await db.execute(query)
    mention = result.scalar_one_or_none()

    if not mention:
        raise HTTPException(status_code=404, detail="Mention not found")

    # Verify ownership
    account_query = select(SocialAccount).where(
        and_(
            SocialAccount.id == mention.social_account_id,
            SocialAccount.user_id == current_user.id,
        )
    )
    account_result = await db.execute(account_query)
    if not account_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Mention not found")

    mention.is_read = True
    await db.commit()

    return {"success": True}


@router.post("/read-all")
async def mark_all_read(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    platform: Platform | None = None,
):
    """Mark all inbox items as read."""
    # Get user's accounts
    accounts_query = select(SocialAccount.id).where(
        SocialAccount.user_id == current_user.id
    )
    if platform:
        accounts_query = accounts_query.where(SocialAccount.platform == platform)

    accounts_result = await db.execute(accounts_query)
    account_ids = [row[0] for row in accounts_result.all()]

    if not account_ids:
        return {"success": True, "updated": 0}

    # Update comments
    comments_query = select(Comment).where(
        and_(
            Comment.social_account_id.in_(account_ids),
            Comment.is_read == False,
        )
    )
    comments_result = await db.execute(comments_query)
    comments = list(comments_result.scalars().all())

    for comment in comments:
        comment.is_read = True

    # Update mentions
    mentions_query = select(Mention).where(
        and_(
            Mention.social_account_id.in_(account_ids),
            Mention.is_read == False,
        )
    )
    mentions_result = await db.execute(mentions_query)
    mentions = list(mentions_result.scalars().all())

    for mention in mentions:
        mention.is_read = True

    await db.commit()

    return {"success": True, "updated": len(comments) + len(mentions)}
