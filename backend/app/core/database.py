import ssl
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from supabase import create_client, Client

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def create_ssl_context() -> ssl.SSLContext | bool | None:
    """
    Create SSL context based on configuration.

    Returns:
        - ssl.SSLContext for verify-ca or verify-full modes
        - True for require mode (SSL required but no cert verification)
        - None for disable mode
        - "prefer" string for prefer mode
    """
    ssl_mode = settings.database_ssl_mode

    if ssl_mode == "disable":
        logger.warning(
            "Database SSL is DISABLED. This should only be used for local development."
        )
        return None

    if ssl_mode in ("allow", "prefer"):
        # Let the driver handle SSL negotiation
        logger.info(f"Database SSL mode: {ssl_mode} (driver-negotiated)")
        return ssl_mode

    if ssl_mode == "require":
        # SSL required but no certificate verification
        # This protects against passive eavesdropping but not MITM attacks
        logger.info("Database SSL mode: require (encrypted but no certificate verification)")
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context

    if ssl_mode in ("verify-ca", "verify-full"):
        # Full certificate verification - recommended for production
        ssl_context = ssl.create_default_context()

        if settings.database_ssl_ca_cert:
            ssl_context.load_verify_locations(cafile=settings.database_ssl_ca_cert)
            logger.info(f"Database SSL: Loaded CA certificate from {settings.database_ssl_ca_cert}")
        else:
            # Use system CA certificates
            logger.info("Database SSL: Using system CA certificates")

        if ssl_mode == "verify-full":
            # verify-full also checks hostname matches certificate
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            logger.info("Database SSL mode: verify-full (certificate + hostname verification)")
        else:
            # verify-ca only checks certificate is valid, not hostname
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            logger.info("Database SSL mode: verify-ca (certificate verification only)")

        return ssl_context

    # Fallback to require mode
    logger.warning(f"Unknown SSL mode '{ssl_mode}', defaulting to 'require'")
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context


# Create SSL context based on environment configuration
ssl_context = create_ssl_context()

# Warn in production if SSL is not properly configured
if not settings.debug and settings.database_ssl_mode not in ("verify-ca", "verify-full"):
    logger.warning(
        f"SECURITY WARNING: Database SSL mode is '{settings.database_ssl_mode}'. "
        "Production environments should use 'verify-full' for maximum security."
    )

# Build connect_args based on SSL configuration
connect_args = {"server_settings": {"application_name": "apulu_studio"}}
if ssl_context is not None:
    connect_args["ssl"] = ssl_context

# SQLAlchemy async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    connect_args=connect_args,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Supabase client for storage and realtime features
def get_supabase() -> Client:
    """Get Supabase client instance."""
    return create_client(settings.supabase_url, settings.supabase_key)


def get_supabase_admin() -> Client:
    """Get Supabase admin client with service key."""
    return create_client(settings.supabase_url, settings.supabase_service_key)
