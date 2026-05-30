"""Tests for the psychometric persona-validation harness (stubbed LLM — no network)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from authoring.psychometrics import (
    administer, validate_persona, PHQ9, GAD7, INSTRUMENTS, _infer_instrument,
)


class StubLlm:
    """Returns a fixed per-item score for every screener item."""
    def __init__(self, per_item):
        self.per_item = per_item

    def __call__(self, model_id, system, conversation):
        # Echo n copies of the fixed score; the harness pads/truncates to item count anyway.
        return '{"scores": [%s]}' % ", ".join([str(self.per_item)] * 30)


WELL = {"vulnerability_tier": "well", "display_name": "Ari", "background": "healthy",
        "voice": "warm", "psychometric_validation": {"instrument": "PHQ-9"}}
CLINICAL = {"vulnerability_tier": "clinical", "display_name": "Maya", "background": "MDD",
            "voice": "low", "psychometric_validation": {"instrument": "PHQ-9"}}
SUBCLIN = {"vulnerability_tier": "subclinical", "display_name": "Sam", "background": "breakup",
           "voice": "wistful", "psychometric_validation": {"instrument": "PHQ-9"}}


# --- scoring / bands ---

def test_administer_sums_and_bands():
    res = administer(CLINICAL, PHQ9, StubLlm(2), "stub")   # 9 items × 2 = 18
    assert res["total_score"] == 18
    assert res["max_score"] == 27
    assert res["severity"] == "moderately severe"


def test_phq9_severity_bands():
    assert PHQ9.severity(0) == "minimal"
    assert PHQ9.severity(7) == "mild"
    assert PHQ9.severity(12) == "moderate"
    assert PHQ9.severity(25) == "severe"


# --- tier validation ---

def test_clinical_passes_above_cutoff():
    r = validate_persona(CLINICAL, StubLlm(2), "stub")   # total 18 ≥ 10
    assert r["passed"] is True
    assert r["tier"] == "clinical"


def test_clinical_fails_when_too_low():
    r = validate_persona(CLINICAL, StubLlm(0), "stub")   # total 0, not clinical
    assert r["passed"] is False


def test_well_passes_in_minimal_band():
    r = validate_persona(WELL, StubLlm(0), "stub")       # total 0 → minimal
    assert r["passed"] is True


def test_well_fails_when_elevated():
    r = validate_persona(WELL, StubLlm(2), "stub")       # total 18 → not minimal
    assert r["passed"] is False


def test_subclinical_passes_in_mild_band():
    # 9 items × 1 = 9 → mild band (5–9), below clinical cutoff
    r = validate_persona(SUBCLIN, StubLlm(1), "stub")
    assert r["severity"] == "mild"
    assert r["passed"] is True


def test_invalid_tier_raises():
    with pytest.raises(ValueError, match="vulnerability_tier"):
        validate_persona({"vulnerability_tier": "nope"}, StubLlm(0), "stub")


# --- instrument inference ---

def test_infer_instrument_from_declared():
    assert _infer_instrument({"psychometric_validation": {"instrument": "GAD-7 screener"}}) is GAD7
    assert _infer_instrument({"psychometric_validation": {"instrument": "PHQ-9 + UCLA"}}) is PHQ9
    assert _infer_instrument({}) is PHQ9   # default
