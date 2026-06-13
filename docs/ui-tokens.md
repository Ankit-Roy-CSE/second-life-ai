# UI Design Tokens — Amazon Second Life AI

>**Single source of truth for all visual values.** Every color, font size, space, radius,
> and shadow used in the codebase comes from here. Tokens are implemented in
> `apps/web/tailwind.config.ts` and `apps/web/app/globals.css` (CSS variables). **Never
> hardcode a hex value or pixel measurement in a component** — reference a token instead.
> See enforcement rules in [ui-rules.md](ui-rules.md).

---

## 0. How tokens are consumed

1.**CSS variables** (HSL channels) are declared on `:root` in `globals.css`.
2.**Tailwind** maps semantic names to those variables in `tailwind.config.ts`.
3.**Components** use Tailwind classes (`bg-primary`, `text-muted-foreground`, `rounded-md`)
 or shadcn/ui semantic tokens — never raw values.

```
globals.css ──declares──▶ --primary: 36 100% 50%
tailwind.config.ts ──maps──▶ colors.primary = hsl(var(--primary))
Component ──uses──▶ className="bg-primary text-primary-foreground"
```

> Color tokens are stored as **HSL channel triplets** (`H S% L%`) without the `hsl()`
> wrapper so Tailwind can compose opacity (`bg-primary/80`). Copy values exactly.

---

## 1. Brand & Theme Concept

An **Amazon-native** identity: the familiar dark navy header, warm cream page backgrounds,
Amazon gold/yellow for primary actions, and the trusted green for sustainability signals.
The product should feel like a natural extension of the Amazon ecosystem — familiar to
anyone who has used Amazon's returns, seller central, or order pages.

| Concept | Token family | Meaning |
|---------|--------------|---------|
| Primary (Amazon gold) | `primary` | CTAs, primary buttons, key actions |
| Secondary (navy) | `secondary` | Header, structural elements, secondary actions |
| Accent (green) | `accent` | Sustainability, eco-signals, positive outcomes |
| Semantic | `success/warning/danger/info` | Status & feedback |
| Grade | `grade-a/b/c/d` | Condition grades — never reuse for anything else |
| Neutrals | `background/foreground/muted/border` | Surfaces & text |

---

## 2. Color Tokens

### 2.1 Core semantic palette (light theme — default)

| Token | HSL (`H S% L%`) | Hex (ref only) | Usage |
|-------|----------------|----------------|-------|
| `--background` | `30 60% 96%` | `#FEF7ED` | App background (warm cream, Amazon-style) |
| `--foreground` | `210 29% 20%` | `#232F3E` | Primary text (Amazon navy) |
| `--card` | `0 0% 100%` | `#FFFFFF` | Card surface |
| `--card-foreground` | `210 29% 20%` | `#232F3E` | Text on cards |
| `--popover` | `0 0% 100%` | `#FFFFFF` | Popover surface |
| `--popover-foreground` | `210 29% 20%` | `#232F3E` | Text on popovers |
| `--primary` | `36 100% 50%` | `#FF9900` | Amazon gold — primary CTAs |
| `--primary-foreground` | `210 29% 20%` | `#232F3E` | Dark text on gold buttons |
| `--secondary` | `210 29% 20%` | `#232F3E` | Amazon navy — header, secondary actions |
| `--secondary-foreground` | `0 0% 100%` | `#FFFFFF` | White text on navy |
| `--accent` | `152 60% 36%` | `#22A06B` | Sustainability green — eco signals |
| `--accent-foreground` | `0 0% 100%` | `#FFFFFF` | Text on accent green |
| `--muted` | `210 20% 95%` | `#F0F2F4` | Muted surface / hover |
| `--muted-foreground` | `210 11% 45%` | `#656D78` | Secondary text, captions |
| `--border` | `210 18% 84%` | `#CDD4DB` | Borders, dividers (slightly stronger than before) |
| `--input` | `210 18% 84%` | `#CDD4DB` | Input borders |
| `--ring` | `36 100% 50%` | `#FF9900` | Focus ring (matches primary) |

### 2.2 Amazon extended palette (for charts, fills, emphasis)

| Token | Hex | Token | Hex |
|-------|-----|-------|-----|
| `gold-50` | `#FFF8E1` | `gold-500` | `#FF9900` (= primary) |
| `gold-100` | `#FFECB3` | `gold-600` | `#E68A00` |
| `gold-200` | `#FFD54F` | `gold-700` | `#CC7A00` |
| `gold-300` | `#FFC107` | `gold-800` | `#996600` |
| `gold-400` | `#FFAB00` | `gold-900` | `#664400` |

| Token | Hex | Token | Hex |
|-------|-----|-------|-----|
| `navy-50` | `#F0F2F5` | `navy-500` | `#37475A` |
| `navy-100` | `#D5DBE1` | `navy-600` | `#2E3A4A` |
| `navy-200` | `#AAB7C4` | `navy-700` | `#232F3E` (= secondary) |
| `navy-300` | `#7F93A6` | `navy-800` | `#1A2430` |
| `navy-400` | `#546978` | `navy-900` | `#111921` |

### 2.3 Semantic status colors

| Token | HSL | Hex | Usage |
|-------|-----|-----|-------|
| `--success` | `152 60% 36%` | `#22A06B` | Success (reuses sustainability green) |
| `--success-foreground` | `0 0% 100%` | `#FFFFFF` | Text on success |
| `--warning` | `36 100% 50%` | `#FF9900` | Warnings (Amazon gold) |
| `--warning-foreground` | `210 29% 20%` | `#232F3E` | Text on warning |
| `--danger` | `0 72% 51%` | `#DC2626` | Destructive, errors |
| `--danger-foreground` | `0 0% 100%` | `#FFFFFF` | Text on danger |
| `--info` | `207 90% 54%` | `#1E88E5` | Informational (Amazon link blue) |
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
| C | `grade-c` | `#F59E0B` | `#232F3E` | Fair, visible wear |
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
| Resell | `action-resell` | `#22A06B` (accent green) |
| Refurbish | `action-refurbish` | `#1E88E5` (info blue) |
| Donate | `action-donate` | `#8B5CF6` (violet) |
| Recycle | `action-recycle` | `#FF9900` (primary gold) |
| Hyperlocal | `action-hyperlocal` | `#0EA5E9` (sky) |

### 2.6 Chart sequence (sustainability dashboard)

Ordered palette for Recharts series; first two are brand-aligned:

`["#22A06B", "#1E88E5", "#FF9900", "#8B5CF6", "#EC4899", "#14B8A6"]`
→ tokens `chart-1` … `chart-6`.

### 2.7 Dark theme (optional, define if time allows)

Override the same `--*` variables under `.dark`. Amazon-style dark: use `#111921` as
background, `#1A2430` as card, keep gold and green as-is. Treated as **stretch** — light
theme is the demo default.

---

## 3. Typography

### 3.1 Font families

| Token | Stack | Usage |
|-------|-------|-------|
| `font-sans` | `"Amazon Ember", Inter, ui-sans-serif, system-ui, sans-serif` | All UI text (default). Falls back to Inter since Ember isn't publicly distributed. |
| `font-mono` | `"JetBrains Mono", ui-monospace, monospace` | IDs, code, metric readouts |

Load **Inter** via `next/font/google` in `app/layout.tsx` (no CDN `<link>`). It's the
closest publicly available match to Amazon Ember in x-height and proportion.

### 3.2 Type scale (use Tailwind classes)

| Token | Size / line-height | Weight | Usage |
|-------|--------------------|--------|-------|
| `text-xs` | 12px / 16px | 400–500 | Captions, badges, table meta |
| `text-sm` | 14px / 20px | 400–500 | Secondary text, labels, form helpers |
| `text-base` | 16px / 24px | 400 | Body (default) |
| `text-lg` | 18px / 28px | 500 | Lead text, card titles |
| `text-xl` | 20px / 28px | 600 | Section headings |
| `text-2xl` | 24px / 32px | 700 | Page subtitles |
| `text-3xl` | 30px / 36px | 700 | Page titles |
| `text-4xl` | 36px / 40px | 700 | Hero / dashboard headline |

### 3.3 Font weights

`font-normal` 400 · `font-medium` 500 · `font-semibold` 600 · `font-bold` 700

> Amazon's UI uses **bold labels** with regular body text. Headings `font-bold`; form labels
> `font-semibold`; body `font-normal`.

### 3.4 Rules

- Headings use `font-bold`; form labels use `font-semibold`; body uses `font-normal`.
- Numeric metrics (CO₂, value, credits) use `font-mono` + `tabular-nums` for alignment.
- Max body line length ~70ch (`max-w-prose`).
- Star ratings use `text-primary` (gold) for filled stars.

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
| `5` | 20 | form field internal padding |
| `6` | 24 | card padding, section gap |
| `8` | 32 | block spacing |
| `12` | 48 | major section spacing |
| `16` | 64 | page section spacing |

Layout constants:

| Token | Value | Usage |
|-------|-------|-------|
| `--container-max` | `1280px` | Max content width (`max-w-screen-xl`) |
| `--page-padding-x` | `16px` mobile / `24px` md / `32px` lg | Horizontal page gutters |
| `--header-height` | `60px` | Top nav (Amazon standard) |
| `--sidebar-width` | `256px` | Dashboard sidebar (if used) |
| `--content-gap` | `24px` | Default gap between cards/sections |

---

## 5. Radius

Amazon uses **small, subtle radii** — not overly rounded. Cards and buttons are slightly
rounded; nothing is pill-shaped by default.

| Token | Value | Usage |
|-------|-------|-------|
| `rounded-sm` | 2px | Tags, micro elements |
| `rounded-md` | 4px | Inputs, buttons (default for interactive) |
| `rounded-lg` | 8px | Cards, containers |
| `rounded-xl` | 12px | Large cards, modals |
| `rounded-full` | 9999px | Avatars, status dots, pill badges |

`--radius` base = **4px** (`0.25rem`); shadcn derives `lg/md/sm` from it.

> **Key difference from previous tokens:** radius is smaller. Amazon's aesthetic is
> structured and sharp — avoid overly rounded UI elements.

---

## 6. Shadows / Elevation

Amazon uses shadows **sparingly**. Most separation comes from borders and background
contrast. Use shadows mainly for floating elements (dropdowns, modals).

| Token | Value | Usage |
|-------|-------|-------|
| `shadow-xs` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle separation |
| `shadow-sm` | `0 1px 3px rgba(0,0,0,0.10)` | Cards (resting) |
| `shadow-md` | `0 4px 8px rgba(0,0,0,0.10)` | Cards (hover), dropdowns |
| `shadow-lg` | `0 8px 16px rgba(0,0,0,0.12)` | Modals, popovers |
| `shadow-focus` | `0 0 0 3px rgba(255,153,0,0.40)` | Focus ring glow (gold) |

> Prefer `border border-border` over shadows for card separation. Use shadows for
> elevation changes (popovers, modals), not for resting cards in most cases.

---

## 7. Borders

| Token | Value |
|-------|-------|
| Default border width | `1px` |
| Emphasis border width | `2px` (focus, selected, active input) |
| Default border color | `--border` (`#CDD4DB`) |
| Divider | `1px solid var(--border)` |

> Amazon uses visible borders on form inputs and cards. Inputs have a clear 1px border
> at rest and a 2px gold/orange border on focus.

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
| `duration-fast` | 100ms | Hover, small state changes |
| `duration-base` | 150ms | Default transitions |
| `duration-slow` | 250ms | Modals, page transitions |
| Easing | `cubic-bezier(0.4, 0, 0.2, 1)` | Standard ease |

> Amazon's UI feels snappy. Keep transitions fast and purposeful.
> Respect `prefers-reduced-motion`: disable non-essential animation.

---

## 11. Component Token Defaults

Canonical per-component values so primitives stay consistent. The component **registry**
([ui-registry.md](ui-registry.md)) must reference these.

### Button

| Variant | Background | Text | Border | Height (md) | Padding-x | Radius |
|---------|-----------|------|--------|-------------|-----------|--------|
| primary | `primary` (gold) | `primary-foreground` (navy) | `1px solid #CC7A00` (darker gold) | 36px (`h-9`) | 16px (`px-4`) | `rounded-md` |
| secondary | `muted` | `foreground` | `border` | 36px | 16px | `rounded-md` |
| outline | `transparent` | `foreground` | `border` | 36px | 16px | `rounded-md` |
| ghost | `transparent` | `foreground` | none | 36px | 16px | `rounded-md` |
| destructive | `danger` | `danger-foreground` | none | 36px | 16px | `rounded-md` |
| accent | `accent` (green) | `accent-foreground` | none | 36px | 16px | `rounded-md` |

Sizes: `sm` h-8 / px-3 / text-sm · `md` h-9 / px-4 / text-sm · `lg` h-10 / px-6 / text-base.
Focus: `shadow-focus` (gold glow) + `ring-2 ring-primary`. Disabled: `opacity-50 cursor-not-allowed`.

> **Amazon button style:** Gold primary with a subtle darker-gold bottom border for depth.
> Secondary buttons are light gray with a border. No rounded-full buttons unless avatar.

### Card

`bg-card text-card-foreground rounded-lg border border-border` · padding `p-6` ·
header/body/footer gap `space-y-4`. Prefer **border** over shadow for resting state.

### Badge

`rounded-md px-2 py-0.5 text-xs font-medium` · variants map to semantic/grade soft pairs.
For the "Eligible for return" badge style: `bg-accent text-accent-foreground rounded-md`.

### Input

`h-9 rounded-md border border-input bg-white px-3 text-sm` · focus `ring-2 ring-primary` +
`border-primary` · error `border-danger` + helper text `text-danger text-xs`.

> **Amazon input style:** Clear border, white bg, gold highlight on focus with 2px border.
> Labels are bold/semibold and sit above the input.

### Select / Dropdown

`h-9 rounded-md border border-input bg-white px-3 text-sm` · same focus as Input.
Placeholder: `text-muted-foreground`.

### Header / NavBar

`bg-secondary text-secondary-foreground h-[60px]` · full-width dark navy bar.
Logo/nav left, user actions right. Links `text-white hover:text-primary`.

### StatCard (dashboard metric)

`Card` + label `text-sm text-muted-foreground font-semibold` + value `text-3xl font-bold
font-mono tabular-nums` + delta `text-xs` (success/danger) + optional icon in `accent`.

### Upload Area

`border-2 border-dashed border-border rounded-lg p-8 text-center` · hover
`border-primary bg-primary/5` · icon `text-muted-foreground`.

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
     borderRadius: { lg: "var(--radius-lg)", md: "var(--radius)", sm: "calc(var(--radius) - 2px)" },
     fontFamily: { sans: ["var(--font-inter)", "system-ui", "sans-serif"], mono: ["var(--font-mono)", "monospace"] },
     boxShadow: {
       xs: "0 1px 2px rgba(0,0,0,0.05)",
       sm: "0 1px 3px rgba(0,0,0,0.10)",
       md: "0 4px 8px rgba(0,0,0,0.10)",
       lg: "0 8px 16px rgba(0,0,0,0.12)",
       focus: "0 0 0 3px rgba(255,153,0,0.40)",
     },
   },
 },
} satisfies Config;
```

```css
/* apps/web/app/globals.css (excerpt) */
:root {
  --background: 30 60% 96%;
  --foreground: 210 29% 20%;
  --card: 0 0% 100%;
  --card-foreground: 210 29% 20%;
  --primary: 36 100% 50%;
  --primary-foreground: 210 29% 20%;
  --secondary: 210 29% 20%;
  --secondary-foreground: 0 0% 100%;
  --accent: 152 60% 36%;
  --accent-foreground: 0 0% 100%;
  --muted: 210 20% 95%;
  --muted-foreground: 210 11% 45%;
  --success: 152 60% 36%; --success-foreground: 0 0% 100%;
  --warning: 36 100% 50%; --warning-foreground: 210 29% 20%;
  --danger: 0 72% 51%; --danger-foreground: 0 0% 100%;
  --info: 207 90% 54%; --info-foreground: 0 0% 100%;
  --border: 210 18% 84%;
  --input: 210 18% 84%;
  --ring: 36 100% 50%;
  --radius: 0.25rem;
  --radius-lg: 0.5rem;
}
```

---

## 13. Amazon Ecosystem Alignment Notes

This token system is designed to make the app feel native to Amazon's UI language:

| Amazon Pattern | Our Implementation |
|----------------|-------------------|
| Dark navy header (`#232F3E`) | `--secondary` as header bg |
| Warm cream page bg | `--background` at `#FEF7ED` |
| Gold/yellow primary CTAs | `--primary` at `#FF9900` |
| Bold labels above inputs | `font-semibold` + positioned above |
| Clear input borders, gold on focus | `border-input` → `ring-primary` on focus |
| Minimal shadows, border-first | Cards use `border` not `shadow` |
| Small corner radius (3–4px) | `--radius: 0.25rem` (4px) |
| Green for positive/sustainability | `--accent` stays eco-green |
| "Eligible for return" pill badge | `Badge` variant with accent bg |
| Star ratings in gold | `text-primary` for filled stars |
| Upload area with dashed border | Defined in component tokens |

> When you add or change a token: update **this file**, `globals.css`, and
> `tailwind.config.ts` together, then note any new component value in
> [ui-registry.md](ui-registry.md).
