# SOAR Edition 2: statistics summary

Generated 2026-11-20T18:22:04+00:00 by `harness/compute_stats.py`.

> Keys not yet verified (no `data/key_verdicts.csv`): grades use the LLM-drafted keys. Not for publication.

- Haiku arm: 88 platforms analysed, 2 excluded; mean platform success rate 0.87 (SD 0.17); share ≥ 0.9: 0.60

| Hypothesis | Estimate | 95% CI | p (one-sided) | p (Holm) | Supported (CI) |
|---|---|---|---|---|---|
| H1 ρ(Runtime_measured, success) > 0 | -0.03 | [-0.24, 0.18] | 0.5990 | 1.0000 | False |
| H2 ρ(Runtime_m) − ρ(Discoverability_m) > 0 | -0.00 | [-0.29, 0.28] | 0.5119 | 1.0000 | False |
| H3 ρ(Runtime_measured, tool calls per success) < 0 | 0.04 | [-0.19, 0.26] | 0.6284 | 1.0000 | False |

ρ between the two primary predictors: 0.02. H3 uses 88 platforms with ≥ 3 successful runs.

## Secondary

| Predictor | ρ with success | 95% CI | n |
|---|---|---|---|
| discoverability_measured | -0.02 | [-0.23, 0.19] | 88 |
| runtime_published | -0.05 | [-0.26, 0.16] | 88 |
| discoverability_published | -0.01 | [-0.21, 0.21] | 88 |
| ars_overall | -0.05 | [-0.26, 0.17] | 88 |

Judge-graded outcome, ρ(Runtime_measured): -0.05 [-0.26, 0.16].

## Mixed-effects logistic regression (run level, Haiku)

| Term | OR per SD | 95% interval |
|---|---|---|
| z_rt | 0.86 | [0.68, 1.07] |
| z_disc | 0.92 | [0.75, 1.14] |

Sonnet arm (descriptive): 29 platforms, ρ(Runtime_measured) -0.02 [-0.39, 0.36].

