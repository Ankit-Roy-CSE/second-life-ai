# Problems in a Second Life Commerce System

> **Solution mapping.** Each problem below is tagged with the microservice(s) that address it
> in **Amazon Second Life AI**. See [architecture.md](../docs/architecture.md) §3 for the full
> service catalog. Status reflects MVP scope — some problems are deliberately deferred to the
> [PRD](prd.md) §11 future roadmap.

## Status Legend

- ✅ **Solved** — directly addressed by the MVP.
- 🟡 **Partial** — mitigated but not fully solved within MVP scope.
- ⛔ **Not in MVP** — out of scope for the hackathon build (future roadmap).

## Service Legend

| Tag | Service | Responsibility |
|-----|---------|----------------|
| `grading` | AI Grading | Condition grade (A–D), confidence, damage summary from images/video |
| `lifecycle` | Lifecycle Decision | Resell / Refurbish / Donate / Recycle / Hyperlocal routing + value estimate |
| `passport` | Product Passport | Transparent grade, ownership, refurb & sustainability history |
| `matching` | Hyperlocal Matching | Nearby-buyer discovery, match scoring, logistics-savings estimate, listings |
| `sustainability` | Sustainability | CO₂ avoided, waste diverted, value recovered, green credits, dashboard |
| `user` | User | Profile, preferences, green-credit balance |
| `gateway` | API Gateway | Returns intake, routing/aggregation, dashboard read-model |

---

## Product Assessment Problems

- ✅ Determining whether a returned product is genuinely functional. → **`grading`** (AI condition grade + confidence + defect list)
- 🟡 Detecting hidden defects that are not visible in images. → **`grading`** (adds video analysis + confidence score to surface uncertainty; truly hidden internal defects remain hard to detect)
- ✅ Inconsistent quality checks by different warehouse employees. → **`grading`** (deterministic AI grading removes per-employee variance)
- ✅ High manual inspection costs. → **`grading`** (automated, keyless mock or real Bedrock/Rekognition)
- ✅ Difficulty grading products into standard quality categories. → **`grading`** (standard A/B/C/D enum)

## Trust Problems

- ✅ Buyers do not trust refurbished or second-hand products. → **`passport`** + **`grading`** (verifiable grade + transparent history)
- ✅ Fear of receiving products different from what was advertised. → **`passport`** + **`grading`** (objective condition record buyers can inspect)
- 🟡 Uncertainty about the remaining lifespan of a product. → **`passport`** (usage/refurb history gives signal; explicit lifespan prediction is future scope)
- ✅ Lack of transparency regarding previous usage history. → **`passport`** (ownership + refurbishment history)
- 🟡 Concerns about authenticity and product reliability. → **`passport`** (provenance trail; cryptographic authenticity verification not in MVP)

## Return Management Problems

- ✅ Processing returns is expensive. → **`gateway`** + **`lifecycle`** (automated intake + routing, no manual triage)
- ✅ Many perfectly usable items end up in liquidation or disposal. → **`lifecycle`** (routes to Resell / Refurbish / Donate before disposal)
- ✅ Delays in deciding the next action for returned inventory. → **`lifecycle`** (instant, event-driven decision on `ProductGraded`)
- ✅ Warehouses become overloaded with returned products. → **`matching`** (hyperlocal transfer diverts items before reverse logistics)
- ✅ Significant operational costs associated with reverse logistics. → **`matching`** + **`lifecycle`** (avoids unnecessary shipping legs)

## Resale Problems

- ✅ Finding the right buyer for a returned item. → **`matching`** (nearby-buyer discovery + match scoring)
- 🟡 Pricing second-hand products accurately. → **`lifecycle`** (value-recovery estimate; dynamic refurbished pricing is roadmap Phase 2)
- ✅ Low visibility of refurbished products compared to new products. → **`matching`** (listings) + **`passport`** (trust-building detail)
- ✅ Long resale cycles leading to increased storage costs. → **`matching`** (fast local matching shortens the cycle)
- ✅ Difficulty matching supply with demand. → **`matching`** (interest + location matching)

## Sustainability Problems

- ✅ Excessive waste generated from usable products. → **`lifecycle`** (reuse routing) + **`sustainability`** (waste-diverted tracking)
- ✅ Carbon emissions caused by transportation and disposal. → **`matching`** (shorter shipping distances) + **`sustainability`** (CO₂-avoided tracking)
- ✅ Products discarded due to minor defects. → **`grading`** + **`lifecycle`** (minor-defect items routed to resell/refurbish)
- ✅ Customers lack incentives to choose sustainable alternatives. → **`sustainability`** (green credits) + **`user`** (credit balance)
- ✅ Limited visibility into the environmental impact of returns. → **`sustainability`** (live dashboard: CO₂, waste, value, credits)

## Customer Behavior Problems

- ⛔ High return rates due to incorrect size or fit. → Predictive Return Prevention (PRD roadmap Phase 2)
- ⛔ Impulse purchases that are later returned. → Not in MVP
- ⛔ Customers ordering multiple variants and returning most of them. → Not in MVP
- 🟡 Lack of awareness about refurbished alternatives. → **`matching`** (marketplace listings surface refurbished options)
- ⛔ Unrealistic expectations leading to unnecessary returns. → Not in MVP (return-prevention scope)

## Peer-to-Peer Resale Problems

> The MVP is **platform-mediated** (listings are generated from platform-graded products, not
> created by third-party sellers), which structurally avoids most P2P fraud vectors.

- 🟡 Fake listings. → **`matching`** + **`grading`** (listings derive from real graded inventory, not free-form user posts)
- ⛔ Counterfeit products. → Not in MVP (no authenticity verification engine)
- 🟡 Fraudulent sellers. → Platform-mediated model (no third-party sellers in MVP)
- ✅ Disputes regarding product condition. → **`passport`** + **`grading`** (objective, timestamped condition record)
- ✅ Lack of trust between buyers and sellers. → **`passport`** (shared transparent history)
- 🟡 Challenges in verifying ownership and authenticity. → **`passport`** (ownership-transfer history; authenticity verification is future)

## Logistics Problems

- ✅ Shipping costs can exceed the resale value of low-cost products. → **`matching`** (hyperlocal) + **`lifecycle`** (value estimate gates routing)
- ⛔ Difficulty identifying the optimal refurbishment center. → Not in MVP (no refurb-center routing)
- ✅ Managing reverse logistics efficiently. → **`matching`** + **`lifecycle`** (divert before / route within reverse logistics)
- 🟡 Handling bulky or fragile products that are expensive to transport. → **`matching`** (reduces distance; no special-handling logic)
- ⛔ Optimizing inventory movement across multiple locations. → Not in MVP (Cross-Region Redistribution, roadmap Phase 3)

## Data and AI Problems

- ⛔ Insufficient historical data for accurate predictions. → Inherent cold-start limitation (deterministic mock seeding used for demo)
- 🟡 Bias in condition assessment models. → **`grading`** (confidence scores surface uncertainty; formal bias auditing not in MVP)
- 🟡 Incorrect classification leading to revenue loss. → **`grading`** (confidence) + **`lifecycle`** (value estimate) reduce blast radius
- ⛔ Difficulty estimating future demand for returned products. → Not in MVP (Real-Time Demand Forecasting, roadmap Phase 3)
- ✅ Lack of explainability in AI-driven decisions. → **`grading`** (damage summary) + **`lifecycle`** (rationale) + **`matching`** (match rationale) — every AI output ships with a human-readable explanation

## Warranty and Support Problems

- ⛔ Determining appropriate warranty periods for refurbished products. → Not in MVP
- ⛔ Handling warranty claims for second-life products. → Not in MVP
- ✅ Tracking ownership transfers. → **`passport`** (ownership history)
- ✅ Maintaining repair and refurbishment histories. → **`passport`** (refurbishment history)
- ⛔ Managing customer support for reused products. → Not in MVP

---

## High-Impact Problems Worth Solving in a Hackathon

| # | Problem | Status | Solved by |
|---|---------|--------|-----------|
| 1 | Building trust in refurbished and second-hand products. | ✅ | `passport` + `grading` |
| 2 | Accurate AI-powered condition grading. | ✅ | `grading` |
| 3 | Finding the next best owner for returned products. | ✅ | `matching` + `lifecycle` |
| 4 | Preventing unnecessary returns before purchase. | ⛔ | Future (roadmap Phase 2) |
| 5 | Creating sustainability incentives through rewards and green credits. | ✅ | `sustainability` + `user` |
| 6 | Optimizing return routing (resell, refurbish, donate, recycle). | ✅ | `lifecycle` |
| 7 | Improving transparency about product condition and history. | ✅ | `passport` |
| 8 | Reducing operational costs associated with returns. | ✅ | `gateway` + `lifecycle` + `matching` |

**Coverage:** 7 of the 8 high-impact problems are directly solved by the MVP. The eighth
(return prevention) is intentionally deferred to the future roadmap, keeping the weekend scope
focused on the value-recovery spine: **grade → decide → passport → match → sustainability**.
