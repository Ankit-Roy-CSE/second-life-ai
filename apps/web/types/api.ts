/**
 * API response types for Amazon Second Life AI (TypeScript mirror).
 *
 * These types mirror the Python REST contracts:
 * packages/shared-py/shared_py/schemas/rest_contracts.py
 *
 * Used by the frontend API client and TanStack Query hooks.
 */

import { Grade, LifecycleAction, ListingChannel, ListingStatus, ReturnStatus } from "./enums";

// ═══════════════════════════════════════════════════════════════════════════
// Common
// ═══════════════════════════════════════════════════════════════════════════

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface HealthResponse {
  status: string;
  service: string;
}

export interface ErrorEnvelope {
  error: {
    code: string;
    message: string;
    correlation_id?: string;
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// User Service
// ═══════════════════════════════════════════════════════════════════════════

export interface UserResponse {
  id: string;
  email: string;
  display_name: string;
  location?: {
    lat: number;
    lng: number;
    city: string;
  };
  interests: string[];
  green_credits: number;
  created_at: string;
}

export interface UserCandidateResponse {
  user_id: string;
  display_name: string;
  location: {
    lat: number;
    lng: number;
    city?: string;
  };
  interests: string[];
  distance_km?: number;
}

export interface UserCandidatesListResponse {
  candidates: UserCandidateResponse[];
  total: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  user: UserResponse;
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name: string;
  location?: {
    lat: number;
    lng: number;
    city: string;
  };
  interests?: string[];
}

// ═══════════════════════════════════════════════════════════════════════════
// Gateway / Returns
// ═══════════════════════════════════════════════════════════════════════════

export interface ReturnCreateRequest {
  product_id: string;
  reason: string;
  media_urls: string[];
}

export interface ReturnResponse {
  id: string; // return_id
  product_id: string;
  user_id: string;
  reason: string;
  status: ReturnStatus;
  media: string[]; // S3 keys
  created_at: string;
}

export interface ReturnDetailResponse extends ReturnResponse {
  grade?: GradeResponse;
  decision?: LifecycleDecisionResponse;
  passport?: PassportResponse;
  matches?: MatchResponse[];
}

// ═══════════════════════════════════════════════════════════════════════════
// Grading Service
// ═══════════════════════════════════════════════════════════════════════════

export interface GradeResponse {
  id: string;
  return_id: string;
  product_id: string;
  grade: Grade;
  confidence: number; // 0–1
  damage_summary: string;
  defects: string[];
  created_at: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Lifecycle Service
// ═══════════════════════════════════════════════════════════════════════════

export interface LifecycleDecisionResponse {
  id: string;
  return_id: string;
  grade_id: string;
  action: LifecycleAction;
  rationale: string;
  value_recovery_estimate: number;
  sustainability_score: number; // 0–100
  created_at: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Passport Service
// ═══════════════════════════════════════════════════════════════════════════

export interface ProductResponse {
  id: string;
  owner_user_id: string;
  category: string;
  title: string;
  brand?: string;
  attributes: Record<string, any>;
  created_at: string;
}

export interface PassportTimelineEntry {
  event: string;
  timestamp: string;
  details: Record<string, any>;
}

export interface PassportResponse {
  id: string;
  product_id: string;
  return_id: string;
  current_grade: Grade;
  ownership_history: any[];
  refurb_history: any[];
  sustainability: Record<string, any>;
  status: string;
  timeline?: PassportTimelineEntry[];
  created_at: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Matching Service
// ═══════════════════════════════════════════════════════════════════════════

export interface MatchResponse {
  id: string;
  match_request_id: string;
  buyer_user_id: string;
  buyer_display_name?: string;
  score: number; // 0–100
  estimated_savings: number;
  distance_km: number;
  created_at: string;
}

export interface ListingResponse {
  id: string;
  product_id: string;
  passport_id?: string;
  price: number;
  channel: ListingChannel;
  status: ListingStatus;
  product?: ProductResponse;
  created_at: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Sustainability Service
// ═══════════════════════════════════════════════════════════════════════════

export interface SustainabilityRecordResponse {
  id: string;
  return_id: string;
  product_id: string;
  co2_avoided_kg: number;
  waste_diverted_kg: number;
  value_recovered: number;
  green_credits: number;
  created_at: string;
}

export interface SustainabilityMetricsResponse {
  totals: {
    co2_avoided_kg: number;
    waste_diverted_kg: number;
    value_recovered: number;
    green_credits: number;
    returns_processed: number;
  };
  breakdown: Array<{
    action: LifecycleAction;
    count: number;
    co2_avoided_kg: number;
    waste_diverted_kg: number;
    value_recovered: number;
  }>;
}

export interface DashboardMetricsResponse {
  sustainability: SustainabilityMetricsResponse;
  recent_returns: ReturnResponse[];
  top_categories: Array<{
    category: string;
    count: number;
  }>;
}
