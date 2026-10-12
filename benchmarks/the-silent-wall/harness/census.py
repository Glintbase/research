"""Part 1 — robots.txt policy census, and the fixed page list for Part 2.

For each sampled domain:
  1. GET https://<domain>/robots.txt once (honest research identity, <= 5 redirects).
  2. Parse with Protego (RFC 9309) and record, per vendor token: whether a group names the
     token explicitly, and whether "/" is allowed.
  3. Choose up to 3 extra same-origin pages, deterministically: the first <loc> URLs of the
     first sitemap (robots Sitemap: line, else /sitemap.xml; a sitemap index is followed one
     level), skipping login/cart/checkout/account URLs. The homepage is always page 1.

Outputs: data/robots/raw/<domain>.txt, data/robots/census.jsonl, data/sample/pages.jsonl
Usage:   python census.py
"""

from __future__ import annotations

import asyncio
import csv
import re
from urllib.parse import urljoin, urlsplit

import httpx
from protego import Protego

from common import AGENT_TOKEN, AGENT_UA, DATA_DIR, MAX_PAGES, ROBOTS_DIR, SAMPLE_CSV, TOKENS, write_jsonl

EXCLUDE_PATH = re.compile(r"login|signin|sign-in|signup|register|cart|checkout|account|basket|auth", re.I)
LOC = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)


def named_tokens(text: str) -> set[str]:
    names = set()
    for line in text.splitlines():
        m = re.match(r"\s*user-agent\s*:\s*(\S+)", line, re.I)
        if m:
            names.add(m.group(1).strip().lower())
    return names


async def fetch(client, url, limit=2_000_000):
    """One retry after 10 s on a network-level failure (residential vantage point)."""
    err = None
    for attempt in range(2):
        try:
            r = await client.get(url)
            return r.status_code, str(r.url), r.text[:limit], r.headers.get("content-type", "")
        except Exception as e:
            err = type(e).__name__
            if attempt == 0:
                await asyncio.sleep(10)
    return None, url, "", f"ERR {err}"


async def one(client, sem, row):
    domain = row["domain"]
    home = f"https://{domain}/"
    async with sem:
        status, final, text, ctype = await fetch(client, f"https://{domain}/robots.txt")
        is_robots = status == 200 and "html" not in ctype.lower() and "<html" not in text[:500].lower()
        robots_text = text if is_robots else ""
        (ROBOTS_DIR / "raw").mkdir(parents=True, exist_ok=True)
        (ROBOTS_DIR / "raw" / f"{domain}.txt").write_text(robots_text, encoding="utf8")
        rp = Protego.parse(robots_text)
        names = named_tokens(robots_text)
        tokens = {}
        for tok, (vendor, purpose) in TOKENS.items():
            tokens[tok] = {
                "named": tok.lower() in names,
                "root_allowed": rp.can_fetch(home, tok),
            }
        rec = {
            "domain": domain,
            "sector": row["sector"],
            "robots_status": status,
            "robots_error": ctype if status is None else None,
            "robots_final_url": final,
            "robots_present": bool(robots_text.strip()),
            "robots_bytes": len(robots_text.encode()),
            "wildcard_root_allowed": rp.can_fetch(home, "*"),
            "agent_root_allowed": rp.can_fetch(home, AGENT_TOKEN),
            "tokens": tokens,
        }

        # Page list: homepage + up to 3 sitemap URLs on the same registrable host.
        pages = [home]
        sitemaps = list(rp.sitemaps) or [f"https://{domain}/sitemap.xml"]
        host = domain.lower()
        urls = []
        for sm in sitemaps[:2]:
            st, _, body, _ = await fetch(client, sm, limit=3_000_000)
            if st != 200 or not body:
                continue
            locs = LOC.findall(body)
            if "<sitemapindex" in body[:2000].lower() and locs:
                st2, _, body2, _ = await fetch(client, locs[0], limit=3_000_000)
                locs = LOC.findall(body2) if st2 == 200 else []
            for u in locs:
                h = (urlsplit(u).hostname or "").lower()
                if (h == host or h == "www." + host) and not EXCLUDE_PATH.search(u) and u.rstrip("/") != home.rstrip("/"):
                    urls.append(u)
                if len(urls) >= MAX_PAGES - 1:
                    break
            if urls:
                break
        pages += urls[: MAX_PAGES - 1]
        page_rec = {
            "domain": domain,
            "sector": row["sector"],
            "pages": pages,
            "page_source": "sitemap" if len(pages) > 1 else "homepage_only",
            "agent_allowed": {p: rp.can_fetch(p, AGENT_TOKEN) for p in pages},
        }
        print(f"{domain:28s} robots={status} named={sum(t['named'] for t in tokens.values())} pages={len(pages)}", flush=True)
        await asyncio.sleep(1.0)
        return rec, page_rec


async def main():
    with open(SAMPLE_CSV, encoding="utf8") as f:
        rows = list(csv.DictReader(f))
    sem = asyncio.Semaphore(2)  # higher concurrency caused spurious connect failures from this vantage point
    async with httpx.AsyncClient(
        headers={"User-Agent": AGENT_UA, "Accept": "text/plain, application/xml, text/xml, */*"},
        follow_redirects=True, max_redirects=5, timeout=httpx.Timeout(20.0, connect=15.0),
    ) as client:
        results = await asyncio.gather(*(one(client, sem, r) for r in rows))
    write_jsonl(ROBOTS_DIR / "census.jsonl", [r for r, _ in results])
    write_jsonl(DATA_DIR / "sample" / "pages.jsonl", [p for _, p in results])


if __name__ == "__main__":
    asyncio.run(main())
