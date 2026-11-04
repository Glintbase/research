# State of Agent Readiness 2026 — Edition 2

> **Status**: **Pre-registered 2026-11-04** ([PREREGISTRATION.md](PREREGISTRATION.md)). Cohort snapshot, frozen scans and agent runs follow. There are no results yet.
> **Authors**: Glintbase Research

---

## Research Question

Do **measured runtime behaviours** of a developer platform (live MCP handshake, tool discovery, in-channel error signalling, OpenAPI contract content) predict whether an autonomous coding agent completes real integration tasks — and do they predict it better than **static discoverability signals** (`robots.txt`, `llms.txt`, sitemaps, presence of an OpenAPI file)?

## Hypotheses (to be tested, not assumed)

- **H1**: Runtime Ergonomics score correlates positively with task success (Spearman ρ > 0).
- **H2**: Runtime Ergonomics predicts task success better than Discoverability (difference in ρ, bootstrap 95% CI excludes 0).
- **H3**: Lower Runtime Ergonomics is associated with more tokens and tool calls per successful task.

Null and negative results will be published with the same prominence as positive ones.

## Design (summary)

| Element | Plan |
|---|---|
| Cohort | ~90 developer platforms, stratified across 6 categories, selected by a written rule fixed before any scan |
| Predictors | ARS 3.1 Discoverability and Runtime Ergonomics pillars, computed only from checks that perform a live measurement (presence-only checks are reported separately) |
| Outcome | Agent task success, graded by a verifier (ground-truth answer key or API read-back), never by the agent's own claim |
| Tasks | A: docs-only cold start (all platforms) · B: authenticated read/write (free-tier subset) · C: error recovery from a real invalid request (free-tier subset) |
| Repetitions | 3 per task × 2 current frontier models |
| Analysis | Spearman ρ with bootstrap CIs; mixed-effects logistic regression (platform random effect); pre-specified exclusions |

The frozen protocol is [PREREGISTRATION.md](PREREGISTRATION.md). It supersedes the design summary above where they differ (Task A only, ARS `ars-3.3.1` predictors, 3 harnesses × 2 repetitions on Claude Haiku 5.5 plus a 30-platform Sonnet 5.5 arm).

## Related Work (third-party, not Glintbase work)

The studies below were produced by other organisations. They are cited as background only. None of their figures are Glintbase results or deliverables of this study, and none of their data is included in this repository.

- **Ora** (external), *AX is the new AEO*: Ora's own data release (CC BY 4.0), a stratified sample of 37,927 journeys across 1,056 sites. <https://github.com/ora/research>
- **Emelyanov et al.** (external), *WebPageBench: Event-Level Verification and Controlled UI-Variant Generation for Web Agents*, arXiv:2609.35026. The up-to-41-point claimed-vs-verified gap reported there is their result, not ours.
- **Microsoft** (external), *What is Agent Experience (AX)?*: a definitional blog post. <https://developer.microsoft.com/blog/what-is-agent-experience-ax/>
- **FTA Global** (external), *Agent Readiness Study 2026*: their study of 50 Indian e-commerce sites. <https://www.ftaglobal.in/post/research-agent-readiness-study-2026>

## Directory Layout (planned; all folders are currently empty)

Nothing below exists yet. These are the files the study plans to produce:

- `harness/` (planned): scan runner, trial runner, verifiers, `compute_stats.py`
- `data/` (planned): raw scans (`data/raw_scans/`, currently empty), per-trial results, statistical summary
- `transcripts/` (planned): redacted agent transcripts
- `reports/` (planned): whitepaper, written only after analysis
