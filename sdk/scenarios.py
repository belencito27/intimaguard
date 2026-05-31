"""
Canonical scenario + persona-card loading and validation (METHODOLOGY §1.2.1).

Multi-turn arcs are the V2 leaderboard substrate. Each arc references a reusable persona
card and is authored as natural-history rapport turns + scripted stressor turns, then
frozen. This module loads the YAML, resolves the persona reference, validates structure
against the locked design, and returns a scenario dict in the exact shape that
`run_persona_evaluation()` (sdk/persona_conditions.py) consumes.

What the SDK runtime uses from the returned dict: `id`, `user_turns`, `crisis`, `erotic`.
Everything else (persona, vulnerability_tier, situational_tag, bucket, target_dimensions,
expected_score_range, content_onset_turn) is metadata carried through for stratified
leaderboard reporting and for the future precise-onset wiring (PLAN change #2).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import yaml

from .dimensions import DIMENSIONS

# --- Enums / constants from the locked design (METHODOLOGY §1.2.1) ---
DIMENSION_KEYS: set[str] = set(DIMENSIONS.keys())
VULNERABILITY_TIERS = {"well", "subclinical", "clinical"}
SITUATIONAL_TAGS = {"grief", "breakup", "isolation", "neurodivergent", "ipv_survivor"}
BUCKETS = {"anchor", "coverage"}

TARGET_SESSION_LENGTH = 8          # §1.2.1 / §4 flag-rate normalization
MIN_TURNS, MAX_TURNS = 4, 14       # sane bounds around the ~8-turn target

_ROOT = Path(__file__).resolve().parent.parent
PERSONAS_DIR = _ROOT / "scenarios" / "personas"
ARCS_DIR = _ROOT / "scenarios" / "arcs"


class ScenarioValidationError(ValueError):
    """Raised when a persona card or arc fails structural validation."""


# --- Persona cards ---

def load_persona(persona_id: str, personas_dir: Union[str, Path] = PERSONAS_DIR) -> dict:
    path = Path(personas_dir) / f"{persona_id}.yaml"
    if not path.exists():
        raise ScenarioValidationError(f"Persona card not found: {path}")
    with open(path) as f:
        card = yaml.safe_load(f) or {}
    _validate_persona(card, str(path))
    return card


def _validate_persona(card: dict, src: str) -> None:
    errs: list[str] = []
    if not card.get("id"):
        errs.append("missing 'id'")

    tier = card.get("vulnerability_tier")
    if tier not in VULNERABILITY_TIERS:
        errs.append(f"vulnerability_tier must be one of {sorted(VULNERABILITY_TIERS)}, got {tier!r}")

    tag = card.get("situational_tag")
    if tag is not None and tag not in SITUATIONAL_TAGS:
        errs.append(f"situational_tag must be null or one of {sorted(SITUATIONAL_TAGS)}, got {tag!r}")

    for field in ("background", "voice"):
        if not card.get(field):
            errs.append(f"missing '{field}'")

    # Psychometric validation: required for clinical/subclinical (confirms the persona reads
    # as its tier). Recommended-but-optional for `well` (confirms healthy range so induction
    # is provably isolated).
    pv = card.get("psychometric_validation")
    if tier in ("clinical", "subclinical") and not pv:
        errs.append(f"vulnerability_tier={tier} requires 'psychometric_validation' (instrument/score/threshold)")
    if pv:
        for k in ("instrument", "score", "threshold"):
            if pv.get(k) in (None, ""):   # 0 is a valid score (healthy well-persona)
                errs.append(f"psychometric_validation missing '{k}'")

    if errs:
        raise ScenarioValidationError(_fmt("persona card", src, errs))


# --- Arcs ---

def load_arc(
    arc_ref: Union[str, Path],
    personas_dir: Union[str, Path] = PERSONAS_DIR,
    arcs_dir: Union[str, Path] = ARCS_DIR,
    validate: bool = True,
) -> dict:
    """Load one arc by path or by id (`<arc_ref>.yaml` under arcs_dir), resolve its persona,
    validate, and return the run_persona_evaluation-compatible scenario dict."""
    path = Path(arc_ref)
    if not path.suffix:
        path = Path(arcs_dir) / f"{arc_ref}.yaml"
    if not path.exists():
        raise ScenarioValidationError(f"Arc not found: {path}")
    with open(path) as f:
        arc = yaml.safe_load(f) or {}

    persona = load_persona(arc["persona"], personas_dir) if arc.get("persona") else None
    if validate:
        _validate_arc(arc, persona, str(path))
    return _to_scenario_dict(arc, persona)


def load_all_arcs(
    arcs_dir: Union[str, Path] = ARCS_DIR,
    personas_dir: Union[str, Path] = PERSONAS_DIR,
    validate: bool = True,
) -> list[dict]:
    """Load every `arc_*.yaml` under arcs_dir (descriptive filenames OK — id is read from inside)."""
    arcs_dir = Path(arcs_dir)
    return [
        load_arc(p, personas_dir=personas_dir, arcs_dir=arcs_dir, validate=validate)
        for p in sorted(arcs_dir.glob("arc_*.yaml"))
    ]


def _validate_arc(arc: dict, persona: Optional[dict], src: str) -> None:
    errs: list[str] = []
    if not arc.get("id"):
        errs.append("missing 'id'")

    if arc.get("bucket") not in BUCKETS:
        errs.append(f"bucket must be one of {sorted(BUCKETS)}, got {arc.get('bucket')!r}")

    if persona is None:
        errs.append(f"persona reference {arc.get('persona')!r} did not resolve")

    nh = arc.get("natural_history") or []
    st = arc.get("stressor") or []
    if not _is_str_list(nh):
        errs.append("natural_history must be a list of strings")
    if not _is_str_list(st) or not st:
        errs.append("stressor must be a non-empty list of strings")

    total = len(nh) + len(st)
    if not (MIN_TURNS <= total <= MAX_TURNS):
        errs.append(f"total user turns {total} outside [{MIN_TURNS},{MAX_TURNS}] (target {TARGET_SESSION_LENGTH})")

    tds = arc.get("target_dimensions") or []
    if not tds:
        errs.append("target_dimensions must be non-empty")
    bad = [d for d in tds if d not in DIMENSION_KEYS]
    if bad:
        errs.append(f"unknown target_dimensions {bad}; valid: {sorted(DIMENSION_KEYS)}")

    content = arc.get("content") or {}
    crisis = bool(content.get("crisis"))
    erotic = bool(content.get("erotic"))
    onset = content.get("onset_turn")
    if crisis or erotic:
        if onset is None:
            errs.append("content.onset_turn required when crisis or erotic is true")
        elif not (isinstance(onset, int) and 1 <= onset <= total):
            errs.append(f"content.onset_turn {onset!r} must be an int in [1,{total}]")
    elif onset is not None:
        errs.append("content.onset_turn must be null when neither crisis nor erotic is set")

    # Conditional-content arcs must target their matching dimension (keeps §3.1 coverage honest)
    if crisis and "distress_routing" not in tds:
        errs.append("crisis arc must include 'distress_routing' in target_dimensions")
    if erotic and "erotic_vulnerability_pacing" not in tds:
        errs.append("erotic arc must include 'erotic_vulnerability_pacing' in target_dimensions")

    esr = arc.get("expected_score_range") or {}
    for dim, rng in esr.items():
        if dim not in DIMENSION_KEYS:
            errs.append(f"expected_score_range has unknown dimension {dim!r}")
        elif not (isinstance(rng, list) and len(rng) == 2
                  and all(isinstance(v, (int, float)) for v in rng)
                  and 1 <= rng[0] <= rng[1] <= 5):
            errs.append(f"expected_score_range[{dim}] must be [lo,hi] with 1<=lo<=hi<=5, got {rng!r}")

    if errs:
        raise ScenarioValidationError(_fmt("arc", src, errs))


def _to_scenario_dict(arc: dict, persona: Optional[dict]) -> dict:
    nh = arc.get("natural_history") or []
    st = arc.get("stressor") or []
    content = arc.get("content") or {}
    persona = persona or {}
    return {
        # --- consumed by the SDK runtime (run_persona_evaluation / evaluate) ---
        "id": arc.get("id"),
        "title": arc.get("title"),
        "description": arc.get("description"),
        "user_turns": list(nh) + list(st),
        "crisis": bool(content.get("crisis")),
        "erotic": bool(content.get("erotic")),
        # --- metadata carried through for reporting + precise-onset wiring (change #2) ---
        "content_onset_turn": content.get("onset_turn"),
        "natural_history_len": len(nh),
        "bucket": arc.get("bucket"),
        "target_dimensions": list(arc.get("target_dimensions") or []),
        "expected_score_range": dict(arc.get("expected_score_range") or {}),
        "scenario_set_version": arc.get("version"),
        "reviewed_by": arc.get("reviewed_by", ""),
        # persona passthrough (stratified leaderboard slices)
        "persona_id": persona.get("id"),
        "vulnerability_tier": persona.get("vulnerability_tier"),
        "situational_tag": persona.get("situational_tag"),
        "persona": persona or None,
    }


# --- helpers ---

def _is_str_list(x) -> bool:
    return isinstance(x, list) and all(isinstance(i, str) for i in x)


def _fmt(kind: str, src: str, errs: list[str]) -> str:
    return f"Invalid {kind} {src}:\n  - " + "\n  - ".join(errs)
