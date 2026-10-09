# The Glintbase Integration Index: Sandboxes Edition 1

> **Status**: Completed Pilot Cohort ($n=1$ Deterministic)  
> **Evaluation Subjects**: Modal, E2B, boat.dev (ASCII), Vercel Sandbox, Daytona  
> **Published**: October 2026  
> **Authors**: Glintbase Research & Developer Infrastructure Labs  
> **Interactive Report**: [https://glintbase.dev/research?edition=sandboxes](https://glintbase.dev/research?edition=sandboxes)

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

| Rank | Platform | Integration Tax ($IT$) | Front-Door ARS | Median Tokens | Total Tokens | Median Steps | Total Steps | Median Time | Total Time | Human Stops ($H_s$) | Stumbles ($!$) | Leaks |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **Modal** | **1.03x** | 89 / 100 | 2,010 | 12,380 | 3.0 | 20 | 19.5s | 123.5s | 1 | 0 | 0 |
| **2** | **E2B** | **1.17x** | 31 / 100 | 1,865 | 10,910 | 3.5 | 21 | 29.2s | 170.1s | 0 | 0 | 0 |
| **3** | **boat.dev** | **1.21x** | 82 / 100 | 2,580 | 26,598 | 3.0 | 22 | 25.0s | 154.0s | 1 | 1 | 0 |
| **4** | **Vercel Sandbox** | **1.37x** | 58 / 100 | 2,235 | 13,820 | 5.0 | 31 | 21.6s | 141.8s | 1 | 0 | 0 |
| **5** | **Daytona** | **1.43x** | 54 / 100 | 2,260 | 16,520 | 5.0 | 37 | 27.4s | 188.3s | 0 | 1 | 0 |

---

## Directory Contents

- `reports/`:
  - [`REPORT_SANDBOXES_EDITION_1.md`](reports/REPORT_SANDBOXES_EDITION_1.md): Flagship publication whitepaper.
  - [`METHODOLOGY.md`](reports/METHODOLOGY.md): Measurement specification, formula derivations, and mathematical rules.
  - [`GOTCHAS_AND_TRAPS.md`](reports/GOTCHAS_AND_TRAPS.md): Detailed diagnostic traces of all 4 silent runtime traps with stack traces.
  - [`DAYTONA_AGENT_EXECUTION_TRACE.md`](reports/DAYTONA_AGENT_EXECUTION_TRACE.md): Dedicated autonomous agent trace breakdown and recommendations for Daytona.
- `transcripts/`:
  - Complete, unedited autonomous agent execution traces (both machine-readable `transcript.jsonl` and formatted `transcript_readable.md`) across all 30 trials (Modal, E2B, boat.dev, Vercel, Daytona).
- `data/`:
  - [`benchmark_master.csv`](data/benchmark_master.csv): Canonical 30-trial results matrix.
  - [`benchmark_master.json`](data/benchmark_master.json): Deep run logs with token prompt/completion splits.
  - [`integration_tax_summary.json`](data/integration_tax_summary.json): Normalized provider-level aggregates.
- `visuals/`:
  - High-resolution Anthropic-style figures (`visual1` through `visual5`).
- `harness/`:
  - Python calculation and visualization scripts, trial templates, and isolated trial solution scripts.
- `distribution/`:
  - Social distribution launch kit for X and LinkedIn.

