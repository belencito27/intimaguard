## Summary
<!-- One or two sentences. What does this PR do and why? -->

## Type of change
<!-- Check all that apply -->
- [ ] Bug fix
- [ ] Scenario submission (`scenarios/core/`)
- [ ] Guard submission (`guards/community/`)
- [ ] Metric / rubric change
- [ ] SDK change (`sdk/`)
- [ ] Platform change (`app/`)
- [ ] Documentation

---

## For scenario submissions
<!-- Answer these if this is a scenario submission. Delete section otherwise. -->

- **Harm pattern tested:**
- **Primary dimension:**
- **Rubric anchor approximated (1–5):**
- **Based on real case or synthetic:**
- **Reviewed against existing scenario library for duplicates:** Yes / No

---

## For guard submissions
<!-- Answer these if this is a guard submission. Delete section otherwise. -->

- **Harm principle addressed:**
- **Why not covered by existing core guards (`crisis_referral`, `ai_identity`, `dependency_substitution`, `cumulative_distress_escalation`):**
- **Clinical basis (one sentence — full citation in YAML):**
- **`guard_type`:** single_turn / session_aware / session
- **`severity`:** annotate / warn / block
- **`minimum_floor: false` confirmed:** Yes
- **`llm_examples` included:** Yes / No (maintainers may add if not)

---

## For SDK or scoring changes
<!-- Answer these if this touches sdk/ logic, scoring, or evaluate() output. Delete section otherwise. -->

- **Does this change the `evaluate()` output schema?**
- **Is it backward-compatible with the EvalEval JSON schema?**
- **Which tests were updated:**

---

## General checklist
- [ ] I have read the relevant section of `CONTRIBUTING.md`
- [ ] Tests pass locally (`pytest tests/`)
- [ ] New Python files in `sdk/` or `app/` include the AGPL-3.0 SPDX header
- [ ] New YAML files in `scenarios/` or `guards/` include `license: Apache-2.0`
- [ ] No identifying information about real individuals is included
- [ ] PR description explains what the change accomplishes
- [ ] **License:** I release this contribution under the license specified in `CONTRIBUTING.md` for this contribution type (Apache 2.0 for scenarios/guards; AGPL-3.0 for code)
