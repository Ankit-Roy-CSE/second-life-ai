/**
 * Async-state selector for data views.
 *
 * Centralizes the fixed-precedence rule that every Async_Data_View must follow:
 *   Loading → Error → Empty → Success
 *
 * Pure function — no UI imports, no side effects.
 */

export type AsyncState = "loading" | "error" | "empty" | "success"

/**
 * Returns exactly one async state based on query flags and item count.
 *
 * Precedence (highest first):
 *  1. isLoading  → "loading"
 *  2. isError    → "error"
 *  3. itemCount <= 0 → "empty"
 *  4. otherwise  → "success"
 */
export function selectAsyncState(input: {
  isLoading: boolean
  isError: boolean
  itemCount: number
}): AsyncState {
  if (input.isLoading) return "loading"
  if (input.isError) return "error"
  if (input.itemCount <= 0) return "empty"
  return "success"
}
