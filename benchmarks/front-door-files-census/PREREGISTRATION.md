# Pre-registration — The Front-Door Files Census (E3)

> **Status:** Frozen 2026-11-04 by commit on branch `research/l1-web-week`, before the census crawl. Two harness pilot sites (`glintbase.dev`, `example.com`) were fetched before freezing to test the crawler; they are excluded from results unless re-fetched in the census run.
> Any change after freezing is listed under *Deviations*.
> **Authors:** Glintbase Research · **Contact:** research@glintbase.dev
> **Programme:** `GLINTBASE_RESEARCH_PROGRAM_NOV2026.md` §5 E3 (internal). Shares its crawler with E1 ([`../web-census-crawler/`](../web-census-crawler/)).

## 1. Research questions (descriptive)

- **RQ1:** What share of sites publish each agent discovery file: `/.well-known/ai-catalog.json`, `/.well-known/ard.json` (or a `Link: rel="ard"` target), `/.well-known/api-catalog` (RFC 9727), `/.well-known/poppy.json`, `/.well-known/agent-card.json` (A2A), `/.well-known/http-message-signatures-directory` (Web Bot Auth), `/llms.txt`, `/sitemap.xml`?
- **RQ2:** Of those found, what share are **valid** (parse, and carry the minimum fields below) and served with the expected media type?
- **RQ3:** How often is an apparent file a **soft-404** — a catch-all page answered with 200 for any path?
- **RQ4:** Do the files link to each other (AI Catalog entry → a fetchable card; root `Link` headers for `rel="ard"`, `describedby`, `alternate type=text/markdown`)?

## 2. Sample (`../web-census-crawler/data/sample.csv`, flag `in_e3`)

The union, after de-duplication (leading `www.` dropped), of:
- Tranco top 5,000 (list `4672X`, retrieved 2026-10-12);
- the Glintbase leaderboard (103 URLs, 2026-11-04);
- MCP Registry publisher domains: the registrable domain (ICANN suffixes, tldextract 5.4.0 bundled list) of each host in the Edition 1 3,000-endpoint MCP sample.

**6,908 sites** (5,000 Tranco, 103 leaderboard, 1,854 MCP publisher domains, with overlap; SHA-256 in `sample_meta.json`). The Silent Wall's 150 domains are all within the Tranco top 5,000.

## 3. Requests (at most 15 per site; crawler `../web-census-crawler/harness/crawl.py` 1.0.0)

`GET /robots.txt` (shared with E1; robots is obeyed for `GlintbaseResearch`) · `GET /` (root `Link` header) · the six `/.well-known/` files above · `/llms.txt` · `/sitemap.xml` · two **control paths** with a random token per site: `/.well-known/glintbase-control-<hex16>` and `/glintbase-control-<hex16>.txt` · the root `Link rel="ard"` target if it isn't `/.well-known/ard.json` · the first URL listed in a fetched AI Catalog's `entries` (cross-link check). If the homepage redirects to another host on the same registrable domain, that host's `robots.txt` is also fetched (counted). Identity, pacing, opt-out, timeouts, retries, vantage point: as E1 §3. Discovery-file bodies under 256 KB are kept unpublished for validation.

## 4. Classification per file (`harness/analyze.py`)

| Outcome | Rule (first match) |
|---|---|
| `self_excluded` | robots.txt disallows the path for `GlintbaseResearch` |
| `error` | no HTTP status (DNS/TLS/connect/timeout) |
| `absent` | status ≠ 200 after redirects |
| `soft_404` | 200, but the body is HTML where JSON/text is expected, **or** the body hash equals the matching control path's body hash, **or** the control path also returned 200 with the same content type and the file fails its validity rule |
| `invalid` | 200, not a soft-404, fails the validity rule |
| `valid` | 200 and passes the validity rule |

**Validity rules (minimum structure; not full schema validation):**
- `ai-catalog.json`: JSON object with an `entries` array; each entry an object with a string `type` and either a `url` or a `data` object.
- `ard.json` / `rel="ard"` target: a JSON object. Media type recorded (`application/ard+json` per the IETF ARD draft-00 is programme item V4; until opened, "draft-00 media type" counts are labelled unverified). Fields reported descriptively.
- `api-catalog`: JSON object with a `linkset` array (RFC 9727 / RFC 9264).
- `poppy.json`: JSON object with string `protocol_version` matching `^\d+\.\d+$`, `organization.name`, and `organization.domain` (the rule used by Glintbase's scanner, draft 0.2).
- `agent-card.json`: JSON object with non-empty string `name` and `description`, and a `skills` array (A2A AgentCard minimum).
- `http-message-signatures-directory`: JSON object with a non-empty `keys` array whose members have `kty`.
- `llms.txt`: text, not HTML, whose first non-empty line starts with `# ` (llmstxt.org).
- `sitemap.xml`: body starts (after whitespace / XML declaration) with `<urlset` or `<sitemapindex`.

**Media type** is recorded per file and compared with the expected type (`application/ai-catalog+json`, `application/ard+json`, `application/linkset+json`, `application/json`, `application/http-message-signatures-directory+json`, `text/plain`/`text/markdown`, XML).

**Site-level:** `catch_all` = the `/.well-known/` control path returned 200. **Cross-links:** catalog → fetched entry is a JSON object (and, for `application/mcp-server-card+json` entries, passes the Server Card v1 required fields); root `Link` relations counted.

## 5. Analysis (`harness/compute_stats.py`; every published number from `data/summary.json`)

- Per file: shares `valid` / `invalid` / `soft_404` / `absent` / `error` / `self_excluded`, with **Wilson 95% intervals**, among reachable sites (homepage returned an HTTP status), overall and by source (Tranco top 1,000 / 1,001–5,000 / leaderboard / MCP publishers).
- Soft-404 rate per file and the share of catch-all sites. Media-type conformance among valid files.
- Co-occurrence of files; cross-link counts.
- The answer to "which discovery file should a site publish today" is written from these adoption and validity numbers only, and says so.
- Optional Lighthouse Agentic Browsing subsample: **not run this week** (dropped; stated).

## 6. Validation gate

30 site × file results, seed `20261104`, stratified by outcome (all `valid` non-sitemap/non-llms files up to 10 included). Each is re-fetched independently (Node `fetch`, same identity) and judged by hand; agreement recorded in `data/validation.csv`. **≥ 90%** required, else fix and re-run. The founder spot-checks 5 and signs before publication.

## 7. Ethics

Public paths only, honest identity, robots obeyed, ≤ 15 requests per site, ≤ 1 request/second per site, opt-out honoured. No ranking of named sites by "missing files"; a per-site derived table is published.

## 8. What this can't claim

- Whether any agent reads these files (E4 and E10 address that).
- Full schema validity: the rules are minimum structure checks.
- Files at other paths, or served only to some user agents or regions; one vantage point, one pass.

## Deviations

1. **2026-11-04, ~3 minutes into the crawl, before any analysis. Unreachable sites stop early; 32 sites in parallel instead of 16.**
   - **Why:** the first 28 sites showed throughput of about 10 sites a minute (an ~11 h crawl), mostly because sites whose host doesn't resolve (e.g. bare CDN or API domains in the Tranco list) still received every planned request, each failing.
   - **Change (crawler 1.0.1):** if `robots.txt` and the homepage both fail below HTTP (DNS, TLS, connect or timeout), the site's remaining requests are not sent. Such sites were already "unreachable" and excluded from every denominator, so no outcome changes. Parallelism went from 16 to 32 sites; the per-site limit (sequential, ≥ 1 s apart) is unchanged.
   - **Data:** the 28 sites completed under 1.0.0 were set aside (`data/raw_discarded_v1_0_0/`, unpublished) and re-crawled under 1.0.1 at the end of the crawl, because the connectivity log shows a total failure at 21:11:22Z during that first start. Only request outcome counts (error types) were looked at before this change.

2. **2026-11-04, during the crawl, on partial data (~450 sites), before any analysis of results. Two validity-rule implementation fixes.** A spot-check of `invalid` outcomes found implementation errors against §4's rules, not rule changes:
   - `sitemap.xml`: the XML prolog skip handled only the declaration, so sitemaps starting with an `<?xml-stylesheet …?>` processing instruction (common in WordPress) were marked invalid. The prolog skip now covers any processing instruction and comment.
   - `llms.txt` over 256 KB: the crawler doesn't keep bodies over 256 KB, so these were marked invalid. They're now judged on media type (`text/plain` or `text/markdown`, not HTML) and flagged "body over 256 KB, judged on media type"; their count is reported.
   The independent checker was given the same corrections.

3. **2026-11-09, after the crawl, before any results analysis. Network failures during the crawl; affected sites re-crawled.**
   - **What was found:** the first look at E1's reachability (a pre-analysis data-quality check) showed 508 of 1,087 sites "unreachable", including 91 of the 103 leaderboard sites (e.g. well-known AI and developer-platform domains), mostly with DNS errors. The connectivity log has total failures at 21:35Z and 22:18–22:31Z. Every site that finished after 22:10Z failed DNS, and about a quarter of earlier sites did too: the 32-site parallel crawl most likely overloaded the residential link's DNS resolution, on top of the outages. Only reachability and error-type counts were seen; no Content-Signal or discovery-file results were looked at.
   - **Rule (fixed before re-crawling):** re-crawl every site whose `robots.txt` **or** homepage request failed below HTTP (DNS, TLS, connect, timeout, protocol error), and every site whose record finished after 2026-11-04T22:00Z, plus the 28 first-start sites already set aside. 
   - **Re-crawl settings:** crawler 1.0.1 unchanged, **12 sites in parallel** (down from 32), with a per-minute connectivity log; nothing else from this lane runs at the same time. A site that fails again is reported as unreachable. If the second pass also shows widespread failures in a time window, those sites get one more pass and the report says so.
   - **Applied:** the rule selected 6,133 of 6,908 sites, so the first pass is unusable as a whole. **All 6,908 sites are re-crawled** on 2026-11-09 (one date for the whole census), and the entire first pass is archived unpublished in `data/raw_discarded_pass1/`. Its results are not analysed.
   - **Third pass (2026-11-13 23:59Z – 2026-11-14 01:34Z, before any results analysis).** The second pass ran normally from 06:48 to about 08:20Z on 2026-11-09 (2,636 sites; 88 per-minute connectivity checks, all ok). The workstation then slept: the connectivity log has no lines between 08:20 and 13:50Z. It woke at 13:50Z with no internet (connectivity FAIL from 13:52Z), and the crawler finished the remaining 4,272 sites by 13:58Z, 4,262 of them with DNS failures, including 91 of the 103 leaderboard sites. Under the rule above, those 4,272 sites (every record finished after 08:30Z) get one more pass; their second-pass records are archived unpublished in `data/raw_discarded_pass2_tail/`. The 2,636 sites from 06:48–08:20Z are kept: all 12 leaderboard sites in that window were reachable, and none of 40 randomly sampled DNS failures from that window resolved when re-checked on 2026-11-14. Third-pass settings are unchanged (crawler 1.0.1, 12 sites in parallel), with a new connectivity log `data/connectivity_pass3.txt` and the workstation held awake. Only reachability, error types and crawl times were looked at. **Consequence:** the census now spans two dates, 2026-11-09 (2,636 sites) and 2026-11-13/14 UTC (4,272 sites, one continuous run from 23:59Z to 01:34Z); the report gives the date for each record.
