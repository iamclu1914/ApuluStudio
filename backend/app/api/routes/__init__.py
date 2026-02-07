from fastapi import APIRouter

from app.api.routes import posts, accounts, inbox, analytics, ai, auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(inbox.router, prefix="/inbox", tags=["inbox"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
