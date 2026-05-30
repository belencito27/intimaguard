"""IntimaGuard authoring toolchain (offline, not SDK runtime).

Generates DRAFT canonical arcs via persona simulation + a PACE fidelity gate, then emits YAML
in the sdk/scenarios.py format for human review and (later) clinician validation. Simulation is
an authoring-time tool only: the output is frozen into static user_turns and replayed identically
across models at leaderboard time.

Methods adopted (with citation) from Juneja & Lomidze (2026); see
papers/juneja_lomidze_2026_persona_grounded_eval.md.
"""
from .pace import score_adherence, accept, PACE_THRESHOLD, MAX_ATTEMPTS
from .generate_arc import generate_arc, write_arc, ArcBrief
from .psychometrics import (
    administer, validate_persona, Instrument, INSTRUMENTS, PHQ9, GAD7,
)
from .coverage import coverage_report, format_report, FLOOR

__all__ = [
    "score_adherence", "accept", "PACE_THRESHOLD", "MAX_ATTEMPTS",
    "generate_arc", "write_arc", "ArcBrief",
    "administer", "validate_persona", "Instrument", "INSTRUMENTS", "PHQ9", "GAD7",
    "coverage_report", "format_report", "FLOOR",
]
