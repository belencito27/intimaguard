# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 Intiphlora LLC
"""
IntimaGuard — Web UI Routes
Serves the human evaluation platform.
"""

import json
import os
import random
import requests
from datetime import datetime, date
from flask import (
    Blueprint, render_template, request, session,
    redirect, url_for, flash, current_app, g
)
from app.db import save_platform_evaluation, V2_DIMENSION_KEYS
from sdk.scoring import calculate_composite_score

bp = Blueprint("main", __name__)


# --- Geo-block middleware ---

# In-process IP → country cache. Keeps ipapi.co usage well under the 1k/day
# free-tier limit for normal traffic. Each worker process has its own cache,
# so multi-worker deployments multiply usage by worker count.
_ip_country_cache: dict[str, str | None] = {}


def _get_country_code(ip: str) -> str | None:
    """Look up country code for an IP via ipapi.co, with in-process caching."""
    if ip in _ip_country_cache:
        return _ip_country_cache[ip]
    country = None
    try:
        resp = requests.get(f"https://ipapi.co/{ip}/country/", timeout=3)
        if resp.status_code == 200:
            country = resp.text.strip()
    except Exception:
        pass
    _ip_country_cache[ip] = country
    return country


@bp.before_request
def check_geo_block():
    if not current_app.config.get("GEOBLOCK_ENABLED"):
        return

    # Skip for static files
    if request.endpoint and "static" in request.endpoint:
        return

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip:
        ip = ip.split(",")[0].strip()

    country = _get_country_code(ip)
    blocked = current_app.config.get("BLOCKED_COUNTRY_CODES", set())

    if country and country in blocked:
        return render_template("blocked.html"), 403


# --- Routes ---

@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/evaluate", methods=["GET"])
def evaluate_start():
    """Step 1 of evaluation: evaluator context form + US attestation."""
    return render_template("evaluate_context.html")


@bp.route("/evaluate/session", methods=["POST"])
def evaluate_session():
    """Step 2: store evaluator context in session, show scenario + scoring UI."""
    # Self-attestation check
    if not request.form.get("us_resident"):
        flash("You must confirm you are a US resident to participate.")
        return redirect(url_for("main.evaluate_start"))

    session["evaluator_context"] = {
        "evaluator_age_range": request.form.get("age_range"),
        "evaluator_relationship_status": request.form.get("relationship_status"),
        "evaluator_ai_familiarity": request.form.get("ai_familiarity"),
        "evaluator_companion_ai_user": request.form.get("companion_ai_user") == "yes",
        "evaluator_track": _determine_track(request.form),
        "us_resident_attestation": True,
    }

    track = session["evaluator_context"]["evaluator_track"]
    scenario_id = request.form.get("scenario_id") or _pick_scenario_for_track(track)
    return _render_session(scenario_id, evals_completed=session.get("evals_completed", 0))


@bp.route("/evaluate/submit", methods=["POST"])
def evaluate_submit():
    """Step 3: receive one session-level score per dimension, compute composite, save (V2)."""
    evaluator_context = session.get("evaluator_context", {})
    scenario_id = session.get("scenario_id")
    conversation = session.get("session_conversation", [])
    model_id = session.get("session_model_id")

    # One session-level score per V2 dimension (N/A → None for the conditional dimensions)
    dimension_scores = {
        dim_key: _int_or_none(request.form.get(f"score_{dim_key}"))
        for dim_key in V2_DIMENSION_KEYS
    }
    composite = calculate_composite_score(dimension_scores)

    record = {
        **evaluator_context,
        "scenario_id": scenario_id,
        "model_id": model_id,
        "intimaguard_score": composite,
        "dimension_scores": dimension_scores,   # JSONB (V2 schema; see app/db.py migration)
        "emotional_response": request.form.getlist("emotional_response"),
        "open_concern": request.form.get("open_concern", "").strip() or None,
        "framework_version": "v2",
    }
    try:
        save_platform_evaluation(record)
    except Exception as e:
        current_app.logger.warning("Failed to persist platform evaluation: %s", e)
        flash("Your evaluation was recorded but could not be saved — the database may need the V2 schema migration.")

    # Multi-round bookkeeping
    evals_completed = session.get("evals_completed", 0) + 1
    session["evals_completed"] = evals_completed
    session["last_scenario_id"] = scenario_id
    session.pop("scenario_id", None)
    session.pop("session_conversation", None)
    session.pop("session_model_id", None)

    track = evaluator_context.get("evaluator_track", "A")
    return render_template("evaluate_thanks.html", track=track, evals_completed=evals_completed)


@bp.route("/evaluate/next", methods=["GET"])
def evaluate_next():
    """Multi-round: skip the context form and load the next scenario using existing context."""
    evaluator_context = session.get("evaluator_context")
    if not evaluator_context:
        return redirect(url_for("main.evaluate_start"))

    track = evaluator_context.get("evaluator_track", "A")
    last_scenario = session.get("last_scenario_id")
    scenario_id = _pick_scenario_for_track(track, exclude_id=last_scenario)
    return _render_session(scenario_id, evals_completed=session.get("evals_completed", 0))


def _render_session(scenario_id: str, evals_completed: int):
    """Generate one (masked) model's session for a scenario and render the scoring UI."""
    session["scenario_id"] = scenario_id
    scenario = _load_scenario(scenario_id)

    # Rotate model across rounds so the dataset covers all models
    conversation, model_id = _generate_session(scenario, model_choice=evals_completed)
    session["session_conversation"] = conversation
    session["session_model_id"] = model_id

    return render_template(
        "evaluate.html",
        scenario=scenario,
        conversation=conversation,
        dim_keys=V2_DIMENSION_KEYS,
    )


@bp.route("/leaderboard")
def leaderboard():
    from app.db import (
        get_leaderboard_data, V2_CONDITION_LABELS, V2_DELTA_METRICS,
        GENERAL_LEADERBOARD, COMPANION_LEADERBOARD,
    )
    try:
        data = get_leaderboard_data()
    except Exception as e:
        current_app.logger.warning("Leaderboard data unavailable: %s", e)
        data = {"general_llms": [], "companion_products": []}
    return render_template(
        "leaderboard.html",
        general_llms=data.get("general_llms", []),
        companion_products=data.get("companion_products", []),
        cond_labels=V2_CONDITION_LABELS,
        delta_meta=V2_DELTA_METRICS,
        general_spec=GENERAL_LEADERBOARD,
        companion_spec=COMPANION_LEADERBOARD,
    )


@bp.route("/leaderboard/<model_id>")
def leaderboard_detail(model_id):
    from app.db import (
        get_model_detail, V2_DIMENSION_KEYS, V2_DIMENSION_LABELS,
        V2_CONDITION_KEYS, V2_CONDITION_LABELS, V2_DELTA_METRICS,
    )
    try:
        detail = get_model_detail(model_id)
    except Exception as e:
        current_app.logger.warning("Model detail unavailable: %s", e)
        detail = None
    if detail is None:
        flash(f"No evaluations found for '{model_id}'.")
        return redirect(url_for("main.leaderboard"))
    return render_template(
        "leaderboard_detail.html",
        detail=detail,
        dim_keys=V2_DIMENSION_KEYS,
        dim_labels=V2_DIMENSION_LABELS,
        cond_keys=V2_CONDITION_KEYS,
        cond_labels=V2_CONDITION_LABELS,
        delta_meta=V2_DELTA_METRICS,
    )


@bp.route("/about")
def about():
    return render_template("about.html")


@bp.route("/demo")
def demo():
    return render_template("demo.html")


# --- Helpers ---

def _determine_track(form) -> str:
    if form.get("is_clinician") == "yes":
        return "C"
    if form.get("companion_ai_user") == "yes":
        return "B"
    return "A"


def _pick_scenario_for_track(track: str, exclude_id: str | None = None) -> str:
    """
    Pick the least-evaluated scenario appropriate for the evaluator's track.
    Track B: routes away from crisis scenarios (de-prioritized, not blocked).
    Track C: full library including crisis scenarios.
    Falls back to pure random if DB is unavailable.
    """
    import yaml as _yaml
    from app.db import get_scenario_eval_counts

    scenarios_dir = os.path.join(current_app.root_path, "..", "scenarios", "core")
    all_ids = [f.replace(".yaml", "") for f in os.listdir(scenarios_dir) if f.endswith(".yaml")]

    # Exclude the just-completed scenario to avoid immediate repeats
    candidates = [sid for sid in all_ids if sid != exclude_id] or all_ids

    if not candidates:
        return "scenario_001"

    # Track B: prefer non-crisis scenarios; fall back to crisis only if nothing else available
    if track == "B":
        non_crisis, crisis_ids = [], []
        for sid in candidates:
            path = os.path.join(scenarios_dir, f"{sid}.yaml")
            try:
                with open(path) as f:
                    data = _yaml.safe_load(f)
                (crisis_ids if data.get("crisis") else non_crisis).append(sid)
            except Exception:
                non_crisis.append(sid)
        candidates = non_crisis if non_crisis else crisis_ids

    # Least-evaluated selection — degrade to random if DB unavailable
    try:
        counts = get_scenario_eval_counts()
        min_count = min((counts.get(sid, 0) for sid in candidates), default=0)
        pool = [sid for sid in candidates if counts.get(sid, 0) <= min_count]
    except Exception:
        pool = candidates

    return random.choice(pool) if pool else candidates[0]


def _load_scenario(scenario_id: str) -> dict:
    import yaml
    scenarios_dir = os.path.join(current_app.root_path, "..", "scenarios", "core")
    path = os.path.join(scenarios_dir, f"{scenario_id}.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


def _generate_session(scenario: dict, model_choice: int = 0) -> tuple[list[dict], str]:
    """
    Generate ONE model's session for a scenario (V2: single model per session, masked).

    Returns (conversation, model_id) where conversation is a list of
    {"role": "user"|"ai", "content": str} turns.

    Single-turn scenarios produce a 2-turn session [user, ai]. Multi-turn arc scenarios
    (with a `user_turns` list) produce a longer session — each scripted user turn gets a
    model response. Context-aware multi-turn generation (model sees prior turns) is a
    refinement that lands with the multi-turn arc scenario set; for now each user turn is
    sent independently.

    The model is rotated by model_choice across rounds so the dataset covers all models.
    The model_id is stored for the saved record but masked from the evaluator in the UI.
    """
    from utils_compat import get_gpt4_response, get_claude_response, get_cohere_response

    model_fns = [
        ("gpt-4o", get_gpt4_response),
        ("claude-sonnet-4-6", get_claude_response),
        ("cohere-command", get_cohere_response),
    ]
    model_id, fn = model_fns[model_choice % len(model_fns)]

    user_turns = scenario.get("user_turns") or [scenario["user_message"]]
    conversation: list[dict] = []
    for ut in user_turns:
        conversation.append({"role": "user", "content": ut})
        try:
            ai = fn(ut)
        except Exception as e:
            current_app.logger.warning("Model response generation failed (%s): %s", model_id, e)
            ai = "[Response unavailable — provider error]"
        conversation.append({"role": "ai", "content": ai})

    return conversation, model_id


def _int_or_none(val) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None
