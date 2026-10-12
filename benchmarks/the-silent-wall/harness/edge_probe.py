"""Part 2 — edge behaviour under three honest identities.

Identities (order randomised per domain and round, seeded):
  agent    GlintbaseResearch/1.0 UA via httpx; obeys robots.txt for its own token
           (disallowed pages are recorded as self_excluded and not fetched)
  script   python-httpx default UA via httpx (generic unlabelled script baseline)
  browser  headless Chromium via Playwright with its default UA (contains "HeadlessChrome")

Pacing: one domain per worker; <= 1 request/second within an identity; >= 30 s pause between
identities on the same domain; fresh cookies for every (domain, identity). Response bodies are
not stored: only status, selected headers, cookie *names*, visible-text length, title and
challenge-marker hits.

Usage: python edge_probe.py --round 1 [--workers 6] [--limit N]
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import re
import time
from datetime import datetime, timezone

import httpx
from playwright.async_api import async_playwright

from common import (
    AGENT_UA, DATA_DIR, EDGE_DIR, HARNESS_VERSION, PAUSE_BETWEEN_IDENTITIES_S,
    PAUSE_BETWEEN_REQUESTS_S, TIMEOUT_S, chromium_executable, read_jsonl,
)

IDENTITIES = ["agent", "script", "browser"]
KEEP_HEADERS = {
    "server", "via", "cf-ray", "cf-mitigated", "cf-cache-status", "x-amzn-waf-action", "x-amz-cf-id",
    "x-amz-cf-pop", "x-vercel-mitigated", "x-vercel-id", "x-datadome", "x-iinfo", "x-cdn", "x-served-by",
    "x-cache", "akamai-grn", "x-akamai-transformed", "x-azure-ref", "retry-after", "content-type", "location",
}
COOKIE_NAMES = re.compile(r"(?:^|,\s*)([A-Za-z0-9_\-\.]+)=")

MARKERS = {
    "cloudflare_challenge": re.compile(r"Just a moment\.\.\.|cf-chl-|cf_chl_opt|challenge-platform", re.I),
    "cloudflare_block": re.compile(r"Attention Required! \| Cloudflare|Sorry, you have been blocked", re.I),
    "akamai_block": re.compile(r"errors\.edgesuite\.net|Reference #\d+\.[0-9a-f]+\.\d+", re.I),
    "akamai_challenge": re.compile(r"_sec/cp_challenge|sec-if-cpt|bm-verify", re.I),
    "datadome": re.compile(r"captcha-delivery\.com|geo\.captcha-delivery", re.I),
    "human_perimeterx": re.compile(r"px-captcha|_pxCaptcha|Press &amp; Hold|Press & Hold", re.I),
    "imperva": re.compile(r"_Incapsula_Resource|Incapsula incident ID", re.I),
    "aws_waf": re.compile(r"awswaf|AwsWafIntegration", re.I),
    "kasada": re.compile(r"KPSDK", re.I),
    "captcha_widget": re.compile(r"g-recaptcha|hcaptcha\.com|challenges\.cloudflare\.com/turnstile", re.I),
}
TAG = re.compile(r"<script\b.*?</script>|<style\b.*?</style>|<[^>]+>", re.S | re.I)
TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)


def visible_text_len(html: str) -> int:
    return len(re.sub(r"\s+", " ", TAG.sub(" ", html)).strip())


def marker_hits(html: str) -> list[str]:
    head = html[:200_000]
    return [k for k, rx in MARKERS.items() if rx.search(head)]


def pick_headers(h) -> dict:
    out = {k.lower(): v[:200] for k, v in h.items() if k.lower() in KEEP_HEADERS}
    sc = h.get_list("set-cookie") if hasattr(h, "get_list") else [v for k, v in h.items() if k.lower() == "set-cookie"]
    out["cookie_names"] = sorted({m.group(1) for c in sc for m in COOKIE_NAMES.finditer(c.split(";", 1)[0])})
    return out


async def http_fetch(client: httpx.AsyncClient, url: str) -> dict:
    t0 = time.perf_counter()
    rec = {"url": url}
    try:
        r = await client.get(url)
        body = r.text[:2_000_000]
        rec.update(status=r.status_code, final_url=str(r.url), redirects=len(r.history), headers=pick_headers(r.headers),
                   text_len=visible_text_len(body), markers=marker_hits(body),
                   title=(TITLE.search(body).group(1).strip()[:120] if TITLE.search(body) else None))
    except httpx.TimeoutException:
        rec["error"] = "timeout"
    except httpx.ConnectError as e:
        rec["error"] = "tls_error" if "ssl" in str(e).lower() or "certificate" in str(e).lower() else "connect_error"
    except Exception as e:
        rec["error"] = f"error:{type(e).__name__}"
    rec["latency_ms"] = round((time.perf_counter() - t0) * 1000)
    return rec


async def browser_fetch(browser, url: str, context) -> dict:
    t0 = time.perf_counter()
    rec = {"url": url}
    page = await context.new_page()
    try:
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT_S * 1000)
        await page.wait_for_timeout(5000)  # let automatic JS challenges resolve, as for a real visitor
        html = await page.content()
        text = await page.evaluate("document.body ? document.body.innerText : ''")
        rec.update(status=resp.status if resp else None, final_url=page.url,
                   headers=pick_headers(await resp.all_headers()) if resp else {},
                   text_len=len(re.sub(r"\s+", " ", text or "").strip()), markers=marker_hits(html),
                   title=(await page.title())[:120])
    except Exception as e:
        msg = str(e).lower()
        rec["error"] = "timeout" if "timeout" in msg else ("tls_error" if "cert" in msg or "ssl" in msg else f"error:{type(e).__name__}")
    finally:
        await page.close()
    rec["latency_ms"] = round((time.perf_counter() - t0) * 1000)
    return rec


async def probe_domain(row: dict, round_name: str, browser, out_dir) -> None:
    out = out_dir / f"{row['domain']}.json"
    if out.exists():
        return
    seed = int(hashlib.sha256(f"{row['domain']}|{round_name}".encode()).hexdigest()[:8], 16)
    order = IDENTITIES[:]
    random.Random(seed).shuffle(order)
    results = []
    for i, ident in enumerate(order):
        if i:
            await asyncio.sleep(PAUSE_BETWEEN_IDENTITIES_S)
        started = datetime.now(timezone.utc).isoformat()
        reqs = []
        if ident == "browser":
            ctx = await browser.new_context()
            try:
                for j, url in enumerate(row["pages"]):
                    if j:
                        await asyncio.sleep(PAUSE_BETWEEN_REQUESTS_S)
                    reqs.append(await browser_fetch(browser, url, ctx))
            finally:
                await ctx.close()
        else:
            headers = {"User-Agent": AGENT_UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"} if ident == "agent" else {}
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, max_redirects=5, timeout=TIMEOUT_S) as client:
                for j, url in enumerate(row["pages"]):
                    if ident == "agent" and not row["agent_allowed"].get(url, True):
                        reqs.append({"url": url, "self_excluded": True})
                        continue
                    if j:
                        await asyncio.sleep(PAUSE_BETWEEN_REQUESTS_S)
                    reqs.append(await http_fetch(client, url))
        results.append({"identity": ident, "order": i, "started_at": started, "requests": reqs})
    rec = {"domain": row["domain"], "sector": row["sector"], "round": round_name,
           "harness_version": HARNESS_VERSION, "identities": results}
    out.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf8")
    s = {r["identity"]: (r["requests"][0].get("status") or r["requests"][0].get("error") or "self_excluded") for r in results}
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {row['domain']:28s} {s}", flush=True)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    rows = read_jsonl(DATA_DIR / "sample" / "pages.jsonl")
    if a.limit:
        rows = rows[: a.limit]
    out_dir = EDGE_DIR / f"round_{a.round}"
    out_dir.mkdir(parents=True, exist_ok=True)
    queue: asyncio.Queue = asyncio.Queue()
    for r in rows:
        queue.put_nowait(r)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=chromium_executable())

        async def worker():
            while not queue.empty():
                r = queue.get_nowait()
                try:
                    await probe_domain(r, a.round, browser, out_dir)
                except Exception as e:
                    print(f"FAILED {r['domain']}: {type(e).__name__}: {e}", flush=True)

        await asyncio.gather(*(worker() for _ in range(a.workers)))
        await browser.close()
    (out_dir / "_round_meta.json").write_text(json.dumps({
        "round": a.round, "finished_at": datetime.now(timezone.utc).isoformat(), "domains": len(rows),
        "harness_version": HARNESS_VERSION, "agent_ua": AGENT_UA, "script_ua": f"python-httpx/{httpx.__version__}",
        "browser": "Chromium (Playwright, headless, default UA)",
    }, indent=2), encoding="utf8")


if __name__ == "__main__":
    asyncio.run(main())
