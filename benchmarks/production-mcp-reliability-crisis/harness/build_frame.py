"""Build the sampling frame from the official MCP Registry.

Steps:
  1. Page through GET /v0/servers?version=latest and save every raw page (the snapshot).
  2. Keep active servers; expand every remotes[] entry into one candidate endpoint.
  3. Normalise URLs, de-duplicate, and apply the pre-registered exclusions.
  4. Write frame.csv (the population) and a seeded random sample of N endpoints.

Usage:
  python build_frame.py crawl            # fetch the snapshot (resumable)
  python build_frame.py frame            # build frame.csv from the snapshot
  python build_frame.py sample --n 3000 --seed 20261012
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import random
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from common import (
    FRAME_DIR,
    USER_AGENT,
    git_sha,
    host_of,
    host_opted_out,
    is_private_address,
    is_templated,
    load_optout,
    normalize_url,
    sha256_file,
)

REGISTRY = "https://registry.modelcontextprotocol.io/v0/servers"
SNAPSHOT_DIR = FRAME_DIR / "registry_snapshot"
OFFICIAL = "io.modelcontextprotocol.registry/official"


def fetch_page(cursor: str | None) -> dict:
    q = {"limit": "100", "version": "latest"}
    if cursor:
        q["cursor"] = cursor
    req = urllib.request.Request(
        REGISTRY + "?" + urllib.parse.urlencode(q), headers={"User-Agent": USER_AGENT}
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception:
            if attempt == 4:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("unreachable")


def crawl() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    pages = sorted(SNAPSHOT_DIR.glob("page_*.json.gz"))
    cursor = None
    if pages:  # resume from the last saved page
        with gzip.open(pages[-1], "rt", encoding="utf8") as f:
            cursor = json.load(f)["response"].get("metadata", {}).get("nextCursor")
        if not cursor:
            print("snapshot already complete")
            return
    n = len(pages)
    while True:
        started = datetime.now(timezone.utc).isoformat()
        d = fetch_page(cursor)
        with gzip.open(SNAPSHOT_DIR / f"page_{n:05d}.json.gz", "wt", encoding="utf8") as f:
            json.dump({"fetched_at": started, "cursor": cursor, "response": d}, f)
        n += 1
        cursor = d.get("metadata", {}).get("nextCursor")
        if n % 20 == 0:
            print(f"{n} pages")
        if not cursor or not d.get("servers"):
            break
        time.sleep(0.3)
    print(f"snapshot complete: {n} pages")


def iter_snapshot():
    for p in sorted(SNAPSHOT_DIR.glob("page_*.json.gz")):
        with gzip.open(p, "rt", encoding="utf8") as f:
            page = json.load(f)
        for entry in page["response"].get("servers", []):
            yield page["fetched_at"], entry


def build_frame() -> None:
    optout = load_optout()
    seen: dict[str, dict] = {}
    counts = {
        "registry_entries": 0,
        "latest_active_servers": 0,
        "servers_with_remotes": 0,
        "remote_entries": 0,
        "excluded_templated": 0,
        "excluded_non_https": 0,
        "excluded_invalid_url": 0,
        "excluded_private_address": 0,
        "excluded_opt_out": 0,
        "duplicate_urls_merged": 0,
    }
    first_fetch = last_fetch = None
    for fetched_at, entry in iter_snapshot():
        first_fetch = first_fetch or fetched_at
        last_fetch = fetched_at
        counts["registry_entries"] += 1
        meta = entry.get("_meta", {}).get(OFFICIAL, {})
        if meta.get("status") != "active" or not meta.get("isLatest"):
            continue
        counts["latest_active_servers"] += 1
        server = entry.get("server", {})
        remotes = server.get("remotes") or []
        if remotes:
            counts["servers_with_remotes"] += 1
        for rem in remotes:
            counts["remote_entries"] += 1
            raw = (rem.get("url") or "").strip()
            if is_templated(raw):
                counts["excluded_templated"] += 1
                continue
            url = normalize_url(raw)
            if not url:
                counts["excluded_invalid_url"] += 1
                continue
            if not url.startswith("https://"):
                counts["excluded_non_https"] += 1
                continue
            if url in seen:
                counts["duplicate_urls_merged"] += 1
                seen[url]["server_names"].add(server.get("name", ""))
                continue
            seen[url] = {
                "url": url,
                "probe_url": raw,  # probed exactly as registered; `url` is only the dedupe key
                "transport": rem.get("type", ""),
                "server_names": {server.get("name", "")},
                "published_at": meta.get("publishedAt", ""),
                "has_headers": bool(rem.get("headers")),
            }

    # Host-level exclusions (one DNS lookup per host).
    host_private: dict[str, bool] = {}
    rows = []
    for url, r in sorted(seen.items()):
        host = host_of(url)
        if host_opted_out(host, optout):
            counts["excluded_opt_out"] += 1
            continue
        if host not in host_private:
            host_private[host] = is_private_address(host)
        if host_private[host]:
            counts["excluded_private_address"] += 1
            continue
        rows.append(
            {
                "url": url,
                "probe_url": r["probe_url"],
                "host": host,
                "transport": r["transport"],
                "server_names": "|".join(sorted(r["server_names"])),
                "published_at": r["published_at"],
                "declares_headers": r["has_headers"],
            }
        )
    counts["frame_endpoints"] = len(rows)

    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    frame_csv = FRAME_DIR / "frame.csv"
    with open(frame_csv, "w", encoding="utf8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_first_page_at": first_fetch,
        "snapshot_last_page_at": last_fetch,
        "registry": REGISTRY + "?version=latest",
        "harness_git_sha": git_sha(),
        "frame_sha256": sha256_file(frame_csv),
        "counts": counts,
    }
    (FRAME_DIR / "frame_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf8")
    print(json.dumps(meta, indent=2))


def sample(n: int, seed: int) -> None:
    with open(FRAME_DIR / "frame.csv", encoding="utf8") as f:
        rows = list(csv.DictReader(f))
    if len(rows) <= 5000:
        chosen = rows
        rule = "full frame (<= 5000 endpoints)"
    else:
        rng = random.Random(seed)
        chosen = sorted(rng.sample(rows, n), key=lambda r: r["url"])
        rule = f"simple random sample n={n}, seed={seed}"
    out = FRAME_DIR / "sample.csv"
    with open(out, "w", encoding="utf8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(chosen[0].keys()))
        w.writeheader()
        w.writerows(chosen)
    meta = {
        "rule": rule,
        "frame_size": len(rows),
        "sample_size": len(chosen),
        "frame_sha256": sha256_file(FRAME_DIR / "frame.csv"),
        "sample_sha256": sha256_file(out),
    }
    (FRAME_DIR / "sample_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("crawl")
    sub.add_parser("frame")
    s = sub.add_parser("sample")
    s.add_argument("--n", type=int, default=3000)
    s.add_argument("--seed", type=int, default=20261012)
    a = ap.parse_args()
    {"crawl": crawl, "frame": build_frame}.get(a.cmd, lambda: sample(a.n, a.seed))()
