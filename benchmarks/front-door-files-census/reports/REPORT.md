# The front-door files census: which agent discovery files do sites publish? (E3)

**Glintbase Research · November 2026 · DRAFT, not for publication** (needs: founder validation sign-off, review)
Pre-registration: [`PREREGISTRATION.md`](../PREREGISTRATION.md) (frozen in commit `3ddbc9e` before the crawl; Deviations 1–3) · Data: [`data/`](../data) · Analysis: [`harness/`](../harness) · Crawler: [`../web-census-crawler/`](../../web-census-crawler/)

Every number below comes from [`data/summary.json`](../data/summary.json), produced by `harness/analyze.py` and `harness/compute_stats.py`. Percentages carry Wilson 95% intervals. Section 5 is **exploratory and not pre-registered**.

---

## Summary

We checked **6,908 sites** (Tranco top 5,000, the Glintbase leaderboard and the domains of MCP Registry publishers) for eight front-door files, each tested against a minimum validity rule and a random control path. **5,257 sites were reachable** and form the denominator.

- **Two files are common; the agent-specific ones are not.** `sitemap.xml` is valid on 53.3% [52.0–54.7] of sites and `llms.txt` on 34.9% [33.6–36.2]. Every agent-discovery file is under 8%: `/.well-known/api-catalog` 7.5% [6.8–8.2], `ai-catalog.json` 3.7% [3.3–4.3], `agent-card.json` 3.4% [2.9–3.9], `ard.json` 1.5% [1.2–1.9], the Web Bot Auth key directory 0.8% [0.6–1.1], `poppy.json` 0.5% [0.4–0.8]. 10.7% [9.9–11.6] of sites have at least one valid agent-discovery file.
- **Adoption is concentrated among agent-builders.** MCP Registry publishers: `llms.txt` 76.6%, API catalog 19.5%, AI Catalog 9.6%, agent card 9.6%. Leaderboard: `llms.txt` 51.0%, API catalog 12.7%, AI Catalog 6.9%. Tranco top 1,000: `llms.txt` 16.3%, every agent file under 2%.
- **Most "200 OK" answers on agent paths are fake.** Among 200 responses, 60–95% are soft-404s (catch-all pages returned for any path) on the six `/.well-known/` agent files, against 20.3% for `llms.txt` and 12.8% for `sitemap.xml`. 11.1% [10.3–12.0] of sites answer 200 to any `/.well-known/` path. A scanner that counts a 200 as "present" would overstate adoption several times over.
- **Media types are often wrong.** 79 of 197 valid AI Catalogs use `application/ai-catalog+json`; the rest use `application/json`. 1 of 78 `ard.json` files uses `application/ard+json`, and most valid `ard.json` files look like AI Catalog documents (`entries` 77, `specVersion` 63). API catalogs mostly get it right (382 of 394 `application/linkset+json`).
- **Files rarely link to each other.** 34 sites (0.6%) send `Link: rel="ard"`. Of 194 AI Catalog first entries we followed, 155 returned a JSON object and 86 a valid MCP Server Card.
- **One operator inflates the MCP-publisher numbers (exploratory, §5).** 76 near-identical sites from one operator share a single API-catalog template. Counting that operator once, the MCP-publisher API-catalog rate drops from 19.5% to 15.9% [14.3–17.8], and "any agent-discovery file" across all sites from 10.7% to 9.4% [8.6–10.2].

**Answer to "which discovery file should a site publish today?"** On this evidence: a valid `sitemap.xml` and `llms.txt` are the only files with real adoption. Among agent-specific files, the RFC 9727 API catalog is the most adopted and the one most often served correctly. No agent-discovery file reaches even 2% of the Tranco top 5,000. This answers what sites publish, not whether any agent reads them (§6).

## 1. Why this study

Agent-discovery proposals keep multiplying: AI Catalogs, ARD, RFC 9727 API catalogs, Personal Agent Protocol (`poppy.json`), A2A agent cards, Web Bot Auth key directories, plus `llms.txt`. Sites and our customers ask which to publish. Glintbase's scanner gives these files 0–1 points. This census measures what's actually published and valid on a defined population.

## 2. Method (summary of the pre-registration)

- **Sample:** 6,908 sites: Tranco top 5,000 (list `4672X`), the leaderboard (103 hosts), and 1,854 MCP Registry publisher domains (registrable domains of the hosts in our MCP reliability sample).
- **Requests (≤ 15 per site):** `robots.txt`; the homepage (for `Link` headers); the six `/.well-known/` files; `/llms.txt`; `/sitemap.xml`; two random control paths (`/.well-known/glintbase-control-<hex>` and `/glintbase-control-<hex>.txt`); a `Link rel="ard"` target if present; the first AI Catalog entry URL. Honest identity, `robots.txt` obeyed, ≤ 1 request/second per site.
- **Outcome per file:** `valid`, `invalid`, `soft_404` (HTML where JSON/text/XML was expected, the same body as the control path, or invalid while the control path also returned 200 with the same type), `absent`, `error`, `self_excluded`.
- **Validity rules** are minimum-structure checks: e.g. AI Catalog = JSON with an `entries` array of typed entries; API catalog = JSON with a `linkset` array; `llms.txt` = text whose first line starts with `# `.

### Crawl history (Deviations 1–3)
The first crawl (2026-11-04) was ruined by DNS and network failures and discarded whole, before any results were looked at. The census re-ran on **2026-11-09** (2,636 sites crawled normally); the machine then slept and woke offline, so the remaining 4,272 sites were crawled again on **2026-11-13/14 UTC** with no connectivity failures. Each record carries its crawl time. Two validity-rule implementation fixes (XML prolog handling; `llms.txt` over 256 KB) were made before any results analysis (Deviation 2).

## 3. Results

### 3.1 Per file, all reachable sites (n = 5,257)

| File | Valid | Invalid | Soft-404 | Absent | Soft-404 share of 200s |
|---|---|---|---|---|---|
| `sitemap.xml` | 2,803 (53.3% [52.0–54.7]) | 12 | 415 | 1,988 | 12.8% |
| `llms.txt` | 1,832 (34.9% [33.6–36.2]) | 83 | 489 | 2,806 | 20.3% |
| `/.well-known/api-catalog` | 394 (7.5% [6.8–8.2]) | 3 | 582 | 4,214 | 59.5% |
| `/.well-known/ai-catalog.json` | 197 (3.7% [3.3–4.3]) | 15 | 540 | 4,424 | 71.8% |
| `/.well-known/agent-card.json` | 177 (3.4% [2.9–3.9]) | 14 | 540 | 4,449 | 73.9% |
| `/.well-known/ard.json` | 78 (1.5% [1.2–1.9]) | 1 | 542 | 4,558 | 87.3% |
| `/.well-known/http-message-signatures-directory` | 42 (0.8% [0.6–1.1]) | 6 | 587 | 4,559 | 92.4% |
| `/.well-known/poppy.json` | 28 (0.5% [0.4–0.8]) | 1 | 546 | 4,604 | 95.0% |

Errors and `self_excluded` (each ≤ 1.3%) are in `summary.json`.

### 3.2 Valid rate by source

| Source | n | `sitemap` | `llms.txt` | API catalog | AI Catalog | Agent card | ARD | Key directory | `poppy` |
|---|---|---|---|---|---|---|---|---|---|
| Tranco top 1,000 | 639 | 34.7% | 16.3% | 1.9% | 0.9% | 0.3% | 0.3% | 0.9% | 0.2% |
| Tranco 1,001–5,000 | 2,797 | 41.6% | 12.4% | 1.3% | 0.8% | 0.1% | 0.4% | 0.1% | 0.2% |
| Leaderboard | 102 | 74.5% | 51.0% | 12.7% | 6.9% | 2.9% | 2.9% | 2.9% | 0.0% |
| MCP Registry publishers | 1,764 | 77.6% | 76.6% | 19.5% | 9.6% | 9.6% | 3.7% | 1.8% | 1.2% |
| MCP Registry publishers, **operator counted once** (§5, exploratory) | 1,689 | 81.0% | 75.6% | 15.9% | 10.1% | 10.0% | 3.8% | 1.8% | 1.3% |

Intervals are in `summary.json` (`by_source`, `exploratory_operator_counted_once`). Leaderboard intervals are wide (n = 102).

### 3.3 Co-occurrence and cross-links
- 4,695 sites have no valid agent-discovery file; 355 have one; 207 have two or more.
- Agent files mostly come with `llms.txt`: 377 of 394 valid API catalogs and 184 of 197 valid AI Catalogs sit on sites that also have a valid `llms.txt`.
- AI Catalog entry types seen: `application/mcp-server-card+json` 169, `application/json` 54, `text/markdown` 45, OpenAPI 45/20, `application/a2a-agent-card+json` 27, and others.
- Root `Link` headers: `rel="describedby"` 238 sites (4.5%), Markdown alternate 105 (2.0%), `rel="ard"` 34 (0.6%).

## 4. What this can't claim

- **Whether any agent reads these files.** Studies E4 (logs) and E10 (lab site) address that.
- **Full schema validity.** The rules are minimum structure checks; a "valid" file may still be wrong in detail.
- **Files at other paths, or served only to some clients or regions.** One vantage point (Nigeria), two crawl dates.
- **"Soft-404" isn't always a mistake by the site.** A catch-all page is a design choice; the point is that a 200 alone doesn't show a file exists.
- **The MCP-publisher group isn't a sample of companies.** It's the domains behind one registry's endpoints, and one operator's cluster shows how lumpy it is (§5).

## 5. Exploratory, not pre-registered: one operator's template cluster

While checking validation, we noticed many MCP-publisher API catalogs were identical. Grouping identical API-catalog documents found **76 sites** (UK lead-generation "cost/quotes" sites and similar) that share one template: all 76 are reachable, serve a valid API catalog, and send a `Link: rel="describedby"` header. That's 76 of the 344 valid MCP-publisher API catalogs and 76 of the 238 `describedby` headers. The list is in [`../../web-census-crawler/data/e3_template_cluster_api_catalog.json`](../../web-census-crawler/data/e3_template_cluster_api_catalog.json).

Counting the operator as one site (n = 5,182 sites overall):

| Measure | Pre-registered | Operator counted once |
|---|---|---|
| API catalog valid, all sites | 7.5% [6.8–8.2] | 6.2% [5.5–6.8] |
| Any agent-discovery file valid, all sites | 10.7% [9.9–11.6] | 9.4% [8.6–10.2] |
| `Link: rel="describedby"`, all sites | 4.5% [4.0–5.1] | 3.1% [2.7–3.7] |
| API catalog valid, MCP publishers | 19.5% [17.7–21.4] | 15.9% [14.3–17.8] |

The cluster was found after the data was seen, so this is a sensitivity check, not a correction. Other clusters may exist; we only grouped API catalogs.

## 6. Validation

30 site × file results (seed `20261104`, stratified by outcome, with up to 10 valid agent files included first) were re-fetched one by one by an independent Node checker and judged by hand. **Agreement: 27/30 (90%)**, exactly the pre-registered bar. All three disagreements are sites that changed or failed between fetches (a sitemap valid at crawl time and absent at check time; two agent-card fetches that errored at crawl time and returned 404 at check time). Each has a reviewer note in [`data/validation.csv`](../data/validation.csv). **Founder sign-off pending** (spot-check of 5; see [`../REVIEW_QUEUE.md`](../REVIEW_QUEUE.md)).

## 7. Before publication

- Founder validation sign-off.
- Open and cite the current ARD draft (V4) before saying anything about its media type beyond what was observed.
- No site is named critically; the cluster's operator isn't named.

*Glintbase sells Agent Readiness Score audits. The scanner's discovery checks are worth 0–1 points each; this census is the evidence behind that weighting.*
