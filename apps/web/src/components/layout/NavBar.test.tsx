/**
 * Tests for NavBar component — Task 7 subtasks 7.1 and 7.2
 *
 * 7.1 Property 6: NavBar credits and avatar reflect live auth context
 *     Validates: Requirements 4.4, 4.5
 *
 * 7.2 Unit test: NavBar logout calls logout() and router.push("/login")
 *     Requirements: 4.1, 4.2
 */

import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import * as fc from "fast-check"
import { NavBar } from "./NavBar"
import type { UserResponse } from "../../../types/api"
import * as authContext from "@/lib/auth-context"

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockLogout = vi.fn()
const mockPush = vi.fn()

vi.mock("@/lib/auth-context", () => ({
  useAuth: vi.fn(),
}))

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}))

// Helper to set what useAuth returns
function setAuthUser(user: UserResponse | null) {
  vi.mocked(authContext.useAuth).mockReturnValue({
    user,
    logout: mockLogout,
    token: user ? "mock-token" : null,
    login: vi.fn(),
    isAuthenticated: !!user,
  })
}

// Fast-check arbitrary for UserResponse
const fcUserResponse = (): fc.Arbitrary<UserResponse> =>
  fc.record({
    id: fc.uuid(),
    email: fc.emailAddress(),
    // Ensure display_name has at least 1 non-whitespace char so toUpperCase() is visible
    display_name: fc.string({ minLength: 1, maxLength: 50 }).filter((s) => s.trim().length > 0),
    interests: fc.array(fc.string()),
    green_credits: fc.integer({ min: 0, max: 100_000 }),
    created_at: fc.constantFrom("2024-01-01T00:00:00Z"),
  })

// ---------------------------------------------------------------------------
// 7.1 Property test: NavBar credits and avatar reflect live auth context
// Validates: Requirements 4.4, 4.5
// ---------------------------------------------------------------------------

describe("Property 6: NavBar credits and avatar reflect live auth context", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("credits badge shows user.green_credits and AvatarFallback shows first letter of display_name", () => {
    fc.assert(
      fc.property(fcUserResponse(), (user) => {
        setAuthUser(user)

        const { unmount } = render(<NavBar />)

        // Credits badge should show the user's green_credits value
        const creditsBadge = screen.getByText(String(user.green_credits))
        expect(creditsBadge).toBeInTheDocument()

        // AvatarFallback should show the first char of display_name uppercased
        const expectedFallback = user.display_name[0].toUpperCase()
        const fallback = screen.getByText(expectedFallback)
        expect(fallback).toBeInTheDocument()

        unmount()
      }),
      { numRuns: 50 }
    )
  })
})

// ---------------------------------------------------------------------------
// 7.2 Unit test: NavBar logout calls logout() and router.push("/login")
// Requirements: 4.1, 4.2
// ---------------------------------------------------------------------------

describe("NavBar logout behaviour", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("calls logout() and router.push('/login') when Log out button is clicked", async () => {
    const user: UserResponse = {
      id: "user-1",
      email: "test@example.com",
      display_name: "Alice",
      interests: [],
      green_credits: 42,
      created_at: "2024-01-01T00:00:00Z",
    }

    setAuthUser(user)

    render(<NavBar />)

    const logoutButton = screen.getByRole("button", { name: /log out/i })
    expect(logoutButton).toBeInTheDocument()

    await userEvent.click(logoutButton)

    expect(mockLogout).toHaveBeenCalledTimes(1)
    expect(mockPush).toHaveBeenCalledTimes(1)
    expect(mockPush).toHaveBeenCalledWith("/login")
  })

  it("shows Sign in link and hides credits/avatar/logout when user is null", () => {
    setAuthUser(null)

    render(<NavBar />)

    // "Sign in" link should be visible
    const signInLink = screen.getByRole("link", { name: /sign in/i })
    expect(signInLink).toBeInTheDocument()
    expect(signInLink).toHaveAttribute("href", "/login")

    // Credits badge, avatar fallback and logout button should NOT be present
    expect(screen.queryByRole("button", { name: /log out/i })).not.toBeInTheDocument()
    expect(screen.queryByText("Credits")).not.toBeInTheDocument()
  })
})
