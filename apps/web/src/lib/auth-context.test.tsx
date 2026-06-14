/**
 * Tests for AuthContext — Task 7 subtask 7.3
 *
 * Property 5: Logout clears all persisted auth state
 * Validates: Requirements 4.1, 4.2
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest"
import { renderHook, act } from "@testing-library/react"
import * as fc from "fast-check"
import React from "react"
import { AuthProvider, useAuth } from "./auth-context"
import { apiClient } from "./api-client"
import type { UserResponse } from "../../types/api"

// Wrapper that provides the real AuthProvider
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
)

// ---------------------------------------------------------------------------
// Property 5: Logout clears all persisted auth state
// Validates: Requirements 4.1, 4.2
// ---------------------------------------------------------------------------

describe("Property 5: Logout clears all persisted auth state", () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it("clears localStorage and apiClient token for arbitrary auth state", () => {
    fc.assert(
      fc.property(
        // Arbitrary token (non-empty string)
        fc.string({ minLength: 1, maxLength: 128 }),
        // Arbitrary user object
        fc.record({
          id: fc.uuid(),
          email: fc.emailAddress(),
          display_name: fc.string({ minLength: 1, maxLength: 50 }),
          interests: fc.array(fc.string()),
          green_credits: fc.integer({ min: 0, max: 100_000 }),
          created_at: fc.constantFrom("2024-01-01T00:00:00Z"),
        }),
        (token, user: UserResponse) => {
          // Seed localStorage directly as if a prior login happened
          localStorage.setItem("slm_token", token)
          localStorage.setItem("slm_user", JSON.stringify(user))
          apiClient.setToken(token)

          const { result } = renderHook(() => useAuth(), { wrapper })

          act(() => {
            result.current.logout()
          })

          // Both localStorage keys must be cleared
          expect(localStorage.getItem("slm_token")).toBeNull()
          expect(localStorage.getItem("slm_user")).toBeNull()

          // Auth context state must be cleared
          expect(result.current.user).toBeNull()
          expect(result.current.token).toBeNull()
          expect(result.current.isAuthenticated).toBe(false)
        }
      ),
      { numRuns: 30 }
    )
  })

  it("apiClient token is null after logout", () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 128 }),
        (token) => {
          localStorage.setItem("slm_token", token)
          localStorage.setItem("slm_user", JSON.stringify({ id: "u1", email: "a@b.com", display_name: "A", interests: [], green_credits: 0, created_at: "2024-01-01T00:00:00Z" }))
          apiClient.setToken(token)

          const { result } = renderHook(() => useAuth(), { wrapper })

          // Spy on setToken to verify it's called with null
          let capturedToken: string | null = "not-called"
          const origSetToken = apiClient.setToken.bind(apiClient)
          apiClient.setToken = (t) => {
            capturedToken = t
            origSetToken(t)
          }

          act(() => {
            result.current.logout()
          })

          expect(capturedToken).toBeNull()

          // Restore
          apiClient.setToken = origSetToken
        }
      ),
      { numRuns: 30 }
    )
  })
})
