# State of Agent Readiness 2026, Edition 2 (SOAR E2): does the ARS score predict agent success?

**Glintbase Research · DRAFT, PROVISIONAL · 2026-11-20**
Pre-registration: [`PREREGISTRATION.md`](PREREGISTRATION.md) (frozen 2026-11-04 before the cohort snapshot, scans and runs; deviations in §12) · Statistics: [`data/stats/results.json`](data/stats/results.json), [`data/stats/summary.md`](data/stats/summary.md) · Analysis code: [`harness/compute_stats.py`](harness/compute_stats.py)

> **Provisional.** The answer keys are LLM-drafted and not yet verified. Victor Okolie reviews them blind to the runs (§4, option (b)). After that review, every run is re-graded from saved evidence and this analysis is re-run. Any number below may change, and none may be published before then. Platforms named in the results also get a 7-day right of reply (§10).
>
> **Conflict of interest:** Glintbase sells ARS audits. This study tests whether that score means anything, and it is published whichever way it goes (§11).

---

## Summary

We asked three coding-agent harnesses to complete cold-start tasks on 88 developer platforms, using only each platform's public documentation. The harnesses were Claude Code, OpenCode and Codex CLI, on `claude-haiku-5-5`. There were three task families per platform:
- the API authentication header;
- a minimal first request;
- error or rate-limit behaviour.

That made 1,470 episodes, plus a `claude-sonnet-5-5` arm of 234 episodes on 29 platforms. We then tested whether each platform's Agent Readiness Score (ARS 3.3.1, frozen before the runs) predicted how often agents succeeded.

**On the provisional keys, it didn't.**

- **H1 is not supported.** The measured Runtime pillar does not predict platform success rate. Spearman ρ = −0.03 (95% CI −0.24 to 0.18; Holm p = 1.0; n = 88).
- **H2 is not supported.** Runtime_measured does not predict better than Discoverability_measured: the difference in ρ is −0.00 (CI −0.29 to 0.28).
- **H3 is not supported.** Runtime_measured is not associated with fewer tool calls per successful run: ρ = +0.04 (CI −0.19 to 0.26).
- **No ARS measure predicts success.** That includes the published pillars and the overall score: ρ from −0.05 to −0.01, every CI spanning 0.
  - The run-level mixed model agrees. Odds ratio per SD of Runtime_measured: 0.86 (95% interval 0.68–1.07). For Discoverability_measured: 0.92 (0.75–1.14).
  - So does the cluster-robust GEE: 0.91 (0.60–1.36) and 0.90 (0.60–1.36).
- **What did predict success was the task family, not the platform's score.**
  - Haiku success was 99.0% on the authentication-header task, 91.8% on error and rate-limit behaviour, and 70.8% on the minimal first request.
  - In the mixed model, the platform random effect (SD 2.4 on the log-odds scale) dwarfs the harness effect (SD 0.25).
  - Platforms differ a lot, but in ways ARS doesn't capture.
- **The harnesses performed alike.** Haiku success was 86.3% for Claude Code, 87.6% for Codex CLI and 87.6% for OpenCode, with mean platform success 0.87 (SD 0.17). Sonnet: 89.7%, with ρ(Runtime_measured) = −0.02 (CI −0.39 to 0.36, n = 29).

**What this means for ARS (if it holds after key review).** Neither the measured nor the published pillars of ARS 3.3.1 tell you whether a coding agent can do a docs-only cold-start task on a platform. As pre-committed (§11), the ARS 3.5 weights rationale must be updated from this result. The report and blog post must say so as prominently as a positive result would have been reported.

## Results

### Pre-registered hypotheses (Haiku arm, 88 platforms)

| | Hypothesis | Estimate | 95% CI | p (Holm) | Supported |
|---|---|---|---|---|---|
| H1 | ρ(Runtime_measured, success) > 0 | −0.03 | [−0.24, 0.18] | 1.00 | No |
| H2 | ρ(Runtime_m) − ρ(Discoverability_m) > 0 | −0.00 | [−0.29, 0.28] | 1.00 | No |
| H3 | ρ(Runtime_measured, tool calls per success) < 0 | +0.04 | [−0.19, 0.26] | 1.00 | No |

The two primary predictors are almost uncorrelated with each other (ρ = 0.02).

### Secondary (reported, not confirmatory)

| Predictor | ρ with success | 95% CI |
|---|---|---|
| Discoverability (measured) | −0.02 | [−0.23, 0.19] |
| Runtime (published) | −0.05 | [−0.26, 0.16] |
| Discoverability (published) | −0.01 | [−0.21, 0.21] |
| ARS overall | −0.05 | [−0.26, 0.17] |

- **By family, ρ(Runtime_measured):**
  - authentication +0.15 [−0.03, 0.30];
  - first request +0.06 [−0.15, 0.27];
  - error and rate-limit −0.20 [−0.38, 0.01].
  - None excludes 0, and the signs disagree.
- **Within category** (category-stratified): −0.03 [−0.24, 0.16].
- **Judge-graded outcome:** −0.05 [−0.26, 0.16].
- **Per harness (exploratory):** Claude Code +0.06, Codex CLI −0.10, OpenCode −0.06; all CIs span 0.
- **Scan re-test reliability** (89 platforms, two scans):
  - Runtime_measured ρ = 0.84 (identical on 81%);
  - Discoverability_measured ρ = 0.85 (identical on 43%);
  - ARS overall ρ = 0.86.
  - The predictors are stable, so the null result is not explained by noisy scores.

### Outcome distribution

- Haiku, 1,470 episodes: 1,281 successes, 175 wrong answers, 9 without a final answer and 5 false refusals.
- 60% of platforms scored ≥ 0.9. That is below the pre-registered ceiling flag (80%), but the outcome is skewed high, which limits variance.

## Limitations

- **Keys are provisional.** See the box at the top.
- **Power** (§9): n = 88 detects ρ ≈ 0.29 with 80% power. A small true association can't be ruled out. A strong one (ρ ≥ 0.3) is unlikely given the CIs.
- **Selection effect** (§12.3): rule-4 replacements removed platforms whose homepages block bots, including OpenAI. The cohort under-represents exactly the platforms where an access-related score should matter most.
- **Missing pairs** (§12.5): 25 platform × family pairs and 2 platforms have no key, so some platforms' success rates rest on two families.
- **Task scope:** only docs-only cold-start Task A. Authenticated and error-recovery tasks (B, C) are deferred to Edition 2.1 (D14).
- **Models and harnesses:** Anthropic models only; three harnesses with their shipped tools.
- **Reviewer:** one human reviewer, so no inter-rater κ.

## Method

- **Cohort:** 90 platforms, the top 15 by GitHub stars in each of 6 categories, from a dated snapshot under a written rule (§2). 88 were analysed; Freestyle and Orama have no keys.
- **Predictors:** ARS 3.3.1 scans frozen before any run (§3).
- **Tasks:** 245 tasks (§4, §12.5).
- **Runs** (§5):
  - Haiku arm: 3 harnesses × 2 repetitions;
  - Sonnet arm: 78 tasks × 3 harnesses × 1;
  - fresh E2B sandbox per episode, fetch arm;
  - $0.50, 80 model calls and 600 s per episode, at most 2 concurrent episodes per docs host.
- **Pilot:** 147 episodes; it passed (0 invalid, $0.011 and 33 s per episode).
- **Outages:** episodes lost to workstation outages were rerun identically (§12.10). The final data has 0 infrastructure errors in 1,704 episodes.
- **Statistics:** Spearman ρ with 10,000-resample percentile bootstrap CIs (seed 20261105), Holm-corrected one-sided bootstrap p-values, a Bayesian binomial mixed GLM, and a cluster-robust GEE logit (§8). Every number comes from `compute_stats.py`.
- **Cost:** about $37 in model spend (Haiku arm $14.28, Sonnet arm $21.09, pilot $1.60), plus E2B sandbox time.

## Before publication

1. Victor's blind key review → `data/key_verdicts.csv`.
2. Re-grade with `--reanalyse` (both experiments), then `compute_stats.py collect` and `analyse`.
3. Update this draft from the new outputs.
4. Right of reply for named platforms.
5. Update the ARS 3.5 weights rationale.
