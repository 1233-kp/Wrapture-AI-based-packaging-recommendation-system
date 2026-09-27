"""Evaluation script: runs the rules engine against a curated reference set
and reports an "agreement rate" — the fraction of cases where the engine's
top pick (or, looser, any of its top 3) is inside a hand-authored set of
"acceptable" material ids for that commodity+conditions.

=============================================================================
WHAT THIS METRIC DOES AND DOES NOT PROVE — READ BEFORE QUOTING THE NUMBER
=============================================================================
DOES:
  - Measure internal consistency between the rules engine's output and our
    own hand-curated expectations (evaluation/reference_cases.py), which
    encode generally-known, textbook-level food-packaging practice.
  - Catch obvious regressions: if a code change makes the engine recommend
    glass for a chip bag, this will flag it.
  - Give a single number to track across changes to rules.json / the scoring
    logic, so we can tell if a tuning change made things better or worse
    *relative to our own reference set*.

DOES NOT:
  - Prove the engine's recommendations are scientifically correct, safe, or
    optimal. The reference set was authored by the same team that built the
    engine, from general knowledge, not from lab trials, food scientist
    review, or a validated external dataset.
  - Measure real-world shelf-life outcomes, cost accuracy, or actual
    consumer/producer preference.
  - Generalize beyond the commodities and materials in our own dataset (see
    data/commodities.json and data/packaging_materials.json for current
    counts) — there is no held-out or independently-sourced test set here.
  - Mean a low score is necessarily an engine bug: the reference case itself
    could be wrong, too narrow, or reflect a regional/product-format
    assumption that doesn't hold universally (e.g. "onions ship in mesh
    bags" is common but not universal).

In short: this is a regression-and-sanity-check tool for internal
development, not a validation study. Treat "78% agreement" as "78% of our
own hand-picked expectations weren't contradicted", not "78% accurate".
=============================================================================

Usage:
    cd backend
    .venv/Scripts/python.exe -m evaluation.run_evaluation
"""

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from engine.recommender import find_commodity, recommend_detailed
from evaluation.reference_cases import REFERENCE_CASES

RESULTS_PATH = Path(__file__).resolve().parent / "results" / "latest.json"


def _run_case(case) -> dict:
    conditions = case.conditions
    result = recommend_detailed(
        case.commodity_id,
        budget_tier=conditions.get("budget_tier", "standard"),
        prioritize_sustainability=conditions.get("prioritize_sustainability", False),
        expected_transport_days=conditions.get("expected_transport_days"),
        ambient_temperature_c=conditions.get("ambient_temperature_c"),
    )
    if result is None:
        return {
            "case_id": case.case_id,
            "commodity_id": case.commodity_id,
            "error": f"Unknown commodity id '{case.commodity_id}' — reference case is stale.",
        }

    recs = result["recommendations"]
    top1_id = recs[0]["material_id"] if recs else None
    top3_ids = {r["material_id"] for r in recs[:3]}

    top1_hit = top1_id in case.expected_material_ids
    top3_hit = bool(top3_ids & case.expected_material_ids)

    commodity = find_commodity(case.commodity_id)

    return {
        "case_id": case.case_id,
        "commodity_id": case.commodity_id,
        "commodity_category": commodity["category"] if commodity else None,
        "conditions": conditions,
        "expected_material_ids": sorted(case.expected_material_ids),
        "actual_top1_material_id": top1_id,
        "actual_top3_material_ids": sorted(top3_ids),
        "top1_hit": top1_hit,
        "top3_hit": top3_hit,
        "source_note": case.source_note,
    }


def run_evaluation() -> dict:
    case_results = [_run_case(case) for case in REFERENCE_CASES]
    valid_results = [r for r in case_results if "error" not in r]
    errored = [r for r in case_results if "error" in r]

    total = len(valid_results)
    top1_hits = sum(1 for r in valid_results if r["top1_hit"])
    top3_hits = sum(1 for r in valid_results if r["top3_hit"])

    by_category: dict[str, dict] = defaultdict(lambda: {"total": 0, "top1_hits": 0, "top3_hits": 0})
    for r in valid_results:
        cat = r["commodity_category"] or "unknown"
        by_category[cat]["total"] += 1
        by_category[cat]["top1_hits"] += int(r["top1_hit"])
        by_category[cat]["top3_hits"] += int(r["top3_hit"])

    category_breakdown = {
        cat: {
            "total": stats["total"],
            "top1_agreement_rate_pct": round(100 * stats["top1_hits"] / stats["total"], 1) if stats["total"] else None,
            "top3_agreement_rate_pct": round(100 * stats["top3_hits"] / stats["total"], 1) if stats["total"] else None,
        }
        for cat, stats in sorted(by_category.items())
    }

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_cases": total,
        "errored_cases": len(errored),
        "top1_agreement_rate_pct": round(100 * top1_hits / total, 1) if total else None,
        "top3_agreement_rate_pct": round(100 * top3_hits / total, 1) if total else None,
        "category_breakdown": category_breakdown,
        "mismatches": [r for r in valid_results if not r["top1_hit"]],
        "errors": errored,
    }

    return {"summary": summary, "cases": case_results}


def _print_report(report: dict) -> None:
    summary = report["summary"]
    print("=" * 78)
    print("Wrapture — rules engine evaluation vs. hand-curated reference set")
    print("=" * 78)
    print(
        "NOTE: this measures agreement with our own curated expectations, not\n"
        "scientific/lab-validated correctness. See the module docstring in\n"
        "evaluation/run_evaluation.py for the full disclaimer.\n"
    )
    print(f"Total reference cases : {summary['total_cases']}")
    if summary["errored_cases"]:
        print(f"Errored cases         : {summary['errored_cases']} (stale commodity id — see 'errors')")
    print(f"Top-1 agreement rate  : {summary['top1_agreement_rate_pct']}%")
    print(f"Top-3 agreement rate  : {summary['top3_agreement_rate_pct']}%  (looser: expected material anywhere in top 3)")
    print()
    print("By commodity category:")
    for cat, stats in summary["category_breakdown"].items():
        print(f"  {cat:20s} n={stats['total']:2d}  top1={stats['top1_agreement_rate_pct']:5.1f}%  top3={stats['top3_agreement_rate_pct']:5.1f}%")
    print()

    if summary["mismatches"]:
        print(f"Top-1 mismatches ({len(summary['mismatches'])}):")
        for m in summary["mismatches"]:
            print(f"  [{m['case_id']}] {m['commodity_id']}: expected one of {m['expected_material_ids']}, got '{m['actual_top1_material_id']}'")
            print(f"      top-3 was: {m['actual_top3_material_ids']}" + ("  (top-3 agreement OK)" if m["top3_hit"] else "  (also missed top-3)"))
    else:
        print("No top-1 mismatches.")
    print("=" * 78)


def main() -> None:
    report = run_evaluation()
    _print_report(report)

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nFull results written to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
