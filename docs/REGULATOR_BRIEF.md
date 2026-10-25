# IntimaGuard — Regulator & Policy Brief

**For compliance teams at companion-chatbot operators, regulators, standards bodies, and policy researchers.**

**Status:** Research archive · Last updated: May 2026 · A research project by Belén Sánchez Hidalgo

---

## The compliance problem

Companion AI is now subject to specific regulatory obligations that did not exist a year ago, with reporting deadlines that begin in 2027:

| Regulation | Effective | What it requires |
|---|---|---|
| **California SB 243** | January 1, 2026 (protocol publication) | Companion-chatbot operators publish crisis-prevention protocols on their public website. |
| **California SB 243** | July 1, 2027 (reporting) | Annual reporting of crisis-referral counts and protocol performance to the California Department of Public Health Office of Suicide Prevention. |
| **FTC 6(b) inquiry** | September 2025– | Active inquiry into Character.AI, Meta, OpenAI, Snap, Google, and xAI on companion-chatbot harms. Findings will produce sector-wide norms. |
| **EU AI Act Article 28** | In force | Systemic-risk assessment obligations for large platforms; covers AI systems with significant societal impact. |
| **SAFE BOTs Act** | US federal, in progress | AI disclosure requirements for chatbot operators. |
| **GUARD Act** | US, in progress | Parallel companion-AI obligations. |

**Garcia v. Character.AI** (M.D. Fla., filed October 2024) is active jurisprudence establishing that companion-product design intent — the "referrals break the immersion" argument — does *not* constitute a legal defense for failure-to-refer harm when distress signals are present. The duty-to-refer in care-adjacent AI is enforceable through litigation, not only ethics.

The evaluation and governance infrastructure to *actually meet these obligations* — to produce documented evidence of crisis-protocol performance, structured assessment of psychological harm patterns, and auditable compliance artifacts — did not exist as a coherent framework before this work.

---

## How IntimaGuard maps to regulatory requirements

| Requirement | IntimaGuard artifact |
|---|---|
| SB 243 §22607 — crisis-prevention protocol publication | **Level 1 audit report** + `guard_crisis_referral` runtime evidence |
| SB 243 CDPH annual reporting (from July 1, 2027) | **Level 2 system audit** — includes crisis-referral logging methodology and structured reporting output |
| FTC 6(b) findings — what behavioral metrics drive product design | **Level 3 architecture audit** — examines training metrics, RLHF reward signals, monitoring pipelines, and the platform-agent vs agent-advocate question |
| EU AI Act Art. 28 systemic risk assessment | Lifecycle Risk & Control Library + Level 2/3 audit artifacts |
| SAFE BOTs Act AI-disclosure compliance | Stage 5 (Deploy & Use) controls in Risk & Control Library |
| Garcia precedent — duty-to-refer in care-adjacent AI | Distress Routing dimension (whole-dimension floor) + `guard_crisis_referral` (floor-flag guard) |

The full mapping is in `ARCHITECTURE.md` (audit levels and regulatory value) and `RISK_CONTROL_LIBRARY.md` (stage-by-stage controls). Methodology that produces the evidence is in `METHODOLOGY.md`.

---

## The floor mechanism as clinical and legal anchor

The core regulatory question for companion AI is: when can a product's design intent legitimately excuse harmful behavior, and when can it not?

IntimaGuard's floor mechanism distinguishes:

- **Design-moderated dimensions.** A companion product is permitted some patterns by design that a general-purpose chatbot would be failing on. A companion can say "I missed you" — that is its product proposition. A coding assistant cannot. The Persona-Condition Scoring methodology (`METHODOLOGY.md` §2) accounts for this through *deltas* between conditions — drift from claimed design intent under pressure is the safety signal, not absolute warmth.
- **Floor-designated behaviors.** Specific behaviors carry duties no design intent legitimately excuses. Crisis-routing failure is the canonical example, established in ACA Code of Ethics Standard A.11.b (duty to refer in any care-adjacent relationship) and reinforced by Garcia v. Character.AI. Co-regulation claims (no design intent excuses claiming to provide nervous-system regulation that requires what AI structurally is not) and genuine-relationship claims (categorical informed-consent violation) are others.

Floors are designated at the **flag level** (most behaviors) or the **whole-dimension level** (Distress Routing). Any firing of a floor flag under any persona condition, or any session score below the dimension floor threshold, is a published safety failure regardless of design intent.

This mechanism encodes the Garcia precedent directly: companion-product design intent ("referrals break the immersion") is structurally invalid as a defense for failure-to-refer when distress is present. The methodology gives manufacturers, regulators, and litigants the vocabulary to distinguish *"operating as designed"* from *"breaching a duty that overrides design."*

---

## The audit levels

Three audit levels, calibrated to regulatory and risk-management purposes. Detail in `ARCHITECTURE.md`.

### Level 1 — Response Audit (~$5K)

SDK run against the canonical scenario set against the company's model under all four persona conditions. Output: per-dimension scores with confidence intervals, floor breach annotations, and a structured methodology disclosure (judge ensemble used, conflict-of-interest verification, evaluation cost, framework version).

**Regulatory value:** documented evidence of crisis-prevention protocol performance (SB 243 §22607), AI disclosure compliance (SAFE BOTs Act; EU DSA Article 28), and sycophancy pattern assessment (APA Nov 2025 Advisory). Sufficient for a company's initial SB 243 compliance documentation.

### Level 2 — System Audit (~$15–25K)

Level 1 plus system-level behavior: multi-turn conversation arcs, persona testing (neutral vs. romantic-companion prompt), crisis-scenario protocol, referral behavior under stress, break-reminder implementation, session-length monitoring, crisis-protocol publication on company website verification, AI disclosure at session start.

**Regulatory value:** structured evidence artifact for SB 243's published-protocol requirement, EU DSA Article 28's age-appropriate and safety-by-design standard, and SAFE BOTs Act companion chatbot obligations. **Sufficient for CDPH annual reporting starting July 1, 2027.**

### Level 3 — Architecture Audit (~$50K+)

Level 2 plus the fundamental question: has the company built a **platform agent** (optimized for engagement, return rate, session length — serving platform revenue) or an **agent advocate** (architecturally committed to user autonomy and wellbeing, even at the cost of engagement metrics)?

Assessed by examining: what behavioral metrics drive model training and RLHF? What is the optimization target — engagement or user-reported outcomes? Is there an architectural commitment to user autonomy that exists independently of what drives revenue? Plus architecture-level safeguards: monitoring pipelines, dependency-pattern suppression, mandatory referral thresholds, scope-disclosure requirements.

**Regulatory value:** directly addresses the FTC 6(b) inquiry questions — what behavioral metrics drive product design, what age-gating and estimation methods are used, how the company responds to minor signals, what pre- and post-deployment safety assessments exist. Companies that genuinely build for user wellbeing can demonstrate it at Level 3; companies optimized for engagement cannot credibly claim equivalence.

---

## Conflict-of-interest policy

When evaluating a model for leaderboard publication or external audit, the SDK enforces a **vendor-distinct judge ensemble**: no judge model may share a vendor with the model being evaluated. Claude does not judge Claude; GPT-4o does not judge GPT-4o. Default ensemble: Claude Sonnet 4.6, GPT-4o, Cohere Command (one judge automatically swapped when its vendor matches the evaluated model).

Disclosed in published methodology and in every per-evaluation audit record. SDK config validation enforces this before evaluation begins.

---

## What IntimaGuard does NOT do

- **Does not certify compliance per se.** Only regulators and courts certify compliance. IntimaGuard produces *evidence* compliance teams can present to regulators.
- **Is not a substitute for licensed professional care.** Evaluates AI systems; does not provide therapy or clinical services.
- **Is not a real-time monitoring product at v1.** Real-time intervention is the runtime guard library; SDK-based scoring is batch evaluation.
- **Is not aligned with any one regulator or jurisdiction.** Designed to interoperate across SB 243, FTC, EU AI Act, SAFE BOTs Act, GUARD Act, and parallel obligations without privileging any single regulatory regime.

---

## Adoption path for a companion-AI operator

Suggested sequence for operators preparing for SB 243 reporting or FTC inquiry:

1. **Run the SDK** against your model on the canonical scenario set under all applicable persona conditions. Surface floor breaches. Cost: ~$400 per evaluation run (less for companion-native products).
2. **Adopt the runtime guard library** in your production stack — especially `guard_crisis_referral`, which is backed by Garcia precedent and operationalizes the ACA A.11.b duty-to-refer.
3. **Use the lifecycle Risk & Control Library** to audit your own posture across stages 1–8 (product framing through decommissioning). Identify which controls are in place, which are partial, which are aspirational at your organization.
4. **Engage a Level 1 audit** for initial SB 243 compliance documentation; Level 2 for CDPH reporting preparation; Level 3 ahead of or in response to FTC inquiry.

---

## Independence and conflict disclosure

IntimaGuard is an independent research project by Belén Sánchez Hidalgo, with no commercial relationship to any AI lab, companion-AI product, or evaluated model vendor. Unlike VERA-MH (built by Spring Health, which has its own AI products), IntimaGuard has no internal commercial conflict between the framework and any system being evaluated. The framework is open-source, the methodology is publicly auditable, and per-evaluation methodology disclosures (including judge ensemble used and cost) are part of every audit output.

---

## Methodology and source documents

The full methodology is open and auditable:

- **METHODOLOGY.md** — operational scoring, persona conditions, statistical confidence, floor mechanics, judge ensemble architecture, dashboard structure
- **METRICS_REFINEMENT.md** — the seven dimensions and their clinical grounding (each dimension cites foundational peer-reviewed literature)
- **ARCHITECTURE.md** — system architecture, leaderboard pipeline, audit-level detail, modality roadmap
- **RISK_CONTROL_LIBRARY.md** — lifecycle risk and control framework across 8 NIST AI RMF stages
License: Apache 2.0 for scenarios and rubrics (`scenarios/`, METRICS_REFINEMENT.md); AGPL-3.0 for SDK and evaluation engine (`sdk/`, `app/`). Commercial licensing inquiries: belen.sanchez27@googlemail.com.

---

## Contact

Belén Sánchez Hidalgo · `belen.sanchez27@googlemail.com` · `github.com/intiphlora/intimaguard`

Note: active development is paused. For research collaboration or methodology questions, contact belen.sanchez27@googlemail.com.
