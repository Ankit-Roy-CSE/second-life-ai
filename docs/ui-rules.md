# UI Rules — AZ Second Life AI

>**Concise, enforceable rules for building the UI.** Pair with [ui-tokens.md](ui-tokens.md)
> (the values) and [ui-registry.md](ui-registry.md) (the components). If a rule here conflicts
> with code, the rule wins — fix the code. Owner: Member C, but every agent touching the
> frontend follows this.

---

## 1. The Five Hard Rules

1.**Tokens only.** Never write a raw hex color or pixel value in a component. Use Tailwind
 classes that map to [ui-tokens.md](ui-tokens.md). 🚫 `bg-[#22A06B]`, `style={{padding:7}}`.
2.**Registry first.** Before building any component, search [ui-registry.md](ui-registry.md)
 and `components/ui`. Reuse or extend an existing component; only invent when nothing fits —
 then register it.
3.**Mobile-first & responsive.** Design for 360px first; layer up with `sm: md: lg:`. Every
 page must be usable on a phone.
4.**Every async view has four states.** Loading, empty, error, and success are all designed
 and implemented. No silent blank screens.
5.**Accessible by default.** Semantic HTML, labeled controls, keyboard navigation, visible
 focus, WCAG AA contrast (tokens are pre-checked).

---

## 2. Styling Rules

-**Tailwind only**, composed with `cn()` (from `lib/utils.ts`). No CSS modules / styled-
 components / inline styles for themeable values.
- Use **semantic tokens** (`bg-primary`, `text-muted-foreground`, `border-border`), not scale
 colors, for UI chrome. Scale colors (`green-500`) are for data viz/fills only.
- Variants come from **CVA** in the component, not ad-hoc conditional class soup.
- Spacing uses the 4px scale (`gap-4`, `p-6`). Radius/shadow/z-index use the token scale.
- Dark mode is a stretch goal; if you add classes, use the `dark:` variants against tokens —
 never hardcode dark colors.

## 3. Layout & Structure

-**Page shell:** top nav (`h-16`, `z-sticky`) + centered content (`max-w-screen-xl`,
 `px-4 md:px-6 lg:px-8`). Optional dashboard sidebar `w-64` on `lg+`.
-**Vertical rhythm:** sections separated by `space-y-6` (cards) / `space-y-12` (page blocks).
-**Grids:** dashboard metrics `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4`; content
+ detail `lg:grid-cols-3` (2 + 1). Use CSS grid/flex, not absolute positioning.
- Keep primary actions top-right of their section; destructive actions separated and `danger`.

## 4. Components & Composition

- Build from primitives in `components/ui`; assemble domain UI in `components/features`.
- Prefer composition over duplication. If you copy a block twice, extract a component and
 register it.
- One responsibility per component. Keep client components small; push `"use client"` to leaves.
- Props are explicit and typed; provide sensible defaults; expose `className` passthrough on
 primitives (merged via `cn()`).

## 5. Required States (every data view)

| State | Rule |
|-------|------|
| **Loading** | Skeletons matching final layout (not a bare spinner) via `Skeleton`. Charts/tables show placeholder shapes. |
| **Empty** | Friendly `EmptyState` with icon, one-line explanation, and a primary action. |
| **Error** | Inline `ErrorState` with a short human message + retry. Never show raw error text/stack. Use the error envelope `message`. |
| **Success** | The actual content. Animate in subtly (`duration-base`). |

Disable submit buttons while pending; show optimistic/pending feedback for mutations.

## 6. Feature-Specific Patterns

These map to the five MVP features — match them exactly across the app.

-**AI Grading / Return submission:** a `FileUpload` (drag-drop, image/video, max 8 files,
 shows thumbnails + progress) + a return-reason field. After submit, show a grading
**progress** state, then a `GradePanel` with a `GradeBadge` (A/B/C/D using grade tokens),
 confidence as a labeled progress bar, and a damage-summary list.
-**Lifecycle decision:** show the chosen action with an action-colored badge/icon
 (`action-*` tokens), the rationale text, and the value-recovery estimate as a `StatCard`.
-**Digital Product Passport:** a `PassportTimeline` (vertical, chronological: graded →
 decided → passported → matched/listed → sold) + history sections (ownership, refurb,
 sustainability). Each entry timestamped; IDs in `font-mono`.
-**Hyperlocal Matching:** a list of `MatchCard`s (buyer proximity, match score as a ring/bar,
 estimated savings, distance). Sort by score. Clear "Match found / No match" banner.
-**Sustainability Dashboard:** top row of `StatCard`s (CO₂ avoided, waste diverted, value
 recovered, green credits) + `ChartCard`s (Recharts) using the chart token sequence. Numbers
 use `font-mono tabular-nums`.

## 7. Data Display

-**Numbers/metrics:** `font-mono tabular-nums`; format with shared helpers (thousands
 separators, units). Always show units (kg, %, ₹/$). Round sensibly.
-**Grades:** only via `GradeBadge`; never restyle grade colors inline.
-**Dates:** human-readable relative or `MMM D, YYYY`; store/transport ISO-8601 UTC.
-**Status:** use `Badge` with semantic variants (`success`/`warning`/`danger`/`info`).
-**Truncation:** ellipsize long text with a tooltip/title; never break layout.

## 8. Feedback & Motion

-**Toasts** for async results (success/error of mutations), top-right, `z-toast`,
 auto-dismiss ~4s. One concern per toast.
-**Skeletons** for loading; **spinners** only for inline button-pending states.
- Transitions: `duration-fast` (hover) / `duration-base` (default) / `duration-slow` (modals).
 Respect `prefers-reduced-motion`.

## 9. Icons & Imagery

-**lucide-react** only. Size with `h-4 w-4`/`h-5 w-5`; color with `text-*` tokens.
- Meaningful icons: `aria-label`; decorative: `aria-hidden`. Don't rely on color alone to
 convey meaning (pair icon + text, important for grades/status).
- Product media via `next/image` with presigned URLs; always set `alt`. Show a placeholder on
 load/error.

## 10. Accessibility Checklist (per view)

- [ ] Semantic landmarks (`header`, `nav`, `main`, `footer`).
- [ ] Every input has a `<label>`; errors linked via `aria-describedby`.
- [ ] Keyboard: all interactive elements reachable + operable; visible focus ring (`ring`).
- [ ] Color contrast AA (use tokens; don't dim text below `muted-foreground`).
- [ ] Images have `alt`; icon-only buttons have `aria-label`.
- [ ] Modals/menus trap focus and close on `Esc` (Radix handles this — keep it intact).

## 11. Content & Microcopy

- Tone: clear, encouraging, sustainability-positive. Short labels, sentence case for body,
 Title Case for buttons/headings.
- Buttons are verbs ("Submit return", "View passport", "Find buyers").
- Empty/error copy is human and actionable, never a stack trace or error code.
- Use the product vocabulary: grade, passport, hyperlocal match, green credits, CO₂ avoided.

## 12. Performance & Hygiene

- Code-split heavy/client-only pieces (charts) with dynamic import where it helps.
- Memoize expensive derived data; stable query keys (TanStack Query). Avoid unnecessary
 `"use client"`.
- No `console.log` in committed code. No unused props/classes. Keep components < ~200 lines;
 split when larger.

---

## Do / Don't

| ✅ Do | ❌ Don't |
|------|---------|
| Use tokens via Tailwind classes | Hardcode hex/px or inline styles |
| Reuse registry components | Reinvent a button/card/badge |
| Design loading/empty/error/success | Ship blank or spinner-only screens |
| Mobile-first, then `md:`/`lg:` | Desktop-only layouts |
| Label inputs, keyboard + focus | Click-only, unlabeled controls |
| `GradeBadge` for grades | Inline grade colors |
| Charts use chart tokens | Hardcoded chart colors |
| Update [ui-registry.md](ui-registry.md) after building | Leave the registry stale |
