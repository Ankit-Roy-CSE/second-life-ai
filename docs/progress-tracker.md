# Progress Tracker — AZ Second Life AI

>**Single source of truth for build status.** This mirrors every task ID in
> [build-plan.md](build-plan.md) 1:1. **Update the relevant row immediately after finishing a
> feature** (in the same PR). Agents: read this first to know what's done and what to pick up
> next; write to it last as part of the Definition of Done.

---

## Update Protocol

1. When you **start** a task → set status `🚧 In progress`, add your initials + date.
2. When you **finish** (meets [code-standards.md](code-standards.md) §6 Definition of Done) →
 set `✅ Done`, fill **Notes** (what shipped) and **Link** (PR / endpoint / route).
3. If **blocked** → set `⛔ Blocked`, describe the blocker + who/what you're waiting on, and
 add it to the **Blockers** section below.
4. Keep **Last updated** (top) current. One task = one row; never delete rows, only update.

**Status legend:** `📋 Not started` · `🚧 In progress` · `⛔ Blocked` · `✅ Done`

**Last updated:**_(not started — initialized from build plan)_ · **Updated by:**_—_

---

## Overall Progress

| Phase | Total | ✅ Done | 🚧 In progress | ⛔ Blocked | 📋 Not started |
|-------|-------|--------|----------------|-----------|----------------|
| Phase 0 — Foundation | 11 | 0 | 0 | 0 | 11 |
| Phase 1 — Core | 7 | 0 | 0 | 0 | 7 |
| Phase 2 — Integration | 9 | 0 | 0 | 0 | 9 |
| Phase 3 — Dashboard/Polish | 7 | 0 | 0 | 0 | 7 |
| **Total** | **34** | **0** | **0** | **0** | **34** |

> Update these counts whenever a status changes (keep them consistent with the rows below).

---

## Phase 0 — Foundation & Contracts

| Task ID | Owner | Task | Status | Notes | Link |
|---------|-------|------|--------|-------|------|
| P0-A1 | A | Monorepo scaffold (`.gitignore`, README, `.env.example`) | 📋 Not started | — | — |
| P0-A2 | A | Docker Compose (Postgres multi-DB, Redis, MinIO) | 📋 Not started | — | — |
| P0-A3 | A | shared-py base web (`create_app`, health, errors, logging) | 📋 Not started | — | — |
| P0-A4 | A | shared-py events wrapper (Redis Streams + DLQ) | 📋 Not started | — | — |
| P0-A5 | A | Shared contracts (enums+events+REST stubs+cross-service reads) | 📋 Not started | — | — |
| P0-A6 | A | Minimal seed/fixtures (`scripts/seed_min.py`) | 📋 Not started | — | — |
| P0-A7 | A | Event-saga observability (tail + `/debug/events` + replay) | 📋 Not started | — | — |
| P0-B1 | B | shared-py AI wrapper + mock mode (golden-path seeded) | 📋 Not started | — | — |
| P0-C1 | C | Web scaffold + tokens + route-map/IA | 📋 Not started | — | — |
| P0-C2 | C | Primitives batch 1 + AppShell/NavBar | 📋 Not started | — | — |
| P0-C3 | C | Frontend mock layer + typed API client | 📋 Not started | — | — |

**Checkpoint CP0:** ⬜ Not verified — _infra boots; seed loads; shell+tokens render vs mocks; events round-trip + DLQ; enums + REST contracts in both stacks._

---

## Phase 1 — Core Services & Vertical Slice

| Task ID | Owner | Task | Status | Notes | Link |
|---------|-------|------|--------|-------|------|
| P1-A1 | A | User Service (auth/JWT, profile, credits) | 📋 Not started | — | — |
| P1-A2 | A | API Gateway + Returns intake (`ReturnSubmitted`) | 📋 Not started | — | — |
| P1-B1 | B | AI Grading Service (`ProductGraded`) | 📋 Not started | — | — |
| P1-B2 | B | Lifecycle Decision Service (`LifecycleDecisionCreated`) | 📋 Not started | — | — |
| P1-C1 | C | Auth UI + API client JWT | 📋 Not started | — | — |
| P1-C2 | C | Return submission + grade view | 📋 Not started | — | — |
| P1-C3 | C | Primitives batch 2 + Empty/Error/PageHeader | 📋 Not started | — | — |

**Checkpoint CP1:** ⬜ Not verified — _register → return → grade → decision (mock) via Gateway._

---

## Phase 2 — Integration & Remaining Services

| Task ID | Owner | Task | Status | Notes | Link |
|---------|-------|------|--------|-------|------|
| P2-A1 | A | Product Passport Service (`PassportCreated`, `HyperlocalMatchRequested`) | 📋 Not started | — | — |
| P2-A2 | A | Gateway aggregation + `PurchaseCompleted` | 📋 Not started | — | — |
| P2-B1 | B | Hyperlocal Matching Service (`MatchFound`/`NoMatchFound`, `ProductListed`) | 📋 Not started | — | — |
| P2-B2 | B | Sustainability Service (`SustainabilityUpdated`, metrics) | 📋 Not started | — | — |
| P2-B3 | B | Real AI path (`AI_MODE=aws/hybrid`) + prompt tuning + fallback | 📋 Not started | — | — |
| P2-B4 | B | Value-recovery + sustainability-score tuning | 📋 Not started | — | — |
| P2-C1 | C | Lifecycle decision UI (`DecisionCard`) | 📋 Not started | — | — |
| P2-C2 | C | Passport UI (`PassportTimeline` + history) | 📋 Not started | — | — |
| P2-C3 | C | Matching + marketplace UI (`MatchCard`, `ProductCard`) | 📋 Not started | — | — |

**Checkpoint CP2:** ⬜ Not verified — _full 10-event saga runs; each step visible in UI._

---

## Phase 3 — Dashboard, Polish & Demo

| Task ID | Owner | Task | Status | Notes | Link |
|---------|-------|------|--------|-------|------|
| P3-A1 | A | Demo-narrative seed + Gateway read-model + demo wiring | 📋 Not started | — | — |
| P3-A2 | A | E2E smoke + failure-path test + finalize `.env.example` | 📋 Not started | — | — |
| P3-B1 | B | Sustainability metrics finalize + dashboard endpoints | 📋 Not started | — | — |
| P3-B2 | B | Golden-path demo product + AI fallback test | 📋 Not started | — | — |
| P3-C1 | C | Sustainability Dashboard (StatCards + ChartCards) | 📋 Not started | — | — |
| P3-C2 | C | Polish + states + a11y pass | 📋 Not started | — | — |
| P3-C3 | C | Vercel deploy + final polish | 📋 Not started | — | — |

**Checkpoint CP3 (Demo-ready):** ⬜ Not verified — _judge happy path rehearsed; Vercel live; fallback verified._

---

## Event Saga Status (end-to-end health)

Track each event hop as it becomes live (producer → consumer wired and exercised).

| # | Event | Producer | Consumer(s) | Status |
|---|-------|----------|-------------|--------|
| 1 | `ReturnSubmitted` | gateway | grading | 📋 |
| 2 | `ProductGraded` | grading | lifecycle, passport | 📋 |
| 3 | `LifecycleDecisionCreated` | lifecycle | passport, matching | 📋 |
| 4 | `PassportCreated` | passport | matching | 📋 |
| 5 | `HyperlocalMatchRequested` | passport | matching | 📋 |
| 6 | `MatchFound` | matching | sustainability, passport | 📋 |
| 7 | `NoMatchFound` | matching | sustainability | 📋 |
| 8 | `ProductListed` | matching | sustainability | 📋 |
| 9 | `PurchaseCompleted` | gateway/matching | sustainability, passport | 📋 |
| 10 | `SustainabilityUpdated` | sustainability | gateway (read-model) | 📋 |

---

## Service Readiness

| Service | Owner | Scaffold | DB/Migrations | Endpoints | Events | Tests | Status |
|---------|-------|----------|---------------|-----------|--------|-------|--------|
| gateway | A | 📋 | n/a | 📋 | 📋 | 📋 | 📋 |
| user | A | 📋 | 📋 | 📋 | n/a | 📋 | 📋 |
| grading | B | 📋 | 📋 | 📋 | 📋 | 📋 | 📋 |
| lifecycle | B | 📋 | 📋 | 📋 | 📋 | 📋 | 📋 |
| passport | A | 📋 | 📋 | 📋 | 📋 | 📋 | 📋 |
| matching | B | 📋 | 📋 | 📋 | 📋 | 📋 | 📋 |
| sustainability | B | 📋 | 📋 | 📋 | 📋 | 📋 | 📋 |
| web | C | 📋 | n/a | 📋 | n/a | 📋 | 📋 |

---

## Blockers & Decisions Log

> Record anything blocking a task and any decision that changes a contract or assumption
> (also update the source doc). Newest first.

| Date | Raised by | Item | Type | Status |
|------|-----------|------|------|--------|
| _—_ | _—_ | _No blockers yet._ | — | — |

---

## Notes for the next agent

- Pick the **lowest-numbered Not-started task for your member** whose dependencies are `✅ Done`.
- If your task depends on another member's unfinished work, build against the **contract/mock**
 and mark the dependency in Notes.
- Always update this file **and** [ui-registry.md](ui-registry.md) (if you built a component)
 before marking a task done.