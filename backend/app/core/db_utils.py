"""Database utilities implementing postgres-patterns best practices.

Provides:
- Cursor-based pagination (O(1) vs OFFSET O(n))
"""
from typing import Any
from sqlalchemy import Select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession


async def cursor_paginate(
    session: AsyncSession,
    query: Select,
    cursor: str | None = None,
    limit: int = 20,
    cursor_column: str = "id",
    order: str = "desc",
    include_total: bool = False,
) -> dict[str, Any]:
    """
    Cursor-based pagination - O(1) performance vs OFFSET O(n).

    Usage:
        query = select(Post).where(Post.user_id == user_id)
        result = await cursor_paginate(session, query, cursor=last_id, limit=20)

    Args:
        session: Database session
        query: Base SQLAlchemy query
        cursor: Last item ID from previous page
        limit: Items per page
        cursor_column: Column to use for cursor (must be indexed)
        order: 'asc' or 'desc'
        include_total: Include total count (expensive)

    Returns:
        dict with items, next_cursor, has_more, total
    """
    from sqlalchemy.orm import InstrumentedAttribute

    # Get the model from the query
    model = query.column_descriptions[0]["entity"]
    column: InstrumentedAttribute = getattr(model, cursor_column)

    # Apply cursor filter
    if cursor:
        if order == "desc":
            query = query.where(column < cursor)
        else:
            query = query.where(column > cursor)

    # Apply ordering
    if order == "desc":
        query = query.order_by(desc(column))
    else:
        query = query.order_by(asc(column))

    # Fetch limit + 1 to check if there are more
    query = query.limit(limit + 1)

    result = await session.execute(query)
    items = list(result.scalars().all())

    # Check if there are more items
    has_more = len(items) > limit
    if has_more:
        items = items[:limit]

    # Get next cursor
    next_cursor = None
    if items and has_more:
        next_cursor = str(getattr(items[-1], cursor_column))

    # Optional total count (expensive - use sparingly)
    total = None
    if include_total:
        # Build count query without pagination
        base_query = query.limit(None).offset(None)
        count_query = base_query.with_only_columns(func.count()).order_by(None)
        total_result = await session.execute(count_query)
        total = total_result.scalar()

    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "total": total,
    }
