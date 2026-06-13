"""
User Service — entry point.

Provides:
- Auth: POST /auth/register, POST /auth/login (JWT issuance)
- Profile: GET/PATCH /users/{id}, GET /users/{id}/credits
- Cross-service: GET /users/candidates (for Matching)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared_py.web import create_app

from app.api.routes import router
from app.config import settings
from app.db.session import engine
from app.domain.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown tasks.
    
    Startup:
    - Create database tables (via SQLAlchemy metadata).
      In production, use Alembic migrations instead.
    
    Shutdown:
    - Dispose database engine.
    """
    # Startup: create tables (dev convenience; use Alembic in prod)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown: dispose engine
    await engine.dispose()


# Create app with shared base (health, logging, error handling, CORS)
app = create_app(service_name=settings.service_name, lifespan=lifespan)

# Include user routes
app.include_router(router)
