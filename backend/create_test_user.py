"""Script to create the test user in the database."""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User


async def create_user():
    async with AsyncSessionLocal() as session:
        # Check if user exists
        result = await session.execute(
            select(User).where(User.id == "user-001")
        )
        user = result.scalar_one_or_none()

        if user:
            print(f"User already exists: {user.id}, {user.email}")
        else:
            # Create user
            user = User(
                id="user-001",
                email="demo@apulu.studio",
                name="Demo User",
                is_active=True,
                max_social_accounts=10,
            )
            session.add(user)
            await session.commit()
            print("Created test user: user-001")


if __name__ == "__main__":
    asyncio.run(create_user())
