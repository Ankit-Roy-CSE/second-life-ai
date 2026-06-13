"""
AI response schemas for Amazon Second Life AI.

These Pydantic models define the typed responses from the AI wrapper.
All four AI capabilities return structured data through these schemas.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, confloat
from shared_py.schemas.enums import Grade, LifecycleAction


class DefectItem(BaseModel):
    """A single detected defect or condition issue."""

    name: str = Field(..., description="Defect name (e.g. 'scratch', 'dent', 'discoloration')")
    severity: str = Field(..., description="Severity: 'minor', 'moderate', 'severe'")
    location: Optional[str] = Field(None, description="Where the defect is located on the product")
    confidence: confloat(ge=0.0, le=1.0) = Field(
        ..., description="AI confidence in this detection (0.0-1.0)"
    )


class DamageSummary(BaseModel):
    """
    Natural language summary of product condition.
    
    Produced by the grading service AI after analyzing images/video.
    """

    text: str = Field(..., description="Human-readable damage/condition summary")
    key_points: list[str] = Field(
        default_factory=list, description="Bullet-point list of key findings"
    )


class GradeResult(BaseModel):
    """
    Complete grading result from analyze_media + summarize_damage.
    
    Returned by the AI Grading Service.
    """

    # 'model_version' would collide with Pydantic's protected 'model_' namespace;
    # opt out so the field keeps its meaningful name.
    model_config = ConfigDict(protected_namespaces=())

    grade: Grade = Field(..., description="Assigned condition grade (A/B/C/D)")
    confidence: confloat(ge=0.0, le=1.0) = Field(
        ..., description="Overall grading confidence (0.0-1.0)"
    )
    damage_summary: DamageSummary = Field(..., description="Natural language condition summary")
    defects: list[DefectItem] = Field(
        default_factory=list, description="Specific defects detected"
    )
    model_version: str = Field(
        default="mock-v1", description="AI model version identifier"
    )


class LifecycleDecision(BaseModel):
    """
    Lifecycle routing decision with rationale and value estimate.
    
    Returned by the Lifecycle Decision Service.
    """

    action: LifecycleAction = Field(..., description="Recommended lifecycle action")
    rationale: str = Field(
        ..., description="Explanation for why this action was chosen"
    )
    value_recovery_estimate: float = Field(
        ..., description="Estimated value recovery in USD", ge=0.0
    )
    sustainability_score: confloat(ge=0.0, le=100.0) = Field(
        ..., description="Sustainability impact score (0-100, higher = more sustainable)"
    )
    confidence: confloat(ge=0.0, le=1.0) = Field(
        ..., description="Decision confidence (0.0-1.0)"
    )


class MatchRationale(BaseModel):
    """
    Explanation for a hyperlocal buyer match.
    
    Returned by the Matching Service for each candidate buyer.
    """

    text: str = Field(
        ..., description="Natural language explanation of why this is a good match"
    )
    key_factors: list[str] = Field(
        default_factory=list,
        description="Factors that contributed to the match (e.g. 'Location 2.4km away', 'Interested in electronics')",
    )
    logistics_benefit: Optional[str] = Field(
        None, description="Estimated logistics/sustainability benefit (e.g. '80% CO2 reduction')"
    )


class MediaLabels(BaseModel):
    """
    Label detection results from image/video analysis (Rekognition).
    
    Internal structure used by analyze_media.
    """

    labels: list[str] = Field(default_factory=list, description="Detected labels")
    defect_cues: list[str] = Field(
        default_factory=list, description="Defect indicators detected"
    )
    confidence_avg: confloat(ge=0.0, le=1.0) = Field(
        0.0, description="Average confidence across all labels"
    )
