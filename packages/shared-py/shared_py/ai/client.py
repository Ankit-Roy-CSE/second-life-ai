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
        product_category="electronics"
    )
"""

import logging
from enum import Enum
from typing import Optional
from shared_py.schemas.enums import Grade, LifecycleAction
from .schemas import GradeResult, LifecycleDecision, MatchRationale
from . import mock

logger = logging.getLogger(__name__)


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

    def __init__(self, mode: AIMode = AIMode.MOCK, aws_region: Optional[str] = None):
        self.mode = mode
        self.aws_region = aws_region or "us-east-1"
        self._bedrock_client = None
        self._rekognition_client = None

        logger.info(f"AI client initialized: mode={mode}, region={aws_region}")

    def _ensure_aws_clients(self):
        """Lazy-load AWS clients only when needed."""
        if self.mode == AIMode.MOCK:
            return

        try:
            import boto3

            if not self._rekognition_client:
                self._rekognition_client = boto3.client("rekognition", region_name=self.aws_region)

            if not self._bedrock_client:
                # Bedrock Runtime client for inference
                self._bedrock_client = boto3.client(
                    "bedrock-runtime", region_name=self.aws_region
                )

            logger.info("AWS clients initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize AWS clients: {e}. Falling back to mock mode.")
            self.mode = AIMode.MOCK

    async def grade_product(
        self, media_keys: list[str], return_reason: str, product_category: str
    ) -> GradeResult:
        """
        Analyze product images/video and assign a condition grade.
        
        Combines:
        1. Media analysis (Rekognition DetectLabels)
        2. Defect detection
        3. Grade assignment
        4. Damage summarization (Bedrock text generation)
        
        Args:
            media_keys: S3 keys for product images/videos
            return_reason: Customer's stated return reason
            product_category: Product category (e.g. "electronics")
        
        Returns:
            GradeResult with grade, confidence, defects, and summary
        """
        try:
            if self.mode == AIMode.MOCK:
                result = mock.mock_grade_product(media_keys, return_reason, product_category)
                logger.debug(f"Mock grading: {result.grade} (confidence={result.confidence:.2f})")
                return result

            # AWS mode - real Rekognition + Bedrock
            self._ensure_aws_clients()

            if self.mode == AIMode.MOCK:  # Fell back due to AWS init failure
                return mock.mock_grade_product(media_keys, return_reason, product_category)

            # TODO: Implement real AWS path in P2-B3
            # For now, fall back to mock even in AWS mode
            logger.warning("Real AWS grading not yet implemented. Using mock.")
            return mock.mock_grade_product(media_keys, return_reason, product_category)

        except Exception as e:
            logger.error(f"AI grading failed: {e}. Falling back to mock.")
            return mock.mock_grade_product(media_keys, return_reason, product_category)

    async def decide_lifecycle(
        self, grade: Grade, product_category: str, value_estimate: float
    ) -> LifecycleDecision:
        """
        Determine optimal lifecycle action for a graded product.
        
        Uses decision table logic + Bedrock for rationale generation.
        
        Args:
            grade: Product condition grade (A/B/C/D)
            product_category: Product category
            value_estimate: Estimated product value (USD)
        
        Returns:
            LifecycleDecision with action, rationale, value recovery, and sustainability score
        """
        try:
            if self.mode == AIMode.MOCK:
                result = mock.mock_decide_lifecycle(grade, product_category, value_estimate)
                logger.debug(
                    f"Mock lifecycle: {result.action} (value_recovery=${result.value_recovery_estimate:.2f})"
                )
                return result

            # AWS mode - decision table + Bedrock rationale
            self._ensure_aws_clients()

            if self.mode == AIMode.MOCK:
                return mock.mock_decide_lifecycle(grade, product_category, value_estimate)

            # TODO: Implement real AWS path in P2-B3
            logger.warning("Real AWS lifecycle decision not yet implemented. Using mock.")
            return mock.mock_decide_lifecycle(grade, product_category, value_estimate)

        except Exception as e:
            logger.error(f"AI lifecycle decision failed: {e}. Falling back to mock.")
            return mock.mock_decide_lifecycle(grade, product_category, value_estimate)

    async def generate_match_rationale(
        self,
        buyer_distance_km: float,
        buyer_interests: list[str],
        product_category: str,
        match_score: float,
    ) -> MatchRationale:
        """
        Generate human-readable explanation for a hyperlocal buyer match.
        
        Uses Bedrock for natural language generation.
        
        Args:
            buyer_distance_km: Distance to buyer in kilometers
            buyer_interests: Buyer's stated interests/categories
            product_category: Product category
            match_score: Match quality score (0.0-1.0)
        
        Returns:
            MatchRationale with text explanation, key factors, and logistics benefit
        """
        try:
            if self.mode == AIMode.MOCK:
                result = mock.mock_match_rationale(
                    buyer_distance_km, buyer_interests, product_category, match_score
                )
                logger.debug(f"Mock match rationale: score={match_score:.2f}")
                return result

            # AWS mode - Bedrock text generation
            self._ensure_aws_clients()

            if self.mode == AIMode.MOCK:
                return mock.mock_match_rationale(
                    buyer_distance_km, buyer_interests, product_category, match_score
                )

            # TODO: Implement real AWS path in P2-B3
            logger.warning("Real AWS match rationale not yet implemented. Using mock.")
            return mock.mock_match_rationale(
                buyer_distance_km, buyer_interests, product_category, match_score
            )

        except Exception as e:
            logger.error(f"AI match rationale failed: {e}. Falling back to mock.")
            return mock.mock_match_rationale(
                buyer_distance_km, buyer_interests, product_category, match_score
            )


# Module-level singleton instance
# Configured from environment at import time
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

    return AIClient(mode=mode, aws_region=aws_region)


# Global singleton instance
ai_client = _create_client()
