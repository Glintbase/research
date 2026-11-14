"""E3 statistics. Every number in the report comes from data/summary.json.

Usage: python compute_stats.py
"""

from __future__ import annotations

import json
import math
from collections import Counter
from itertools import combinations
from pathlib import Path

STUDY_DIR = Path(__file__).resolve().parent.parent
DATA = STUDY_DIR / "data"
FILES = ["ai_catalog", "ard", "api_catalog", "poppy", "agent_card", "sig_directory", "llms_txt", "sitemap"]
OUTCOMES = ["valid", "invalid", "soft_404", "absent", "error", "self_excluded"]


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * (c - h), 2), round(100 * (c + h), 2)]


def prop(k, n):
    return {"k": k, "n": n, "pct": round(100 * k / n, 2) if n else None, "ci95": wilson(k, n)}


def per_file(rows):
    out = {}
    n = len(rows)
    for f in FILES:
        oc = Counter(r["files"][f]["outcome"] for r in rows)
        valid = [r for r in rows if r["files"][f]["outcome"] == "valid"]
        served200 = [r for r in rows if r["files"][f]["outcome"] in ("valid", "invalid", "soft_404")]
        out[f] = {"outcomes": {o: prop(oc.get(o, 0), n) for o in OUTCOMES},
                  "soft_404_among_200": prop(oc.get("soft_404", 0), len(served200)),
                  "media_type_ok_among_valid": prop(sum(r["files"][f]["media_type_ok"] for r in valid), len(valid)),
                  "content_types_valid": dict(Counter(r["files"][f]["content_type"] for r in valid).most_common(5))}
    return out


def main():
    rows_all = [json.loads(l) for l in (DATA / "sites.jsonl").read_text(encoding="utf8").splitlines() if l.strip()]
    rows = [r for r in rows_all if r.get("reachable") and "files" in r]
    S = {"sites_in_sample": len(rows_all), "reachable": len(rows), "unreachable_or_excluded": len(rows_all) - len(rows),
         "catch_all_wk": prop(sum(r["catch_all"] for r in rows), len(rows)),
         "catch_all_root": prop(sum(r["catch_all_root"] for r in rows), len(rows)),
         "overall": per_file(rows), "by_source": {}}

    def src(r, name):
        s = r["sources"].split("|")
        rank = int(r["tranco_rank"]) if r["tranco_rank"] else None
        return {"tranco_top1000": rank is not None and rank <= 1000,
                "tranco_1001_5000": rank is not None and rank > 1000,
                "leaderboard": "leaderboard" in s, "mcp_registry": "mcp_registry" in s}[name]

    for name in ("tranco_top1000", "tranco_1001_5000", "leaderboard", "mcp_registry"):
        sub = [r for r in rows if src(r, name)]
        S["by_source"][name] = {"n": len(sub), "valid": {f: prop(sum(r["files"][f]["outcome"] == "valid" for r in sub), len(sub)) for f in FILES}}
    agent_files = ["ai_catalog", "ard", "api_catalog", "poppy", "agent_card", "sig_directory"]
    S["any_agent_discovery_file_valid"] = prop(sum(any(r["files"][f]["outcome"] == "valid" for f in agent_files) for r in rows), len(rows))
    S["count_valid_agent_files"] = dict(Counter(sum(r["files"][f]["outcome"] == "valid" for f in agent_files) for r in rows))
    S["cooccurrence_valid"] = {f"{a}+{b}": sum(r["files"][a]["outcome"] == "valid" and r["files"][b]["outcome"] == "valid" for r in rows)
                               for a, b in combinations(FILES, 2)}
    S["link_header"] = {"rel_ard": prop(sum(bool(r.get("link_rel_ard")) for r in rows), len(rows)),
                        "describedby": prop(sum(bool(r.get("link_describedby")) for r in rows), len(rows)),
                        "md_alternate": prop(sum(bool(r.get("link_md_alternate")) for r in rows), len(rows))}
    S["ard_link_targets"] = dict(Counter(r["ard_link_target"]["outcome"] for r in rows if r.get("ard_link_target")))
    cl = [r["catalog_link"] for r in rows if r.get("catalog_link")]
    S["catalog_cross_links"] = {"fetched": len(cl), "json_object": sum(c["json_object"] for c in cl),
                                "server_card_valid_v1": sum(c["server_card_valid_v1"] for c in cl)}
    S["ai_catalog_entry_types"] = dict(Counter(t for r in rows for t in r.get("ai_catalog_entry_types") or []).most_common(10))
    S["ard_top_keys"] = dict(Counter(k for r in rows for k in r.get("ard_top_keys") or []).most_common(15))

    # Exploratory, not pre-registered: one operator's template cluster counted as a single site
    # (the alphabetically first member stays, the others are dropped). The list was built after the
    # census by grouping identical api-catalog documents (web-census-crawler/data/e3_template_cluster_api_catalog.json).
    cluster_path = STUDY_DIR.parent / "web-census-crawler" / "data" / "e3_template_cluster_api_catalog.json"
    if cluster_path.exists():
        cluster = sorted(json.loads(cluster_path.read_text(encoding="utf8")))
        drop = set(cluster[1:])
        once = [r for r in rows if r["site"] not in drop]
        mcp_once = [r for r in once if src(r, "mcp_registry")]
        S["exploratory_operator_counted_once"] = {
            "note": "Exploratory, not pre-registered. One operator's template cluster counted as one site.",
            "cluster_sites": len(cluster),
            "cluster_reachable": sum(r["site"] in set(cluster) for r in rows),
            "cluster_with_valid_api_catalog": sum(r["site"] in set(cluster) and r["files"]["api_catalog"]["outcome"] == "valid" for r in rows),
            "cluster_with_link_describedby": sum(r["site"] in set(cluster) and bool(r.get("link_describedby")) for r in rows),
            "all_sites": {"n": len(once), "valid": {f: prop(sum(r["files"][f]["outcome"] == "valid" for r in once), len(once)) for f in FILES},
                          "any_agent_discovery_file_valid": prop(sum(any(r["files"][f]["outcome"] == "valid" for f in agent_files) for r in once), len(once)),
                          "link_describedby": prop(sum(bool(r.get("link_describedby")) for r in once), len(once))},
            "mcp_registry": {"n": len(mcp_once), "valid": {f: prop(sum(r["files"][f]["outcome"] == "valid" for r in mcp_once), len(mcp_once)) for f in FILES}},
        }
    (DATA / "summary.json").write_text(json.dumps(S, indent=2), encoding="utf8")
    print(json.dumps({"reachable": S["reachable"], "catch_all_wk": S["catch_all_wk"],
                      "valid": {f: S["overall"][f]["outcomes"]["valid"]["k"] for f in FILES},
                      "soft404": {f: S["overall"][f]["outcomes"]["soft_404"]["k"] for f in FILES}}, indent=1))


if __name__ == "__main__":
    main()
