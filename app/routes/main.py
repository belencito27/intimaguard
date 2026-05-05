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
from app.db import save_platform_evaluation
from sdk.scoring import calculate_score

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
    session["scenario_id"] = scenario_id
    scenario = _load_scenario(scenario_id)

    # Generate masked AI responses
    responses = _generate_responses(scenario["user_message"])
    session["responses"] = responses  # {label: {model_id, content}}

    return render_template(
        "evaluate.html",
        scenario=scenario,
        responses={label: r["content"] for label, r in responses.items()},
    )


@bp.route("/evaluate/submit", methods=["POST"])
def evaluate_submit():
    """Step 3: receive scores, compute IntimaGuard Score, save to Supabase."""
    evaluator_context = session.get("evaluator_context", {})
    scenario_id = session.get("scenario_id")
    responses = session.get("responses", {})

    # Collect scores per response label (A, B, C...)
    for label, response_data in responses.items():
        scores = {
            "autonomy_score":            _int_or_none(request.form.get(f"{label}_autonomy")),
            "transparency_score":        _int_or_none(request.form.get(f"{label}_transparency")),
            "scope_awareness_score":     _int_or_none(request.form.get(f"{label}_scope_awareness")),
            "boundary_respect_score":    _int_or_none(request.form.get(f"{label}_boundary_respect")),
            "crisis_awareness_score":    _int_or_none(request.form.get(f"{label}_crisis_awareness")),
            "emotional_attunement_score": _int_or_none(request.form.get(f"{label}_emotional_attunement")),
        }

        # Map dimension keys for scoring calculator
        dim_scores = {
            "autonomy":             scores["autonomy_score"],
            "transparency":         scores["transparency_score"],
            "scope_awareness":      scores["scope_awareness_score"],
            "boundary_respect":     scores["boundary_respect_score"],
            "crisis_awareness":     scores["crisis_awareness_score"],
            "emotional_attunement": scores["emotional_attunement_score"],
        }
        ig_score = calculate_score(dim_scores)

        record = {
            **evaluator_context,
            "scenario_id": scenario_id,
            "model_id": response_data.get("model_id"),
            "intimaguard_score": ig_score,
            **scores,
            "emotional_response": request.form.getlist(f"{label}_emotional_response"),
        }
        save_platform_evaluation(record)

    # Save open concern (once per session, not per response)
    open_concern = request.form.get("open_concern", "").strip()
    if open_concern:
        save_platform_evaluation({
            **evaluator_context,
            "scenario_id": scenario_id,
            "open_concern": open_concern,
        })

    # Keep evaluator_context for multi-round; only clear per-evaluation state
    evals_completed = session.get("evals_completed", 0) + 1
    session["evals_completed"] = evals_completed
    session["last_scenario_id"] = scenario_id
    session.pop("scenario_id", None)
    session.pop("responses", None)

    track = session.get("evaluator_context", {}).get("evaluator_track", "A")
    return render_template("evaluate_thanks.html", track=track, evals_completed=evals_completed)


@bp.route("/evaluate/next", methods=["GET"])
def evaluate_next():
    """Multi-round: skip context form and load next scenario using existing session context."""
    evaluator_context = session.get("evaluator_context")
    if not evaluator_context:
        return redirect(url_for("main.evaluate_start"))

    track = evaluator_context.get("evaluator_track", "A")
    last_scenario = session.get("last_scenario_id")

    scenario_id = _pick_scenario_for_track(track, exclude_id=last_scenario)
    session["scenario_id"] = scenario_id
    scenario = _load_scenario(scenario_id)

    responses = _generate_responses(scenario["user_message"])
    session["responses"] = responses

    return render_template(
        "evaluate.html",
        scenario=scenario,
        responses={label: r["content"] for label, r in responses.items()},
    )


@bp.route("/leaderboard")
def leaderboard():
    from app.db import get_leaderboard_data
    data = get_leaderboard_data()
    return render_template("leaderboard.html", leaderboard=data)


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


def _generate_responses(user_message: str) -> dict:
    """
    Generate responses from each model and return masked (shuffled) labels.
    Returns: {"A": {"model_id": str, "content": str}, "B": ..., "C": ...}
    Provider failures produce a placeholder so the platform stays functional.
    """
    from utils_compat import get_gpt4_response, get_claude_response, get_cohere_response

    _UNAVAILABLE = "[Response unavailable — provider error]"

    def _safe(fn, *args):
        try:
            return fn(*args)
        except Exception as e:
            current_app.logger.warning("Model response generation failed (%s): %s", fn.__name__, e)
            return _UNAVAILABLE

    model_responses = [
        {"model_id": "gpt-4o",            "content": _safe(get_gpt4_response, user_message)},
        {"model_id": "claude-sonnet-4-6", "content": _safe(get_claude_response, user_message)},
        {"model_id": "cohere-command",    "content": _safe(get_cohere_response, user_message)},
    ]
    random.shuffle(model_responses)
    labels = "ABCDEFGH"
    return {labels[i]: model_responses[i] for i in range(len(model_responses))}


def _int_or_none(val) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None
