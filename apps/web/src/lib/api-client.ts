import { ReturnResponse, ReturnDetailResponse, DashboardMetricsResponse, LoginRequest, LoginResponse, RegisterRequest, ReturnCreateRequest } from "../../types/api";
import { ReturnStatus, Grade } from "../../types/enums";

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
    }
  },
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
  }
};
