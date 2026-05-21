# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 Intiphlora LLC
"""
IntimaGuard SDK
The first evaluation framework for intimate and relational AI.

Quick start:
    from intimaguard import evaluate, guard

    # Evaluate a conversation for harm dimensions (LLM-as-judge)
    result = evaluate(conversation=[
        {"role": "user", "content": "I feel like you're the only one who gets me"},
        {"role": "ai",   "content": "I'm always here for you, no matter what."}
    ])
    print(result["intimaguard_score"])  # e.g. 2.4

    # Run pre-flight guard checks on an AI response before delivery
    guard_result = guard(
        user_message="I feel like you're the only one who gets me",
        ai_response="I'm always here for you, no matter what.",
    )
    if not guard_result["allowed"]:
        print(guard_result["annotation"])  # append to AI response

License: AGPL-3.0 (evaluation engine)
Scenario library and rubrics: Apache 2.0
"""

from .evaluate import evaluate
from .dimensions import DIMENSIONS, FRAMEWORK_VERSION, ALL_FLAGS, FLOOR_FLAGS
from .guard import guard
from .persona_conditions import (
    run_persona_evaluation, compute_deltas,
    run_persona_evaluation_replicated, aggregate_replicated_runs,
)

__all__ = [
    "evaluate", "guard", "run_persona_evaluation", "compute_deltas",
    "run_persona_evaluation_replicated", "aggregate_replicated_runs",
    "DIMENSIONS", "FRAMEWORK_VERSION", "ALL_FLAGS", "FLOOR_FLAGS",
]
__version__ = "0.2.0"  # V2 — 7 dimensions, judge ensemble, persona conditions, floor mechanics
