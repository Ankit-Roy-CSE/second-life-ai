import os
import pytest


@pytest.fixture(autouse=True)
def _restore_ai_mode():
    prior = os.environ.get("AI_MODE")
    try:
        yield
    finally:
        if prior is None:
            os.environ.pop("AI_MODE", None)
        else:
            os.environ["AI_MODE"] = prior
