"""Descriptive breakdowns for the E1 report, beyond the pre-registered tables in summary.json.

Reads data/sites.jsonl (derived per-site fields) and writes data/descriptives.json. Every number
here is a count or share over reachable sites; nothing is re-classified. These tables are labelled
"descriptive, not pre-registered" in the report.

    python harness/descriptives.py
"""
import json
import math
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
Z = 1.959964


def wilson(k, n):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return [round(100 * (c - h), 1), round(100 * (c + h), 1)]


def share(k, n):
    return {"k": k, "n": n, "pct": round(100 * k / n, 1) if n else None, "ci95": wilson(k, n)}


def policy_str(p):
    return ", ".join(f"{k}={v}" for k, v in sorted(p.items())) if p else ""


def main():
    rows = [json.loads(l) for l in (DATA / "sites.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    reach = [r for r in rows if r["reachable"]]
    n = len(reach)
    signal = [r for r in reach if r["class"] != "none"]
    robots = [r for r in reach if r["robots_has_signals"]]
    header = [r for r in reach if r["header_values"]]
    md = [r for r in reach if r["md_served"]]
    out = {"n_reachable": n}

    # robots.txt: is there a file at all?
    out["robots_txt_status"] = {
        "served_200": share(sum(1 for r in reach if r.get("robots_status") == 200), n),
        "not_found_404": share(sum(1 for r in reach if r.get("robots_status") == 404), n),
    }

    # Full robots policies (the * group), as stated.
    out["robots_policy_sets"] = dict(Counter(policy_str(r["robots_policy"]) for r in robots if r["robots_policy"]).most_common())
    out["robots_signals_named_groups_only"] = sum(1 for r in robots if not r["robots_policy"])
    train_no = [r for r in reach if r["robots_policy"].get("ai-train") == "no"]
    out["robots_ai_train_no"] = {
        "share": share(len(train_no), n),
        "also_ai_input_yes": sum(1 for r in train_no if r["robots_policy"].get("ai-input") == "yes"),
        "also_search_yes": sum(1 for r in train_no if r["robots_policy"].get("search") == "yes"),
        "sites": sorted(r["site"] for r in train_no),
    }

    # Named user-agent groups carrying Content-Signal lines.
    # Each group is {"agents": [...], "signals": {...}}; count sites per agent token and value.
    named_sites = [r for r in reach if r.get("robots_named_groups")]
    per_agent = {}
    for r in named_sites:
        seen = {}
        for g in r["robots_named_groups"]:
            for ua in g["agents"]:
                seen[ua] = policy_str(g["signals"])
        for ua, pol in seen.items():
            per_agent.setdefault(ua, Counter())[pol] += 1
    out["named_groups"] = {
        "sites": len(named_sites),
        "sites_with_any_no": sum(1 for r in named_sites if any("no" in g["signals"].values() for g in r["robots_named_groups"])),
        "sites_with_different_policies_per_bot": sum(
            1 for r in named_sites if len({policy_str(g["signals"]) for g in r["robots_named_groups"]}) > 1
        ),
        "agents": {ua: dict(c) for ua, c in sorted(per_agent.items(), key=lambda kv: -sum(kv[1].values()))},
    }
    out["robots_path_scoped_sites"] = sum(1 for r in robots if any(k.startswith("/") for k in r["robots_policy"]))
    out["robots_nonstandard_keys"] = dict(
        Counter(k for r in robots for k in r["robots_policy"] if k not in ("search", "ai-input", "ai-train") and not k.startswith("/"))
    )

    # Headers: where they appear and on which CDN.
    out["header"] = {
        "sites": len(header),
        "on_markdown_only": sum(1 for r in header if r["header_on_md_only"]),
        "cdn": dict(Counter(r["cdn"] for r in header).most_common()),
        "value_sets": dict(Counter(", ".join(sorted(r["header_values"])) for r in header).most_common()),
    }

    # Markdown serving.
    out["markdown"] = {
        "served": share(len(md), n),
        "vary_accept_when_served": share(sum(1 for r in md if r["md_vary_accept"]), len(md)),
        "twin_advertised": share(sum(1 for r in reach if r["md_twin_advertised"]), n),
        "docs_markdown_served_sites": sum(1 for r in reach if (r.get("docs_md_served") or 0) > 0),
        "served_by_cdn": dict(Counter(r["cdn"] for r in md).most_common()),
        "served_without_header": sum(1 for r in md if not r["header_values"]),
    }

    # Popularity bands within the Tranco top 1,000.
    bands = {"1-100": (1, 100), "101-500": (101, 500), "501-1000": (501, 1000)}
    tr = [r for r in reach if r.get("tranco_rank")]
    out["tranco_bands"] = {}
    for name, (lo, hi) in bands.items():
        b = [r for r in tr if lo <= int(r["tranco_rank"]) <= hi]
        out["tranco_bands"][name] = {
            "any_signal": share(sum(1 for r in b if r["class"] != "none"), len(b)),
            "robots_signal": share(sum(1 for r in b if r["robots_has_signals"]), len(b)),
            "header_signal": share(sum(1 for r in b if r["header_values"]), len(b)),
        }

    # Leaderboard sites that state a signal: public facts only (robots file, public headers).
    lb = [r for r in signal if "leaderboard" in r["sources"]]
    out["leaderboard_signal_sites"] = [
        {
            "site": r["site"],
            "robots_policy": policy_str(r["robots_policy"]),
            "header": ", ".join(sorted(r["header_values"])),
            "markdown_served": r["md_served"],
            "cdn": r["cdn"],
        }
        for r in sorted(lb, key=lambda r: r["site"])
        if r["class"] != "conflict"  # the one conflict site is not named (see report §4)
    ]
    out["leaderboard_conflict_sites_not_named"] = sum(1 for r in lb if r["class"] == "conflict")

    (DATA / "descriptives.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2)[:6000])


if __name__ == "__main__":
    main()
