# Pre-registration — The Silent Wall, Part C: does a signature open the wall? (E6)

> **Status:** Frozen 2026-11-04 by commit on branch `research/l1-web-week`, before any request of this study was sent.
> Any change after freezing is listed under *Deviations*.
> **Authors:** Glintbase Research · **Contact:** research@glintbase.dev
> **Parent study:** [The Silent Wall](../the-silent-wall/PREREGISTRATION.md) (its pre-registration lists Part C as optional). **Programme:** `GLINTBASE_RESEARCH_PROGRAM_NOV2026.md` §5 E6, decision D12 (internal).

## 1. Research questions

- **RQ1 (primary):** Does adding a verifiable identity — Web Bot Auth HTTP Message Signatures — change how sites' edges treat our honest research agent, compared with the same agent unsigned? Outcome: homepage "challenged or blocked".
- **RQ2:** Does the effect differ by CDN/WAF vendor (descriptive)?
- **RQ3:** How do both agent arms compare with the headless-browser control, and with The Silent Wall's October results for the same domains (descriptive; different dates)?

No directional hypothesis. The expected result may well be "no difference": unless an edge has registered or otherwise trusts our key, a signature it can't verify against a known agent may be ignored.

## 2. Sample

The Silent Wall's **150 domains and frozen page lists** (`../the-silent-wall/data/sample/pages.jsonl`: homepage plus up to 3 sitemap pages) and its frozen `robots.txt` decisions for the token `GlintbaseResearch`, unchanged, for direct comparison.

## 3. Arms

| Arm | Client | Identity |
|---|---|---|
| `unsigned` | httpx 0.28.1 (The Silent Wall's `agent` fetch code, imported unchanged) | `User-Agent: GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot; research@glintbase.dev)`; obeys the frozen robots decisions (`self_excluded`) |
| `signed` | identical to `unsigned` | plus, on every request **including each redirect hop**: `Signature-Agent: sig1="https://glintbase.dev"`, `Signature-Input: sig1=("@authority" "signature-agent";key="sig1");created;expires(+300 s);keyid(JWK SHA-256 thumbprint);alg="ed25519";nonce;tag="web-bot-auth"`, `Signature: sig1=:…:` (RFC 9421, Ed25519; draft-meunier-webbotauth-httpsig-protocol-02) |
| `browser` | headless Chromium via Playwright (The Silent Wall's `browser` identity, unchanged) | default UA |

- **No Cloudflare-registered arm** (programme §10.6: registration can't clear in a week).
- **Key directory (prerequisite for `signed`):** the public key is published as a JWK Set at `https://glintbase.dev/.well-known/http-message-signatures-directory` with media type `application/http-message-signatures-directory+json` (draft-meunier-webbotauth-httpsig-directory-00), and the bot page describes it. The `signed` arm runs **only after** that URL serves our key; the go-live time and the served JWKS are recorded in `data/run_notes.md`. If the directory can't go live this week, the `signed` arm doesn't run and the study reports only the unsigned and browser rounds (a stated outcome, not a failure to hide).
- **Signature check before the signed rounds:** our signatures are verified against the published directory by an independent verifier (a Web Bot Auth test endpoint or a second implementation), recorded in the run notes.

## 4. Rounds

- **U-rounds (unsigned + browser), available now:** `U1` on 2026-11-04/05 and `U2` on a later day. They give the unsigned agent's and the browser's current outcomes, a re-test of The Silent Wall's agent/browser rates on the same pages, and the unsigned arm's day-to-day stability.
- **S-rounds (all three arms in one domain session), after the directory is live:** `S1` and `S2` on different days. Arm order is randomised per domain and round (seed: SHA-256 of `domain|round|part-c`).
- **Primary comparison (RQ1) uses S-rounds only**, where unsigned and signed run minutes apart in the same session: `S1` is the headline; `S2` is the replication.
- **Pacing (as The Silent Wall):** ≤ 1 request/s within an arm, ≥ 30 s between arms on a domain, fresh cookies per (domain, arm), up to 4 domains in parallel. Never concurrently with another study's traffic from this lane; a per-minute connectivity log runs alongside.
- **Vantage point:** the researcher's residential connection (as The Silent Wall); IP/ASN recorded in run notes.

## 5. Classification

The Silent Wall's per-request classifier (`../the-silent-wall/harness/analyze.py`, unchanged): `self_excluded`, `error`, `challenge`, `block`, `rate_limited`, `ok`, `thin`, `other`; domain outcome = homepage outcome (primary) and worst page (secondary); CDN vendor from headers by The Silent Wall's rules.

## 6. Analysis (`harness/compute_stats.py`; every published number from `data/summary.json`)

- Per arm and round: shares of homepage outcomes with **Wilson 95% intervals**.
- **RQ1:** McNemar's exact test, `unsigned` vs `signed`, on homepage "challenged or blocked", among domains where both arms returned an HTTP response (errors excluded and counted), with discordant counts, in `S1` (headline) and `S2` (replication). Also `unsigned` vs `browser` and `signed` vs `browser`.
- **RQ2:** the same discordant counts by CDN vendor (descriptive; small cells flagged).
- **Stability:** per-arm agreement of homepage outcomes between rounds, Cohen's κ.
- **RQ3:** U- and S-round rates beside The Silent Wall's published October rates (descriptive only).
- Results are aggregated; named domains appear only for public robots facts.

## 7. Validation gate

30 domain × arm results from `S1` (or from `U1` if no S-round runs), seed `20261104`, stratified by outcome and arm. Each is re-checked by hand from the stored headers and markers, and the homepage re-opened with an independent client where relevant; agreement recorded in `data/validation.csv`. **≥ 90%** required, else fix the classifier and re-run. The founder spot-checks 5 and signs before publication.

## 8. Ethics

Honest identities only; the signature asserts who we are and nothing else. No CAPTCHA solving or bypassing — a challenge is recorded, never evaded. No spoofing of any vendor's crawler. Public pages only; about 12 requests per domain per arm-round; opt-out honoured. A CDN vendor named in a finding gets a 7-day right of reply before publication.

## 9. What this can't claim

- How edges treat **registered** signed agents (no registered arm), or vendors' verified crawlers.
- Whether an edge verified our signature at all: we see only outcomes, not the edge's verification result.
- Generality beyond 150 popular domains, one vantage point, and a few days.

## Deviations

1. **2026-11-09, before any E6 request. U-rounds dropped; S-rounds start directly; nonce length set to 64 bytes.**
   - **Why:** the research session was halted 2026-11-04 to 2026-11-09, and the key directory went live (07:02:54Z on 2026-11-09) before any U-round could run. Running all three arms in the same session (S-rounds) is the pre-registered primary design, so the U-rounds, whose purpose was to use time before the directory was live, are not run.
   - **Rounds:** `S1` on 2026-11-09 (after the E1/E3 re-crawl finishes; never concurrently), `S2` on 2026-11-10.
   - **Nonce:** §3 didn't fix the nonce length. The first build used 32 bytes, which Cloudflare's reference verifier (`web-bot-auth` 0.2.0) rejects; it is now 64 bytes. No signed request had been sent to any study site. Verification results are in `data/run_notes.md`.
   - **Consequence:** the study's comparison with The Silent Wall's October rates uses S-round `unsigned` and `browser` arms.

2. **2026-11-14, before S1. Rounds moved to 2026-11-14 and later; different network vantage point.**
   - **Why:** the research sessions were halted again between 2026-11-09 and 2026-11-14, so S1 didn't run on 2026-11-09 as planned.
   - **Vantage point:** S1 runs from public IP 102.90.126.151 (Nigeria), in an AfriNIC allocation (102.88.0.0–102.95.255.255) registered to `ORG-MN1-AFRINIC`, **not** the AS36873 (Airtel) connection The Silent Wall used. The ASN wasn't confirmed (the lookup service was rate-limited).
   - **Consequence:** the primary comparison (unsigned vs signed, same session, same IP) is unaffected. The descriptive comparison with The Silent Wall's October rates (RQ3) now also differs by network and is labelled so; IP reputation may differ.

3. **2026-11-14/15. An extra same-day re-test (`S1R`); S2 runs on 2026-11-15 as planned.**
   - **What happened:** on 2026-11-14 the founder asked in-session for S2 to run immediately. It started at 13:39:42Z, 17 minutes after S1 finished, with the same harness, sample, arms, pacing and vantage point (102.90.126.151, NG); the signed arm was re-checked at the transport layer just before. The founder's relayed decision, "Tomorrow, as planned", arrived while it ran.
   - **Action (2026-11-15, before any outcome of that run was looked at):** the 2026-11-14 run is relabelled **`S1R`**, an exploratory same-day re-test that is **not** the pre-registered replication. **S2 runs on 2026-11-15** as §4 says.
   - **Reporting:** S1R appears only in a labelled exploratory section (same-day repeatability). The primary comparison is S1, and the replication is S2.

4. **2026-11-14, during S1R. Connection outage; affected domains set aside.**
   - **What happened:** the per-minute connectivity log failed three checks in a row, at 13:55:30, 13:56:30 and 13:57:31Z.
   - **Rule (fixed before looking at outcomes):** every domain with any arm whose `started_at` falls between 13:50:30Z and 14:02:31Z (5 minutes either side of the failed checks) is set aside. That's 37 domains, moved to `data/edge/_discarded/round_S1R_outage/`. Because S1R is exploratory and S2 replaces it as the replication, they are not re-run; S1R covers the remaining 113 domains.

5. **2026-11-15/16. S2 outage and early stop; affected and unreached domains re-run.**
   - **What happened:** during S2 on 2026-11-15, the connectivity log failed four checks (14:03:25–14:06:27Z). From 14:02:55Z the browser got `ERR_NAME_NOT_RESOLVED` and the HTTP arms got connect errors. The run then stopped at 111 of 150 domains (the research session hit its usage limit), and the monitor stopped logging after 14:06Z.
   - **Rule (Deviation 4's rule, applied from timestamps only, before looking at S2 outcomes):** every domain with any arm started between 13:58:25Z and 14:11:27Z (5 minutes either side of the failed checks) is moved to `data/edge/_discarded/round_S2_outage/`. Those domains and every domain not reached are re-run with the unchanged harness on 2026-11-16, after the same pre-checks (keep-awake, transport-layer signing check, connectivity).
   - **Consequence:** S2 spans 2026-11-15 (domains finished before the outage) and 2026-11-16 (the rest). Each record keeps its own `started_at`. Both dates differ from S1's, so S2 is still a different-day replication.
   - **Vantage point for the 2026-11-16 part:** public IP 197.211.52.5 (Nigeria), AfriNIC 197.211.52.0/24 (remark "ENTERPRISE-PHC"), a different allocation from S1's and the 2026-11-15 part's (102.88.0.0–102.95.255.255). Within each domain all three arms still run minutes apart from the same IP, so the paired comparison is unaffected. Cross-round comparisons (stability) now also differ by network for these 63 domains, and the report says so.
