# Gateway service entry point — implemented in P1-A2
# Stub to satisfy Docker Compose / healthcheck during Phase 0

from shared_py.web import create_app  # noqa: F401 — will be available after P0-A3

app = create_app(service_name="gateway")
