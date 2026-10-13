# Pre-registration — The Silent Wall (2026)

> **Status:** Frozen 2026-10-12 by local commit **after** the Part 1 census was collected (see Deviation 1) and **before** any Part 2 request.
> **Authors:** Glintbase Research · **Contact:** research@glintbase.dev

## 1. Research questions (descriptive)

- **RQ1 (policy):** What do popular websites' `robots.txt` files say about vendor-documented AI agents, split by purpose (training / search / user-initiated)?
- **RQ2 (behaviour):** How often is a **self-declared, unverified** research agent challenged or blocked at the edge, compared with a generic unlabelled HTTP client and a headless browser, fetching the same public pages from the same IP?
- **RQ3 (disagreement):** Among sites whose `robots.txt` permits our agent's request, how often does the edge still challenge or block it?
- **RQ4 (variation):** How do RQ2 and RQ3 vary by sector and by CDN/WAF vendor? (Descriptive only; cells are small.)

**Scope.** This measures treatment of *declared but unverified* agents. It says nothing about how sites treat vendors' **verified** crawlers (OpenAI, Anthropic and others), which edges verify by IP range, reverse DNS or Web Bot Auth signatures. We do not imitate those crawlers.

## 2. Sample

- **Source:** Tranco list **`4672X`** (retrieved 2026-10-12).
- **Sectors (30 domains each, 150 in total):** SaaS/B2B software (`saas`), e-commerce/retail/travel booking (`ecommerce`), finance (`finance`), news/media/publishing (`media`), developer tools/infrastructure (`devtools`).
- **Labelling rule:**
  - Walk Tranco from rank 1 and assign each registrable domain to a sector by the primary purpose of its public homepage, until each sector has 30.
  - **Excluded:** CDNs, ad-tech/analytics, DNS/registrar/hosting endpoints, app-instance hosts (e.g. `*.force.com`), government, education, non-profits/open-source foundations, adult, gambling, gaming, search engines/portals/social networks, hardware/telecom, conglomerates' generic portals, classifieds, and AI chat products.
  - Only the first-ranked domain of a brand is kept (e.g. `amazon.com`, not `amazon.de`).
  - `finance` means regulated financial-services or payments firms: banks, payment networks/processors, brokerages, exchanges, BNPL, plus `tradingview.com`, `intuit.com`.
- **Labeller:** a single labeller (Claude, under the researcher's direction). **Limitation:** beyond rank 1,500, finance and developer-tool candidates were found with a keyword screen and then labelled by hand, so domains with uninformative names may be missed. Rank ranges per sector: e-commerce 27–975, SaaS 63–687, media 156–705, devtools 2–1975, finance 131–3158.
- **The sample is fixed in `data/sample/domains.csv`.**

## 3. Part 1 — Policy census (`harness/census.py`)

- **Fetch:** one `GET https://<domain>/robots.txt` per domain with the research identity, ≤ 5 redirects. Concurrency is 2; a network-level failure is retried once after 10 s, and the error type is recorded. An HTML response or non-200 status counts as "no robots.txt", so everything is allowed.
- **Parser:** Protego 0.7.0 (RFC 9309).
- **Recorded per token:** whether a `User-agent` group names it explicitly, and whether `/` is allowed. **Tokens** (from vendor documentation, checked 2026-10-12):
  - OpenAI: `GPTBot`, `OAI-SearchBot`, `ChatGPT-User`
  - Anthropic: `ClaudeBot`, `Claude-SearchBot`, `Claude-User`
  - Perplexity: `PerplexityBot`, `Perplexity-User`
  - Google: `Google-Extended`, and `Googlebot` as a control
  - Others: `Applebot-Extended`, `CCBot`, `Meta-ExternalAgent`, `Bytespider`
- **Caveat:** OpenAI and Anthropic state that user-initiated agents may not follow `robots.txt`, so the policy is reported as written.
- **Page list for Part 2:** the homepage plus up to 3 same-host URLs, taken in order from the first sitemap (the robots `Sitemap:` line, else `/sitemap.xml`; one level of sitemap index followed), excluding login/cart/checkout/account/auth URLs. It is fixed in `data/sample/pages.jsonl` before Part 2.

## 4. Part 2 — Edge behaviour (`harness/edge_probe.py`)

| Identity | Client | User-Agent |
|---|---|---|
| `agent` | httpx 0.28.1 | `GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot; research@glintbase.dev)`. Obeys `robots.txt` for token `GlintbaseResearch`; disallowed pages are `self_excluded`, not fetched |
| `script` | httpx 0.28.1 | library default (`python-httpx/0.28.1`) |
| `browser` | Chromium 148 headless via Playwright 1.63 | default (`… HeadlessChrome/148 …`). Waits 5 s after `domcontentloaded` so automatic JS challenges can resolve; the final state is recorded |

- **Order and pacing:**
  - identity order is randomised per domain and round (seeded by SHA-256 of `domain|round`);
  - fresh cookies for each (domain, identity);
  - ≤ 1 request/s within an identity, and ≥ 30 s between identities on the same domain;
  - up to 4 domains in parallel (Deviation 3);
  - never concurrently with another study's traffic on the same connection.
- **Rounds:** two, run back-to-back on 2026-10-12 (a one-day schedule).
- **Vantage point:** one residential connection (AS36873 Airtel Networks, Nigeria). **Limitation:** edge decisions depend on IP reputation and geography; all identities share the IP, so the comparison between identities is controlled, but absolute rates may differ elsewhere.
- **Stored:** status, selected headers, cookie *names*, visible-text length, title, and challenge-marker hits. Page bodies are not stored.

## 5. Classification (`harness/analyze.py`), per request

| Outcome | Rule (first match) |
|---|---|
| `self_excluded` | agent only: `robots.txt` disallows the page for `GlintbaseResearch` |
| `error` | timeout, TLS or connection failure, or 5xx |
| `challenge` | header `cf-mitigated: challenge`, `x-amzn-waf-action: challenge/captcha` or `x-vercel-mitigated: challenge`; **or** a challenge marker (Cloudflare interstitial, Akamai `sec-if-cpt`/`bm-verify`, DataDome `captcha-delivery`, HUMAN `px-captcha`, Imperva `_Incapsula_Resource`, AWS WAF, Kasada, CAPTCHA widget) on a non-2xx response or a page with < 2,000 visible characters |
| `block` | 401/403/406/451 without challenge markers, or a 2xx page whose only content is a vendor block page (`cloudflare_block`/`akamai_block` marker with < 2,000 visible characters) |
| `rate_limited` | 429 |
| `ok` | 2xx with ≥ 200 visible characters |
| `thin` | 2xx with < 200 visible characters (e.g. JS-only shell for non-browser clients) |
| `other` | anything else (e.g. 404 on a sitemap URL) |

- **Domain-level outcome per identity:** the homepage outcome (primary). Secondary: the "worst" outcome across pages, ordered `block` > `challenge` > `rate_limited` > `error` > `thin` > `other` > `ok`.
- **CDN/WAF vendor per domain:** from response headers across identities (Cloudflare `cf-ray`/`server: cloudflare`; Akamai `akamai-grn`/`AkamaiGHost`; CloudFront `x-amz-cf-id`; Fastly `x-served-by: cache-…`; Vercel `x-vercel-id`; DataDome `x-datadome`; Imperva `x-iinfo`/`x-cdn: Imperva`; Azure `x-azure-ref`; else `other/unknown`).

## 6. Analysis

- Proportions with Wilson 95% intervals.
- **RQ2:** paired comparisons between identities on the homepage outcome "challenged or blocked" use **McNemar's exact test** (agent vs browser, agent vs script, script vs browser), reported with discordant counts.
- **RQ3:** among domains where `robots.txt` allows `GlintbaseResearch` on `/`, the share where the agent's homepage outcome is `challenge` or `block`.
- **Stability:** per-identity agreement of homepage outcome between rounds, with Cohen's κ.
- **Validation gate before publishing:** 20 stratified domain×identity results are re-checked by hand by viewing the stored headers and markers, and the domain is reopened in a normal browser where relevant. **≥ 90% agreement is required.**
- Results are aggregated. Named domains appear only for public `robots.txt` policy facts.

## 7. Ethics

Honest identities only; no CAPTCHA solving or bypassing (a challenge is recorded, never evaded); public pages only; about 12 requests per site per round; public bot page with opt-out; no bodies stored.

## Deviations

1. **Part 1 census collected before freezing; re-run with lower concurrency.**
   - **What happened:** the first census run (concurrency 8, no retry) produced 83/150 fetch failures. 58 of those succeeded when fetched sequentially, so the failures were mostly self-inflicted load on the residential connection.
   - **Action:** the census was re-run in full with concurrency 2 and one retry (`data/robots/census_run.log`), and that run is the one reported. Before freezing, only fetch-status counts and one token count (`GPTBot` named on 18 domains in the discarded first run) were looked at; no policy analysis was done.
   - **Result:** 10 domains remain unreachable from this vantage point for every client, including a headless browser (`coinbase.com`, `kraken.com`, `binance.com`, `sberbank.ru`, `vtb.ru`, `tbank.ru`, `alfabank.ru`, `bancodevenezuela.com`, `wsj.com`, `npr.org`). They are reported as such.

2. **Connection outage during Part 2; affected results discarded and re-probed (2026-10-13, before any analysis of Part 2).**
   - **What happened:** the residential connection failed from about **19:09 UTC on 2026-10-12** until at least 20:10 UTC. From that point every request from every identity failed, including domains that had loaded moments earlier.
   - **Discarded:**
     - all of round 2 (19:42–20:10 UTC, every request an error);
     - every round-1 domain where any identity started at or after 19:09:00 UTC (18 domains, mostly finance, the tail of the run order).
     All of it is archived in `data/edge/_discarded/`.
   - **Action:** connectivity was confirmed restored at 00:51 UTC on 2026-10-13. Those round-1 domains were then re-probed with the unchanged harness, and round 2 was re-run in full.
   - **Consequence:** round 1 now spans two sessions about 6 hours apart. Before this decision, only error counts and timestamps were inspected.

3. **Browser-identity measurement defects found after round 1; both rounds re-run in full (2026-10-13).**
   - **How it was found:** a first analysis of round 1 showed a 22% homepage error rate for `browser`, against 9–10% for `agent` and `script`. Checking the cases where only the browser failed revealed two harness defects:
     - **Timeouts:** with 6 domains in parallel on the residential link, full page loads exceeded the 20 s limit. Loaded one at a time, the same pages took 5–8 s.
     - **Hidden error responses:** when a site returns an error status with an empty body, Chromium raises `net::ERR_HTTP_RESPONSE_CODE_FAILURE` instead of returning the response, so those were recorded as `error` instead of e.g. `block`.
   - **Fix:**
     - the main-document response is captured even when navigation raises;
     - the browser page-load timeout is 45 s (HTTP clients unchanged at 20 s);
     - up to **4** domains in parallel;
     - the first line of each error message is stored.
   - **Action:** round 1 and the partial round 2 were archived (`data/edge/_discarded/`), and **both rounds were re-run in full, for all three identities**, so conditions are identical across identities.
   - **Disclosure:** this decision was made after round-1 outcome tables had been seen. The classification rules (§5) and analysis (§6) are unchanged.


