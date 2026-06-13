"""
Shared enums for Amazon Second Life AI.

These enums are the single source of truth for the backend.
They must be mirrored in the frontend (`apps/web/types/enums.ts`).

When adding or modifying an enum:
1. Update this file
2. Update apps/web/types/enums.ts
3. Update both in the same commit
4. Note the change in docs/code-standards.md §4.1 if it affects contracts
"""

from enum import Enum


class Grade(str, Enum):
    """
    Product condition grade assigned by the AI Grading Service.
    
    A = Excellent (like new, minimal wear)
    B = Good (minor cosmetic defects, fully functional)
    C = Fair (moderate wear, functional issues possible)
    D = Poor (significant damage, refurbish/recycle candidate)
    """

    A = "A"
    B = "B"
    C = "C"
    D = "D"


class LifecycleAction(str, Enum):
    """
    Lifecycle decision for a returned product.
    
    Determined by the Lifecycle Decision Service based on grade, category, and value.
    """

    RESELL = "RESELL"  # Resell as-is (Grade A/B)
    REFURBISH = "REFURBISH"  # Repair/refurbish then resell (Grade B/C)
    DONATE = "DONATE"  # Donate to charity (low value, functional)
    RECYCLE = "RECYCLE"  # Recycle materials (Grade D, damaged beyond repair)
    HYPERLOCAL = "HYPERLOCAL"  # Match to nearby buyer for pickup (any grade)


class ReturnStatus(str, Enum):
    """
    Status of a product return as it flows through the event saga.
    
    FAILED is set when the saga encounters an unrecoverable error (e.g. DLQ'd event).
    """

    SUBMITTED = "SUBMITTED"  # Return created, awaiting grading
    GRADED = "GRADED"  # AI grading complete
    DECIDED = "DECIDED"  # Lifecycle decision made
    PASSPORTED = "PASSPORTED"  # Digital passport created
    MATCHING = "MATCHING"  # Hyperlocal matching in progress
    LISTED = "LISTED"  # Listed in marketplace or matched to buyer
    SOLD = "SOLD"  # Purchase completed
    FAILED = "FAILED"  # Saga failed (event DLQ'd or unrecoverable error)


class ListingChannel(str, Enum):
    """
    Channel where a product is listed for sale.
    """

    HYPERLOCAL = "HYPERLOCAL"  # Matched to a nearby buyer for local pickup
    MARKETPLACE = "MARKETPLACE"  # Listed in the general refurbished marketplace


class ListingStatus(str, Enum):
    """
    Status of a product listing.
    """

    ACTIVE = "ACTIVE"  # Available for purchase
    RESERVED = "RESERVED"  # Reserved by a buyer (payment pending)
    SOLD = "SOLD"  # Purchase completed
    EXPIRED = "EXPIRED"  # Listing expired without sale
