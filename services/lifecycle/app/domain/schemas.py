"""
Pydantic request/response DTOs for the Lifecycle Decision Service.

These are the service-specific schemas. Shared types (LifecycleAction enum,
event payloads) live in shared_py.schemas.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from shared_py.schemas.enums import LifecycleAction


class DecisionResponse(BaseModel):
    """Response for GET /decisions/{return_id}."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    return_id: str
    grade_id: str
    action: LifecycleAction
    rationale: str
    value_recovery_estimate: float = Field(..., ge=0.0)
    sustainability_score: float = Field(..., ge=0.0, le=100.0)
    created_at: datetime


class DecisionListResponse(BaseModel):
    """Response for GET /decisions (list view)."""

    items: list[DecisionResponse]
    total: int
