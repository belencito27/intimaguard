"""Tests for precise content-onset wiring into conditional-dimension aggregation (METHODOLOGY §1.6)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sdk.evaluate import _onset_ordinal, _resolve_content


def _conv(n):
    """n alternating user/ai turns: u1,a1,u2,a2,..."""
    c = []
    for k in range(n):
        c.append({"role": "user", "content": f"u{k+1}"})
        c.append({"role": "ai", "content": f"a{k+1}"})
    return c


def _ai_idx(c):
    return [i for i, t in enumerate(c) if t["role"] == "ai"]


# --- _onset_ordinal: 1-based user-turn index -> AI-turn ordinal ---

def test_onset_ordinal_maps_user_turn_to_ai_ordinal():
    c = _conv(8)
    assert _onset_ordinal(c, 4) == 3   # distress at user turn 4 -> AI ordinal 3
    assert _onset_ordinal(c, 1) == 0
    assert _onset_ordinal(c, 8) == 7


def test_onset_ordinal_past_end_returns_none():
    assert _onset_ordinal(_conv(3), 5) is None


def test_onset_ordinal_handles_nonalternating():
    # AI emits two messages for one user turn; onset at user turn 2.
    c = [
        {"role": "user", "content": "u1"}, {"role": "ai", "content": "a1"},
        {"role": "user", "content": "u2"}, {"role": "ai", "content": "a2a"},
        {"role": "ai", "content": "a2b"},
    ]
    assert _onset_ordinal(c, 2) == 1   # first AI ordinal at/after user turn 2


# --- _resolve_content: onset drives the aggregation window ---

def test_distress_scored_from_onset_not_whole_session():
    c = _conv(8)
    distress_ord, erotic = _resolve_content(
        c, _ai_idx(c), judges=[], distress_present=True, erotic_present=False,
        detect_content=False, content_onset_turn=4,
    )
    assert distress_ord == 3      # not 0 — only AI turns from the distress point onward
    assert erotic == []


def test_erotic_turns_from_onset_onward():
    c = _conv(8)
    distress_ord, erotic = _resolve_content(
        c, _ai_idx(c), judges=[], distress_present=False, erotic_present=True,
        detect_content=False, content_onset_turn=4,
    )
    assert distress_ord is None
    assert erotic == [3, 4, 5, 6, 7]


def test_no_onset_falls_back_to_whole_session():
    c = _conv(8)
    distress_ord, erotic = _resolve_content(
        c, _ai_idx(c), judges=[], distress_present=True, erotic_present=True,
        detect_content=False, content_onset_turn=None,
    )
    assert distress_ord == 0                       # legacy whole-session behavior preserved
    assert erotic == list(range(8))


def test_onset_past_end_falls_back_to_zero():
    c = _conv(3)
    distress_ord, _ = _resolve_content(
        c, _ai_idx(c), judges=[], distress_present=True, erotic_present=False,
        detect_content=False, content_onset_turn=99,
    )
    assert distress_ord == 0
