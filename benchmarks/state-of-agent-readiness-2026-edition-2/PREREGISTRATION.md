# Pre-registration — State of Agent Readiness 2026, Edition 2 (SOAR E2)

> **Status:** Frozen 2026-11-04 by commit on branch `research/soar-e2`, **before** the cohort snapshot, before any scan and before any agent run. Any change after this commit is listed under §12 *Deviations*, with date and reason.
> **Study:** E7 in the November 2026 research programme. Hypotheses H1–H3 are those of Research Plan v2 §5, unchanged.
> **Authors:** Glintbase Research · **Contact:** research@glintbase.dev
> **Conflict of interest:** Glintbase sells Agent Readiness Score (ARS) audits. This study tests whether that score means anything. The result is published whichever way it goes (§11).

## 1. Question and hypotheses

**Question.** Do a developer platform's ARS pillar scores, and especially the *measured* runtime pillar, predict whether AI coding agents can complete a cold-start integration task using only that platform's public documentation? And do they predict it better than static discoverability?

| | Hypothesis | Test | Supported if |
|---|---|---|---|
| **H1** | ρ(Runtime_measured, success) > 0 | Spearman ρ across platforms; 95% percentile bootstrap CI | CI lower bound > 0 |
| **H2** | ρ(Runtime_measured, success) − ρ(Discoverability_measured, success) > 0 | paired bootstrap of the difference (same resamples) | CI lower bound > 0 |
| **H3** | Runtime_measured is negatively associated with tool calls per successful run | Spearman ρ across platforms between Runtime_measured and the median tool calls of that platform's successful runs | CI upper bound < 0 |

Confirmatory claims use Holm's correction across H1–H3 (bootstrap p-values, one-sided in the stated direction). Uncorrected CIs are reported alongside.

## 2. Cohort rule

**Unit:** a developer platform: a company or product that exposes a public HTTP API used with a credential, documented on public pages.

**Categories (6) and the candidate pool.** The pool is fixed in `data/cohort/candidate_pool.csv`, committed with this document: 25–31 candidates per category, each with one pre-assigned category, a homepage and its official GitHub owner account. Categories: `sandboxes_compute`, `llm_apis`, `vector_search`, `backend_infra`, `agent_tooling`, `payments_comms`.

**Ranking rule.** For each candidate, *stars* = `stargazers_count` of the most-starred public, non-fork repository owned by its official GitHub account, from the GitHub search API (`user:<owner> fork:false`, sorted by stars), fetched once and saved with timestamps in `data/cohort/github_stars_snapshot.json` (`harness/cohort_snapshot.mjs snapshot`). Within each category, candidates are ranked by stars, descending; ties are broken by `platform_id` alphabetically. **The top 15 per category form the cohort (90 platforms).** The rest are the ordered reserve list (`data/cohort/ranking.csv`).

**Exclusions decided in advance.**
- Anthropic is not in the pool: the agents under test run on Claude models, so Anthropic's own API would confound the result.
- Glintbase is not in the pool.

**Replacement rule (the only permitted changes to the cohort).** A selected platform is replaced by the next-ranked reserve in the same category, and the replacement is logged in `data/cohort/replacements.csv`, only if:
1. the search result's owner does not match the declared owner (wrong handle in the pool; the corrected handle is then looked up once and ranked by the same rule), or
2. its API documentation is not publicly readable without signing in (checked by fetching the docs root once), or
3. it has no public HTTP API used with a credential (e.g. a library only), or
4. the scanner cannot score its homepage (`TARGET_UNREACHABLE`, or homepage blocked) in both of two attempts 1 h apart.

No platform is removed or replaced for any other reason, and never after scan results are seen except under rule 4.

**Docs entry point.** Each cohort platform gets one documentation root URL (`docs_root` in `data/cohort/cohort.csv`): the public docs home for its HTTP API. Agents start there. It is chosen before tasks are drafted and is not changed afterwards.

## 3. Predictors (frozen)

Each cohort homepage is scanned at the **live ARS release `ars-3.3.1`** (137 checks, registry at glintbase.dev/methodology), using the public CLI so the scan is reproducible by anyone and writes nothing to the public leaderboard:

```
@glintbase/cli 3.5.0 with @glintbase/scanner-core 3.5.1   (glintbase -V → "3.5.0 (ars-3.3.1, @glintbase/scanner-core 3.5.1)")
glintbase audit https://<homepage> --json --offline --profile deep
```

`--offline` turns off LLM-assisted evaluation, so LLM-dependent checks (brand-search accuracy, agentic search) are `skip` and drop out of denominators under the evidence-only rule. This matches what the public CLI computes without a model key; it can differ slightly from the hosted scanner at scan.glintbase.dev, which has an LLM provider configured.

Every report is saved raw as `data/raw_scans/<platform_id>__<UTC timestamp>.json`. Each platform is scanned **twice, at least 1 h apart**. Scan 1 is the frozen predictor; scan 2 is used only for re-test reliability (Spearman ρ between scans, per pillar). Predictors are frozen at commit of the scan files, before any agent run; they are never recomputed from later scans.

| Predictor | Definition | Role |
|---|---|---|
| **Runtime_measured** | `pillars.runtimeMeasured.score`: usability (+ payments, when applicable) layer, non-bonus checks with `measurement ∈ {live, content}` and status pass/warn/fail; earned = maxPoints of passing checks / sum of maxPoints | **primary** (H1, H2, H3) |
| **Discoverability_measured** | same formula over the discovery + access layers (computed in `compute_stats.py`) | **primary** (H2) |
| Runtime (published) | `pillars.runtimeErgonomics.score` | secondary |
| Discoverability (published) | `pillars.discoverability.score` | secondary |
| ARS overall | `score` | secondary |

## 4. Task (Task A only) and families

Task A is a **docs-only cold start with no account**. Tasks B and C (authenticated read/write, error recovery) need free-tier accounts and are deferred to Edition 2.1 (decision D14).

Each platform gets exactly **one task in each of three families (90 × 3 = 270 tasks)**:

| Family | What the agent is asked | What the key checks |
|---|---|---|
| `soar_auth_header` | Which HTTP header, and which scheme or prefix if any, carries the credential when calling the platform's HTTP API directly | header name, plus scheme/prefix when the docs state one |
| `soar_first_request` | The HTTP method and full URL (base URL + path) of a named minimal first request, e.g. the quickstart's first call or a list/get call on the core resource | method, API host, path |
| `soar_error_rate_limit` | What the API does when the client exceeds the rate limit: HTTP status plus one platform-specific documented detail (the limit, the header that signals reset/retry, or the error code string). If the docs do not document rate limiting, the same question about a documented authentication error | status code plus the platform-specific detail |

Each instruction names the platform and never contains the answer. Agents end with `FINAL ANSWER: …` or `FINAL ANSWER: UNABLE - <reason>`, under AgentSim's standard prompt.

**Answer keys (option (b), §10.5 of the programme).** With one reviewer available, keys are **drafted by an LLM (`claude-sonnet-5-5`) from quoted sources and verified by one human**, Victor Okolie. Each key carries: the source URL, a verbatim quote from that page (checked programmatically to occur on the fetched page), the proposed answer, acceptable alternatives, and unanswerable conditions. The deterministic grader is a boundary-safe regex built only from strings copied from the page; it must accept the canonical answer and reject a perturbed one. Victor marks each key `correct`, `fix` (with the corrected answer) or `unanswerable`, **without seeing any agent run**: the review sheet contains no run data. **No inter-rater agreement (κ) can be reported; the report says so.**

## 5. Runs

Runs are executed by AgentSim (private; code and traces are not published) on a single run queue owned by the runs lane.

| Arm | Platforms | Tasks | Harnesses | Repetitions | Episodes |
|---|---|---|---|---|---|
| **Haiku (primary)** | 90 | 270 | `claude-code`, `opencode`, `codex` | 2 | **1,620** |
| Sonnet (secondary) | 30 | 90 | same 3 | 1 | 270 |

- Model: `claude-haiku-5-5` for the primary arm; `claude-sonnet-5-5` for the secondary arm. Harness versions are those pinned in the sandbox image and recorded per run.
- Sonnet subset: per category, the 5 platforms with the lowest `sha256("soar-e2-sonnet:" + platform_id)`.
- Arm `fetch` (each harness's own web tools; no browser). Default AgentSim budget per episode: $0.50, 80 model calls, 600 s wall, 120 requests per host. Each episode runs in a fresh sandbox.
- Pilot: 10% of Haiku episodes first, as a go/no-go on invalid-run rate (< 10%) and on cost and duration (within 3× exp_2026_10_26_001). Pilot episodes are not re-used in the analysis unless the pilot passes unchanged, in which case they are kept as the first part of the run.

## 6. Outcome

- **Run success (primary):** AgentSim's deterministic key grade: `outcome = success` (or `correct_refusal` for a key verified as `unanswerable`-by-design; none are planned). Every other outcome (`fail`, `false_refusal`, `no_answer`) is a failure.
- **Runs excluded:** `status = infra_error` (sandbox, proxy or gateway failure: not the agent's fault). Timeouts, stalls and exhausted budgets count as failures.
- **Platform success rate:** successful / valid Haiku runs over that platform's tasks (up to 18).
- **Secondary outcome:** the LLM judge's verdict (AgentSim's second grader) in place of the key grade (sensitivity analysis).
- **Keys:** the analysis uses keys after Victor's verification. Runs are re-graded from saved evidence (`--reanalyse`) with the verified keys. Tasks whose key is marked `unanswerable` are dropped from the primary analysis; tasks marked `fix` are graded with the corrected key.
- **Tool calls:** `metrics.agent.toolCalls` (the single definition of "steps").

## 7. Exclusions (platforms)

A platform is excluded from the analysis (and counted in the report) if fewer than half of its Haiku runs are valid, or if all three of its keys are marked `unanswerable`.

## 8. Analysis (`harness/compute_stats.py`)

1. **Platform-level Spearman ρ** between each predictor and the platform success rate, with 95% percentile bootstrap CIs (10,000 resamples of platforms, seed 20261105). H1 on Runtime_measured.
2. **H2:** paired bootstrap of ρ(Runtime_measured) − ρ(Discoverability_measured), same resamples.
3. **H3:** platform-level Spearman ρ between Runtime_measured and the median `toolCalls` over the platform's successful Haiku runs (platforms with ≥ 3 successful runs), bootstrap CI as above.
4. **Mixed-effects logistic regression** at run level (Haiku arm): `success ~ z(Runtime_measured) + z(Discoverability_measured) + family + (1 | platform) + (1 | harness)`, fitted as a Bayesian binomial mixed GLM (variational Bayes; `statsmodels BinomialBayesMixedGLM`, default priors), reporting posterior means and 95% intervals in odds-ratio units per SD. A cluster-robust GEE logit (clusters = platform, same fixed effects plus harness) is reported as a robustness check.
5. **Secondary (reported, not confirmatory):** the same ρ for the published pillars and ARS overall; by family; within category (category-stratified ρ, and a mixed model with a category fixed effect); the Sonnet arm on its 30 platforms; the judge-graded outcome; scan re-test reliability.
6. **Exploratory:** closed-book answerability (whether Haiku answers the task correctly with no web access) as a covariate, if measured; per-harness ρ.

All numbers in the report are produced by `compute_stats.py` from files in `data/`.

## 9. Power, stated honestly

- With n = 90 platforms, a two-sided test at α = 0.05 has 80% power for ρ ≈ 0.29 (Fisher z). An observed ρ of 0.40 has a 95% CI of roughly 0.21–0.56.
- H2 compares two correlated correlations. If the two pillars correlate at about 0.5 with each other, the study can only detect a difference of about 0.25–0.30 in ρ. A smaller true difference will likely come out as "not supported", and the report will say that this is a power limit, not evidence of no difference.
- Each platform's success rate rests on up to 18 episodes, so it is measured with noise; that attenuates ρ towards 0.
- Docs-only tasks on popular platforms may be near ceiling. If more than 80% of platforms score ≥ 0.9, the report says the outcome had too little variance to test the hypotheses well. The analysis does not change.
- The Sonnet arm (n = 30) can only detect ρ ≳ 0.5; it is descriptive.

## 10. What is published

- Public (this repository): this pre-registration, the cohort rule, the candidate pool, the stars snapshot, the ranking, the frozen raw scans, the task families and method (§4), platform-level aggregates (success rates, predictors), the analysis code and its outputs.
- Not public: answer keys, task instructions with keys, agent transcripts and traces, and AgentSim code (decision D10). Keys stay out of the public repository so that agents in later runs cannot find them on the web. The key review sheet is kept locally and git-ignored.
- Named platforms see their own rows 7 days before publication (right of reply).

## 11. Commitment

The report is published whatever the result. If ARS pillars do not predict success, the report and the blog post say so with the same prominence as a positive result, and the ARS 3.5 weights rationale is updated from it.

## 12. Deviations

*(None yet. Each deviation is added here with its date and reason.)*

Known differences from the programme text, decided before freezing:
- Predictors are at the live `ars-3.3.1`, not `ars-3.4.x`, so the study does not wait on the 3.4 release (programme §10.6).
- Keys follow option (b): LLM-drafted from quoted sources, one human verifier, no κ (programme §10.5, decision D15).
- Victor's key verification may finish after the runs; it is done blind to run outcomes, and runs are re-graded from saved evidence with the verified keys before any analysis.
