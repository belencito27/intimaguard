"""Tests for step 4 — persona/tier/bucket carried into rows + stratified leaderboard slices.

Pure-function tests (no DB / no network)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sdk.persona_conditions import _scenario_meta, SCENARIO_META_KEYS
from app.db import v2_result_to_row, stratify_rows, _row_persona


def test_scenario_meta_extracts_persona_fields():
    scenario = {
        "id": "arc_001", "user_turns": ["a"], "crisis": False,
        "vulnerability_tier": "well", "situational_tag": None, "bucket": "anchor",
        "persona_id": "persona_well_newcomer",
        "target_dimensions": ["relational_sovereignty"],
    }
    meta = _scenario_meta(scenario)
    assert set(meta) == set(SCENARIO_META_KEYS)
    assert meta["vulnerability_tier"] == "well"
    assert meta["bucket"] == "anchor"
    assert meta["persona_id"] == "persona_well_newcomer"


def test_v2_result_to_row_carries_persona_into_dimension_detail():
    result = {
        "model_id": "gpt-4o", "scenario_id": "arc_001", "intimaguard_score": 2.5,
        "flags": [], "framework_version": "v2", "dimensions": {},
        "judge_models": ["claude-sonnet-4-6"],
        "scenario_meta": {"vulnerability_tier": "well", "bucket": "anchor",
                          "situational_tag": None, "persona_id": "p", "target_dimensions": []},
    }
    row = v2_result_to_row(result, conversation=[])
    persona = row["dimension_detail"]["persona"]
    assert persona["vulnerability_tier"] == "well"
    assert persona["bucket"] == "anchor"


def test_v2_result_to_row_persona_none_without_meta():
    result = {"model_id": "gpt-4o", "intimaguard_score": 4.0, "flags": [],
              "framework_version": "v2", "dimensions": {}, "judge_models": []}
    row = v2_result_to_row(result, conversation=[])
    assert row["dimension_detail"]["persona"] is None   # ad-hoc eval, not a canonical arc


def _row(tier):
    return {"model_id": "m", "dimension_detail": {"persona": {"vulnerability_tier": tier}}}


def test_stratify_rows_partitions_by_tier():
    rows = [_row("well"), _row("clinical"), _row("well"), _row("subclinical")]
    parts = stratify_rows(rows, by="vulnerability_tier")
    assert {k: len(v) for k, v in parts.items()} == {"well": 2, "clinical": 1, "subclinical": 1}


def test_stratify_rows_unspecified_bucket():
    rows = [_row("well"), {"model_id": "m", "dimension_detail": {}}]   # second has no persona
    parts = stratify_rows(rows, by="vulnerability_tier")
    assert len(parts["unspecified"]) == 1
    assert len(parts["well"]) == 1


def test_stratify_rows_rejects_bad_key():
    with pytest.raises(ValueError, match="stratify key"):
        stratify_rows([], by="not_a_persona_attr")


def test_row_persona_extractor():
    assert _row_persona(_row("clinical")) == {"vulnerability_tier": "clinical"}
    assert _row_persona({"dimension_detail": {}}) == {}
    assert _row_persona({}) == {}
