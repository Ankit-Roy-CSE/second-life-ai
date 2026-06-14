import { ReturnResponse, ReturnDetailResponse, DashboardMetricsResponse, LoginRequest, LoginResponse, RegisterRequest, ReturnCreateRequest, PassportResponse, MatchResponse, ListingResponse } from "../../types/api";
import { ReturnStatus, Grade, LifecycleAction, ListingChannel, ListingStatus } from "../../types/enums";
import { MetricsSchema, type SustainabilityMetrics } from "@/lib/schemas/sustainability";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== "false"; // Default to true in Phase 0

let authToken: string | null = null;

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers);
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }
  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => null);
    throw new Error(errorBody?.error?.message || "API request failed");
  }
  return res.json();
}

export const apiClient = {
  setToken(token: string | null) {
    authToken = token;
  },

  async getReturns(): Promise<ReturnResponse[]> {
    if (USE_MOCKS) return MOCKS.returns;
    const res = await fetch(`${API_BASE_URL}/returns`);
    if (!res.ok) throw new Error("Failed to fetch returns");
    return res.json();
  },
  
  async getReturn(id: string): Promise<ReturnDetailResponse> {
    if (USE_MOCKS) return MOCKS.returnDetail;
    const res = await fetch(`${API_BASE_URL}/returns/${id}`);
    if (!res.ok) throw new Error("Failed to fetch return details");
    return res.json();
  },

  async getPassport(id: string): Promise<PassportResponse> {
    if (USE_MOCKS) return MOCKS.passport;
    const res = await fetch(`${API_BASE_URL}/passports/${id}`);
    if (!res.ok) throw new Error("Failed to fetch passport details");
    return res.json();
  },

  async getMatches(returnId: string): Promise<MatchResponse[]> {
    if (USE_MOCKS) return MOCKS.matches;
    const res = await fetch(`${API_BASE_URL}/matches?return_id=${returnId}`);
    if (!res.ok) throw new Error("Failed to fetch matches");
    return res.json();
  },

  async getMarketplace(channel?: ListingChannel, status?: ListingStatus): Promise<ListingResponse[]> {
    if (USE_MOCKS) return MOCKS.marketplace;
    let url = `${API_BASE_URL}/marketplace?`;
    if (channel) url += `channel=${channel}&`;
    if (status) url += `status=${status}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch marketplace listings");
    return res.json();
  },

  async createReturn(data: ReturnCreateRequest): Promise<ReturnResponse> {
    if (USE_MOCKS) {
      return {
        id: `ret_${Math.random().toString(36).substr(2, 9)}`,
        product_id: data.product_id,
        user_id: "user_mock",
        reason: data.reason,
        status: ReturnStatus.SUBMITTED,
        media: data.media_urls,
        created_at: new Date().toISOString()
      };
    }
    const res = await fetchWithAuth(`${API_BASE_URL}/returns`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    return res;
  },

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    if (USE_MOCKS) return MOCKS.login;
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials)
    });
    if (!res.ok) throw new Error("Login failed");
    return res.json();
  },
  
  async register(data: RegisterRequest): Promise<LoginResponse> {
    if (USE_MOCKS) return MOCKS.login;
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error("Registration failed");
    return res.json();
  },
  
  async getDashboardMetrics(): Promise<DashboardMetricsResponse> {
    if (USE_MOCKS) return MOCKS.dashboard;
    const res = await fetch(`${API_BASE_URL}/sustainability/dashboard`);
    if (!res.ok) throw new Error("Failed to fetch dashboard metrics");
    return res.json();
  },

  async getSustainabilityMetrics(userId?: string): Promise<SustainabilityMetrics> {
    if (USE_MOCKS) {
      return MetricsSchema.parse(MOCKS.sustainabilityMetrics);
    }
    const query = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
    const res = await fetch(`${API_BASE_URL}/sustainability/metrics${query}`);
    if (!res.ok) throw new Error("Failed to fetch sustainability metrics");
    const json = await res.json();
    return MetricsSchema.parse(json);
  }
};

const MOCKS = {
  returns: [
    {
      id: "ret_123",
      product_id: "prod_1",
      user_id: "user_1",
      reason: "Defective",
      status: ReturnStatus.SUBMITTED,
      media: [],
      created_at: new Date().toISOString()
    }
  ],
  returnDetail: {
    id: "ret_123",
    product_id: "prod_1",
    user_id: "user_1",
    reason: "Defective",
    status: ReturnStatus.GRADED,
    media: [],
    created_at: new Date().toISOString(),
    grade: {
      id: "grd_1",
      return_id: "ret_123",
      product_id: "prod_1",
      grade: Grade.A,
      confidence: 0.95,
      damage_summary: "No visible damage",
      defects: [],
      created_at: new Date().toISOString()
    },
    decision: {
      id: "dec_1",
      return_id: "ret_123",
      grade_id: "grd_1",
      action: LifecycleAction.RESELL,
      rationale: "Grade A product with no damage; suitable for immediate resale.",
      value_recovery_estimate: 249.99,
      sustainability_score: 95,
      created_at: new Date().toISOString()
    },
    passport: {
      id: "pass_123",
      product_id: "prod_1",
      return_id: "ret_123",
      current_grade: Grade.A,
      ownership_history: [],
      refurb_history: [],
      sustainability: {},
      status: "ACTIVE",
      created_at: new Date().toISOString()
    }
  },
  passport: {
    id: "pass_123",
    product_id: "prod_1",
    return_id: "ret_123",
    current_grade: Grade.A,
    ownership_history: [
      { owner_id: "user_1", start_date: "2024-01-10T10:00:00Z", end_date: new Date().toISOString() }
    ],
    refurb_history: [],
    sustainability: {
      co2_avoided_kg: 15.4,
      waste_diverted_kg: 2.1
    },
    status: "ACTIVE",
    timeline: [
      { event: "Product Manufactured", timestamp: "2023-11-01T08:00:00Z", details: { location: "Factory A" } },
      { event: "Original Purchase", timestamp: "2024-01-10T10:00:00Z", details: { channel: "Amazon.com" } },
      { event: "Return Submitted", timestamp: new Date(Date.now() - 86400000).toISOString(), details: { reason: "Defective" } },
      { event: "AI Grading Completed", timestamp: new Date(Date.now() - 43200000).toISOString(), details: { grade: Grade.A, confidence: "95%" } },
      { event: "Lifecycle Decision Made", timestamp: new Date(Date.now() - 3600000).toISOString(), details: { action: "RESELL", value_recovery: "$249.99" } },
      { event: "Digital Passport Created", timestamp: new Date().toISOString(), details: { passport_id: "pass_123" } }
    ],
    created_at: new Date().toISOString()
  },
  matches: [
    {
      id: "match_1",
      match_request_id: "req_1",
      buyer_user_id: "buyer_1",
      buyer_display_name: "Alice J.",
      score: 92,
      estimated_savings: 15.50,
      distance_km: 2.4,
      created_at: new Date().toISOString()
    },
    {
      id: "match_2",
      match_request_id: "req_1",
      buyer_user_id: "buyer_2",
      buyer_display_name: "Bob S.",
      score: 85,
      estimated_savings: 12.00,
      distance_km: 5.1,
      created_at: new Date().toISOString()
    },
    {
      id: "match_3",
      match_request_id: "req_1",
      buyer_user_id: "buyer_3",
      buyer_display_name: "Charlie D.",
      score: 65,
      estimated_savings: 5.20,
      distance_km: 12.8,
      created_at: new Date().toISOString()
    }
  ],
  marketplace: [
    {
      id: "list_1",
      product_id: "prod_1",
      price: 249.99,
      channel: ListingChannel.MARKETPLACE,
      status: ListingStatus.ACTIVE,
      product: {
        id: "prod_1",
        owner_user_id: "user_sys",
        category: "electronics",
        title: "Sony WH-1000XM4 Wireless Headphones",
        attributes: {},
        created_at: new Date().toISOString()
      },
      created_at: new Date().toISOString()
    },
    {
      id: "list_2",
      product_id: "prod_2",
      price: 89.99,
      channel: ListingChannel.HYPERLOCAL,
      status: ListingStatus.ACTIVE,
      product: {
        id: "prod_2",
        owner_user_id: "user_sys",
        category: "electronics",
        title: "Logitech MX Master 3 Mouse",
        attributes: {},
        created_at: new Date().toISOString()
      },
      created_at: new Date().toISOString()
    }
  ],
  login: {
    access_token: "mock-jwt-token",
    user: {
      id: "user_1",
      email: "demo@amazon.com",
      display_name: "Demo Customer",
      interests: ["electronics"],
      green_credits: 150,
      created_at: new Date().toISOString()
    }
  },
  dashboard: {
    sustainability: {
      totals: {
        co2_avoided_kg: 120.5,
        waste_diverted_kg: 45.2,
        value_recovered: 850.0,
        green_credits: 320,
        returns_processed: 12
      },
      breakdown: []
    },
    recent_returns: [],
    top_categories: []
  },
  sustainabilityMetrics: {
    totals: {
      co2_avoided_kg: 120.5,
      waste_diverted_kg: 45.2,
      value_recovered: 850.0,
      green_credits: 320,
      returns_processed: 12,
    },
    breakdown: [
      { action: "RESELL",     count: 5, co2_avoided_kg: 60.0, waste_diverted_kg: 20.0, value_recovered: 500.0 },
      { action: "REFURBISH",  count: 3, co2_avoided_kg: 30.5, waste_diverted_kg: 12.2, value_recovered: 250.0 },
      { action: "DONATE",     count: 2, co2_avoided_kg: 18.0, waste_diverted_kg:  8.0, value_recovered:  60.0 },
      { action: "RECYCLE",    count: 1, co2_avoided_kg:  6.0, waste_diverted_kg:  3.0, value_recovered:  20.0 },
      { action: "HYPERLOCAL", count: 1, co2_avoided_kg:  6.0, waste_diverted_kg:  2.0, value_recovered:  20.0 },
    ],
  }
};
