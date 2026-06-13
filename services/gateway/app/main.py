"""
API Gateway — entry point.
Full implementation in P1-A2. This stub gives the service a working
/health and /ready endpoint so docker-compose healthchecks pass from Phase 0.
"""

from shared_py.web import create_app

from app.config import settings

app = create_app(service_name=settings.service_name)

# Routes and lifespan wired in P1-A2:
#   from app.api.routes import router
#   app.include_router(router)
