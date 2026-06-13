"""
AI wrapper for Amazon Second Life AI.

Public API — import from here in services.

Usage:
    from shared_py.ai import ai_client, GradeResult, LifecycleDecision, MatchRationale
    
    # Grade a product
    result = await ai_client.grade_product(
        media_keys=["s3://bucket/image.jpg"],
        return_reason="Defective",
        product_category="electronics"
    )
    
    # Decide lifecycle
    decision = await ai_client.decide_lifecycle(
        grade=result.grade,
        product_category="electronics",
        value_estimate=150.00
    )
    
    # Generate match rationale
    rationale = await ai_client.generate_match_rationale(
        buyer_distance_km=3.2,
        buyer_interests=["electronics", "gaming"],
        product_category="electronics",
        match_score=0.87
    )
"""

from .client import ai_client, AIClient, AIMode
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
    # Schemas
    "DefectItem",
    "DamageSummary",
    "GradeResult",
    "LifecycleDecision",
    "MatchRationale",
    "MediaLabels",
]

__version__ = "0.1.0"
