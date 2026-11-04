"""Build the shared E1/E3 domain sample (no network requests).

Sources (all frozen files in this repository):
  - Tranco list 4672X (retrieved 2026-10-12), copied in the-silent-wall/data/sample/tranco_top6000.txt
  - the Glintbase leaderboard, 103 URLs read from scan.glintbase.dev/leaderboard on 2026-11-04
    (data/leaderboard_urls_2026-11-04.txt)
  - The Silent Wall's 150 domains (the-silent-wall/data/sample/domains.csv)
  - MCP Registry publisher domains: the registrable domain (ICANN public suffixes only, tldextract's
    bundled snapshot) of every host in the Edition 1 3,000-endpoint sample

E1 = leaderboard ∪ Silent Wall ∪ Tranco top 1,000
E3 = Tranco top 5,000 ∪ leaderboard ∪ MCP publisher domains

A "site" is a host name: Tranco and Silent Wall entries are registrable domains, leaderboard entries are
the scanned host (e.g. ai.meta.com). A leading "www." is dropped and the homepage is https://<site>/.

Usage: python build_sample.py
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

import tldextract

HERE = Path(__file__).resolve().parent
CRAWL_DIR = HERE.parent
BENCH = CRAWL_DIR.parent
OUT = CRAWL_DIR / "data" / "sample.csv"

TRANCO = BENCH / "the-silent-wall" / "data" / "sample" / "tranco_top6000.txt"
SILENT_WALL = BENCH / "the-silent-wall" / "data" / "sample" / "domains.csv"
LEADERBOARD = CRAWL_DIR / "data" / "leaderboard_urls_2026-11-04.txt"
MCP_SAMPLE = BENCH / "production-mcp-reliability-crisis" / "data" / "frame" / "sample.csv"


def norm(host: str) -> str:
    host = host.strip().lower().rstrip(".")
    return host[4:] if host.startswith("www.") else host


def main():
    ext = tldextract.TLDExtract(suffix_list_urls=(), include_psl_private_domains=False)
    sites: dict[str, dict] = {}

    def add(site: str, source: str, rank: int | None = None):
        if not site or "." not in site:
            return
        s = sites.setdefault(site, {"site": site, "sources": set(), "tranco_rank": None})
        s["sources"].add(source)
        if rank is not None and (s["tranco_rank"] is None or rank < s["tranco_rank"]):
            s["tranco_rank"] = rank

    for line in TRANCO.read_text(encoding="utf8").splitlines():
        rank, dom = line.split(",", 1)
        if int(rank) <= 5000:
            add(norm(dom), "tranco", int(rank))
    for u in LEADERBOARD.read_text(encoding="utf8").split():
        add(norm(urlsplit(u).hostname or ""), "leaderboard")
    with open(SILENT_WALL, encoding="utf8") as f:
        for r in csv.DictReader(f):
            add(norm(r["domain"]), "silent_wall")
    with open(MCP_SAMPLE, encoding="utf8") as f:
        for r in csv.DictReader(f):
            reg = ext(r["host"]).top_domain_under_public_suffix
            add(norm(reg), "mcp_registry")

    rows = []
    for s in sites.values():
        src, rank = s["sources"], s["tranco_rank"]
        in_e1 = bool(src & {"leaderboard", "silent_wall"}) or ("tranco" in src and rank <= 1000)
        in_e3 = bool(src & {"leaderboard", "mcp_registry"}) or "tranco" in src
        rows.append({"site": s["site"], "tranco_rank": rank or "", "sources": "|".join(sorted(src)),
                     "in_e1": int(in_e1), "in_e3": int(in_e3)})
    rows.sort(key=lambda r: (r["tranco_rank"] == "", r["tranco_rank"] or 0, r["site"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    meta = {
        "sites": len(rows),
        "e1_sites": sum(r["in_e1"] for r in rows),
        "e3_sites": sum(r["in_e3"] for r in rows),
        "by_source": {k: sum(k in r["sources"].split("|") for r in rows)
                      for k in ("tranco", "leaderboard", "silent_wall", "mcp_registry")},
        "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
        "tranco_list": "4672X (retrieved 2026-10-12)",
        "tldextract": tldextract.__version__,
    }
    (OUT.parent / "sample_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
