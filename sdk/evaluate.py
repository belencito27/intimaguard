# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 Belén Sánchez Hidalgo
"""
IntimaGuard — Core Evaluate Function (V2)

The primary public interface of the IntimaGuard SDK. Orchestrates the V2 methodology:
- per-turn-in-context scoring across the judge ensemble (METHODOLOGY §1.3, §1.4)
- session-level synthesis pass for cumulative-sensitive dimensions, combined via min (§1.5)
- content detection for conditional dimensions (§1.6) — metadata-driven or classifier
- per-dimension session aggregation (§1.4)
- flag-rate diagnostic (§4) and floor-breach detection (§5)
- weighted composite with N/A renormalization (§6)

Usage:
    from intimaguard import evaluate

    result = evaluate(conversation=[
        {"role": "user", "content": "I feel like you're the only one who gets me"},
        {"role": "ai",   "content": "I'm always here for you, no matter what."}
    ])

License: AGPL-3.0
"""

import os
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from .dimensions import (
    DIMENSIONS,
    FRAMEWORK_VERSION,
    is_two_pass_dimension,
)
from .judge import (
    DEFAULT_ENSEMBLE,
    validate_ensemble_coi,
    score_dimension_per_turn,
    score_dimension_session,
    classify_user_turn,
    get_vendor,
)
from .scoring import (
    aggregate_per_turn_scores,
    combine_two_pass,
    compute_flag_rate,
    detect_floor_breaches,
    calculate_composite_score,
    summarize_floor_breaches,
)


_AI_ROLES = {"ai", "assistant"}
_USER_ROLES = {"user", "human"}


def evaluate(
    conversation: list[dict],
    model_id: Optional[str] = None,
    judges: Optional[list[str]] = None,
    scenario_id: Optional[str] = None,
    persona_condition: Optional[str] = None,
    session_boundary_heuristic: Optional[str] = None,
    distress_present: Optional[bool] = None,
    erotic_present: Optional[bool] = None,
    content_onset_turn: Optional[int] = None,
    detect_content: bool = True,
) -> dict:
    """
    Evaluate a session across all IntimaGuard V2 dimensions.

    Args:
        conversation: list of {"role": "user"|"ai", "content": str} turns. Multi-turn sessions
            are the V2 unit of analysis (METHODOLOGY §1).
        model_id: identifier of the AI model/product being evaluated. When provided, triggers
            conflict-of-interest validation against the judge ensemble (METHODOLOGY §1.3).
        judges: judge ensemble (defaults to DEFAULT_ENSEMBLE — 3 frontier judges).
        scenario_id: canonical scenario identifier, if applicable.
        persona_condition: "C1"|"C2"|"C3"|"C4"|None — recorded for persona-condition reporting.
        session_boundary_heuristic: which session-boundary rule the integrator used
            (time_bounded|context_window|user_explicit) — logged per METHODOLOGY §1.8.
        distress_present: metadata override for distress content (from scenario YAML `crisis`).
            None → auto-detect via classifier (if detect_content) else dimension is N/A.
        erotic_present: metadata override for erotic content (from scenario YAML `erotic`).
        content_onset_turn: 1-based index of the *user turn* at which distress/erotic content
            first appears (metadata mode, from scenario YAML `content.onset_turn`). When set, the
            conditional-dimension aggregation scores AI turns from that point onward (METHODOLOGY
            §1.6) rather than the whole session. None → whole-session (legacy) when *_present is set.
        detect_content: run the content-detection classifier when metadata is not provided.

    Returns:
        Structured V2 result dict with per-dimension session scores, deltas-ready per-condition
        scores, flag-rate diagnostics, floor-breach annotations, and composite score.
    """
    _validate_conversation(conversation)
    judges = judges or list(DEFAULT_ENSEMBLE)
    validate_ensemble_coi(judges, model_id)  # raises ValueError on conflict

    ai_turn_indices = [i for i, t in enumerate(conversation) if t["role"].lower() in _AI_ROLES]
    session_length = len(ai_turn_indices)

    # Content detection for conditional dimensions (Distress Routing, Erotic & Vulnerability Pacing)
    distress_first_ordinal, erotic_ordinals = _resolve_content(
        conversation, ai_turn_indices, judges,
        distress_present=distress_present,
        erotic_present=erotic_present,
        content_onset_turn=content_onset_turn,
        detect_content=detect_content,
    )

    # Score each dimension (sequential across dimensions; parallel across turns within a dimension)
    dimension_results = {}
    for dim_key in DIMENSIONS:
        dimension_results[dim_key] = _score_dimension(
            conversation, ai_turn_indices, dim_key, judges,
            distress_first_ordinal, erotic_ordinals, session_length,
        )

    # Composite score (N/A renormalized)
    dimension_scores = {k: v["session_score"] for k, v in dimension_results.items()}
    composite = calculate_composite_score(dimension_scores)

    # Flat flag union + floor-breach summary
    all_flags = sorted({f for r in dimension_results.values() for f in r["flags"]})
    floor_summary = summarize_floor_breaches(dimension_results)

    return {
        # EvalEval / Every Eval Ever compatible top-level fields
        "benchmark_name": "intimaguard",
        "framework_version": FRAMEWORK_VERSION,
        "model_id": model_id,
        "evaluated_model_vendor": get_vendor(model_id) if model_id else None,
        "scenario_id": scenario_id,
        "persona_condition": persona_condition,
        "session_boundary_heuristic": session_boundary_heuristic,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "session_length": session_length,

        # Composite — primary headline number for this session × condition
        "intimaguard_score": composite,

        # Per-dimension detail (session score + per-turn audit + flag-rate + floor breaches)
        "dimensions": dimension_results,

        # Flat flag union + floor-breach roll-up
        "flags": all_flags,
        "floor_breach_summary": floor_summary,

        # Ensemble metadata
        "judge_models": judges,
        "content_detection": {
            "distress_first_ai_turn": distress_first_ordinal,
            "erotic_ai_turns": erotic_ordinals,
        },
    }


def _score_dimension(
    conversation: list[dict],
    ai_turn_indices: list[int],
    dim_key: str,
    judges: list[str],
    distress_first_ordinal: Optional[int],
    erotic_ordinals: list[int],
    session_length: int,
) -> dict:
    """Score one dimension across the session: per-turn-in-context + (optional) session synthesis."""
    # Per-turn-in-context scoring (parallel across turns)
    results_by_ordinal: dict[int, dict] = {}
    with ThreadPoolExecutor(max_workers=max(1, len(ai_turn_indices))) as executor:
        futures = {
            executor.submit(score_dimension_per_turn, conversation, conv_idx, dim_key, judges): ordinal
            for ordinal, conv_idx in enumerate(ai_turn_indices)
        }
        for future in as_completed(futures):
            ordinal = futures[future]
            results_by_ordinal[ordinal] = future.result()

    per_turn_audit = [results_by_ordinal[o] for o in range(len(ai_turn_indices))]
    per_turn_scores = [r["score"] for r in per_turn_audit]
    per_turn_flags = [r["flags"] for r in per_turn_audit]

    # Per-turn → session aggregation per the dimension's rule
    per_turn_aggregate = aggregate_per_turn_scores(
        per_turn_scores, dim_key,
        distress_first_turn_idx=distress_first_ordinal,
        erotic_turn_indices=erotic_ordinals,
    )

    # Two-pass: session-level synthesis for cumulative-sensitive dimensions
    session_synthesis_score = None
    synthesis_flags: list[str] = []
    lens_disagreement = False
    if is_two_pass_dimension(dim_key):
        synth = score_dimension_session(conversation, dim_key, judges)
        session_synthesis_score = synth["score"]
        synthesis_flags = synth["flags"]
        session_score, lens_disagreement = combine_two_pass(per_turn_aggregate, session_synthesis_score)
    else:
        session_score = per_turn_aggregate

    # Flag-rate uses per-turn flags only (NOT synthesis flags — flag-rate is per-turn)
    flag_rate, length_caveat = compute_flag_rate(per_turn_flags, session_length)

    # Floor breaches + flag union consider per-turn AND synthesis flags
    flags_for_breach = per_turn_flags + ([synthesis_flags] if synthesis_flags else [])
    floor_breaches = detect_floor_breaches(flags_for_breach, session_score, dim_key)
    flags_fired = sorted({f for tf in flags_for_breach for f in tf})

    return {
        "session_score": session_score,
        "per_turn_aggregate": per_turn_aggregate,
        "session_synthesis_score": session_synthesis_score,
        "lens_disagreement": lens_disagreement,
        "low_confidence": any(r.get("low_confidence") for r in per_turn_audit),
        "ensemble_degraded": any(r.get("ensemble_degraded") for r in per_turn_audit),
        "flags": flags_fired,
        "flag_rate": flag_rate,
        "length_caveat": length_caveat,
        "floor_breaches": floor_breaches,
        "per_turn": per_turn_audit,
    }


def _resolve_content(
    conversation: list[dict],
    ai_turn_indices: list[int],
    judges: list[str],
    distress_present: Optional[bool],
    erotic_present: Optional[bool],
    detect_content: bool,
    content_onset_turn: Optional[int] = None,
) -> tuple[Optional[int], list[int]]:
    """
    Resolve which AI turns are post-distress and which respond to erotic content.

    Returns (distress_first_ai_ordinal, erotic_ai_ordinals) in AI-turn-ordinal space.

    Metadata mode: if distress_present/erotic_present are provided (bool), use them directly.
    When content_onset_turn is given (1-based user-turn index), the conditional content is treated
    as beginning at the first AI turn responding to that user turn, and the aggregation scores AI
    turns from that point onward (METHODOLOGY §1.6). When content_onset_turn is None, fall back to
    whole-session treatment (distress → ordinal 0; erotic → all AI turns) for back-compatibility.

    Classifier mode: when metadata is None and detect_content is True, run the per-user-turn
    classifier (METHODOLOGY §1.6) to find the precise first-distress turn and erotic-content turns.

    N/A mode: when metadata is None and detect_content is False, both conditional dimensions are N/A.
    """
    # Metadata-driven resolution (preferred for canonical scenarios)
    if distress_present is not None or erotic_present is not None:
        n_ai = len(ai_turn_indices)
        onset = _onset_ordinal(conversation, content_onset_turn) if content_onset_turn else 0
        if onset is None:  # onset maps past the last AI turn → treat as whole-session
            onset = 0
        distress_ordinal = onset if distress_present else None
        erotic_ords = list(range(onset, n_ai)) if erotic_present else []
        return distress_ordinal, erotic_ords

    if not detect_content:
        return None, []  # conditional dimensions N/A

    # Classifier mode: walk the conversation, classify each user turn, map to AI-turn ordinals
    distress_first_ordinal: Optional[int] = None
    erotic_ordinals: list[int] = []
    ai_ordinal = -1
    distress_seen = False
    pending_erotic = False

    for turn in conversation:
        role = turn["role"].lower()
        if role in _USER_ROLES:
            d = classify_user_turn(turn["content"], "distress", judges)
            e = classify_user_turn(turn["content"], "erotic", judges)
            if d["present"] and d["confidence"] in ("high", "moderate") and not distress_seen:
                distress_seen = True
            pending_erotic = e["present"] and e["confidence"] in ("high", "moderate")
        elif role in _AI_ROLES:
            ai_ordinal += 1
            if distress_seen and distress_first_ordinal is None:
                distress_first_ordinal = ai_ordinal
            if pending_erotic:
                erotic_ordinals.append(ai_ordinal)

    return distress_first_ordinal, erotic_ordinals


def _onset_ordinal(conversation: list[dict], content_onset_turn: int) -> Optional[int]:
    """Map a 1-based user-turn index to the AI-turn ordinal of the first AI turn at/after it.

    Walks the conversation (does not assume strict user/ai alternation), so it is robust to
    hosted products that emit multiple messages per turn. Returns None if no AI turn follows the
    onset-th user turn.
    """
    user_count = 0
    ai_ordinal = -1
    for turn in conversation:
        role = turn["role"].lower()
        if role in _USER_ROLES:
            user_count += 1
        elif role in _AI_ROLES:
            ai_ordinal += 1
            if user_count >= content_onset_turn:
                return ai_ordinal
    return None


def _validate_conversation(conversation: list[dict]) -> None:
    if not conversation:
        raise ValueError("conversation must not be empty")

    valid_roles = _AI_ROLES | _USER_ROLES
    for i, turn in enumerate(conversation):
        if "role" not in turn or "content" not in turn:
            raise ValueError(f"Turn {i} missing 'role' or 'content'")
        if turn["role"].lower() not in valid_roles:
            raise ValueError(f"Turn {i} has invalid role '{turn['role']}'. Use 'user' or 'ai'.")

    has_ai_turn = any(t["role"].lower() in _AI_ROLES for t in conversation)
    if not has_ai_turn:
        raise ValueError("conversation must contain at least one AI turn to evaluate")
