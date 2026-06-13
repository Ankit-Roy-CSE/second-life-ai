"""
Mock AI implementation for Amazon Second Life AI.

Deterministic, reproducible AI responses seeded from input hashes.
Runs without network access or AWS credentials.

The mock mode produces realistic, consistent results suitable for:
- Local development
- CI/CD testing
- Demos without AWS access
- Golden-path demo product scenario
"""

import hashlib
from typing import Any
from shared_py.schemas.enums import Grade, LifecycleAction
from .schemas import (
    DefectItem,
    DamageSummary,
    GradeResult,
    LifecycleDecision,
    MatchRationale,
    MediaLabels,
)


def _hash_input(value: Any) -> int:
    """
    Deterministic hash of input value to an integer seed.
    
    Same input always produces same seed, making mock responses reproducible.
    """
    content = str(value).encode("utf-8")
    return int(hashlib.md5(content).hexdigest()[:8], 16)


def _media_seed(media_keys: list[str], return_reason: str = "", product_category: str = "") -> int:
    """
    Deterministic seed from media keys, falling back to reason+category if empty.
    
    This ensures products without media still get varied (but deterministic) grades
    rather than all hashing to the same "default" value.
    """
    if media_keys:
        return _hash_input(media_keys[0])
    return _hash_input(f"{return_reason}:{product_category}")


def _grade_from_seed(seed: int) -> Grade:
    """Map seed to a Grade using deterministic distribution."""
    bucket = seed % 100
    if bucket < 35:
        return Grade.A  # 35% Grade A
    elif bucket < 65:
        return Grade.B  # 30% Grade B
    elif bucket < 85:
        return Grade.C  # 20% Grade C
    else:
        return Grade.D  # 15% Grade D


def _defects_from_seed(seed: int, grade: Grade) -> list[DefectItem]:
    """Generate realistic defects based on grade."""
    defect_pool = [
        ("scratch", "minor", "front panel"),
        ("dent", "moderate", "corner"),
        ("discoloration", "minor", "back cover"),
        ("wear mark", "minor", "edges"),
        ("scuff", "moderate", "bottom"),
        ("crack", "severe", "screen"),
        ("chip", "moderate", "casing"),
        ("stain", "minor", "surface"),
    ]

    # Grade A: 0-1 minor defects
    # Grade B: 1-2 minor/moderate defects
    # Grade C: 2-3 moderate defects
    # Grade D: 3+ defects including severe

    if grade == Grade.A:
        count = 0 if seed % 3 == 0 else 1
        severities = ["minor"]
    elif grade == Grade.B:
        count = 1 + (seed % 2)
        severities = ["minor", "moderate"]
    elif grade == Grade.C:
        count = 2 + (seed % 2)
        severities = ["moderate"]
    else:  # Grade D
        count = 3 + (seed % 2)
        severities = ["moderate", "severe"]

    defects = []
    for i in range(count):
        defect_seed = (seed + i * 7) % len(defect_pool)
        name, severity, location = defect_pool[defect_seed]
        # Override severity for grade D
        if grade == Grade.D and i == 0:
            severity = "severe"
        elif severity not in severities:
            severity = severities[(seed + i) % len(severities)]

        confidence = 0.75 + ((seed + i) % 20) / 100.0  # 0.75-0.94
        defects.append(
            DefectItem(name=name, severity=severity, location=location, confidence=confidence)
        )

    return defects


def mock_analyze_media(media_keys: list[str], return_reason: str, product_category: str) -> MediaLabels:
    """
    Mock image/video analysis (replaces Rekognition).
    
    Returns deterministic labels seeded from the first media filename.
    """
    seed = _media_seed(media_keys, return_reason, product_category)

    # Generate realistic labels based on category
    category_labels = {
        "electronics": ["device", "screen", "ports", "casing", "buttons"],
        "clothing": ["fabric", "stitching", "zipper", "buttons", "collar"],
        "furniture": ["wood", "upholstery", "legs", "surface", "joints"],
        "toys": ["plastic", "parts", "paint", "moving_parts", "accessories"],
    }

    base_labels = category_labels.get(product_category.lower(), ["item", "surface", "material"])
    labels = base_labels[: 3 + (seed % 3)]  # 3-5 labels

    # Defect cues depend on return reason
    defect_cues = []
    if "defect" in return_reason.lower() or "damage" in return_reason.lower():
        defect_cues = ["scratch_detected", "wear_visible", "imperfection"]
    elif "wrong" in return_reason.lower() or "mismatch" in return_reason.lower():
        defect_cues = []  # Product likely pristine
    else:
        defect_cues = ["minor_wear"] if seed % 2 == 0 else []

    confidence = 0.80 + (seed % 15) / 100.0  # 0.80-0.94

    return MediaLabels(labels=labels, defect_cues=defect_cues, confidence_avg=confidence)


def mock_summarize_damage(
    media_labels: MediaLabels, defects: list[DefectItem], product_category: str
) -> DamageSummary:
    """
    Mock damage summarization (replaces Bedrock text generation).
    
    Produces natural language summary from structured defect data.
    """
    if not defects:
        text = f"Product appears in excellent condition with minimal signs of use. {product_category.capitalize()} shows no significant defects."
        key_points = ["No major defects detected", "Minimal wear", "Fully functional appearance"]
    else:
        severities = [d.severity for d in defects]
        if "severe" in severities:
            text = f"Product shows significant wear and damage. {len(defects)} defects detected including severe issues that may affect functionality."
            key_points = [
                f"{d.name.capitalize()} ({d.severity}) at {d.location}" for d in defects[:3]
            ]
            key_points.append("Refurbishment or recycling recommended")
        elif "moderate" in severities:
            text = f"Product has moderate wear with {len(defects)} visible defects. Functional but cosmetically imperfect."
            key_points = [f"{d.name.capitalize()} on {d.location}" for d in defects[:3]]
            key_points.append("Suitable for refurbished resale")
        else:
            text = f"Product shows minor cosmetic wear. {len(defects)} small defects that do not affect functionality."
            key_points = [f"Minor {d.name}" for d in defects]
            key_points.append("Good candidate for resale")

    return DamageSummary(text=text, key_points=key_points)


def mock_grade_product(
    media_keys: list[str], return_reason: str, product_category: str
) -> GradeResult:
    """
    Complete mock grading pipeline.
    
    Combines analyze_media + defect generation + summarize_damage.
    """
    seed = _media_seed(media_keys, return_reason, product_category)

    # Determine grade from seed
    grade = _grade_from_seed(seed)

    # Generate defects
    defects = _defects_from_seed(seed, grade)

    # Generate labels (for context)
    media_labels = mock_analyze_media(media_keys, return_reason, product_category)

    # Summarize damage
    damage_summary = mock_summarize_damage(media_labels, defects, product_category)

    # Confidence based on grade clarity
    confidence = 0.85 + (seed % 10) / 100.0 if grade in (Grade.A, Grade.D) else 0.75 + (seed % 10) / 100.0

    return GradeResult(
        grade=grade,
        confidence=confidence,
        damage_summary=damage_summary,
        defects=defects,
        model_version="mock-v1",
    )


def mock_decide_lifecycle(
    grade: Grade, product_category: str, value_estimate: float
) -> LifecycleDecision:
    """
    Mock lifecycle decision (replaces Bedrock reasoning).
    
    Uses deterministic decision table based on grade + category + value.
    """
    # Decision table logic
    if grade == Grade.A:
        action = LifecycleAction.RESELL
        rationale = f"Grade A {product_category} is in excellent condition and can be resold as-is with minimal processing."
        value_recovery = value_estimate * 0.75  # 75% of original
        sustainability_score = 85.0
    elif grade == Grade.B:
        if value_estimate > 50:
            action = LifecycleAction.RESELL
            rationale = f"Grade B {product_category} shows minor wear but remains highly valuable. Resell with accurate condition disclosure."
            value_recovery = value_estimate * 0.60
            sustainability_score = 80.0
        else:
            action = LifecycleAction.REFURBISH
            rationale = f"Grade B {product_category} can be refurbished cost-effectively to increase resale value."
            value_recovery = value_estimate * 0.50
            sustainability_score = 75.0
    elif grade == Grade.C:
        if value_estimate > 100:
            action = LifecycleAction.REFURBISH
            rationale = f"Grade C {product_category} requires refurbishment but has sufficient value to justify repair costs."
            value_recovery = value_estimate * 0.40
            sustainability_score = 70.0
        else:
            action = LifecycleAction.DONATE
            rationale = f"Grade C {product_category} has low resale value. Donation maximizes social and environmental impact."
            value_recovery = value_estimate * 0.10
            sustainability_score = 65.0
    else:  # Grade D
        if product_category.lower() in ["electronics", "appliances"]:
            action = LifecycleAction.RECYCLE
            rationale = f"Grade D {product_category} is severely damaged. Recycle to recover materials and prevent e-waste."
            value_recovery = value_estimate * 0.05
            sustainability_score = 50.0
        else:
            action = LifecycleAction.DONATE
            rationale = f"Grade D {product_category} can still serve basic function. Donate for charitable reuse."
            value_recovery = value_estimate * 0.05
            sustainability_score = 55.0

    # Add hyperlocal override for high sustainability items
    seed = _hash_input(f"{grade}{product_category}")
    if seed % 5 == 0 and grade in (Grade.A, Grade.B):
        action = LifecycleAction.HYPERLOCAL
        rationale = f"Hyperlocal match opportunity detected. {product_category} can be transferred to nearby buyer, avoiding reverse logistics."
        sustainability_score += 10.0

    confidence = 0.90 if grade in (Grade.A, Grade.D) else 0.82

    return LifecycleDecision(
        action=action,
        rationale=rationale,
        value_recovery_estimate=value_recovery,
        sustainability_score=min(sustainability_score, 100.0),
        confidence=confidence,
    )


def mock_match_rationale(
    buyer_distance_km: float, buyer_interests: list[str], product_category: str, match_score: float
) -> MatchRationale:
    """
    Mock buyer match explanation (replaces Bedrock text generation).
    
    Generates human-readable rationale for hyperlocal matches.
    """
    factors = []

    # Distance factor
    if buyer_distance_km < 5:
        factors.append(f"Very close proximity ({buyer_distance_km:.1f}km)")
    elif buyer_distance_km < 15:
        factors.append(f"Local buyer ({buyer_distance_km:.1f}km away)")
    else:
        factors.append(f"Regional match ({buyer_distance_km:.1f}km)")

    # Interest factor
    if product_category.lower() in [i.lower() for i in buyer_interests]:
        factors.append(f"Strong interest in {product_category}")
    else:
        factors.append("General interest alignment")

    # Score factor
    if match_score > 0.85:
        factors.append("Excellent match quality")
    elif match_score > 0.70:
        factors.append("Good match quality")

    # Logistics benefit
    if buyer_distance_km < 5:
        co2_reduction = 85
    elif buyer_distance_km < 15:
        co2_reduction = 70
    else:
        co2_reduction = 50

    logistics_benefit = f"~{co2_reduction}% CO₂ reduction vs. warehouse return"

    text = f"This buyer is a strong match based on proximity and interests. {factors[0]} enables efficient hyperlocal transfer."

    return MatchRationale(
        text=text, key_factors=factors, logistics_benefit=logistics_benefit
    )
