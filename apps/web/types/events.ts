/**
 * Event types for Amazon Second Life AI (TypeScript mirror).
 *
 * These types mirror the Python event schemas:
 * packages/shared-py/shared_py/events/schemas.py
 *
 * Used by the frontend for type-safe event handling and mocking.
 */

import { Grade, LifecycleAction, ListingChannel, ListingStatus } from "./enums";

/**
 * Event envelope (wraps every message on slmai:events stream).
 */
export interface EventEnvelope<T = Record<string, any>> {
  event_id: string; // UUID v4
  event_type: string; // PascalCase event name
  event_version: string; // e.g. "1.0"
  occurred_at: string; // ISO-8601 UTC timestamp
  correlation_id: string; // Return/saga ID
  producer: string; // Service name
  data: T; // Event-specific payload
}

// ═══════════════════════════════════════════════════════════════════════════
// Event Payloads
// ═══════════════════════════════════════════════════════════════════════════

export interface ReturnSubmittedEventData {
  return_id: string;
  product_id: string;
  user_id: string;
  reason: string;
  media: string[]; // S3/MinIO object keys
}

export interface ProductGradedEventData {
  return_id: string;
  grade_id: string;
  product_id: string;
  grade: Grade;
  confidence: number; // 0–1
  damage_summary: string;
  defects: string[];
}

export interface LifecycleDecisionCreatedEventData {
  return_id: string;
  decision_id: string;
  grade_id: string;
  action: LifecycleAction;
  rationale: string;
  value_recovery_estimate: number;
  sustainability_score: number; // 0–100
}

export interface PassportCreatedEventData {
  passport_id: string;
  product_id: string;
  return_id: string;
  current_grade: Grade;
}

export interface HyperlocalMatchRequestedEventData {
  return_id: string;
  product_id: string;
  category: string;
  location: {
    lat: number;
    lng: number;
    city?: string;
  };
}

export interface MatchFoundEventData {
  return_id: string;
  match_request_id: string;
  buyer_user_id: string;
  score: number; // 0–100
  estimated_savings: number;
  distance_km: number;
}

export interface NoMatchFoundEventData {
  return_id: string;
  match_request_id: string;
  reason: string;
}

export interface ProductListedEventData {
  listing_id: string;
  product_id: string;
  return_id: string;
  channel: ListingChannel;
  price: number;
  status: ListingStatus;
}

export interface PurchaseCompletedEventData {
  listing_id: string;
  product_id: string;
  return_id: string;
  buyer_user_id: string;
  price: number;
}

export interface SustainabilityUpdatedEventData {
  return_id: string;
  product_id: string;
  sustainability_record_id: string;
  co2_avoided_kg: number;
  waste_diverted_kg: number;
  value_recovered: number;
  green_credits: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// Event Type Union (for discriminated unions in handlers)
// ═══════════════════════════════════════════════════════════════════════════

export type EventData =
  | ReturnSubmittedEventData
  | ProductGradedEventData
  | LifecycleDecisionCreatedEventData
  | PassportCreatedEventData
  | HyperlocalMatchRequestedEventData
  | MatchFoundEventData
  | NoMatchFoundEventData
  | ProductListedEventData
  | PurchaseCompletedEventData
  | SustainabilityUpdatedEventData;

export type EventType =
  | "ReturnSubmitted"
  | "ProductGraded"
  | "LifecycleDecisionCreated"
  | "PassportCreated"
  | "HyperlocalMatchRequested"
  | "MatchFound"
  | "NoMatchFound"
  | "ProductListed"
  | "PurchaseCompleted"
  | "SustainabilityUpdated";
