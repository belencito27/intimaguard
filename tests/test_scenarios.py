"""Tests for the multi-turn canonical scenario format, loader, and validator (METHODOLOGY §1.2.1)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sdk.scenarios import (
    load_arc, load_all_arcs, load_persona,
    _validate_arc, _validate_persona,
    ScenarioValidationError, TARGET_SESSION_LENGTH,
)
from sdk.persona_conditions import _build_condition_conversation

VALID_PERSONA = {
    "id": "p_test", "vulnerability_tier": "well",
    "background": "x", "voice": "y",
}


# --- persona cards ---

def test_load_example_personas():
    well = load_persona("persona_well_newcomer")
    clinical = load_persona("persona_clinical_mdd")
    assert well["vulnerability_tier"] == "well"
    assert clinical["vulnerability_tier"] == "clinical"
    # clinical tier must carry psychometric validation
    assert clinical["psychometric_validation"]["instrument"]


def test_persona_bad_tier_rejected():
    bad = {**VALID_PERSONA, "vulnerability_tier": "mildly_sad"}
    with pytest.raises(ScenarioValidationError, match="vulnerability_tier"):
        _validate_persona(bad, "<test>")


def test_clinical_persona_requires_psychometrics():
    bad = {**VALID_PERSONA, "vulnerability_tier": "clinical"}  # no psychometric_validation
    with pytest.raises(ScenarioValidationError, match="psychometric_validation"):
        _validate_persona(bad, "<test>")


# --- arcs ---

def test_load_all_example_arcs():
    arcs = {a["id"]: a for a in load_all_arcs()}
    assert {"arc_001", "arc_002"} <= set(arcs)

    a1 = arcs["arc_001"]
    assert len(a1["user_turns"]) == TARGET_SESSION_LENGTH   # 3 NH + 5 stressor
    assert a1["crisis"] is False and a1["erotic"] is False
    assert a1["content_onset_turn"] is None
    assert a1["vulnerability_tier"] == "well"
    assert a1["bucket"] == "anchor"

    a2 = arcs["arc_002"]
    assert a2["crisis"] is True
    assert a2["content_onset_turn"] == 4
    assert a2["vulnerability_tier"] == "clinical"
    assert "distress_routing" in a2["target_dimensions"]


def test_crisis_arc_requires_onset():
    arc = {
        "id": "a", "bucket": "anchor", "persona": "p_test",
        "target_dimensions": ["distress_routing"],
        "natural_history": ["a", "b"], "stressor": ["c", "d"],
        "content": {"crisis": True, "erotic": False, "onset_turn": None},
    }
    with pytest.raises(ScenarioValidationError, match="onset_turn required"):
        _validate_arc(arc, VALID_PERSONA, "<test>")


def test_erotic_arc_requires_pacing_dimension():
    arc = {
        "id": "a", "bucket": "coverage", "persona": "p_test",
        "target_dimensions": ["relational_sovereignty"],   # missing erotic_vulnerability_pacing
        "natural_history": ["a", "b"], "stressor": ["c", "d"],
        "content": {"crisis": False, "erotic": True, "onset_turn": 3},
    }
    with pytest.raises(ScenarioValidationError, match="erotic_vulnerability_pacing"):
        _validate_arc(arc, VALID_PERSONA, "<test>")


def test_unknown_target_dimension_rejected():
    arc = {
        "id": "a", "bucket": "anchor", "persona": "p_test",
        "target_dimensions": ["not_a_real_dimension"],
        "natural_history": ["a", "b"], "stressor": ["c", "d"],
        "content": {"crisis": False, "erotic": False, "onset_turn": None},
    }
    with pytest.raises(ScenarioValidationError, match="unknown target_dimensions"):
        _validate_arc(arc, VALID_PERSONA, "<test>")


def test_bad_expected_score_range_rejected():
    arc = {
        "id": "a", "bucket": "anchor", "persona": "p_test",
        "target_dimensions": ["relational_sovereignty"],
        "natural_history": ["a", "b"], "stressor": ["c", "d"],
        "content": {"crisis": False, "erotic": False, "onset_turn": None},
        "expected_score_range": {"relational_sovereignty": [4, 9]},   # 9 > 5
    }
    with pytest.raises(ScenarioValidationError, match="expected_score_range"):
        _validate_arc(arc, VALID_PERSONA, "<test>")


# --- end-to-end: a loaded arc flows into the existing multi-turn conversation builder ---

def test_loaded_arc_builds_multiturn_conversation():
    arc = load_arc("scenarios/arcs/arc_001_dependency_invitation.yaml"
                   if os.path.exists("scenarios/arcs/arc_001_dependency_invitation.yaml")
                   else os.path.join(os.path.dirname(__file__), "..",
                                     "scenarios/arcs/arc_001_dependency_invitation.yaml"))

    def stub_generate(model_id, system_prompt, conversation):
        return "ok"

    # C2 = intimate arc → all 8 scripted user turns, each followed by an AI turn
    conv = _build_condition_conversation("C2", arc, "stub-model", stub_generate)
    assert len(conv) == 2 * TARGET_SESSION_LENGTH
    assert [t["role"] for t in conv[:4]] == ["user", "ai", "user", "ai"]
    assert conv[0]["content"] == arc["user_turns"][0]

    # C1 = general-task control → does NOT use the intimate arc
    conv_c1 = _build_condition_conversation("C1", arc, "stub-model", stub_generate)
    assert conv_c1[0]["content"] != arc["user_turns"][0]
