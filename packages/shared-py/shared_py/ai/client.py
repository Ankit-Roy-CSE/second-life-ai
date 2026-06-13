"""
AI client wrapper for Amazon Second Life AI.

Provides a unified interface to AWS Bedrock + Rekognition with seamless mock mode fallback.
All AI calls in the platform go through this wrapper.

Modes (set via AI_MODE env var):
- mock: Deterministic, reproducible, no AWS (default)
- aws: Real AWS Bedrock + Rekognition
- hybrid: Rekognition for vision, Bedrock for text, mock for fallback

Usage:
    from shared_py.ai import ai_client
    
    result = await ai_client.grade_product(
        media_keys=["s3://bucket/image.jpg"],
        return_reason="Defective",
        product_category="electronics",
        correlation_id="return-uuid-123"
    )
"""

import logging
from enum import Enum
from typing import Optional

from shared_py.schemas.enums import Grade
from .schemas import DamageSummary, GradeResult, LifecycleDecision, MatchRationale, MediaLabels
from . import mock

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# Golden-path demo constants
# ═══════════════════════════════════════════════════════════════════════════

# Use this key in seed scripts and demo walkthroughs.
# It produces Grade B → RESELL with good confidence — the ideal demo narrative.
GOLDEN_PATH_MEDIA_KEY = "products/golden-path/demo-headphones-001.jpg"

# The golden-path product category for the demo flow
GOLDEN_PATH_CATEGORY = "electronics"

# The golden-path return reason
GOLDEN_PATH_REASON = "Item not as expected"


class AIMode(str, Enum):
    """AI backend mode."""

    MOCK = "mock"  # Deterministic mock (default)
    AWS = "aws"  # Real AWS Bedrock + Rekognition
    HYBRID = "hybrid"  # Mix of AWS + mock


class AIClient:
    """
    Unified AI client with mode switching and graceful degradation.
    
    Singleton instance configured at module load via AI_MODE env var.
    """

    def __init__(
        self,
        mode: AIMode = AIMode.MOCK,
        aws_region: Optional[str] = None,
        bedrock_model_id: Optional[str] = None,
    ):
        self.mode = mode
        self.aws_region = aws_region or "us-east-1"
        self.bedrock_model_id = bedrock_model_id or "anthropic.claude-3-haiku-20240307-v1:0"
        self._bedrock_client = None
        self._rekognition_client = None

        logger.info(
            "ai_client_initialized",
            extra={"mode": mode, "region": aws_region, "bedrock_model": self.bedrock_model_id},
        )

    def _ensure_aws_clients(self):
        """Lazy-load AWS clients only when needed."""
        if self.mode == AIMode.MOCK:
            return

        try:
            import boto3

            if not self._rekognition_client:
                self._rekognition_client = boto3.client("rekognition", region_name=self.aws_region)

            if not self._bedrock_client:
                self._bedrock_client = boto3.client(
                    "bedrock-runtime", region_name=self.aws_region
                )

            logger.info("aws_clients_initialized")
        except Exception as e:
            logger.warning(
                "aws_clients_failed_fallback_to_mock",
                extra={"error": str(e)},
            )
            self.mode = AIMode.MOCK

    # ═══════════════════════════════════════════════════════════════════════
    # Public API — matches spec: analyze_media, summarize_damage,
    # decide_lifecycle, match_rationale + convenience grade_product
    # ═══════════════════════════════════════════════════════════════════════

    async def analyze_media(
        self,
        media_keys: list[str],
        return_reason: str,
        product_category: str,
        *,
        correlation_id: Optional[str] = None,
    ) -> MediaLabels:
        """
        Analyze product images/video and extract labels + defect cues.
        
        Stage 1 of grading pipeline (Rekognition DetectLabels).
        
        Args:
            media_keys: S3 keys for product images/videos
            return_reason: Customer's stated return reason
            product_category: Product category (e.g. "electronics")
            correlation_id: Return ID for structured logging
        
        Returns:
            MediaLabels with detected labels and defect cues
        """
        log_extra = {"correlation_id": correlation_id, "service": "ai"}
        try:
            if self.mode == AIMode.MOCK:
                result = mock.mock_analyze_media(media_keys, return_reason, product_category)
                logger.debug("mock_analyze_media", extra={**log_extra, "labels": len(result.labels)})
                return result

            self._ensure_aws_clients()
            if self.mode == AIMode.MOCK:
                return mock.mock_analyze_media(media_keys, return_reason, product_category)

            # TODO: Implement real Rekognition path in P2-B3
            logger.warning("aws_analyze_media_not_implemented", extra=log_extra)
            return mock.mock_analyze_media(media_keys, return_reason, product_category)

        except Exception as e:
            logger.error("analyze_media_failed", extra={**log_extra, "error": str(e)})
            return mock.mock_analyze_media(media_keys, return_reason, product_category)

    async def summarize_damage(
        self,
        media_labels: MediaLabels,
        defects: list,
        product_category: str,
        *,
        correlation_id: Optional[str] = None,
    ) -> DamageSummary:
        """
        Generate natural language damage summary from structured defect data.
        
        Stage 2 of grading pipeline (Bedrock text generation).
        
        Args:
            media_labels: Labels from analyze_media
            defects: List of DefectItem instances
            product_category: Product category
            correlation_id: Return ID for structured logging
        
        Returns:
            DamageSummary with text and key_points
        """
        log_extra = {"correlation_id": correlation_id, "service": "ai"}
        try:
            if self.mode == AIMode.MOCK:
                result = mock.mock_summarize_damage(media_labels, defects, product_category)
                logger.debug("mock_summarize_damage", extra=log_extra)
                return result

            self._ensure_aws_clients()
            if self.mode == AIMode.MOCK:
                return mock.mock_summarize_damage(media_labels, defects, product_category)

            # TODO: Implement real Bedrock summarization in P2-B3
            logger.warning("aws_summarize_damage_not_implemented", extra=log_extra)
            return mock.mock_summarize_damage(media_labels, defects, product_category)

        except Exception as e:
            logger.error("summarize_damage_failed", extra={**log_extra, "error": str(e)})
            return mock.mock_summarize_damage(media_labels, defects, product_category)

    async def grade_product(
        self,
        media_keys: list[str],
        return_reason: str,
        product_category: str,
        *,
        correlation_id: Optional[str] = None,
    ) -> GradeResult:
        """
        Full grading pipeline: analyze_media + defects + summarize_damage.
        
        Convenience method that combines the two spec functions into a single call.
        Services can call this directly or use analyze_media + summarize_damage separately.
        
        Args:
            media_keys: S3 keys for product images/videos
            return_reason: Customer's stated return reason
            product_category: Product category (e.g. "electronics")
            correlation_id: Return ID for structured logging
        
        Returns:
            GradeResult with grade, confidence, defects, and summary
        """
        log_extra = {"correlation_id": correlation_id, "service": "ai"}
        try:
            if self.mode == AIMode.MOCK:
                result = mock.mock_grade_product(media_keys, return_reason, product_category)
                logger.debug(
                    "mock_grade_product",
                    extra={**log_extra, "grade": result.grade.value, "confidence": result.confidence},
                )
                return result

            self._ensure_aws_clients()
            if self.mode == AIMode.MOCK:
                return mock.mock_grade_product(media_keys, return_reason, product_category)

            # TODO: Implement real AWS path in P2-B3
            logger.warning("aws_grade_product_not_implemented", extra=log_extra)
            return mock.mock_grade_product(media_keys, return_reason, product_category)

        except Exception as e:
            logger.error("grade_product_failed", extra={**log_extra, "error": str(e)})
            return mock.mock_grade_product(media_keys, return_reason, product_category)

    async def decide_lifecycle(
        self,
        grade: Grade,
        product_category: str,
        value_estimate: float,
        *,
        correlation_id: Optional[str] = None,
    ) -> LifecycleDecision:
        """
        Determine optimal lifecycle action for a graded product.
        
        Uses decision table logic + Bedrock for rationale generation.
        
        Args:
            grade: Product condition grade (A/B/C/D)
            product_category: Product category
            value_estimate: Estimated product value (USD)
            correlation_id: Return ID for structured logging
        
        Returns:
            LifecycleDecision with action, rationale, value recovery, and sustainability score
        """
        log_extra = {"correlation_id": correlation_id, "service": "ai"}
        try:
            if self.mode == AIMode.MOCK:
                result = mock.mock_decide_lifecycle(grade, product_category, value_estimate)
                logger.debug(
                    "mock_decide_lifecycle",
                    extra={**log_extra, "action": result.action.value, "value_recovery": result.value_recovery_estimate},
                )
                return result

            self._ensure_aws_clients()
            if self.mode == AIMode.MOCK:
                return mock.mock_decide_lifecycle(grade, product_category, value_estimate)

            # TODO: Implement real AWS path in P2-B3
            logger.warning("aws_decide_lifecycle_not_implemented", extra=log_extra)
            return mock.mock_decide_lifecycle(grade, product_category, value_estimate)

        except Exception as e:
            logger.error("decide_lifecycle_failed", extra={**log_extra, "error": str(e)})
            return mock.mock_decide_lifecycle(grade, product_category, value_estimate)

    async def match_rationale(
        self,
        buyer_distance_km: float,
        buyer_interests: list[str],
        product_category: str,
        match_score: float,
        *,
        correlation_id: Optional[str] = None,
    ) -> MatchRationale:
        """
        Generate human-readable explanation for a hyperlocal buyer match.
        
        Uses Bedrock for natural language generation.
        
        Args:
            buyer_distance_km: Distance to buyer in kilometers
            buyer_interests: Buyer's stated interests/categories
            product_category: Product category
            match_score: Match quality score (0.0-1.0)
            correlation_id: Return ID for structured logging
        
        Returns:
            MatchRationale with text explanation, key factors, and logistics benefit
        """
        log_extra = {"correlation_id": correlation_id, "service": "ai"}
        try:
            if self.mode == AIMode.MOCK:
                result = mock.mock_match_rationale(
                    buyer_distance_km, buyer_interests, product_category, match_score
                )
                logger.debug(
                    "mock_match_rationale",
                    extra={**log_extra, "score": match_score},
                )
                return result

            self._ensure_aws_clients()
            if self.mode == AIMode.MOCK:
                return mock.mock_match_rationale(
                    buyer_distance_km, buyer_interests, product_category, match_score
                )

            # TODO: Implement real AWS path in P2-B3
            logger.warning("aws_match_rationale_not_implemented", extra=log_extra)
            return mock.mock_match_rationale(
                buyer_distance_km, buyer_interests, product_category, match_score
            )

        except Exception as e:
            logger.error("match_rationale_failed", extra={**log_extra, "error": str(e)})
            return mock.mock_match_rationale(
                buyer_distance_km, buyer_interests, product_category, match_score
            )

    # Keep backward-compatible alias
    generate_match_rationale = match_rationale


# ═══════════════════════════════════════════════════════════════════════════
# Module-level singleton
# ═══════════════════════════════════════════════════════════════════════════


def _create_client() -> AIClient:
    """Create AI client from environment variables."""
    import os

    mode_str = os.getenv("AI_MODE", "mock").lower()
    try:
        mode = AIMode(mode_str)
    except ValueError:
        logger.warning(f"Invalid AI_MODE '{mode_str}'. Defaulting to 'mock'.")
        mode = AIMode.MOCK

    aws_region = os.getenv("AWS_REGION", "us-east-1")
    bedrock_model_id = os.getenv("BEDROCK_MODEL_ID", None)

    return AIClient(mode=mode, aws_region=aws_region, bedrock_model_id=bedrock_model_id)


# Global singleton instance
ai_client = _create_client()
