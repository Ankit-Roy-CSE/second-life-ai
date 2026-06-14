# Amazon Second Life AI — Demo Script

**Total Runtime:** ~4:00  
**Flow:** Login → Dashboard → Submit Return → AI Grading → Decision → Passport → Matches → Marketplace → Sustainability → Logout

---

## Scene 1: Opening (0:00–0:10)

> "Welcome to Amazon Second Life AI — a platform that uses AI to give every returned product on Amazon its best possible second life. Let me show you how it works."

---

## Scene 2: Authentication & Dashboard (0:10–0:50)

> "Users sign in through our secure auth system with real-time Zod validation."

*[Type email: demo@amazon.com, password: any value, click "Sign in"]*

> "We land on the personalized Dashboard. On the left — the Profile Card with the user's Green Credits balance. On the right — Active Returns showing live status of each item in the pipeline, and a Sustainability Summary with CO₂ avoided and credits earned."

*[Point to each section briefly]*

> "The NavBar dynamically reflects the logged-in user — live credits badge that links to sustainability analytics, avatar initial, and a Log Out button. Let's submit a return."

*[Click "Returns" in navbar]*

---

## Scene 3: Return Submission & AI Grading (0:50–1:50)

> "Here sellers submit returns. Select a reason — defective — upload photos…"

*[Select "Defective / Does not work", drag files into upload zone]*

> "…and submit for AI inspection."

*[Click "Submit for AI Inspection"]*

> "Our AI engine — powered by AWS Bedrock and Rekognition — analyzes the images in real-time."

*[Watch progress: 20%… 40%… 60%… 80%… 100%]*

> "Grade A — Like New — 98% confidence. No scratches, no dents, zero defects. An excellent resale candidate."

---

## Scene 4: Lifecycle Decision & Passport (1:50–2:35)

*[Click "View Full Decision"]*

> "The AI doesn't just grade — it decides the optimal next step. Here it recommends Resell, with a value recovery of two-forty-nine ninety-nine and a sustainability score of ninety-five out of one hundred."

*[Navigate to /passport/pass_123]*

> "Every product gets a Digital Passport — an immutable lifecycle record. The timeline traces it from manufacture through purchase, return, grading, decision, to passport creation. Full transparency for the next owner."

---

## Scene 5: Hyperlocal Matching (2:35–3:00)

*[Navigate to /matches]*

> "Hyperlocal Matching finds nearby buyers instead of shipping to warehouses — cutting logistics cost and carbon. Alice is our top match at ninety-two percent, two-point-four kilometers away, saving fifteen-fifty in shipping. All powered by our geospatial matching engine."

---

## Scene 6: Marketplace (3:00–3:25)

*[Navigate to /marketplace]*

> "Products also land on our Refurbished Marketplace. Each card features product imagery, AI-verified grade badges, and pricing. Users filter by channel — marketplace or local pickup. The Sony headphones at two-forty-nine ninety-nine, the Logitech mouse at eighty-nine ninety-nine for local pickup."

---

## Scene 7: Sustainability & Closing (3:25–4:00)

*[Click Credits badge in navbar → /sustainability]*

> "The Sustainability Dashboard tracks cumulative impact — one-twenty point five kilos of CO₂ avoided, forty-five kilos of waste diverted, eight-fifty dollars recovered, three-twenty green credits earned. The breakdown chart shows impact per lifecycle action."

*[Click "Log out" in navbar]*

> "One click to log out — session cleared, token removed, redirected to login. No stale data anywhere."

*[Pause]*

> "Seven microservices, an event-driven saga, AI that gracefully degrades between real AWS and mock modes — turning Amazon's return problem into a sustainability solution. Thank you."

---

## Key Features Highlighted

| Feature | Scene | What's Shown |
|---------|-------|-------------|
| Secure Auth | 2 | Zod validation, JWT tokens, toast notifications |
| **User Dashboard (NEW)** | 2 | Profile card, active returns, sustainability summary |
| **Dynamic NavBar (NEW)** | 2, 7 | Live credits → /sustainability, avatar, Log Out |
| Return Submission + AI Grading | 3 | Upload, progress animation, Grade A result |
| Lifecycle Decision | 4 | Rationale, value recovery, sustainability score |
| Digital Product Passport | 4 | Timeline, ownership history, immutable record |
| Hyperlocal Matching | 5 | Geospatial buyer matches, distance, savings |
| **Marketplace with Images (NEW)** | 6 | Product photos, grade badges, channel tabs |
| Sustainability Dashboard | 7 | 4 stat cards, breakdown chart |
| **Secure Logout (NEW)** | 7 | Session clear, redirect |

---

## Pre-Demo Checklist

- [ ] Dev server running (`cd apps/web && npm run dev`)
- [ ] Mock mode active (default — no AWS keys needed)
- [ ] Browser at `http://localhost:3000/login`
- [ ] Clear localStorage for clean first-login experience
- [ ] Browser zoom 90-100%
