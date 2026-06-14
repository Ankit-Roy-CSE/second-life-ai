"""
Sustainability Service — entry point.

Consumes MatchFound / NoMatchFound / ProductListed / PurchaseCompleted
→ calculates CO₂/waste/value/credits → emits SustainabilityUpdated.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared_py.events.handlers import start_consumer, stop_consumer
from shared_py.web import add_ready_check, create_app

from app.api.routes import router as sustainability_router
from app.config import settings
from app.db.session import close_db, init_db

# Register event handlers (side effect: @subscribe decorators run)
import app.events.handlers  # noqa: F401


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Service startup and shutdown."""
    init_db(settings.database_url)

    add_ready_check(name="postgres", fn=_check_postgres)

    consumer_task = asyncio.create_task(
        start_consumer(redis_url=settings.redis_url, group="sustainability")
    )

    yield

    await stop_consumer()
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
    await close_db()


async def _check_postgres() -> str:
    from sqlalchemy import text
    from app.db.session import _engine

    if _engine is None:
        raise RuntimeError("Database engine not initialized")
    try:
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:
        raise RuntimeError(f"Database check failed: {exc}") from exc


app = create_app(service_name=settings.service_name, lifespan=lifespan)
app.include_router(sustainability_router)
