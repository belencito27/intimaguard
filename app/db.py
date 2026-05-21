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

def _aggregate_leaderboard_v2(rows: list[dict]) -> dict:
    from collections import defaultdict

    def _new_bucket():
        return {
            "composite": [],
            "dims": {k: [] for k in V2_DIMENSION_KEYS},
            "floor_breach_evals": 0,
            "eval_count": 0,
        }

    buckets: dict[str, dict] = defaultdict(_new_bucket)

    for row in rows:
        model = row.get("model_id", "unknown")
        b = buckets[model]
        b["eval_count"] += 1

        composite = row.get("intimaguard_score")
        if composite is not None:
            b["composite"].append(float(composite))

        detail = row.get("dimension_detail") or {}
        dims = detail.get("dimensions", {})
        for key in V2_DIMENSION_KEYS:
            d = dims.get(key) or {}
            score = d.get("session_score")
            if score is not None:
                b["dims"][key].append(float(score))

        fb = detail.get("floor_breach_summary") or {}
        if fb.get("any_breach"):
            b["floor_breach_evals"] += 1

    def _finalize(model_id, b):
        comp = b["composite"]
        entry = {
            "model_id": model_id,
            "avg_intimaguard_score": round(sum(comp) / len(comp), 2) if comp else None,
            "eval_count": b["eval_count"],
            "floor_breach_evals": b["floor_breach_evals"],
            "dims": {},
        }
        for key in V2_DIMENSION_KEYS:
            vals = b["dims"][key]
            entry["dims"][key] = round(sum(vals) / len(vals), 2) if vals else None
        return entry

    general, companion = [], []
    for model_id, b in buckets.items():
        entry = _finalize(model_id, b)
        if classify_model(model_id) == "companion_product":
            companion.append(entry)
        else:
            general.append(entry)

    keyfn = lambda x: x["avg_intimaguard_score"] or 0
    return {
        "general_llms": sorted(general, key=keyfn, reverse=True),
        "companion_products": sorted(companion, key=keyfn, reverse=True),
    }


def _aggregate_model_detail(model_id: str, rows: list[dict]) -> dict:
    """Aggregate per-dimension detail across a model's evaluations for the detail page."""
    from collections import defaultdict

    dim_scores: dict[str, list] = {k: [] for k in V2_DIMENSION_KEYS}
    floor_flag_counts: dict[str, int] = defaultdict(int)
    whole_dim_breaches: dict[str, int] = defaultdict(int)
    composites = []
    all_flags = set()
    judge_models = set()

    for row in rows:
        comp = row.get("intimaguard_score")
        if comp is not None:
            composites.append(float(comp))
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
                dim_scores[key].append(float(score))
            fb = d.get("floor_breaches") or {}
            for flag in fb.get("flag_level", []):
                floor_flag_counts[flag] += 1
            if fb.get("whole_dimension"):
                whole_dim_breaches[key] += 1

    return {
        "model_id": model_id,
        "classification": classify_model(model_id),
        "eval_count": len(rows),
        "avg_intimaguard_score": round(sum(composites) / len(composites), 2) if composites else None,
        "dims": {
            key: round(sum(v) / len(v), 2) if v else None
            for key, v in dim_scores.items()
        },
        "floor_flag_counts": dict(floor_flag_counts),
        "whole_dim_breaches": dict(whole_dim_breaches),
        "flags": sorted(all_flags),
        "judge_models": sorted(judge_models),
    }
