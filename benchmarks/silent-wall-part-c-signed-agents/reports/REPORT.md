# The Silent Wall, Part C: does a Web Bot Auth signature open the wall? (E6)

**Glintbase Research · November 2026 · DRAFT, not for publication** (needs: founder validation sign-off, review)
Pre-registration: [`PREREGISTRATION.md`](../PREREGISTRATION.md) (frozen in commit `3ddbc9e` before any request; Deviations 1–5) · Data: [`data/`](../data) · Harness: [`harness/`](../harness) · Parent study: [The Silent Wall](../../the-silent-wall/)

Every number below comes from [`data/summary.json`](../data/summary.json), produced by `harness/compute_stats.py --rounds S1,S2,S1R`. Percentages carry Wilson 95% intervals. Section 3.5 (S1R) is **exploratory**.

---

## Summary

We fetched The Silent Wall's 150 popular sites three ways, minutes apart and from the same IP: as our honest research agent **unsigned**, as the same agent **signed** with Web Bot Auth (HTTP Message Signatures, Ed25519, `Signature-Agent` pointing at our published key directory), and as a **headless browser**. We did this in two pre-registered rounds on different days: **S1** on 2026-11-14 and **S2** on 2026-11-15/16.

- **The signature changed nothing.**
  - **S1:** signed and unsigned got the same homepage outcome on all 140 domains where both got an HTTP response (0 discordant pairs; McNemar p = 1.0), each challenged or blocked on 20.7% [14.8–28.2].
  - **S2:** 2 of 138 pairs differed, one in each direction (p = 1.0), and both arms were challenged or blocked on 17.4% [12.0–24.6].
  - The null holds behind every CDN we could identify (Cloudflare, Akamai, CloudFront, Fastly, Vercel, DataDome and the rest).
- **The honest agent was treated about like a browser.** Homepage challenged or blocked, of 150:

  | Round | Unsigned | Signed | Browser |
  |---|---|---|---|
  | S1 | 19.3% [13.8–26.4] | 19.3% [13.8–26.4] | 20.7% [15.0–27.8] |
  | S2 | 16.0% [11.0–22.7] | 16.7% [11.6–23.4] | 20.0% [14.4–27.1] |

  Paired, the agent and the browser differed on 10 of 140 domains in S1 (p = 0.75) and 8 of 137 in S2 (p = 0.29). In both rounds the browser was the one blocked more often.
- **Stable across days.** Between S1 and S2, 96.7% of domains kept the same homepage outcome for the unsigned agent (κ = 0.934), 96.0% for the signed agent (κ = 0.921) and 95.3% for the browser (κ = 0.904).
- **Similar to October.** The Silent Wall measured 16.0% [11.0–22.7] for the agent and 18.7% [13.2–25.7] for the browser in October 2026, from a different network (§4).

**What it means.** A valid signature from an agent that no edge has registered or otherwise trusts is, in practice, ignored: it doesn't help and it doesn't hurt. For agent builders, signing is cheap and harmless, but on its own it doesn't open the wall. Any benefit would have to come from registration with an edge's verified-bot programme, which this study didn't test.

## 1. Why this study

Arkose reports that only 2.3% of agent sessions are signed (vendor report). The Silent Wall found that declaring an honest identity didn't cost access compared with a browser. The natural next question: does proving that identity cryptographically, with the IETF Web Bot Auth drafts, change how edges treat an agent?

## 2. Method (summary of the pre-registration)

- **Sample:** The Silent Wall's 150 domains (5 sectors × 30), with its frozen page lists (homepage plus up to 3 sitemap pages) and `robots.txt` decisions.
- **Arms**, in random order per domain and round, ≥ 30 s apart, with fresh cookies each:
  - `unsigned`: httpx, `User-Agent: GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot; research@glintbase.dev)`; obeys `robots.txt` for its token;
  - `signed`: identical, plus `Signature-Agent: sig1="https://glintbase.dev"`, `Signature-Input` (`"@authority"` and `"signature-agent";key="sig1"`, `created`, `expires` +300 s, `keyid` = JWK thumbprint, `alg="ed25519"`, 64-byte `nonce`, `tag="web-bot-auth"`) and `Signature` on every request, including each redirect hop;
  - `browser`: headless Chromium (Playwright), default user agent.
- **Key directory:** `https://glintbase.dev/.well-known/http-message-signatures-directory`, live since 2026-11-09 07:02:54Z, served as `application/http-message-signatures-directory+json`. The directory response itself isn't signed yet.
- **Signatures verified independently** before the first signed round: Cloudflare's reference implementation (`web-bot-auth` 0.2.0) verified our request signature against the key fetched live from the directory. Before every round, a transport-layer check confirmed that the signed arm sends the three headers and the unsigned arm sends none.
- **Classification:** The Silent Wall's classifier, unchanged (`ok`, `thin`, `challenge`, `block`, `rate_limited`, `error`, `other`, `self_excluded`). Primary outcome: homepage challenged or blocked.
- **No registered arm:** registration with Cloudflare's signed-agents programme can't clear within a week.

### Run history (Deviations 1–5)
- **S1:** 2026-11-14, 12:13–13:23Z, all 150 domains, no connectivity failures.
- **S1R (exploratory):** on 2026-11-14 a second round started 17 minutes after S1, at the founder's request. It was then relabelled S1R, a same-day re-test, when the decision came to run the pre-registered replication on a later day. A 3-minute outage set aside 37 of its domains, which weren't re-run.
- **S2:** started 2026-11-15. A 4-minute outage and an early stop left 87 clean domains. The 63 others (24 in the outage window, 39 never reached) were run on 2026-11-16 with no connectivity failures. Each record keeps its own timestamp.
- **Vantage points:** S1, S1R and the 2026-11-15 part of S2 ran from one AfriNIC allocation (102.88.0.0–102.95.255.255, Nigeria). The 2026-11-16 part ran from another (197.211.52.0/24, Nigeria). The Silent Wall used AS36873. Within a domain and round, all three arms always share one IP.

## 3. Results

### 3.1 Homepage outcome per arm, S1 (2026-11-14) and S2 (2026-11-15/16), n = 150 each

| Outcome | S1 unsigned | S1 signed | S1 browser | S2 unsigned | S2 signed | S2 browser |
|---|---|---|---|---|---|---|
| `ok` | 102 | 102 | 106 | 104 | 104 | 104 |
| `challenge` | 15 | 15 | 12 | 10 | 12 | 11 |
| `block` | 14 | 14 | 19 | 14 | 13 | 19 |
| `error` | 8 | 8 | 6 | 11 | 9 | 8 |
| `thin` | 7 | 7 | 2 | 7 | 7 | 4 |
| `other` | 2 | 2 | 3 | 2 | 2 | 2 |
| `rate_limited` | 1 | 1 | 2 | 1 | 2 | 2 |
| `self_excluded` | 1 | 1 | — | 1 | 1 | — |
| **Challenged or blocked** | **19.3%** | **19.3%** | **20.7%** | **16.0%** | **16.7%** | **20.0%** |
| Worst page challenged or blocked | 22.0% | 22.0% | 24.0% | 18.7% | 19.3% | 23.3% |

### 3.2 Paired comparisons (domains where both arms got an HTTP response)

| Comparison | Round | Pairs | Bad for first only | Bad for second only | McNemar exact p |
|---|---|---|---|---|---|
| Unsigned vs signed | S1 | 140 | 0 | 0 | 1.0 |
| Unsigned vs signed | S2 | 138 | 1 | 1 | 1.0 |
| Unsigned vs browser | S1 | 140 | 4 | 6 | 0.75 |
| Unsigned vs browser | S2 | 137 | 2 | 6 | 0.29 |
| Signed vs browser | S1 | 140 | 4 | 6 | 0.75 |
| Signed vs browser | S2 | 139 | 3 | 7 | 0.34 |

**The two S2 discordant pairs (descriptive).** Both are DataDome-protected sites, and they point in opposite directions:
- **A news site:** only the signed arm got a DataDome challenge (403). The same site blocked all three arms in S1, so this looks like a site whose treatment varies from one visit to the next.
- **A payments site:** only the signed arm got through (200); the unsigned agent and the browser were blocked. The same pattern appears in S1R, but in both rounds the signed arm ran directly after the unsigned one (S1R reused S2's arm order, see §3.5). In S1, where the signed arm ran last, all three arms were blocked. We can't tell a signature effect from an ordering or timing effect with two observations. It's a lead for a targeted follow-up, not a finding.

### 3.3 Stability, S1 → S2 (different days)

| Arm | Same homepage outcome | Cohen's κ |
|---|---|---|
| Unsigned | 145/150 (96.7% [92.4–98.6]) | 0.934 |
| Signed | 144/150 (96.0% [91.5–98.2]) | 0.921 |
| Browser | 143/150 (95.3% [90.7–97.7]) | 0.904 |

63 of the 150 S2 domains ran from a different IP allocation than S1 (§2), so this agreement includes any network effect.

### 3.4 Against The Silent Wall (descriptive; different dates and network)

| Homepage challenged or blocked | October 2026 (The Silent Wall, AS36873) | S1, 2026-11-14 | S2, 2026-11-15/16 |
|---|---|---|---|
| Honest agent (unsigned) | 16.0% [11.0–22.7] | 19.3% [13.8–26.4] | 16.0% [11.0–22.7] |
| Headless browser | 18.7% [13.2–25.7] | 20.7% [15.0–27.8] | 20.0% [14.4–27.1] |

### 3.5 Exploratory: same-day re-test (S1R, 113 domains)
- **Signed vs unsigned:** 1 discordant pair of 105 (the payments site above; p = 1.0).
- **Agreement with S1, the same afternoon:** unsigned 99.1% (κ = 0.983), signed 96.5% (κ = 0.930), browser 97.3% (κ = 0.946).
- **Caveat:** S1R ran under the round name S2, so its arm order per domain is the same as S2's, and it isn't independent of S2 on ordering.

## 4. What this can't claim

- **How edges treat registered signed agents** (e.g. Cloudflare's signed-agents programme), or vendors' verified crawlers. Our key isn't registered anywhere.
- **Whether any edge verified our signature.** We see outcomes only. An edge may have verified it and given it no weight, or not checked it at all.
- **The directory response isn't signed yet.** The draft recommends signing it, and a strict verifier could ignore keys from an unsigned directory.
- **Generality.** 150 popular domains, two Nigerian IP allocations, three days. The comparison with October differs by network and date, so it is descriptive only.
- **Single-site patterns.** The two S2 discordant pairs are too few to support any vendor-level claim.

## 5. Validation

30 domain × arm results from S1 (seed `20261104`, stratified by outcome and arm) were judged by hand from the stored status, headers, challenge markers, visible-text length and title. **Agreement: 28/30 (93.3%)**:
- a browser fetch of one news site was a 301 followed by an HTTP/2 protocol error (classifier `other`, by hand `error`);
- a browser fetch of one retailer's homepage returned 142 visible characters, consistent with a bot interstitial (classifier `thin`, by hand `challenge`). This is in the browser arm, not the signed-vs-unsigned comparison.

The two S2 discordant pairs were also checked by hand against their stored evidence; their classifications follow the rules (§3.2). Details are in [`data/validation.csv`](../data/validation.csv) and [`data/run_notes.md`](../data/run_notes.md). **Founder sign-off pending** (see [`../REVIEW_QUEUE.md`](../REVIEW_QUEUE.md)).

## 6. Before publication

- Founder validation sign-off.
- Optional: set `WEB_BOT_AUTH_DIRECTORY_KEY` on the host so the directory response is signed (the founder's decision).
- If the payments-site pattern is followed up or a vendor is named, a 7-day right of reply. The draft names no site or vendor critically.

*Glintbase sells Agent Readiness Score audits. Our scanner doesn't sign its requests yet; this result suggests signing would be neutral, which is the research programme's condition for signing scanner requests ("if it helps or is neutral").*
