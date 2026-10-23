# The Silent Wall: How Bot Defences Treat AI Agents

> **Status**: Published 2026-10-23. Data collected 2026-10-12/13; final report in [`reports/REPORT.md`](reports/REPORT.md). The pre-registered validation gate passed (20/20 hand-checked results agreed, ≥ 90% required). Protocol and deviations: [`PREREGISTRATION.md`](PREREGISTRATION.md).
> **Authors**: Glintbase Research

---

## Research Question

How do enterprise websites' **published policies** (`robots.txt`, AI-usage policies) and **observable edge behaviour** (WAF challenges, blocks, rate limits) treat AI agents compared with ordinary browsers — and how often do the two disagree?

## Design (summary)

1. **Policy census.** For a fixed list of ~150 domains, fetch `robots.txt` once and record the rules for real, vendor-documented agent tokens (e.g. `GPTBot`, `OAI-SearchBot`, `ChatGPT-User`, `ClaudeBot`, `Claude-User`, `Claude-SearchBot`, `PerplexityBot`, `Google-Extended`). Token names are verified against each vendor's documentation at study start.
2. **Behavioural probe — honest identities only.** Request a small fixed set of public pages per domain using:
   - a Glintbase research agent that identifies itself truthfully (`GlintbaseResearchAgent/1.0 (+https://glintbase.dev/research/bot)`),
   - a generic HTTP-client baseline (e.g. Python `requests` default user agent),
   - a real headless browser baseline.

   We do **not** spoof third-party crawler user agents. Edge networks verify those crawlers by IP range, reverse DNS, or Web Bot Auth signatures, so a spoofed request measures impostor detection, not how real agents are treated.
3. **Classification.** Response status, challenge markers (e.g. `cf-mitigated`, interstitial pages), and whether the content an agent needs is reachable.

## Ethics & Rate Limits

- Sequential requests, ≤1 request/second per domain, ≤10 pages per domain.
- Our own agent obeys `robots.txt` for its own token.
- A public page describes the bot and gives an opt-out contact.
- Domain-level results are reported in aggregate; named examples only where the policy is public.

## Directory Layout (populated as the study runs)

- `harness/` — census and probe scripts
- `data/` — raw responses (headers only, no page bodies stored), classifications
- `reports/` — whitepaper (written only after analysis)
