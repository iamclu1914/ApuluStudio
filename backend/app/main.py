from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.logger import logger
from app.core.middleware import (
    ExceptionHandlerMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from app.models.user import User
from app.api.routes import api_router
from app.core.constants import TEMP_USER_ID
from app.services.background_scheduler import (
    start_scheduler,
    stop_scheduler,
    background_scheduler,
)
from app.services.late_sync_scheduler import (
    start_late_sync_scheduler,
    stop_late_sync_scheduler,
    late_sync_scheduler,
)
from app.core.http_client import init_http_client, close_http_client

settings = get_settings()
DEV_LAN_ORIGIN_REGEX = (
    r"^https?://"
    r"(localhost|127\.0\.0\.1|10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
    r"172\.(1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})"
    r"(?::\d+)?$"
)


async def ensure_test_user_exists():
    """Create the test user if it doesn't exist."""
    async with AsyncSessionLocal() as session:
        # Check if user exists
        result = await session.execute(
            select(User).where(User.id == TEMP_USER_ID)
        )
        user = result.scalar_one_or_none()

        if not user:
            # Create test user
            user = User(
                id=TEMP_USER_ID,
                email="demo@apulu.studio",
                name="Demo User",
                is_active=True,
                max_social_accounts=10,
            )
            session.add(user)
            await session.commit()
            print(f"Created test user: {TEMP_USER_ID}")
        else:
            print(f"Test user already exists: {TEMP_USER_ID}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {settings.app_name}...", version="0.1.0")

    # Initialize shared HTTP client with connection pooling
    await init_http_client()
    logger.info("HTTP client initialized with connection pooling")

    await ensure_test_user_exists()

    # Start background scheduler for automatic post publishing
    await start_scheduler()
    logger.info("Background scheduler started - scheduled posts will auto-publish")

    if settings.late_sync_interval_seconds > 0:
        await start_late_sync_scheduler()
        logger.info(
            "LATE sync scheduler started",
            interval_seconds=late_sync_scheduler.sync_interval,
        )

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name}...")
    await stop_scheduler()
    logger.info("Background scheduler stopped")
    await stop_late_sync_scheduler()
    logger.info("LATE sync scheduler stopped")

    # Close HTTP client and release connections
    await close_http_client()
    logger.info("HTTP client closed")


app = FastAPI(
    title=settings.app_name,
    description="All-in-one social media management dashboard for solopreneurs",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Custom middleware (order matters - added first = innermost)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ExceptionHandlerMiddleware)
app.add_middleware(SecurityHeadersMiddleware)  # Security headers on all responses
app.add_middleware(
    RateLimitMiddleware,
    max_requests=100,  # 100 requests per minute
    window_seconds=60,
)

# CORS middleware - added LAST to be outermost (handles all responses including errors)
# NOTE: Origins must NOT have trailing slashes (browsers send Origin without one)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,  # from FRONTEND_URL env var (trailing slash stripped in config)
        "https://studio-lime-mu-69.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=DEV_LAN_ORIGIN_REGEX if settings.debug else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "status": "running",
        "docs": "/api/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/scheduler/status")
async def scheduler_status():
    """Get background scheduler status."""
    return {
        "running": background_scheduler.is_running,
        "check_interval_seconds": background_scheduler.check_interval,
        "message": "Scheduler is actively checking for due posts" if background_scheduler.is_running else "Scheduler is stopped",
    }


@app.post("/api/scheduler/check-now")
async def scheduler_check_now():
    """Manually trigger a check for due posts (useful for testing)."""
    if not background_scheduler.is_running:
        return {"success": False, "message": "Scheduler is not running"}

    await background_scheduler.check_now()
    return {"success": True, "message": "Check triggered - due posts will be published"}
