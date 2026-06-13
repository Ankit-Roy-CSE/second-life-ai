"""
User Service — entry point.
Full implementation (auth, profile, credits) in P1-A1.
Stub provides working /health and /ready from Phase 0.
"""

from shared_py.web import create_app

from app.config import settings

app = create_app(service_name=settings.service_name)
