# Requirements Document

## Introduction

This feature delivers the **Sustainability Dashboard** for the Amazon Second Life AI web app
(build task **P3-C1**, owned by Member C, scoped to `apps/web` only). The dashboard is the
closing beat of the demo narrative: after a return flows through grading → decision → passport →
match → purchase, the `/sustainability` page visualizes the cumulative environmental and economic
impact — CO₂ avoided, waste diverted, value recovered, and green credits — backed by the
Sustainability Service metrics surfaced through the Gateway BFF.

The page is built with the established frontend stack (Next.js 14 App Router, TypeScript, Tailwind,
TanStack Query, Zod, Recharts). It reuses the existing design system: the `StatCard` component
(built in P2-C1) for headline metrics and the standard async-state components (`Skeleton`,
`EmptyState`, `ErrorState`, `PageHeader`). It introduces one new feature component, `ChartCard`,
which is currently `📋 Planned` in the component registry and must be registered on completion.

All data is consumed **only through the Gateway** via the typed API client and validated with Zod
schemas; the existing mock layer serves data until the live Gateway aggregate is available. Every
visual value comes from design tokens in `ui-tokens.md` — no raw hex or pixel literals.

Dependencies (both Done): **P2-B2 Sustainability Service** and **P1-C3 primitives batch 2**.

## Glossary

- **Web_App**: The Next.js 14 frontend application located at `apps/web`. The only client that
  talks to the Gateway.
- **Sustainability_Dashboard**: The page component served at the `/sustainability` route
  (`apps/web/src/app/sustainability/page.tsx`).
- **Gateway**: The API Gateway (port 8000), the single backend entry point for the Web_App. The
  Web_App MUST NOT call backend services directly.
- **Sustainability_Service**: The backend service (port 8006, owned by Member B) that computes
  sustainability metrics. Reached only through the Gateway.
- **Metrics_Endpoint**: The Gateway-surfaced endpoint `GET /sustainability/metrics?user_id=`,
  returning a `SustainabilityMetricsResponse` (`totals` object + `breakdown` array).
- **API_Client**: The typed Gateway client at `apps/web/src/lib/api-client.ts`.
- **Mock_Layer**: The static-fixture mock data path in the API_Client, enabled when
  `NEXT_PUBLIC_USE_MOCKS` is not `"false"`, used before the live Gateway aggregate is available.
- **Metrics_Schema**: The Zod schema that parses and validates the Metrics_Endpoint response into a
  typed `SustainabilityMetricsResponse`.
- **Dashboard_Query**: The TanStack Query hook that fetches and caches sustainability metrics via
  the API_Client.
- **StatCard**: The existing registry metric-tile component
  (`apps/web/src/components/features/StatCard.tsx`, built in P2-C1).
- **StatCard_Row**: The row of four StatCard tiles showing the headline metrics.
- **Headline_Metrics**: The four headline values — CO₂ avoided (kg), waste diverted (kg), value
  recovered (currency), and green credits.
- **ChartCard**: The new feature component (`apps/web/src/components/features/ChartCard.tsx`) that
  wraps a Recharts chart in a titled card with its own async states.
- **Chart_Tokens**: The ordered chart color sequence `chart-1 … chart-6` defined in `ui-tokens.md`
  §2.6, consumed as design tokens (never raw hex).
- **Async_View**: Any region of the Sustainability_Dashboard whose content depends on the result of
  the Dashboard_Query.
- **Skeleton**, **EmptyState**, **ErrorState**, **PageHeader**: Existing registry components used
  for async view states.
- **Component_Registry**: The living component registry at `docs/ui-registry.md`.
- **Design_Tokens**: The visual values (color, spacing, type, radius, shadow) defined in
  `docs/ui-tokens.md`; the only allowed source of visual values.

## Requirements

### Requirement 1: Sustainability page route

**User Story:** As a demo customer, I want a dedicated `/sustainability` page, so that I can view
the cumulative impact of returns in one place.

#### Acceptance Criteria

1. THE Web_App SHALL serve the Sustainability_Dashboard at the `/sustainability` route.
2. THE Sustainability_Dashboard SHALL render a PageHeader that states the page title and a subtitle
   describing the dashboard purpose.
3. THE Sustainability_Dashboard SHALL render within the existing application shell layout used by
   other routes.

### Requirement 2: Headline metrics StatCard row

**User Story:** As a demo customer, I want four headline metric tiles, so that I can read the key
sustainability outcomes at a glance.

#### Acceptance Criteria

1. WHEN the Dashboard_Query returns metrics successfully, THE StatCard_Row SHALL render exactly four
   StatCard tiles for CO₂ avoided, waste diverted, value recovered, and green credits.
2. THE StatCard_Row SHALL reuse the existing StatCard component without creating a replacement
   metric-tile component.
3. THE StatCard_Row SHALL display each Headline_Metric value using the `totals` object from the
   Metrics_Endpoint response.
4. THE StatCard_Row SHALL pass the measurement unit for CO₂ avoided as "kg" and for waste diverted
   as "kg" to the corresponding StatCard tiles.
5. THE StatCard_Row SHALL format numeric metric values using the existing `formatNumber` utility.

### Requirement 3: Chart visualizations

**User Story:** As a demo customer, I want one or more charts of sustainability data, so that I can
see how impact breaks down across lifecycle actions.

#### Acceptance Criteria

1. THE Sustainability_Dashboard SHALL render at least one ChartCard built with Recharts.
2. THE ChartCard SHALL render its chart series colors using Chart_Tokens (`chart-1 … chart-6`).
3. WHEN the `breakdown` array from the Metrics_Endpoint response contains one or more entries, THE
   ChartCard SHALL render one chart series datum per breakdown entry.
4. THE ChartCard SHALL render a title and an optional description supplied through its props.
5. WHERE a description prop is provided, THE ChartCard SHALL display the description beneath the
   title.

### Requirement 4: Gateway-only data access via typed client and Zod

**User Story:** As a frontend engineer, I want all dashboard data to come through the typed Gateway
client validated by Zod, so that the Web_App stays within its architectural boundary and fails
safely on malformed data.

#### Acceptance Criteria

1. THE Sustainability_Dashboard SHALL obtain all metrics through the API_Client.
2. THE API_Client SHALL request sustainability metrics from the Gateway Metrics_Endpoint
   `GET /sustainability/metrics?user_id=`.
3. THE Sustainability_Dashboard SHALL NOT call any backend service other than through the Gateway.
4. WHEN a metrics response is received from the Gateway, THE Metrics_Schema SHALL validate the
   response before the Sustainability_Dashboard renders it.
5. IF the metrics response fails Metrics_Schema validation, THEN THE Dashboard_Query SHALL surface
   an error result to the Sustainability_Dashboard.
6. WHILE the environment variable `NEXT_PUBLIC_USE_MOCKS` is not set to `"false"`, THE API_Client
   SHALL return Mock_Layer metrics that conform to the Metrics_Schema.
7. FOR ALL Mock_Layer metrics objects, parsing the object with the Metrics_Schema SHALL produce an
   equivalent typed object (round-trip property).

### Requirement 5: Async view states

**User Story:** As a demo customer, I want clear loading, empty, error, and success states, so that
the dashboard communicates its status instead of showing a blank or broken screen.

#### Acceptance Criteria

1. WHILE the Dashboard_Query is fetching metrics, THE Async_View SHALL display Skeleton placeholders.
2. IF the Dashboard_Query results in an error, THEN THE Async_View SHALL display an ErrorState with a
   retry control.
3. WHEN the retry control is activated, THE Dashboard_Query SHALL re-fetch the sustainability metrics.
4. WHEN the Dashboard_Query succeeds and the `breakdown` array is empty, THE ChartCard SHALL display
   an EmptyState.
5. WHEN the Dashboard_Query succeeds with metrics present, THE Sustainability_Dashboard SHALL display
   the StatCard_Row and the ChartCard in their success states.

### Requirement 6: Component reuse and registry update

**User Story:** As a frontend engineer, I want existing components reused and new ones registered,
so that the design system stays coherent and discoverable.

#### Acceptance Criteria

1. THE Sustainability_Dashboard SHALL reuse the existing StatCard, Skeleton, EmptyState, ErrorState,
   and PageHeader registry components.
2. WHERE no existing registry component fits a need, THE Web_App SHALL add the new ChartCard
   component under `apps/web/src/components/features`.
3. WHEN the ChartCard component is completed, THE Component_Registry SHALL record the ChartCard entry
   with status `✅ Built`, including path, props, and Chart_Tokens used.

### Requirement 7: Design-token compliance

**User Story:** As a frontend engineer, I want every visual value sourced from design tokens, so that
the dashboard matches the Amazon-native visual language and passes UI rules.

#### Acceptance Criteria

1. THE Sustainability_Dashboard SHALL express all colors using Design_Tokens.
2. THE Sustainability_Dashboard SHALL express all spacing, radius, and typography using Design_Tokens.
3. THE ChartCard SHALL source chart series colors only from Chart_Tokens.
4. IF a required chart color token is absent from the token configuration, THEN THE Web_App SHALL add
   the Chart_Tokens definition to the token configuration before use.
