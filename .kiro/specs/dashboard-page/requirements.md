# Requirements Document

## Introduction

The User Dashboard feature provides the authenticated landing page at `/dashboard`. It surfaces three data panels — a user profile card, an active-returns list, and a sustainability summary — alongside a fully functional Logout control. The feature also updates the NavBar to read live auth context data instead of hardcoded values. All mock data is already wired through `apiClient` with `NEXT_PUBLIC_USE_MOCKS=true`, so the full page renders without a running backend.

## Glossary

- **Dashboard_Page**: The Next.js page component at `app/dashboard/page.tsx` that renders the authenticated user overview
- **Auth_Context**: The React context provided by `AuthProvider` in `lib/auth-context.tsx`, exposing `{ user, logout, isAuthenticated }`
- **Profile_Card**: The new `ProfileCard` component displaying the authenticated user's identity and green-credits balance
- **Active_Returns_List**: The new `ActiveReturnsList` component rendering the user's return items with status badges
- **Sustainability_Summary**: The new `SustainabilitySummary` component showing CO₂ avoided and green credits earned
- **Return_Status_Badge**: The new `ReturnStatusBadge` component mapping `ReturnStatus` enum values to styled `Badge` chips
- **NavBar**: The existing `components/layout/NavBar.tsx` shell header, to be updated with live auth data and a logout control
- **useReturns**: The new TanStack Query hook in `hooks/use-returns.ts` wrapping `apiClient.getReturns()`
- **ReturnStatus**: The enum from `types/enums.ts` — SUBMITTED, GRADED, DECIDED, PASSPORTED, MATCHING, LISTED, SOLD, FAILED
- **UserResponse**: The type from `types/api.ts` — `{ id, email, display_name, interests, green_credits, created_at }`
- **SustainabilityMetrics**: The Zod-validated type from `lib/schemas/sustainability` returned by `useSustainabilityMetrics`

---

## Requirements

### Requirement 1: Authentication Guard

**User Story:** As a visitor, I want unauthenticated access to `/dashboard` to be blocked, so that only logged-in users can see their personal data.

#### Acceptance Criteria

1. WHEN a user navigates to `/dashboard` and `Auth_Context.user` is null, THE Dashboard_Page SHALL call `router.push("/login")` and render no dashboard content
2. WHILE `Auth_Context.user` is null after mount, THE Dashboard_Page SHALL return null and not render any child components
3. WHEN `Auth_Context.user` becomes non-null on mount (session restored from localStorage), THE Dashboard_Page SHALL render the full dashboard without requiring a page reload

---

### Requirement 2: Active Returns List

**User Story:** As an authenticated user, I want to see my active returns with their current status, so that I can track what is happening with each item.

#### Acceptance Criteria

1. WHEN the Dashboard_Page mounts with a valid user, THE useReturns hook SHALL fetch `ReturnResponse[]` from `apiClient.getReturns()` with `staleTime` of 30,000 ms and `retry` of 1
2. WHILE the returns query is loading, THE Dashboard_Page SHALL render a skeleton placeholder in the returns section
3. WHEN the returns query resolves successfully, THE Active_Returns_List SHALL render one row per `ReturnResponse` containing `product_id`, `reason`, formatted `created_at`, and a Return_Status_Badge
4. WHEN the returns array is empty, THE Active_Returns_List SHALL render an `EmptyState` component with a link to `/returns`
5. IF the returns query fails, THEN THE Dashboard_Page SHALL render an `ErrorState` in the returns section with a retry button that calls `refetch()` on the useReturns query
6. WHEN a return row is rendered, THE Active_Returns_List SHALL wrap it in a link to `/returns/{id}` so the user can navigate to the detail page
7. THE Return_Status_Badge SHALL map every `ReturnStatus` value to a `Badge` with a non-empty label and appropriate variant: SUBMITTED/GRADED → `info`; DECIDED/PASSPORTED/MATCHING → `warning`; LISTED/SOLD → `success`; FAILED → `danger`

---

### Requirement 3: User Profile and Sustainability Display

**User Story:** As an authenticated user, I want to see my profile information and sustainability impact on the dashboard, so that I can understand my contributions at a glance.

#### Acceptance Criteria

1. WHEN the Dashboard_Page renders with a valid user, THE Profile_Card SHALL display `user.display_name`, `user.email`, and `user.green_credits` sourced directly from `Auth_Context` without making an additional API call
2. WHEN the sustainability metrics query resolves successfully, THE Sustainability_Summary SHALL render a `StatCard` for `co2_avoided_kg` with unit "kg" and tone "success", and a `StatCard` for `green_credits` with an Award icon
3. WHILE the sustainability metrics query is loading, THE Dashboard_Page SHALL render a skeleton placeholder in the sustainability section
4. IF the sustainability metrics query fails, THEN THE Dashboard_Page SHALL render an `ErrorState` in the sustainability section with a retry button that calls `refetch()` on the metrics query independently of the returns section
5. THE Sustainability_Summary SHALL include a link to `/sustainability` labeled "View full report"

---

### Requirement 4: Logout and NavBar Updates

**User Story:** As an authenticated user, I want a working Logout button in the NavBar that clears my session and redirects me to the login page, so that I can securely end my session from any page.

#### Acceptance Criteria

1. WHEN a user clicks the Logout control in the NavBar, THE NavBar SHALL call `Auth_Context.logout()` which removes `slm_token` and `slm_user` from `localStorage` and sets the API client token to null
2. WHEN `Auth_Context.logout()` completes, THE NavBar SHALL call `router.push("/login")` to redirect the user
3. WHEN `Auth_Context.user` is null, THE NavBar SHALL hide the credits badge and avatar and render a "Sign in" link to `/login` instead
4. WHEN `Auth_Context.user` is non-null, THE NavBar SHALL display `user.green_credits` in the credits `Badge` (replacing the hardcoded value of 150)
5. WHEN `Auth_Context.user` is non-null, THE NavBar SHALL display the first letter of `user.display_name` as the `AvatarFallback` (replacing the hardcoded "U")
6. THE NavBar SHALL be converted to a Client Component (add `"use client"` directive) to enable `useAuth()` and `useRouter()` hooks

---

### Requirement 5: Page Structure and Async State Patterns

**User Story:** As a developer, I want the dashboard to follow the same page structure and async-state conventions used across the app, so that the codebase stays consistent and maintainable.

#### Acceptance Criteria

1. THE Dashboard_Page SHALL use the container class pattern `container mx-auto py-8 max-w-screen-xl px-4 md:px-6` for its root element
2. THE Dashboard_Page SHALL render a `PageHeader` component with `title="Dashboard"` and a subtitle greeting the user by `display_name`
3. THE useReturns hook SHALL follow the same structure as `useSustainabilityMetrics`: export a named `RETURNS_QUERY_KEY` constant, accept no required arguments, wrap `apiClient.getReturns()` as `queryFn`, and return the standard TanStack Query result object
4. WHEN any async section is loading, THE Dashboard_Page SHALL render a `Skeleton` component — no section may show a blank space or spinner not from the design system
5. THE Dashboard_Page SHALL initiate both the returns query and the sustainability metrics query in parallel on mount, not sequentially
6. WHERE the sustainability metrics query is called from Dashboard_Page, THE useSustainabilityMetrics hook SHALL be invoked with `user.id` as the `userId` argument so that future API integration can scope results to the current user

---

### Requirement 6: New Dashboard Route

**User Story:** As a user, I want `/dashboard` to be a real route in the Next.js app, so that the redirect from login and register actually lands somewhere useful.

#### Acceptance Criteria

1. THE Dashboard_Page SHALL exist at `apps/web/src/app/dashboard/page.tsx` with the `"use client"` directive
2. WHEN the `/dashboard` route is loaded, THE Dashboard_Page SHALL be accessible via the Next.js app router with no 404 error
3. THE Dashboard_Page layout SHALL use a responsive grid that places `Profile_Card` in a sidebar column on large screens (`lg:col-span-1`) and the returns/sustainability sections in the main area (`lg:col-span-2`)
