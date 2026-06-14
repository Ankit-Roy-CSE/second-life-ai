# Requirements Document

## Introduction

This feature (build task **P3-C2**, Member C / Frontend) is a polish and refinement pass
across the existing `apps/web` Next.js application for **Amazon Second Life AI**. The goal is
to bring every route to a consistent, production-quality bar before the demo: every
asynchronous view presents all four required states (loading, empty, error, success) per
[ui-rules.md](../../../docs/ui-rules.md) §5; every layout is verified responsive across mobile,
tablet, and desktop breakpoints using design tokens only; and every view satisfies the
accessibility checklist in ui-rules.md §10.

The task also includes one explicit, concrete gap: the primary navigation in
`apps/web/src/components/layout/NavBar.tsx` is missing a **Marketplace** link even though the
`/marketplace` route exists. That link must be added following the exact pattern of the
existing links.

This is primarily a refinement task over existing code — it reuses the already-built registry
components (`Skeleton`, `EmptyState`, `ErrorState`, `PageHeader`) and introduces no new backend
calls. The frontend talks to the Gateway only. The `/sustainability` route (P3-C1, already
done) is the reference implementation for correct async-state handling and is treated as the
pattern other routes are brought up to.

## Scope

The routes in scope for the audit are: `/login`, `/register`, `/returns`, `/returns/[id]`,
`/passport/[id]`, `/matches`, `/marketplace`, `/sustainability`. Member C owns `apps/web` only;
no backend, contract, or Gateway changes are part of this task.

## Glossary

- **Web_App**: The Next.js 14 App Router application in `apps/web` owned by Member C.
- **NavBar**: The primary navigation layout component at
  `apps/web/src/components/layout/NavBar.tsx`.
- **Route**: A page under `apps/web/src/app` corresponding to one of the in-scope paths.
- **Async_Data_View**: Any Route region whose content depends on data fetched from the Gateway
  (currently `/returns/[id]`, `/passport/[id]`, `/matches`, `/marketplace`, `/sustainability`).
- **Mutation_View**: Any Route whose primary interaction submits data to the Gateway rather
  than fetching for display (currently `/login`, `/register`, `/returns`).
- **Loading_State**: The placeholder UI rendered while data is being fetched, built with the
  registry `Skeleton` component and shaped to match the final layout.
- **Empty_State**: The UI rendered when a successful fetch returns zero items, built with the
  registry `EmptyState` component.
- **Error_State**: The UI rendered when a fetch fails, built with the registry `ErrorState`
  component, including a retry control.
- **Success_State**: The UI rendered when a fetch returns one or more items (the actual
  content).
- **Retry_Control**: The action exposed by `Error_State` (`onRetry`) that re-attempts the
  failed data fetch.
- **Design_Token**: A Tailwind class that maps to a value defined in
  [ui-tokens.md](../../../docs/ui-tokens.md) (e.g. `bg-primary`, `text-muted-foreground`,
  `gap-4`).
- **Breakpoint**: A Tailwind responsive width tier — mobile (base, 360px), tablet (`md:`,
  768px), desktop (`lg:`, 1024px and up).
- **Registry_Component**: A component already catalogued in
  [ui-registry.md](../../../docs/ui-registry.md).
- **Semantic_Landmark**: An HTML sectioning element conveying page structure (`header`, `nav`,
  `main`, `footer`).

## Requirements

### Requirement 1: Marketplace navigation link

**User Story:** As a user, I want a Marketplace link in the primary navigation, so that I can
reach the `/marketplace` route directly like every other primary destination.

#### Acceptance Criteria

1. THE NavBar SHALL render a navigation link whose destination is the `/marketplace` route.
2. THE NavBar SHALL render the Marketplace link with the class string
   `text-sm font-medium text-white hover:text-primary`, matching the existing Returns,
   Matches, and Dashboard links.
3. THE NavBar SHALL position the Marketplace link within the same navigation grouping as the
   existing Returns, Matches, and Dashboard links.
4. THE NavBar SHALL display the visible text `Marketplace` for the Marketplace link.

### Requirement 2: Async data views present four states

**User Story:** As a user, I want every data-driven screen to clearly show whether content is
loading, empty, errored, or ready, so that I never face a silent blank screen.

#### Acceptance Criteria

1. WHILE an Async_Data_View is fetching data, THE Web_App SHALL render the Loading_State for
   that Async_Data_View.
2. WHEN an Async_Data_View fetch completes successfully with zero items, THE Web_App SHALL
   render the Empty_State for that Async_Data_View.
3. WHEN an Async_Data_View fetch completes successfully with one or more items, THE Web_App
   SHALL render the Success_State for that Async_Data_View.
4. IF an Async_Data_View fetch fails, THEN THE Web_App SHALL render the Error_State for that
   Async_Data_View.
5. THE Web_App SHALL render exactly one of Loading_State, Empty_State, Error_State, or
   Success_State for each Async_Data_View at any given time.

### Requirement 3: Loading state uses skeletons

**User Story:** As a user, I want loading screens to preview the shape of the incoming content,
so that the interface feels responsive and intentional.

#### Acceptance Criteria

1. WHILE an Async_Data_View is in the Loading_State, THE Web_App SHALL render the loading
   placeholder using the registry `Skeleton` Registry_Component.
2. THE Web_App SHALL shape each Loading_State to approximate the layout of the corresponding
   Success_State rather than rendering a bare spinner.

### Requirement 4: Empty state uses the EmptyState component

**User Story:** As a user, I want empty screens to explain that there is nothing to show, so
that I understand the screen loaded correctly and there is simply no data.

#### Acceptance Criteria

1. WHEN an Async_Data_View renders the Empty_State, THE Web_App SHALL render it using the
   registry `EmptyState` Registry_Component.
2. THE Web_App SHALL provide a `title` and a descriptive message to each rendered `EmptyState`.
3. WHERE the `/returns/[id]` Route returns a return that has not yet been graded, THE Web_App
   SHALL render an `EmptyState` explaining that the return is not yet graded.
4. WHERE the `/passport/[id]` Route resolves no passport content, THE Web_App SHALL render an
   `EmptyState` rather than rendering nothing.

### Requirement 5: Error state uses the ErrorState component with retry

**User Story:** As a user, I want failed screens to show a clear message and a way to try
again, so that a transient failure does not force me to leave the page.

#### Acceptance Criteria

1. WHEN an Async_Data_View renders the Error_State, THE Web_App SHALL render it using the
   registry `ErrorState` Registry_Component.
2. THE Web_App SHALL pass a human-readable message to each rendered `ErrorState` instead of a
   raw error object or stack trace.
3. WHEN an Async_Data_View renders the Error_State, THE Web_App SHALL provide a Retry_Control
   via the `onRetry` prop.
4. WHEN the user activates the Retry_Control, THE Web_App SHALL re-attempt the failed data
   fetch for that Async_Data_View without triggering a full browser page reload.

### Requirement 6: Mutation views give pending and result feedback

**User Story:** As a user submitting a form, I want clear feedback while my submission is
processing and after it completes, so that I know my action was received.

#### Acceptance Criteria

1. WHILE a Mutation_View submission is in progress, THE Web_App SHALL disable the submit
   control for that Mutation_View.
2. WHILE a Mutation_View submission is in progress, THE Web_App SHALL display a pending
   indication to the user.
3. WHEN a Mutation_View submission succeeds, THE Web_App SHALL present a success confirmation
   to the user.
4. IF a Mutation_View submission fails, THEN THE Web_App SHALL present a human-readable failure
   message to the user instead of a raw error object or stack trace.

### Requirement 7: Responsive layouts across breakpoints

**User Story:** As a user on a phone, tablet, or desktop, I want every page to be usable at my
screen size, so that the app works wherever I open it.

#### Acceptance Criteria

1. THE Web_App SHALL render every in-scope Route as usable content at the mobile Breakpoint
   (360px width) without horizontal overflow of the page body.
2. THE Web_App SHALL render every in-scope Route as usable content at the tablet Breakpoint
   (768px width).
3. THE Web_App SHALL render every in-scope Route as usable content at the desktop Breakpoint
   (1024px width and above).
4. THE Web_App SHALL express responsive layout adjustments using Tailwind responsive
   Design_Token classes (`sm:`, `md:`, `lg:`).

### Requirement 8: Tokens-only styling

**User Story:** As a frontend maintainer, I want all polished components to use design tokens,
so that the app stays visually consistent and theme-able.

#### Acceptance Criteria

1. THE Web_App SHALL express colors in in-scope Routes and components using Design_Token
   classes rather than raw hex color literals.
2. THE Web_App SHALL express spacing and sizing in in-scope Routes and components using
   Design_Token classes rather than raw pixel literals.
3. WHERE a styling value is needed that no Design_Token provides, THE Web_App SHALL use an
   existing Registry_Component that supplies that value rather than introducing a raw literal.

### Requirement 9: Semantic structure and landmarks

**User Story:** As a user relying on assistive technology, I want pages built from meaningful
HTML structure, so that I can navigate by landmark and understand page regions.

#### Acceptance Criteria

1. THE Web_App SHALL render primary navigation inside a `nav` Semantic_Landmark.
2. THE Web_App SHALL render each Route's primary content inside a `main` Semantic_Landmark.
3. THE Web_App SHALL render heading text for each Route using heading elements in a descending
   order without skipping levels.

### Requirement 10: Labeled controls and ARIA

**User Story:** As a user relying on assistive technology, I want every control to be
announced with a meaningful name, so that I can operate forms and buttons confidently.

#### Acceptance Criteria

1. THE Web_App SHALL associate every form input in the in-scope Routes with a `Label`
   Registry_Component via matching `htmlFor` and `id` attributes.
2. WHEN a form input has a validation error, THE Web_App SHALL link the error message to that
   input via `aria-describedby`.
3. THE Web_App SHALL provide an `aria-label` for every icon-only interactive control in the
   in-scope Routes.
4. THE Web_App SHALL mark decorative icons with `aria-hidden` so that they are not announced
   by assistive technology.

### Requirement 11: Keyboard navigation and visible focus

**User Story:** As a keyboard-only user, I want to reach and operate every interactive element
and see where focus is, so that I can use the app without a mouse.

#### Acceptance Criteria

1. THE Web_App SHALL make every interactive element in the in-scope Routes reachable and
   operable using the keyboard.
2. WHEN an interactive element receives keyboard focus, THE Web_App SHALL display a visible
   focus indicator using the `ring` Design_Token.
3. WHILE a modal or menu is open, THE Web_App SHALL retain the Radix focus-trap and
   `Esc`-to-close behavior of the underlying Registry_Component.

### Requirement 12: Color contrast and non-color cues

**User Story:** As a user with low vision or color blindness, I want text to be legible and
meaning to never depend on color alone, so that I can read and understand every screen.

#### Acceptance Criteria

1. THE Web_App SHALL render text in the in-scope Routes using foreground Design_Token classes
   that meet WCAG AA contrast against their background.
2. THE Web_App SHALL NOT dim body text below the `muted-foreground` Design_Token.
3. WHERE meaning is conveyed by color (such as grade or status), THE Web_App SHALL pair the
   color with text or an icon so that meaning does not depend on color alone.

### Requirement 13: Image alt text

**User Story:** As a user relying on assistive technology, I want images described, so that I
understand non-text content.

#### Acceptance Criteria

1. THE Web_App SHALL provide an `alt` attribute for every image rendered in the in-scope
   Routes.
2. IF a product image fails to load or is absent, THEN THE Web_App SHALL render a placeholder
   in its place.
