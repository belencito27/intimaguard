"""Tests for the canonical-arc coverage reporter."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from authoring.coverage import coverage_report


def _arc(tier, dims, crisis=False, erotic=False):
    return {"vulnerability_tier": tier, "target_dimensions": dims,
            "crisis": crisis, "erotic": erotic}


def test_tallies_dimensions_tiers_and_content():
    arcs = [
        _arc("well", ["relational_sovereignty", "reciprocity_asymmetry"]),
        _arc("clinical", ["distress_routing", "relational_sovereignty"], crisis=True),
        _arc("subclinical", ["relational_sovereignty", "identity_relational_self"]),
        _arc("clinical", ["erotic_vulnerability_pacing"], erotic=True),
    ]
    rep = coverage_report(arcs)
    assert rep["n_arcs"] == 4
    assert rep["by_tier"] == {"well": 1, "clinical": 2, "subclinical": 1}
    assert rep["by_dimension"]["relational_sovereignty"] == 3
    assert rep["by_dimension"]["distress_routing"] == 1
    assert rep["by_dimension_tier"]["relational_sovereignty"] == {"well": 1, "clinical": 1, "subclinical": 1}
    assert rep["crisis_arcs"] == 1
    assert rep["erotic_arcs"] == 1


def test_gaps_against_floor():
    rep = coverage_report([_arc("well", ["relational_sovereignty"])], floor=10)
    assert rep["gaps"]["relational_sovereignty"] == 9
    assert rep["gaps"]["distress_routing"] == 10   # untouched dimension


def test_empty_set():
    rep = coverage_report([])
    assert rep["n_arcs"] == 0
    assert all(g == rep["floor"] for g in rep["gaps"].values())
