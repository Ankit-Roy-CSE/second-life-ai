# Implementation Plan: Frontend Polish & Accessibility (P3-C2)

## Overview

This plan converts the frontend-polish-a11y design into incremental coding steps for
`apps/web` (Next.js 14 App Router, TypeScript, Tailwind, TanStack Query). It is a refinement
pass — no backend, contract, or Gateway changes. Work is ordered so the pure async-state
helper and the TanStack Query hooks land first, then the routes are migrated onto them, then
the EmptyState/ARIA/landmark/alt-text fixes, then tests and verification, and finally the docs
updates required by the Definition of Done.

Each task builds on the previous ones and ends wired into a route or shared module so there is
no orphaned code. Sub-tasks marked with `*` are optional test/verification tasks and can be
skipped for a faster MVP; they are still scheduled in the dependency graph.

## Tasks

- [x] 1. Set up the frontend testing framework
  - Add and configure the test toolchain in `apps/web`: a test runner (Vitest or Jest) with
    React Testing Library, `jest-axe` for accessibility assertions, and `fast-check` for
    property-based testing
  - Add `jsdom` environment, a test setup file (RTL matchers + `jest-axe` `toHaveNoViolations`),
    and a `test` script in `apps/web/package.json`
  - Add a path alias / module resolution config so tests can import from `@/lib`, `@/hooks`,
    `@/components`
  - _Requirements: 2.5 (enables PBT), 9–13 (enables jest-axe component tests)_

- [x] 2. Implement the pure async-state selector
  - [x] 2.1 Create `selectAsyncState` helper
    - Create `apps/web/src/lib/async-state.ts` exporting the `AsyncState` union type
      (`"loading" | "error" | "empty" | "success"`) and the pure `selectAsyncState({ isLoading,
      isError, itemCount })` function
    - Implement the fixed precedence: loading → error → empty (`itemCount <= 0`) → success
    - Keep it UI-free and side-effect-free
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 2.2 Write property test for `selectAsyncState`
    - **Property 1: Async views resolve to exactly one correct state**
    - **Validates: Requirements 2.5** (underpins 2.1, 2.2, 2.3, 2.4)
    - Use `fast-check` to generate random `{ isLoading: boolean, isError: boolean, itemCount:
      integer (incl. 0 and negatives) }`; assert the result is a member of the four-element set
      and equals the independently recomputed precedence value; minimum 100 iterations
    - Tag: `// Feature: frontend-polish-a11y, Property 1: Async views resolve to exactly one correct state`

- [x] 3. Implement TanStack Query hooks for the migrated routes
  - [x] 3.1 Create `useMatches` hook
    - Create `apps/web/src/hooks/use-matches.ts` exporting `useMatches(returnId: string)` that
      wraps `useQuery<MatchResponse[], Error>` over `apiClient.getMatches(returnId)`, mirroring
      `useSustainabilityMetrics` (`queryKey: ["matches", returnId]`, `staleTime: 30_000`,
      `retry: 1`)
    - _Requirements: 2.1, 2.4, 5.3, 5.4_

  - [x] 3.2 Create `useMarketplaceListings` hook
    - Create `apps/web/src/hooks/use-marketplace-listings.ts` exporting
      `useMarketplaceListings()` that wraps `useQuery<ListingResponse[], Error>` over
      `apiClient.getMarketplace()` (`queryKey: ["marketplace", "listings"]`, `staleTime:
      30_000`, `retry: 1`)
    - _Requirements: 2.1, 2.4, 5.3, 5.4_

  - [ ]* 3.3 Write unit tests for the query hooks
    - Render each hook with a `QueryClientProvider` and a mocked `apiClient`; assert success,
      empty, and error result shapes and that `refetch` re-invokes the query function
    - _Requirements: 2.1, 2.4, 5.4_

- [x] 4. Add the Marketplace navigation link and avatar label to the NavBar
  - [x] 4.1 Add the Marketplace link
    - In `apps/web/src/components/layout/NavBar.tsx`, insert a `Link href="/marketplace"` with
      visible text `Marketplace` and the exact class string
      `text-sm font-medium text-white hover:text-primary`, positioned in the same `<nav>`
      grouping as Returns / Matches / Dashboard
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 9.1_

  - [x] 4.2 Add an accessible name to the icon-only avatar trigger
    - Add `aria-label="User menu"` to the icon-only `Avatar` trigger in the same file
    - _Requirements: 10.3_

  - [ ]* 4.3 Write component test for NavBar
    - Assert a link with `href="/marketplace"`, accessible name `Marketplace`, the shared class
      string, and placement within `<nav>`; assert the avatar trigger exposes an accessible name;
      run `jest-axe`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 10.3_

- [x] 5. Migrate `/matches` onto `useMatches` with refetch-based retry
  - [x] 5.1 Replace manual fetching and standardize the four states
    - In `apps/web/src/app/matches/page.tsx`, replace the `useEffect`/`useState` fetch with
      `useMatches(returnId)`; render exactly one of Skeleton / EmptyState / ErrorState / content
      (use `selectAsyncState` semantics), keeping `PageHeader` always rendered
    - Change `onRetry={() => window.location.reload()}` to `onRetry={() => refetch()}` and pass
      a human-readable `message` to `ErrorState`
    - Confirm single descending heading order and that decorative icons are `aria-hidden`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 4.1, 4.2, 5.1, 5.2, 5.3, 5.4, 7.1, 7.2, 7.3, 7.4, 9.2, 9.3_

  - [ ]* 5.2 Write component tests for `/matches`
    - Mock the query in loading / empty / error / success and assert the single correct branch;
      click Retry in the error branch and assert the query function is re-invoked and
      `window.location.reload` is never called; run `jest-axe`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.1, 5.4, 9–13_

- [x] 6. Migrate `/marketplace` onto `useMarketplaceListings` with refetch-based retry
  - [x] 6.1 Replace manual fetching, preserve Tabs filtering, wire retry
    - In `apps/web/src/app/marketplace/page.tsx`, replace the `useEffect`/`useState` fetch with
      `useMarketplaceListings()`; preserve the client-side `Tabs` channel filtering (query loads
      once, `ListingGrid` filters in memory)
    - Pass `refetch` down so each `ListingGrid` `ErrorState` uses `onRetry={() => refetch()}`
      instead of `window.location.reload()`, with a human-readable `message`; keep all four
      states; confirm heading order
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 4.1, 5.1, 5.2, 5.3, 5.4, 7.1, 7.2, 7.3, 7.4, 9.2, 9.3_

  - [x] 6.2 Ensure product image alt text and placeholder
    - In the marketplace `ProductCard`, set `alt={product.title}` on the `next/image` and keep
      the `bg-muted` placeholder for the absent/failed image case (`image: undefined`)
    - _Requirements: 13.1, 13.2_

  - [ ]* 6.3 Write component tests for `/marketplace`
    - Mock the query in loading / empty / error / success and assert the single correct branch;
      click Retry and assert re-invocation without `window.location.reload`; assert every image
      has an `alt` and the placeholder renders when image is absent; run `jest-axe`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.1, 5.4, 13.1, 13.2_

- [x] 7. Add EmptyState coverage to the single-entity async views
  - [x] 7.1 Add EmptyState to `/returns/[id]` (ungraded)
    - In `apps/web/src/app/returns/[id]/page.tsx`, replace the ad-hoc inline "not been graded
      yet" `<div>` with the registry `EmptyState` (`icon={ClipboardCheck}`, title "Not graded
      yet", descriptive message) when `returnDetail` exists but `grade` is null
    - Keep the existing Skeleton and `ErrorState` (with its `fetchDetail` retry); confirm heading
      order
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 5.4, 9.2, 9.3_

  - [x] 7.2 Add EmptyState to `/passport/[id]` (no content)
    - In `apps/web/src/app/passport/[id]/page.tsx`, replace `if (!passport) return null` with a
      rendered `EmptyState` (`icon={FileSearch}`, title "No passport found", descriptive message)
      inside a `PageHeader` wrapper so the screen never renders blank
    - Ensure status meaning is conveyed by text (non-color) per 12.3; confirm heading order
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 4.1, 4.4, 5.1, 5.2, 5.3, 5.4, 9.2, 9.3, 12.3_

  - [ ]* 7.3 Write component tests for the EmptyState additions
    - `/returns/[id]` with `grade: null` renders the "Not graded yet" `EmptyState`;
      `/passport/[id]` with no passport renders the "No passport found" `EmptyState` (not null);
      run `jest-axe` on both
    - _Requirements: 4.2, 4.3, 4.4, 9–13_

- [x] 8. Wire form-error ARIA on the mutation views
  - [x] 8.1 Add aria-describedby/aria-invalid on `/login` inputs
    - In `apps/web/src/app/login/page.tsx`, add `aria-invalid` and
      `aria-describedby={errors.email && "email-error"}` (and the password equivalent) on each
      `Input`, pointing at the existing error element `id`s; confirm single descending heading
      hierarchy
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 9.3, 10.1, 10.2, 11.2, 12.1_

  - [x] 8.2 Add aria-describedby/aria-invalid on `/register` inputs
    - In `apps/web/src/app/register/page.tsx`, add the same `aria-invalid`/`aria-describedby`
      wiring on all three inputs (displayName/email/password) pointing at `displayName-error`,
      `email-error`, `password-error`; confirm heading order
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 9.3, 10.1, 10.2, 12.1_

  - [ ]* 8.3 Write component tests for mutation feedback and ARIA
    - For `/login` and `/register`: assert disabled submit + pending label while pending, success
      toast on resolve, human-readable failure toast on reject; assert errored inputs expose
      `aria-invalid` and `aria-describedby` linked to the visible error message; run `jest-axe`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 10.1, 10.2_

- [x] 9. Audit and fix the `/returns` mutation view accessibility
  - In `apps/web/src/app/returns/page.tsx`, verify icon-only FileUpload remove controls have an
    `aria-label`, decorative icons are `aria-hidden`, and the heading order is a single
    descending hierarchy; preserve the existing pending Progress / disabled submit / toast
    behavior (no state-machine change)
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 10.1, 10.3, 10.4, 11.1, 11.2, 9.3_

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Responsive and tokens-only verification
  - [ ]* 11.1 Verify responsive layouts across breakpoints
    - Verify each in-scope route renders usable content with no horizontal body overflow at 360 /
      768 / 1024 px and that responsive adjustments use `sm:`/`md:`/`lg:` token classes (optional
      Playwright viewport snapshots; no property test)
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ]* 11.2 Run tokens-only static checks
    - Run `npm run lint`; grep in-scope files for raw hex (`#`) and arbitrary pixel (`[NNpx]`)
      literals to enforce tokens-only styling; confirm body copy is not dimmed below
      `text-muted-foreground`
    - _Requirements: 8.1, 8.2, 8.3, 12.1, 12.2_

- [x] 12. Update documentation (Definition of Done)
  - [x] 12.1 Update the UI registry
    - Update `docs/ui-registry.md`: add/annotate the NavBar row to note the new Marketplace link
    - _Requirements: 1.1, 1.4_

  - [x] 12.2 Update the progress tracker
    - Update `docs/progress-tracker.md` to mark build task P3-C2 with status + notes
    - _Requirements: 1.1_

- [x] 13. Final checkpoint - Ensure all tests and build pass
  - Run `npm run lint && npm run build`; ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional (tests/verification) and can be skipped for a faster MVP.
- The pure `selectAsyncState` helper and the TanStack Query hooks (tasks 2–3) are implemented
  before the route migrations (tasks 5–6) so the routes build on stable shared modules.
- Per-route accessibility, landmark, heading, and alt-text fixes are folded into each route's
  task to avoid concurrent edits to the same file.
- Property test backs the single universal invariant (Property 1, Requirement 2.5); all other
  acceptance criteria are validated with React Testing Library + `jest-axe` and static/responsive
  checks per the design's Testing Strategy.
- No backend, contract, or Gateway changes; the frontend continues to talk to the Gateway only
  via the existing `api-client.ts` mock layer.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1", "3.1", "3.2", "4.1", "9"] },
    { "id": 2, "tasks": ["2.2", "3.3", "4.2", "5.1", "6.1", "7.1", "7.2", "8.1", "8.2", "12.1", "12.2"] },
    { "id": 3, "tasks": ["4.3", "5.2", "6.2", "7.3", "8.3", "11.1", "11.2"] },
    { "id": 4, "tasks": ["6.3"] }
  ]
}
```
