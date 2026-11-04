"""Silent Wall Part C: the same honest agent, unsigned vs Web Bot Auth-signed, plus the browser control.

Fetch and classification code is The Silent Wall's (../../the-silent-wall/harness/edge_probe.py and
analyze.py), imported unchanged. Page lists and robots decisions are The Silent Wall's frozen
data/sample/pages.jsonl.

Arms (order randomised per domain and round, seeded by SHA-256 of "domain|round|part-c"):
  unsigned  httpx, User-Agent GlintbaseResearch/1.0 (...), obeys robots.txt for its token (frozen decisions)
  signed    identical to `unsigned`, plus Signature-Agent / Signature-Input / Signature headers on every
            request, including each redirect hop (webbotauth.py)
  browser   headless Chromium, Playwright default UA (The Silent Wall's browser identity)

Pacing as in The Silent Wall: <= 1 request/second within an arm, >= 30 s between arms on the same
domain, fresh cookies per (domain, arm), up to 4 domains in parallel.

Usage:
  python edge_probe_c.py --round U1 --arms unsigned,browser       # before the key directory is live
  python edge_probe_c.py --round S1 --arms unsigned,signed,browser
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
STUDY_DIR = HERE.parent
SW_HARNESS = STUDY_DIR.parent / "the-silent-wall" / "harness"
sys.path.insert(0, str(SW_HARNESS))

import edge_probe as sw  # noqa: E402  (The Silent Wall's fetch code, unchanged)
from common import AGENT_UA, DATA_DIR as SW_DATA, chromium_executable, read_jsonl  # noqa: E402

import webbotauth  # noqa: E402

HARNESS_VERSION = "1.0.0"
OUT_ROOT = STUDY_DIR / "data" / "edge"
ARMS = ["unsigned", "signed", "browser"]


async def run_arm(arm: str, row: dict, browser, key) -> list[dict]:
    reqs = []
    if arm == "browser":
        ctx = await browser.new_context()
        try:
            for j, url in enumerate(row["pages"]):
                if j:
                    await asyncio.sleep(sw.PAUSE_BETWEEN_REQUESTS_S)
                reqs.append(await sw.browser_fetch(browser, url, ctx))
        finally:
            await ctx.close()
        return reqs
    headers = {"User-Agent": AGENT_UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"}
    hooks = {"request": [webbotauth.httpx_signing_hook(key)]} if arm == "signed" else {}
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, max_redirects=5,
                                 timeout=sw.TIMEOUT_S, event_hooks=hooks) as client:
        for j, url in enumerate(row["pages"]):
            if not row["agent_allowed"].get(url, True):
                reqs.append({"url": url, "self_excluded": True})
                continue
            if j:
                await asyncio.sleep(sw.PAUSE_BETWEEN_REQUESTS_S)
            reqs.append(await sw.http_fetch(client, url))
    return reqs


async def probe_domain(row: dict, round_name: str, arms: list[str], browser, key, out_dir: Path):
    out = out_dir / f"{row['domain']}.json"
    if out.exists():
        return
    seed = int(hashlib.sha256(f"{row['domain']}|{round_name}|part-c".encode()).hexdigest()[:8], 16)
    order = arms[:]
    random.Random(seed).shuffle(order)
    results = []
    for i, arm in enumerate(order):
        if i:
            await asyncio.sleep(sw.PAUSE_BETWEEN_IDENTITIES_S)
        started = datetime.now(timezone.utc).isoformat()
        results.append({"identity": arm, "order": i, "started_at": started,
                        "requests": await run_arm(arm, row, browser, key)})
    rec = {"domain": row["domain"], "sector": row["sector"], "round": round_name,
           "harness_version": HARNESS_VERSION, "identities": results}
    out.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf8")
    s = {r["identity"]: (r["requests"][0].get("status") or r["requests"][0].get("error") or "self_excluded")
         for r in results}
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {row['domain']:28s} {s}", flush=True)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    ap.add_argument("--arms", default="unsigned,signed,browser")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only")
    ap.add_argument("--out")
    a = ap.parse_args()
    arms = [x for x in a.arms.split(",") if x]
    assert all(x in ARMS for x in arms), arms
    key = webbotauth.load_key() if "signed" in arms else None
    rows = read_jsonl(SW_DATA / "sample" / "pages.jsonl")
    if a.only:
        keep = set(a.only.split(","))
        rows = [r for r in rows if r["domain"] in keep]
    if a.limit:
        rows = rows[: a.limit]
    out_dir = Path(a.out) if a.out else OUT_ROOT / f"round_{a.round}"
    out_dir.mkdir(parents=True, exist_ok=True)
    queue: asyncio.Queue = asyncio.Queue()
    for r in rows:
        queue.put_nowait(r)
    started = datetime.now(timezone.utc).isoformat()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=chromium_executable()) if "browser" in arms else None

        async def worker():
            while not queue.empty():
                r = queue.get_nowait()
                try:
                    await probe_domain(r, a.round, arms, browser, key, out_dir)
                except Exception as e:
                    print(f"FAILED {r['domain']}: {type(e).__name__}: {e}", flush=True)

        await asyncio.gather(*(worker() for _ in range(a.workers)))
        if browser:
            await browser.close()
    (out_dir / "_round_meta.json").write_text(json.dumps({
        "round": a.round, "arms": arms, "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
        "domains": len(rows), "harness_version": HARNESS_VERSION, "agent_ua": AGENT_UA,
        "signature_agent": webbotauth.SIGNATURE_AGENT if key else None,
        "keyid": webbotauth.thumbprint(webbotauth.public_jwk(key.public_key())) if key else None,
        "browser": "Chromium (Playwright, headless, default UA)",
    }, indent=2), encoding="utf8")


if __name__ == "__main__":
    asyncio.run(main())
