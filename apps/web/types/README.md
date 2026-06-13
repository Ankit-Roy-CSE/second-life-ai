# Frontend Types — Amazon Second Life AI

> **TypeScript mirrors of Python backend schemas.**  
> These types MUST stay in sync with `packages/shared-py/shared_py/schemas/`.

---

## Files

| File | Purpose | Python source |
|------|---------|---------------|
| `enums.ts` | 5 shared enums (Grade, LifecycleAction, ReturnStatus, ListingChannel, ListingStatus) | `shared_py/schemas/enums.py` |
| `events.ts` | Event envelope + 10 event payload types | `shared_py/events/schemas.py` |
| `api.ts` | REST request/response types (User, Return, Grade, Decision, Passport, Match, Listing, Sustainability) | `shared_py/schemas/rest_contracts.py` |
| `index.ts` | Re-exports all types for clean imports | — |

---

## Usage

Import types from the barrel export:

```typescript
import {
  Grade,
  ReturnStatus,
  ReturnResponse,
  EventEnvelope,
  ProductGradedEventData,
} from "@/types";

// Or use the full path:
import { Grade } from "@/types/enums";
```

---

## Keeping in Sync

**When modifying:**

1. Update the Python source first (e.g. `shared_py/schemas/enums.py`).
2. Update the corresponding TS file here (e.g. `types/enums.ts`).
3. **Commit both in the same PR** — the contract change is atomic across stacks.
4. If the change affects cross-service calls, update `docs/code-standards.md` §4.1 and/or `packages/shared-py/shared_py/schemas/SERVICE_ENDPOINTS.md`.

**Automated sync (future):**

- Consider a codegen script (`scripts/sync_types.py`) that reads Python schemas and generates TS types.
- For now, manual sync is acceptable for a 48h build.

---

## Validation

Frontend API client (`lib/api`) should validate responses with **Zod schemas** mirroring these types. See:

```typescript
// lib/api/schemas.ts (to be created by Member C in P0-C3)
import { z } from "zod";

export const ReturnResponseSchema = z.object({
  id: z.string().uuid(),
  product_id: z.string().uuid(),
  user_id: z.string().uuid(),
  reason: z.string(),
  status: z.nativeEnum(ReturnStatus),
  media: z.array(z.string()),
  created_at: z.string().datetime(),
});

export type ReturnResponse = z.infer<typeof ReturnResponseSchema>;
```

---

## Notes

- All IDs are UUID v4 strings.
- All timestamps are ISO-8601 UTC strings.
- Enums are string enums (not numeric) to match Python `str, Enum`.
- The `PaginatedResponse<T>` generic wraps list endpoints with `total`, `limit`, `offset`.
- Error responses use `ErrorEnvelope` with `{ error: { code, message, correlation_id } }`.
