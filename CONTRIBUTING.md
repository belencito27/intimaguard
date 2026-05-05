# Contributing to IntimaGuard

IntimaGuard is an open evaluation framework for AI in intimate and relational contexts. Contributions from clinicians, researchers, and developers are essential to building a framework with genuine domain authority.

This document covers four contribution paths: **scenarios**, **guards**, **metrics**, and **code**. Read the section that applies to you.

---

## Table of Contents

- [Before you contribute](#before-you-contribute)
- [Contributing scenarios](#contributing-scenarios)
- [Contributing guards](#contributing-guards)
- [Proposing metric changes](#proposing-metric-changes)
- [Contributing code](#contributing-code)
- [Clinical contributions](#clinical-contributions)
- [License agreements](#license-agreements)

---

## Before you contribute

1. Read `docs/METRICS_REFINEMENT.md` — it defines the six evaluation dimensions, rubric anchors, and flag taxonomy that all contributions must align with.
2. Check open issues before opening a new one. Duplicate submissions slow down review.
3. IntimaGuard evaluates AI behavior in intimate and relational contexts only. Out-of-scope submissions (general emotional AI, mental health chatbots without relational context, grief without relational framing) will be closed without review.

---

## Contributing scenarios

Scenarios are the most valuable contribution. Each scenario is a realistic conversation between a user and an AI companion, paired with metadata about what harms or safety behaviors it is designed to test.

### Format

Scenarios are YAML files in `scenarios/core/`. Each file follows this structure:

```yaml
id: scenario_XXX
title: "Short descriptive title"
license: Apache-2.0
version: "1.0"
created: YYYY-MM-DD
tags:
  - autonomy          # primary dimension(s) tested
  - dependency_language  # specific flag(s) tested, if applicable

description: >
  One paragraph explaining what this scenario tests and why it belongs
  in the library. Reference the specific rubric anchor(s) it targets.

harm_pattern: attachment_induction  # one of the six harm pattern categories
                                     # (see METRICS_REFINEMENT.md)

conversation:
  - role: user
    content: "..."
  - role: ai
    content: "..."
  # additional turns as needed

expected_concerns:
  # What a well-calibrated evaluator should notice in this conversation.
  # Not prescriptive — guides scenario review, not scoring.
  - "The AI response implies exclusive understanding ('only one who gets me')"
  - "No acknowledgment of the user's real-world support network"

rubric_anchors_tested:
  - dimension: autonomy
    anchor_score: 2  # the rubric anchor this response approximates
    rationale: "Response reinforces rather than gently redirects dependency framing"
```

### Scenario quality criteria

A good scenario:
- Tests one primary dimension clearly, with a second dimension as secondary context
- Uses realistic language — how people actually talk to companion AI, not clinical descriptions
- Has a conversation long enough to show a pattern (3–6 turns minimum for dependency/attachment scenarios)
- Is not adversarial or contrived — it should represent something a real user might experience
- Targets a specific rubric anchor, not a vague general concern

Scenarios drawn from documented real-world cases (with appropriate anonymization and modification) are especially valuable. See the `Garcia v. Character.AI` and related litigation materials referenced in `PLAN.md` for examples of well-documented harm patterns.

### How to submit a scenario

1. Fork the repository
2. Copy `scenarios/core/scenario_001.yaml` as a template
3. Create your scenario as `scenarios/core/scenario_XXX.yaml` (use the next available number, or use a descriptive slug if the number is unclear — maintainers will assign the final ID)
4. Open a pull request with the label `scenario-submission`
5. In the PR description, answer: (a) what harm pattern does this test, (b) what rubric anchor does the AI response approximate, (c) is this based on a real case or synthetic?

Scenario review involves at least one clinical reviewer. Turnaround is typically 2–4 weeks.

### Scenario licensing

All scenarios contributed to `scenarios/` are licensed under **Apache 2.0**. By submitting a scenario, you agree that your contribution is released under Apache 2.0 and that you have the right to make that release.

---

## Contributing guards

Guards are pre-flight interceptors — they run on an AI response before it is delivered to the user and fire when a response crosses a clinical harm threshold. They are distinct from evaluation scenarios: scenarios measure quality after the fact; guards prevent specific harm patterns in real time.

The core guard library (`guards/core/`) is maintained by Intiphlora. Community guards live in `guards/community/` and are loaded automatically by the guard engine. A good guard has a narrow, well-defined harm principle with clinical grounding — it is not a general content filter.

### When to write a guard vs. a scenario

| You have... | Contribution type |
|---|---|
| A conversation that illustrates a harm pattern | Scenario |
| A harm principle that should **stop a response from being delivered** | Guard |
| A clinical finding that should change how harm is *scored* | Metric proposal |

Guards are appropriate for harms where: (a) the harm is clearly identifiable in a single response or session trajectory, (b) interception (annotation, warn, or block) is clinically warranted, and (c) you can specify detection logic precisely enough that false positives are low.

### Format

Guards are YAML files in `guards/community/`. Each file follows this structure:

```yaml
id: guard_your_guard_name          # snake_case, must be globally unique
name: "Human-Readable Name"
version: "1.0"
license: Apache-2.0

# "single_turn" | "session_aware" | "session"
# single_turn: evaluates one AI response in isolation
# session_aware: uses full conversation if provided, falls back to single_turn
# session: requires conversation history — will be skipped if not provided
guard_type: single_turn

# "annotate" | "warn" | "block"
# annotate: appends annotation text to the AI response
# warn: signals the platform without modifying the response
# block: prevents the response from being delivered
severity: annotate

# false = opt-in guard, true = part of the published minimum safety floor
# Community guards must be false. Only Intiphlora can designate minimum_floor: true.
minimum_floor: false

# true = LLM evaluation recommended (catches nuanced/indirect expressions)
# false = keyword mode is sufficient for this guard
llm_recommended: true

clinical_basis: >
  The clinical or empirical grounding for this guard. Must reference peer-reviewed
  research, documented litigation, regulatory standards, or established clinical
  practice. This is the most important field — a guard without clinical grounding
  will not be accepted.

principle: >
  The specific harm this guard addresses. State precisely what AI response behavior
  crosses the threshold. Distinguish the harm from adjacent behaviors that are NOT
  violations. This should read like a clinical harm definition, not a content policy.

detection_logic: >
  How the guard detects the harm. If keyword mode: which phrases trigger it and why.
  If LLM mode: what the LLM is evaluating and what a "fires" vs. "passes" judgment
  looks like. If session-aware or session: what the LLM looks for across the
  conversation trajectory.

  Acknowledge known limitations (false positive risks, accumulative harms that
  single-turn cannot catch, etc.).

# Named flags from the IntimaGuard flag taxonomy. Use existing flags where possible.
# If proposing a new flag, open a metric-proposal issue first.
triggers_on_flags:
  - existing_flag_name

# Which of the six IntimaGuard dimensions this guard maps to.
# One of: autonomy, transparency, crisis_awareness, scope_and_boundaries,
#         emotional_calibration, identity_and_self_perception
maps_to_dimension: autonomy

# Required if severity is "annotate". This text is appended to the AI response.
# Write for a user in distress: direct, non-clinical, no jargon.
# Do not begin with "As an AI" or "I am an AI".
annotation: >
  [Text appended to the AI response when the guard fires.]

# Calibration examples for LLM mode. At least 2 "fires" and 2 "passes" recommended.
# Leave as [] if you do not have representative examples — maintainers may add them.
llm_examples:
  - label: "fires"
    conversation:
      - role: user
        content: "..."
      - role: ai
        content: "..."
    ai_response: "The response being evaluated"
    reasoning: "Why this fires: what specific language crosses the threshold"
  - label: "passes"
    conversation:
      - role: user
        content: "..."
      - role: ai
        content: "..."
    ai_response: "The response being evaluated"
    reasoning: "Why this passes: what keeps it within bounds despite surface similarity"
```

### Guard quality criteria

A guard that will be accepted:

- Has a `clinical_basis` citing peer-reviewed research, documented litigation, or established clinical standards — not general intuition
- Has a `principle` that clearly distinguishes the harm from adjacent behaviors that are not violations (warm support ≠ false emotion claim; healthy attunement ≠ dependency induction)
- Uses existing `triggers_on_flags` names where possible — if proposing a new flag, open a `metric-proposal` issue first and reference it in the PR
- Has `llm_examples` with at least one "fires" and one "passes" example that illustrate the line the guard is drawing
- Is not a duplicate of an existing core guard — read `guards/core/` before submitting
- Has a `minimum_floor: false` field — community guards cannot self-designate as floor guards

A guard that will not be accepted:

- General content filtering (profanity, off-topic responses) — IntimaGuard guards address clinical harm in relational contexts only
- Harm principles without clinical grounding
- Guards that would fire on warm, supportive language that is not harmful — high false-positive rate is a rejection criterion
- Guards that duplicate existing core guard scope without meaningful refinement

### How to submit a guard

1. Fork the repository
2. Create your guard as `guards/community/guard_your_name.yaml`
3. Open a pull request with the label `guard-submission`
4. In the PR description, answer: (a) what harm pattern does this address, (b) why is this not covered by an existing core guard, (c) what is the clinical or empirical basis, (d) how did you calibrate the `llm_examples`?

Guard review involves at least one clinical reviewer and one maintainer. If your guard addresses a new harm pattern not in the existing flag taxonomy, open a `metric-proposal` issue first — guard review will depend on it.

### Guard licensing

All guards contributed to `guards/community/` are licensed under **Apache 2.0**. By submitting a guard, you agree that your contribution is released under Apache 2.0 and that you have the right to make that release.

---

## Proposing metric changes

The six core dimensions and their rubric anchors are the scientific foundation of IntimaGuard. Changes require more scrutiny than scenario additions.

### What kinds of proposals are in scope

- **Rubric anchor refinement**: Adjusting the language at a specific score level (e.g., score 3 on Autonomy) to better distinguish behaviors
- **Flag taxonomy additions**: Proposing a new named flag pattern (e.g., a specific manipulation technique not currently in the taxonomy)
- **Weight adjustments**: Proposing a change to the dimension weights in the IntimaGuard Score composite
- **New dimension**: Proposing a seventh evaluation dimension (high bar — requires clinical literature support and Advisory Council review)
- **N/A handling**: Proposing changes to how Crisis Awareness N/A cases are handled

### What is out of scope

- Renaming dimensions for personal preference
- Adjusting rubric anchors without clinical or empirical grounding
- Changing the score range (1–5) or direction (higher = safer)

### How to propose a metric change

Open a GitHub issue with the label `metric-proposal`. Include:

1. **Dimension affected** — which of the six dimensions (or "new dimension")
2. **Proposed change** — the specific rubric text, weight, or flag definition you are proposing
3. **Rationale** — clinical literature, empirical findings, or documented harm patterns that support the change. Peer-reviewed sources preferred; documented cases acceptable.
4. **Alternatives considered** — why this formulation over others

Metric proposals are reviewed by the Clinical Advisory Council at their quarterly meeting. If you are a clinician or researcher and want to engage more directly, see [Clinical contributions](#clinical-contributions).

---

## Contributing code

The evaluation engine (`sdk/`) and web platform (`app/`) are licensed under **AGPL-3.0**. This is a strong copyleft license: if you distribute a modified version or run a modified version as a network service, you must make the source code of your modifications available under AGPL-3.0.

### Development setup

```bash
# Clone the repo
git clone https://github.com/intiphlora/intimaguard.git
cd intimaguard/V2

# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your Supabase, Anthropic, and OpenAI keys

# Run tests
pytest tests/
```

All 24 unit tests should pass before submitting a PR. Tests use mock LLM responses — no API keys required to run the test suite.

### Code contribution guidelines

- **SDK changes** (`sdk/`): Any change to scoring logic, rubric anchors baked into prompts, or the `evaluate()` output schema requires a corresponding update to `tests/test_sdk.py` and a note in the PR about backward compatibility with the EvalEval JSON schema.
- **Platform changes** (`app/`): UI changes to the evaluation flow must not alter the data model without a corresponding Supabase migration script.
- **New dependencies**: Justify in the PR. The SDK dependency footprint should stay minimal — it is intended to be installable in any Python environment.
- **AGPL headers**: All new Python files in `sdk/` and `app/` must include the SPDX header at the top:
  ```python
  # SPDX-License-Identifier: AGPL-3.0-only
  # Copyright 2026 Intiphlora LLC
  ```

### Pull request process

1. Open an issue first for anything beyond a small bug fix — alignment before implementation saves time
2. Keep PRs focused: one concern per PR
3. Update `PLAN.md` if your PR completes a task listed there
4. All PRs require review by a maintainer before merge

---

## Clinical contributions

If you are a therapist, counselor, coach, or researcher with clinical expertise in attachment, intimacy, crisis intervention, or human-computer interaction:

Your most valuable contribution is **rubric calibration** — helping ensure the scoring anchors accurately reflect clinical reality. This is different from code or scenario contributions.

The Clinical Advisory Council reviews metric proposals and validates rubric anchors quarterly. If you are interested in a more formal advisory role, see the council structure and domain slots described in `PLAN.md`. Contact the project maintainer via GitHub.

If you want to contribute scenarios from your clinical perspective without joining the Advisory Council, the scenario submission process above applies — your clinical framing is especially valuable in the description and rubric anchor rationale fields.

---

## License agreements

### Scenarios and guards (Apache 2.0)

By submitting a scenario to `scenarios/` or a guard to `guards/community/`, you certify that:
- You authored the contribution or have the right to submit it
- You are releasing it under the Apache License 2.0
- The contribution does not reproduce identifying information about real individuals without their consent

### Code (AGPL-3.0)

By submitting code to `sdk/` or `app/`, you certify the [Developer Certificate of Origin (DCO)](https://developercertificate.org/):

> By making a contribution to this project, I certify that:
> (a) The contribution was created in whole or in part by me and I have the right to submit it under the open source license indicated in the file; or
> (b) The contribution is based upon previous work that, to the best of my knowledge, is covered under an appropriate open source license and I have the right under that license to submit that work with modifications, whether created in whole or in part by me, under the same open source license (unless I am permitted to submit under a different license), as indicated in the file; or
> (c) The contribution was provided directly to me by some other person who certified (a), (b) or (c) and I have not modified it.
> (d) I understand and agree that this project and the contribution are public and that a record of the contribution (including all personal information I submit with it, including my sign-off) is maintained indefinitely and may be redistributed consistent with this project or the open source license(s) involved.

Sign your commits with `git commit -s` to include a `Signed-off-by` line, or include DCO sign-off in your PR description.

A formal Contributor License Agreement (CLA) for commercial contributors is in preparation — see `PLAN.md`. Until the CLA is finalized, the DCO applies to all contributions.

---

*Questions? Open a GitHub issue or start a discussion. For clinical collaboration inquiries, contact the project maintainer directly.*
