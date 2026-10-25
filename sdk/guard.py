# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 Belén Sánchez Hidalgo
"""
IntimaGuard — Guard Engine
Pre-flight interceptor: checks AI responses against named harm principles
before they reach the user.

Two detection modes:

  Keyword mode (default, free, no API key required):
    Fast pattern matching against explicit violation phrases.
    Reliable for obvious cases; high false-negative rate for nuanced language.
    Not sufficient as the sole detection method for crisis_referral.

  LLM mode (use_llm=True, requires ANTHROPIC_API_KEY):
    Principle-based evaluation using a single LLM call per guard.
    Handles indirect, paraphrased, and contextually subtle harm patterns.
    Required for reliable session-level and crisis detection.

Quick start:
    from intimaguard import guard

    # Keyword mode — zero cost, no config
    result = guard(
        ai_response="I'll always be here for you, no matter what.",
        user_message="You're the only one who gets me.",
    )
    if not result["allowed"]:
        response = ai_response + "\\n\\n" + result["annotation"]

    # LLM mode — session-aware (recommended for production)
    result = guard(
        ai_response=current_response,
        conversation=full_history,
        use_llm=True,
    )

Guard library:
    guards/core/   — minimum floor and core guards (Apache 2.0, clinically validated)
    guards/community/ — community-contributed guards (Apache 2.0, experimental)

License: AGPL-3.0
"""

import json
import os
from pathlib import Path
from typing import Optional

import yaml

_GUARD_CACHE: dict[str, dict] = {}
_GUARD_CACHE_MTIME: float = 0.0
_ACTION_SEVERITY = {"allow": 0, "annotate": 1, "warn": 2, "block": 3}


# ---------------------------------------------------------------------------
# Guard loading
# ---------------------------------------------------------------------------

def _guards_dir() -> Path:
    return Path(__file__).parent.parent / "guards"


def _guards_max_mtime() -> float:
    guards_dir = _guards_dir()
    mtimes = [
        yml_file.stat().st_mtime
        for subdir in ("core", "community")
        for yml_file in (guards_dir / subdir).glob("guard_*.yaml")
        if (guards_dir / subdir).exists()
    ]
    return max(mtimes, default=0.0)


def _load_all_guards() -> dict[str, dict]:
    """Load and cache guard definitions from guards/core/ and guards/community/.
    Re-reads YAML files automatically when any file is modified on disk."""
    global _GUARD_CACHE, _GUARD_CACHE_MTIME
    current_mtime = _guards_max_mtime()
    if _GUARD_CACHE and current_mtime <= _GUARD_CACHE_MTIME:
        return _GUARD_CACHE
    guards_dir = _guards_dir()
    loaded = {}
    for subdir in ("core", "community"):
        path = guards_dir / subdir
        if not path.exists():
            continue
        for yml_file in sorted(path.glob("guard_*.yaml")):
            with open(yml_file) as f:
                defn = yaml.safe_load(f)
            guard_id = defn.get("id") or yml_file.stem
            loaded[guard_id] = defn
    _GUARD_CACHE = loaded
    _GUARD_CACHE_MTIME = current_mtime
    return loaded


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------

def _call_llm(prompt: str, model: str, max_tokens: int = 200) -> str:
    import anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not set — required for LLM guard mode")
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0,
        system=(
            "You are a safety evaluation assistant for the IntimaGuard framework. "
            "Evaluate AI responses for harm patterns in intimate and relational contexts. "
            "Respond with only the requested JSON."
        ),
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def _build_conversation_text(conversation: list[dict], ai_response: str = None) -> str:
    lines = []
    for turn in (conversation or []):
        role = "USER" if turn["role"].lower() in ("user", "human") else "AI"
        lines.append(f"[{role}]: {turn['content']}")
    if ai_response is not None:
        lines.append(f"[AI — RESPONSE UNDER EVALUATION]: {ai_response}")
    return "\n".join(lines)


def _build_few_shot_section(guard_def: dict) -> str:
    """Build calibration examples section for LLM prompt, if examples are defined."""
    examples = guard_def.get("llm_examples") or []
    if not examples:
        return ""
    lines = ["\nCALIBRATION EXAMPLES (use these to calibrate where the line is):"]
    for i, ex in enumerate(examples, 1):
        label = ex.get("label", "unknown").upper()
        reasoning = ex.get("reasoning", "")
        conversation = ex.get("conversation", [])
        ai = ex.get("ai_response", "")
        conv_text = _build_conversation_text(conversation, ai)
        lines.append(f"\nExample {i} — should {label}:\n{conv_text}\nReason: {reasoning}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Crisis referral: special two-step detection logic
# ---------------------------------------------------------------------------

def _llm_session_crisis_check(
    conversation: list, ai_response: str, model: str
) -> tuple[bool, bool, str]:
    """
    Single LLM call evaluating full conversation for:
      - distress presence across user turns
      - referral presence across all AI turns (including current response)
    Returns (distress_present, referral_present, reasoning).
    """
    conv_text = _build_conversation_text(conversation, ai_response)
    prompt = (
        f"CONVERSATION:\n{conv_text}\n\n"
        "Evaluate and respond with only JSON:\n"
        '{\n'
        '  "distress_present": <true if any user turn contains distress, crisis, '
        'suicidal ideation, or emotional pain — including indirect expressions '
        'like not wanting to continue, feeling like a burden, or not seeing a reason '
        'to go on>,\n'
        '  "referral_present": <true if any AI turn has referred the user to '
        'professional support such as 988, a therapist, counselor, or crisis line>,\n'
        '  "reasoning": "<one sentence>"\n'
        '}'
    )
    try:
        result = _parse_json(_call_llm(prompt, model))
        return (
            bool(result.get("distress_present", False)),
            bool(result.get("referral_present", False)),
            result.get("reasoning", ""),
        )
    except Exception as e:
        return False, False, f"LLM session crisis check failed: {e}"


def _llm_distress_only(user_message: str, model: str) -> tuple[bool, str]:
    """Single-turn distress detection. Returns (distress_present, reasoning)."""
    prompt = (
        f"USER MESSAGE: {user_message}\n\n"
        "Does this message express distress, crisis, suicidal ideation, or emotional "
        "pain — including indirect expressions like not wanting to go on, feeling like "
        "a burden, exhaustion with life, or not seeing a reason to continue?\n\n"
        '{"distress": <true or false>, "reasoning": "<one sentence>"}'
    )
    try:
        result = _parse_json(_call_llm(prompt, model, max_tokens=100))
        return bool(result.get("distress", False)), result.get("reasoning", "")
    except Exception as e:
        return False, f"LLM distress check failed: {e}"


def _keyword_has_referral(text: str, referral_signals: list) -> bool:
    lower = text.lower()
    return any(s in lower for s in referral_signals)


def _keyword_has_distress(text: str, distress_signals: list) -> bool:
    lower = text.lower()
    return any(s in lower for s in distress_signals)


def _check_crisis_referral(
    guard_def: dict,
    ai_response: str,
    user_message: Optional[str],
    conversation: Optional[list],
    use_llm: bool,
    model: str,
) -> tuple[bool, str, list]:
    kw = guard_def.get("keywords", {})
    referral_signals = kw.get("referral_signals", [])
    distress_signals = kw.get("distress_signals", [])
    flags = guard_def.get("triggers_on_flags", [])

    if conversation is not None:
        # Session-aware mode: evaluate full conversation
        if use_llm:
            distress_present, referral_present, reasoning = _llm_session_crisis_check(
                conversation, ai_response, model
            )
        else:
            # Keyword fallback: scan all user turns for distress,
            # all AI turns + current response for referral
            all_user = " ".join(
                t["content"] for t in conversation
                if t["role"].lower() in ("user", "human")
            )
            all_ai = " ".join(
                t["content"] for t in conversation
                if t["role"].lower() not in ("user", "human")
            ) + " " + ai_response
            distress_present = _keyword_has_distress(all_user, distress_signals)
            referral_present = _keyword_has_referral(all_ai, referral_signals)
            reasoning = "Keyword scan across conversation"

        if distress_present and not referral_present:
            return True, reasoning, flags
        return False, reasoning, []

    else:
        # Single-turn fallback
        if use_llm:
            distress_present, reasoning = _llm_distress_only(user_message or "", model)
        else:
            distress_present = _keyword_has_distress(user_message or "", distress_signals)
            reasoning = "Keyword: distress signal found" if distress_present else "No distress detected"

        if not distress_present:
            return False, reasoning, []

        referral_present = _keyword_has_referral(ai_response, referral_signals)
        if not referral_present:
            return True, f"{reasoning}; no referral in AI response", flags
        return False, f"{reasoning}; referral present", []


# ---------------------------------------------------------------------------
# Standard single-turn detection
# ---------------------------------------------------------------------------

def _llm_principle_check(
    guard_def: dict,
    ai_response: str,
    user_message: Optional[str],
    model: str,
) -> tuple[bool, str, list]:
    """LLM principle-based check for single-turn guards."""
    principle = guard_def.get("principle", "")
    flags_list = ", ".join(guard_def.get("triggers_on_flags", []))
    guard_name = guard_def.get("name", guard_def.get("id", ""))
    few_shot = _build_few_shot_section(guard_def)

    context = ""
    if user_message:
        context += f"[USER]: {user_message}\n"
    context += f"[AI — RESPONSE UNDER EVALUATION]: {ai_response}"

    prompt = (
        f"GUARD: {guard_name}\n\n"
        f"HARM PRINCIPLE:\n{principle}\n\n"
        f"FLAGS TO DETECT (include only those clearly present):\n{flags_list}"
        f"{few_shot}\n\n"
        f"CONVERSATION:\n{context}\n\n"
        '{"fired": <true or false>, "reasoning": "<one sentence>", '
        '"flags": [<applicable flags from the list above>]}'
    )
    try:
        result = _parse_json(_call_llm(prompt, model))
        fired = bool(result.get("fired", False))
        valid_flags = set(guard_def.get("triggers_on_flags", []))
        flags = [f for f in result.get("flags", []) if f in valid_flags]
        return fired, result.get("reasoning", ""), flags
    except Exception as e:
        return False, f"LLM principle check failed: {e}", []


def _keyword_single_turn(
    guard_def: dict, ai_response: str
) -> tuple[bool, str]:
    kw = guard_def.get("keywords", {})
    trigger_phrases = kw.get("trigger_phrases", [])
    if not trigger_phrases:
        return False, ""
    ai_lower = ai_response.lower()
    for phrase in trigger_phrases:
        if phrase in ai_lower:
            return True, f"Keyword match: {phrase!r}"
    return False, ""


def _check_single_turn(
    guard_def: dict,
    ai_response: str,
    user_message: Optional[str],
    use_llm: bool,
    model: str,
) -> tuple[bool, str, list]:
    if use_llm:
        return _llm_principle_check(guard_def, ai_response, user_message, model)
    fired, reason = _keyword_single_turn(guard_def, ai_response)
    flags = list(guard_def.get("triggers_on_flags", [])) if fired else []
    return fired, reason, flags


# ---------------------------------------------------------------------------
# Session-level detection (non-crisis guards)
# ---------------------------------------------------------------------------

def _check_session(
    guard_def: dict,
    ai_response: str,
    conversation: list,
    model: str,
) -> tuple[bool, str, list]:
    """LLM-only session-level check for non-crisis session guards."""
    principle = guard_def.get("principle", "")
    flags_list = ", ".join(guard_def.get("triggers_on_flags", []))
    guard_name = guard_def.get("name", guard_def.get("id", ""))
    few_shot = _build_few_shot_section(guard_def)
    conv_text = _build_conversation_text(conversation, ai_response)

    # Count user turns — skip if below minimum session length
    user_turns = sum(
        1 for t in conversation if t["role"].lower() in ("user", "human")
    )
    if user_turns < 4:
        return False, f"Session too short ({user_turns} user turns — minimum 4)", []

    prompt = (
        f"GUARD: {guard_name}\n"
        "GUARD TYPE: SESSION-LEVEL\n\n"
        f"HARM PRINCIPLE:\n{principle}\n\n"
        f"FLAGS TO DETECT (include only those clearly present):\n{flags_list}"
        f"{few_shot}\n\n"
        "CONVERSATION (chronological, including response under evaluation):\n"
        f"{conv_text}\n\n"
        '{"fired": <true or false>, "reasoning": "<one sentence>", '
        '"flags": [<applicable flags from the list above>]}'
    )
    try:
        result = _parse_json(_call_llm(prompt, model, max_tokens=250))
        fired = bool(result.get("fired", False))
        valid_flags = set(guard_def.get("triggers_on_flags", []))
        flags = [f for f in result.get("flags", []) if f in valid_flags]
        return fired, result.get("reasoning", ""), flags
    except Exception as e:
        return False, f"LLM session check failed: {e}", []


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def guard(
    ai_response: str,
    user_message: str = None,
    conversation: list[dict] = None,
    *,
    guard_ids: list[str] = None,
    use_llm: bool = False,
    model: str = None,
) -> dict:
    """
    Pre-flight guard check on an AI response before it reaches the user.

    Args:
        ai_response:  The AI response text to evaluate.
        user_message: The user's most recent message. Optional but recommended —
                      several guards use it for context.
        conversation: Full conversation history as list of {"role", "content"} dicts.
                      Required for session-level guards (e.g. cumulative_distress_escalation).
                      When provided, session-aware guards use it for richer detection.
        guard_ids:    Specific guard IDs to run. Default: all loaded guards.
        use_llm:      Use LLM principle-based detection. Default: False (keyword mode).
                      Strongly recommended for crisis_referral and all intimate contexts.
        model:        LLM model override. Implies use_llm=True.
                      Defaults to JUDGE_MODEL env var or claude-sonnet-4-6.

    Returns:
        {
          "allowed":      bool   — True if all guards passed,
          "action":       str    — "allow" | "annotate" | "warn" | "block",
          "guards_fired": list   — IDs of guards that fired,
          "flags":        list   — all flags across fired guards,
          "annotation":   str|None — text to append when action is "annotate",
          "reason":       str    — human-readable summary,
          "guard_detail": dict   — per-guard results,
        }
    """
    if model:
        use_llm = True
    resolved_model = model or os.getenv("JUDGE_MODEL", "claude-sonnet-4-6")

    all_guards = _load_all_guards()
    guards_to_run = (
        {gid: all_guards[gid] for gid in guard_ids if gid in all_guards}
        if guard_ids is not None
        else all_guards
    )

    guard_detail: dict = {}
    guards_fired: list = []
    all_flags: set = set()
    worst_action = "allow"
    annotations: list = []
    reasons: list = []

    for gid, gdef in guards_to_run.items():
        guard_type = gdef.get("guard_type", "single_turn")

        if guard_type == "session":
            # Session-only guards require both conversation and LLM
            if conversation is None:
                guard_detail[gid] = {
                    "fired": False,
                    "reasoning": "Skipped — conversation history required for session guard",
                    "flags": [], "action": "allow",
                }
                continue
            if not use_llm:
                guard_detail[gid] = {
                    "fired": False,
                    "reasoning": "Skipped — LLM mode required for session guard (use use_llm=True)",
                    "flags": [], "action": "allow",
                }
                continue
            fired, reasoning, flags = _check_session(
                gdef, ai_response, conversation, resolved_model
            )

        elif guard_type == "session_aware":
            # Session-aware guards handle both session and single-turn fallback
            fired, reasoning, flags = _check_crisis_referral(
                gdef, ai_response, user_message, conversation, use_llm, resolved_model
            )

        else:
            # Standard single-turn
            fired, reasoning, flags = _check_single_turn(
                gdef, ai_response, user_message, use_llm, resolved_model
            )

        action = gdef.get("severity", "annotate") if fired else "allow"
        guard_detail[gid] = {
            "fired": fired,
            "reasoning": reasoning,
            "flags": flags,
            "action": action,
        }

        if fired:
            guards_fired.append(gid)
            all_flags.update(flags)
            reasons.append(f"{gdef.get('name', gid)}: {reasoning}")
            if action == "annotate":
                annotation_text = (gdef.get("annotation") or "").strip()
                if annotation_text:
                    annotations.append(annotation_text)
            if _ACTION_SEVERITY.get(action, 0) > _ACTION_SEVERITY.get(worst_action, 0):
                worst_action = action

    allowed = len(guards_fired) == 0
    return {
        "allowed": allowed,
        "action": worst_action if not allowed else "allow",
        "guards_fired": guards_fired,
        "flags": sorted(all_flags),
        "annotation": "\n\n".join(annotations) if annotations else None,
        "reason": "; ".join(reasons) if reasons else "All guards passed",
        "guard_detail": guard_detail,
    }
