"""E3: classify each front-door file per site from the shared crawl (pre-registration §4).

Usage: python analyze.py   -> data/sites.jsonl (one row per site, with per-file outcomes), data/files.csv
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY_DIR = HERE.parent
BENCH = STUDY_DIR.parent
CRAWL_RAW = BENCH / "web-census-crawler" / "data" / "raw"
SAMPLE = BENCH / "web-census-crawler" / "data" / "sample.csv"

FILES = {  # step -> (name, kind, expected media types)
    "wk_ai_catalog": ("ai_catalog", "json", ("application/ai-catalog+json",)),
    "wk_ard": ("ard", "json", ("application/ard+json",)),
    "wk_api_catalog": ("api_catalog", "json", ("application/linkset+json",)),
    "wk_poppy": ("poppy", "json", ("application/json",)),
    "wk_agent_card": ("agent_card", "json", ("application/json",)),
    "wk_sig_directory": ("sig_directory", "json", ("application/http-message-signatures-directory+json",)),
    "llms_txt": ("llms_txt", "text", ("text/plain", "text/markdown")),
    "sitemap": ("sitemap", "xml", ("application/xml", "text/xml")),
}
HTMLISH = re.compile(r"^\s*(<!doctype html|<html|<head|<body|<script)", re.I)


def load_json(body: str | None):
    if not body:
        return None
    try:
        return json.loads(body.lstrip("﻿"))
    except ValueError:
        return None


def valid(name: str, body: str | None, site: str) -> tuple[bool, list[str]]:
    body = body or ""
    if name in ("ai_catalog", "ard", "api_catalog", "poppy", "agent_card", "sig_directory"):
        d = load_json(body)
        if not isinstance(d, dict):
            return False, ["not a JSON object"]
        p = []
        if name == "ai_catalog":
            e = d.get("entries")
            if not isinstance(e, list):
                p.append("entries")
            elif not all(isinstance(x, dict) and isinstance(x.get("type"), str) and (isinstance(x.get("url"), str) or isinstance(x.get("data"), dict)) for x in e):
                p.append("entry shape")
        elif name == "api_catalog":
            if not isinstance(d.get("linkset"), list):
                p.append("linkset")
        elif name == "poppy":
            if not (isinstance(d.get("protocol_version"), str) and re.match(r"^\d+\.\d+$", d["protocol_version"])):
                p.append("protocol_version")
            org = d.get("organization") if isinstance(d.get("organization"), dict) else {}
            for k in ("name", "domain"):
                if not (isinstance(org.get(k), str) and org[k].strip()):
                    p.append(f"organization.{k}")
        elif name == "agent_card":
            for k in ("name", "description"):
                if not (isinstance(d.get(k), str) and d[k].strip()):
                    p.append(k)
            if not isinstance(d.get("skills"), list):
                p.append("skills")
        elif name == "sig_directory":
            keys = d.get("keys")
            if not (isinstance(keys, list) and keys and all(isinstance(k, dict) and k.get("kty") for k in keys)):
                p.append("keys")
        return not p, p
    if name == "llms_txt":
        if HTMLISH.match(body):
            return False, ["html"]
        first = next((l for l in body.splitlines() if l.strip()), "")
        return first.startswith("# "), ([] if first.startswith("# ") else ["first line not '# '"])
    if name == "sitemap":
        s = re.sub(r"^﻿?\s*(<\?xml[^>]*\?>\s*)?(<!--.*?-->\s*)*", "", body[:5000], flags=re.S)
        ok = s.startswith("<urlset") or s.startswith("<sitemapindex")
        return ok, ([] if ok else ["not urlset/sitemapindex"])
    return False, ["unknown"]


def outcome(name: str, kind: str, r: dict, control: dict | None) -> tuple[str, list[str]]:
    if not r:
        return "not_requested", []
    if r.get("self_excluded"):
        return "self_excluded", []
    if "status" not in r:
        return "error", []
    if r["status"] != 200:
        return "absent", []
    body = r.get("body")
    ctype = r.get("headers", {}).get("content-type", "").lower()
    is_html = "html" in ctype or bool(body and HTMLISH.match(body))
    if body is None:
        # bodies over 256 KB are not kept: a large XML sitemap is judged on its content type
        ok, problems = (name == "sitemap" and "xml" in ctype and not is_html), ["body not kept"]
    else:
        ok, problems = valid(name, body, "")
    if is_html:
        return "soft_404", ["html"]
    if control and control.get("status") == 200:
        if control.get("body_sha256") and control.get("body_sha256") == r.get("body_sha256"):
            return "soft_404", ["same as control"]
        cctype = control.get("headers", {}).get("content-type", "").lower().split(";")[0]
        if cctype == ctype.split(";")[0] and not ok:
            return "soft_404", ["control 200, same type"]
    return ("valid" if ok else "invalid"), problems


def derive(rec: dict) -> dict:
    by = {}
    for r in rec["requests"]:
        by.setdefault(r["step"], r)
    home = by.get("home_html", {})
    row = {"site": rec["site"], "reachable": "status" in home, "home_status": home.get("status"),
           "catch_all": by.get("control_wk", {}).get("status") == 200,
           "catch_all_root": by.get("control_root", {}).get("status") == 200, "files": {}}
    for step, (name, kind, expected) in FILES.items():
        r = by.get(step)
        control = by.get("control_root") if name in ("llms_txt", "sitemap") else by.get("control_wk")
        oc, problems = outcome(name, kind, r or {}, control)
        ctype = (r or {}).get("headers", {}).get("content-type", "").lower().split(";")[0].strip() or None
        row["files"][name] = {"outcome": oc, "problems": problems, "status": (r or {}).get("status"),
                              "content_type": ctype, "media_type_ok": bool(ctype and ctype in expected),
                              "redirected": bool((r or {}).get("redirects"))}
    # ARD via Link header
    links = home.get("headers", {}).get("link", "")
    row["link_rel_ard"] = bool(re.search(r'rel="?[^";,]*\bard\b', links, re.I))
    row["link_describedby"] = bool(re.search(r'rel="?[^";,]*\bdescribedby\b', links, re.I))
    row["link_md_alternate"] = bool(re.search(r"text/markdown", links, re.I) and re.search(r"alternate", links, re.I))
    al = by.get("ard_link")
    if al:
        oc, problems = outcome("ard", "json", al, by.get("control_wk"))
        row["ard_link_target"] = {"outcome": oc, "content_type": al.get("headers", {}).get("content-type", "").split(";")[0] or None}
    cl = by.get("catalog_link")
    if cl:
        d = load_json(cl.get("body")) if cl.get("status") == 200 else None
        card = isinstance(d, dict) and isinstance(d.get("$schema"), str) and "server-card" in d["$schema"].lower() \
            and all(isinstance(d.get(k), str) and d[k].strip() for k in ("name", "version", "description"))
        row["catalog_link"] = {"status": cl.get("status"), "json_object": isinstance(d, dict), "server_card_valid_v1": bool(card),
                               "content_type": cl.get("headers", {}).get("content-type", "").split(";")[0] or None}
    cat = by.get("wk_ai_catalog") or {}
    d = load_json(cat.get("body")) if row["files"]["ai_catalog"]["outcome"] in ("valid", "invalid") else None
    if isinstance(d, dict) and isinstance(d.get("entries"), list):
        row["ai_catalog_entry_types"] = sorted({e.get("type") for e in d["entries"] if isinstance(e, dict) and isinstance(e.get("type"), str)})
    ard = by.get("wk_ard") or {}
    d = load_json(ard.get("body")) if row["files"]["ard"]["outcome"] in ("valid",) else None
    if isinstance(d, dict):
        row["ard_top_keys"] = sorted(d.keys())[:20]
    return row


def main():
    with open(SAMPLE, encoding="utf8") as f:
        sample = {r["site"]: r for r in csv.DictReader(f) if r["in_e3"] == "1"}
    rows, missing = [], 0
    for site, s in sample.items():
        p = CRAWL_RAW / f"{site}.json"
        if not p.exists():
            missing += 1
            continue
        rec = json.loads(p.read_text(encoding="utf8"))
        if "requests" not in rec:
            row = {"site": site, "reachable": False, "excluded": rec.get("excluded") or "crawler_error"}
        else:
            row = derive(rec)
        row["sources"] = s["sources"]
        row["tranco_rank"] = s["tranco_rank"]
        rows.append(row)
    rows.sort(key=lambda r: r["site"])
    with open(STUDY_DIR / "data" / "sites.jsonl", "w", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    names = [v[0] for v in FILES.values()]
    with open(STUDY_DIR / "data" / "files.csv", "w", encoding="utf8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["site", "sources", "tranco_rank", "reachable", "catch_all", "link_rel_ard", "link_md_alternate"]
                   + [f"{n}_outcome" for n in names] + [f"{n}_content_type" for n in names])
        for r in rows:
            fl = r.get("files", {})
            w.writerow([r["site"], r["sources"], r["tranco_rank"], r.get("reachable"), r.get("catch_all", ""),
                        r.get("link_rel_ard", ""), r.get("link_md_alternate", "")]
                       + [fl.get(n, {}).get("outcome", "") for n in names] + [fl.get(n, {}).get("content_type") or "" for n in names])
    tally = {n: {} for n in names}
    for r in rows:
        for n, v in r.get("files", {}).items():
            tally[n][v["outcome"]] = tally[n].get(v["outcome"], 0) + 1
    print(f"{len(rows)} sites ({missing} not crawled yet)")
    for n, t in tally.items():
        print(f"  {n:14s} {t}")


if __name__ == "__main__":
    main()
