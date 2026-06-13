"""
AI wrapper for Amazon Second Life AI.

Public API — import from here in services.

Usage:
    from shared_py.ai import ai_client, GradeResult, LifecycleDecision, MatchRationale
    
    # Full grading pipeline (convenience)
    result = await ai_client.grade_product(
        media_keys=["s3://bucket/image.jpg"],
        return_reason="Defective",
        product_category="electronics",
        correlation_id="return-uuid-123"
    )
    
    # Or use the two-stage spec functions separately:
    labels = await ai_client.analyze_media(media_keys, reason, category, correlation_id=cid)
    summary = await ai_client.summarize_damage(labels, defects, category, correlation_id=cid)
    
    # Decide lifecycle
    decision = await ai_client.decide_lifecycle(
        grade=result.grade,
        product_category="electronics",
        value_estimate=150.00,
        correlation_id="return-uuid-123"
    )
    
    # Generate match rationale
    rationale = await ai_client.match_rationale(
        buyer_distance_km=3.2,
        buyer_interests=["electronics", "gaming"],
        product_category="electronics",
        match_score=0.87,
        correlation_id="return-uuid-123"
    )
"""

from .client import (
    ai_client,
    AIClient,
    AIMode,
    GOLDEN_PATH_MEDIA_KEY,
    GOLDEN_PATH_CATEGORY,
    GOLDEN_PATH_REASON,
)
from .schemas import (
    DefectItem,
    DamageSummary,
    GradeResult,
    LifecycleDecision,
    MatchRationale,
    MediaLabels,
)

__all__ = [
    # Client
    "ai_client",
    "AIClient",
    "AIMode",
    # Golden-path constants
    "GOLDEN_PATH_MEDIA_KEY",
    "GOLDEN_PATH_CATEGORY",
    "GOLDEN_PATH_REASON",
    # Schemas
    "DefectItem",
    "DamageSummary",
    "GradeResult",
    "LifecycleDecision",
    "MatchRationale",
    "MediaLabels",
]

__version__ = "0.1.0"
