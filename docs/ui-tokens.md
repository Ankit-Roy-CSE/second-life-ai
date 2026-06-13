# UI Design Tokens — AZ Second Life AI

>**Single source of truth for all visual values.** Every color, font size, space, radius,
> and shadow used in the codebase comes from here. Tokens are implemented in
> `apps/web/tailwind.config.ts` and `apps/web/app/globals.css` (CSS variables). **Never
> hardcode a hex value or pixel measurement in a component** — reference a token instead.
> See enforcement rules in [ui-rules.md](ui-rules.md).

---

## 0. How tokens are consumed

1.**CSS variables** (HSL channels) are declared on `:root` in `globals.css`.
2.**Tailwind** maps semantic names to those variables in `tailwind.config.ts`.
3.**Components** use Tailwind classes (`bg-primary`, `text-muted-foreground`, `rounded-lg`)
 or shadcn/ui semantic tokens — never raw values.

```
globals.css ──declares──▶ --primary: 152 60% 36%
tailwind.config.ts ──maps──▶ colors.primary = hsl(var(--primary))
Component ──uses──▶ className="bg-primary text-primary-foreground"
```

> Color tokens are stored as **HSL channel triplets** (`H S% L%`) without the `hsl()`
> wrapper so Tailwind can compose opacity (`bg-primary/80`). Copy values exactly.

---

## 1. Brand & Theme Concept

A **circular-commerce / sustainability** identity: trustworthy green as the primary,
a deep slate for structure, and a warm amber accent for value/credits. The grade scale
(A→D) has its own dedicated, color-blind-considerate palette because grades are the most
important data the product displays.

| Concept | Token family | Meaning |
|---------|--------------|---------|
| Primary (green) | `primary` | Brand, primary actions, "sustainable/good" |
| Secondary (slate) | `secondary` | Structure, secondary actions |
| Accent (amber) | `accent` | Value recovered, green credits, highlights |
| Semantic | `success/warning/danger/info` | Status & feedback |
| Grade | `grade-a/b/c/d` | Condition grades — never reuse for anything else |
| Neutrals | `background/foreground/muted/border` | Surfaces & text |

---

## 2. Color Tokens

### 2.1 Core semantic palette (light theme — default)

| Token | HSL (`H S% L%`) | Hex (ref only) | Usage |
|-------|----------------|----------------|-------|
| `--background` | `0 0% 100%` | `#FFFFFF` | App background |
| `--foreground` | `222 47% 11%` | `#0F172A` | Primary text |
| `--card` | `0 0% 100%` | `#FFFFFF` | Card surface |
| `--card-foreground` | `222 47% 11%` | `#0F172A` | Text on cards |
| `--popover` | `0 0% 100%` | `#FFFFFF` | Popover surface |
| `--popover-foreground` | `222 47% 11%` | `#0F172A` | Text on popovers |
| `--primary` | `152 60% 36%` | `#22A06B` | Brand green, primary buttons |
| `--primary-foreground` | `0 0% 100%` | `#FFFFFF` | Text/icon on primary |
| `--secondary` | `215 28% 17%` | `#1E293B` | Slate, secondary buttons |
| `--secondary-foreground` | `0 0% 100%` | `#FFFFFF` | Text on secondary |
| `--accent` | `38 92% 50%` | `#F59E0B` | Amber, value/credits highlight |
| `--accent-foreground` | `222 47% 11%` | `#0F172A` | Text on accent |
| `--muted` | `210 40% 96%` | `#F1F5F9` | Muted surface / hover |
| `--muted-foreground` | `215 16% 47%` | `#64748B` | Secondary text, captions |
| `--border` | `214 32% 91%` | `#E2E8F0` | Borders, dividers |
| `--input` | `214 32% 91%` | `#E2E8F0` | Input borders |
| `--ring` | `152 60% 36%` | `#22A06B` | Focus ring (matches primary) |

### 2.2 Primary green scale (for charts, fills, emphasis)

| Token | Hex | Token | Hex |
|-------|-----|-------|-----|
| `green-50` | `#ECFDF5` | `green-500` | `#22A06B` (= primary) |
| `green-100` | `#D1FAE5` | `green-600` | `#1B8055` |
| `green-200` | `#A7F3D0` | `green-700` | `#15643F` |
| `green-300` | `#6EE7B7` | `green-800` | `#0F4A2F` |
| `green-400` | `#34D399` | `green-900` | `#0A3320` |

### 2.3 Semantic status colors

| Token | HSL | Hex | Usage |
|-------|-----|-----|-------|
| `--success` | `152 60% 36%` | `#22A06B` | Success (reuses brand green) |
| `--success-foreground` | `0 0% 100%` | `#FFFFFF` | Text on success |
| `--warning` | `38 92% 50%` | `#F59E0B` | Warnings, "review" |
| `--warning-foreground` | `222 47% 11%` | `#0F172A` | Text on warning |
| `--danger` | `0 72% 51%` | `#DC2626` | Destructive, recycle/discard |
| `--danger-foreground` | `0 0% 100%` | `#FFFFFF` | Text on danger |
| `--info` | `217 91% 60%` | `#3B82F6` | Informational |
| `--info-foreground` | `0 0% 100%` | `#FFFFFF` | Text on info |

> In shadcn/ui, `--danger` maps to the `destructive` token name. Keep both names pointing
> at the same value.

### 2.4 Grade palette (condition A/B/C/D) — reserved

These are the most important domain colors. Use **only** for grade badges, grade-keyed
charts, and grade emphasis. Each pairs a fill with an accessible foreground.

| Grade | Token | Hex | Foreground | Meaning |
|-------|-------|-----|-----------|---------|
| A | `grade-a` | `#15803D` | `#FFFFFF` | Like-new / excellent |
| B | `grade-b` | `#65A30D` | `#FFFFFF` | Good, minor wear |
| C | `grade-c` | `#F59E0B` | `#0F172A` | Fair, visible wear |
| D | `grade-d` | `#DC2626` | `#FFFFFF` | Poor / recycle candidate |

Soft (badge background) variants:

| Grade | Soft bg | Soft text |
|-------|---------|-----------|
| A | `#DCFCE7` | `#14532D` |
| B | `#ECFCCB` | `#3F6212` |
| C | `#FEF3C7` | `#92400E` |
| D | `#FEE2E2` | `#991B1B` |

### 2.5 Lifecycle action colors

For decision badges/icons (Resell / Refurbish / Donate / Recycle / Hyperlocal):

| Action | Token | Hex |
|--------|-------|-----|
| Resell | `action-resell` | `#22A06B` (green-500) |
| Refurbish | `action-refurbish` | `#3B82F6` (info) |
| Donate | `action-donate` | `#8B5CF6` (`#violet`) |
| Recycle | `action-recycle` | `#F59E0B` (accent) |
| Hyperlocal | `action-hyperlocal` | `#0EA5E9` (`#sky`) |

### 2.6 Chart sequence (sustainability dashboard)

Ordered palette for Recharts series; first two are brand-aligned:

`["#22A06B", "#3B82F6", "#F59E0B", "#8B5CF6", "#EC4899", "#14B8A6"]`
→ tokens `chart-1` … `chart-6`.

### 2.7 Dark theme (optional, define if time allows)

Override the same `--*` variables under `.dark`. Minimum set: invert
`background`/`foreground`, lift surfaces to slate-900/800, keep `primary` green but raise
lightness one step. Treated as **stretch** — light theme is the demo default.

---

## 3. Typography

### 3.1 Font families

| Token | Stack | Usage |
|-------|-------|-------|
| `font-sans` | `Inter, ui-sans-serif, system-ui, sans-serif` | All UI text (default) |
| `font-mono` | `"JetBrains Mono", ui-monospace, monospace` | IDs, code, metric readouts |

Load **Inter** via `next/font/google` in `app/layout.tsx` (no CDN `<link>`).

### 3.2 Type scale (use Tailwind classes)

| Token | Size / line-height | Weight | Usage |
|-------|--------------------|--------|-------|
| `text-xs` | 12px / 16px | 400–500 | Captions, badges, table meta |
| `text-sm` | 14px / 20px | 400–500 | Secondary text, labels |
| `text-base` | 16px / 24px | 400 | Body (default) |
| `text-lg` | 18px / 28px | 500 | Lead text, card titles |
| `text-xl` | 20px / 28px | 600 | Section headings |
| `text-2xl` | 24px / 32px | 600 | Page subtitles |
| `text-3xl` | 30px / 36px | 700 | Page titles |
| `text-4xl` | 36px / 40px | 700 | Hero / dashboard headline |
| `text-5xl` | 48px / 1 | 800 | Marketing hero only |

### 3.3 Font weights

`font-normal` 400 · `font-medium` 500 · `font-semibold` 600 · `font-bold` 700 · `font-extrabold` 800

### 3.4 Rules

- Headings use `font-semibold`/`font-bold`; body uses `font-normal`.
- Numeric metrics (CO₂, value, credits) use `font-mono` + `tabular-nums` for alignment.
- Max body line length ~70ch (`max-w-prose`).

---

## 4. Spacing

Base unit = **4px**. Use Tailwind spacing scale only.

| Token | px | Common use |
|-------|----|-----------|
| `0.5` | 2 | hairline gaps |
| `1` | 4 | icon/text gap |
| `2` | 8 | tight padding, badge padding |
| `3` | 12 | compact control padding |
| `4` | 16 | default element padding/gap |
| `6` | 24 | card padding, section gap |
| `8` | 32 | block spacing |
| `12` | 48 | major section spacing |
| `16` | 64 | page section spacing |
| `24` | 96 | hero spacing |

Layout constants:

| Token | Value | Usage |
|-------|-------|-------|
| `--container-max` | `1280px` | Max content width (`max-w-screen-xl`) |
| `--page-padding-x` | `16px` mobile / `24px` md / `32px` lg | Horizontal page gutters |
| `--header-height` | `64px` | Top nav |
| `--sidebar-width` | `256px` | Dashboard sidebar (if used) |
| `--content-gap` | `24px` | Default gap between cards/sections |

---

## 5. Radius

| Token | Value | Usage |
|-------|-------|-------|
| `rounded-sm` | 4px | Badges, tags |
| `rounded-md` | 6px | Inputs, small buttons |
| `rounded-lg` | 8px | Buttons, cards (default) |
| `rounded-xl` | 12px | Large cards, modals |
| `rounded-2xl` | 16px | Hero / feature panels |
| `rounded-full` | 9999px | Avatars, pills, icon buttons |

`--radius` base = **8px** (`0.5rem`); shadcn derives `lg/md/sm` from it.

---

## 6. Shadows / Elevation

| Token | Value | Usage |
|-------|-------|-------|
| `shadow-xs` | `0 1px 2px rgba(15,23,42,0.04)` | Subtle separation |
| `shadow-sm` | `0 1px 3px rgba(15,23,42,0.08)` | Cards (resting) |
| `shadow-md` | `0 4px 12px rgba(15,23,42,0.08)` | Cards (hover), dropdowns |
| `shadow-lg` | `0 10px 24px rgba(15,23,42,0.10)` | Modals, popovers |
| `shadow-focus` | `0 0 0 3px rgba(34,160,107,0.35)` | Focus ring glow (primary) |

---

## 7. Borders

| Token | Value |
|-------|-------|
| Default border width | `1px` |
| Emphasis border width | `2px` (focus, selected) |
| Default border color | `--border` (`#E2E8F0`) |
| Divider | `1px solid var(--border)` |

---

## 8. Breakpoints (Tailwind defaults — mobile-first)

| Token | Min width | Target |
|-------|-----------|--------|
| `sm` | 640px | Large phone / small tablet |
| `md` | 768px | Tablet |
| `lg` | 1024px | Laptop |
| `xl` | 1280px | Desktop (container max) |
| `2xl` | 1536px | Large desktop |

Design **mobile-first**; layer complexity upward with `md:`/`lg:` prefixes.

---

## 9. Z-index scale

| Token | Value | Usage |
|-------|-------|-------|
| `z-base` | 0 | Default flow |
| `z-dropdown` | 1000 | Dropdowns, selects |
| `z-sticky` | 1100 | Sticky headers |
| `z-overlay` | 1200 | Modal backdrop |
| `z-modal` | 1300 | Modal/dialog |
| `z-popover` | 1400 | Popovers, tooltips |
| `z-toast` | 1500 | Toasts (top-most) |

---

## 10. Motion

| Token | Value | Usage |
|-------|-------|-------|
| `duration-fast` | 120ms | Hover, small state changes |
| `duration-base` | 200ms | Default transitions |
| `duration-slow` | 320ms | Modals, page transitions |
| Easing | `cubic-bezier(0.4, 0, 0.2, 1)` | Standard ease |

Respect `prefers-reduced-motion`: disable non-essential animation.

---

## 11. Component Token Defaults

Canonical per-component values so primitives stay consistent. The component **registry**
([ui-registry.md](ui-registry.md)) must reference these.

### Button

| Variant | Background | Text | Border | Height (md) | Padding-x | Radius |
|---------|-----------|------|--------|-------------|-----------|--------|
| primary | `primary` | `primary-foreground` | none | 40px (`h-10`) | 16px (`px-4`) | `rounded-lg` |
| secondary | `secondary` | `secondary-foreground` | none | 40px | 16px | `rounded-lg` |
| outline | `transparent` | `foreground` | `border` | 40px | 16px | `rounded-lg` |
| ghost | `transparent` | `foreground` | none | 40px | 16px | `rounded-lg` |
| destructive | `danger` | `danger-foreground` | none | 40px | 16px | `rounded-lg` |

Sizes: `sm` h-9 / px-3 / text-sm · `md` h-10 / px-4 / text-sm · `lg` h-11 / px-6 / text-base.
Focus: `shadow-focus` + `ring`. Disabled: `opacity-50 cursor-not-allowed`.

### Card

`bg-card text-card-foreground rounded-xl border border-border shadow-sm` · padding `p-6` ·
header/body/footer gap `space-y-4`.

### Badge

`rounded-full px-2.5 py-0.5 text-xs font-medium` · variants map to semantic/grade soft pairs.

### Input

`h-10 rounded-md border border-input bg-background px-3 text-sm` · focus `ring` +
`border-ring` · error `border-danger` + helper text `text-danger text-xs`.

### StatCard (dashboard metric)

`Card` + label `text-sm text-muted-foreground` + value `text-3xl font-bold font-mono
tabular-nums` + delta `text-xs` (success/danger) + optional icon in `accent`.

---

## 12. Reference `tailwind.config.ts` mapping (implement exactly)

```ts
// apps/web/tailwind.config.ts (excerpt — the binding contract)
export default {
 theme: {
 extend: {
 colors: {
 background: "hsl(var(--background))",
 foreground: "hsl(var(--foreground))",
 primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
 secondary: { DEFAULT: "hsl(var(--secondary))", foreground: "hsl(var(--secondary-foreground))" },
 accent: { DEFAULT: "hsl(var(--accent))", foreground: "hsl(var(--accent-foreground))" },
 muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
 success: { DEFAULT: "hsl(var(--success))", foreground: "hsl(var(--success-foreground))" },
 warning: { DEFAULT: "hsl(var(--warning))", foreground: "hsl(var(--warning-foreground))" },
 danger: { DEFAULT: "hsl(var(--danger))", foreground: "hsl(var(--danger-foreground))" },
 info: { DEFAULT: "hsl(var(--info))", foreground: "hsl(var(--info-foreground))" },
 border: "hsl(var(--border))",
 input: "hsl(var(--input))",
 ring: "hsl(var(--ring))",
 grade: { a: "#15803D", b: "#65A30D", c: "#F59E0B", d: "#DC2626" },
 },
 borderRadius: { lg: "var(--radius)", md: "calc(var(--radius) - 2px)", sm: "calc(var(--radius) - 4px)" },
 fontFamily: { sans: ["var(--font-inter)", "system-ui", "sans-serif"], mono: ["var(--font-mono)", "monospace"] },
 boxShadow: {
 xs: "0 1px 2px rgba(15,23,42,0.04)",
 sm: "0 1px 3px rgba(15,23,42,0.08)",
 md: "0 4px 12px rgba(15,23,42,0.08)",
 lg: "0 10px 24px rgba(15,23,42,0.10)",
 },
 },
 },
} satisfies Config;
```

```css
/* apps/web/app/globals.css (excerpt) */
:root {
--background: 0 0% 100%;
--foreground: 222 47% 11%;
--card: 0 0% 100%;
--card-foreground: 222 47% 11%;
--primary: 152 60% 36%;
--primary-foreground: 0 0% 100%;
--secondary: 215 28% 17%;
--secondary-foreground: 0 0% 100%;
--accent: 38 92% 50%;
--accent-foreground: 222 47% 11%;
--muted: 210 40% 96%;
--muted-foreground: 215 16% 47%;
--success: 152 60% 36%; --success-foreground: 0 0% 100%;
--warning: 38 92% 50%; --warning-foreground: 222 47% 11%;
--danger: 0 72% 51%; --danger-foreground: 0 0% 100%;
--info: 217 91% 60%; --info-foreground: 0 0% 100%;
--border: 214 32% 91%;
--input: 214 32% 91%;
--ring: 152 60% 36%;
--radius: 0.5rem;
}
```

> When you add or change a token: update **this file**, `globals.css`, and
> `tailwind.config.ts` together, then note any new component value in
> [ui-registry.md](ui-registry.md).