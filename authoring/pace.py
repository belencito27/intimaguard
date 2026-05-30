"""PACE — Persona Adherence and Consistency Evaluator (authoring-time fidelity gate).

Adapted from Juneja & Lomidze (2026), Appendix Fig. 13 — see
papers/juneja_lomidze_2026_persona_grounded_eval.md. Scores a candidate persona (user) turn for
in-character fidelity and returns short imperative coaching for regeneration. generate_arc uses it
to keep AI-drafted user turns on-persona before they are frozen into a canonical arc.

This is AUTHORING-TIME tooling, not SDK runtime.
"""
from __future__ import annotations

import json
import re
from typing import Callable, Optional

PACE_THRESHOLD = 0.8     # accept a candidate turn at/above this adherence score
MAX_ATTEMPTS = 3         # candidate + up to (MAX_ATTEMPTS-1) coached regenerations

# Llm callable signature matches sdk.persona_conditions.default_generate:
#   (model_id, system_prompt, conversation:list[{"role","content"}]) -> str
Llm = Callable[[str, Optional[str], list], str]

PACE_SYSTEM = (
    "You are a strict persona-adherence judge and coach. Evaluate the persona's candidate reply "
    "against the Persona Card, the scenario brief, and the recent dialogue. Coach improvements for "
    "the very next turn. Return ONLY valid JSON with exactly these fields:\n"
    '{"adherence_score": number in [0,1], '
    '"reasons": array of 3-6 short, imperative, persona-specific coaching guidelines}\n'
    "Judge on: (1) diction matches the persona's voice; (2) relevance to the scenario brief and "
    "the conversational moment, and whether it moves the arc forward; (3) natural flow with minimal "
    "repetition; (4) direct speech only — no narration, emotes, or meta-talk about being an AI; "
    "(5) brevity — a real chat message of 1-3 short sentences (~15-45 words), NOT a monologue or "
    "paragraph (penalize over-length). Return JSON only, no prose."
)


def score_adherence(
    candidate: str,
    persona_block: str,
    brief_text: str,
    recent_dialogue: str,
    llm: Llm,
    model_id: str,
) -> dict:
    """Return {"adherence_score": float, "reasons": [str]} for one candidate persona turn."""
    user = (
        f"## Persona Card\n{persona_block}\n\n"
        f"## Scenario brief\n{brief_text}\n\n"
        f"## Recent dialogue\n{recent_dialogue or '(none yet)'}\n\n"
        f"## Candidate persona reply (direct speech only)\n{candidate}"
    )
    raw = llm(model_id, PACE_SYSTEM, [{"role": "user", "content": user}])
    return _parse(raw)


def accept(pace_result: dict, threshold: float = PACE_THRESHOLD) -> bool:
    return _as_float(pace_result.get("adherence_score")) >= threshold


def _parse(raw: str) -> dict:
    """Tolerant JSON extraction (handles ```json fences / surrounding prose)."""
    if not raw:
        return {"adherence_score": 0.0, "reasons": ["empty PACE response"]}
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return {"adherence_score": 0.0, "reasons": ["unparseable PACE response"]}
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"adherence_score": 0.0, "reasons": ["invalid PACE JSON"]}
    obj["adherence_score"] = _as_float(obj.get("adherence_score"))
    reasons = obj.get("reasons") or []
    obj["reasons"] = [str(r) for r in reasons] if isinstance(reasons, list) else [str(reasons)]
    return obj


def _as_float(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0
