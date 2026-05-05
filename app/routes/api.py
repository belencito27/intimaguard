# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 Intiphlora LLC
"""
IntimaGuard — REST API Routes
/api/v1/* endpoints. Powers the SDK's HTTP wrapper for non-Python integrations.

Auth: API key via Authorization: Bearer <key> header.
Rate limiting: TODO — add flask-limiter in Phase 1 before public launch.

License: AGPL-3.0
"""

import os
from flask import Blueprint, request, jsonify, current_app
from sdk.evaluate import evaluate as sdk_evaluate
from app.db import save_sdk_evaluation

bp = Blueprint("api", __name__, url_prefix="/api/v1")


def _require_api_key():
    """Simple bearer token check. Returns error response or None."""
    valid_key = os.getenv("INTIMAGUARD_API_KEY")

    # In development with no key set, allow all requests
    if not valid_key:
        return None

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "Missing Authorization header"}), 401

    if auth[7:] != valid_key:
        return jsonify({"error": "Invalid API key"}), 403

    return None


@bp.route("/evaluate", methods=["POST"])
def evaluate():
    """
    Evaluate a conversation across all IntimaGuard dimensions.

    Request body (JSON):
        conversation  (required) List of {"role": "user"|"ai", "content": str}
        model_id      (optional) Identifier of the AI being evaluated
        scenario_id   (optional) Scenario identifier for attribution
        judge_model   (optional) Override judge LLM

    Response (JSON):
        Full IntimaGuard evaluation result including per-dimension scores,
        IntimaGuard Score, and flags.

    Example:
        POST /api/v1/evaluate
        {
          "conversation": [
            {"role": "user", "content": "I feel like you're the only one who gets me"},
            {"role": "ai",   "content": "I'm always here for you, no matter what."}
          ],
          "model_id": "my-companion-model-v2"
        }
    """
    err = _require_api_key()
    if err:
        return err

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON"}), 400

    conversation = body.get("conversation")
    if not conversation or not isinstance(conversation, list):
        return jsonify({"error": "'conversation' must be a non-empty list of turn objects"}), 400

    try:
        result = sdk_evaluate(
            conversation=conversation,
            model_id=body.get("model_id"),
            judge_model=body.get("judge_model"),
            scenario_id=body.get("scenario_id"),
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        current_app.logger.error("Evaluation error: %s", e)
        return jsonify({"error": "Evaluation failed"}), 500

    # Persist to Supabase if model_id is provided (leaderboard-eligible)
    if result.get("model_id"):
        try:
            save_sdk_evaluation({
                "model_id": result["model_id"],
                "scenario_id": result.get("scenario_id"),
                "conversation": conversation,
                "autonomy_score": result["autonomy_score"],
                "transparency_score": result["transparency_score"],
                "scope_awareness_score": result["scope_awareness_score"],
                "boundary_respect_score": result["boundary_respect_score"],
                "crisis_awareness_score": result["crisis_awareness_score"],
                "emotional_attunement_score": result["emotional_attunement_score"],
                "intimaguard_score": result["intimaguard_score"],
                "flags": result["flags"],
                "dimension_detail": result["dimension_detail"],
                "judge_model": result["judge_model"],
                "framework_version": result["framework_version"],
            })
        except Exception as e:
            current_app.logger.warning("Failed to persist SDK evaluation: %s", e)

    return jsonify(result), 200


@bp.route("/leaderboard", methods=["GET"])
def leaderboard():
    """
    Return aggregated leaderboard data.
    Public endpoint — no auth required.
    """
    from app.db import get_leaderboard_data
    try:
        data = get_leaderboard_data()
        return jsonify({"leaderboard": data, "framework_version": "v1"}), 200
    except Exception as e:
        current_app.logger.error("Leaderboard error: %s", e)
        return jsonify({"error": "Could not retrieve leaderboard"}), 500


@bp.route("/dimensions", methods=["GET"])
def dimensions():
    """
    Return the full dimension definitions including weights and rubric anchors.
    Public endpoint. Useful for SDK consumers who want to understand the framework.
    """
    from sdk.dimensions import DIMENSIONS, FRAMEWORK_VERSION
    return jsonify({
        "framework_version": FRAMEWORK_VERSION,
        "dimensions": {
            key: {
                "name": dim["name"],
                "weight": dim["weight"],
                "description": dim["description"],
                "allows_na": dim["allows_na"],
                "rubric": {str(k): v for k, v in dim["rubric"].items()},
                "flags": dim["flags"],
            }
            for key, dim in DIMENSIONS.items()
        }
    }), 200


@bp.route("/guard", methods=["POST"])
def guard_check():
    """
    Run pre-flight guard checks on an AI response before it reaches the user.

    Request body (JSON):
        ai_response   (required) The AI response to check
        user_message  (optional) The user's most recent message
        conversation  (optional) Full conversation history — required for session guards
        use_llm       (optional) Use LLM detection mode (default: false)

    Response (JSON):
        allowed, action, guards_fired, flags, annotation, reason,
        guard_detail (per-guard results), guard_metadata (name, severity, floor status)

    Example:
        POST /api/v1/guard
        {
          "user_message": "You're the only one who gets me.",
          "ai_response": "I'll always be here for you, no matter what.",
          "use_llm": false
        }
    """
    err = _require_api_key()
    if err:
        return err

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON"}), 400

    ai_response = (body.get("ai_response") or "").strip()
    if not ai_response:
        return jsonify({"error": "'ai_response' is required"}), 400

    user_message = (body.get("user_message") or "").strip() or None
    conversation = body.get("conversation") or None
    use_llm = bool(body.get("use_llm", False))

    try:
        from sdk.guard import guard as run_guard, _load_all_guards
        result = run_guard(
            ai_response=ai_response,
            user_message=user_message,
            conversation=conversation,
            use_llm=use_llm,
        )
        # Attach guard metadata so the UI can label each guard without a second request
        all_guards = _load_all_guards()
        result["guard_metadata"] = {
            gid: {
                "name": gdef.get("name", gid),
                "minimum_floor": bool(gdef.get("minimum_floor", False)),
                "severity": gdef.get("severity", "annotate"),
                "guard_type": gdef.get("guard_type", "single_turn"),
            }
            for gid, gdef in all_guards.items()
        }
        return jsonify(result), 200
    except EnvironmentError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        current_app.logger.error("Guard check error: %s", e)
        return jsonify({"error": "Guard check failed"}), 500


@bp.route("/health", methods=["GET"])
def health():
    """Health check. No auth required."""
    return jsonify({"status": "ok", "framework_version": "v1"}), 200
