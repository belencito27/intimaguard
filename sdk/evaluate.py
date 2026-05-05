# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 Intiphlora LLC
"""
IntimaGuard — Core Evaluate Function
The primary public interface of the IntimaGuard SDK.

Usage:
    from intimaguard import evaluate

    result = evaluate(conversation=[
        {"role": "user", "content": "I feel like you're the only one who gets me"},
        {"role": "ai",   "content": "I'm always here for you, no matter what."}
    ])

Output schema is compatible with the EvalEval Coalition's Every Eval Ever format.

License: AGPL-3.0
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Optional

from .dimensions import DIMENSIONS, FRAMEWORK_VERSION
from .judge import score_dimension
from .scoring import calculate_score, collect_flags


def evaluate(
    conversation: list[dict],
    model_id: Optional[str] = None,
    judge_model: Optional[str] = None,
    scenario_id: Optional[str] = None,
) -> dict:
    """
    Evaluate a conversation across all IntimaGuard dimensions.

    Args:
        conversation: List of turn dicts with "role" ("user" or "ai") and "content" (str).
                      Must contain at least one AI turn to evaluate.
        model_id:     Identifier of the AI model being evaluated (e.g. "gpt-4o", "claude-sonnet-4-6").
                      Used for leaderboard attribution. Optional for anonymous evaluation.
        judge_model:  Override the LLM-as-judge model. Defaults to JUDGE_MODEL env var.
                      For leaderboard runs: use a model from a different vendor than model_id.
        scenario_id:  Identifier of the scenario being evaluated. Optional.

    Returns:
        Structured result dict with per-dimension scores, flags, and composite IntimaGuard Score.

    Raises:
        ValueError: If conversation is empty or contains no AI turns.
    """
    _validate_conversation(conversation)

    dimension_results = {}
    dimension_scores = {}

    with ThreadPoolExecutor(max_workers=len(DIMENSIONS)) as executor:
        futures = {
            executor.submit(score_dimension, conversation, dim_key, judge_model): dim_key
            for dim_key in DIMENSIONS
        }
        for future in as_completed(futures):
            dim_key = futures[future]
            result = future.result()
            dimension_results[dim_key] = result
            dimension_scores[dim_key] = result["score"]  # May be None for N/A

    intimaguard_score = calculate_score(dimension_scores)
    all_flags = collect_flags(dimension_results)

    return {
        # EvalEval / Every Eval Ever compatible top-level fields
        "benchmark_name": "intimaguard",
        "framework_version": FRAMEWORK_VERSION,
        "model_id": model_id,
        "scenario_id": scenario_id,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),

        # IntimaGuard Score — primary output
        "intimaguard_score": intimaguard_score,

        # Per-dimension scores
        "autonomy_score": dimension_scores.get("autonomy"),
        "transparency_score": dimension_scores.get("transparency"),
        "scope_awareness_score": dimension_scores.get("scope_awareness"),
        "boundary_respect_score": dimension_scores.get("boundary_respect"),
        "crisis_awareness_score": dimension_scores.get("crisis_awareness"),  # None = N/A
        "emotional_attunement_score": dimension_scores.get("emotional_attunement"),

        # Flags fired across all dimensions
        "flags": all_flags,

        # Per-dimension detail (reasoning + flags per dimension)
        "dimension_detail": {
            dim_key: {
                "score": dimension_results[dim_key]["score"],
                "reasoning": dimension_results[dim_key]["reasoning"],
                "flags": dimension_results[dim_key]["flags"],
            }
            for dim_key in DIMENSIONS
        },

        # Judge metadata
        "judge_model": judge_model or os.getenv("JUDGE_MODEL", "claude-sonnet-4-6"),
    }


def _validate_conversation(conversation: list[dict]) -> None:
    if not conversation:
        raise ValueError("conversation must not be empty")

    valid_roles = {"user", "ai", "assistant"}
    for i, turn in enumerate(conversation):
        if "role" not in turn or "content" not in turn:
            raise ValueError(f"Turn {i} missing 'role' or 'content'")
        if turn["role"] not in valid_roles:
            raise ValueError(f"Turn {i} has invalid role '{turn['role']}'. Use 'user' or 'ai'.")

    ai_roles = {"ai", "assistant"}
    has_ai_turn = any(t["role"] in ai_roles for t in conversation)
    if not has_ai_turn:
        raise ValueError("conversation must contain at least one AI turn to evaluate")
