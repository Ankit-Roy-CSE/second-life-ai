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


class MetricsTotals(BaseModel):
    """Aggregated totals block — matches frontend `SustainabilityMetricsResponse.totals`."""

    co2_avoided_kg: float = Field(..., ge=0.0)
    waste_diverted_kg: float = Field(..., ge=0.0)
    value_recovered: float = Field(..., ge=0.0)
    green_credits: float = Field(..., ge=0.0)
    returns_processed: int = Field(..., ge=0)


class MetricsBreakdownItem(BaseModel):
    """Per-lifecycle-action breakdown row — matches frontend `breakdown[]`."""

    action: str
    count: int = Field(..., ge=0)
    co2_avoided_kg: float = Field(..., ge=0.0)
    waste_diverted_kg: float = Field(..., ge=0.0)
    value_recovered: float = Field(..., ge=0.0)


class SustainabilityMetricsResponse(BaseModel):
    """
    Aggregated dashboard metrics — matches the frontend contract
    (apps/web/types/api.ts → SustainabilityMetricsResponse).

    The Gateway wraps this inside DashboardMetricsResponse (adds recent_returns,
    top_categories) for GET /sustainability/dashboard.
    """

    totals: MetricsTotals
    breakdown: list[MetricsBreakdownItem]
