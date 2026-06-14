"""
Pydantic request/response DTOs for the Sustainability Service.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SustainabilityRecordResponse(BaseModel):
    """Response for GET /sustainability/{id} and list items."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    return_id: str
    product_id: str
    user_id: str
    co2_avoided_kg: float = Field(..., ge=0.0)
    waste_diverted_kg: float = Field(..., ge=0.0)
    value_recovered: float = Field(..., ge=0.0)
    green_credits: float = Field(..., ge=0.0)
    lifecycle_stage: str
    created_at: datetime
    updated_at: datetime


class SustainabilityListResponse(BaseModel):
    """Response for GET /sustainability (paginated list)."""

    items: list[SustainabilityRecordResponse]
    total: int


class SustainabilityMetricsResponse(BaseModel):
    """Response for GET /sustainability/metrics — aggregated totals."""

    total_co2_avoided_kg: float = Field(..., ge=0.0)
    total_waste_diverted_kg: float = Field(..., ge=0.0)
    total_value_recovered: float = Field(..., ge=0.0)
    total_green_credits: float = Field(..., ge=0.0)
    total_returns_processed: int = Field(..., ge=0)
    records: list[SustainabilityRecordResponse]
