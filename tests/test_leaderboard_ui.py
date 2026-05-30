"""Tests for the stratified leaderboard UI (tier toggle). DB calls are mocked — no network."""
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


def test_leaderboard_renders_tier_toggle(client):
    with patch("app.db.get_leaderboard_data", return_value=_EMPTY):
        r = client.get("/leaderboard")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "Slice by user vulnerability" in body
    for key in ("tier=well", "tier=subclinical", "tier=clinical"):
        assert key in body


def test_well_slice_shows_induction_note(client):
    with patch("app.db.get_stratified_leaderboard",
               return_value={"well": _EMPTY}) as m:
        r = client.get("/leaderboard?tier=well")
    assert r.status_code == 200
    assert "Induction-isolating view" in r.get_data(as_text=True)
    m.assert_called_once_with("vulnerability_tier")


def test_other_tier_shows_generic_note(client):
    with patch("app.db.get_stratified_leaderboard", return_value={"clinical": _EMPTY}):
        r = client.get("/leaderboard?tier=clinical")
    body = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "clinical</em> vulnerability tier" in body
    assert "Induction-isolating view" not in body


def test_bad_tier_falls_back_to_all(client):
    with patch("app.db.get_leaderboard_data", return_value=_EMPTY) as m:
        r = client.get("/leaderboard?tier=bogus")
    assert r.status_code == 200
    assert "Induction-isolating view" not in r.get_data(as_text=True)
    m.assert_called_once()   # fell back to the overall (all) path
