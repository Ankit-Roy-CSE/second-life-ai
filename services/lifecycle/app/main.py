"""
Lifecycle Decision Service — entry point.
Full implementation in P1-B2.
"""

from shared_py.web import create_app

from app.config import settings

app = create_app(service_name=settings.service_name)
