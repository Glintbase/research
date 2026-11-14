# Web census data (E1 + E3): what's ready

**Status (2026-11-14): READY.** Final census data from crawl pass 2 (2026-11-09, 2,636 sites) and pass 3 (2026-11-13/14 UTC, 4,272 sites); see E1/E3 Deviation 3. Validation: E1 30/30, E3 27/30. Founder sign-off pending, so treat as final data, unpublished results.

| File | Study | Contents | Ready? |
|---|---|---|---|
| `sample.csv`, `sample_meta.json` | E1 + E3 | The frozen site list (6,908 sites; `in_e1` / `in_e3` flags, sources, Tranco rank) | Yes (frozen 2026-11-04) |
| `../../content-signal-census/data/sites.jsonl` | E1 | One row per site: `class` (none / robots_only / header_only / agree / conflict), robots `*`-group policy, `Content-Signal` header values on HTML, Markdown, twin and docs responses, `md_served`, `md_vary_accept`, CDN | Yes (2026-11-14) |
| `../../content-signal-census/data/sites.csv` | E1 | Flat version of the above | Yes (2026-11-14) |
| `../../front-door-files-census/data/sites.jsonl` | E3 | One row per site: per-file outcome (valid / invalid / soft_404 / absent / error / self_excluded / not_requested), status, content type, media-type conformance; `catch_all`; root `Link` relations; AI Catalog entry types and cross-link result | Yes (2026-11-14) |
| `../../front-door-files-census/data/files.csv` | E3 | Flat version: one column per file outcome and content type | Yes (2026-11-14) |
| `raw/` | both | Per-site request records with kept bodies. **Not published** (gitignored) | — |

Notes for lane L2 (ARS 3.4):
- `not_requested` means the site was unreachable (robots.txt and the homepage both failed below HTTP), so no further requests were sent. Exclude these, and any row with `reachable: false`, from denominators.
- A file is `soft_404` when a 200 response is HTML where JSON/text/XML was expected, matches the control path's body, or fails validity while the control path also returned 200 with the same type.
- Validity rules are minimum-structure checks (see `../../front-door-files-census/PREREGISTRATION.md` §4), not full schema validation.
- Results are unvalidated until each study's `data/validation.csv` exists and its REVIEW_QUEUE item is signed.
