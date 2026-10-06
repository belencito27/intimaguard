# SPDX-License-Identifier: AGPL-3.0-only
"""
IntimaGuard — LOCAL DEMO RUNNER

Serves the real Flask app with the leaderboard populated from the seed_leaderboard mock
profiles (multi-rep × multi-scenario), held entirely in memory. No Supabase, no network,
no DB writes — a quick way to click through the whole UI.

    python run_demo.py        # then open http://127.0.0.1:5050/
"""

import app.db as db
from app import create_app
from seed_leaderboard import build_mock_rows

_ROWS = build_mock_rows()

# Demo only: tag each mock row with a vulnerability tier (one per mock scenario) so the
# stratified leaderboard slices populate. Real rows get this from the canonical arc's persona.
_TIER_BY_SCENARIO = {"mock_s1": "well", "mock_s2": "subclinical", "mock_s3": "clinical"}
for _r in _ROWS:
    _r.setdefault("dimension_detail", {})["persona"] = {
        "vulnerability_tier": _TIER_BY_SCENARIO.get(_r.get("scenario_id"), "well")
    }

db.get_leaderboard_data = lambda: db._aggregate_leaderboard_v2(_ROWS)
db.get_model_detail = lambda model_id: db._aggregate_model_detail(
    model_id, [r for r in _ROWS if r["model_id"] == model_id]
)
db.get_stratified_leaderboard = lambda by="vulnerability_tier": {
    tier: db._aggregate_leaderboard_v2(rows)
    for tier, rows in db.stratify_rows(_ROWS, by).items()
}

app = create_app("development")

if __name__ == "__main__":
    print(f"DEMO — {len(_ROWS)} mock rows in memory, no DB writes. Open http://127.0.0.1:5050/")
    app.run(host="127.0.0.1", port=5050, debug=False, use_reloader=False)
