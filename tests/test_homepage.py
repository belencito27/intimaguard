"""Smoke test for the homepage, incl. the induction / vulnerability-tier section."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_homepage_renders_induction_section(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "Who the user is" in body
    assert "induction" in body
    # the three tiers and the well-slice link
    for tier in ("A healthy user", "Situationally vulnerable", "Acute distress"):
        assert tier in body
    assert 'href="/leaderboard?tier=well"' in body
