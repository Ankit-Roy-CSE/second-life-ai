# UI Component Registry — AZ Second Life AI

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
- **Status:** 📋 Planned
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
- **Status:** 📋 Planned
- **Path:** components/ui/GradeBadge.tsx
- **Owner:** C
- **Purpose:** Display condition grade A/B/C/D with reserved grade colors.
- **Props:** `grade: "A" | "B" | "C" | "D"`, `size?: "sm" | "md" | "lg"`, `showLabel?: boolean`.
- **Variants:** keyed by grade (grade soft bg + text).
- **Tokens used:** `grade-a..d` + soft variants from [ui-tokens.md](ui-tokens.md) §2.4.
- **Notes:** Pair color with the letter (don't rely on color alone). Used by GradePanel, PassportTimeline, ProductCard.

### Input / Textarea
- **Status:** 📋 Planned
- **Path:** components/ui/Input.tsx, components/ui/Textarea.tsx
- **Owner:** C
- **Purpose:** Text entry.
- **Props:** standard input props, `error?: boolean`, `className`.
- **Tokens used:** `input`, `ring`, `danger` (error), `h-10`, `rounded-md`.
- **Notes:** Always used with a `<Label>`; error state links helper text via `aria-describedby`.

### Label
- **Status:** 📋 Planned · **Path:** components/ui/Label.tsx · **Owner:** C
- **Purpose:** Accessible form label. **Tokens:** `text-sm font-medium foreground`.

### Select
- **Status:** 📋 Planned · **Path:** components/ui/Select.tsx · **Owner:** C
- **Purpose:** Dropdown select (Radix). **Tokens:** `input`, `popover`, `z-dropdown`.
- **Notes:** Keep Radix keyboard/focus behavior.

### Tabs
- **Status:** 📋 Planned · **Path:** components/ui/Tabs.tsx · **Owner:** C
- **Purpose:** Sectioned navigation within a view (Radix). **Tokens:** `muted`, `primary`, `border`.

### Dialog / Modal
- **Status:** 📋 Planned · **Path:** components/ui/Dialog.tsx · **Owner:** C
- **Purpose:** Modal overlay (Radix). **Tokens:** `popover`, `shadow-lg`, `z-overlay/z-modal`.
- **Notes:** Focus trap + `Esc` close (Radix default — keep).

### Progress
- **Status:** 📋 Planned · **Path:** components/ui/Progress.tsx · **Owner:** C
- **Purpose:** Linear progress / confidence bar. **Props:** `value: number` (0–100), `variant?`.
- **Tokens:** `muted` track, `primary`/grade fill, `rounded-full`.

### Skeleton
- **Status:** 📋 Planned · **Path:** components/ui/Skeleton.tsx · **Owner:** C
- **Purpose:** Loading placeholder. **Tokens:** `muted`, `rounded-md`, pulse animation.

### Toast / Toaster
- **Status:** 📋 Planned · **Path:** components/ui/Toast.tsx · **Owner:** C
- **Purpose:** Transient feedback. **Tokens:** semantic colors, `shadow-lg`, `z-toast`.
- **Notes:** One provider at root; trigger via `useToast()`.

### Tooltip
- **Status:** 📋 Planned · **Path:** components/ui/Tooltip.tsx · **Owner:** C
- **Purpose:** Hover/focus hints (Radix). **Tokens:** `popover`, `z-popover`.

### Avatar
- **Status:** 📋 Planned · **Path:** components/ui/Avatar.tsx · **Owner:** C
- **Purpose:** User/buyer avatar. **Tokens:** `muted`, `rounded-full`.

---

## Layer 2 — Composite / Feature components (`components/features/`)

Use primitives + domain data. Owned by C; data shapes come from backend DTOs.

### StatCard
- **Status:** 📋 Planned
- **Path:** components/features/StatCard.tsx
- **Owner:** C
- **Purpose:** Dashboard metric tile (CO₂ avoided, value recovered, green credits, etc.).
- **Props:** `label: string`, `value: string | number`, `unit?: string`, `delta?: number`, `icon?: LucideIcon`, `tone?: "default" | "success" | "warning"`.
- **Tokens used:** `Card`, `muted-foreground`, `text-3xl font-mono tabular-nums`, `accent` icon, `success/danger` delta.
- **Depends on:** Card, lucide-react.
- **Usage:** `<StatCard label="CO₂ avoided" value={128.4} unit="kg" delta={12} icon={Leaf} />`

### ChartCard
- **Status:** 📋 Planned
- **Path:** components/features/ChartCard.tsx
- **Owner:** C
- **Purpose:** Titled container wrapping a Recharts chart with required states.
- **Props:** `title`, `description?`, `children` (chart), `isLoading?`, `isError?`.
- **Tokens used:** `Card`, chart sequence `chart-1..6`.
- **Depends on:** Card, recharts, Skeleton, ErrorState. Mark `"use client"`.

### FileUpload
- **Status:** 📋 Planned
- **Path:** components/features/FileUpload.tsx
- **Owner:** C
- **Purpose:** Drag-and-drop image/video upload for returns (thumbnails + progress).
- **Props:** `accept`, `maxFiles=8`, `onChange(files)`, `value`, `disabled?`.
- **Tokens used:** `border` (dashed), `muted`, `primary` (active), `rounded-xl`.
- **Notes:** Validate type/size; show per-file progress; keyboard accessible.

### GradePanel
- **Status:** 📋 Planned
- **Path:** components/features/GradePanel.tsx
- **Owner:** C
- **Purpose:** Show grading result — grade, confidence, damage summary.
- **Props:** `grade`, `confidence` (0–1), `damageSummary: string`, `defects: string[]`.
- **Depends on:** GradeBadge, Progress, Card.

### DecisionCard
- **Status:** 📋 Planned
- **Path:** components/features/DecisionCard.tsx
- **Owner:** C
- **Purpose:** Lifecycle decision (action + rationale + value estimate).
- **Props:** `action: LifecycleAction`, `rationale: string`, `valueRecovery: number`, `sustainabilityScore: number`.
- **Tokens used:** `action-*` colors, Card, StatCard.

### PassportTimeline
- **Status:** 📋 Planned
- **Path:** components/features/PassportTimeline.tsx
- **Owner:** C
- **Purpose:** Vertical chronological history of a product passport.
- **Props:** `events: { type, label, timestamp, meta? }[]`.
- **Tokens used:** `border`, `primary` markers, `muted-foreground`, `font-mono` ids.

### MatchCard
- **Status:** 📋 Planned
- **Path:** components/features/MatchCard.tsx
- **Owner:** C
- **Purpose:** A hyperlocal buyer match (score, savings, distance).
- **Props:** `buyer`, `score: number`, `estimatedSavings: number`, `distanceKm: number`.
- **Depends on:** Card, Avatar, Progress/score ring, Badge.

### ProductCard
- **Status:** 📋 Planned
- **Path:** components/features/ProductCard.tsx
- **Owner:** C
- **Purpose:** Marketplace listing tile (image, title, grade, price).
- **Props:** `product`, `grade`, `price`, `channel`.
- **Depends on:** Card, GradeBadge, next/image.

### EmptyState
- **Status:** 📋 Planned
- **Path:** components/features/EmptyState.tsx
- **Owner:** C
- **Purpose:** Standard empty view (icon + message + action). Required by [ui-rules.md](ui-rules.md) §5.
- **Props:** `icon?`, `title`, `description?`, `action?`.

### ErrorState
- **Status:** 📋 Planned
- **Path:** components/features/ErrorState.tsx
- **Owner:** C
- **Purpose:** Standard inline error with retry. Required by ui-rules §5.
- **Props:** `title?`, `message`, `onRetry?`.

### PageHeader
- **Status:** 📋 Planned
- **Path:** components/features/PageHeader.tsx
- **Owner:** C
- **Purpose:** Page title + subtitle + optional actions slot.
- **Props:** `title`, `subtitle?`, `actions?`.

---

## Layer 3 — Layout (`components/layout/`)

### AppShell
- **Status:** 📋 Planned · **Path:** components/layout/AppShell.tsx · **Owner:** C
- **Purpose:** Top nav + content container; wraps all routes. **Tokens:** `header-height`, `container-max`, `z-sticky`.

### NavBar
- **Status:** 📋 Planned · **Path:** components/layout/NavBar.tsx · **Owner:** C
- **Purpose:** Brand, primary nav links, user menu, green-credit balance. **Depends on:** Button, Avatar.

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
| Primitives | 0 | 0 | 14 |
| Composite/feature | 0 | 0 | 11 |
| Layout | 0 | 0 | 3 |

> Update the counts and individual statuses as components are built. The first agent to build
> a primitive should flip its status to 🚧 then ✅ and fill in the real prop signature.