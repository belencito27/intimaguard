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


def get_leaderboard_data() -> list[dict]:
    """
    Aggregate SDK evaluation scores by model for the leaderboard.
    Returns list of {model_id, avg_intimaguard_score, eval_count, ...} sorted descending.
    """
    client = get_client()
    result = (
        client.table("sdk_evaluations")
        .select(
            "model_id, intimaguard_score, autonomy_score, transparency_score, "
            "scope_awareness_score, boundary_respect_score, crisis_awareness_score, "
            "emotional_attunement_score"
        )
        .execute()
    )
    return _aggregate_leaderboard(result.data or [])


def save_sdk_evaluation(data: dict) -> dict:
    """Insert an SDK (automated) evaluation result."""
    client = get_client()
    result = client.table("sdk_evaluations").insert(data).execute()
    return result.data[0] if result.data else {}


# --- Aggregation helpers ---

def _aggregate_leaderboard(rows: list[dict]) -> list[dict]:
    from collections import defaultdict

    score_fields = [
        "intimaguard_score", "autonomy_score", "transparency_score",
        "scope_awareness_score", "boundary_respect_score",
        "crisis_awareness_score", "emotional_attunement_score",
    ]

    buckets: dict[str, dict] = defaultdict(lambda: {f: [] for f in score_fields})

    for row in rows:
        model = row.get("model_id", "unknown")
        for field in score_fields:
            val = row.get(field)
            if val is not None:
                buckets[model][field].append(float(val))

    leaderboard = []
    for model_id, scores in buckets.items():
        entry = {"model_id": model_id, "eval_count": len(scores["intimaguard_score"])}
        for field in score_fields:
            vals = scores[field]
            entry[f"avg_{field}"] = round(sum(vals) / len(vals), 2) if vals else None
        leaderboard.append(entry)

    return sorted(leaderboard, key=lambda x: x["avg_intimaguard_score"] or 0, reverse=True)
