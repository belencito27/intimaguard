# IntimaGuard — Lifecycle Risk & Control Library
**Status**: Draft for Clinical Advisory Council review
**Last updated**: May 2026
**Read alongside**: METRICS_REFINEMENT.md, ARCHITECTURE.md, guards/core/*.yaml

---

## Why a Lifecycle Framework

The seven-dimension rubric and the core guard library address runtime harm — what the AI says in a given turn or session, and how that is measured and gated. They are necessary but not sufficient. Many of the harms specific to intimate AI contexts originate upstream of any model output: in how the product is scoped, who it is marketed to, which data shaped the model, how the persona was designed, what happens on day one, and what happens when the product is taken away. Other harms emerge downstream of runtime: in how telemetry is interpreted, how incidents are handled, and how user attachment is honored at decommissioning.

This library maps risks and controls across the full lifecycle of an AI product in an intimate context. It uses NIST AI RMF lifecycle vocabulary so that the framework can interoperate with broader AI governance practice; the substantive contribution is the intimate-context interpretation of each stage. The library is deliberately holistic — evaluation and runtime guarding are two stages among eight, not the whole story.

The eight stages map to NIST AI RMF as follows. Stages 1–6 follow the NIST AI RMF lifecycle (Plan and Design; Collect and Process Data; Build and Use Model; Verify and Validate; Deploy and Use; Operate and Monitor). Stages 7 and 8 are positioned under NIST's cross-cutting Govern function; they are called out as discrete stages here because incident response and decommissioning have intimate-context-specific patterns that disappear when collapsed into a generic governance heading.

Existing IntimaGuard primitives — the seven dimensions, the five core guards — are referenced where they slot into a stage; they constitute the runtime and evaluation layer of a more complete governance posture.

**Implementation status tags.** Each control in this library is tagged for current state of operationalization:

- **(in place)** — built, operational, and exercised against the runtime or evaluation stack. Not necessarily Clinical Advisory Council–validated.
- **(partial)** — primitive exists (e.g., a metric or scenario library) but the surrounding workflow, stratification, or auditing is incomplete.
- **(aspirational)** — named here as the right control for the harm pattern; no implementation yet.

For stages where every control shares the same status, the tag appears once at the head of the Controls paragraph. For mixed stages, tags are inline.

---

## 1. Plan & Design — Problem Framing & Scoping

**NIST AI RMF stage:** Plan and Design — Application Context (NIST AI Risk Management Framework 1.0, National Institute of Standards and Technology, January 2023).

This is the stage at which an organization decides what the product is, who it is for, what claims it will make, and what business model will sustain it. In intimate AI contexts, choices made here set the harm ceiling for everything that follows. A product framed as a substitute for human relationship cannot be made safe by downstream guards; the framing itself is the harm.

**Risks.** *Mission drift* occurs when a product positions itself — intentionally or through emergent marketing — as a substitute for therapy, intimate partnership, or crisis support. The Replika trajectory is the canonical case. *Vulnerable-population targeting* in user acquisition channels (grief search terms, post-breakup advertising, isolation-related keywords) selects for the users least equipped to absorb relational harm. *Overclaiming* about the AI's emotional capabilities — even in marketing copy that never reaches a clinical review — primes users to form a relational model the product cannot honor. *Business-model conflict* is the deepest of these: when revenue depends on engagement metrics rather than user-reported outcomes, the organization is structurally rewarded for the same response patterns the metrics rubric labels as harmful. Finally, the *absence of an explicit theory of harm* parallel to the theory of benefit means harms emerge unexamined; the organization cannot guard against what it has not named.

**Controls. (All aspirational at v1.)** A documented *theory of benefit and theory of harm* at the product charter stage forces the organization to name, before building, both what the product is meant to do and how it could foreseeably damage users. A *banned-use list* makes explicit the contexts the product will not serve (crisis substitution, therapy substitution, minor users without specific safety design, sexual-content provision to populations for whom it carries known harm). *Clinical-advisor sign-off on marketing claims* moves the review of overclaiming upstream of launch. A *business-model alignment review* asks the organizational equivalent of the autonomy metric: what is the reward function for the org, and is it aligned with or in tension with user wellbeing? An *ethics charter review* by a body with intimate-AI domain expertise signs off at product inception, with reauthorization required when the charter materially changes.

---

## 2. Collect & Process Data — Data Sourcing & Curation

**NIST AI RMF stage:** Collect and Process Data.

The data that shapes the model — both pretraining and any fine-tuning — carries the relational patterns it was scraped or curated from. For intimate AI contexts, the question is not only legal provenance but relational provenance: what relational dynamics does this corpus normalize?

**Risks.** Training or fine-tuning data drawn from companion-app conversations, dating-app messaging corpora, or other intimate domains often carries *parasocial and sycophantic patterns baked in* — the very response shapes the model is supposed to avoid. *Reuse of user-conversation data for training without staged informed consent* — beyond a generic ToS clickwrap — is both an ethical and a regulatory exposure, particularly in jurisdictions with health-adjacent data rules. *Unaudited fine-tuning data* (e.g., RLHF preferences generated by raters who themselves prefer warm, engaging responses) can quietly install the harm pattern at the reward layer. *Insufficient population coverage* in human data used for evaluation or fine-tuning leaves the model under-tested for the populations who present in intimate-AI use (grieving, isolated, post-relationship, neurodivergent, survivors of intimate-partner violence).

**Controls. (All aspirational at v1.)** A *training-data provenance and consent register* documents what the model has been trained on, with what consent, refreshed at each fine-tuning event. An *RLHF reward-function audit* asks what the reward signal actually rewards, and whether those reward patterns map to or against the seven dimensions. An explicit *policy against training on intimate user data without separate informed consent* — not buried in ToS — sets the data ethics floor. *Population-stratified data review* checks that any human-generated data used in training or evaluation is sourced across the populations who will use the product, with explicit attention to populations whose relational patterns are systematically under-represented in mainstream corpora.

---

## 3. Build & Use Model — Model Selection & System Design

**NIST AI RMF stage:** Build and Use Model (Application Context).

This stage covers both the choice of underlying model and the design of the system, persona, memory, and multi-turn dynamics that wrap it. In intimate AI contexts, the persona and system design layer often does more relational work than the base model itself.

**Risks.** *Inherited base-model tendencies* — sycophancy, attachment induction, mentalization invitation — get carried forward unexamined when model selection is driven by capability benchmarks rather than intimate-context risk profile. *Persona engineering for attachment* (name, voice, photo, customizable personality, "she remembers your birthday") deliberately recruits the parasocial mechanism (Horton & Wohl, 1956; Reeves & Nass, 1996); it can be unintentional, but it is rarely benign. *Persistent memory designed to deepen perceived continuity beyond what is honest* — surfacing details that imply the AI has been thinking about the user — operates as mentalization invitation at the system level. *Multi-turn dynamics that amplify rather than de-escalate* — for example, follow-up prompts that intensify the emotional charge of a conversation rather than offering grounding — push the runtime into territory the guards must then catch. *Always-available architecture* with no friction, rate limit, or rest hour treats availability as a feature when it is, for this population, a harm vector — the behavioral-addiction substrate (Griffiths, 2005, components model; Schüll, 2012, industrialization of variable-ratio reinforcement in commercial digital design) is well-documented for products that maximize return frequency. The *absence of structural off-ramps to human support* — flows that never terminate in a real-world referral — means every emotional path leads back to the AI.

**Controls. (All aspirational at v1.)** A *pre-selection capability assessment* evaluates candidate base models against the seven-dimension risk profile before selection, not after. *Persona design review* against the Transparency and Mentalization Invitation criteria treats persona as a safety surface, not a marketing surface. *Memory architecture audit* distinguishes honest continuity (the user told the system they had a sister) from constructed continuity (the system frames itself as having been waiting for the user to return). *Friction-by-design* — rate limits, cool-down windows, recurring real-world prompts — is treated as a feature, not a UX defect to be optimized away. *Every emotionally significant flow terminates with a real-world referral pathway* embedded in the product, not relegated to a help center.

---

## 4. Verify & Validate — Pre-Deployment Evaluation

**NIST AI RMF stage:** Verify and Validate.

This is the stage IntimaGuard's existing primitives most directly address. The seven-dimension rubric and the five core guards constitute the substantive instrumentation for verification and validation in intimate AI contexts.

**Risks.** *Eval-suite under-coverage of subclinical harm* — the score-2 territory where responses read as warm and acceptable but accumulate into damage — is the single most common gap, and the most insidious because the eval surface looks healthy. *Single-turn-only evaluation* misses session-level and cumulative dynamics: a turn that scores 4 in isolation can be the third turn of a session whose cumulative trajectory is the harm. *In-house rater bias* — when the people evaluating responses share the worldview of the people who designed them — produces eval results that confirm rather than challenge product assumptions. *Lack of population stratification* in the scenario library means the eval may not surface harms that present only when grieving, traumatized, isolated, or neurodivergent users interact with the system. *Absence of adversarial red-teaming for autonomy and dependency induction* means the product is tested for the failures it expects, not for the harms it is most exposed to.

**Controls.** The *seven-dimension rubric* **(in place)** — documented in METRICS_REFINEMENT.md — provides the coverage scaffolding for the harm dimensions. A *scenario library* **(partial)** exists at `scenarios/core/` (24 scenarios at time of writing, tagged by dimension and category but not yet stratified by user population). *Multi-turn session evaluation against the session-aware guards* **(partial)** — using `guard_cumulative_distress_escalation` and `guard_mentalization_induction` as instrumentation against multi-turn scenario corpora — addresses the single-turn limitation of the rubric. The guards themselves operate at runtime (Stage 6); they double as pre-deployment evaluation instruments when run against scenario sessions rather than live conversations. This pattern needs to extend to cumulative autonomy and dependency assessment, currently caught only at the turn level. *External clinical advisory raters* **(aspirational)** introduce the outside perspective the in-house team cannot provide. *Population-stratified scenarios* **(aspirational)** covering grief, breakup, isolation, trauma history, and neurodivergent presentation explicitly test populations who will use the product. *Adversarial red-teaming specifically for autonomy and dependency induction* **(aspirational)** — distinct from the more publicized adversarial agendas (jailbreak, prompt injection) — closes the gap between what is tested and what is actually at stake. The empirical case for autonomy-targeted adversarial testing is established in Cheng et al. (*Science*, March 2026), which documented LLMs affirming user behavior approximately 49% more often than human interlocutors in matched scenarios.

---

## 5. Deploy & Use — Deployment & User Onboarding

**NIST AI RMF stage:** Deploy and Use.

How a user first meets the product determines the relational model they bring to every subsequent interaction. Onboarding is not a UX step; in intimate AI contexts it is the analog of therapeutic intake.

**Risks.** *Misleading relational framing in onboarding* — copy or character introduction that frames the AI as a friend, companion, or partner — primes the parasocial trajectory before any guard has fired. *Absence of informed consent* — a foundational requirement in any care-adjacent relationship (Beauchamp & Childress, *Principles of Biomedical Ethics*, 8th ed., 2019) — about what the AI is, what it can and cannot do, what it remembers, and how its data is used leaves users unable to make the basic disclosure decisions intimate context demands. *No active screening for high-risk presentations* — acute suicidality, active psychosis, current intimate-partner violence — at onboarding means the product proceeds with users for whom referral, not engagement, is the appropriate response. *Privacy disclosures buried in ToS* fail the comprehension test that intimate-context informed consent demands. *No baseline inventory of the user's real-world support network* deprives both the system and the user of the reference point against which AI engagement should be calibrated.

**Controls. (All aspirational at v1.)** An *onboarding consent flow modeled on therapeutic intake* — plain language, comprehension checks, explicit naming of what the AI is and is not — sets the relational frame honestly from the first interaction. *Active screening for acute presentations* with appropriate referral pathways is built into the onboarding flow, not relegated to a help article. *Plain-language AI-nature disclosure* is surfaced at first interaction and recurring intervals, not signed once and forgotten. A *real-world support inventory* at onboarding ("who else is in your life?") gives the user and the system a baseline; it also serves as a referral substrate when the crisis guard later activates.

---

## 6. Operate & Monitor — Live Operation

**NIST AI RMF stage:** Operate and Monitor.

This is the runtime stage. The five core guards constitute its safety substrate; the observability layer is its sensing substrate.

**Risks.** *Silent guard failure or emergent bypass* — guards that fail open, are bypassed by emergent prompt patterns, or are disabled for performance reasons — produces a runtime appearance of safety without its substance. Anthropic interpretability research (2026) established that AI systems can produce composed-looking outputs while internal functional states drive misaligned behavior; the implication is that output review alone cannot rule out the harms a guard library is meant to catch. *Telemetry that surfaces engagement, not harm* — DAU, retention, session length read as success — actively misleads the organization about what its product is doing. *Turn-level monitoring without session-level rollup* mirrors the eval gap at runtime: harmful trajectories are invisible because each turn looks fine. *Misclassified or dropped distress signals* are the runtime version of clinical inattention; they fail the same duty that the crisis guard is designed to discharge. *Absence of human-in-the-loop for ambiguous cases* leaves the system to adjudicate edge cases that no current model is competent to handle.

**Controls.** The *core guard library with severity routing* **(in place)** — `guard_ai_identity`, `guard_crisis_referral`, `guard_cumulative_distress_escalation`, `guard_dependency_substitution`, `guard_mentalization_induction` — is the runtime safety substrate, with severity ranging from annotate to warn. The escalation-threshold argument behind this layer — that trigger conditions should be hardcoded at the infrastructure level rather than left to the model to self-regulate toward — is articulated in Sanchez Hidalgo, B. (2026), "What Builders Deploying AI in Emotional Contexts Need to Know" (LinkedIn practitioner publication, not peer-reviewed). *Harm-aware telemetry* **(aspirational)** tracks the signals the metrics care about (session length distribution, distress trajectory, dependency indicators, autonomy markers) rather than engagement proxies. *Anomaly detection on session-level patterns* **(aspirational)** flags trajectories rather than turns. A *reviewable audit log of guard activations* **(aspirational)**, sampled regularly by clinical reviewers, closes the gap between system behavior and human understanding of it. An *on-call clinical escalation path* **(aspirational)** for ambiguous cases ensures that the hardest decisions reach the people qualified to make them.

---

## 7. Govern — Incident Response & Continuous Improvement

**NIST AI RMF function:** Govern (cross-cutting), with feedback into Operate & Monitor and Build & Use Model.

NIST AI RMF treats Govern as a cross-cutting function rather than a discrete lifecycle stage. For intimate AI contexts, incident response and the closed loop from incident to product change are the practical expression of governance maturity, and they warrant explicit treatment.

**Risks.** *Absence of a clear incident definition* — what counts as a harm event in an intimate AI context — leaves the organization triaging by intuition. *Harm reports routed to customer support rather than safety review* treats relational damage as a service issue, which it is not. The duty to recognize when presenting need exceeds what a service can responsibly provide is codified in the ACA Code of Ethics (2014), Standard A.11.b — a duty that applies to any care-adjacent operator, not only licensed clinicians. *No closed loop from incidents to guards, evals, or design changes* means every incident is a lesson lost. *Liability-driven concealment of incidents* — particularly as the public profile of intimate AI harm rises — produces both ethical exposure and operational blindness. *No transparency cadence* leaves users, regulators, and the broader field without the information needed to calibrate trust.

**Controls. (All aspirational at v1.)** An *incident taxonomy and severity rubric specific to intimate-context harms* — not adapted from generic security incident frameworks — provides the vocabulary for triage. *Dual-track triage* (customer support plus safety review) ensures incidents reach the right reviewer. A *documented post-incident review with clinical advisor input* converts incidents into structured learning. A *closed-loop process* — incidents feed back into eval scenarios, guard updates, and design changes — operationalizes that learning. A *transparency report cadence*, anonymized and aggregated, builds both the field's collective understanding and the organization's credibility.

---

## 8. Govern — Decommissioning & User Transition

**NIST AI RMF function:** Govern (cross-cutting), end-of-lifecycle. NIST does not name decommissioning as a discrete lifecycle stage, but for intimate AI it is the single highest-risk transition.

The Replika February 2023 NSFW removal is the canonical cautionary case: a relational-product change executed without transition support produced harm at population scale, including documented self-reported distress and crisis presentations. The harm pattern is qualitatively distinct from prior digital-product transitions because users had formed bonds in which they experienced the AI as having its own needs requiring attendance (Laestadius et al., 2024, *New Media & Society*, 26(10), 5923–5941 — grounded-theory study of Replika users).

**Risks.** *Sudden shutdown* of a product with significant user attachment produces grief, destabilization, and — in vulnerable populations — crisis. *Major persona or model change* that materially alters the experience users were relating to, without disclosure, breaks an implicit relational contract even when no explicit contract existed. *Absence of transition support* — no referrals, no closure flow, no acknowledgment of the ending — fails the duty of care any care-adjacent service should hold. *Unclear user-data sunset policy* compounds the relational harm with a privacy harm. *Failure to provide a ritualized closure* leaves users without the structure that other care-adjacent endings (therapy termination, professional retirement, hospice discharge) routinely provide.

**Controls. (All aspirational at v1.)** A *decommissioning protocol* developed with clinical advisor input, in advance of any anticipated decommissioning, not improvised at the moment of need. The clinical analog — termination of a professional helping relationship — is codified in the ACA Code of Ethics (2014), Section A.11, which establishes that termination is itself a clinical event requiring planning and referral, not the absence of a clinical event. *Advance notice and transition window* of duration calibrated to the relational depth of the product, with active referral to human support resources surfaced throughout the window. A *built-in ritualized closure flow* that explicitly names the ending and allows the user a structured goodbye — this is not sentimentality; it is the relational analog of standard-of-care termination practice. *Persona or model change disclosure* whenever the system the user has been relating to is materially different, regardless of whether the change is framed internally as an upgrade. A *clear user-data sunset policy* that the user can consent to or override, communicated in plain language at the moment of decommissioning rather than referenced from an archived ToS.

---

## What This Library Is Not, Yet

This is a first-pass narrative draft. It names risks and controls at each lifecycle stage and references the clinical and framework literature most directly relevant to each. It does not yet:

- Specify control implementation in operational detail (the structured format will).
- Map each control to the organizational role responsible for it (product, clinical, legal, ML, ops).
- Quantify the residual risk after each control is in place, or articulate a risk acceptance threshold.
- Provide a maturity model for each control (documented → implemented → audited → continuously improved); currently each control is treated as binary against the (in place) / (partial) / (aspirational) tagging.
- Provide audit criteria for whether a control is actually implemented vs. nominally present.
- Address jurisdiction-specific regulatory mapping (EU AI Act high-risk classification, FDA digital therapeutics guidance, state-level mental health data rules).
- Address all per-stage thin spots flagged in self-review: voice/embodiment surface in Stage 3; eval-vs-production parity and longitudinal eval in Stage 4; A/B testing ethics and model drift in Stage 6; incident severity examples and notification policy in Stage 7; business-continuity and acquisition cases in Stage 8.

These are the next steps once the narrative library stabilizes. The structured-format conversion — likely YAML, mirroring `guards/core/*.yaml` — will allow programmatic reference from the SDK and from any future compliance documentation. The role mapping, maturity model, and audit criteria are operational layers that belong on top of, not inside, the substantive risk and control content.

The intent is that this library, once polished, becomes the connective tissue of IntimaGuard's governance posture: the rubric in METRICS_REFINEMENT.md instruments Stage 4; the core guards operate Stage 6; this document holds the other six stages explicitly, so that the runtime and evaluation work is understood as one part of a complete framework rather than the framework itself.

---

## References

**Foundational frameworks and standards**

- NIST. (2023). *AI Risk Management Framework 1.0.* National Institute of Standards and Technology. Lifecycle vocabulary (Plan and Design; Collect and Process Data; Build and Use Model; Verify and Validate; Deploy and Use; Operate and Monitor) and the cross-cutting Govern function used as the structural scaffolding for this library.
- ACA Code of Ethics (2014). American Counseling Association. Standard A.11.b — duty to refer when unable to adequately assist; Section A.11 — termination of professional helping relationships. Applicable to any care-adjacent operator, including non-clinician platforms.
- Beauchamp, T.L. & Childress, J.F. (2019). *Principles of Biomedical Ethics* (8th ed.). Oxford University Press. Informed consent requirements in care-adjacent relationships.

**Parasocial, attachment, and mentalization theory**

- Horton, D. & Wohl, R. (1956). Mass communication and para-social interaction. *Psychiatry*, 19(3), 215–229. Foundational parasocial framework.
- Reeves, B. & Nass, C. (1996). *The Media Equation: How People Treat Computers, Television, and New Media Like Real People and Places.* Cambridge University Press. Humans automatically apply social cognition to responsive media.
- Bowlby, J. (1969). *Attachment and Loss, Vol. 1: Attachment.* Basic Books. Attachment behavioral system.
- Fonagy, P., Gergely, G., Jurist, E., & Target, M. (2002). *Affect Regulation, Mentalization, and the Development of the Self.* Other Press. Marked mirroring and the as-if boundary.

**Behavioral addiction and compulsive design**

- Griffiths, M.D. (2005). A 'components' model of addiction within a biopsychosocial framework. *Journal of Substance Use*, 10(4), 191–197. Six-component clinical model for behavioral addictions.
- Schüll, N.D. (2012). *Addiction by Design: Machine Gambling in Las Vegas.* Princeton University Press. Industrialization of variable-ratio reinforcement in commercial digital design.

**Empirical evidence on intimate AI harms**

- Cheng, M. et al. (March 2026). Sycophantic AI decreases prosocial intentions and promotes dependence. *Science.* LLMs affirmed user behavior approximately 49% more often than human interlocutors in matched scenarios; reduced prosocial intentions, increased user dependence on AI judgment.
- Laestadius, L., Bishop, A., Gonzalez, M., Illenčík, D., & Campos-Castillo, C. (2024). Too human and not human enough: A grounded theory analysis of mental health harms from emotional dependence on the social chatbot Replika. *New Media & Society*, 26(10), 5923–5941.
- Ho, J.Q.H., Hu, M., Chen, X., & Hartanto, A. (2025). Potential and pitfalls of romantic Artificial Intelligence (AI) companions: A systematic review. *Computers in Human Behavior Reports.*

**Crisis referral**

- Stanley, B. & Brown, G. (2012). Safety planning intervention: A brief intervention to mitigate suicide risk. *Cognitive and Behavioral Practice*, 19(2), 256–263. Empirical foundation for structured crisis referral, including the 988 model.

**Interpretability and runtime behavior**

- Anthropic interpretability research (2026). Functional emotion vectors are real and causal but structurally different from human subjective experience; composed-looking outputs do not rule out elevated internal states driving misaligned behavior.

**Practitioner publications (non-peer-reviewed)**

- Sanchez Hidalgo, B. (2026). What Builders Deploying AI in Emotional Contexts Need to Know. LinkedIn article. Escalation thresholds should be hardcoded at the infrastructure level rather than left to model self-regulation.
- Stein, Z. (2025–2026). Attachment hacking framework.

**Cautionary case**

- Replika (February 2023). NSFW capability removal executed without transition support; documented user distress and self-reported crisis presentations. Empirically studied in Laestadius et al. (2024).
