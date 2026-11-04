"""E1: derive per-site Content-Signal fields from the shared crawl (pre-registration §4–5).

Usage: python analyze.py   -> data/sites.jsonl, data/sites.csv
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY_DIR = HERE.parent
BENCH = STUDY_DIR.parent
CRAWL_RAW = BENCH / "web-census-crawler" / "data" / "raw"
SAMPLE = BENCH / "web-census-crawler" / "data" / "sample.csv"
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("sw_analyze", BENCH / "the-silent-wall" / "harness" / "analyze.py")
_sw = importlib.util.module_from_spec(_spec)
sys.path.insert(0, str(BENCH / "the-silent-wall" / "harness"))
_spec.loader.exec_module(_sw)
vendor_of = _sw.vendor_of  # The Silent Wall's CDN rules

KEYS = ("search", "ai-input", "ai-train")
LINE = re.compile(r"^\s*([A-Za-z-]+)\s*:\s*(.*?)\s*$")


def parse_signal(value: str | None) -> dict:
    """'search=yes, ai-train=no' -> {'search': 'yes', 'ai-train': 'no'} (keys lower-cased)."""
    out = {}
    if not value:
        return out
    for part in re.split(r"[,|]", value):
        if "=" in part:
            k, v = part.split("=", 1)
            k, v = k.strip().lower(), v.strip().lower().strip('"')
            if k:
                out[k] = v
    return out


def robots_signals(text: str) -> dict:
    """Content-Signal lines per user-agent group. Returns {'groups': [{'agents': [...], 'signals': {...}}], 'global': {...}}."""
    groups, cur, in_agents, glob = [], None, False, {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0]
        m = LINE.match(line)
        if not m:
            continue
        field, value = m.group(1).lower(), m.group(2)
        if field == "user-agent":
            if not in_agents:
                cur = {"agents": [], "signals": {}}
                groups.append(cur)
                in_agents = True
            cur["agents"].append(value.strip().lower())
            continue
        in_agents = False
        if field == "content-signal":
            sig = parse_signal(value)
            if cur is None:
                glob.update(sig)
            else:
                cur["signals"].update(sig)
    return {"groups": [g for g in groups if g["signals"]], "global": glob}


def robots_policy(rs: dict) -> dict:
    for g in rs["groups"]:
        if "*" in g["agents"]:
            return g["signals"]
    return rs["global"]


def derive(rec: dict) -> dict:
    reqs = {}
    for r in rec["requests"]:
        reqs.setdefault(r["step"], []).append(r)
    first = lambda s: (reqs.get(s) or [{}])[0]  # noqa: E731
    robots, home, md = first("robots"), first("home_html"), first("home_md")
    row = {"site": rec["site"], "reachable": "status" in home, "home_status": home.get("status"),
           "home_error": home.get("error"), "home_self_excluded": bool(home.get("self_excluded"))}
    text = robots.get("body") if robots.get("status") == 200 else ""
    if text and ("html" in robots.get("headers", {}).get("content-type", "").lower()
                 or text.lstrip().lower().startswith(("<!doctype", "<html"))):
        text = ""
    rs = robots_signals(text or "")
    pol = robots_policy(rs)
    row["robots_status"] = robots.get("status")
    row["robots_has_signals"] = bool(rs["groups"] or rs["global"])
    row["robots_policy"] = pol
    row["robots_named_groups"] = [{"agents": g["agents"], "signals": g["signals"]} for g in rs["groups"] if "*" not in g["agents"]]

    headers = {}
    for step, label in (("home_html", "html"), ("home_md", "md"), ("md_twin", "md_twin"), ("docs_html", "docs_html"), ("docs_md", "docs_md")):
        for i, r in enumerate(reqs.get(step, [])):
            v = r.get("headers", {}).get("content-signal")
            if v:
                headers[f"{label}{i if step.startswith('docs') else ''}"] = parse_signal(v)
    row["header_signals"] = headers
    ct = md.get("headers", {}).get("content-type", "").lower()
    row["md_requested"] = bool(md)
    row["md_served"] = bool(md.get("status") and 200 <= md["status"] < 300 and ct.startswith(("text/markdown", "text/x-markdown")))
    row["md_vary_accept"] = "accept" in md.get("headers", {}).get("vary", "").lower()
    row["md_twin_advertised"] = "md_twin" in reqs
    row["docs_pages"] = len(reqs.get("docs_html", []))
    row["docs_md_served"] = sum(bool(r.get("status") and 200 <= r["status"] < 300 and r.get("headers", {}).get("content-type", "").lower().startswith(("text/markdown", "text/x-markdown"))) for r in reqs.get("docs_md", []))
    row["cdn"] = vendor_of([r for r in rec["requests"] if r.get("headers")])

    has_r, has_h = bool(pol) or row["robots_has_signals"], bool(headers)
    conflict_keys = set()
    for h in headers.values():
        for k, v in h.items():
            if k in pol and pol[k] != v:
                conflict_keys.add(k)
    hv = list(headers.values())
    for i in range(len(hv)):
        for j in range(i + 1, len(hv)):
            for k in set(hv[i]) & set(hv[j]):
                if hv[i][k] != hv[j][k]:
                    conflict_keys.add(k)
    if not has_r and not has_h:
        cls = "none"
    elif has_r and not has_h:
        cls = "robots_only"
    elif has_h and not has_r:
        cls = "conflict" if conflict_keys else "header_only"
    else:
        cls = "conflict" if conflict_keys else "agree"
    row["class"] = cls
    row["conflict_keys"] = sorted(conflict_keys)
    row["ai_train_conflict_no_yes"] = pol.get("ai-train") == "no" and any(h.get("ai-train") == "yes" for h in headers.values())
    row["md_header_differs_from_html"] = ("md" in headers or "html" in headers) and row["md_served"] and headers.get("md") != headers.get("html")
    row["header_on_md_only"] = bool(headers) and all(k.startswith(("md", "docs_md")) for k in headers)
    row["header_values"] = sorted({f"{k}={v}" for h in headers.values() for k, v in h.items()})
    return row


def main():
    with open(SAMPLE, encoding="utf8") as f:
        sample = {r["site"]: r for r in csv.DictReader(f) if r["in_e1"] == "1"}
    rows, missing = [], []
    for site, s in sample.items():
        p = CRAWL_RAW / f"{site}.json"
        if not p.exists():
            missing.append(site)
            continue
        rec = json.loads(p.read_text(encoding="utf8"))
        if "requests" not in rec:
            rows.append({"site": site, "reachable": False, "excluded": rec.get("excluded") or "crawler_error"})
            continue
        row = derive(rec)
        row["sources"] = s["sources"]
        row["tranco_rank"] = s["tranco_rank"]
        rows.append(row)
    rows.sort(key=lambda r: r["site"])
    out = STUDY_DIR / "data" / "sites.jsonl"
    with open(out, "w", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    flat = ["site", "sources", "tranco_rank", "reachable", "home_status", "cdn", "class", "robots_has_signals",
            "md_served", "md_vary_accept", "md_twin_advertised", "ai_train_conflict_no_yes", "md_header_differs_from_html",
            "header_on_md_only"]
    with open(STUDY_DIR / "data" / "sites.csv", "w", encoding="utf8", newline="") as f:
        w = csv.writer(f)
        w.writerow(flat + ["robots_policy", "header_values", "conflict_keys"])
        for r in rows:
            w.writerow([r.get(k, "") for k in flat] + [
                ";".join(f"{k}={v}" for k, v in sorted((r.get("robots_policy") or {}).items())),
                ";".join(r.get("header_values") or []), ";".join(r.get("conflict_keys") or [])])
    counts = {}
    for r in rows:
        counts[r.get("class", "unreachable")] = counts.get(r.get("class", "unreachable"), 0) + 1
    print(f"{len(rows)} sites ({len(missing)} not crawled yet) -> {out.name}: {counts}")


if __name__ == "__main__":
    main()
