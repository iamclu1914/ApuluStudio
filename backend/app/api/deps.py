"""API dependencies for authentication and authorization."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import get_settings
from app.core.constants import TEMP_USER_ID
from app.core.security import verify_access_token
from app.models.user import User

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)
settings = get_settings()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        credentials: The HTTP Bearer credentials
        db: Database session

    Returns:
        The authenticated User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        if settings.debug:
            result = await db.execute(
                select(User).where(User.id == TEMP_USER_ID)
            )
            user = result.scalar_one_or_none()
            if user is not None:
                return user
        raise credentials_exception

    token = credentials.credentials
    user_id = verify_access_token(token)

    if user_id is None:
        raise credentials_exception

    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency to get the current active user.

    Args:
        current_user: The authenticated user from get_current_user

    Returns:
        The authenticated and active User object

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
