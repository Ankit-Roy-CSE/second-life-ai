"""
AI Grading Service — entry point.
Full implementation (Rekognition + Bedrock, ProductGraded event) in P1-B1.
"""

from shared_py.web import create_app

from app.config import settings

app = create_app(service_name=settings.service_name)
