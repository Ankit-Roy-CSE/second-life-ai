"""
Event envelope and payload schemas for the Amazon Second Life AI event saga.

All events flow through Redis Streams (`slmai:events`) with a consistent envelope.
Event payloads (the `data` field) are defined here as typed Pydantic models.

See architecture.md §6 for the full event catalog and sequence.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# Event Envelope (wraps every message)
# ═══════════════════════════════════════════════════════════════════════════


class EventEnvelope(BaseModel):
    """
    The standard envelope for every event published to `slmai:events`.

    Fields:
        event_id: Unique ID for this event instance (UUID v4) — used for idempotency.
        event_type: PascalCase name of the event (e.g. "ProductGraded").
        event_version: Semantic version of the payload schema (e.g. "1.0").
        occurred_at: ISO-8601 UTC timestamp when the event was created.
        correlation_id: The return/saga ID threading this event through the system.
        producer: Service name that emitted the event (e.g. "grading").
        data: Event-specific payload (one of the *EventData models below).
    """

    event_id: str = Field(..., description="UUID v4 string, unique per event instance")
    event_type: str = Field(..., description="PascalCase event name")
    event_version: str = Field(default="1.0", description="Payload schema version")
    occurred_at: datetime = Field(..., description="ISO-8601 UTC timestamp")
    correlation_id: str = Field(..., description="Return/saga ID")
    producer: str = Field(..., description="Service name that emitted the event")
    data: dict[str, Any] = Field(..., description="Event-specific payload")


# ═══════════════════════════════════════════════════════════════════════════
# Event Payloads (the `data` field for each event_type)
# ═══════════════════════════════════════════════════════════════════════════


class ReturnSubmittedEventData(BaseModel):
    """
    Payload for `ReturnSubmitted` event.
    
    Producer: gateway (after creating the Return entity).
    Consumer: grading service.
    """

    return_id: str = Field(..., description="UUID of the Return")
    product_id: str = Field(..., description="UUID of the Product")
    user_id: str = Field(..., description="UUID of the User who submitted the return")
    reason: str = Field(..., description="Return reason (user-provided text)")
    media: list[str] = Field(
        default_factory=list,
        description="S3/MinIO object keys for uploaded images/videos",
    )


class ProductGradedEventData(BaseModel):
    """
    Payload for `ProductGraded` event.
    
    Producer: grading service (after AI analysis).
    Consumers: lifecycle service, passport service.
    """

    return_id: str = Field(..., description="UUID of the Return")
    grade_id: str = Field(..., description="UUID of the Grade entity")
    product_id: str = Field(..., description="UUID of the Product")
    grade: str = Field(..., description="Grade (A/B/C/D)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0–1")
    damage_summary: str = Field(..., description="AI-generated damage summary text")
    defects: list[str] = Field(
        default_factory=list, description="List of detected defect labels"
    )
    original_price_usd: float | None = Field(
        default=None,
        description="Catalogue/purchase price in USD; None when not available",
    )


class LifecycleDecisionCreatedEventData(BaseModel):
    """
    Payload for `LifecycleDecisionCreated` event.
    
    Producer: lifecycle service (after decision logic + AI rationale).
    Consumers: passport service, matching service.
    """

    return_id: str = Field(..., description="UUID of the Return")
    decision_id: str = Field(..., description="UUID of the LifecycleDecision entity")
    grade_id: str = Field(..., description="UUID of the Grade")
    action: str = Field(
        ..., description="Lifecycle action (RESELL/REFURBISH/DONATE/RECYCLE/HYPERLOCAL)"
    )
    rationale: str = Field(..., description="AI-generated rationale for the decision")
    value_recovery_estimate: float = Field(
        ..., description="Estimated value recovery in dollars"
    )
    sustainability_score: float = Field(
        ..., ge=0.0, le=100.0, description="Sustainability score 0–100"
    )


class PassportCreatedEventData(BaseModel):
    """
    Payload for `PassportCreated` event.
    
    Producer: passport service (after building the digital passport).
    Consumer: matching service.
    """

    passport_id: str = Field(..., description="UUID of the Passport entity")
    product_id: str = Field(..., description="UUID of the Product")
    return_id: str = Field(..., description="UUID of the Return")
    current_grade: str = Field(..., description="Current grade (A/B/C/D)")


class HyperlocalMatchRequestedEventData(BaseModel):
    """
    Payload for `HyperlocalMatchRequested` event.
    
    Producer: passport service (triggers matching flow).
    Consumer: matching service.
    """

    return_id: str = Field(..., description="UUID of the Return")
    product_id: str = Field(..., description="UUID of the Product")
    category: str = Field(..., description="Product category for matching")
    passport_id: str | None = Field(
        default=None,
        description="UUID of the Passport; used by matching to link listings back to the passport",
    )
    location: dict[str, Any] = Field(
        ..., description="Location dict with lat, lng, city fields"
    )


class MatchFoundEventData(BaseModel):
    """
    Payload for `MatchFound` event.
    
    Producer: matching service (after finding nearby buyers).
    Consumers: sustainability service, passport service.
    """

    return_id: str = Field(..., description="UUID of the Return")
    match_request_id: str = Field(..., description="UUID of the MatchRequest")
    buyer_user_id: str = Field(..., description="UUID of the matched buyer User")
    score: float = Field(..., ge=0.0, le=100.0, description="Match score 0–100")
    estimated_savings: float = Field(
        ..., description="Estimated logistics/CO2 savings in dollars"
    )
    distance_km: float = Field(..., description="Distance to buyer in kilometers")


class NoMatchFoundEventData(BaseModel):
    """
    Payload for `NoMatchFound` event.
    
    Producer: matching service (when no nearby buyers meet the criteria).
    Consumer: sustainability service.
    """

    return_id: str = Field(..., description="UUID of the Return")
    match_request_id: str = Field(..., description="UUID of the MatchRequest")
    reason: str = Field(..., description="Reason why no match was found")


class ProductListedEventData(BaseModel):
    """
    Payload for `ProductListed` event.
    
    Producer: matching service (after creating a Listing).
    Consumer: sustainability service.
    """

    listing_id: str = Field(..., description="UUID of the Listing entity")
    product_id: str = Field(..., description="UUID of the Product")
    return_id: str = Field(..., description="UUID of the Return")
    channel: str = Field(
        ..., description="Listing channel (HYPERLOCAL/MARKETPLACE)"
    )
    price: float = Field(..., description="Listing price in dollars")
    status: str = Field(..., description="Listing status (ACTIVE/RESERVED/SOLD/EXPIRED)")


class PurchaseCompletedEventData(BaseModel):
    """
    Payload for `PurchaseCompleted` event.
    
    Producer: matching service or gateway (demo-triggered).
    Consumers: sustainability service, passport service.
    """

    listing_id: str = Field(..., description="UUID of the Listing")
    product_id: str = Field(..., description="UUID of the Product")
    return_id: str = Field(..., description="UUID of the Return")
    buyer_user_id: str = Field(..., description="UUID of the buyer User")
    price: float = Field(..., description="Final purchase price in dollars")


class SustainabilityUpdatedEventData(BaseModel):
    """
    Payload for `SustainabilityUpdated` event.
    
    Producer: sustainability service (after calculating metrics).
    Consumer: gateway (updates read-model/aggregates for dashboard).
    """

    return_id: str = Field(..., description="UUID of the Return")
    product_id: str = Field(..., description="UUID of the Product")
    sustainability_record_id: str = Field(
        ..., description="UUID of the SustainabilityRecord entity"
    )
    co2_avoided_kg: float = Field(..., description="CO2 avoided in kilograms")
    waste_diverted_kg: float = Field(..., description="Waste diverted in kilograms")
    value_recovered: float = Field(..., description="Value recovered in dollars")
    green_credits: float = Field(..., description="Green credits awarded to the user")


# ═══════════════════════════════════════════════════════════════════════════
# Event Type Registry (map event_type → payload model)
# ═══════════════════════════════════════════════════════════════════════════

EVENT_TYPE_TO_MODEL: dict[str, type[BaseModel]] = {
    "ReturnSubmitted": ReturnSubmittedEventData,
    "ProductGraded": ProductGradedEventData,
    "LifecycleDecisionCreated": LifecycleDecisionCreatedEventData,
    "PassportCreated": PassportCreatedEventData,
    "HyperlocalMatchRequested": HyperlocalMatchRequestedEventData,
    "MatchFound": MatchFoundEventData,
    "NoMatchFound": NoMatchFoundEventData,
    "ProductListed": ProductListedEventData,
    "PurchaseCompleted": PurchaseCompletedEventData,
    "SustainabilityUpdated": SustainabilityUpdatedEventData,
}
