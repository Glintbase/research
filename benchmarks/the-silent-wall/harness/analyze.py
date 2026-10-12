"""Classify edge results and compute every number reported for The Silent Wall.

Usage: python analyze.py --round 1 [--retest 2]
Writes data/edge_round_<r>.jsonl (per domain × identity), data/summary.json, data/summary.md
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict

from common import DATA_DIR, EDGE_DIR, ROBOTS_DIR, TOKENS, read_jsonl, write_jsonl

CHALLENGE_MARKERS = {"cloudflare_challenge", "akamai_challenge", "datadome", "human_perimeterx", "imperva",
                     "aws_waf", "kasada", "captcha_widget"}
BLOCK_MARKERS = {"cloudflare_block", "akamai_block"}
SEVERITY = ["block", "challenge", "rate_limited", "error", "thin", "other", "ok", "self_excluded"]
IDENTS = ["agent", "script", "browser"]


def classify_request(r: dict) -> str:
    if r.get("self_excluded"):
        return "self_excluded"
    if r.get("error"):
        return "error"
    st = r.get("status") or 0
    h = r.get("headers", {})
    m = set(r.get("markers", []))
    text = r.get("text_len") or 0
    if (h.get("cf-mitigated", "").lower() == "challenge"
            or h.get("x-amzn-waf-action", "").lower() in {"challenge", "captcha"}
            or h.get("x-vercel-mitigated", "").lower() == "challenge"):
        return "challenge"
    if m & CHALLENGE_MARKERS and (not 200 <= st < 300 or text < 2000):
        return "challenge"
    if st in (401, 403, 406, 451):
        return "block"
    if 200 <= st < 300 and m & BLOCK_MARKERS and text < 2000:
        return "block"
    if st == 429:
        return "rate_limited"
    if st >= 500:
        return "error"
    if 200 <= st < 300:
        return "ok" if text >= 200 else "thin"
    return "other"


def vendor_of(reqs: list[dict]) -> str:
    seen = Counter()
    for r in reqs:
        h = r.get("headers", {})
        server = h.get("server", "").lower()
        if "cf-ray" in h or server == "cloudflare":
            seen["cloudflare"] += 1
        elif "akamai-grn" in h or "akamaighost" in server or "x-akamai-transformed" in h:
            seen["akamai"] += 1
        elif "x-amz-cf-id" in h:
            seen["cloudfront"] += 1
        elif "x-datadome" in h:
            seen["datadome"] += 1
        elif "x-iinfo" in h or "imperva" in h.get("x-cdn", "").lower():
            seen["imperva"] += 1
        elif "x-vercel-id" in h or server == "vercel":
            seen["vercel"] += 1
        elif h.get("x-served-by", "").startswith("cache-") or "fastly" in h.get("via", "").lower():
            seen["fastly"] += 1
        elif "x-azure-ref" in h:
            seen["azure"] += 1
    return seen.most_common(1)[0][0] if seen else "other/unknown"


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * max(0, c - hw), 1), round(100 * min(1, c + hw), 1)]


def prop(k, n):
    return {"k": k, "n": n, "pct": round(100 * k / n, 1) if n else None, "ci95": wilson(k, n)}


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value from discordant counts b, c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return round(min(1.0, 2 * tail), 4)


def build_round(rnd: str) -> list[dict]:
    rows = []
    for p in sorted((EDGE_DIR / f"round_{rnd}").glob("*.json")):
        if p.name.startswith("_"):
            continue
        d = json.loads(p.read_text(encoding="utf8"))
        all_reqs = [r for i in d["identities"] for r in i["requests"]]
        vendor = vendor_of(all_reqs)
        for ident in d["identities"]:
            reqs = ident["requests"]
            outcomes = [classify_request(r) for r in reqs]
            fetched = [o for o in outcomes if o != "self_excluded"]
            worst = min(fetched, key=SEVERITY.index) if fetched else "self_excluded"
            home = reqs[0]
            rows.append({
                "domain": d["domain"], "sector": d["sector"], "round": rnd, "identity": ident["identity"],
                "order": ident["order"], "vendor": vendor, "home_outcome": outcomes[0], "worst_outcome": worst,
                "page_outcomes": outcomes, "home_status": home.get("status"), "home_error": home.get("error"),
                "home_markers": home.get("markers"), "home_text_len": home.get("text_len"),
            })
    return rows


def analyse(rows: list[dict], census: dict) -> dict:
    s: dict = {}
    by = defaultdict(dict)
    for r in rows:
        by[r["domain"]][r["identity"]] = r
    domains = sorted(by)
    s["domains"] = len(domains)
    blocked = lambda o: o in ("challenge", "block")  # noqa: E731

    # RQ2 — outcome distribution per identity (homepage) and "worst page"
    for key in ("home_outcome", "worst_outcome"):
        s[f"rq2_{key}"] = {
            ident: {o: prop(sum(by[d][ident][key] == o for d in domains if ident in by[d]), len(domains)) for o in SEVERITY}
            for ident in IDENTS
        }
    s["rq2_challenged_or_blocked_home"] = {
        ident: prop(sum(blocked(by[d][ident]["home_outcome"]) for d in domains if ident in by[d]), len(domains))
        for ident in IDENTS
    }
    pairs = {}
    for a, b in (("agent", "browser"), ("agent", "script"), ("script", "browser")):
        both = [d for d in domains if a in by[d] and b in by[d]
                and "self_excluded" not in (by[d][a]["home_outcome"], by[d][b]["home_outcome"])
                and "error" not in (by[d][a]["home_outcome"], by[d][b]["home_outcome"])]
        only_a = sum(blocked(by[d][a]["home_outcome"]) and not blocked(by[d][b]["home_outcome"]) for d in both)
        only_b = sum(blocked(by[d][b]["home_outcome"]) and not blocked(by[d][a]["home_outcome"]) for d in both)
        pairs[f"{a}_vs_{b}"] = {"paired_domains": len(both), f"only_{a}_blocked": only_a,
                                f"only_{b}_blocked": only_b, "mcnemar_exact_p": mcnemar_exact(only_a, only_b)}
    s["rq2_paired"] = pairs

    # RQ1 — robots.txt policy
    c = list(census.values())
    readable = [r for r in c if r["robots_status"] is not None]
    s["rq1_robots_fetched"] = prop(len(readable), len(c))
    s["rq1_robots_present"] = prop(sum(r["robots_present"] for r in readable), len(readable))
    s["rq1_tokens"] = {
        tok: {"vendor": v, "purpose": p,
              "named": prop(sum(r["tokens"][tok]["named"] for r in readable), len(readable)),
              "root_disallowed": prop(sum(not r["tokens"][tok]["root_allowed"] for r in readable), len(readable))}
        for tok, (v, p) in TOKENS.items()
    }
    purposes = defaultdict(list)
    for tok, (_, p) in TOKENS.items():
        purposes[p].append(tok)
    s["rq1_any_token_disallowed_by_purpose"] = {
        p: prop(sum(any(not r["tokens"][t]["root_allowed"] for t in toks) for r in readable), len(readable))
        for p, toks in purposes.items()
    }

    # RQ3 — policy allows our agent on "/", but the edge challenges/blocks it
    allowed = [d for d in domains if census.get(d, {}).get("robots_status") is not None
               and census[d]["agent_root_allowed"] and "agent" in by[d]
               and by[d]["agent"]["home_outcome"] not in ("error", "self_excluded")]
    s["rq3_policy_allows_but_edge_blocks_agent"] = prop(sum(blocked(by[d]["agent"]["home_outcome"]) for d in allowed), len(allowed))
    s["rq3_same_but_browser_passes"] = prop(
        sum(blocked(by[d]["agent"]["home_outcome"]) and by[d]["browser"]["home_outcome"] == "ok" for d in allowed), len(allowed))

    # RQ4 — by sector and vendor (agent homepage challenged/blocked)
    for dim in ("sector", "vendor"):
        groups = defaultdict(list)
        for d in domains:
            if "agent" in by[d]:
                groups[by[d]["agent"][dim]].append(d)
        s[f"rq4_by_{dim}"] = {
            g: {ident: prop(sum(blocked(by[d][ident]["home_outcome"]) for d in ds if ident in by[d]), len(ds)) for ident in IDENTS}
            for g, ds in sorted(groups.items())
        }
    s["unreachable_all_identities"] = sorted(d for d in domains if all(by[d][i]["home_outcome"] == "error" for i in IDENTS if i in by[d]))
    return s


def stability(r1, r2):
    idx = {(r["domain"], r["identity"]): r["home_outcome"] for r in r2}
    out = {}
    for ident in IDENTS:
        pairs = [(r["home_outcome"], idx[(r["domain"], ident)]) for r in r1 if r["identity"] == ident and (r["domain"], ident) in idx]
        n = len(pairs)
        agree = sum(a == b for a, b in pairs)
        c1, c2 = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
        pe = sum(c1[k] * c2.get(k, 0) for k in c1) / n / n if n else 0
        po = agree / n if n else 0
        out[ident] = {"same": prop(agree, n), "kappa": round((po - pe) / (1 - pe), 3) if n and pe < 1 else None}
    return out


def fmt(p):
    return f"{p['pct']}% ({p['k']}/{p['n']}; CI {p['ci95'][0]}–{p['ci95'][1]})" if p and p.get("ci95") else "n/a"


def to_md(S):
    s = S["round_1"]
    L = [f"# The Silent Wall — summary ({S['rounds']})", "", f"Domains: {s['domains']}", "",
         "## RQ2 Homepage challenged or blocked, by identity", ""]
    L += [f"- **{i}**: {fmt(s['rq2_challenged_or_blocked_home'][i])}" for i in IDENTS]
    L += ["", "| Outcome (homepage) | agent | script | browser |", "|---|---|---|---|"]
    for o in SEVERITY:
        L.append(f"| {o} | " + " | ".join(fmt(s["rq2_home_outcome"][i][o]) for i in IDENTS) + " |")
    L += ["", "Paired comparisons (homepage challenged/blocked; excluding errors and self-exclusions):", ""]
    L += [f"- {k}: {v}" for k, v in s["rq2_paired"].items()]
    L += ["", "## RQ1 robots.txt", "", f"- robots.txt fetched: {fmt(s['rq1_robots_fetched'])}; present among fetched: {fmt(s['rq1_robots_present'])}", "",
          "| Token | Vendor | Purpose | Named | Disallows `/` |", "|---|---|---|---|---|"]
    for t, v in s["rq1_tokens"].items():
        L.append(f"| {t} | {v['vendor']} | {v['purpose']} | {fmt(v['named'])} | {fmt(v['root_disallowed'])} |")
    L += ["", "Any token of a purpose disallowed at `/`: " + ", ".join(f"{p}: {fmt(v)}" for p, v in s["rq1_any_token_disallowed_by_purpose"].items()), ""]
    L += ["## RQ3 Policy allows, edge blocks", "", f"- Agent challenged/blocked although robots.txt allows it: {fmt(s['rq3_policy_allows_but_edge_blocks_agent'])}",
          f"- …while the headless browser got the page: {fmt(s['rq3_same_but_browser_passes'])}", ""]
    for dim in ("sector", "vendor"):
        L += [f"## RQ4 by {dim} (homepage challenged/blocked)", "", f"| {dim} | n | agent | script | browser |", "|---|---|---|---|---|"]
        for g, v in s[f"rq4_by_{dim}"].items():
            L.append(f"| {g} | {v['agent']['n']} | " + " | ".join(f"{v[i]['pct']}%" for i in IDENTS) + " |")
        L.append("")
    L += [f"Unreachable for every identity: {len(s['unreachable_all_identities'])} domains", ""]
    if "stability" in S:
        L += ["## Stability between rounds", ""] + [f"- {i}: {fmt(v['same'])}, κ={v['kappa']}" for i, v in S["stability"].items()]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    ap.add_argument("--retest")
    a = ap.parse_args()
    census = {r["domain"]: r for r in read_jsonl(ROBOTS_DIR / "census.jsonl")}
    r1 = build_round(a.round)
    write_jsonl(DATA_DIR / f"edge_round_{a.round}.jsonl", r1)
    S = {"rounds": f"round {a.round}" + (f" + {a.retest}" if a.retest else ""), "round_1": analyse(r1, census)}
    if a.retest:
        r2 = build_round(a.retest)
        write_jsonl(DATA_DIR / f"edge_round_{a.retest}.jsonl", r2)
        S["round_2"] = analyse(r2, census)
        S["stability"] = stability(r1, r2)
    (DATA_DIR / "summary.json").write_text(json.dumps(S, indent=2), encoding="utf8")
    md = to_md(S)
    (DATA_DIR / "summary.md").write_text(md, encoding="utf8")
    print(md)


if __name__ == "__main__":
    main()
