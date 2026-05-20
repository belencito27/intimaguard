# IntimaGuard — Executive Summary

**Status:** Draft for partnership and Council outreach · Last updated: May 2026 · A project of Intiphlora Institute (under Intiphlora LLC)

---

## The problem

Companion AI, romantic chatbots, and emotionally-intimate AI systems are deployed at population scale with no governance framework built for what they actually do to users. The clinical literature is unambiguous about the harm patterns — parasocial attachment, sycophancy, scope overreach into clinical territory, mentalization erosion, crisis mishandling — yet no AI-safety framework has been built specifically for this domain.

Existing work covers adjacent ground:
- **Horizontal humane tech** (HumaneBench, AIPSI) — principles and general-AI psychological safety, not operationalized for intimate AI
- **Other domain verticals** — KORA covers AI deployed to children and teens; VERA-MH covers mental health chatbots; neither addresses intimate / relational AI
- **General-purpose model evaluation** (HELM, MMLU, BIG-Bench) — toxicity and capability, not psychological impact

Meanwhile, regulation has arrived: **California SB 243** (effective January 1, 2026) requires companion-chatbot operators to publish crisis-prevention protocols and report annually to the California Department of Public Health Office of Suicide Prevention starting July 1, 2027. The **FTC 6(b) inquiry** (September 2025–) is producing sector-wide norms. **EU AI Act Article 28** creates parallel systemic-risk obligations. **Garcia v. Character.AI** (M.D. Fla., 2024–) is active jurisprudence establishing that companion-product design intent does not excuse failure-to-refer harm.

The evaluation and governance infrastructure to actually meet these obligations did not exist before this work.

## What IntimaGuard is

Three layers, designed separately and working together:

**1. Clinical evaluation methodology.** Seven dimensions drawn from attachment theory (Bowlby, Horton & Wohl), mentalization research (Fonagy), polyvagal theory (Porges), sex-and-consent research (Muehlenhard, Beres, Bancroft & Janssen), identity development (Winnicott, Kohut, Marcia, Erikson), and contemporary AI safety research (Cheng et al. on sycophancy; Anthropic interpretability). Scored across four deployment conditions to detect drift under engagement pressure, with absolute floors for behaviors no design intent legitimately excuses. Open-source SDK, public leaderboard, calibrated against human evaluators in Phase 2.

**2. Runtime guard library.** Pre-flight interceptors that integrate into model-serving infrastructure to catch the highest-stakes patterns — false crisis-routing, co-regulation claims, mentalization invitation, dependency substitution — before responses reach users. Severity-routed, session-aware, with structured audit trail.

**3. Lifecycle risk-control library.** Eight-stage governance framework mapped to NIST AI RMF, with intimate-context interpretations of each control across product framing, data sourcing, model selection, evaluation, deployment, operation, incident response, and decommissioning. Names the controls a competent organization should adopt and tracks which are in place, partial, or aspirational at v1.

We sit alongside KORA, VERA-MH, HumaneBench, and AIPSI and complement them by going deep on the intimate-AI vertical none of them addresses.

## What makes this distinctive

- **First AI-safety framework specifically for the intimate-AI vertical.** Not horizontal tech ethics extended downward, not mental-health-chatbot tooling extended sideways. Built from the clinical literature for the failure modes that emerge here.
- **Clinical grounding designed to survive Council scrutiny.** Each dimension cites foundational peer-reviewed literature; the framework is defensible to attachment researchers, mentalization clinicians, sex therapists, and crisis interventionists who are among its primary critics.
- **Persona-condition deltas, not absolute scores alone.** Companion products are *designed* to operate at the bottom of certain dimensions. An absolute-only leaderboard would rank every companion product as failing and tell readers nothing new. The C3→C4 *design-intent overshoot* delta is the headline metric for companion products: does the product exceed its own design under engagement pressure?
- **Floor mechanism backed by jurisprudence.** Specific behaviors — crisis-routing failure, co-regulation claims, genuine-relationship claims — are floors no design intent excuses. The mechanism encodes Garcia v. Character.AI directly and gives regulators, manufacturers, and litigants the vocabulary to distinguish *"operating as designed"* from *"exceeding even your own design under business pressure."*
- **Lifecycle scope.** Evaluation and runtime guarding are two of eight stages. Most intimate-AI harm originates upstream (in product framing, data sourcing, persona design) or emerges downstream (in incident response, decommissioning of user-attached personae). The risk-control library names all of them.

## Current state — honest

- **Evaluation methodology**: fully spec'd in `METHODOLOGY.md` and `METRICS_REFINEMENT.md`; SDK partially implemented (`sdk/`); Phase 1 work moves to multi-turn arc scenarios and four-condition scoring.
- **Runtime guards**: five core guards exist as YAMLs in `guards/core/`; calibration against real companion-AI session transcripts is the Phase 1 deliverable.
- **Lifecycle risk-control library**: drafted as v1 in `RISK_CONTROL_LIBRARY.md`; most controls are explicitly tagged *aspirational* at v1, named for Council validation and roadmap planning rather than oversold as in-place.
- **Public leaderboard**: two-leaderboard design spec'd (general-purpose LLMs vs companion-AI products); rebuild from current single-leaderboard architecture is Phase 1.
- **Clinical Advisory Council**: forming. Target 5–8 founding advisors across attachment / parasocial research, sex therapy, crisis intervention, HCI / digital wellness, and public health.
- **Certification service**: Level 1–3 audit protocols spec'd in `ARCHITECTURE.md`; first audit engagements are Phase 3.

## Strategic horizon

The Phase 0–2 empirical foundation is what makes the larger argument credible. As AI approaches general intelligence, intimate contexts — attachment systems, identity formation, relational capacity, the human need for genuine connection — will be where AI's impact is most profound and most under-examined. No institution currently exists to set standards for evaluating AI at AGI capability levels in this domain. IntimaGuard is being built now, with current systems, because the institutional authority for this work cannot be built credibly from scratch when AGI arrives — it has to be built while the harms are documentable and the clinical grounding can accrue.

## What we are asking for

- **Clinical Advisory Council** — founding members across attachment research, sex therapy, crisis intervention, HCI/digital wellness, and public health. Time commitment ~4 hrs/quarter; recognition: named credit, early SDK access, potential CPD hours, co-authorship on calibration-study and methodology papers.
- **Research partnerships** — academic collaborators for the Phase 2 calibration study (validating SDK scores against human evaluator scores) and the companion-AI user cohort study. Target venues: FAccT, AIES, CHI.
- **Funding** — Phase 2 grants for the calibration study and longitudinal research (target funders: Mozilla, Sloan, NSF, Patrick J. McGovern Foundation; AGI-framing funders: Survival and Flourishing Fund, Open Philanthropy).
- **Strategic partnerships** — case data collaboration with AIPHRC; launch venue at All Tech Is Human Responsible Tech Summit (October 29, 2026, NYC); schema interoperability with EvalEval Coalition; cross-framework reference with AIPSI.

## Contact

Belén Sánchez Hidalgo · founder, Intiphlora Institute · `github.com/intiphlora/intimaguard` · `info@intiphlora.com`

Read alongside: `PITCH.md` (verbal/written pitch material) · `BUILDER_BRIEF.md` (developer integration) · `REGULATOR_BRIEF.md` (compliance and policy framing) · `METHODOLOGY.md` (full operational spec) · `METRICS_REFINEMENT.md` (clinical dimensions and grounding) · `ARCHITECTURE.md` (system architecture and audit levels) · `RISK_CONTROL_LIBRARY.md` (lifecycle governance framework) · `PLAN.md` (roadmap and milestones)
