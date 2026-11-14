# Content Signals in the wild: robots.txt, response headers and Markdown (E1)

**Glintbase Research · November 2026 · DRAFT, not for publication** (needs: founder validation sign-off, review)
Pre-registration: [`PREREGISTRATION.md`](../PREREGISTRATION.md) (frozen in commit `3ddbc9e` before the crawl; Deviations 1–3) · Data: [`data/`](../data) · Analysis: [`harness/`](../harness) · Crawler: [`../web-census-crawler/`](../../web-census-crawler/)

Every number below comes from [`data/summary.json`](../data/summary.json), produced by `harness/analyze.py` and `harness/compute_stats.py`. Percentages carry Wilson 95% intervals.

---

## Summary

We checked **1,121 sites** (the Glintbase leaderboard, The Silent Wall's 150 domains and the Tranco top 1,000) for **Content Signals**, the AI-use preferences a site can state in `robots.txt` (`Content-Signal:` lines) or in a `Content-Signal` HTTP response header. We compared what each site says in `robots.txt` with what its homepage says in headers, both as HTML and when asked for Markdown. **754 sites were reachable** and form the denominator; the other 367 are mostly Tranco infrastructure hosts (CDN, DNS, API domains) that serve no website.

- **Almost nobody states Content Signals.** 93.5% [91.5–95.0] of sites state none, anywhere. 6.5% [5.0–8.5] state some: 4.2% [3.0–5.9] in `robots.txt` and 2.9% [1.9–4.4] in a response header.
- **Agent-focused companies use them more.** 22.5% [15.5–31.6] of leaderboard sites state a signal (23 of 102), against 3.9% [2.7–5.7] of the Tranco top 1,000 and 8.0% [4.5–13.8] of The Silent Wall's 150 popular sites.
- **Signals rarely appear in both places, so there's little to conflict.** Only 5 sites state signals in both `robots.txt` and a header: 4 agree and **1 conflicts** (`robots.txt` says `ai-train=no`, the Markdown response says `ai-train=yes`). With 5 cases, the conflict rate among them (20.0%, interval 3.6–62.4) means almost nothing.
- **Markdown is where the headers are.** 7.3% [5.6–9.4] of sites serve Markdown when asked (31.4% of the leaderboard). Among those 55, 38.2% send a `Content-Signal` header on the Markdown response, but only 1 sends one on the HTML response. In 40.0% [28.1–53.2] of them, the Markdown response's signal differs from the HTML response's, almost always because only the Markdown response has one.
- **The header looks like a CDN default.** Every one of the 22 sites with a header signal sends the same value, `ai-input=yes, ai-train=yes, search=yes`. 21 of the 22 are on Cloudflare: 9.5% of Cloudflare-fronted sites send a header signal, against 0.4% of sites whose CDN we couldn't identify, and none behind CloudFront, Akamai, Fastly or Vercel. 95.5% of header-signalling sites send it only on Markdown or docs Markdown responses.
- **`robots.txt` signals are more varied.** Among robots policies: `search=yes` 30; `ai-input=yes` 24, `no` 2; `ai-train=yes` 16, `no` 13. 8 sites also set signals for named crawlers.

## 1. Why this study

Content Signals let a site say, separately, whether its content may be used for search, as AI input (e.g. retrieval for an answer) or for AI training. They can be stated in `robots.txt` or sent as a response header. A vendor study (AI Ranked, 2026-10-28; labelled "vendor") reported that many Markdown homepages carry a training-permissive header that may not match the site's own policy. We measured how often that happens on a defined population with an open method.

## 2. Method (summary of the pre-registration)

- **Sample:** 1,121 sites: the leaderboard (103 hosts, read 2026-11-04), The Silent Wall's 150 domains, and the Tranco top 1,000 (list `4672X`, the list The Silent Wall used), de-duplicated.
- **Requests (≤ 8 per site):** `robots.txt`; the homepage as HTML; the homepage with `Accept: text/markdown`; a Markdown twin if advertised; up to 2 docs pages as HTML and Markdown. Honest identity `GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot; research@glintbase.dev)`, `robots.txt` obeyed for that token, ≤ 1 request/second per site.
- **Robots policy:** the `*` group's `Content-Signal` values (or lines before any group). **Header signals:** every `Content-Signal` header seen on the site.
- **Classes:** `none`, `robots_only`, `header_only`, `agree`, `conflict` (a key with different values in `robots.txt` and a header, or between two headers).
- **Vantage point:** one residential connection in Nigeria.

### Crawl history (Deviations 1–3)
The first crawl (2026-11-04) was ruined by DNS and network failures on the residential link, and was discarded as a whole before any results were looked at. The census was re-run on **2026-11-09**: 2,636 sites were crawled normally, then the machine slept and woke offline, and every site crawled after that failed. Those 4,272 sites were crawled again on **2026-11-13/14 UTC** with no connectivity failures. Each record carries its crawl time. For E1, that means a site's data is from either 2026-11-09 or 2026-11-13/14.

## 3. Results

### 3.1 Where sites state Content Signals (n = 754 reachable sites)

| Class | Sites | Share |
|---|---|---|
| `none` | 705 | 93.5% [91.5–95.0] |
| `robots_only` | 27 | 3.6% [2.5–5.2] |
| `header_only` | 17 | 2.3% [1.4–3.6] |
| `agree` | 4 | 0.5% [0.2–1.4] |
| `conflict` | 1 | 0.1% [0.0–0.7] |

### 3.2 By sample source

| Source | Reachable | Any signal | `robots.txt` | Header | Serves Markdown |
|---|---|---|---|---|---|
| Leaderboard | 102 | 23 (22.5% [15.5–31.6]) | 18 | 9 | 32 (31.4%) |
| The Silent Wall's 150 | 137 | 11 (8.0% [4.5–13.8]) | 7 | 5 | 9 (6.6%) |
| Tranco top 1,000 | 639 | 25 (3.9% [2.7–5.7]) | 14 | 13 | 22 (3.4%) |

Sources overlap (some Silent Wall domains are in the Tranco top 1,000), so rows don't sum to the total.

### 3.3 By CDN (descriptive; cells under 30 sites are small)

| CDN | Sites | Header signal | Serves Markdown | Markdown responses with a header |
|---|---|---|---|---|
| Cloudflare | 220 | 21 (9.5%) | 30 | 20 of 30 |
| Other / unknown | 259 | 1 (0.4%) | 6 | 1 of 6 |
| CloudFront | 100 | 0 | 4 | 0 of 4 |
| Akamai | 66 | 0 | 0 | — |
| Fastly | 60 | 0 | 0 | — |
| Vercel | 43 | 0 | 15 | 0 of 15 |

### 3.4 What this suggests (interpretation, not measurement)
The header signal on the web today is almost entirely one value on one CDN's Markdown responses. That matches Cloudflare's documented Markdown-for-Agents behaviour (programme item V2; the documentation still has to be opened and cited before publication). If so, most header signals reflect a CDN default rather than a choice by the site. We can't tell which from outside.

## 4. What this can't claim

- **Whether any AI company honours `Content-Signal`** in either place.
- **Intent.** A header may be a CDN default the site never chose (see §3.4).
- **Coverage of the site.** Only the homepage and up to 2 docs pages were fetched; a site can set different signals elsewhere.
- **Small numbers.** Conflicts can only occur where signals appear in both places, and only 5 sites do that. The conflict rate isn't estimable with useful precision.
- **One vantage point, two crawl dates** (§2). Responses can vary by location and bot treatment, and a challenge page's headers are recorded as what we got.

## 5. Validation

30 sites (seed `20261104`, stratified by class, with every `conflict` site included) were re-fetched one by one by an independent Node checker written for the purpose, and classified by hand from its output. **Agreement: 30/30** ([`data/validation.csv`](../data/validation.csv)). **Founder sign-off pending** (spot-check of 5; see [`../REVIEW_QUEUE.md`](../REVIEW_QUEUE.md)).

## 6. Before publication

- Founder validation sign-off.
- Open and cite Cloudflare's Markdown-for-Agents documentation (V2) and the AI Ranked study (V1) before comparing with them.
- If any site or CDN is named critically, a 7-day right of reply. The draft names none.

*Glintbase sells Agent Readiness Score audits. Content Signals aren't part of the current score; a check based on this study is planned for ARS 3.4.*
