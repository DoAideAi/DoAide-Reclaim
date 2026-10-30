"""The hit-rate report: do enough families find something, and do finders share it?

The proposed decision rule (docs/HIT_RATE_TEST.md): GO to phase 2 when at least TARGET families
have searched, at least MIN_HIT_RATE of them found something, and at least MIN_SHARE_RATE of the
finders shared their card. With 20 families every rate is directional; the Wilson interval says by
how much.
"""
from __future__ import annotations

import math
import statistics
from collections import Counter
from typing import Dict, List, Optional, Tuple

from . import portals
from .money import format_inr

TARGET = 20
MIN_HIT_RATE = 0.10
MIN_SHARE_RATE = 0.30


def wilson(hits: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """95% Wilson score interval for hits/n; honest at small n where p +/- 2se is not."""
    if n == 0:
        return 0.0, 0.0
    p = hits / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def _rate(k: int, n: int) -> Optional[float]:
    return k / n if n else None


def summarize(
    cases: List[dict],
    target: int = TARGET,
    min_hit_rate: float = MIN_HIT_RATE,
    min_share_rate: float = MIN_SHARE_RATE,
) -> Dict[str, object]:
    searched = [c for c in cases if any(r["status"] in ("found", "not_found") for r in c["results"])]
    hit_cases = [c for c in searched if any(r["status"] == "found" for r in c["results"])]
    finds = [r for c in cases for r in c["results"] if r["status"] == "found"]
    with_amount = [r for r in finds if r["amount"]]
    family_totals = [sum(r["amount"] or 0 for r in c["results"] if r["status"] == "found") for c in hit_cases]
    known_totals = [t for t in family_totals if t > 0]
    shared = [c for c in hit_cases if (c.get("card") or {}).get("shared") is True]
    done = [c for c in cases if c.get("done")]
    minutes = [c["done"]["minutes"] for c in done if c["done"].get("minutes")]

    per_portal = {}
    for portal in portals.PORTALS:
        rows = [r for c in cases for r in c["results"] if r["portal"] == portal["id"]]
        looked = [r for r in rows if r["status"] in ("found", "not_found")]
        found = [r for r in rows if r["status"] == "found"]
        blocked = Counter(r["reason"] for r in rows if r["status"] == "blocked")
        per_portal[portal["id"]] = {
            "searched": len(looked),
            "found": len(found),
            "hit_rate": _rate(len(found), len(looked)),
            "rupees": sum(r["amount"] or 0 for r in found),
            "blocked": dict(blocked),
        }

    hit_rate = _rate(len(hit_cases), len(searched))
    share_rate = _rate(len(shared), len(hit_cases))
    failed = []
    if len(searched) < target:
        verdict = f"INCOMPLETE: {len(searched)} of {target} families have searched"
    else:
        if (hit_rate or 0) < min_hit_rate:
            failed.append(f"family hit rate below {min_hit_rate:.0%}")
        if hit_cases and (share_rate or 0) < min_share_rate:
            failed.append(f"share rate below {min_share_rate:.0%}")
        verdict = "GO to phase 2 (claim packets)" if not failed else "NOT YET: " + "; ".join(failed)

    return {
        "cases": len(cases),
        "searched": len(searched),
        "done": len(done),
        "hit_families": len(hit_cases),
        "hit_rate": hit_rate,
        "hit_rate_95": wilson(len(hit_cases), len(searched)),
        "finds": len(finds),
        "finds_with_amount": len(with_amount),
        "rupees_found": sum(r["amount"] for r in with_amount),
        "median_family_rupees": statistics.median(known_totals) if known_totals else None,
        "max_family_rupees": max(known_totals) if known_totals else None,
        "shared": len(shared),
        "share_rate": share_rate,
        "median_minutes": statistics.median(minutes) if minutes else None,
        "portals": per_portal,
        "verdict": verdict,
        "rule": {"target": target, "min_hit_rate": min_hit_rate, "min_share_rate": min_share_rate},
    }


def _pct(value: Optional[float]) -> str:
    return "n/a" if value is None else f"{value:.0%}"


def render(summary: Dict[str, object]) -> str:
    s = summary
    low, high = s["hit_rate_95"]
    lines = [
        f"Families: {s['cases']} enrolled, {s['searched']} searched, {s['done']} finished",
        f"Family hit rate: {s['hit_families']}/{s['searched']} = {_pct(s['hit_rate'])}"
        + (f"  (95% interval {low:.0%} to {high:.0%})" if s["searched"] else ""),
        f"Finds: {s['finds']}, of which {s['finds_with_amount']} came with an amount"
        + (f" ({format_inr(s['rupees_found'])} in total)" if s["rupees_found"] else ""),
    ]
    if s["median_family_rupees"] is not None:
        lines.append(
            f"Per finding family with an amount: median {format_inr(s['median_family_rupees'])}, "
            f"max {format_inr(s['max_family_rupees'])}"
        )
    lines.append(f"Cards shared: {s['shared']}/{s['hit_families']} finding families = {_pct(s['share_rate'])}")
    if s["median_minutes"] is not None:
        lines.append(f"Median minutes per finished family: {s['median_minutes']:g}")
    lines.append("")
    lines.append(f"{'portal':<10}{'searched':>9}{'found':>7}{'hit':>7}  blocked")
    for portal_id, row in s["portals"].items():
        blocked = ", ".join(f"{k} {v}" for k, v in sorted(row["blocked"].items())) or "-"
        lines.append(
            f"{portal_id:<10}{row['searched']:>9}{row['found']:>7}{_pct(row['hit_rate']):>7}  {blocked}"
        )
    lines.append("")
    rule = s["rule"]
    lines.append(
        f"Verdict: {s['verdict']}  (rule: {rule['target']} families, hit rate >= "
        f"{rule['min_hit_rate']:.0%}, share rate >= {rule['min_share_rate']:.0%})"
    )
    return "\n".join(lines) + "\n"
