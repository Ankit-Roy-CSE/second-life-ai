/**
 * Shared enums for Amazon Second Life AI (TypeScript mirror).
 *
 * These enums MUST stay in sync with the Python source:
 * packages/shared-py/shared_py/schemas/enums.py
 *
 * When modifying:
 * 1. Update packages/shared-py/shared_py/schemas/enums.py
 * 2. Update this file
 * 3. Commit both in the same PR
 * 4. Note in docs/code-standards.md §4.1 if it affects contracts
 */

/**
 * Product condition grade assigned by the AI Grading Service.
 *
 * A = Excellent (like new, minimal wear)
 * B = Good (minor cosmetic defects, fully functional)
 * C = Fair (moderate wear, functional issues possible)
 * D = Poor (significant damage, refurbish/recycle candidate)
 */
export enum Grade {
  A = "A",
  B = "B",
  C = "C",
  D = "D",
}

/**
 * Lifecycle decision for a returned product.
 *
 * Determined by the Lifecycle Decision Service based on grade, category, and value.
 */
export enum LifecycleAction {
  RESELL = "RESELL", // Resell as-is (Grade A/B)
  REFURBISH = "REFURBISH", // Repair/refurbish then resell (Grade B/C)
  DONATE = "DONATE", // Donate to charity (low value, functional)
  RECYCLE = "RECYCLE", // Recycle materials (Grade D, damaged beyond repair)
  HYPERLOCAL = "HYPERLOCAL", // Match to nearby buyer for pickup (any grade)
}

/**
 * Status of a product return as it flows through the event saga.
 *
 * FAILED is set when the saga encounters an unrecoverable error (e.g. DLQ'd event).
 */
export enum ReturnStatus {
  SUBMITTED = "SUBMITTED", // Return created, awaiting grading
  GRADED = "GRADED", // AI grading complete
  DECIDED = "DECIDED", // Lifecycle decision made
  PASSPORTED = "PASSPORTED", // Digital passport created
  MATCHING = "MATCHING", // Hyperlocal matching in progress
  LISTED = "LISTED", // Listed in marketplace or matched to buyer
  SOLD = "SOLD", // Purchase completed
  FAILED = "FAILED", // Saga failed (event DLQ'd or unrecoverable error)
}

/**
 * Channel where a product is listed for sale.
 */
export enum ListingChannel {
  HYPERLOCAL = "HYPERLOCAL", // Matched to a nearby buyer for local pickup
  MARKETPLACE = "MARKETPLACE", // Listed in the general refurbished marketplace
}

/**
 * Status of a product listing.
 */
export enum ListingStatus {
  ACTIVE = "ACTIVE", // Available for purchase
  RESERVED = "RESERVED", // Reserved by a buyer (payment pending)
  SOLD = "SOLD", // Purchase completed
  EXPIRED = "EXPIRED", // Listing expired without sale
}
