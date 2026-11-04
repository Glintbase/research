"""Shared crawler for E1 (Content-Signal census) and E3 (front-door files census).

One pass per site, requests sent one at a time with >= 1 s between them (<= 1 request/second per
site). Honest identity; robots.txt is obeyed for the token `GlintbaseResearch` on every path except
robots.txt itself (a disallowed request is recorded as `self_excluded` and not sent).

Per site, in order (E1 sites get steps marked E1, E3 sites steps marked E3; shared steps run once):

  shared  1  GET /robots.txt
  shared  2  GET /                     Accept: text/html,...  (root Link header for E3)
  E1      3  GET <final homepage URL>  Accept: text/markdown
  E1      4  GET the Markdown twin, if the homepage advertises one (Link header or <link rel=alternate
             type=text/markdown>)
  E1    5-8  up to 2 docs pages, each as HTML then as Markdown (+ the docs host's robots.txt when it
             differs from the site's host); truncated at 8 E1 requests
  E3   9-14  /.well-known/ai-catalog.json, ard.json, api-catalog, poppy.json, agent-card.json,
             http-message-signatures-directory
  E3     15  /llms.txt
  E3     16  /sitemap.xml
  E3  17-18  control paths: /.well-known/glintbase-control-<random>, /glintbase-control-<random>.txt
  E3     19  the root Link rel="ard" target, if it isn't /.well-known/ard.json
  E3     20  the first URL an ai-catalog entry points to (cross-link check)

Limits: E1 <= 8 requests per site, E3 <= 15 (robots and the homepage count for both).

Stored (data/raw/<site>.json, not published): status, final URL, selected headers, content type,
body length and SHA-256, and parsed fields. Full bodies are kept only for robots.txt and for files
under 256 KB that are expected to be text or JSON (discovery files, llms.txt, control paths), for
validation. HTML page bodies are never stored.

Usage: python crawl.py [--workers 16] [--limit N] [--only site1,site2] [--sample data/sample.csv]
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import re
import secrets
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx
import tldextract
from protego import Protego

HERE = Path(__file__).resolve().parent
CRAWL_DIR = HERE.parent
DATA_DIR = CRAWL_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
BENCH = CRAWL_DIR.parent

HARNESS_VERSION = "1.0.0"
USER_AGENT = "GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot; research@glintbase.dev)"
TOKEN = "GlintbaseResearch"
TIMEOUT_S = 15.0
PAUSE_S = 1.0
RETRY_PAUSE_S = 10.0
MAX_BODY = 1_000_000
KEEP_BODY = 256_000
E1_MAX, E3_MAX = 8, 15

HTML_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
MD_ACCEPT = "text/markdown"
WELL_KNOWN = {
    "ai_catalog": ("/.well-known/ai-catalog.json", "application/ai-catalog+json, application/json;q=0.9, */*;q=0.1"),
    "ard": ("/.well-known/ard.json", "application/ard+json, application/json;q=0.9, */*;q=0.1"),
    "api_catalog": ("/.well-known/api-catalog", "application/linkset+json, application/json;q=0.9, */*;q=0.1"),
    "poppy": ("/.well-known/poppy.json", "application/json, */*;q=0.1"),
    "agent_card": ("/.well-known/agent-card.json", "application/json, */*;q=0.1"),
    "sig_directory": ("/.well-known/http-message-signatures-directory",
                      "application/http-message-signatures-directory+json, application/json;q=0.9, */*;q=0.1"),
}
KEEP_HEADERS = {
    "content-type", "content-signal", "link", "vary", "server", "via", "cf-ray", "cf-cache-status",
    "cf-mitigated", "x-amz-cf-id", "x-served-by", "x-cache", "x-vercel-id", "x-vercel-mitigated",
    "akamai-grn", "x-akamai-transformed", "x-datadome", "x-iinfo", "x-cdn", "x-azure-ref",
    "x-amzn-waf-action", "location", "content-length", "x-markdown-tokens", "x-robots-tag",
}
DOCS_HOST = re.compile(r"^(docs|doc|developer|developers|dev|api|learn|reference)\.", re.I)
DOCS_PATH = re.compile(r"^/(docs|doc|documentation|developers|developer|api|reference|guides|guide|learn)(/|$)", re.I)
EXCLUDE_PATH = re.compile(r"login|signin|sign-in|signup|sign-up|logout|cart|checkout|account|auth|register", re.I)

_ext = tldextract.TLDExtract(suffix_list_urls=(), include_psl_private_domains=False)


def registrable(host: str) -> str:
    return _ext(host).top_domain_under_public_suffix or host


class LinkParser(HTMLParser):
    """Collects <a href> (document order) and <link rel=alternate type=text/markdown>."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.anchors: list[str] = []
        self.md_alternates: list[str] = []
        self.title = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "a" and a.get("href") and len(self.anchors) < 2000:
            self.anchors.append(a["href"])
        elif tag == "link" and "alternate" in a.get("rel", "").lower().split() and \
                a.get("type", "").lower().startswith("text/markdown") and a.get("href"):
            self.md_alternates.append(a["href"])
        elif tag == "title" and self.title is None:
            self._in_title = True

    def handle_data(self, data):
        if self._in_title:
            self.title = (self.title or "") + data

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False


def parse_link_header(value: str | None) -> list[dict]:
    """RFC 8288 Link header -> [{href, rel, type}] (tolerant)."""
    out = []
    if not value:
        return out
    for part in re.split(r",\s*(?=<)", value):
        m = re.match(r"\s*<([^>]*)>(.*)", part)
        if not m:
            continue
        params = {}
        for pm in re.finditer(r';\s*([A-Za-z0-9*\-]+)\s*=\s*("([^"]*)"|[^;,\s]+)', m.group(2)):
            params[pm.group(1).lower()] = (pm.group(3) if pm.group(3) is not None else pm.group(2)).strip()
        out.append({"href": m.group(1), "rel": params.get("rel", "").lower(), "type": params.get("type", "").lower()})
    return out


class Site:
    def __init__(self, client: httpx.AsyncClient, row: dict):
        self.client = client
        self.site = row["site"]
        self.in_e1 = row["in_e1"] == "1"
        self.in_e3 = row["in_e3"] == "1"
        self.origin = f"https://{self.site}"
        self.requests: list[dict] = []
        self.counts = {"e1": 0, "e3": 0}
        self.robots: dict[str, Protego | None] = {}
        self.last_sent = 0.0

    def allowed(self, url: str) -> bool:
        host = urlsplit(url).hostname or ""
        rp = self.robots.get(host)
        return True if rp is None else rp.can_fetch(url, TOKEN)

    async def get(self, step: str, url: str, accept: str, studies: tuple[str, ...], keep_body: bool = False,
                  check_robots: bool = True) -> dict:
        rec = {"step": step, "url": url, "accept": accept, "studies": list(studies)}
        if check_robots and not self.allowed(url):
            rec["self_excluded"] = True
            self.requests.append(rec)
            return rec
        for s in studies:
            self.counts[s] += 1
        for attempt in (1, 2):
            wait = self.last_sent + PAUSE_S - time.monotonic()
            if wait > 0:
                await asyncio.sleep(wait)
            self.last_sent = time.monotonic()
            await self._fetch(rec, url, accept, keep_body)
            if rec.get("error") in ("connect_error", "timeout") and attempt == 1:
                rec["retried"] = True
                await asyncio.sleep(RETRY_PAUSE_S)
                for k in ("error", "error_detail"):
                    rec.pop(k, None)
                continue
            break
        self.requests.append(rec)
        return rec

    async def _fetch(self, rec: dict, url: str, accept: str, keep_body: bool):
        t0 = time.perf_counter()
        buf = bytearray()

        async def run():
            async with self.client.stream("GET", url, headers={"Accept": accept}) as r:
                rec["status"] = r.status_code
                rec["final_url"] = str(r.url)
                rec["redirects"] = len(r.history)
                rec["headers"] = {k.lower(): v[:500] for k, v in r.headers.items() if k.lower() in KEEP_HEADERS}
                if len(r.headers.get_list("content-signal")) > 1:
                    rec["headers"]["content-signal"] = " | ".join(r.headers.get_list("content-signal"))[:500]
                async for chunk in r.aiter_bytes():
                    buf.extend(chunk)
                    if len(buf) >= MAX_BODY:
                        rec["truncated"] = True
                        break

        try:
            await asyncio.wait_for(run(), timeout=TIMEOUT_S + 5)
        except (asyncio.TimeoutError, httpx.TimeoutException):
            rec["error"] = "timeout"
        except httpx.ConnectError as e:
            msg = str(e).lower()
            rec["error"] = "tls_error" if ("ssl" in msg or "certificate" in msg) else (
                "dns_error" if ("getaddrinfo" in msg or "11001" in msg or "name or service" in msg) else "connect_error")
            rec["error_detail"] = str(e).splitlines()[0][:200] if str(e) else None
        except httpx.TooManyRedirects:
            rec["error"] = "too_many_redirects"
        except Exception as e:
            rec["error"] = f"error:{type(e).__name__}"
            rec["error_detail"] = str(e).splitlines()[0][:200] if str(e) else None
        rec["latency_ms"] = round((time.perf_counter() - t0) * 1000)
        rec["body_bytes"] = len(buf)
        rec["body_sha256"] = hashlib.sha256(bytes(buf)).hexdigest() if buf else None
        rec["_body"] = bytes(buf)
        if keep_body and len(buf) <= KEEP_BODY:
            rec["body"] = bytes(buf).decode("utf8", "replace")

    # ------------------------------------------------------------------
    async def load_robots(self, host: str, studies: tuple[str, ...], step: str) -> dict:
        url = f"https://{host}/robots.txt"
        rec = await self.get(step, url, "text/plain, */*;q=0.1", studies, keep_body=True, check_robots=False)
        text = rec.get("_body", b"").decode("utf8", "replace") if rec.get("status") == 200 else ""
        ctype = rec.get("headers", {}).get("content-type", "").lower()
        if "html" in ctype or text.lstrip().lower().startswith(("<!doctype", "<html")):
            text = ""
        try:
            self.robots[host] = Protego.parse(text)
        except Exception:
            self.robots[host] = None
        return rec

    async def run(self) -> dict:
        both = tuple(s for s, on in (("e1", self.in_e1), ("e3", self.in_e3)) if on)
        host = self.site
        await self.load_robots(host, both, "robots")
        home = await self.get("home_html", f"{self.origin}/", HTML_ACCEPT, both)
        home_body = home.get("_body", b"")
        lp = LinkParser()
        if home.get("status") and "html" in home.get("headers", {}).get("content-type", "").lower():
            try:
                lp.feed(home_body[:MAX_BODY].decode("utf8", "replace"))
            except Exception:
                pass
        home["title"] = (lp.title or "").strip()[:120] or None
        home["html_md_alternates"] = lp.md_alternates[:5]
        final_home = home.get("final_url") or f"{self.origin}/"
        final_host = urlsplit(final_home).hostname or host
        if final_host != host and final_host not in self.robots and registrable(final_host) == registrable(host):
            # robots of the host the homepage redirected to (shared step; counts for both studies)
            await self.load_robots(final_host, both, "robots_final_host")

        if self.in_e1:
            await self.run_e1(home, lp, final_home)
        if self.in_e3:
            await self.run_e3(home)
        for r in self.requests:
            r.pop("_body", None)
        return {
            "site": self.site, "in_e1": self.in_e1, "in_e3": self.in_e3, "requests": self.requests,
            "counts": self.counts, "harness_version": HARNESS_VERSION,
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }

    async def run_e1(self, home: dict, lp: LinkParser, final_home: str):
        def budget():
            return E1_MAX - self.counts["e1"]

        if not home.get("status"):
            return
        await self.get("home_md", final_home, MD_ACCEPT, ("e1",))
        twins = [l["href"] for l in parse_link_header(home.get("headers", {}).get("link"))
                 if l["rel"] == "alternate" and l["type"].startswith("text/markdown")] + lp.md_alternates
        if twins and budget() > 0:
            await self.get("md_twin", urljoin(final_home, twins[0]), "text/markdown, text/plain;q=0.9, */*;q=0.1", ("e1",))
        # docs pages: first two same-site links matching the docs rule, in document order
        site_reg = registrable(self.site)
        picked: list[str] = []
        for href in lp.anchors:
            u = urljoin(final_home, href.strip())
            p = urlsplit(u)
            if p.scheme not in ("http", "https") or not p.hostname or registrable(p.hostname) != site_reg:
                continue
            u = urlunsplit(("https", p.netloc.lower(), p.path or "/", p.query, ""))
            if u.rstrip("/") == final_home.rstrip("/") or u in picked or EXCLUDE_PATH.search(p.path + "?" + p.query):
                continue
            if DOCS_HOST.match(p.hostname) or DOCS_PATH.match(p.path or "/"):
                picked.append(u)
            if len(picked) == 2:
                break
        home["docs_pages"] = picked
        for u in picked:
            h = urlsplit(u).hostname
            if h not in self.robots:
                if budget() < 3:
                    break
                await self.load_robots(h, ("e1",), "docs_robots")
            if budget() < 2:
                break
            d = await self.get("docs_html", u, HTML_ACCEPT, ("e1",))
            await self.get("docs_md", d.get("final_url") or u, MD_ACCEPT, ("e1",))

    async def run_e3(self, home: dict):
        for key, (path, accept) in WELL_KNOWN.items():
            await self.get(f"wk_{key}", f"{self.origin}{path}", accept, ("e3",), keep_body=True)
        await self.get("llms_txt", f"{self.origin}/llms.txt", "text/plain, text/markdown;q=0.9, */*;q=0.1", ("e3",), keep_body=True)
        await self.get("sitemap", f"{self.origin}/sitemap.xml", "application/xml, text/xml;q=0.9, */*;q=0.1", ("e3",),
                       keep_body=True)
        tok = secrets.token_hex(8)
        await self.get("control_wk", f"{self.origin}/.well-known/glintbase-control-{tok}", "application/json, */*;q=0.1",
                       ("e3",), keep_body=True)
        await self.get("control_root", f"{self.origin}/glintbase-control-{tok}.txt", "text/plain, */*;q=0.1",
                       ("e3",), keep_body=True)
        ard_links = [l["href"] for l in parse_link_header(home.get("headers", {}).get("link")) if "ard" in l["rel"].split()]
        if ard_links:
            target = urljoin(home.get("final_url") or f"{self.origin}/", ard_links[0])
            if urlsplit(target).path != "/.well-known/ard.json" and self.counts["e3"] < E3_MAX:
                await self.get("ard_link", target, WELL_KNOWN["ard"][1], ("e3",), keep_body=True)
        cat = next((r for r in self.requests if r["step"] == "wk_ai_catalog"), {})
        if cat.get("status") == 200 and self.counts["e3"] < E3_MAX:
            try:
                doc = json.loads(cat.get("_body", b"").decode("utf8", "replace"))
            except ValueError:
                doc = None
            entries = doc.get("entries") if isinstance(doc, dict) else None
            urls = [e.get("url") for e in entries or [] if isinstance(e, dict) and isinstance(e.get("url"), str)]
            if urls:
                await self.get("catalog_link", urljoin(cat.get("final_url") or self.origin, urls[0]),
                               "application/json, */*;q=0.1", ("e3",), keep_body=True)


def load_optout() -> set[str]:
    hosts = set()
    for p in [CRAWL_DIR / "optout.txt", BENCH / "production-mcp-reliability-crisis" / "optout.txt"]:
        if p.exists():
            for line in p.read_text(encoding="utf8").splitlines():
                line = line.split("#", 1)[0].strip().lower()
                if line:
                    hosts.add(line)
    return hosts


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", default=str(DATA_DIR / "sample.csv"))
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only")
    ap.add_argument("--out", default=str(RAW_DIR))
    a = ap.parse_args()
    with open(a.sample, encoding="utf8") as f:
        rows = list(csv.DictReader(f))
    if a.only:
        keep = set(a.only.split(","))
        rows = [r for r in rows if r["site"] in keep]
    if a.limit:
        rows = rows[: a.limit]
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    optout = load_optout()
    queue: asyncio.Queue = asyncio.Queue()
    for r in rows:
        queue.put_nowait(r)
    done = 0
    started = datetime.now(timezone.utc).isoformat()
    limits = httpx.Limits(max_connections=a.workers * 4, max_keepalive_connections=a.workers)
    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, follow_redirects=True, max_redirects=5,
                                 timeout=httpx.Timeout(TIMEOUT_S), limits=limits) as client:
        async def worker():
            nonlocal done
            while not queue.empty():
                row = queue.get_nowait()
                out = out_dir / f"{row['site']}.json"
                if out.exists():
                    done += 1
                    continue
                site = row["site"]
                if any(site == h or site.endswith("." + h) for h in optout):
                    rec = {"site": site, "excluded": "opt_out"}
                else:
                    try:
                        rec = await Site(client, row).run()
                    except Exception as e:
                        rec = {"site": site, "crawler_error": f"{type(e).__name__}: {e}"[:300]}
                out.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf8")
                done += 1
                if done % 50 == 0:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {done}/{len(rows)}", flush=True)

        await asyncio.gather(*(worker() for _ in range(a.workers)))
    (out_dir / "_run_meta.json").write_text(json.dumps({
        "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(), "sites": len(rows),
        "workers": a.workers, "harness_version": HARNESS_VERSION, "user_agent": USER_AGENT,
        "httpx": httpx.__version__,
    }, indent=2), encoding="utf8")


if __name__ == "__main__":
    asyncio.run(main())
