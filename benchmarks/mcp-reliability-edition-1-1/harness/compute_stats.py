"""Edition 1.1 statistics. Every number in the report comes from data/summary.json.

Usage: python compute_stats.py --round 1 [--retest 2]
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY_DIR = HERE.parent
DATA = STUDY_DIR / "data"
ED1_HEADLINE = STUDY_DIR.parent / "production-mcp-reliability-crisis" / "data" / "round_2.jsonl"


def read(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf8").splitlines() if l.strip()]


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (c - h), 1), round(100 * (c + h), 1)


def prop(k: int, n: int) -> dict:
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "pct": round(100 * k / n, 1) if n else None, "ci95": [lo, hi]}


def mcnemar_exact(b: int, c: int) -> float | None:
    n = b + c
    if n == 0:
        return None
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return round(min(1.0, 2 * p), 4)


def kappa(a: list, b: list) -> float | None:
    n = len(a)
    if not n:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n / n
    return round((po - pe) / (1 - pe), 3) if pe < 1 else None


def pctile(vals, q):
    if not vals:
        return None
    s = sorted(vals)
    return s[min(len(s) - 1, int(q * (len(s) - 1) + 0.5))]


def paired(ed1: dict, r1: dict, name: str, include, outcome) -> dict:
    keys = [u for u in ed1 if u in r1 and include(ed1[u]) and include(r1[u])]
    b = sum(outcome(ed1[u]) and not outcome(r1[u]) for u in keys)
    c = sum(not outcome(ed1[u]) and outcome(r1[u]) for u in keys)
    return {"outcome": name, "n_pairs": len(keys),
            "edition1": prop(sum(outcome(ed1[u]) for u in keys), len(keys)),
            "edition1_1": prop(sum(outcome(r1[u]) for u in keys), len(keys)),
            "lost_ed1_yes_now_no": b, "gained_ed1_no_now_yes": c, "mcnemar_exact_p": mcnemar_exact(b, c)}


def analyse(rows: list[dict]) -> dict:
    classified = [r for r in rows if r["primary_status"] != "excluded"]
    n = len(classified)
    status = Counter(r["primary_status"] for r in classified)
    hs = [r for r in classified if r.get("era") in ("modern", "legacy") and r["primary_status"] in ("ok", "handshake_only")]
    ok = [r for r in classified if r["primary_status"] == "ok"]
    ext_rows = [r for r in hs if r.get("extensions") is not None]
    ext_counter = Counter(e for r in ext_rows for e in (r.get("extensions") or []))
    cards = [r for r in classified if "server_card_status" in r]
    tools_rows = [r for r in ok if r.get("tool_count")]
    per_tool_sizes = [s for r in tools_rows for s in (r.get("schema_bytes_per_tool") or [])]
    hosts = Counter(r["host"] for r in classified)
    # host-weighted view: mean of within-host shares
    by_host = defaultdict(list)
    for r in classified:
        by_host[r["host"]].append(r)

    def host_weighted(pred):
        return round(100 * statistics.mean(sum(pred(x) for x in v) / len(v) for v in by_host.values()), 1) if by_host else None

    return {
        "endpoints_total": len(rows),
        "excluded": len(rows) - n,
        "classified": n,
        "distinct_hosts": len(hosts),
        "largest_host_count": hosts.most_common(1)[0][1] if hosts else 0,
        "primary_status": {k: prop(v, n) for k, v in status.most_common()},
        "primary_status_host_weighted_pct": {k: host_weighted(lambda r, k=k: r["primary_status"] == k) for k in status},
        "handshake": {
            "n": len(hs),
            "modern": prop(sum(r["era"] == "modern" for r in hs), len(hs)),
            "dual_era_among_modern": prop(sum(bool(r.get("dual_era")) for r in hs if r["era"] == "modern"), sum(r["era"] == "modern" for r in hs)),
            "protocol_versions_legacy": dict(Counter(r.get("protocol_version") for r in hs if r["era"] == "legacy").most_common()),
        },
        "extensions": {
            "n_handshaken_with_capabilities": len(ext_rows),
            "any_extension": prop(sum(bool(r.get("extensions")) for r in ext_rows), len(ext_rows)),
            "declares_skills": prop(sum(bool(r.get("declares_skills")) for r in ext_rows), len(ext_rows)),
            "skills_list_ok_among_declaring": prop(sum(bool(r.get("skills_list_ok")) for r in ext_rows if r.get("declares_skills")),
                                                   sum(bool(r.get("declares_skills")) for r in ext_rows)),
            "extension_ids": dict(ext_counter.most_common(20)),
        },
        "server_card": {
            "n_fetched": len(cards),
            "skipped": dict(Counter(r.get("server_card_skipped") for r in classified if r.get("server_card_skipped"))),
            "http_200": prop(sum(r.get("server_card_status") == 200 for r in cards), len(cards)),
            "json_object": prop(sum(bool(r.get("server_card_json")) for r in cards), len(cards)),
            "valid_v1": prop(sum(bool(r.get("server_card_valid_v1")) for r in cards), len(cards)),
            "valid_v1_among_ok": prop(sum(bool(r.get("server_card_valid_v1")) for r in ok if "server_card_status" in r),
                                      sum("server_card_status" in r for r in ok)),
            "media_type_among_json": dict(Counter(r.get("server_card_content_type") for r in cards if r.get("server_card_json")).most_common()),
        },
        "tools": {
            "endpoints_with_tools": len(tools_rows),
            "tools_total": sum(r["tool_count"] for r in tools_rows),
            "endpoints_all_tools_annotated": prop(sum(r.get("pct_tools_annotated") == 100.0 for r in tools_rows), len(tools_rows)),
            "endpoints_any_tool_annotated": prop(sum((r.get("pct_tools_annotated") or 0) > 0 for r in tools_rows), len(tools_rows)),
            "tools_annotated_pooled": prop(round(sum(r["tool_count"] * (r.get("pct_tools_annotated") or 0) / 100 for r in tools_rows)),
                                           sum(r["tool_count"] for r in tools_rows)),
            "endpoints_any_output_schema": prop(sum((r.get("pct_tools_output_schema") or 0) > 0 for r in tools_rows), len(tools_rows)),
            "schema_bytes_per_tool": {"n": len(per_tool_sizes), "median": pctile(per_tool_sizes, 0.5),
                                      "p90": pctile(per_tool_sizes, 0.9), "max": max(per_tool_sizes) if per_tool_sizes else None},
            "schema_bytes_per_endpoint_total": {"median": pctile([r["schema_bytes_total"] for r in tools_rows if r.get("schema_bytes_total")], 0.5),
                                                "p90": pctile([r["schema_bytes_total"] for r in tools_rows if r.get("schema_bytes_total")], 0.9)},
            "error_in_channel_among_ok": prop(sum(bool(r.get("error_in_channel")) for r in ok if "error_in_channel" in r),
                                              sum("error_in_channel" in r for r in ok)),
        },
        "max_requests_per_endpoint": max((r.get("requests_sent") or 0) for r in rows),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    ap.add_argument("--retest")
    a = ap.parse_args()
    r1_rows = read(DATA / f"round_{a.round}.jsonl")
    summary = {"round": a.round, "round_stats": analyse(r1_rows)}
    ed1 = {r["url"]: r for r in read(ED1_HEADLINE) if r["primary_status"] != "excluded"}
    r1 = {r["url"]: r for r in r1_rows if r["primary_status"] != "excluded"}
    every = lambda r: True  # noqa: E731
    hs = lambda r: r.get("era") in ("modern", "legacy") and r["primary_status"] in ("ok", "handshake_only")  # noqa: E731
    summary["paired_vs_edition1"] = {
        "edition1_round": "production-mcp-reliability-crisis/data/round_2.jsonl (2026-10-12, headline)",
        "ok": paired(ed1, r1, "ok", every, lambda r: r["primary_status"] == "ok"),
        "modern_era": paired(ed1, r1, "modern era among handshaken in both", hs, lambda r: r.get("era") == "modern"),
        "error_in_channel": paired(ed1, r1, "in-channel canary error", lambda r: "error_in_channel" in r, lambda r: bool(r["error_in_channel"])),
        "auth_compliant": paired(ed1, r1, "auth compliant among auth-gated in both", lambda r: r["primary_status"].startswith("auth_"),
                                 lambda r: r["primary_status"] == "auth_compliant"),
        "unreachable": paired(ed1, r1, "unreachable", every, lambda r: r["primary_status"] == "unreachable"),
        "transitions": {f"{a_} -> {b_}": v for (a_, b_), v in Counter(
            (ed1[u]["primary_status"], r1[u]["primary_status"]) for u in ed1 if u in r1).most_common() if a_ != b_},
    }
    if a.retest:
        r2 = {r["url"]: r for r in read(DATA / f"round_{a.retest}.jsonl") if r["primary_status"] != "excluded"}
        keys = sorted(set(r1) & set(r2))
        s1 = [r1[u]["primary_status"] for u in keys]
        s2 = [r2[u]["primary_status"] for u in keys]
        summary["retest"] = {"round": a.retest, "n": len(keys), "agreement": prop(sum(x == y for x, y in zip(s1, s2)), len(keys)),
                             "cohens_kappa": kappa(s1, s2), "round_stats": analyse(list(r2.values()))}
    (DATA / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf8")
    print(json.dumps({k: summary[k] for k in summary if k != "round_stats"}, indent=1)[:3000])
    rs = summary["round_stats"]
    print(json.dumps({k: rs[k] for k in ("classified", "primary_status", "handshake", "extensions", "server_card")}, indent=1)[:4000])


if __name__ == "__main__":
    main()
