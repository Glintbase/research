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
