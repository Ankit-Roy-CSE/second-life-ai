"""
API Gateway — entry point.

The Gateway is the single entry point for the frontend:
- Verifies JWTs and forwards user_id to downstream services
- Proxies auth endpoints to User Service
- Owns the Return entity (creates returns, emits ReturnSubmitted events)
- Aggregates data from multiple services (BFF pattern)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared_py.web import create_app

from app.api.debug_routes import router as debug_router
from app.api.routes import router
from app.clients.http_client import service_client
from app.config import settings
from app.db.session import engine
from app.domain.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown tasks.
    
    Startup:
    - Create Return table via SQLAlchemy metadata
    
    Shutdown:
    - Close HTTP client
    - Dispose database engine
    """
    # Startup: create Return table
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown
    await service_client.close()
    await engine.dispose()


# Create app with shared base
app = create_app(service_name=settings.service_name, lifespan=lifespan)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)  # Main routes (auth proxy, returns)
app.include_router(debug_router)  # Debug/observability routes (P0-B3)
