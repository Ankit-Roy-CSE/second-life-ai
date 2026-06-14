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

import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Optional

from shared_py.schemas.enums import Grade, LifecycleAction
from .schemas import (
    DamageSummary,
    DefectItem,
    GradeResult,
    LifecycleDecision,
    MatchRationale,
    MediaLabels,
)
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

# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════

BEDROCK_TIMEOUT_SECONDS = 12
REKOGNITION_TIMEOUT_SECONDS = 8
PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    """Load a prompt template from the prompts directory."""
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8")


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
            from botocore.config import Config

            bedrock_config = Config(
                read_timeout=BEDROCK_TIMEOUT_SECONDS,
                connect_timeout=5,
                retries={"max_attempts": 1},
            )
            rekognition_config = Config(
                read_timeout=REKOGNITION_TIMEOUT_SECONDS,
                connect_timeout=5,
                retries={"max_attempts": 1},
            )

            if not self._rekognition_client:
                self._rekognition_client = boto3.client(
                    "rekognition",
                    region_name=self.aws_region,
                    config=rekognition_config,
                )

            if not self._bedrock_client:
                self._bedrock_client = boto3.client(
                    "bedrock-runtime",
                    region_name=self.aws_region,
                    config=bedrock_config,
                )

            logger.info("aws_clients_initialized")
        except Exception as e:
            logger.warning(
                "aws_clients_failed_fallback_to_mock",
                extra={"error": str(e)},
            )
            self.mode = AIMode.MOCK

    # ═══════════════════════════════════════════════════════════════════════
    # AWS Bedrock helpers
    # ═══════════════════════════════════════════════════════════════════════

    def _invoke_bedrock(self, system_prompt: str, user_message: str) -> str:
        """
        Invoke Bedrock Claude model and return the text response.
        
        Raises on failure so callers can fall back to mock.
        """
        self._ensure_aws_clients()
        if self._bedrock_client is None:
            raise RuntimeError("Bedrock client not available")

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        })

        response = self._bedrock_client.invoke_model(
            modelId=self.bedrock_model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )

        response_body = json.loads(response["body"].read())
        # Claude response format: {"content": [{"type": "text", "text": "..."}]}
        return response_body["content"][0]["text"]

    def _parse_json_response(self, text: str) -> dict:
        """
        Parse JSON from Bedrock response, stripping markdown fencing if present.
        
        Raises ValueError on parse failure.
        """
        cleaned = text.strip()
        # Strip markdown code fences if the model wraps output
        if cleaned.startswith("```"):
            # Remove first line (```json or ```) and last line (```)
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        return json.loads(cleaned)

    # ═══════════════════════════════════════════════════════════════════════
    # AWS Rekognition helpers
    # ═══════════════════════════════════════════════════════════════════════

    def _detect_labels_s3(self, s3_key: str) -> dict:
        """
        Call Rekognition DetectLabels on an S3 object.
        
        Expects keys in format "bucket-name/path/to/image.jpg" or just "path/to/image.jpg"
        using the default bucket from S3_BUCKET env var.
        """
        self._ensure_aws_clients()
        if self._rekognition_client is None:
            raise RuntimeError("Rekognition client not available")

        bucket = os.getenv("S3_BUCKET", "slmai-media")

        # Handle s3:// URIs
        key = s3_key
        if key.startswith("s3://"):
            parts = key[5:].split("/", 1)
            if len(parts) == 2:
                bucket = parts[0]
                key = parts[1]
            else:
                key = parts[0]

        response = self._rekognition_client.detect_labels(
            Image={"S3Object": {"Bucket": bucket, "Name": key}},
            MaxLabels=20,
            MinConfidence=60.0,
        )
        return response

    def _detect_moderation_s3(self, s3_key: str) -> dict:
        """Call Rekognition DetectModerationLabels on an S3 object."""
        self._ensure_aws_clients()
        if self._rekognition_client is None:
            raise RuntimeError("Rekognition client not available")

        bucket = os.getenv("S3_BUCKET", "slmai-media")

        key = s3_key
        if key.startswith("s3://"):
            parts = key[5:].split("/", 1)
            if len(parts) == 2:
                bucket = parts[0]
                key = parts[1]
            else:
                key = parts[0]

        response = self._rekognition_client.detect_moderation_labels(
            Image={"S3Object": {"Bucket": bucket, "Name": key}},
            MinConfidence=60.0,
        )
        return response

    # ═══════════════════════════════════════════════════════════════════════
    # Real AWS implementations
    # ═══════════════════════════════════════════════════════════════════════

    def _aws_analyze_media(
        self, media_keys: list[str], return_reason: str, product_category: str
    ) -> MediaLabels:
        """
        Real Rekognition-based media analysis.
        
        Calls DetectLabels + DetectModerationLabels on the first image.
        """
        if not media_keys:
            raise ValueError("No media keys provided for Rekognition analysis")

        primary_key = media_keys[0]

        # DetectLabels for general labels
        label_response = self._detect_labels_s3(primary_key)
        labels = [lbl["Name"].lower().replace(" ", "_") for lbl in label_response.get("Labels", [])]

        # DetectModerationLabels for damage/defect cues
        moderation_response = self._detect_moderation_s3(primary_key)
        moderation_labels = [
            lbl["Name"].lower().replace(" ", "_")
            for lbl in moderation_response.get("ModerationLabels", [])
        ]

        # Extract defect cues from labels that suggest damage
        damage_keywords = {
            "scratch", "crack", "dent", "broken", "damaged", "wear",
            "stain", "chip", "tear", "discoloration", "rust", "corrosion",
        }
        defect_cues = []
        for label in labels + moderation_labels:
            for keyword in damage_keywords:
                if keyword in label:
                    defect_cues.append(f"{keyword}_detected")
                    break

        # Also add cues based on return reason
        if "defect" in return_reason.lower() or "damage" in return_reason.lower():
            if not defect_cues:
                defect_cues.append("defect_reported")

        # Average confidence from Rekognition labels
        confidences = [lbl["Confidence"] / 100.0 for lbl in label_response.get("Labels", [])]
        confidence_avg = sum(confidences) / len(confidences) if confidences else 0.75

        return MediaLabels(
            labels=labels[:10],  # Cap at 10 most relevant
            defect_cues=defect_cues,
            confidence_avg=min(confidence_avg, 1.0),
        )

    def _aws_grade_product(
        self, media_keys: list[str], return_reason: str, product_category: str
    ) -> GradeResult:
        """
        Real Bedrock-based grading pipeline.
        
        Uses Rekognition for image analysis, then Bedrock Claude for grade + damage summary.
        """
        # Step 1: Get image labels (Rekognition or derive from context)
        media_labels: Optional[MediaLabels] = None
        try:
            if media_keys and self._rekognition_client:
                media_labels = self._aws_analyze_media(media_keys, return_reason, product_category)
        except Exception as e:
            logger.warning("rekognition_failed_using_context_only", extra={"error": str(e)})

        labels_context = ""
        defect_context = ""
        if media_labels:
            labels_context = f"Detected labels: {', '.join(media_labels.labels)}"
            defect_context = (
                f"Defect indicators: {', '.join(media_labels.defect_cues)}"
                if media_labels.defect_cues
                else "Defect indicators: none detected"
            )
        else:
            labels_context = "No image labels available (image analysis unavailable)"
            defect_context = "Defect indicators: unknown"

        # Step 2: Ask Bedrock Claude to grade
        system_prompt = _load_prompt("grading")
        user_message = (
            f"Product category: {product_category}\n"
            f"Return reason: {return_reason}\n"
            f"{labels_context}\n"
            f"{defect_context}\n\n"
            f"Based on this information, provide the product grade and damage assessment."
        )

        raw_response = self._invoke_bedrock(system_prompt, user_message)
        parsed = self._parse_json_response(raw_response)

        # Parse into GradeResult
        grade = Grade(parsed["grade"])
        confidence = float(parsed["confidence"])
        defects = [
            DefectItem(
                name=d["name"],
                severity=d["severity"],
                location=d.get("location", "unknown"),
                confidence=float(d.get("confidence", 0.8)),
            )
            for d in parsed.get("defects", [])
        ]
        damage_summary = DamageSummary(
            text=parsed["damage_summary"]["text"],
            key_points=parsed["damage_summary"].get("key_points", []),
        )

        return GradeResult(
            grade=grade,
            confidence=confidence,
            damage_summary=damage_summary,
            defects=defects,
            model_version=f"bedrock-{self.bedrock_model_id.split('.')[-1][:20]}",
        )

    def _aws_decide_lifecycle(
        self, grade: Grade, product_category: str, value_estimate: float
    ) -> LifecycleDecision:
        """Real Bedrock-based lifecycle decision."""
        system_prompt = _load_prompt("lifecycle")
        user_message = (
            f"Grade: {grade.value}\n"
            f"Product category: {product_category}\n"
            f"Estimated value: ${value_estimate:.2f}\n\n"
            f"Determine the optimal lifecycle action for this product."
        )

        raw_response = self._invoke_bedrock(system_prompt, user_message)
        parsed = self._parse_json_response(raw_response)

        return LifecycleDecision(
            action=LifecycleAction(parsed["action"]),
            rationale=parsed["rationale"],
            value_recovery_estimate=float(parsed["value_recovery_estimate"]),
            sustainability_score=float(parsed["sustainability_score"]),
            confidence=float(parsed["confidence"]),
        )

    def _aws_match_rationale(
        self,
        buyer_distance_km: float,
        buyer_interests: list[str],
        product_category: str,
        match_score: float,
    ) -> MatchRationale:
        """Real Bedrock-based match rationale generation."""
        system_prompt = _load_prompt("matching")
        user_message = (
            f"Buyer distance: {buyer_distance_km:.1f} km\n"
            f"Buyer interests: {', '.join(buyer_interests) if buyer_interests else 'general'}\n"
            f"Product category: {product_category}\n"
            f"Match score: {match_score:.2f}\n\n"
            f"Generate a compelling match explanation."
        )

        raw_response = self._invoke_bedrock(system_prompt, user_message)
        parsed = self._parse_json_response(raw_response)

        return MatchRationale(
            text=parsed["text"],
            key_factors=parsed.get("key_factors", []),
            logistics_benefit=parsed.get("logistics_benefit"),
        )

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
                # Fell back during _ensure_aws_clients
                return mock.mock_analyze_media(media_keys, return_reason, product_category)

            # Real Rekognition path (aws and hybrid both use Rekognition for vision)
            result = self._aws_analyze_media(media_keys, return_reason, product_category)
            logger.info(
                "aws_analyze_media_success",
                extra={**log_extra, "labels": len(result.labels), "defect_cues": len(result.defect_cues)},
            )
            return result

        except Exception as e:
            logger.warning(
                "analyze_media_failed_fallback_to_mock",
                extra={**log_extra, "error": str(e)},
            )
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

            # Real Bedrock path for summarization (aws and hybrid)
            system_prompt = (
                "You are a product condition summarizer. Given detected labels and defects, "
                "produce a concise natural language summary. Respond with ONLY valid JSON:\n"
                '{"text": "1-2 sentence summary", "key_points": ["point 1", "point 2"]}'
            )
            defect_descs = [
                f"{d.name} ({d.severity}) at {d.location}" if hasattr(d, "name") else str(d)
                for d in defects
            ]
            user_message = (
                f"Product category: {product_category}\n"
                f"Detected labels: {', '.join(media_labels.labels)}\n"
                f"Defect cues: {', '.join(media_labels.defect_cues) or 'none'}\n"
                f"Defects found: {'; '.join(defect_descs) or 'none'}\n\n"
                f"Summarize the product condition."
            )

            raw_response = self._invoke_bedrock(system_prompt, user_message)
            parsed = self._parse_json_response(raw_response)

            result = DamageSummary(
                text=parsed["text"],
                key_points=parsed.get("key_points", []),
            )
            logger.info("aws_summarize_damage_success", extra=log_extra)
            return result

        except Exception as e:
            logger.warning(
                "summarize_damage_failed_fallback_to_mock",
                extra={**log_extra, "error": str(e)},
            )
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

            # Real AWS grading (Rekognition + Bedrock)
            result = self._aws_grade_product(media_keys, return_reason, product_category)
            logger.info(
                "aws_grade_product_success",
                extra={**log_extra, "grade": result.grade.value, "confidence": result.confidence},
            )
            return result

        except Exception as e:
            logger.warning(
                "grade_product_failed_fallback_to_mock",
                extra={**log_extra, "error": str(e)},
            )
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
                    extra={
                        **log_extra,
                        "action": result.action.value,
                        "value_recovery": result.value_recovery_estimate,
                    },
                )
                return result

            self._ensure_aws_clients()
            if self.mode == AIMode.MOCK:
                return mock.mock_decide_lifecycle(grade, product_category, value_estimate)

            # Real Bedrock path for lifecycle decision
            # In hybrid mode, Bedrock is used for text generation
            result = self._aws_decide_lifecycle(grade, product_category, value_estimate)
            logger.info(
                "aws_decide_lifecycle_success",
                extra={**log_extra, "action": result.action.value},
            )
            return result

        except Exception as e:
            logger.warning(
                "decide_lifecycle_failed_fallback_to_mock",
                extra={**log_extra, "error": str(e)},
            )
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

            # Real Bedrock path for match rationale
            result = self._aws_match_rationale(
                buyer_distance_km, buyer_interests, product_category, match_score
            )
            logger.info("aws_match_rationale_success", extra=log_extra)
            return result

        except Exception as e:
            logger.warning(
                "match_rationale_failed_fallback_to_mock",
                extra={**log_extra, "error": str(e)},
            )
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
