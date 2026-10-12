"""Compute every number reported for the study from data/round_<name>.jsonl.

Usage:
  python compute_stats.py --round 1                 # single round
  python compute_stats.py --round 1 --retest 2      # plus stability (RQ6)

Writes data/summary.json and data/summary.md. The report must only quote numbers from these.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter

from common import DATA_DIR, read_jsonl

STATUS_ORDER = [
    "ok", "handshake_only", "auth_compliant", "auth_noncompliant", "modern_rejected",
    "legacy_sse", "jsonrpc_error", "payment_required", "server_error", "not_mcp", "unreachable",
]


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return None
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [round(100 * max(0.0, centre - half), 1), round(100 * min(1.0, centre + half), 1)]


def prop(k: int, n: int) -> dict:
    return {"k": k, "n": n, "pct": round(100 * k / n, 1) if n else None, "ci95": wilson(k, n)}


def distribution(rows, key, order=None) -> dict:
    n = len(rows)
    c = Counter(r.get(key) for r in rows)
    keys = order or sorted(c, key=lambda k: -c[k])
    return {str(k): prop(c.get(k, 0), n) for k in keys if c.get(k, 0) or order}


def median(vals):
    vals = [v for v in vals if v is not None]
    return statistics.median(vals) if vals else None


def analyse(rows: list[dict]) -> dict:
    s: dict = {}
    s["sample_endpoints"] = len(rows)
    excluded = [r for r in rows if r["primary_status"] == "excluded"]
    a = [r for r in rows if r["primary_status"] != "excluded"]
    s["excluded"] = dict(Counter(r.get("excluded_reason") for r in excluded))
    s["analysed_endpoints"] = len(a)

    # RQ1 — primary status
    s["rq1_primary_status"] = distribution(a, "primary_status", STATUS_ORDER)
    s["rq1_by_transport"] = {
        t: distribution([r for r in a if r.get("transport") == t], "primary_status", STATUS_ORDER)
        for t in sorted({r.get("transport") for r in a})
    }
    reached = [r for r in a if r["primary_status"] != "unreachable"]
    s["rq1_speaks_mcp"] = prop(
        sum(r["primary_status"] in {"ok", "handshake_only", "auth_compliant", "auth_noncompliant", "modern_rejected", "legacy_sse"} for r in a),
        len(a),
    )
    s["rq1_reachable"] = prop(len(reached), len(a))

    # Host clustering: some hosts publish hundreds of endpoints. Sensitivity view where
    # each host counts once (mean of within-host shares).
    by_host: dict[str, list[dict]] = {}
    for r in a:
        by_host.setdefault(r.get("host") or "", []).append(r)
    s["hosts"] = len(by_host)
    s["endpoints_per_host_max"] = max((len(v) for v in by_host.values()), default=0)
    s["top_hosts_share_of_sample"] = {h: len(v) for h, v in sorted(by_host.items(), key=lambda kv: -len(kv[1]))[:10]}
    s["rq1_primary_status_host_weighted_pct"] = {
        st: round(100 * statistics.mean(sum(r["primary_status"] == st for r in v) / len(v) for v in by_host.values()), 1)
        for st in STATUS_ORDER
    } if by_host else {}

    # RQ2 — protocol era/version among completed handshakes
    hs = [r for r in a if r.get("protocol_version") or r.get("supported_versions")]
    s["rq2_handshakes"] = len(hs)
    s["rq2_era"] = distribution(hs, "era")
    legacy = [r for r in hs if r.get("era") == "legacy"]
    s["rq2_legacy_negotiated_version"] = distribution(legacy, "protocol_version")
    s["rq2_modern_supported"] = prop(sum(r.get("era") == "modern" for r in hs), len(hs))
    s["rq2_dual_era_among_modern"] = prop(sum(bool(r.get("dual_era")) for r in hs if r.get("era") == "modern"),
                                          sum(r.get("era") == "modern" for r in hs))
    s["rq2_session_issued_among_legacy"] = prop(sum(bool(r.get("session_issued")) for r in legacy), len(legacy))
    s["rq2_handshake_latency_ms_median"] = median(r.get("handshake_latency_ms") for r in hs)

    # RQ3 — auth challenge compliance
    auth = [r for r in a if r["primary_status"] in {"auth_compliant", "auth_noncompliant"}]
    s["rq3_auth_endpoints"] = prop(len(auth), len(a))
    s["rq3_compliant_among_auth"] = prop(sum(r["primary_status"] == "auth_compliant" for r in auth), len(auth))
    s["rq3_bearer_challenge_among_auth"] = prop(sum(bool(r.get("www_authenticate_bearer")) for r in auth), len(auth))
    s["rq3_prm_valid_among_auth"] = prop(sum(bool(r.get("prm_valid")) for r in auth), len(auth))
    s["rq3_auth_after_anonymous_handshake"] = prop(sum(bool(r.get("auth_after_handshake")) for r in auth), len(auth))

    # RQ4 — tool metadata among endpoints that listed tools
    ok = [r for r in a if r["primary_status"] == "ok"]
    with_tools = [r for r in ok if (r.get("tool_count") or 0) > 0]
    s["rq4_ok_endpoints"] = len(ok)
    s["rq4_zero_tools"] = prop(sum((r.get("tool_count") or 0) == 0 for r in ok), len(ok))
    s["rq4_tool_count_median"] = median(r.get("tool_count") for r in with_tools)
    s["rq4_paginated"] = prop(sum(bool(r.get("tools_paginated")) for r in ok), len(ok))
    s["rq4_all_tools_strict_schema"] = prop(sum(r.get("pct_tools_strict_schema") == 100.0 for r in with_tools), len(with_tools))
    s["rq4_any_readonly_annotation"] = prop(sum((r.get("pct_tools_readonly_declared") or 0) > 0 for r in with_tools), len(with_tools))
    s["rq4_any_destructive_annotation"] = prop(sum((r.get("pct_tools_destructive_declared") or 0) > 0 for r in with_tools), len(with_tools))
    s["rq4_all_tools_described"] = prop(sum(r.get("pct_tools_described") == 100.0 for r in with_tools), len(with_tools))
    s["rq4_mean_pct_strict"] = round(statistics.mean(r["pct_tools_strict_schema"] for r in with_tools), 1) if with_tools else None

    # RQ5 — in-channel error signalling on the unknown-tool canary
    can = [r for r in a if r.get("canary_http_status") is not None]
    s["rq5_canary_answered"] = len(can)
    s["rq5_error_in_channel"] = prop(sum(bool(r.get("error_in_channel")) for r in can), len(can))
    s["rq5_canary_http_status"] = dict(Counter(str(r.get("canary_http_status")) for r in can).most_common())
    return s


def stability(r1: list[dict], r2: list[dict]) -> dict:
    b = {r["url"]: r["primary_status"] for r in r2 if r["primary_status"] != "excluded"}
    pairs = [(r["primary_status"], b[r["url"]]) for r in r1 if r["url"] in b and r["primary_status"] != "excluded"]
    n = len(pairs)
    agree = sum(x == y for x, y in pairs)
    # Cohen's kappa
    c1 = Counter(x for x, _ in pairs)
    c2 = Counter(y for _, y in pairs)
    pe = sum(c1[k] * c2.get(k, 0) for k in c1) / (n * n) if n else 0
    po = agree / n if n else 0
    kappa = round((po - pe) / (1 - pe), 3) if n and pe < 1 else None
    changes = Counter(f"{x} -> {y}" for x, y in pairs if x != y)
    return {"paired": n, "same_status": prop(agree, n), "cohens_kappa": kappa, "top_changes": dict(changes.most_common(10))}


def fmt(p):
    if not isinstance(p, dict) or "pct" not in p:
        return str(p)
    ci = p["ci95"]
    return f"{p['pct']}% ({p['k']}/{p['n']}; 95% CI {ci[0]}–{ci[1]})" if ci else "n/a (n=0)"


def to_markdown(summary: dict) -> str:
    s = summary["round_1"]
    lines = [f"# Summary — {summary['rounds']}", "",
             f"Sample endpoints: {s['sample_endpoints']} · analysed: {s['analysed_endpoints']} · excluded: {s['excluded']}", "",
             "## RQ1 Primary status", "", "| Status | Share |", "|---|---|"]
    lines += [f"| {k} | {fmt(v)} |" for k, v in s["rq1_primary_status"].items()]
    lines += ["", f"Hosts: {s['hosts']} (max {s['endpoints_per_host_max']} endpoints on one host). Host-weighted shares: "
              + ", ".join(f"{k} {v}%" for k, v in s["rq1_primary_status_host_weighted_pct"].items() if v), ""]
    lines += [f"- Reachable: {fmt(s['rq1_reachable'])}", f"- Speaks MCP (any protocol answer or MCP auth challenge): {fmt(s['rq1_speaks_mcp'])}", ""]
    lines += ["## RQ2 Protocol era", "", f"Completed handshakes: {s['rq2_handshakes']}",
              f"- Modern (2026-07-28) support: {fmt(s['rq2_modern_supported'])}",
              f"- Dual-era (modern + legacy) among modern: {fmt(s['rq2_dual_era_among_modern'])}",
              f"- Legacy negotiated versions: " + ", ".join(f"{k}: {fmt(v)}" for k, v in s["rq2_legacy_negotiated_version"].items()),
              f"- Legacy servers issuing sessions: {fmt(s['rq2_session_issued_among_legacy'])}",
              f"- Median handshake latency: {s['rq2_handshake_latency_ms_median']} ms", ""]
    lines += ["## RQ3 Auth", "", f"- Auth-gated endpoints: {fmt(s['rq3_auth_endpoints'])}",
              f"- Compliant challenge (Bearer + RFC 9728 metadata): {fmt(s['rq3_compliant_among_auth'])}",
              f"- Bearer challenge present: {fmt(s['rq3_bearer_challenge_among_auth'])}",
              f"- Valid protected-resource metadata: {fmt(s['rq3_prm_valid_among_auth'])}", ""]
    lines += ["## RQ4 Tools (among `ok` endpoints)", "", f"- `ok` endpoints: {s['rq4_ok_endpoints']}",
              f"- Zero tools listed: {fmt(s['rq4_zero_tools'])}", f"- Median tool count: {s['rq4_tool_count_median']}",
              f"- All tools strictly typed: {fmt(s['rq4_all_tools_strict_schema'])}",
              f"- Any readOnlyHint declared: {fmt(s['rq4_any_readonly_annotation'])}",
              f"- Any destructiveHint declared: {fmt(s['rq4_any_destructive_annotation'])}",
              f"- All tools described: {fmt(s['rq4_all_tools_described'])}", ""]
    lines += ["## RQ5 In-channel errors", "", f"- Canary answered over HTTP: {s['rq5_canary_answered']}",
              f"- Error returned in-channel: {fmt(s['rq5_error_in_channel'])}", ""]
    if "stability" in summary:
        st = summary["stability"]
        lines += ["## RQ6 Re-test reliability (back-to-back rounds; see Deviation 1)", "", f"- Paired endpoints: {st['paired']}",
                  f"- Same primary status: {fmt(st['same_status'])}", f"- Cohen's κ: {st['cohens_kappa']}", ""]
        if "stability_excluding_hosts" in summary:
            sx = summary["stability_excluding_hosts"]
            lines += [f"Excluding {', '.join(sx['excluded_hosts'])}: same status {fmt(sx['same_status'])}, κ {sx['cohens_kappa']}", ""]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    ap.add_argument("--retest")
    ap.add_argument("--sensitivity-exclude-host", action="append", default=[],
                    help="also report stability without these hosts (e.g. a host whose anonymous quota our probing exhausted)")
    a = ap.parse_args()
    r1 = read_jsonl(DATA_DIR / f"round_{a.round}.jsonl")
    summary = {"rounds": f"round {a.round}" + (f" + retest {a.retest}" if a.retest else ""), "round_1": analyse(r1)}
    if a.retest:
        r2 = read_jsonl(DATA_DIR / f"round_{a.retest}.jsonl")
        summary["round_2"] = analyse(r2)
        summary["stability"] = stability(r1, r2)
        if a.sensitivity_exclude_host:
            ex = set(a.sensitivity_exclude_host)
            summary["stability_excluding_hosts"] = {
                "excluded_hosts": sorted(ex),
                **stability([r for r in r1 if r.get("host") not in ex], [r for r in r2 if r.get("host") not in ex]),
            }
    (DATA_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf8")
    md = to_markdown(summary)
    (DATA_DIR / "summary.md").write_text(md, encoding="utf8")
    print(md)


if __name__ == "__main__":
    main()
