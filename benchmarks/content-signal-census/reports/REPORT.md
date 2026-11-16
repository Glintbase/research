# Content Signals in the wild: what 754 websites tell AI systems about using their content

**Glintbase Research · November 2026 · Final report**
Pre-registration: [`PREREGISTRATION.md`](../PREREGISTRATION.md) (frozen in commit `3ddbc9e` before the crawl) · Data: [`data/`](../data) · Analysis: [`harness/`](../harness) · Crawler: [`../web-census-crawler/`](../../web-census-crawler/)

Every number in sections 3.1–3.4 comes from [`data/summary.json`](../data/summary.json), the pre-registered analysis (`harness/analyze.py`, `harness/compute_stats.py`). Sections 3.5–3.9 are **descriptive breakdowns added after the pre-registered analysis**, from [`data/descriptives.json`](../data/descriptives.json) (`harness/descriptives.py`); they count the same per-site fields and re-classify nothing. Percentages carry Wilson 95% intervals in brackets.

---

## Summary

**Content Signals** let a website say, separately, whether its content may be used to build a **search** index, as live **AI input** (for example retrieval for a chatbot answer), or for **AI training**. A site can state them in `robots.txt` or send them in a `Content-Signal` HTTP response header.

We checked **1,121 sites**: the Glintbase agent-readiness leaderboard (103 companies building for AI agents), The Silent Wall's 150 popular domains, and the Tranco top 1,000. For each we compared what `robots.txt` says with what the homepage's response headers say, both as normal HTML and when an AI agent asks for Markdown. **754 sites were reachable** and form every denominator.

1. **Almost nobody states Content Signals.** 93.5% [91.5–95.0] of sites state none, anywhere. 6.5% [5.0–8.5] state some: 4.2% in `robots.txt`, 2.9% in a response header.
2. **Companies building for AI agents use them almost six times as often.** 22.5% [15.5–31.6] of leaderboard sites state a signal, against 3.9% [2.7–5.7] of the Tranco top 1,000. Popularity makes no difference within the Tranco list.
3. **Every header signal we saw is the same value, and almost all come from one CDN.** All 22 sites that send a `Content-Signal` header send exactly `ai-input=yes, ai-train=yes, search=yes`. 21 of them are on Cloudflare, and 21 send it only on Markdown responses. That matches the default Cloudflare documents for its Markdown for Agents feature.
4. **The header often says something the site never said.** Of the 55 sites that serve Markdown to agents, 40.0% [28.1–53.2] send a different signal on the Markdown response than on the HTML page, almost always because only the Markdown response has one. A human visitor and an AI agent can get two different statements about the same page.
5. **Direct contradictions exist but are rare, because few sites state signals in both places.** 5 sites do. 4 agree; 1 says `ai-train=no` in `robots.txt` while its Markdown response says `ai-train=yes`.
6. **Where sites write their own policy, they split on training.** Of the 29 sites whose general `robots.txt` policy mentions training, 16 allow it and 13 refuse it, yet all 30 that mention `search` allow it. Search and AI input are broadly welcome; training is where sites diverge.

---

## 1. Background

### 1.1 What Content Signals are

Content Signals were introduced by Cloudflare in 2025 and are documented at [contentsignals.org](https://contentsignals.org/). They extend `robots.txt` with a `Content-Signal` line that grants (`yes`) or withholds (`no`) three uses:

| Signal | Meaning (contentsignals.org) |
|---|---|
| `search` | Building a search index and providing search results (links and short excerpts). Does not include AI-generated search summaries. |
| `ai-input` | Inputting content into AI models, e.g. retrieval augmented generation, grounding, or real-time use for generative AI search answers. |
| `ai-train` | Training or fine-tuning AI models. |

A missing signal neither grants nor restricts. The directive can apply to all crawlers (`User-Agent: *`), to named crawlers, or to specific paths, for example `Content-Signal: /blog/ ai-train=no, search=yes, ai-input=no`. Content Signals express preferences; contentsignals.org itself notes that not every automated system honours `robots.txt`.

### 1.2 The response header

Cloudflare also sends signals as an HTTP response header. Its [Markdown for Agents documentation](https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/) (last updated 2026-11-09) says that when a client asks for `Accept: text/markdown`, Cloudflare can convert the page to Markdown, and:

> "When the origin response does not include a `content-signal` header, Markdown for Agents adds a default `Content-Signal: ai-train=yes, search=yes, ai-input=yes`."

If the origin already sets a `content-signal` header, Cloudflare keeps the origin's value. The documentation describes no other way to change or remove the default.

### 1.3 Why we measured it

A vendor study by AI Ranked ([2026-10-28](https://airanked.ai/research/markdown-for-agents-study), 285 high-traffic sites, labelled here as vendor research) found 28 homepages serving Markdown, 15 of them with the default `ai-train=yes` header, including one site whose `robots.txt` says `ai-train=no`. We wanted the same question answered on a defined, larger population with a pre-registered, open method: **how often do sites state Content Signals at all, and how often do the two places disagree?**

---

## 2. Method

- **Sample (1,121 sites):** the Glintbase leaderboard (103 hosts, read 2026-11-04), The Silent Wall's 150 domains, and the Tranco top 1,000 (list `4672X`), de-duplicated. 754 were reachable. The other 367 are mostly Tranco infrastructure hosts (CDN, DNS and API domains) that serve no website, plus 37 sites whose `robots.txt` disallows our crawler from the homepage, which we respected and excluded.
- **Requests (at most 8 per site):** `robots.txt`; the homepage as HTML; the homepage with `Accept: text/markdown`; a Markdown twin if the page advertises one; and up to 2 linked docs pages, each as HTML and as Markdown.
- **Identity and conduct:** every request identified itself as `GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot)`, obeyed `robots.txt` for that name, and sent at most one request per second to a site. Only public pages were requested.
- **What counts as a signal:** the `robots.txt` policy is the `User-Agent: *` group's `Content-Signal` values; signals for named crawlers are reported separately (§3.6). A header signal is any `Content-Signal` header on the homepage HTML, its Markdown response, or a docs response.
- **Classes:** `none`, `robots_only`, `header_only`, `agree`, `conflict` (a key with different values in `robots.txt` and a header, or between two headers).
- **When:** the census ran from one residential connection in Nigeria. Network interruptions during the planned crawl meant affected sites were re-crawled under a rule fixed in advance, so each site's data comes from either 2026-11-09 or 2026-11-13/14 (UTC). The pre-registration's Deviations section records exactly what happened and which sites were re-crawled.

---

## 3. Results

### 3.1 Where sites state Content Signals (n = 754)

| Class | Sites | Share |
|---|---|---|
| No signal anywhere | 705 | 93.5% [91.5–95.0] |
| `robots.txt` only | 27 | 3.6% [2.5–5.2] |
| Response header only | 17 | 2.3% [1.4–3.6] |
| Both, agreeing | 4 | 0.5% [0.2–1.4] |
| Both, conflicting | 1 | 0.1% [0.0–0.7] |

Overall, **6.5% [5.0–8.5]** of sites state any Content Signal: **4.2% [3.0–5.9]** in `robots.txt` and **2.9% [1.9–4.4]** in a header.

### 3.2 By sample

| Sample | Reachable | Any signal | `robots.txt` | Header | Serves Markdown |
|---|---|---|---|---|---|
| Glintbase leaderboard | 102 | 23 · **22.5%** [15.5–31.6] | 18 · 17.6% | 9 · 8.8% | 32 · 31.4% |
| The Silent Wall's 150 | 137 | 11 · 8.0% [4.5–13.8] | 7 · 5.1% | 5 · 3.6% | 9 · 6.6% |
| Tranco top 1,000 | 639 | 25 · 3.9% [2.7–5.7] | 14 · 2.2% | 13 · 2.0% | 22 · 3.4% |

The samples overlap (some Silent Wall domains are in the Tranco top 1,000), so rows don't add up to the total. Companies on the leaderboard are much more likely to state signals and to serve Markdown, which fits a population that builds for AI agents.

### 3.3 By CDN

| CDN | Sites | Header signal | Serves Markdown | Markdown responses with a header |
|---|---|---|---|---|
| Cloudflare | 220 | 21 · **9.5%** [6.3–14.2] | 30 · 13.6% | 20 of 30 |
| Other / unidentified | 259 | 1 · 0.4% [0.1–2.2] | 6 · 2.3% | 1 of 6 |
| CloudFront | 100 | 0 | 4 · 4.0% | 0 of 4 |
| Akamai | 66 | 0 | 0 | — |
| Fastly | 60 | 0 | 0 | — |
| Vercel | 43 | 0 | 15 · **34.9%** | 0 of 15 |

The CDN is identified from response headers; cells under 30 sites are small. Vercel-hosted sites serve Markdown most often, but none of them send a signal with it.

### 3.4 Markdown responses: a second, different statement

55 sites (**7.3%** [5.6–9.4]) return Markdown when an agent asks for it. Among them:

| | Sites | Share of the 55 |
|---|---|---|
| Send a `Content-Signal` header on the Markdown response | 21 | 38.2% |
| Send one on the HTML response | 1 | 1.8% |
| Markdown signal differs from the HTML page's signal | 22 | **40.0%** [28.1–53.2] |

In almost every case the difference is that the Markdown response carries a signal and the HTML page carries none. So an AI agent asking for Markdown is told "training allowed", while a person, a search crawler, or an agent fetching HTML is told nothing.

### 3.5 The header is one value, mostly from one place *(descriptive)*

| | Count |
|---|---|
| Sites sending any `Content-Signal` header | 22 |
| …with the value `ai-input=yes, ai-train=yes, search=yes` | **22 of 22** |
| …on Cloudflare | 21 of 22 |
| …only on Markdown responses | 21 of 22 · 95.5% [78.2–99.2] |
| …that also state a policy in their own `robots.txt` | 5 of 22 |

Every header signal we saw is identical to the default Cloudflare documents (§1.2), and it appears only where that feature applies. We can't see from outside whether a site chose this value, but for **17 of the 22** sites the header is the *only* place any signal appears.

### 3.6 What sites write in their own `robots.txt` *(descriptive)*

81.3% [78.4–83.9] of reachable sites serve a `robots.txt` file (6.9% return 404). Among the 32 sites with `Content-Signal` lines:

| General policy (`User-Agent: *`) | Sites |
|---|---|
| `ai-input=yes, ai-train=yes, search=yes` (allow everything) | 15 |
| `ai-input=yes, ai-train=no, search=yes` (allow search and AI input, refuse training) | 6 |
| `ai-train=no, search=yes, use=reference` | 4 |
| `ai-input=no, ai-train=no, search=yes` (search only) | 2 |
| `ai-input=yes, search=yes` (training left unstated) | 1 |
| `ai-input=yes, ai-train=no, search=yes, use=reference` | 1 |
| Path-by-path signals, plus allow-everything | 1 |
| Signals for named crawlers only, no general policy | 2 |

- **Training is the dividing line.** 13 sites (1.7% [1.0–2.9] of all reachable sites) refuse AI training in `robots.txt`; every one of them still allows search, and 7 of them also allow AI input.
- **`use=reference` is not a defined signal.** 5 sites add a `use` key that contentsignals.org doesn't define; systems that follow the spec will ignore it.
- **One site sets signals path by path**, as the spec allows, alongside a general allow-everything policy.

### 3.7 Different rules for different crawlers *(descriptive)*

8 sites put `Content-Signal` lines inside groups for named crawlers. 5 of them refuse at least one crawler something, and 3 set different policies for different crawlers. The pattern is consistent: assistant and search crawlers (for example `ChatGPT-User`, `OAI-SearchBot`, `Claude-User`, `PerplexityBot`) get `search` and `ai-input`, while `Bytespider` is refused all three uses on 3 of the 4 sites that name it.

### 3.8 Popularity doesn't predict adoption *(descriptive)*

| Tranco rank | Reachable | Any signal |
|---|---|---|
| 1–100 | 62 | 3 · 4.8% [1.7–13.3] |
| 101–500 | 244 | 10 · 4.1% [2.2–7.4] |
| 501–1,000 | 333 | 12 · 3.6% [2.1–6.2] |

The largest websites are no more likely to state Content Signals than the rest of the top 1,000. What predicts adoption is building for AI agents (§3.2), not size.

### 3.9 Markdown for agents, more broadly *(descriptive)*

- **55 sites** serve Markdown from the homepage and **58** serve it on at least one linked docs page. Docs are where Markdown is most often offered.
- 96.4% [87.7–99.0] of sites that serve Markdown send `Vary: Accept`, which tells caches that HTML and Markdown are different responses.
- **30 sites (4.0%)** advertise a Markdown version of the homepage with `<link rel="alternate" type="text/markdown">` or a `Link` header.
- Markdown comes mostly from Cloudflare (30 sites) and Vercel (15 sites). 33 of the 55 serve Markdown with no signal at all.

### 3.10 The leaderboard companies that state signals

These are public facts: what each site's `robots.txt` and response headers said when we fetched them. The one leaderboard site whose signals conflict is not listed (see §4).

| Site | `robots.txt` policy | Header | Serves Markdown | CDN |
|---|---|---|---|---|
| arrivl.ai | named crawler only (CCBot: allow all three) | — | yes | other |
| blackforestlabs.ai | `ai-input=yes, search=yes` | — | no | Vercel |
| cloudflare.com | named crawler only (cohere-ai: allow all three) | `ai-input=yes, ai-train=yes, search=yes` | yes | Cloudflare |
| comfy.org | allow all three | — | no | Cloudflare |
| coreweave.com | — | allow all three | yes | Cloudflare |
| cresta.com | — | allow all three | yes | Cloudflare |
| dodopayments.com | — | allow all three | yes | Cloudflare |
| elevenlabs.io | allow all three | — | yes | Cloudflare |
| exa.ai | allow all three, plus path-by-path `search=yes` | — | yes | Vercel |
| firecrawl.dev | allow all three | — | yes | Vercel |
| glean.com | — | allow all three | yes | Cloudflare |
| llamaindex.ai | allow all three | — | no | Vercel |
| mailtrap.io | allow all three | allow all three | yes | Cloudflare |
| nvidia.com | allow all three | — | no | CloudFront |
| ora.ai | allow all three | — | yes | Vercel |
| pxxl.app | `ai-train=no, search=yes, use=reference` | — | no | Cloudflare |
| tastelabs.com | `ai-train=no, search=yes, use=reference` | — | no | Cloudflare |
| telnyx.com | allow all three | allow all three | yes | Cloudflare |
| together.ai | — | allow all three | yes | Cloudflare |
| wandb.ai | allow all three | — | no | Cloudflare |
| x.ai | allow all three | — | no | Cloudflare |
| zernio.com | `ai-input=yes, ai-train=no, search=yes` | — | yes | Vercel |

"Allow all three" means `ai-input=yes, ai-train=yes, search=yes`.

---

## 4. What this means

**For site owners.** If your site is on Cloudflare and Markdown for Agents is on, your Markdown responses probably tell AI systems that training is allowed, whatever your `robots.txt` says, unless your origin sends its own `Content-Signal` header. Check it in one command each:

```
curl -s https://your-site.com/robots.txt | grep -i content-signal
curl -sI -H "Accept: text/markdown" https://your-site.com/ | grep -i content-signal
```

If the two disagree, set a `Content-Signal` header at your origin; Cloudflare keeps an origin value rather than adding its default. And decide on training explicitly: it's the one use sites disagree about, and leaving it unstated in `robots.txt` while a CDN states it for you is the gap this study found.

**For people building agents and crawlers.** A signal on a Markdown response isn't necessarily the site's own statement. Where both exist, `robots.txt` is the place a site writes its policy deliberately.

**For the conflict we found.** One leaderboard site refuses AI training in `robots.txt` while its Markdown response carries the CDN default allowing it. We don't name it: the evidence points to a default the site likely never chose, not a decision by the site. The per-site data in `data/` lists every site's public signals.

---

## 5. What this can't claim

- **Whether any AI company honours `Content-Signal`**, in either place.
- **Intent.** A header may be a CDN default the site never chose (§3.5).
- **The rest of a site.** Only the homepage and up to 2 docs pages were fetched; a site can set different signals elsewhere, and path-scoped signals were recorded as written.
- **Small numbers.** Conflicts can only occur where signals appear in both places, and only 5 sites do that, so the conflict rate among them can't be estimated usefully.
- **One vantage point.** Responses can vary by location and by how a site treats bots.
- **Sections 3.5–3.9 were not pre-registered.** They are descriptive counts of the same data and test no hypothesis.

## 6. Validation

30 sites (seed `20261104`, stratified by class, with the conflict site included) were re-fetched one at a time by an independent checker written for the purpose and classified by hand from its output. **Agreement: 30 of 30** ([`data/validation.csv`](../data/validation.csv)). Founder spot-check: FOUNDER_SPOTCHECK_PENDING.

## 7. Data and reuse

- [`data/sites.csv`](../data/sites.csv) and `sites.jsonl`: one row per site with derived fields (class, CDN, policies, Markdown flags). Raw responses are not published.
- [`data/summary.json`](../data/summary.json): every pre-registered number. [`data/descriptives.json`](../data/descriptives.json): sections 3.5–3.9.
- Code and data are released for reuse; please cite as below.

**Cite as:** Glintbase Research (2026). *Content Signals in the wild: what 754 websites tell AI systems about using their content.* https://glintbase.dev/research/content-signals

*Glintbase sells Agent Readiness Score (ARS) audits. Content Signals aren't part of the current score; a reported, unscored check based on this study is planned for ARS 3.4.*
