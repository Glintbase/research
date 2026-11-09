# Remote MCP Server Reliability, Edition 1.1: the 3.5-week re-probe

**Glintbase Research · November 2026 · DRAFT, not for publication** (needs: founder validation sign-off, review)
Pre-registration: [`PREREGISTRATION.md`](../PREREGISTRATION.md) (frozen in commit `3ddbc9e` before any request) · Data: [`data/`](../data) · Harness: [`harness/`](../harness) · Edition 1: [`../production-mcp-reliability-crisis/`](../../production-mcp-reliability-crisis/)

Every number below comes from [`data/summary.json`](../data/summary.json), produced by `harness/compute_stats.py --round 1 --retest 2`. Percentages carry Wilson 95% intervals.

---

## Summary (round 1, 2026-11-04)

We re-probed the **same 3,000 endpoints** (2,244 hosts) that Edition 1 sampled from the official MCP Registry on 2026-10-12. The probe was Edition 1's harness, unchanged, plus metadata-only additions. 2,999 endpoints were classified (1 excluded: its host now resolves to a private address).

- **Little moved in 3.5 weeks.** 55.5% [53.7–57.3] of endpoints completed a handshake and listed tools anonymously, against 57.0% [55.2–58.7] for the same endpoints in Edition 1. Pairwise, 78 endpoints lost that status and 35 gained it (McNemar exact p = 0.0001). Most of the losses became unreachable (27) or stopped answering as MCP (23).
- **The `2026-07-28` revision gained a little ground.** Among the 1,648 endpoints that completed a handshake in both editions, 13.7% [12.1–15.5] now speak `2026-07-28`, up from 12.6% [11.1–14.3]. 19 endpoints moved to the new revision and 1 moved back (McNemar p < 0.001). Across all 1,677 handshakes this round, 14.0% [12.4–15.7] were modern, and 26.9% of those also accept older revisions.
- **Auth compliance edged up.** Of the 837 endpoints that required auth in both editions, 84.2% [81.6–86.5] now give a challenge an agent can follow, up from 82.9% [80.2–85.3] (12 gained, 1 lost; p = 0.0034).
- **Error signalling didn't change at all.** Among the 1,698 endpoints that answered the canary call in both editions, 74.4% returned an in-channel error both times, with no endpoint changing either way.
- **Extensions and Skills are rare.** 2.4% [1.8–3.3] of handshaking endpoints declare any MCP extension: `io.modelcontextprotocol/ui` (29), `io.modelcontextprotocol/skills` (9) and `io.modelcontextprotocol/tasks` (3). All 9 Skills declarers answered `skills/list` (0.5% [0.3–1.0] of handshakes, 9 hosts).
- **Server Cards: 8.6% of endpoints, but 60 hosts.** 245 endpoints served a Server Card at `<endpoint>/server-card` that has the v1 required fields (8.6% [7.7–9.7] of 2,834 endpoints where it was fetched). But one gateway host accounts for 184 of them, so only 60 of 2,085 hosts serve a valid card (2.6% when each host counts once).
- **Stable over four days.** Re-probed 4.4 days later (round 2, 2026-11-09), 97.4% [96.8–97.9] of endpoints kept the same primary status (Cohen's κ = 0.959). Round 2's figures are within a point of round 1's: 55.9% `ok`, 14.1% of handshakes modern, 9 Skills declarers, 250 valid Server Cards, 60.1% of tools annotated.
- **Tool annotations cover about 60% of tools.** Across 30,014 listed tools, 59.7% [59.2–60.3] carry an `annotations` object. 56.7% of endpoints annotate every tool and 31.2% declare an `outputSchema` on at least one. The median tool input schema is 721 bytes (p90 1,202; max 22,977), and the median endpoint's schemas total 4,390 bytes (p90 41,222).

## 1. Why a re-probe

Edition 1 (published 2026-10-23) found that most listed remote MCP endpoints work, but few spoke the `2026-07-28` revision and a quarter mishandled errors. Since then, the reference servers moved to the stateless revision, the Skills extension reached Beta, and Server Cards were finalised. This edition asks, on the same endpoints, whether servers followed.

## 2. Method (summary of the pre-registration)

- **Sample:** Edition 1's seeded random sample of 3,000 endpoints from the 26,365-endpoint registry frame of 2026-10-12, unchanged, so results pair. New registry entries are **not** included this time.
- **Probe:** Edition 1's harness (1.0.0), imported unchanged: `server/discover`, then legacy `initialize` where needed, `tools/list`, and a call to the non-existent tool `__glintbase_probe_nonexistent_tool__`; RFC 9728 metadata on 401. **No real tool was called.**
- **Additions (1.1.0):** extensions read from the handshake's `capabilities.extensions`; tool annotation, `outputSchema` and schema size read from the existing `tools/list` response; `skills/list` only where the Skills extension is declared; `GET <endpoint>/server-card`. The additions never pushed an endpoint above 8 requests.
- **Identity:** `GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot; research@glintbase.dev)`, from one residential connection in Nigeria (AS36873), the same as Edition 1.
- **Comparison round:** Edition 1's published headline round (2026-10-12, 17:24–17:53Z).

## 3. Results

### 3.1 Status, same endpoints, two dates

| Primary status | Edition 1.1 round 1 (n = 2,999) | Host-weighted |
|---|---|---|
| `ok` (handshake + tools listed) | 55.5% [53.7–57.3] | 46.3% |
| `auth_compliant` | 24.0% [22.5–25.6] | 30.3% |
| `unreachable` | 5.5% [4.7–6.4] | 7.1% |
| `not_mcp` | 5.0% [4.2–5.8] | 5.5% |
| `auth_noncompliant` | 4.5% [3.8–5.3] | 5.7% |
| `payment_required` | 2.2% [1.7–2.8] | 1.3% |
| `server_error` | 1.6% [1.2–2.2] | 2.1% |
| `jsonrpc_error` | 0.7% [0.5–1.1] | 0.6% |
| `legacy_sse` | 0.5% [0.3–0.9] | 0.7% |
| `handshake_only` | 0.4% [0.2–0.7] | 0.3% |
| `modern_rejected` | 0.1% [0.0–0.2] | 0.1% |

Paired changes against Edition 1 (McNemar exact test on discordant pairs):

| Outcome | Pairs | Edition 1 | Edition 1.1 | Lost | Gained | p |
|---|---|---|---|---|---|---|
| `ok` | 2,999 | 57.0% | 55.5% | 78 | 35 | 0.0001 |
| Modern era (handshaken both times) | 1,648 | 12.6% | 13.7% | 1 | 19 | < 0.001 |
| Auth compliant (auth-gated both times) | 837 | 82.9% | 84.2% | 1 | 12 | 0.0034 |
| In-channel canary error (answered both times) | 1,698 | 74.4% | 74.4% | 0 | 0 | — |
| Unreachable | 2,999 | 4.7% | 5.5% | 27 | 50 | 0.0117 |

The largest transitions were `ok → unreachable` (27), `ok → not_mcp` (23), `unreachable → ok` (15), `auth_compliant → unreachable` (13) and `auth_noncompliant → auth_compliant` (12). The full transition table is in `summary.json`.

### 3.2 New features

- **Extensions:** 41 of 1,677 handshaking endpoints (2.4%) declare at least one. Of 9 declaring Skills, all 9 returned a `skills/list` result.
- **Server Cards:** 354 endpoints answered `/server-card` with HTTP 200, 284 with a JSON object, and 245 with the v1 required fields (`$schema`, `name`, `version`, `description`). 242 of the 284 JSON cards used the `application/mcp-server-card+json` media type. Among `ok` endpoints, 12.6% [11.0–14.2] serve a valid card. Host concentration matters here: one host holds 184 of the 245.
- **Tool metadata:** see the summary. Annotation coverage is a property of whole servers: most endpoints annotate all of their tools or none.

## 4. What this can't claim

- **Not a trend.** Two points 3.5 weeks apart, on a sample drawn from the October registry. New servers registered since then aren't in it.
- **Not quality.** Whether tools, Skills or cards are useful or correct isn't measured. A declared extension says nothing about the skills behind it.
- **Server Card prevalence is a lower bound.** Cards listed in an AI Catalog, or at other paths, weren't fetched.
- **One registry, one vantage point, first page of `tools/list` only**, as in Edition 1.
- **Re-test interval.** Round 2 ran 4.4 days after round 1, not ~24 h as planned, because the research session was halted (Deviation 2). Agreement therefore includes genuine server changes over four days.
- **Interrupted round.** The workstation slept for 13.4 h during round 1. Endpoints in flight, and those probed in the two minutes after resume, were re-probed (Deviation 1), so round 1 spans 06:41–06:50Z and 20:14–21:01Z.
- **Small cells.** The Skills and extension counts are single digits to low tens; their intervals are wide.
- **Comparison with other probes is descriptive.** Kin Lane's probe (vendor post: 44 of 1,450 endpoints on `2026-07-28`) used a different frame and date.

## 5. Validation

30 endpoints (seed `20261104`, stratified by status, including up to 6 with Skills or cards) were re-checked by an independent Node client written for the purpose. Agreement: **28/30 (93.3%) on primary status**, 29/30 on Server Card validity, and 30/30 on Skills declaration. Both disagreements were servers whose state changed between fetches (a `tools/list` timeout in round 1; a timeout in the second check). A first version of the checker mislabelled two `-32020` rejections; it was fixed and the whole check re-run, and both outputs are kept. **Founder sign-off pending** (spot-check of 5; see `REVIEW_QUEUE.md`).

### 3.3 Re-test (RQ5)

Round 2 (2026-11-09 06:20–06:48Z, same harness and sample, same ASN) classified 2,999 endpoints. 2,922 (97.4% [96.8–97.9]) kept their round-1 primary status; Cohen's κ = 0.959. Round 2 shares: `ok` 55.9% [54.1–57.7]; modern among handshakes 14.1% [12.5–15.9]; Skills declared 0.5% (9); valid Server Card 8.8% [7.8–9.9] of 2,853 fetched; tools annotated 60.1% [59.5–60.6] of 30,333.

## 6. Pending before publication

- Founder validation sign-off.
- 7-day right of reply for any named vendor (none named so far; the gateway host is not named).

*Glintbase sells Agent Readiness Score audits, which include MCP checks.*
