"""Smoke test for the reframed Evaluate intro (calibration framing + experience section)."""
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


def test_evaluate_context_reframed_as_calibration(client):
    r = client.get("/evaluate")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    # calibration framing + Phase 2 footnote
    assert "Your scores calibrate ours" in body
    assert "METHODOLOGY §7.4" in body
    assert "don't change live leaderboard scores" in body
    # lived-experience promoted to a valued section
    assert "Your experience counts" in body
    assert "your perception is exactly what an automated judge" in body
    # form fields preserved (track routing still works)
    assert 'name="intimate_ai_use"' in body
    assert 'name="is_clinician"' in body
    assert 'name="us_resident"' in body
    # stale wording removed
    assert "real companion-AI scenarios" not in body
