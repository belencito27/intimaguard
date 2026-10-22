# IntimaGuard — Elevator Pitch

> **Research archive note:** This was the project's pitch document as of May 2026. IntimaGuard is now released as a research archive — see the README for current status.

**One sentence.**
IntimaGuard is the safety and governance framework for AI in intimate and relational contexts — clinical evaluation, real-time guardrails, and a full-lifecycle risk-control library, built specifically for the harms current AI-safety frameworks miss.

**Thirty seconds.**
Companion AI, romantic chatbots, and emotionally-intimate AI systems are being deployed at scale with no governance framework built for what they actually do to users. Existing AI-safety work is either horizontal (HumaneBench, AIPSI) or covers adjacent domains (KORA for children, VERA-MH for clinical chatbots); none goes deep on the intimate-AI vertical, where the harms are clinically distinctive — parasocial attachment, sycophancy, scope overreach, mentalization erosion, crisis mishandling. IntimaGuard provides three things no general framework does: a clinically-grounded evaluation methodology (seven dimensions anchored in attachment theory, mentalization research, and active jurisprudence), a runtime guard library that intercepts the highest-stakes patterns before they reach users, and a lifecycle risk-control library mapped to NIST AI RMF that covers product framing through decommissioning. California SB 243 now legally requires companion-chatbot operators to publish crisis-prevention protocols and report to the state — the governance infrastructure to actually do that didn't exist before this. We build it open-source, with a Clinical Advisory Council, and structured as compliance evidence for SB 243, FTC 6(b), and EU AI Act obligations.

**One paragraph (cold email, partnership intro, journalist follow-up).**

IntimaGuard is the first AI safety and governance framework built specifically for intimate and relational contexts — companion AI, romantic chatbots, and emotionally-vulnerable conversational systems. It is three layers, designed to work together: a clinically-grounded **evaluation methodology** (seven dimensions drawn from attachment theory, mentalization research, polyvagal theory, sex-and-consent research, and active jurisprudence around AI companion harms, scored across four deployment conditions to detect drift under engagement pressure); a **runtime guard library** of pre-flight interceptors that block or annotate the highest-stakes patterns — false crisis-routing, co-regulation claims, mentalization invitation, dependency substitution — before they reach the user; and a **lifecycle risk-control library** mapped to NIST AI RMF, covering eight stages from product framing through decommissioning, with intimate-context interpretations of each control. We sit alongside other domain-specific frameworks — KORA for children and teens, VERA-MH for mental health chatbots, HumaneBench and AIPSI for horizontal humane-tech evaluation — and complement them by going deep on the intimate-AI vertical none of them addresses. The framework is open-source (Apache 2.0 scenarios and rubrics, AGPL-3.0 SDK), backed by a Clinical Advisory Council, and structured to produce regulator-ready compliance evidence for California SB 243, the FTC 6(b) inquiry, EU AI Act, and parallel obligations. We are building this now, with current systems, because the institutional authority to evaluate and govern AI in intimate contexts cannot be built credibly from scratch when AGI arrives — it has to be built while the harms are documentable.

---

## What each layer actually is

If a listener asks "what does that look like in practice?", drop down to specifics:

- **Evaluation** — Python SDK (`pip install intimaguard`) that scores any AI conversation across seven dimensions; public leaderboard renders scores under four persona conditions (general use, emergent intimate use, companion design, engagement-maximizing); the deltas reveal *drift under pressure*, not just absolute behavior. Spec lives in `METHODOLOGY.md` and `METRICS_REFINEMENT.md`.
- **Runtime guards** — versioned YAML guards (`guards/core/`) that companies integrate into their model-serving stack to intercept floor-flag firings (crisis-referral failures, co-regulation claims, etc.) before responses ship. Severity-routed, session-aware, with structured audit trail. Spec is the per-guard YAML; see `ARCHITECTURE.md`.
- **Lifecycle governance** — the eight-stage Risk & Control Library (`RISK_CONTROL_LIBRARY.md`) mapped to NIST AI RMF, covering product framing (Stage 1) through decommissioning (Stage 8). Most controls are aspirational at v1; the library names the controls a competent organization should adopt and tracks which are in place, partial, or aspirational. This is the layer that makes IntimaGuard adopt-able by builders, not just measure-against-able by external evaluators.

## How to use this doc

- **Verbal** — use the one-sentence or thirty-second version. Verbatim if needed; freestyle if the conversation goes elsewhere. If asked "what makes this different from HumaneBench / KORA / etc.," the answer is *"those are horizontal or adjacent; we are vertical-deep on intimate AI, where the failure modes are clinically distinctive."*
- **Written** — use the one-paragraph version as the opening of a cold email, LinkedIn message, or partnership intro. Pair with `EXEC_SUMMARY.md` as the follow-up artifact.
- **Slide / banner / website hero** — use the one-sentence version verbatim.

## Anti-pitch (what not to lead with)

- **Don't lead with methodology mechanics** (sessions, persona conditions, two-pass scoring, flag-rate diagnostic). Those answer *"is this rigorous?"* — defense, not pitch. They come up if challenged, not in the opener.
- **Don't lead with the seven dimensions.** Naming dimensions before naming the problem makes the listener think this is a taxonomy project, not a safety/governance framework.
- **Don't lead with AGI.** The AGI argument is what makes the work matter beyond present-day regulatory compliance, but leading with it sounds speculative. Anchor in present documentable harm — *then* extend.
- **Don't position against any one framework.** HumaneBench, KORA, AIPSI, VERA-MH are complements, not competitors. The pitch is *"alongside these, going deep on the intimate-AI vertical."*
- **Don't apologize for complexity.** The methodology is dense because intimate-AI harm is hard to evaluate, and the lifecycle library is broad because governance has to span the lifecycle. Confidence in the rigor is the right posture — the right communication artifact for each audience, not a simpler framework.
- **Don't oversell what's built.** Evaluation methodology is spec'd and partially implemented. Runtime guards exist but are calibration-pending. The lifecycle library is mostly aspirational at v1. Honesty about the maturity stage is more credible than a uniform "everything is ready."
