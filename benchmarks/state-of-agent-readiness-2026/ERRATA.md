# Errata: State of Agent Readiness 2026

> **Correction date**: 2026-10-12
> **Source of truth**: [`data/full-scores.csv`](data/full-scores.csv) and [`data/research-dataset.json`](data/research-dataset.json) (generated 2026-08-05). The two files agree with each other on every platform's ARS, pass counts and hops.
> **Not changed**: the PDF in `reports/` is left as published. This file lists every place we found where the PDF or the README disagrees with the data.

---

## 1. Nature of the dataset

- **Simulated traversal, not live agent runs.** Every record comes from the deterministic Pathfinder scanner. The scanner does not call an LLM, and its token figures are a fixed function of hop count. Every 1-hop benchmark costs 2,620 (or 2,575) tokens, every 2-hop benchmark 3,240 (or 3,195), every 3-hop benchmark 3,860, and so on in steps of 620. Treat the "tokens", "wasted tokens" and "cost" figures as modelled estimates, not measured consumption.
- **The 450 live-harness runs have no published data.** PDF §6, Figures 4 and 10, and the Resilience Tax table describe 450 live executions across OpenCode CLI, Cursor and Antigravity. No per-run data, transcripts or harness outputs for them exist in this repository. Those results cannot be checked, so we removed them from README-level summaries. The PDF text remains as published.
- **The surface flags are unreliable.** `hasLlmsTxt`, `hasOpenApi`, `hasMcp`, `hasSitemap`, `hasChangelog` and `hasGithub` (CSV `LlmsTxt`, `OpenAPI`, …) are `true` / `1` for **all 100** records. No adoption rate can be computed from them.

## 2. Headline numbers: README and PDF vs. data

| Item | README (before) | PDF | Data | Note |
|---|---|---|---|---|
| Mean ARS | 50.7 | 50.7 | **50.66** | Agrees |
| Median ARS | n/a | 52 | **52** | Agrees |
| Max ARS | n/a | 85 (OpenAI, Hall of Fame #1) | **79** (Runway) | No platform scores ≥ 80 |
| Platforms with ARS ≥ 80 ("Optimal") | n/a | 6 | **0** | |
| Tier counts ≥80 / 70–79 / 50–69 / 30–49 / <30 | n/a | 6 / 12 / 42 / 28 / 12 | **0 / 5 / 49 / 38 / 8** | |
| llms.txt adoption | 52% | 18% (p. 6, p. 10 "only 18") | flag is `true` for 100/100 | Unreliable; **no supportable figure** |
| Mean traversal hops | 27.4 ("4.6× optimal") | 9.2 (live harness, unpublished) | **17.59** summed hops per platform across 10 benchmarks (median 18, range 10–57). Minimum possible is 10, so ≈1.76× | |
| Annual token tax | "$433,200 / year per 1,000 active agent developers" | $433,200 / yr at "100k sessions/mo" | not in dataset | See §4 |
| Token waste | n/a | "~550k tokens waste / 1K sessions" | 549,995 wasted tokens **summed across the 100-platform cohort** (one modelled traversal each) | Unit wrong in PDF |
| Mean token efficiency | n/a | 84.0% | 84.0% (`meanEfficiency` 0.84) | Agrees |

## 3. Per-platform and per-benchmark disagreements (PDF vs. data)

**Platform ARS**

| Platform | PDF | Data (`full-scores.csv`) |
|---|---|---|
| OpenAI | 85 (Hall of Fame #1, "gold standard") | **35** (rank 85 of 100) |
| Anthropic | 78 (Hall of Fame #2) | **57** |
| Cohere | 72 | **66** |
| Replicate | 70 | **60** |
| Pinecone | 70 | **58** |
| Hugging Face | 35 | **64** |
| Turbopuffer | 55 | **61** |
| AutoGen (Microsoft) | 25 | **14** (lowest in cohort) |
| Vercel | 65 (p. 17) / 67 (Appendix A) | **67** |
| DeepSeek | 68 (Appendix A) | **39** |
| LlamaIndex, DeepInfra, Fal.ai, Lovable, E2B | 48, 48, 46, 58, 31 | Agree |

The data's top five are Runway 79, Letta 73, Exa 72, Cerebrium 71 and OpenRouter 71, not the PDF's Hall of Fame. PDF Appendix A lists Runway (79) as rank 1 and OpenAI (85) as rank 2, which contradicts itself.

**Benchmark pass rates** (from the CSV `*_Status` columns; they match `cohortStats.benchmarkPassRates`)

| Benchmark | PDF | Data |
|---|---|---|
| B-01 Cold Start Discoverability | 97% | **95%** |
| B-02 Machine Entrypoint Quality | 93% | **94%** |
| B-03 Auth Path Completeness | 21% | 21% |
| B-04 Quickstart Completeness | 18% | 18% |
| B-05 SDK Discoverability | 29% | 29% |
| B-06 API Reference Navigability | 16% | **18%** |
| B-07 Core Concept Disambiguation | 16% | 16% |
| B-08 Error Surface Completeness | 13% | **11%** |
| B-09 Rate Limit Transparency | 8% | **0%** |
| B-10 Versioning & Change Signal | 22% | 22% |

**Category means** (PDF §3 → data)

| Category | PDF N / mean | Data N / mean |
|---|---|---|
| A Foundation Models | 24 / 68.4 ("highest-performing category") | 24 / **44.7** (second-lowest) |
| B AI Infrastructure | 12 / 54.2 | 12 / **51.8** |
| C Vector Databases | 10 / 61.0 | 10 / **52.4** |
| D Observability & Evals | 10 / 48.5 | 10 / **53.0** |
| E Orchestration & Frameworks | 10 / 42.1 ("second-lowest") | 10 / **52.9** |
| F Dev Tools & Media APIs | 10 / 49.8 | **14 / 56.3** |
| G Data & Annotation | 6 / 44.0 | 6 / **44.2** |
| H Agent & Automation | 8 / 46.2 | 8 / **52.4** |
| I Security & Guardrails | 5 / 41.0 | **4 / 45.8** |
| J Gateways & Edge | 5 / 52.6 | **2 / 67.0** |

**Regions**: the PDF gives US N=68, mean 52.4. The data has USA N=70, mean 53.3. China, Korea, Australia and India together are N=12, mean 36.6, against the PDF's "China & Asia-Pacific N=18, 46.8". All other regions together are N=18, mean 49.8, against the PDF's "Europe & Canada N=14, 53.1".

**llms.txt differential**: PDF §5 claims "mean ARS 72.4 with llms.txt vs 45.8 without". This cannot be reproduced, because the dataset marks every platform as having llms.txt.

## 4. The $433,200 figure

The PDF's cost table (§5) computes the annual tax as follows:

> (low-ARS session cost − high-ARS session cost) × 100,000 sessions/month × 12, using **Claude Fable 5 input pricing** ($10 / 1M tokens)
> = ($482.00 − $121.00 per 1k sessions) × 100 × 12 = **$433,200 / year**

That is a figure **per 100,000 agent sessions per month**, comparing a hypothetical 48,200-token session with a hypothetical 12,100-token session. Neither session size appears in the dataset; the dataset's mean modelled session is 30,856 tokens. It is **not** "per 1,000 active agent developers", as the README said. The same calculation gives $216,600 for GPT 5.6 Sol and $64,980 for Gemini 3.6 Flash.

## 5. Licence conflict (resolved 2026-10-12)

- Every page of the PDF carries "© 2026 Glintbase Research & Developer Infrastructure Labs. **All rights reserved.**"
- The root `README.md` states that benchmark datasets and reports are licensed **CC-BY 4.0**.
- PDF Appendix B says the UABS prompts are published under the **MIT License**.
- `LICENSE` and `CITATION.cff` say **Apache-2.0** (code).

**Resolution:** the PDF, datasets, transcripts and benchmark prompts are © 2026 Glintbase, all rights reserved, matching the PDF footer. The README's CC-BY 4.0 statement and the MIT note in Appendix B are withdrawn. Apache-2.0 continues to cover the code (`LICENSE`, `CITATION.cff`).

## 6. Minor

- PDF Appendix A points to `ars-report/data/exports/full-scores.csv`. In this repository the file is at `data/full-scores.csv`.
- The PDF's "1,000 Pathfinder scans" matches the data: 100 platforms × 10 benchmarks.
