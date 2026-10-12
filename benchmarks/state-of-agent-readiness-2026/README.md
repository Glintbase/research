# State of Agent Readiness 2026

> **Status**: Completed Global Benchmark ($N=100$ Platforms)  
> **Evaluation Subjects**: 100 Major AI & Developer Infrastructure Platforms across 10 Cohorts  
> **Published**: August 2026  
> **Authors**: Glintbase Research & Developer Infrastructure Labs  
> **Interactive Report**: [https://glintbase.dev/research?edition=ars2026](https://glintbase.dev/research?edition=ars2026)

---

## Executive Summary

Autonomous coding agents navigate documentation and developer infrastructure differently than human developers. Where humans skim visual layouts and parse marketing narrative, agents execute programmatic HTTP requests, grep plain-text indices, and follow structured quickstarts.

The **State of Agent Readiness 2026** report provides the first comprehensive empirical evaluation of the global developer ecosystem's machine operability.

> [!WARNING]
> **Corrections (2026-10-12).** The headline numbers below have been recomputed from `data/full-scores.csv` and `data/research-dataset.json`, which are the source of truth. The PDF disagrees with the data in many places: OpenAI's score, the top-ranked platforms, category means, llms.txt adoption and several benchmark pass rates. Every disagreement is listed, with both values, in [`ERRATA.md`](ERRATA.md).
>
> The dataset is a **simulated, deterministic traversal** by the Pathfinder scanner, not live agent runs. Its token figures are modelled from hop counts. The PDF also describes 450 live-harness runs; **no data for those runs is published in this repository**, so they are not summarised here.

### Key Headline Metrics (from the published data):
- **ARS across 100 platforms**: mean **50.7**, median **52**, range 14–79. The highest score is Runway at 79, and **no platform scores ≥ 80**. Selected platforms: OpenAI **35**, Anthropic **57**, AutoGen (Microsoft) **14**.
- **Benchmark pass rates**:

  | B-01 | B-02 | B-03 | B-04 | B-05 | B-06 | B-07 | B-08 | B-09 | B-10 |
  |---|---|---|---|---|---|---|---|---|---|
  | 95% | 94% | 21% | 18% | 29% | 18% | 16% | 11% | 0% | 22% |

  (Discovery → Auth → Quickstart → SDK → API Ref → Concepts → Errors → Rate Limits → Versioning.)
- **Traversal**: mean **17.6** summed hops per platform across the 10 benchmarks (median 18). The minimum possible is 10.
- **Machine index adoption (llms.txt)**: **cannot be determined from this dataset**, because the `hasLlmsTxt` flag is `true` for all 100 records. *(The earlier README figure of 52% and the PDF's 18% are both unsupported.)*
- **Modelled token cost**: the PDF's "$433,200 / year" compares a hypothetical 48,200-token session with a hypothetical 12,100-token session at Claude Fable 5 input pricing. It is a figure **per 100,000 agent sessions per month**, not "per 1,000 active agent developers" as this README previously said.

*Previous headline values (2026-10-12 correction): llms.txt adoption 52% → not determinable. Mean traversal 27.4 hops (4.6× optimal) → 17.6 hops (≈1.8× the 10-hop minimum). $433,200 "per 1,000 developers" → per 100k sessions/month.*

---

## Directory Contents

- `reports/`:
  - [`STATE_OF_AGENT_READINESS_2026.pdf`](reports/STATE_OF_AGENT_READINESS_2026.pdf): Full 24-page publication report, as originally published. Read it together with [`ERRATA.md`](ERRATA.md): many figures in the PDF disagree with the data, and its live-harness section has no published data. *(The PDF says "All rights reserved", which conflicts with the CC-BY 4.0 statement in the root README. This is flagged for the owner in ERRATA §5.)*
- [`ERRATA.md`](ERRATA.md): Every disagreement between the PDF, this README and the data, with both values (added 2026-10-12).
- `data/`:
  - [`full-scores.csv`](data/full-scores.csv): 100 platforms scored across 10 deterministic benchmarks.
  - [`research-dataset.json`](data/research-dataset.json): Deep metadata, grade distribution, and regional taxonomy. *(The `surfaces` flags are `true` for every record and should not be used.)*
