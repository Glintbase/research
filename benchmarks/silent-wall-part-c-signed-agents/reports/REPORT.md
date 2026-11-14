# The Silent Wall, Part C: does a Web Bot Auth signature open the wall? (E6)

**Glintbase Research · November 2026 · DRAFT, not for publication** (needs: replication round S2, founder validation sign-off, review)
Pre-registration: [`PREREGISTRATION.md`](../PREREGISTRATION.md) (frozen in commit `3ddbc9e` before any request; Deviations 1–2) · Data: [`data/`](../data) · Harness: [`harness/`](../harness) · Parent study: [The Silent Wall](../../the-silent-wall/)

Every number below comes from [`data/summary.json`](../data/summary.json), produced by `harness/compute_stats.py --rounds S1`. Percentages carry Wilson 95% intervals.

---

## Summary (round S1, 2026-11-14)

We fetched The Silent Wall's 150 popular sites three ways, minutes apart, from the same IP: as our honest research agent **unsigned**, as the same agent **signed** with Web Bot Auth (HTTP Message Signatures, Ed25519, `Signature-Agent` pointing at our published key directory), and as a **headless browser**.

- **The signature changed nothing.** On all 140 domains where both agent arms got an HTTP response, the signed and unsigned agent had the same homepage outcome, without exception (0 discordant pairs; McNemar p = 1.0). Each was challenged or blocked on 20.7% [14.8–28.2] of them. That holds behind every CDN we could identify: Cloudflare (37 pairs), Akamai (26), CloudFront (23), Fastly (11), Vercel (7), DataDome (3) and the rest (33).
- **The honest agent was treated about like a browser.** Homepage challenged or blocked: unsigned 19.3% [13.8–26.4], signed 19.3% [13.8–26.4], headless browser 20.7% [15.0–27.8] of 150. Paired, the agent and the browser differed on 10 of 140 domains (agent-only 4, browser-only 6; p = 0.75).
- **Similar to October.** The Silent Wall measured 16.0% [11.0–22.7] for the agent and 18.7% [13.2–25.7] for the browser in October 2026, from a different network (§4).

**What it means.** A valid signature from an agent no edge has registered or otherwise trusts is simply ignored: it doesn't help and it doesn't hurt. For agent builders, signing is cheap and harmless, but on its own it doesn't open the wall. Any benefit would have to come from registration with an edge's verified-bot programme, which this study didn't test.

## 1. Why this study

Arkose reports that only 2.3% of agent sessions are signed (vendor report). The Silent Wall found that declaring an honest identity didn't cost access compared with a browser. The natural next question: does proving that identity cryptographically, with the IETF Web Bot Auth drafts, change how edges treat an agent?

## 2. Method (summary of the pre-registration)

- **Sample:** The Silent Wall's 150 domains (5 sectors × 30) and its frozen page lists (homepage plus up to 3 sitemap pages) and `robots.txt` decisions.
- **Arms**, order randomised per domain, ≥ 30 s apart, fresh cookies each:
  - `unsigned`: httpx, `User-Agent: GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot; research@glintbase.dev)`, obeys `robots.txt` for its token;
  - `signed`: identical, plus `Signature-Agent: sig1="https://glintbase.dev"`, `Signature-Input` (`"@authority"` and `"signature-agent";key="sig1"`, `created`, `expires` +300 s, `keyid` = JWK thumbprint, `alg="ed25519"`, 64-byte `nonce`, `tag="web-bot-auth"`) and `Signature` on every request, including each redirect hop;
  - `browser`: headless Chromium (Playwright), default UA.
- **Key directory:** `https://glintbase.dev/.well-known/http-message-signatures-directory`, live since 2026-11-09 07:02:54Z, served as `application/http-message-signatures-directory+json`. The directory response itself is not yet signed.
- **Signature verified independently** before the signed round: Cloudflare's reference implementation (`web-bot-auth` 0.2.0) verified our request signature against the key fetched live from the directory. After S1 we re-confirmed, at the transport layer, that the signed arm sends the three headers and the unsigned arm doesn't.
- **Classification:** The Silent Wall's classifier, unchanged (`ok`, `thin`, `challenge`, `block`, `rate_limited`, `error`, `other`, `self_excluded`). Primary outcome: homepage challenged or blocked.
- **No registered arm:** registering with Cloudflare's signed-agents programme can't clear within a week.

## 3. Results

### 3.1 Homepage outcome per arm (n = 150 each)

| Outcome | Unsigned | Signed | Browser |
|---|---|---|---|
| `ok` | 102 (68.0%) | 102 (68.0%) | 106 (70.7%) |
| `challenge` | 15 (10.0%) | 15 (10.0%) | 12 (8.0%) |
| `block` | 14 (9.3%) | 14 (9.3%) | 19 (12.7%) |
| `error` | 8 (5.3%) | 8 (5.3%) | 6 (4.0%) |
| `thin` | 7 (4.7%) | 7 (4.7%) | 2 (1.3%) |
| `other` | 2 | 2 | 3 |
| `rate_limited` | 1 | 1 | 2 |
| `self_excluded` | 1 | 1 | — |
| **Challenged or blocked** | **19.3% [13.8–26.4]** | **19.3% [13.8–26.4]** | **20.7% [15.0–27.8]** |
| Worst page challenged or blocked | 22.0% [16.1–29.3] | 22.0% [16.1–29.3] | 24.0% [17.9–31.4] |

### 3.2 Paired comparisons (domains where both arms got an HTTP response; 10 excluded for errors or self-exclusion)

| Comparison | Pairs | Bad for first only | Bad for second only | McNemar exact p |
|---|---|---|---|---|
| Unsigned vs signed | 140 | 0 | 0 | 1.0 |
| Unsigned vs browser | 140 | 4 | 6 | 0.75 |
| Signed vs browser | 140 | 4 | 6 | 0.75 |

By CDN (unsigned vs signed): 0 discordant pairs behind every vendor identified.

### 3.3 Against The Silent Wall (descriptive; different date and network)

| Homepage challenged or blocked | October 2026 (The Silent Wall, AS36873) | November 2026 (S1, this study) |
|---|---|---|
| Honest agent (unsigned) | 16.0% [11.0–22.7] | 19.3% [13.8–26.4] |
| Headless browser | 18.7% [13.2–25.7] | 20.7% [15.0–27.8] |

## 4. What this can't claim

- **How edges treat registered signed agents** (e.g. Cloudflare's signed-agents programme), or vendors' verified crawlers. Our key isn't registered anywhere.
- **Whether any edge verified our signature.** We see outcomes only. An edge may have verified it and given it no weight, or not checked it at all.
- **The directory response isn't signed yet.** The draft recommends signing it; a strict verifier could ignore keys from an unsigned directory. This can't change the null result unless some edge verifies and then rewards signatures, which none appeared to.
- **One round so far.** S2, the pre-registered replication on a different day, hasn't run.
- **Generality.** 150 popular domains, one vantage point (Nigeria; IP 102.90.126.151, an AfriNIC allocation registered to `ORG-MN1-AFRINIC`, not The Silent Wall's AS36873), one day. The comparison with October differs by network and date, so it's descriptive only.

## 5. Validation

30 domain × arm results from S1 (seed `20261104`, stratified by outcome and arm) were judged by hand from the stored status, headers, challenge markers, visible-text length and title. **Agreement: 28/30 (93.3%)**:
- a browser fetch of one news site was a 301 followed by an HTTP/2 protocol error (classifier `other`, by hand `error`);
- a browser fetch of one retailer's homepage returned 142 visible characters, consistent with a bot interstitial (classifier `thin`, by hand `challenge`). That's the one disagreement that changes the primary outcome, and it's in the browser arm, not the signed-vs-unsigned comparison.

Details in [`data/validation.csv`](../data/validation.csv). **Founder sign-off pending** (see [`../REVIEW_QUEUE.md`](../REVIEW_QUEUE.md)).

## 6. Before publication

- Round S2 on a later day (replication), then re-run `compute_stats.py --rounds S1,S2` for stability.
- Founder validation sign-off.
- Optional: set `WEB_BOT_AUTH_DIRECTORY_KEY` so the directory response is signed (the founder's decision).
- If a CDN vendor is named in a finding, a 7-day right of reply. Here every vendor shows the same null, so no vendor is singled out.

*Glintbase sells Agent Readiness Score audits. Our scanner doesn't sign its requests yet; this result suggests signing would be neutral, which is the research programme's condition for signing scanner requests ("if it helps or is neutral").*
