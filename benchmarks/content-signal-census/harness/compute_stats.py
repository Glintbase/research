"""E1 statistics. Every number in the report comes from data/summary.json.

Usage: python compute_stats.py
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

STUDY_DIR = Path(__file__).resolve().parent.parent
DATA = STUDY_DIR / "data"
CLASSES = ["none", "robots_only", "header_only", "agree", "conflict"]
KEYS = ("search", "ai-input", "ai-train")


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * (c - h), 1), round(100 * (c + h), 1)]


def prop(k, n):
    return {"k": k, "n": n, "pct": round(100 * k / n, 1) if n else None, "ci95": wilson(k, n)}


def block(rows):
    n = len(rows)
    out = {"n": n, "class": {c: prop(sum(r["class"] == c for r in rows), n) for c in CLASSES}}
    out["any_signal"] = prop(sum(r["class"] != "none" for r in rows), n)
    out["robots_signal"] = prop(sum(bool(r["robots_has_signals"]) for r in rows), n)
    out["header_signal"] = prop(sum(bool(r["header_signals"]) for r in rows), n)
    out["md_served"] = prop(sum(bool(r["md_served"]) for r in rows), n)
    md = [r for r in rows if r["md_served"]]
    out["among_md_served"] = {
        "n": len(md),
        "md_header_present": prop(sum("md" in r["header_signals"] for r in md), len(md)),
        "html_header_present": prop(sum("html" in r["header_signals"] for r in md), len(md)),
        "md_header_differs_from_html": prop(sum(bool(r["md_header_differs_from_html"]) for r in md), len(md)),
        "vary_accept": prop(sum(bool(r["md_vary_accept"]) for r in md), len(md)),
    }
    both = [r for r in rows if r["class"] in ("agree", "conflict")]
    out["conflict_among_both_present"] = prop(sum(r["class"] == "conflict" for r in both), len(both))
    out["ai_train_robots_no_header_yes"] = prop(sum(bool(r["ai_train_conflict_no_yes"]) for r in rows), n)
    return out


def main():
    rows_all = [json.loads(l) for l in (DATA / "sites.jsonl").read_text(encoding="utf8").splitlines() if l.strip()]
    rows = [r for r in rows_all if r.get("reachable")]
    S = {
        "sites_in_sample": len(rows_all),
        "unreachable_or_excluded": len(rows_all) - len(rows),
        "homepage_self_excluded": sum(bool(r.get("home_self_excluded")) for r in rows_all),
        "overall": block(rows),
        "by_source": {},
        "by_cdn": {},
        "robots_policy_values": {k: dict(Counter((r.get("robots_policy") or {}).get(k) for r in rows if (r.get("robots_policy") or {}).get(k))) for k in KEYS},
        "header_values": dict(Counter(v for r in rows for v in r.get("header_values") or []).most_common(20)),
        "header_value_sets": dict(Counter(", ".join(r["header_values"]) for r in rows if r.get("header_values")).most_common(10)),
        "conflict_keys": dict(Counter(k for r in rows for k in r.get("conflict_keys") or [])),
        "named_group_signals_sites": sum(bool(r.get("robots_named_groups")) for r in rows),
        "header_on_md_only": prop(sum(bool(r.get("header_on_md_only")) for r in rows if r["header_signals"]), sum(bool(r["header_signals"]) for r in rows)),
    }
    for src in ("leaderboard", "silent_wall", "tranco"):
        sub = [r for r in rows if src in r["sources"].split("|") and (src != "tranco" or (r["tranco_rank"] and int(r["tranco_rank"]) <= 1000))]
        S["by_source"][src if src != "tranco" else "tranco_top1000"] = block(sub)
    cdn = Counter(r["cdn"] for r in rows)
    for c, k in cdn.most_common():
        sub = [r for r in rows if r["cdn"] == c]
        b = block(sub)
        S["by_cdn"][c] = {"n": k, "header_signal": b["header_signal"], "md_served": b["md_served"],
                          "conflict": b["class"]["conflict"], "small_cell": k < 30}
    # header signal among md-served by CDN (where the Cloudflare default would show)
    S["md_header_by_cdn"] = {c: prop(sum("md" in r["header_signals"] for r in rows if r["cdn"] == c and r["md_served"]),
                                     sum(r["cdn"] == c and r["md_served"] for r in rows)) for c in cdn}
    (DATA / "summary.json").write_text(json.dumps(S, indent=2), encoding="utf8")
    print(json.dumps({k: S[k] for k in ("sites_in_sample", "unreachable_or_excluded", "overall", "conflict_keys", "header_value_sets")}, indent=1))


if __name__ == "__main__":
    main()
