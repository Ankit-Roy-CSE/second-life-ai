"""
Pydantic request/response DTOs for the AI Grading Service.

These are the service-specific schemas. Shared types (Grade enum, event payloads)
live in shared_py.schemas.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from shared_py.schemas.enums import Grade


class DefectOut(BaseModel):
    """Serialised defect item in API responses."""

    name: str
    severity: str
    location: Optional[str] = None
    confidence: float


class GradeResponse(BaseModel):
    """Response for GET /grades/{return_id}."""

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    return_id: str
    product_id: str
    grade: Grade
    confidence: float = Field(..., ge=0.0, le=1.0)
    damage_summary: str
    key_points: list[str]
    defects: list[DefectOut]
    model_version: str
    return_reason: str
    media_keys: list[str]
    created_at: datetime


class GradeListResponse(BaseModel):
    """Response for GET /grades (list view)."""

    items: list[GradeResponse]
    total: int
