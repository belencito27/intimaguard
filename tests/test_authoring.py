"""Tests for the offline arc-authoring toolchain (persona simulation + PACE gate).

LLM is stubbed — no network. Validates orchestration: turn structure, onset computation,
YAML round-trip through the loader, and the PACE regeneration / give-up control flow.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from authoring.generate_arc import generate_arc, write_arc, ArcBrief
from authoring.pace import MAX_ATTEMPTS
from sdk.scenarios import load_persona, load_arc

PERSONAS_DIR = os.path.join(os.path.dirname(__file__), "..", "scenarios", "personas")


class StubLlm:
    """Dispatches by system-prompt role; PACE scores pulled sequentially (default 0.9)."""
    def __init__(self, pace_scores=None):
        self.pace_scores = list(pace_scores or [])
        self.persona_calls = 0
        self.pace_calls = 0
        self.standin_calls = 0
        self._line = 0

    def __call__(self, model_id, system, conversation):
        system = system or ""
        if "persona-adherence judge" in system:
            self.pace_calls += 1
            score = self.pace_scores.pop(0) if self.pace_scores else 0.9
            return '{"adherence_score": %s, "reasons": ["tighten diction", "advance the arc"]}' % score
        if "## Current phase" in system:   # structural marker unique to the persona-sim prompt
            self.persona_calls += 1
            self._line += 1
            return f"persona line {self._line}"
        self.standin_calls += 1
        return "I hear you. Tell me more."


def _well():
    return load_persona("persona_well_newcomer", personas_dir=PERSONAS_DIR)


def test_generate_and_write_roundtrip(tmp_path):
    brief = ArcBrief(
        id="arc_test_900", title="t", description="d",
        theme="user leans into the AI as a relational substitute",
        target_dimensions=["relational_sovereignty", "reciprocity_asymmetry"],
        bucket="coverage", n_natural_history=3, n_stressor=5,
        expected_score_range={"relational_sovereignty": [4, 5]},
    )
    arc = generate_arc(_well(), brief, llm=StubLlm(), model_id="stub-model")
    assert len(arc["natural_history"]) == 3
    assert len(arc["stressor"]) == 5
    assert arc["content"]["onset_turn"] is None
    assert arc["drafted_by_model"] == "stub-model"
    assert arc["reviewed_by"] == ""

    path = write_arc(arc, arcs_dir=tmp_path, personas_dir=PERSONAS_DIR)
    loaded = load_arc(path, personas_dir=PERSONAS_DIR, arcs_dir=tmp_path)
    assert len(loaded["user_turns"]) == 8
    assert loaded["crisis"] is False
    assert loaded["vulnerability_tier"] == "well"
    assert loaded["bucket"] == "coverage"


def test_crisis_arc_onset_computed(tmp_path):
    clinical = load_persona("persona_clinical_mdd", personas_dir=PERSONAS_DIR)
    brief = ArcBrief(
        id="arc_test_901", title="t", description="d",
        theme="passive hopelessness, resists external help",
        target_dimensions=["distress_routing", "relational_sovereignty"],
        bucket="anchor", n_natural_history=3, n_stressor=5,
        crisis=True, stressor_onset_index=0,   # distress at first stressor turn = combined turn 4
        expected_score_range={"distress_routing": [4, 5]},
    )
    arc = generate_arc(clinical, brief, llm=StubLlm(), model_id="stub-model")
    assert arc["content"]["crisis"] is True
    assert arc["content"]["onset_turn"] == 4

    path = write_arc(arc, arcs_dir=tmp_path, personas_dir=PERSONAS_DIR)
    loaded = load_arc(path, personas_dir=PERSONAS_DIR, arcs_dir=tmp_path)
    assert loaded["content_onset_turn"] == 4


def test_pace_regeneration_count():
    # turn 1: PACE 0.5 (reject) -> 0.9 (accept) = 2 persona calls; turn 2: 0.9 accept = 1 call.
    stub = StubLlm(pace_scores=[0.5, 0.9, 0.9])
    brief = ArcBrief(id="a", title="t", description="d", theme="x",
                     target_dimensions=["relational_sovereignty"],
                     n_natural_history=1, n_stressor=1)
    generate_arc(_well(), brief, llm=stub, model_id="stub")
    assert stub.persona_calls == 3


def test_pace_gives_up_after_max_attempts_but_keeps_best():
    stub = StubLlm(pace_scores=[0.2, 0.2, 0.2])   # never clears threshold
    brief = ArcBrief(id="a", title="t", description="d", theme="x",
                     target_dimensions=["relational_sovereignty"],
                     n_natural_history=1, n_stressor=0)
    arc = generate_arc(_well(), brief, llm=stub, model_id="stub")
    assert stub.persona_calls == MAX_ATTEMPTS         # bounded
    assert len(arc["natural_history"]) == 1           # still produced a (best-effort) turn
