# Pre-registration — Content-Signal Consistency Census (E1)

> **Status:** Frozen 2026-11-04 by commit on branch `research/l1-web-week`, before the census crawl. Two harness pilot sites (`glintbase.dev`, `example.com`) were fetched before freezing to test the crawler; they are excluded from results unless re-fetched in the census run.
> Any change after freezing is listed under *Deviations*.
> **Authors:** Glintbase Research · **Contact:** research@glintbase.dev
> **Programme:** `GLINTBASE_RESEARCH_PROGRAM_NOV2026.md` §5 E1 (internal). Shares its crawler with E3 ([`../web-census-crawler/`](../web-census-crawler/)).

## 1. Research questions (descriptive)

- **RQ1:** What share of sites state AI-use preferences with **Content Signals**, in `robots.txt`, in the `Content-Signal` HTTP response header, or both?
- **RQ2:** Where a site states them in more than one place, how often do they **disagree** — e.g. `robots.txt` says `ai-train=no` and a response header says `ai-train=yes`?
- **RQ3:** How often does a site serve Markdown to `Accept: text/markdown`, and what `Content-Signal` does that Markdown response carry compared with the HTML response?
- **RQ4:** How do RQ1–RQ3 vary by CDN vendor (descriptive)?

## 2. Sample (`../web-census-crawler/data/sample.csv`, flag `in_e1`)

The union, after de-duplication (leading `www.` dropped), of:
- the Glintbase leaderboard: 103 URLs read from `scan.glintbase.dev/leaderboard` on 2026-11-04 (the scanned host is the site, e.g. `ai.meta.com`);
- The Silent Wall's 150 domains;
- the Tranco top 1,000 (list `4672X`, retrieved 2026-10-12, the same list The Silent Wall used).

**1,121 sites** (sample SHA-256 in `../web-census-crawler/data/sample_meta.json`). The homepage is `https://<site>/`.

## 3. Requests (at most 8 per site; crawler `../web-census-crawler/harness/crawl.py` 1.0.0)

1. `GET /robots.txt`
2. `GET /` with `Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8`
3. the homepage's final URL with `Accept: text/markdown`
4. the Markdown twin, if the homepage advertises one (`Link: <…>; rel="alternate"; type="text/markdown"` or `<link rel="alternate" type="text/markdown">`)
5–8. up to **2 docs pages**: the first two links in the homepage HTML, in document order, on the same registrable domain, whose host starts with `docs.`/`doc.`/`developer(s).`/`dev.`/`api.`/`learn.`/`reference.` or whose first path segment is `docs`/`doc`/`documentation`/`developer(s)`/`api`/`reference`/`guide(s)`/`learn`, excluding login/cart/checkout/account/auth/register URLs. Each is fetched as HTML, then as Markdown. If a docs page is on another host, that host's `robots.txt` is fetched first. The list is truncated so the site total stays ≤ 8.

- **Identity:** `GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot; research@glintbase.dev)`. **robots.txt is obeyed** for the token `GlintbaseResearch` (Protego 0.7.0); a disallowed request is recorded `self_excluded` and not sent.
- **Pacing:** requests to a site are sequential with ≥ 1 s between them (≤ 1 request/second per site); 16 sites in parallel; 15 s timeout; ≤ 5 redirects; one retry after 10 s on a connection error or timeout.
- **Opt-out:** `../web-census-crawler/optout.txt` and the Edition 1 MCP opt-out list are honoured.
- **Stored:** status, final URL, selected headers (incl. `Content-Signal`, `Content-Type`, `Vary`, `Link`, CDN headers), body length and hash; the full `robots.txt`. HTML bodies are not stored. Raw records stay unpublished; derived per-site fields are published.
- **Vantage point:** the researcher's residential connection; IP/ASN in `../web-census-crawler/data/run_notes.md`.

## 4. Definitions

- **Content Signals** (contentsignals.org; the `Content-Signal` directive in `robots.txt` and the `Content-Signal` response header used by Cloudflare). Value syntax: comma-separated `key=yes|no`. Keys analysed: `search`, `ai-input`, `ai-train`; other keys are recorded and counted. Verification of the Cloudflare default header (`ai-train=yes, search=yes, ai-input=yes` on Markdown responses) is programme item V2; until it is opened, it is not cited as fact.
- **robots.txt signals:** `Content-Signal:` lines (case-insensitive) attached to the user-agent group they appear in (lines before any `User-agent:` line are "global"). The **robots policy** used for comparison is the `*` group's signals (or global lines if there is no `*` group signal). Signals in named groups are reported separately.
- **Header signals:** the `Content-Signal` header on (a) the homepage HTML response, (b) the homepage Markdown response, (c) docs responses. Multiple header instances are joined.
- **Markdown served:** the response to `Accept: text/markdown` has status 2xx and `Content-Type` `text/markdown` or `text/x-markdown`.
- **Reachable:** the homepage HTML request returned an HTTP status. Unreachable sites are reported and excluded from denominators of RQ1–RQ3.

## 5. Classification (per site, primary)

Comparing the robots policy with every header value observed on the site (HTML, Markdown, docs):

| Class | Rule |
|---|---|
| `none` | no Content Signal in robots.txt and none in any response header |
| `robots_only` | robots.txt has signals; no response header has any |
| `header_only` | at least one response header has signals; robots.txt has none |
| `conflict` | both present, and for at least one key present in both, a header value differs from the robots value (or two headers differ from each other) |
| `agree` | both present, and no key present in both differs |

Secondary per-site flags: `ai_train_conflict_no_yes` (robots `ai-train=no`, some header `ai-train=yes`), `md_header_differs_from_html` (Markdown and HTML headers differ, both fetched), `md_served`, `header_on_md_only`, CDN vendor (The Silent Wall's header rules).

## 6. Analysis (`harness/compute_stats.py`; every published number comes from `data/summary.json`)

- Shares with **Wilson 95% intervals**, overall and by sample source (leaderboard / Silent Wall / Tranco top 1,000) and by CDN vendor (descriptive; small cells flagged).
- Value distributions for each key, robots vs header.
- No inferential tests are planned.
- Named sites appear only for public facts (what a robots file or a public response header says), never in a "worst offenders" list; a per-site table of derived fields is published in `data/`.

## 7. Validation gate

30 sites drawn with seed `20261104`, stratified by class (all `conflict` sites up to 10 included). Each is re-fetched independently (Node `fetch`, same identity, `robots.txt` + HTML + Markdown) and classified by hand; agreement on class recorded in `data/validation.csv`. **≥ 90% agreement** required; otherwise fix and re-run. A difference caused by the site changing between fetches is recorded as such. The founder spot-checks 5 and signs (name, date, scope) before publication.

## 8. Ethics

Public pages only, honest identity, robots.txt obeyed, ≤ 8 requests per site, ≤ 1 request/second per site, opt-out honoured. Vendors named critically (e.g. a CDN whose default contradicts a site's robots policy) get a 7-day right of reply before publication.

## 9. What this can't claim

- Whether any AI company honours `Content-Signal` in either place.
- Intent: a header may be a CDN default the site never chose.
- Pages beyond the homepage and up to 2 docs pages; a site can set different signals elsewhere.
- One vantage point, one day; responses can vary by geography and bot treatment (a challenged request shows the challenge page's headers, which are reported as such).

## Deviations

1. **2026-11-04, ~3 minutes into the crawl, before any analysis. Unreachable sites stop early; 32 sites in parallel instead of 16.**
   - **Why:** the first 28 sites showed throughput of about 10 sites a minute (an ~11 h crawl), mostly because sites whose host doesn't resolve (e.g. bare CDN or API domains in the Tranco list) still received every planned request, each failing.
   - **Change (crawler 1.0.1):** if `robots.txt` and the homepage both fail below HTTP (DNS, TLS, connect or timeout), the site's remaining requests are not sent. Such sites were already "unreachable" and excluded from every denominator, so no outcome changes. Parallelism went from 16 to 32 sites; the per-site limit (sequential, ≥ 1 s apart) is unchanged.
   - **Data:** the 28 sites completed under 1.0.0 are kept (their records are a superset of what 1.0.1 would send). Only request outcome counts (error types) were looked at before this change.
