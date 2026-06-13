"""
API Gateway — entry point.
Full implementation in P1-A2. This stub gives the service a working
/health and /ready endpoint so docker-compose healthchecks pass from Phase 0.
"""

from shared_py.web import create_app

from app.config import settings
from app.api.debug_routes import router as debug_router

app = create_app(service_name=settings.service_name)

# P0-B3: debug/observability routes (read-only event stream view + trigger)
app.include_router(debug_router)

# Routes and lifespan wired in P1-A2:
#   from app.api.routes import router
#   app.include_router(router)
