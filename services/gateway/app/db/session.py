"""
Database session management for Gateway Service.

Gateway has a minimal database: only the Return table.
No migrations (Alembic) — tables created via SQLAlchemy metadata in lifespan.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Gateway has its own database for the Return table
DATABASE_URL = "postgresql+asyncpg://slmai:slmai_password@postgres:5432/slmai_gateway"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    
    Usage in routes:
        @router.post("/returns")
        async def create_return(
            request: ReturnCreateRequest,
            db: AsyncSession = Depends(get_db)
        ):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
