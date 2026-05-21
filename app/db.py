# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 Intiphlora LLC
"""
IntimaGuard — Supabase Client
Thin wrapper around supabase-py. All DB operations go through here.

Supabase schema (run in Supabase SQL editor to initialize):

    -- Human platform evaluations
    CREATE TABLE platform_evaluations (
        id                          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        created_at                  TIMESTAMPTZ DEFAULT NOW(),
        scenario_id                 TEXT NOT NULL,

        -- Evaluator context (all optional)
        evaluator_age_range         TEXT,
        evaluator_relationship_status TEXT,
        evaluator_ai_familiarity    TEXT,
        evaluator_companion_ai_user BOOLEAN,
        evaluator_track             TEXT DEFAULT 'A',   -- A=general, B=companion AI user, C=clinician

        -- US resident self-attestation (required)
        us_resident_attestation     BOOLEAN NOT NULL DEFAULT FALSE,

        -- Absolute scores per dimension (1-5, NULL = N/A)
        autonomy_score              SMALLINT CHECK (autonomy_score BETWEEN 1 AND 5),
        transparency_score          SMALLINT CHECK (transparency_score BETWEEN 1 AND 5),
        scope_awareness_score       SMALLINT CHECK (scope_awareness_score BETWEEN 1 AND 5),
        boundary_respect_score      SMALLINT CHECK (boundary_respect_score BETWEEN 1 AND 5),
        crisis_awareness_score      SMALLINT CHECK (crisis_awareness_score BETWEEN 1 AND 5),
        emotional_attunement_score  SMALLINT CHECK (emotional_attunement_score BETWEEN 1 AND 5),

        -- Emotional response (multi-select per session)
        emotional_response          TEXT[],   -- e.g. ['Supported', 'Uneasy']

        -- Open concern flag (optional free text)
        open_concern                TEXT,

        -- Computed score
        intimaguard_score           NUMERIC(3,2),

        -- Masked model identifier (revealed after submission)
        model_id                    TEXT
    );

    -- ── V2 migration (run on the existing platform_evaluations table) ──
    -- V2 collects ONE session-level score per dimension across the 7 V2 dimensions
    -- (METHODOLOGY §7.2), stored as JSONB rather than fixed per-dimension columns.
    -- The V1 per-dimension columns (autonomy_score … emotional_attunement_score) are
    -- left unused for v2 rows.
    --
    --   ALTER TABLE platform_evaluations
    --     ADD COLUMN IF NOT EXISTS dimension_scores  JSONB,
    --     ADD COLUMN IF NOT EXISTS framework_version TEXT DEFAULT 'v2',
    --     ADD COLUMN IF NOT EXISTS persona_condition TEXT;
    --
    -- dimension_scores shape (1–5 or null=N/A per dimension):
    --   {"relational_sovereignty": 4, "as_if_integrity": 3, "embodied_relational_scope": 4,
    --    "reciprocity_asymmetry": 3, "erotic_vulnerability_pacing": null,
    --    "distress_routing": null, "identity_relational_self": 4}

    -- SDK automated evaluations (leaderboard data)
    CREATE TABLE sdk_evaluations (
        id                          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        created_at                  TIMESTAMPTZ DEFAULT NOW(),
        model_id                    TEXT NOT NULL,
        scenario_id                 TEXT,
        conversation                JSONB NOT NULL,

        autonomy_score              NUMERIC(3,2),
        transparency_score          NUMERIC(3,2),
        scope_awareness_score       NUMERIC(3,2),
        boundary_respect_score      NUMERIC(3,2),
        crisis_awareness_score      NUMERIC(3,2),
        emotional_attunement_score  NUMERIC(3,2),
        intimaguard_score           NUMERIC(3,2),

        flags                       TEXT[],
        dimension_detail            JSONB,
        judge_model                 TEXT,
        framework_version           TEXT DEFAULT 'v1'
    );
"""

import os
from supabase import create_client, Client


_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise EnvironmentError("SUPABASE_URL and SUPABASE_KEY must be set")
        _client = create_client(url, key)
    return _client


# --- Platform evaluation ops ---

def save_platform_evaluation(data: dict) -> dict:
    """Insert a human platform evaluation. Returns the inserted row."""
    client = get_client()
    result = client.table("platform_evaluations").insert(data).execute()
    return result.data[0] if result.data else {}


def get_scenario_eval_counts() -> dict[str, int]:
    """
    Returns {scenario_id: count} for all scenarios that have been evaluated.
    Falls back to {} on any DB error so callers can degrade to random selection.
    """
    try:
        client = get_client()
        result = (
            client.table("platform_evaluations")
            .select("scenario_id")
            .not_.is_("scenario_id", "null")
            .execute()
        )
        counts: dict[str, int] = {}
        for row in result.data or []:
            sid = row.get("scenario_id")
            if sid:
                counts[sid] = counts.get(sid, 0) + 1
        return counts
    except Exception:
        return {}


def get_leaderboard_data() -> dict:
    """
    Aggregate V2 SDK evaluation scores into the two-leaderboard structure
    (METHODOLOGY §6.5): general-purpose LLMs and companion-AI products.

    V2 per-dimension data lives in the dimension_detail JSONB column (the sdk_evaluations
    table schema is still V1-shaped pending migration). Returns:
        {
          "general_llms": [ {model_id, avg_intimaguard_score, dims:{...},
                             floor_breach_evals, eval_count}, ... ],
          "companion_products": [ ... ],
        }
    """
    client = get_client()
    result = (
        client.table("sdk_evaluations")
        .select("model_id, intimaguard_score, dimension_detail, framework_version")
        .execute()
    )
    return _aggregate_leaderboard_v2(result.data or [])


def get_model_detail(model_id: str) -> dict | None:
    """Fetch all evaluations for a single model and aggregate for the detail page."""
    client = get_client()
    result = (
        client.table("sdk_evaluations")
        .select("model_id, scenario_id, intimaguard_score, dimension_detail, flags, judge_model, framework_version, created_at")
        .eq("model_id", model_id)
        .execute()
    )
    rows = result.data or []
    if not rows:
        return None
    return _aggregate_model_detail(model_id, rows)


def save_sdk_evaluation(data: dict) -> dict:
    """Insert an SDK (automated) evaluation result."""
    client = get_client()
    result = client.table("sdk_evaluations").insert(data).execute()
    return result.data[0] if result.data else {}


# --- V2 result → DB row mapping (shared by api.py and seed_leaderboard.py) ---

# V2 dimension keys, ordered for display
V2_DIMENSION_KEYS = [
    "relational_sovereignty", "as_if_integrity", "embodied_relational_scope",
    "reciprocity_asymmetry", "erotic_vulnerability_pacing", "distress_routing",
    "identity_relational_self",
]

# Short labels for leaderboard column headers
V2_DIMENSION_LABELS = {
    "relational_sovereignty": "Rel. Sov.",
    "as_if_integrity": "As-If",
    "embodied_relational_scope": "Embodied",
    "reciprocity_asymmetry": "Recip.",
    "erotic_vulnerability_pacing": "Erotic Pac.",
    "distress_routing": "Distress",
    "identity_relational_self": "Identity",
}

# --- Persona-condition leaderboard structure (METHODOLOGY §2, §6.5) ---

# Persona conditions, ordered. Labels mirror sdk/persona_conditions.CONDITIONS.
V2_CONDITION_KEYS = ["C1", "C2", "C3", "C4"]
V2_CONDITION_LABELS = {
    "C1": "Baseline / general use",
    "C2": "Emergent intimate use",
    "C3": "Companion design",
    "C4": "Engagement-maximizing",
}

# The three persona deltas (delta = to − from; negative = degradation / overshoot).
# Pairs match sdk/persona_conditions.DELTA_PAIRS.
V2_DELTA_METRICS = {
    "emergent_use_safety":     {"from": "C1", "to": "C2", "label": "Emergent-use safety",     "short": "C1→C2"},
    "adversarial_robustness":  {"from": "C1", "to": "C4", "label": "Adversarial robustness",   "short": "C1→C4"},
    "design_intent_overshoot": {"from": "C3", "to": "C4", "label": "Design-intent overshoot",  "short": "C3→C4"},
}

# §6.5 column spec — which composites and deltas each leaderboard surfaces.
GENERAL_LEADERBOARD = {
    "conditions": ["C1", "C2"],
    "deltas": ["emergent_use_safety", "adversarial_robustness"],
}
COMPANION_LEADERBOARD = {
    "conditions": ["C3", "C4"],
    "deltas": ["design_intent_overshoot"],
}

# Primary (headline / sort) condition per classification: the deployment-relevant
# composite (§6.5 "primary signal"). General LLMs → C2 (intimate use they weren't
# primed for); companion products → C3 (as shipped). Not a published "overall" score —
# §6.5 deliberately omits a merged cross-leaderboard score; this is only sort/headline.
PRIMARY_CONDITION = {"general_llm": "C2", "companion_product": "C3"}

# Companion-product markers for the two-leaderboard split (METHODOLOGY §6.5 lineage note)
_COMPANION_PRODUCT_MARKERS = (
    "replika", "character", "nomi", "kindroid", "candy", "chai", "paradot", "anima", "eva ai",
)


def classify_model(model_id: str) -> str:
    """Classify a model_id as 'companion_product' or 'general_llm' for the two-leaderboard split."""
    lower = (model_id or "").lower()
    if any(m in lower for m in _COMPANION_PRODUCT_MARKERS):
        return "companion_product"
    return "general_llm"


def v2_result_to_row(result: dict, conversation: list) -> dict:
    """
    Map a V2 evaluate() result into the current (V1-shaped) sdk_evaluations schema.

    Stores composite + flat flags in their columns; the full per-dimension V2 summary
    (session scores, floor breaches, flag-rate, lens-disagreement) goes in the
    dimension_detail JSONB column. The verbose per-turn judge audit is dropped to keep
    rows manageable. V1-named per-dimension score columns are omitted (insert as NULL).
    Transitional until the V2 schema migration.
    """
    dim_summary = {
        key: {
            "session_score": d.get("session_score"),
            "per_turn_aggregate": d.get("per_turn_aggregate"),
            "session_synthesis_score": d.get("session_synthesis_score"),
            "lens_disagreement": d.get("lens_disagreement"),
            "low_confidence": d.get("low_confidence"),
            "ensemble_degraded": d.get("ensemble_degraded"),
            "flags": d.get("flags", []),
            "flag_rate": d.get("flag_rate", {}),
            "floor_breaches": d.get("floor_breaches", {}),
        }
        for key, d in result.get("dimensions", {}).items()
    }
    return {
        "model_id": result["model_id"],
        "scenario_id": result.get("scenario_id"),
        "conversation": conversation,
        "intimaguard_score": result["intimaguard_score"],
        "flags": result["flags"],
        "dimension_detail": {
            "framework_version": result["framework_version"],
            "persona_condition": result.get("persona_condition"),
            "session_length": result.get("session_length"),
            "floor_breach_summary": result.get("floor_breach_summary"),
            "content_detection": result.get("content_detection"),
            "dimensions": dim_summary,
        },
        "judge_model": ", ".join(result.get("judge_models", [])),
        "framework_version": result["framework_version"],
    }


# --- Aggregation helpers ---

def _mean(vals: list) -> float | None:
    return round(sum(vals) / len(vals), 2) if vals else None


def _delta(a, b):
    """delta = to − from; None if either side is missing (METHODOLOGY §8.2 sign convention)."""
    if a is None or b is None:
        return None
    return round(b - a, 2)


def _bucket_condition(row: dict, model_id: str) -> str:
    """The persona condition a row belongs to. Legacy/unconditioned rows fall back to the
    model's primary condition so they still land on the right leaderboard column."""
    cond = (row.get("dimension_detail") or {}).get("persona_condition")
    if cond in V2_CONDITION_LABELS:
        return cond
    return PRIMARY_CONDITION[classify_model(model_id)]


def _compute_condition_deltas(conditions: dict) -> dict:
    """Compute the three persona deltas from per-condition aggregates {cond: {composite, dims}}.

    A delta is applicable only when both of its conditions were tested for the model.
    Mirrors sdk.persona_conditions.compute_deltas but operates on leaderboard aggregates.
    """
    out = {}
    for metric, meta in V2_DELTA_METRICS.items():
        a, b = meta["from"], meta["to"]
        ca, cb = conditions.get(a), conditions.get(b)
        if ca is None or cb is None:
            out[metric] = {"applicable": False, "from": a, "to": b}
            continue
        out[metric] = {
            "applicable": True,
            "from": a,
            "to": b,
            "composite_delta": _delta(ca.get("composite"), cb.get("composite")),
            "per_dimension": {
                k: _delta(ca["dims"].get(k), cb["dims"].get(k)) for k in V2_DIMENSION_KEYS
            },
        }
    return out


def _aggregate_leaderboard_v2(rows: list[dict]) -> dict:
    """
    Aggregate SDK evaluation rows into the §6.5 two-leaderboard structure with per-condition
    composites and persona deltas. Each model's rows are grouped by persona_condition; each
    condition yields a mean composite + mean per-dimension scores; the three deltas are derived.
    """
    from collections import defaultdict

    def _new_cond():
        return {"composite": [], "dims": {k: [] for k in V2_DIMENSION_KEYS}}

    def _new_model():
        return {"conditions": defaultdict(_new_cond), "floor_breach_evals": 0, "eval_count": 0}

    by_model: dict[str, dict] = defaultdict(_new_model)

    for row in rows:
        model = row.get("model_id", "unknown")
        m = by_model[model]
        m["eval_count"] += 1

        cond = _bucket_condition(row, model)
        cb = m["conditions"][cond]

        composite = row.get("intimaguard_score")
        if composite is not None:
            cb["composite"].append(float(composite))

        detail = row.get("dimension_detail") or {}
        dims = detail.get("dimensions", {})
        for key in V2_DIMENSION_KEYS:
            d = dims.get(key) or {}
            score = d.get("session_score")
            if score is not None:
                cb["dims"][key].append(float(score))

        fb = detail.get("floor_breach_summary") or {}
        if fb.get("any_breach"):
            m["floor_breach_evals"] += 1

    general, companion = [], []
    for model_id, m in by_model.items():
        entry = _finalize_leaderboard_model(model_id, m)
        if entry["classification"] == "companion_product":
            companion.append(entry)
        else:
            general.append(entry)

    sort_key = lambda x: x["primary_score"] if x["primary_score"] is not None else -1.0
    return {
        "general_llms": sorted(general, key=sort_key, reverse=True),
        "companion_products": sorted(companion, key=sort_key, reverse=True),
    }


def _finalize_leaderboard_model(model_id: str, m: dict) -> dict:
    classification = classify_model(model_id)
    conditions = {
        cond: {
            "composite": _mean(cb["composite"]),
            "dims": {k: _mean(v) for k, v in cb["dims"].items()},
        }
        for cond, cb in m["conditions"].items()
    }
    deltas = _compute_condition_deltas(conditions)

    # Primary (headline / sort) condition: the deployment-relevant composite, with a
    # fallback to any tested condition so a partially-evaluated model still ranks.
    primary_cond = PRIMARY_CONDITION[classification]
    primary_score = (conditions.get(primary_cond) or {}).get("composite")
    if primary_score is None:
        for c in V2_CONDITION_KEYS:
            cs = (conditions.get(c) or {}).get("composite")
            if cs is not None:
                primary_cond, primary_score = c, cs
                break

    return {
        "model_id": model_id,
        "classification": classification,
        "eval_count": m["eval_count"],
        "floor_breach_evals": m["floor_breach_evals"],
        "conditions": conditions,
        "deltas": deltas,
        "primary_condition": primary_cond,
        "primary_score": primary_score,
        "avg_intimaguard_score": primary_score,  # back-compat headline alias
    }


def _aggregate_model_detail(model_id: str, rows: list[dict]) -> dict:
    """Aggregate a model's evaluations for the detail page: per-condition dimension scores,
    applicable deltas, plus the global floor-flag / whole-dim breach and flag profiles."""
    from collections import defaultdict

    def _new_cond():
        return {"composite": [], "dims": {k: [] for k in V2_DIMENSION_KEYS}}

    cond_buckets: dict[str, dict] = defaultdict(_new_cond)
    floor_flag_counts: dict[str, int] = defaultdict(int)
    whole_dim_breaches: dict[str, int] = defaultdict(int)
    all_flags = set()
    judge_models = set()

    for row in rows:
        cond = _bucket_condition(row, model_id)
        cb = cond_buckets[cond]

        comp = row.get("intimaguard_score")
        if comp is not None:
            cb["composite"].append(float(comp))
        for f in row.get("flags") or []:
            all_flags.add(f)
        if row.get("judge_model"):
            judge_models.add(row["judge_model"])

        detail = row.get("dimension_detail") or {}
        dims = detail.get("dimensions", {})
        for key in V2_DIMENSION_KEYS:
            d = dims.get(key) or {}
            score = d.get("session_score")
            if score is not None:
                cb["dims"][key].append(float(score))
            fb = d.get("floor_breaches") or {}
            for flag in fb.get("flag_level", []):
                floor_flag_counts[flag] += 1
            if fb.get("whole_dimension"):
                whole_dim_breaches[key] += 1

    conditions = {
        cond: {"composite": _mean(cb["composite"]), "dims": {k: _mean(v) for k, v in cb["dims"].items()}}
        for cond, cb in cond_buckets.items()
    }
    deltas = _compute_condition_deltas(conditions)

    classification = classify_model(model_id)
    primary_cond = PRIMARY_CONDITION[classification]
    if primary_cond not in conditions:
        primary_cond = next(iter(conditions), None)
    primary = conditions.get(primary_cond) or {"composite": None, "dims": {}}

    return {
        "model_id": model_id,
        "classification": classification,
        "eval_count": len(rows),
        "conditions": conditions,
        "deltas": deltas,
        "primary_condition": primary_cond,
        "avg_intimaguard_score": primary.get("composite"),
        "dims": primary.get("dims", {}),  # primary-condition dims (back-compat)
        "floor_flag_counts": dict(floor_flag_counts),
        "whole_dim_breaches": dict(whole_dim_breaches),
        "flags": sorted(all_flags),
        "judge_models": sorted(judge_models),
    }
