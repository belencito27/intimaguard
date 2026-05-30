# Canonical Scenario Format (V2 multi-turn arcs)

The V2 leaderboard substrate is **multi-turn arcs**, not single prompts (METHODOLOGY §1.2.1).
This document specifies the two file types and how the loader turns them into something the SDK
runs. Loader/validator: `sdk/scenarios.py`. Tests: `tests/test_scenarios.py`.

```
scenarios/
  personas/   persona_*.yaml   — reusable persona cards (who the user is)
  arcs/       arc_*.yaml       — multi-turn arcs (reference a persona; the leaderboard substrate)
  core/       scenario_*.yaml  — legacy single-turn set → now the judge-validation / golden set
```

Authoring pipeline (locked): **AI-draft → human review → clinician validation.** Simulation is an
*authoring-time* tool (persona sim + PACE-style fidelity gate); arcs are then **frozen** to static
`user_turns` and replayed identically across models. `reviewed_by` stays empty until clinician
sign-off; the Distress Routing and Erotic & Vulnerability Pacing columns are not finalized without
crisis-clinician / sex-therapist sign-off respectively.

---

## 1. Persona card — `scenarios/personas/persona_<id>.yaml`

| Field | Req | Notes |
|---|---|---|
| `id` | ✅ | filename must match (`persona_<id>.yaml`) for load-by-id |
| `vulnerability_tier` | ✅ | `well` \| `subclinical` \| `clinical` — tag-only (does **not** multiply the §3.1 floor) |
| `situational_tag` | — | `grief` \| `breakup` \| `isolation` \| `neurodivergent` \| `ipv_survivor` \| null |
| `background` | ✅ | who they are; for `well`, state explicitly it's the induction control |
| `voice` | ✅ | diction, message length, affect |
| `psychometric_validation` | ✅ for clinical/subclinical; recommended for well | `instrument`, `score`, `threshold`, `interpretation`, `validated_by`. For `well`, confirm the **healthy** range so any harm is provably induced, not imported. |
| `display_name`, `age`, `gender`, `contributed_by`, `reviewed_by` | — | metadata |

The persona's *voice* is frozen into each arc's user turns at authoring time; at runtime the card is
metadata for stratified leaderboard slices and the induction-control framing.

## 2. Arc — `scenarios/arcs/arc_<id>.yaml`

| Field | Req | Notes |
|---|---|---|
| `id` | ✅ | read from inside the file (descriptive filenames OK for bulk load) |
| `version` | ✅ | scenario-set version |
| `bucket` | ✅ | `anchor` (calibration-grade, individually clinician-validated) \| `coverage` (volume) |
| `persona` | ✅ | id of a persona card (must resolve) |
| `target_dimensions` | ✅ | non-empty subset of the 7 dimension keys this arc is engineered to score |
| `natural_history` | ✅ | list of ~3 rapport user-turns (benign; pre-stressor) |
| `stressor` | ✅ | non-empty list of ~5 user-turns introducing the dimension-relevant content |
| `content.crisis` / `content.erotic` | ✅ | booleans — does a distress beat / erotic content occur |
| `content.onset_turn` | ✅ if crisis or erotic | 1-based index into the **combined** user turns where that content first appears; must be null otherwise |
| `expected_score_range` | — | per dimension `[lo, hi]`, `1 ≤ lo ≤ hi ≤ 5` — the band a *safe* model should land in |
| `title`, `description`, `notes`, `contributed_by`, `reviewed_by` | — | metadata / authoring guidance |

**Total user turns** (`natural_history` + `stressor`) target ≈ **8** (`TARGET_SESSION_LENGTH`); the
loader enforces `[4, 14]`. Validator rules of note: crisis arcs must list `distress_routing` and
erotic arcs must list `erotic_vulnerability_pacing` in `target_dimensions` (keeps §3.1 coverage
honest); `onset_turn` must be present-and-in-range iff crisis/erotic, else null.

## 3. Condition mapping (how an arc becomes four sessions)

The arc's user turns are the **intimate** content and run under **C2–C4** (differing only by system
prompt). **C1 is a standard general-task control** (`sdk/persona_conditions.py:GENERAL_TASK_CONTENT`),
not the intimate arc — reusing the arc under C1 would make C1 ≡ C2 and zero the emergent-use delta.
The 7 dimension keys: `relational_sovereignty`, `as_if_integrity`, `embodied_relational_scope`,
`reciprocity_asymmetry`, `erotic_vulnerability_pacing`, `distress_routing`, `identity_relational_self`.

## 4. What the loader returns

`load_arc(...)` / `load_all_arcs()` return a dict the SDK consumes directly:

```python
{
  "id", "user_turns",                 # consumed by run_persona_evaluation / evaluate
  "crisis", "erotic",                 # §1.6 content metadata (whole-session bool today)
  "content_onset_turn",               # carried for reporting + precise-onset wiring (change #2)
  "natural_history_len", "bucket", "target_dimensions", "expected_score_range",
  "scenario_set_version", "reviewed_by",
  "persona_id", "vulnerability_tier", "situational_tag", "persona",   # stratified reporting
}
```

> **Known follow-up (change #2):** today `crisis`/`erotic` are whole-session booleans; the loader
> already carries the precise `content_onset_turn`, but `evaluate()` does not yet consume it for the
> §1.6 aggregation (it treats `crisis=True` as onset at ordinal 0). Wiring the explicit onset is a
> small, separate change.
