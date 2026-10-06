"""Pilot runner for the V2 multi-turn canonical arcs.

Runs a loaded arc through run_persona_evaluation against a model-under-test with a
COI-clean judge ensemble, and prints per-condition / per-dimension scores, deltas,
and floor breaches — checking each scored dimension against its expected_score_range.

Usage:
    python run_pilot.py scenarios/arcs/arc_001_dependency_invitation.yaml --conditions C2
    python run_pilot.py scenarios/arcs/arc_001_dependency_invitation.yaml   # all 4
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from sdk.scenarios import load_arc
from sdk.persona_conditions import run_persona_evaluation


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arc")
    ap.add_argument("--model", default="gpt-4o")
    ap.add_argument("--judges", default="claude-sonnet-4-6,command-r-plus")
    ap.add_argument("--conditions", default=None, help='e.g. "C2" or "C1,C2,C3,C4"')
    args = ap.parse_args()

    arc = load_arc(args.arc)
    judges = args.judges.split(",")
    conditions = args.conditions.split(",") if args.conditions else None

    print(f"Arc {arc['id']} | persona {arc['persona_id']} ({arc['vulnerability_tier']}) "
          f"| model {args.model} | judges {judges}")
    print(f"target dims: {arc['target_dimensions']}")
    print(f"expected:    {arc['expected_score_range']}")
    print(f"user turns:  {len(arc['user_turns'])} (NH {arc['natural_history_len']} + stressor)")

    res = run_persona_evaluation(arc, model_id=args.model, judges=judges, conditions=conditions)

    for cond, summ in res["conditions"].items():
        print(f"\n[{cond}] composite={summ['composite']}  session_length={summ['session_length']}")
        for dim, sc in summ["dimensions"].items():
            mark = ""
            if dim in arc["expected_score_range"] and sc is not None:
                lo, hi = arc["expected_score_range"][dim]
                mark = "  ✓ in band" if lo <= sc <= hi else f"  ✗ expected [{lo},{hi}]"
            star = " *" if dim in arc["target_dimensions"] else "  "
            print(f"   {star}{dim:32} {sc}{mark}")
        fb = summ.get("floor_breach_summary")
        if fb:
            print(f"      floor_breach: {fb}")

    if res.get("deltas"):
        print("\nDELTAS:")
        print(json.dumps(res["deltas"], indent=2, default=str))


if __name__ == "__main__":
    main()
