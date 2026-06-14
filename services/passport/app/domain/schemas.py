"""
Pydantic request/response DTOs for the Product Passport Service.

Shared types (Grade enum, event payloads) live in shared_py.schemas.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from shared_py.schemas.enums import Grade


# ── Product schemas ──────────────────────────────────────────────────────────

class ProductResponse(BaseModel):
    """Response model for Product reads."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_user_id: str
    category: str
    title: str
    brand: str
    attributes: dict[str, Any]
    created_at: datetime


# ── Passport schemas ──────────────────────────────────────────────────────────

class PassportResponse(BaseModel):
    """Response model for GET /passports/{id}."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    return_id: str
    product_id: str
    current_grade: Optional[Grade] = None
    grade_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    damage_summary: Optional[str] = None
    lifecycle_action: Optional[str] = None
    value_recovery_estimate: Optional[float] = None
    sustainability_score: Optional[float] = None
    ownership_history: list[dict[str, Any]]
    refurb_history: list[dict[str, Any]]
    sustainability: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime


class PassportListResponse(BaseModel):
    """Paginated list of passports."""

    items: list[PassportResponse]
    total: int
    limit: int
    offset: int
