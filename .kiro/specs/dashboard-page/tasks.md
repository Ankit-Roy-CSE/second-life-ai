# Implementation Plan: User Dashboard

## Overview

Build the `/dashboard` page from scratch, wire up the `useReturns` hook, add new feature components (`ProfileCard`, `ActiveReturnsList`, `ReturnStatusBadge`, `SustainabilitySummary`), and update `NavBar` to use live auth data with a working Logout button. All work is in `apps/web/src`. Mock data is already available — no backend changes needed.

## Tasks

- [ ] 1. Create the `useReturns` TanStack Query hook
  - Create `src/hooks/use-returns.ts` following the exact pattern of `use-sustainability-metrics.ts`
  - Export `RETURNS_QUERY_KEY = ["returns"] as const`
  - Wrap `apiClient.getReturns()` as `queryFn` with `staleTime: 30_000` and `retry: 1`
  - Return the standard `UseQueryResult<ReturnResponse[], Error>` object
  - _Requirements: 2.1, 5.3_

  - [ ]* 1.1 Write unit test for `useReturns` hook configuration
    - Use `renderHook` with a `QueryClientProvider` wrapper and mock `apiClient.getReturns`
    - Assert the hook resolves with mock data and that `RETURNS_QUERY_KEY` is used as the query key
    - _Requirements: 2.1_

- [ ] 2. Create `ReturnStatusBadge` component
  - Create `src/components/features/ReturnStatusBadge.tsx`
  - Implement the full `ReturnStatus → { variant, label }` mapping table from the design
  - Render a `Badge` from `@/components/ui/Badge` with the mapped variant and label
  - _Requirements: 2.7_

  - [ ]* 2.1 Write property test for `ReturnStatusBadge`
    - **Property 3: Every ReturnStatus maps to a visible Badge**
    - Enumerate all 8 `ReturnStatus` values; for each, render `ReturnStatusBadge` and assert a Badge with non-empty label and valid variant is present
    - **Validates: Requirements 2.7**

- [ ] 3. Create `ActiveReturnsList` component
  - Create `src/components/features/ActiveReturnsList.tsx`
  - Accept `returns: ReturnResponse[]` as props
  - When `returns.length === 0`: render `EmptyState` with Package icon, title "No active returns", description, and a `Button` linking to `/returns`
  - When non-empty: render a `Card > CardHeader > CardContent` with one row per return
  - Each row: display `product_id` (truncated to 16 chars), `reason`, `created_at` formatted as locale date string, and `ReturnStatusBadge`
  - Wrap each row in a Next.js `Link` to `/returns/${return.id}`
  - _Requirements: 2.3, 2.4, 2.6_

  - [ ]* 3.1 Write property test for `ActiveReturnsList`
    - **Property 2: ActiveReturnsList is a faithful projection of input data**
    - Generate arrays of `ReturnResponse` with fast-check (`fc.array(fc.record({ id: fc.string(), product_id: fc.string(), ... }), { maxLength: 20 })`)
    - Assert rendered row count equals input array length
    - Assert each row contains an anchor with `href` matching `/returns/${item.id}`
    - **Validates: Requirements 2.3, 2.6**

- [ ] 4. Create `ProfileCard` component
  - Create `src/components/features/ProfileCard.tsx`
  - Accept `user: UserResponse` as props
  - Render `Card > CardHeader > CardContent` layout
  - `CardHeader`: `Avatar` with `AvatarFallback` showing `user.display_name[0].toUpperCase()`
  - `CardContent`: `display_name` as heading, `email` as muted subtext, `green_credits` in a `Badge variant="success"` with a Leaf icon and label "Green Credits"
  - No async data fetching — pure display component
  - _Requirements: 3.1_

  - [ ]* 4.1 Write property test for `ProfileCard`
    - **Property 4: ProfileCard is a pure display of UserResponse fields**
    - Generate random `UserResponse` objects with fast-check; render `ProfileCard` for each
    - Assert `display_name`, `email`, and `green_credits` are all present in the rendered output
    - **Validates: Requirements 3.1**

- [ ] 5. Create `SustainabilitySummary` component
  - Create `src/components/features/SustainabilitySummary.tsx`
  - Accept `totals: SustainabilityMetrics["totals"]` as props
  - Render `Card > CardHeader > CardContent` layout with a 2-column grid
  - Column 1: `StatCard` for `co2_avoided_kg` — label "CO₂ Avoided", unit "kg", tone "success", Leaf icon
  - Column 2: `StatCard` for `green_credits` — label "Green Credits", Award icon
  - Card footer: `Link` to `/sustainability` with text "View full report →"
  - _Requirements: 3.2, 3.5_

  - [ ]* 5.1 Write property test for `SustainabilitySummary`
    - **Property 7: SustainabilitySummary is a pure projection of totals**
    - Generate random `totals` objects with fast-check; render `SustainabilitySummary` for each
    - Assert rendered output contains both `formatNumber(totals.co2_avoided_kg)` and `formatNumber(totals.green_credits)` strings
    - **Validates: Requirements 3.2**

- [ ] 6. Checkpoint — Ensure components render correctly
  - Ensure all tests pass for tasks 1–5, ask the user if questions arise.

- [ ] 7. Update `NavBar` to use live auth data
  - Add `"use client"` directive to `src/components/layout/NavBar.tsx`
  - Import `useAuth` from `@/lib/auth-context` and `useRouter` from `next/navigation`
  - Replace hardcoded `150` credits badge with `user?.green_credits ?? 0`
  - Replace hardcoded `AvatarFallback>U` with `user?.display_name?.[0]?.toUpperCase() ?? "?"`
  - Add a `Button` (variant `"ghost"`, size `"sm"`) with text "Log out" after the Avatar
  - `onClick` handler: call `logout()` then `router.push("/login")`
  - When `user` is null: hide the credits badge, Avatar, and Logout button; show a `Link` to `/login` with text "Sign in"
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 7.1 Write property test for NavBar credits and avatar display
    - **Property 6: NavBar credits and avatar reflect live auth context**
    - Mock `useAuth` to return random `UserResponse` objects generated with fast-check
    - Assert credits badge text equals `String(user.green_credits)` and AvatarFallback text equals `user.display_name[0].toUpperCase()`
    - **Validates: Requirements 4.4, 4.5**

  - [ ]* 7.2 Write unit test for NavBar logout
    - Mock `useAuth` (returns `{ user: mockUser, logout: jest.fn() }`) and `useRouter`
    - Simulate click on "Log out" button
    - Assert `logout()` was called once and `router.push` was called with `"/login"`
    - _Requirements: 4.1, 4.2_

  - [ ]* 7.3 Write property test for logout clearing auth state
    - **Property 5: Logout clears all persisted auth state**
    - Set arbitrary values for `localStorage.slm_token` and `localStorage.slm_user`; call `logout()` from the real `AuthContext`
    - Assert both localStorage keys are null and `apiClient`'s token is null
    - **Validates: Requirements 4.1, 4.2**

- [ ] 8. Create the Dashboard page route
  - Create `src/app/dashboard/page.tsx` with `"use client"` directive
  - Import `useAuth` and `useRouter`; add auth guard: `useEffect(() => { if (!user) router.push("/login") }, [user, router])`; return null when user is falsy
  - Mount both `useReturns()` and `useSustainabilityMetrics(user.id)` in parallel (not sequential)
  - Render `PageHeader` with `title="Dashboard"` and `subtitle={"Welcome back, " + user.display_name}`
  - Layout: `container mx-auto py-8 max-w-screen-xl px-4 md:px-6` root → responsive grid (`grid grid-cols-1 lg:grid-cols-3 gap-6`)
  - Left column (`lg:col-span-1`): `ProfileCard user={user}`
  - Right column (`lg:col-span-2`, `space-y-6`):
    - Returns section: loading → `Skeleton className="h-48 w-full rounded-xl"`; error → `ErrorState`; success → `ActiveReturnsList`
    - Sustainability section: loading → `Skeleton className="h-36 w-full rounded-xl"`; error → `ErrorState`; success → `SustainabilitySummary`
  - _Requirements: 1.1, 1.2, 1.3, 5.1, 5.2, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3_

  - [ ]* 8.1 Write property test for unauthenticated redirect
    - **Property 1: Unauthenticated redirect is total**
    - Mock `useAuth` to return `{ user: null }`; render `DashboardPage`
    - Assert `router.push` was called with `"/login"` and no dashboard content (ProfileCard, ActiveReturnsList, SustainabilitySummary) is present in the tree
    - **Validates: Requirements 1.1, 1.2**

  - [ ]* 8.2 Write integration test for authenticated render
    - Wrap in `QueryClientProvider` + mock `AuthProvider` with a valid user
    - Mock `apiClient.getReturns` and `apiClient.getSustainabilityMetrics` to return mock data
    - Assert `ProfileCard`, `ActiveReturnsList`, and `SustainabilitySummary` all render after queries resolve
    - Assert no redirect is triggered
    - _Requirements: 1.3, 5.5_

- [ ] 9. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, confirm the page renders correctly at `/dashboard` with mock data, ask the user if questions arise.

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": [1, 2, 4, 5] },
    { "wave": 2, "tasks": [3] },
    { "wave": 3, "tasks": [6] },
    { "wave": 4, "tasks": [7] },
    { "wave": 5, "tasks": [8] },
    { "wave": 6, "tasks": [9] }
  ]
}
```

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- The auth guard (`useEffect` + `router.push`) is the established client-side pattern in this app — do not add middleware or server-side redirects
- `NavBar` becoming a Client Component is safe: it already relies on client-side rendering via `AppShell` and does not need to be a Server Component for any reason
- `useReturns` does not accept a `userId` argument because `apiClient.getReturns()` does not yet accept one in the mock layer — scoping by user is a future concern
- All property tests should use `@fast-check/vitest` or the fast-check adapter consistent with the rest of the test suite
