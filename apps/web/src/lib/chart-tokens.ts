/**
 * Ordered chart color accessor for Recharts.
 *
 * Colors are sourced exclusively from the Chart_Tokens design tokens
 * (--chart-1 … --chart-6) defined in globals.css and tailwind.config.ts.
 * Never use raw hex literals in components — reference this tuple instead.
 *
 * Satisfies Requirements 3.2, 7.3, 7.4.
 */
export const CHART_TOKENS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
  "hsl(var(--chart-6))",
] as const

export type ChartToken = (typeof CHART_TOKENS)[number]
