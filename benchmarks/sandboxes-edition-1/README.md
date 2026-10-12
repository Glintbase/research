# The Glintbase Integration Index: Sandboxes Edition 1

> **Status**: Completed Pilot Cohort ($n=1$ Deterministic)  
> **Evaluation Subjects**: Modal, E2B, boat.dev (ASCII), Vercel Sandbox, Daytona  
> **Published**: October 2026  
> **Authors**: Glintbase Research & Developer Infrastructure Labs  
> **Interactive Report**: [https://glintbase.dev/research?edition=sandboxes](https://glintbase.dev/research?edition=sandboxes)

> [!WARNING]
> **Corrections (2026-10-12)**: see [`ERRATA.md`](ERRATA.md).
> - **Prompts were not identical across providers.** The ranking is **indicative only, not a controlled comparison.**
> - Tokens, steps and wall time were **self-reported by the agent**, not measured by the harness.
> - The pass rate is **28/30 (93.3%)**, not 100%. Modal and boat ran no tests in Trial 6.
> - "0 leaks" was **not verifiable** with the published verifier.
> - Human stops recorded in the transcripts are **0 for every provider**.
> - The boat 402, Modal malformed-token, Vercel human-stop and Daytona 401 traps are **not captured** in the published transcripts.

---

## Executive Summary

Autonomous coding agents (e.g. Devin, OpenCode, Cursor, Antigravity) require instant, disposable, secure compute environments to install dependencies, run test suites, and execute arbitrary code. Every cloud sandbox provider claims instant boots and frictionless APIs.

We evaluated 5 leading cloud sandboxes across **119 front-door scanner runs** and **30 live, empirical agent integration trials** across 6 standardized challenges:
1. **Hello Lifecycle**: Zero-state microVM boot and stdout probe.
2. **Install & Run Dependencies**: Installing binary packages (`polars`) and executing calculations.
3. **Remember Me (State Persistence)**: Cross-command disk persistence in `/tmp/state.txt`.
4. **Serve It (Ingress Networking)**: Spawning an HTTP server and obtaining external public preview URLs.
5. **Break It (Error Resilience & Recovery)**: Trap intentional `1/0` errors and probe health recovery.
6. **Real Job (SWE Test Suite)**: Cloning `bottlepy/bottle` and running unit test suites.

---

## The Master Leaderboard

*As originally published, with corrected columns marked. Front-Door ARS corrected 2026-10-12 to the Phase 1 scan values in `data/phase1-scans/`. The previous values (Modal 89, E2B 31, Vercel 58, Daytona 54) matched neither the scans nor the report. Scores from State of Agent Readiness 2026 come from a different scanner and scale and are not comparable.*

| Rank | Platform | Integration Tax ($IT$) | Front-Door ARS | Median Tokens | Total Tokens | Median Steps | Total Steps | Median Time | Total Time | Human Stops ($H_s$) | Stumbles ($!$) | Leaks |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **Modal** | **1.03x** | 36 / 100 | 2,010 | 12,380 | 3.0 | 20 | 19.5s | 123.5s | ~~1~~ 0 | 0 | n/v |
| **2** | **E2B** | **1.17x** | 75 / 100 | 1,865 | 10,910 | 3.5 | 21 | 29.2s | 170.1s | 0 | 0 | n/v |
| **3** | **boat.dev** | **1.21x** | 82 / 100 | 2,580 | 26,598 | 3.0 | 22 | 25.0s | 154.0s | ~~1~~ 0 | 1 | n/v |
| **4** | **Vercel Sandbox** | **1.37x** | 69 / 100 | 2,235 | 13,820 | 5.0 | 31 | 21.6s | 141.8s | ~~1~~ 0 | 0 | n/v |
| **5** | **Daytona** | **1.43x** | 48 / 100 | 2,260 | 16,520 | 5.0 | 37 | 27.4s | 188.3s | 0 | ~~1~~ 0 | n/v |

*n/v = not verifiable. The published verifier deleted leftover sandboxes and still passed; Daytona Trial 4 had one. With corrected pass rates (Modal and boat 5/6), the published penalty rule gives E2B 1.17x, Vercel 1.37x, Modal 1.37x, Daytona 1.43x and boat 1.61x. Token, step and time medians are self-reported; transcript-measured counts are in [`data/measured_metrics.csv`](data/measured_metrics.csv).*

---

## Directory Contents

- `reports/`:
  - [`REPORT_SANDBOXES_EDITION_1.md`](reports/REPORT_SANDBOXES_EDITION_1.md): Flagship publication whitepaper.
  - [`METHODOLOGY.md`](reports/METHODOLOGY.md): Measurement specification, formula derivations, and mathematical rules.
  - [`GOTCHAS_AND_TRAPS.md`](reports/GOTCHAS_AND_TRAPS.md): Runtime traps and workarounds. *(Correction 2026-10-12: most of the traps listed are not captured in the published transcripts, and each is labelled.)*
  - [`DAYTONA_AGENT_EXECUTION_TRACE.md`](reports/DAYTONA_AGENT_EXECUTION_TRACE.md): Dedicated autonomous agent trace breakdown and recommendations for Daytona.
- [`ERRATA.md`](ERRATA.md): Corrections of 2026-10-12, with evidence.
- `transcripts/`:
  - Complete autonomous agent execution traces (credentials and one unrelated private repository listing redacted on 2026-10-12) (both machine-readable `transcript.jsonl` and formatted `transcript_readable.md`) across all 30 trials (Modal, E2B, boat.dev, Vercel, Daytona).
- `data/`:
  - [`benchmark_master.csv`](data/benchmark_master.csv): Canonical 30-trial results matrix.
  - [`benchmark_master.json`](data/benchmark_master.json): Deep run logs with token prompt/completion splits.
  - [`integration_tax_summary.json`](data/integration_tax_summary.json): Normalized provider-level aggregates.
  - [`measured_metrics.csv`](data/measured_metrics.csv): Turns, tool calls and session length derived from the transcripts by `harness/measure_transcripts.py` (added 2026-10-12).
  - [`trial_corrections.csv`](data/trial_corrections.csv): Per-trial corrections to the raw rows, which are left unchanged (added 2026-10-12).
- `visuals/`:
  - High-resolution figures (`visual1` through `visual5`). These show the originally published values and have not been regenerated.
- `harness/`:
  - Python calculation and visualization scripts, `measure_transcripts.py`, and per-trial `PROMPT.txt`, `solution.py`, `verify.py` and `run_log.json`. The `verify.py` files were corrected on 2026-10-12: leftover sandboxes now fail the leak check, and Trial 6 requires a real test-run summary.
- `distribution/`:
  - Social distribution launch kit for X and LinkedIn. *(Annotated 2026-10-12: do not publish as written.)*

