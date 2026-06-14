/**
 * Unit tests for useReturns hook.
 * Validates: Requirements 2.1
 */
import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import React from "react"
import { useReturns, RETURNS_QUERY_KEY } from "./use-returns"
import { apiClient } from "@/lib/api-client"
import type { ReturnResponse } from "../../types/api"
import { ReturnStatus } from "../../types/enums"

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    getReturns: vi.fn(),
  },
}))

const mockReturns: ReturnResponse[] = [
  {
    id: "ret_001",
    product_id: "prod_001",
    user_id: "user_001",
    reason: "Defective screen",
    status: ReturnStatus.SUBMITTED,
    media: [],
    created_at: "2025-01-01T00:00:00Z",
  },
  {
    id: "ret_002",
    product_id: "prod_002",
    user_id: "user_001",
    reason: "Wrong item",
    status: ReturnStatus.GRADED,
    media: [],
    created_at: "2025-01-02T00:00:00Z",
  },
]

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children)
  }
  return Wrapper
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe("useReturns", () => {
  it("resolves with data returned by apiClient.getReturns", async () => {
    vi.mocked(apiClient.getReturns).mockResolvedValue(mockReturns)

    const { result } = renderHook(() => useReturns(), { wrapper: makeWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockReturns)
    expect(apiClient.getReturns).toHaveBeenCalledTimes(1)
  })

  it("uses RETURNS_QUERY_KEY as the query key", async () => {
    vi.mocked(apiClient.getReturns).mockResolvedValue(mockReturns)

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    })

    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(QueryClientProvider, { client: queryClient }, children)
    wrapper.displayName = "QueryClientWrapper"

    const { result } = renderHook(() => useReturns(), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    // The active query cache should contain an entry whose key starts with RETURNS_QUERY_KEY
    const cache = queryClient.getQueryCache().getAll()
    const keys = cache.map((q) => q.queryKey)
    expect(keys).toContainEqual([...RETURNS_QUERY_KEY])
  })

  it("surfaces an error when apiClient.getReturns rejects", async () => {
    vi.mocked(apiClient.getReturns).mockRejectedValue(new Error("Network error"))

    const { result } = renderHook(() => useReturns(), { wrapper: makeWrapper() })

    // The hook has retry: 1, so allow up to 5 s for both attempts to exhaust.
    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 })

    expect(result.current.error?.message).toBe("Network error")
  })

  it("RETURNS_QUERY_KEY is ['returns']", () => {
    expect(RETURNS_QUERY_KEY).toEqual(["returns"])
  })
})
