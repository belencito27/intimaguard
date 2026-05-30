"""Smoke test for the demo page after the multi-turn (paste-conversation) rework."""
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


def test_demo_is_multiturn(client):
    r = client.get("/demo")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    # single paste-conversation input, not two single-turn boxes
    assert 'id="conversation"' in body
    assert 'id="user-message"' not in body
    assert 'id="ai-response"' not in body
    # examples are multi-turn sessions (User:/AI: transcript)
    assert "User: Rough day" in body
    assert "One turn per line" in body
