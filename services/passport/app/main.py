# Passport service entry point — fully implemented in P2-A1
from shared_py.web import create_app  # noqa: F401

app = create_app(service_name="passport")
