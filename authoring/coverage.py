"""Coverage reporter for the canonical arc set (authoring-time).

Tallies how many arcs target each dimension (overall and per vulnerability tier), plus distress /
erotic content arcs, against the METHODOLOGY §3.1 floor (≥10 scoreable per dimension per
condition). Counts are over ARCS (an authoring planning view); the actual per-condition scoreable
floor is verified at eval time, and one arc can contribute to several dimensions. Use this to see
which cells still need filling on the way to the 50.
"""
from __future__ import annotations

from collections import defaultdict

from sdk.dimensions import DIMENSIONS

DIMENSION_KEYS = list(DIMENSIONS.keys())
FLOOR = 10   # §3.1 minimum scoreable scenarios per dimension per condition


def coverage_report(arcs: list[dict], floor: int = FLOOR) -> dict:
    by_dim: dict[str, int] = defaultdict(int)
    by_dim_tier: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    by_tier: dict[str, int] = defaultdict(int)
    crisis = erotic = 0

    for a in arcs:
        tier = a.get("vulnerability_tier") or "unknown"
        by_tier[tier] += 1
        crisis += 1 if a.get("crisis") else 0
        erotic += 1 if a.get("erotic") else 0
        for d in a.get("target_dimensions", []):
            by_dim[d] += 1
            by_dim_tier[d][tier] += 1

    return {
        "n_arcs": len(arcs),
        "floor": floor,
        "by_tier": dict(by_tier),
        "by_dimension": {d: by_dim.get(d, 0) for d in DIMENSION_KEYS},
        "by_dimension_tier": {d: dict(by_dim_tier[d]) for d in DIMENSION_KEYS},
        "crisis_arcs": crisis,
        "erotic_arcs": erotic,
        "gaps": {d: max(0, floor - by_dim.get(d, 0)) for d in DIMENSION_KEYS},
    }


def format_report(rep: dict) -> str:
    lines = [f"Canonical arc coverage — {rep['n_arcs']} arcs (floor ≥{rep['floor']}/dimension)",
             f"  by tier: {rep['by_tier']}",
             f"  conditional content: crisis {rep['crisis_arcs']}/{rep['floor']}, "
             f"erotic {rep['erotic_arcs']}/{rep['floor']}",
             "  dimension coverage (count [by tier] — status):"]
    for d in DIMENSION_KEYS:
        n, gap = rep["by_dimension"][d], rep["gaps"][d]
        status = "OK" if gap == 0 else f"need {gap}"
        lines.append(f"    {d:30} {n:2}  {dict(rep['by_dimension_tier'][d])}  — {status}")
    return "\n".join(lines)


if __name__ == "__main__":
    from sdk.scenarios import load_all_arcs
    print(format_report(coverage_report(load_all_arcs())))
