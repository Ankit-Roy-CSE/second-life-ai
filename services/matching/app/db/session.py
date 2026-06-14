"""
Async SQLAlchemy engine and session factory for the Hyperlocal Matching Service.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared_py.config import get_logger

logger = get_logger(__name__)

_engine = None
_session_factory = None


def init_db(database_url: str) -> None:
    """Initialise the async engine and session factory."""
    global _engine, _session_factory

    _engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    _session_factory = async_sessionmaker(
        bind=_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    logger.info("db_engine_initialized", extra={"service": "matching"})


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async DB session per request.

    Usage in a route:
        async def my_route(db: AsyncSession = Depends(get_db)): ...
    """
    if _session_factory is None:
        raise RuntimeError("DB not initialised — call init_db() in lifespan startup")

    async with _session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db() -> None:
    """Dispose the engine on service shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("db_engine_closed", extra={"service": "matching"})
