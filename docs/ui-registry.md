# UI Component Registry — Amazon Second Life AI

>**Living registry of every UI component.** Before building a component, search this file.
> **If it exists, reuse it. If a close match exists, extend it. Only invent when nothing
> fits — then add it here in the same commit.** This prevents three people from building
> three different buttons. Pair with [ui-rules.md](ui-rules.md) and [ui-tokens.md](ui-tokens.md).

---

## How to use this registry

1.**Search before you build.** Ctrl-F the component name / purpose here and check
 `apps/web/components/ui` and `apps/web/components/features`.
2.**Match the pattern exactly.** Same props naming, same variant system (CVA), same tokens.
3.**Status legend:** `✅ Built` · `🚧 In progress` · `📋 Planned` · `🔁 Needs update`.
4.**After building/changing a component, update its row here** (status, props, variants,
 path, owner) — this is part of the Definition of Done.

### Entry template (copy for new components)

```md
### <ComponentName>
-**Status:** 📋 Planned
-**Path:** components/ui/<ComponentName>.tsx
-**Owner:** C
-**Purpose:** <one line>
-**Props:** `prop: type` — <desc>; …
-**Variants:** <variant: values> (via CVA)
-**Tokens used:** <token names from ui-tokens.md>
-**Depends on:** <other registry components / libs>
-**Usage:**
 ```tsx
 <ComponentName prop="..." />
 ```
-**Notes:** <a11y, gotchas>
```

---

## Layer 1 — Primitives (`components/ui/`)

Generic, token-driven, no business logic. Many are generated/adapted from shadcn/ui.

### Button
- **Status:** ✅ Built
- **Path:** components/ui/Button.tsx
- **Owner:** C
- **Purpose:** Primary interactive control.
- **Props:** `variant`, `size`, `asChild?: boolean`, `disabled?`, standard `button` props, `className`.
- **Variants:** `variant`: `primary | secondary | outline | ghost | destructive`; `size`: `sm | md | lg | icon` (via CVA).
- **Tokens used:** `primary`, `secondary`, `danger`, `border`, `ring`, `rounded-lg`, button heights/padding from [ui-tokens.md](ui-tokens.md) §11.
- **Depends on:** CVA, `cn()`.
- **Usage:** `<Button variant="primary" size="md">Submit return</Button>`
- **Notes:** `asChild` for link buttons; focus ring required; disabled = `opacity-50`.

### Card
- **Status:** 📋 Planned
- **Path:** components/ui/Card.tsx
- **Owner:** C
- **Purpose:** Surface container; base for most panels.
- **Props:** `className`; subcomponents `Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter`.
- **Variants:** none (composition).
- **Tokens used:** `card`, `border`, `rounded-xl`, `shadow-sm`, `p-6`.
- **Usage:** `<Card><CardHeader><CardTitle>…</CardTitle></CardHeader><CardContent>…</CardContent></Card>`

### Badge
- **Status:** 📋 Planned
- **Path:** components/ui/Badge.tsx
- **Owner:** C
- **Purpose:** Small status/label pill.
- **Props:** `variant`, `className`, children.
- **Variants:** `default | success | warning | danger | info | muted` (soft token pairs).
- **Tokens used:** semantic soft pairs, `rounded-full`, `text-xs`.
- **Notes:** For grades use `GradeBadge`, not this.

### GradeBadge

File: apps/web/src/components/ui/GradeBadge.tsx
Last updated: 2026-06-13

- **Status:** ✅ Built
- **Owner:** C
- **Purpose:** Display condition grade A/B/C/D with reserved grade colors.

| Property         | Class           |
| ---------------- | --------------- |
| Background       | bg-grade-a...d  |
| Border radius    | rounded-full (icon), rounded-md (label) |
| Text — primary   | text-grade-a...d-foreground |
| Text size        | text-xs (sm), text-sm (md), text-lg (lg) |
| Spacing          | px-3 (label), mr-1 (icon gap) |

**Pattern notes:**
Strictly uses semantic design tokens for grades. Circular (`rounded-full`) for icon only, `rounded-md` with `px-3` when text label is shown. Used by `GradePanel`, `PassportTimeline`, `ProductCard`.

### Input / Textarea
- **Status:** 📋 Planned
- **Path:** components/ui/Input.tsx, components/ui/Textarea.tsx
- **Owner:** C
- **Purpose:** Text entry.
- **Props:** standard input props, `error?: boolean`, `className`.
- **Tokens used:** `input`, `ring`, `danger` (error), `h-10`, `rounded-md`.
- **Notes:** Always used with a `<Label>`; error state links helper text via `aria-describedby`.

### Label
- **Status:** ✅ Built · **Path:** components/ui/Label.tsx · **Owner:** C
- **Purpose:** Accessible form label. **Tokens:** `text-sm font-medium foreground`.

### Select
- **Status:** ✅ Built · **Path:** components/ui/Select.tsx · **Owner:** C
- **Purpose:** Dropdown select (Radix). **Tokens:** `input`, `popover`, `z-dropdown`.
- **Notes:** Keep Radix keyboard/focus behavior.

### Tabs
- **Status:** ✅ Built · **Path:** components/ui/Tabs.tsx · **Owner:** C
- **Purpose:** Sectioned navigation within a view (Radix). **Tokens:** `muted`, `primary`, `border`.

### Dialog / Modal
- **Status:** ✅ Built · **Path:** components/ui/Dialog.tsx · **Owner:** C
- **Purpose:** Modal overlay (Radix). **Tokens:** `popover`, `shadow-lg`, `z-overlay/z-modal`.
- **Notes:** Focus trap + `Esc` close (Radix default — keep).

### Progress
- **Status:** ✅ Built · **Path:** components/ui/Progress.tsx · **Owner:** C
- **Purpose:** Linear progress / confidence bar. **Props:** `value: number` (0–100), `variant?`.
- **Tokens:** `muted` track, `primary`/grade fill, `rounded-full`.

### Skeleton
- **Status:** ✅ Built · **Path:** components/ui/Skeleton.tsx · **Owner:** C
- **Purpose:** Loading placeholder. **Tokens:** `muted`, `rounded-md`, pulse animation.

### Toast / Toaster
- **Status:** ✅ Built · **Path:** components/ui/Toast.tsx · **Owner:** C
- **Purpose:** Transient feedback. **Tokens:** semantic colors, `shadow-lg`, `z-toast`.
- **Notes:** One provider at root; trigger via `useToast()`.

### Tooltip
- **Status:** ✅ Built · **Path:** components/ui/Tooltip.tsx · **Owner:** C
- **Purpose:** Hover/focus hints (Radix). **Tokens:** `popover`, `z-popover`.

### Avatar

File: apps/web/src/components/ui/Avatar.tsx
Last updated: 2026-06-14

- **Status:** ✅ Built
- **Owner:** C
- **Purpose:** User/buyer avatar, displays image or initials.

| Property         | Class           |
| ---------------- | --------------- |
| Background       | bg-muted        |
| Border radius    | rounded-full    |
| Text — primary   | text-muted-foreground (fallback) |
| Spacing          | h-10 w-10 (default base) |

**Pattern notes:**
Follows Radix UI patterns. The fallback explicitly uses `bg-muted text-muted-foreground` to gracefully handle missing avatars or initials while matching the design system's muted color palette.

---

## Layer 2 — Composite / Feature components (`components/features/`)

Use primitives + domain data. Owned by C; data shapes come from backend DTOs.

### StatCard

File: apps/web/src/components/features/StatCard.tsx
Last updated: 2026-06-14

- **Status:** ✅ Built
- **Owner:** C
- **Purpose:** Dashboard metric tile (CO₂ avoided, value recovered, green credits, etc.).

| Property         | Class           |
| ---------------- | --------------- |
| Background       | bg-card         |
| Border           | border-border   |
| Border radius    | rounded-xl (Card default) |
| Text — primary   | text-3xl font-mono tabular-nums font-bold |
| Text — secondary | text-sm font-semibold text-muted-foreground uppercase tracking-wide |
| Spacing          | p-6 (CardContent) |
| Accent usage     | bg-muted text-accent (icon wrapper), text-success/text-danger (deltas) |

**Pattern notes:**
Uses strict typography scales for the metric (`text-3xl font-mono tabular-nums`). The label uses `uppercase tracking-wide` for a dense dashboard aesthetic. Delta text dynamically colors itself with `text-success` or `text-danger`.

### ChartCard

File: apps/web/src/components/features/ChartCard.tsx
Last updated: 2026-06-15

- **Status:** ✅ Built
- **Path:** components/features/ChartCard.tsx
- **Owner:** C
- **Purpose:** Titled card container wrapping a Recharts BarChart with full async states (loading/empty/error/success).
- **Props:** `title: string`, `description?: string`, `breakdown: MetricsBreakdownEntry[]`, `isLoading?: boolean`, `isError?: boolean`, `onRetry?: () => void`
- **Tokens used:** `Card`, chart sequence `chart-1..6` (via `CHART_TOKENS` from `lib/chart-tokens.ts`)
- **Depends on:** Card, recharts, Skeleton, EmptyState, ErrorState, `@/lib/chart-tokens`, `@/lib/schemas/sustainability`. Mark `"use client"`.
- **Notes:** Chart Cell colors sourced exclusively from CHART_TOKENS (no raw hex). Empty breakdown → EmptyState. Must be used inside a TanStack Query context.

### FileUpload

File: apps/web/src/components/features/FileUpload.tsx
Last updated: 2026-06-13

- **Status:** ✅ Built
- **Owner:** C
- **Purpose:** Drag-and-drop image/video upload for returns (thumbnails + progress).

| Property         | Class           |
| ---------------- | --------------- |
| Background       | bg-primary/5 (drag/hover), bg-muted (thumbnails) |
| Border           | border-2 border-dashed border-border (active: border-primary) |
| Border radius    | rounded-lg (dropzone), rounded-md (thumbnails) |
| Text — primary   | text-foreground |
| Text — secondary | text-muted-foreground |
| Spacing          | p-8 (dropzone), gap-4 (grid) |
| Hover state      | hover:border-primary hover:bg-primary/5 |
| Accent usage     | bg-danger (remove button hover) |

**Pattern notes:**
Upload area uses dashed `border-border`, highlighting with `primary` border and subtle `bg-primary/5` background on hover or drag-over. Image thumbnails use simple `rounded-md` borders.

### GradePanel

File: apps/web/src/components/features/GradePanel.tsx
Last updated: 2026-06-13

- **Status:** ✅ Built
- **Owner:** C
- **Purpose:** Show grading result — grade, confidence, damage summary.

| Property         | Class           |
| ---------------- | --------------- |
| Background       | bg-card, bg-secondary (header), bg-muted (inner blocks) |
| Border           | border-border   |
| Border radius    | rounded-xl (Card default), rounded-lg (inner blocks) |
| Text — primary   | text-foreground |
| Text — secondary | text-muted-foreground, text-secondary-foreground |
| Spacing          | p-6 (CardContent), p-4 (headers/blocks), gap-8 |
| Accent usage     | text-primary (shield), text-warning (alerts), text-success (checks) |

**Pattern notes:**
Uses standard Card wrapper. A colored header (`bg-secondary`) is used to denote AI results. Internal sub-sections (grade, damage summary) use `bg-muted` and `border-border/50` to create contained visual groupings.

### DecisionCard

File: apps/web/src/components/features/DecisionCard.tsx
Last updated: 2026-06-14

- **Status:** ✅ Built
- **Owner:** C
- **Purpose:** Lifecycle decision (action + rationale + value estimate).

| Property         | Class           |
| ---------------- | --------------- |
| Background       | bg-card, bg-secondary (header) |
| Border           | border-border   |
| Border radius    | rounded-xl (Card default) |
| Text — primary   | text-xl flex items-center gap-2 (header), text-base leading-relaxed (rationale) |
| Text — secondary | text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-2 (label) |
| Spacing          | p-6 space-y-8 (CardContent) |
| Accent usage     | Dynamic action colors (text-accent, text-info, text-action-donate, text-primary, text-action-hyperlocal) |

**Pattern notes:**
The header uses `bg-secondary` matching the AI response aesthetic (similar to GradePanel). The specific action dynamically maps to a design system color token for the header icon and action text.

### PassportTimeline

File: apps/web/src/components/features/PassportTimeline.tsx
Last updated: 2026-06-14

- **Status:** ✅ Built
- **Owner:** C
- **Purpose:** Vertical chronological history of a product passport.

| Property         | Class           |
| ---------------- | --------------- |
| Background       | bg-card (timeline item) |
| Border           | border-border (item), bg-gradient-to-b from-transparent via-border to-transparent (timeline line) |
| Border radius    | rounded-lg (item), rounded-full (marker) |
| Text — primary   | font-bold text-base (title), text-foreground (details) |
| Text — secondary | text-xs font-mono text-muted-foreground (timestamp), font-semibold capitalize (keys) |
| Spacing          | p-4 (item padding), pl-6 space-y-8 (timeline container) |
| Accent usage     | border-4 border-background bg-primary (marker) |

**Pattern notes:**
Uses standard structural tailwind classes (like `ml-3`) rather than arbitrary pixels. Event timestamps use `font-mono`. The vertical line is created using a subtle border-colored gradient.

### MatchCard

File: apps/web/src/components/features/MatchCard.tsx
Last updated: 2026-06-14

- **Status:** ✅ Built
- **Owner:** C
- **Purpose:** A hyperlocal buyer match (score, savings, distance).

| Property         | Class           |
| ---------------- | --------------- |
| Background       | bg-card         |
| Border           | hover:border-primary/50 |
| Border radius    | rounded-lg (Card default) |
| Text — primary   | text-lg font-semibold (name), text-base font-bold (savings value) |
| Text — secondary | text-sm text-muted-foreground (distance), text-xs text-muted-foreground font-semibold uppercase tracking-wider (label) |
| Spacing          | p-6 (CardContent) |
| Hover state      | hover:border-primary/50 hover:shadow-md transition-all |
| Shadow           | hover:shadow-md |
| Accent usage     | text-primary (score), bg-success/10 text-success (dollar icon), Badge variant="success" |

**Pattern notes:**
Implements interactive card hover states (`hover:border-primary/50 hover:shadow-md`). The savings label strictly matches the dashboard uppercase tracking-wider aesthetic for secondary labels. The score uses a `primary` Progress bar, and successful elements (dollars, badges) leverage the `success` semantic token.

### ProductCard

File: apps/web/src/components/features/ProductCard.tsx
Last updated: 2026-06-14

- **Status:** ✅ Built
- **Owner:** C
- **Purpose:** Marketplace listing tile (image, title, grade, price).

| Property         | Class           |
| ---------------- | --------------- |
| Background       | bg-card, bg-muted (image placeholder) |
| Border           | hover:border-primary/50, border-b border-border (image wrapper) |
| Border radius    | rounded-lg (Card default) |
| Text — primary   | text-lg font-semibold line-clamp-2 (title), text-xl font-bold (price) |
| Text — secondary | text-sm text-muted-foreground font-medium (shipping status) |
| Spacing          | p-5 flex flex-col flex-1 (CardContent), pt-4 border-t (footer) |
| Hover state      | hover:border-primary/50 hover:shadow-md transition-all |
| Shadow           | hover:shadow-md (card), shadow-sm (floating badges) |
| Accent usage     | Badge variant="info" (local pickup) |

**Pattern notes:**
Employs standard Next.js `<Image />` component with `fill` and `object-cover` within a `relative aspect-square` wrapper for perfectly proportioned, performant images. Floating badges (`GradeBadge`, `Badge`) utilize `shadow-sm` for separation from the underlying image. Consistent interactive hover states match `MatchCard`.

### EmptyState
- **Status:** ✅ Built
- **Path:** components/features/EmptyState.tsx
- **Owner:** C
- **Purpose:** Standard empty view (icon + message + action). Required by ui-rules.md §5.
- **Props:** `icon?`, `title`, `description?`, `action?`.

### ErrorState
- **Status:** ✅ Built
- **Path:** components/features/ErrorState.tsx
- **Owner:** C
- **Purpose:** Standard inline error with retry. Required by ui-rules §5.
- **Props:** `title?`, `message`, `onRetry?`.

### PageHeader
- **Status:** ✅ Built
- **Path:** components/features/PageHeader.tsx
- **Owner:** C
- **Purpose:** Page title + subtitle + optional actions slot.
- **Props:** `title`, `subtitle?`, `actions?`.

---

## Layer 3 — Layout (`components/layout/`)

### AppShell
- **Status:** ✅ Built · **Path:** components/layout/AppShell.tsx · **Owner:** C
- **Purpose:** Top nav + content container; wraps all routes. **Tokens:** `header-height`, `container-max`, `z-sticky`.

### NavBar

File: apps/web/src/components/layout/NavBar.tsx
Last updated: 2026-06-15

- **Status:** ✅ Built · **Path:** components/layout/NavBar.tsx · **Owner:** C
- **Purpose:** Brand, primary nav links, user menu, green-credit balance. **Depends on:** Button, Avatar.

| Property         | Class           |
| ---------------- | --------------- |
| Background       | `bg-secondary` |
| Text — primary   | `text-secondary-foreground` |
| Text — links     | `text-white hover:text-primary` |
| Shadow           | `shadow-sm` |
| Spacing          | `h-header` (60px), `px-4 md:px-6 lg:px-8` |
| Positioning      | `sticky top-0 z-[1100]` |

**Pattern notes:**
The NavBar anchors the top of the interface. It strongly uses the `secondary` brand color (Navy) to ground the design. Links hover to `primary` (Gold) to provide high-contrast interactive states.

Navigation links (in order): **Returns · Matches · Marketplace · Dashboard**. The Avatar trigger carries `aria-label="User menu"` for screen-reader accessibility.

### Sidebar (optional)
- **Status:** 📋 Planned · **Path:** components/layout/Sidebar.tsx · **Owner:** C
- **Purpose:** Dashboard nav on `lg+`. **Tokens:** `sidebar-width`, `muted`.

---

## Utilities (not components, but registry-tracked)

| Util | Path | Purpose |
|------|------|---------|
| `cn()` | lib/utils.ts | Merge Tailwind classes (clsx + tailwind-merge) |
| `formatNumber()` | lib/utils.ts | Thousands/units formatting for metrics |
| `formatDate()` | lib/utils.ts | ISO → human date |
| `useToast()` | components/ui/Toast.tsx | Trigger toasts |

---

## Registry Status Summary

| Layer | Built | In progress | Planned |
|-------|-------|-------------|---------|
| Primitives | 13 | 0 | 1 |
| Composite/feature | 11 | 0 | 0 |
| Layout | 1 | 0 | 2 |

> Update the counts and individual statuses as components are built. The first agent to build
> a primitive should flip its status to 🚧 then ✅ and fill in the real prop signature.