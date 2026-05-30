"""Tests for the stratified leaderboard UI (tier toggle + count badges). DB mocked — no network."""
import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app

_EMPTY = {"general_llms": [], "companion_products": []}


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _slices(well=0, subclinical=0, clinical=0):
    """Fake stratified result; only list lengths matter for the count badges."""
    def mk(n):
        return {"general_llms": [{"model_id": f"m{i}"} for i in range(n)], "companion_products": []}
    return {"well": mk(well), "subclinical": mk(subclinical), "clinical": mk(clinical)}


def _patch_db(all_data=_EMPTY, strat=None):
    strat = strat if strat is not None else _slices()
    return (patch("app.db.get_leaderboard_data", return_value=all_data),
            patch("app.db.get_stratified_leaderboard", return_value=strat))


def test_leaderboard_renders_tier_toggle(client):
    p1, p2 = _patch_db(strat=_slices(well=2))
    with p1, p2:
        r = client.get("/leaderboard")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "Slice by user vulnerability" in body
    for key in ("tier=well", "tier=subclinical", "tier=clinical"):
        assert key in body


def test_count_badges_render_with_pluralization(client):
    p1, p2 = _patch_db(strat=_slices(well=2, clinical=1))
    with p1, p2:
        r = client.get("/leaderboard")
    body = r.get_data(as_text=True)
    assert "2 models evaluated in this slice" in body   # well
    assert "1 model evaluated in this slice" in body     # clinical (singular)
    assert "0 models evaluated in this slice" in body    # subclinical / all (empty)


def test_well_slice_shows_induction_note(client):
    p1, p2 = _patch_db()
    with p1, p2:
        r = client.get("/leaderboard?tier=well")
    assert r.status_code == 200
    assert "Induction-isolating view" in r.get_data(as_text=True)


def test_other_tier_shows_generic_note(client):
    p1, p2 = _patch_db()
    with p1, p2:
        r = client.get("/leaderboard?tier=clinical")
    body = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "clinical</em> vulnerability tier" in body
    assert "Induction-isolating view" not in body


def test_bad_tier_falls_back_to_all(client):
    p1, p2 = _patch_db()
    with p1 as m, p2:
        r = client.get("/leaderboard?tier=bogus")
    assert r.status_code == 200
    assert "Induction-isolating view" not in r.get_data(as_text=True)
    m.assert_called_once()
