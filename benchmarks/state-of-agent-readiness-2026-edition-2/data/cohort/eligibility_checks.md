# Cohort eligibility checks (2026-11-04)

Replacement rules: PREREGISTRATION.md §2. Result: **no replacements** (`data/cohort/replacements.csv` not created).

- **Rule 1 (owner handle):** corrected once for convex, fireworks, perplexity (`owner_corrections.csv`, re-queried in `github_stars_snapshot.json` → `corrections`). `smithery-ai` owns no public non-fork repository, so Smithery has no valid star count and ranks last (`no_valid_owner`); it would not be selected either way.
- **Rule 2 (docs public without sign-in):** each selected `docs_root` was fetched once with the research user agent (`GlintbaseResearch/1.0`), 2026-11-04 ~20:30 UTC. 84 returned HTTP 200 directly; huggingface, alibaba and activeloop returned 200 on a retry with a 60 s timeout. **algolia, codesandbox, vultr** returned HTTP 403 with a Cloudflare challenge page ("Just a moment..."). That is a bot challenge, not a sign-in wall: the docs are public to people. They stay in the cohort under rule 2 as written; agents will meet the same challenge, which is part of what ARS measures (`anti-crawler-challenge-free`).
- **Rule 3 (public HTTP API with a credential):** every selected platform documents one (judged from the docs entry point; no platform failed).
- **Rule 4 (scanner cannot score the homepage):** see `data/raw_scans/manifest.jsonl`.
- **Snapshot timing:** the stars snapshot ran 2026-11-04 06:32–06:50 UTC and, after a DNS failure on this workstation stopped it, resumed 20:17–20:24 UTC for the remaining candidates. Every row carries its own `fetched_at`.
