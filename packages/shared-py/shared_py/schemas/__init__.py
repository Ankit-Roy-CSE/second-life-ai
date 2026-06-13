"""
shared_py.schemas — shared data models, enums, and contracts.

Exports:
- Enums: Grade, LifecycleAction, ReturnStatus, ListingChannel, ListingStatus
- REST DTOs: Cross-service request/response models
"""

from shared_py.schemas.enums import (
    Grade,
    LifecycleAction,
    ListingChannel,
    ListingStatus,
    ReturnStatus,
)
from shared_py.schemas.rest_contracts import (
    ErrorEnvelope,
    HealthResponse,
    PaginatedResponse,
    ProductResponse,
    ReturnCreateRequest,
    ReturnResponse,
    UserCandidateResponse,
    UserCandidatesListResponse,
)

__all__ = [
    # Enums
    "Grade",
    "LifecycleAction",
    "ReturnStatus",
    "ListingChannel",
    "ListingStatus",
    # REST contracts
    "UserCandidateResponse",
    "UserCandidatesListResponse",
    "ReturnCreateRequest",
    "ReturnResponse",
    "ProductResponse",
    "PaginatedResponse",
    "HealthResponse",
    "ErrorEnvelope",
]
