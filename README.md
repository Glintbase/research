<div align="center">

# Glintbase Research & Systems Intelligence Lab
### Empirical Benchmarks, Datasets, and Evaluation Suites for Autonomous AI Coding Agents

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Research: All rights reserved](https://img.shields.io/badge/Research%20%26%20Data-All%20rights%20reserved-lightgrey.svg)](#license--ethics-statement)
[![Benchmarks: 2 Published](https://img.shields.io/badge/Benchmarks-2%20Published-crimson.svg)](https://glintbase.dev/research)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://python.org)

[Explore Interactive Research Hub](https://glintbase.dev/research) • [Sandboxes Edition 1](benchmarks/sandboxes-edition-1) • [ARS 2026 Report](benchmarks/state-of-agent-readiness-2026) • [Citation](#citation)

</div>

---

## Overview

Welcome to the canonical research repository for **Glintbase**. This repository hosts the open-source evaluation harnesses, canonical datasets, mathematical models, high-resolution visual assets, and whitepapers developed by the Glintbase Research & Systems Intelligence Lab.

Our mission is to establish rigorous, empirical, and reproducible standards for **Agent Experience (AX)** and machine-operable developer infrastructure. We do not rely on vendor marketing claims, synthetic prompt vanity benchmarks, or front-door documentation; we deploy live, autonomous AI coding agents to measure real execution friction, token bleed, and runtime gotchas.

---

## Published Benchmark Editions

> **Corrections (2026-10-12):** both published benchmarks have been corrected. See [`benchmarks/sandboxes-edition-1/ERRATA.md`](benchmarks/sandboxes-edition-1/ERRATA.md) and [`benchmarks/state-of-agent-readiness-2026/ERRATA.md`](benchmarks/state-of-agent-readiness-2026/ERRATA.md).

| Series & Edition | Title | Scope | Date | Status & Deliverables |
|---|---|---|---|---|
| **Integration Index · Sandboxes Edition 1** (latest) | [**The Glintbase Integration Index: Sandboxes Edition 1**](benchmarks/sandboxes-edition-1) | 5 Cloud Sandboxes (Modal, E2B, boat.dev, Vercel, Daytona) | October 2026 | Published pilot, corrected 2026-10-12 • 30 agent trials (n=1 each) • 119 front-door checks • 5 figures • Gotchas dossier. Corrected pass rate is 28/30. Prompts differed by provider, so the ranking is indicative only. |
| **State of Agent Readiness 2026 · Edition 1** | [**State of Agent Readiness 2026 (ARS 2026)**](benchmarks/state-of-agent-readiness-2026) | 100 developer platforms across 10 categories | August 2026 | Published, corrected 2026-10-12 • 24-page PDF • dataset of 1,000 simulated Pathfinder traversals (100 platforms × 10 benchmarks). The PDF's 450 live-harness runs have no published data. |

## Studies in Progress

Each study is pre-registered before data collection; its README states the research question, design and current status. Reports marked "draft" are not yet final publications.

| Study | Question | Status |
|---|---|---|
| [**State of Agent Readiness 2026 — Edition 2**](benchmarks/state-of-agent-readiness-2026-edition-2) | Do measured runtime behaviours predict agent task success better than static discoverability signals? | Planned (paused at design) |
| [**The Silent Wall**](benchmarks/the-silent-wall) | How do public bot policies and WAF behaviour treat declared AI agents vs. browsers? | Published 2026-10-23 · [report](benchmarks/the-silent-wall/reports/REPORT.md) |
| [**Remote MCP Server Reliability**](benchmarks/production-mcp-reliability-crisis) | How often do public remote MCP servers fail protocol, discovery, and error-signalling basics? | Data collected · [draft report](benchmarks/production-mcp-reliability-crisis/reports/REPORT.md) |
| [**Beyond Self-Reporting**](benchmarks/beyond-self-reporting-execution-gap) | How far do agents' self-reported completions diverge from verified backend state in integration tasks? | Paused |

---

## Repository Structure

```
glintbase-research/
├── README.md                                # Canonical research index and reproduction guide
├── LICENSE                                  # Apache 2.0 License
├── CITATION.cff                             # Machine-readable citation metadata
├── BOT.md                                   # Description of the research crawler user agent
├── .gitignore
│
└── benchmarks/
    ├── sandboxes-edition-1/                 # The Glintbase Integration Index: Cloud Sandboxes
    │   ├── README.md                        # Summary, leaderboard table, and reproduction steps
    │   ├── ERRATA.md                        # Corrections of 2026-10-12 with evidence
    │   ├── .env.example                     # Environment key template (zero secrets)
    │   │
    │   ├── reports/
    │   │   ├── REPORT_SANDBOXES_EDITION_1.md# Canonical publication whitepaper
    │   │   ├── METHODOLOGY.md               # Mathematical formulation of Integration Tax (IT)
    │   │   ├── GOTCHAS_AND_TRAPS.md         # Runtime trap stack traces and workarounds
    │   │   └── DAYTONA_AGENT_EXECUTION_TRACE.md # Dedicated execution trace & gotchas deep-dive
    │   │
    │   ├── transcripts/                     # Complete autonomous agent traces (JSONL + Markdown)
    │   │   ├── boat/                        # Trials 1–6 (24 to 88 raw transcript events per trial)
    │   │   ├── daytona/                     # Trials 1–6 (33 to 110 raw transcript events per trial)
    │   │   ├── e2b/                         # Trials 1–6 (50 to 85 raw transcript events per trial)
    │   │   ├── modal/                       # Trials 1–6 (20 to 32 raw transcript events per trial)
    │   │   └── vercel/                      # Trials 1–6 (42 to 92 raw transcript events per trial)
    │   │
    │   ├── data/
    │   │   ├── benchmark_master.json        # 30-trial results as published (tokens/steps/time self-reported)
    │   │   ├── benchmark_master.csv         # Tabular dataset for pandas / R / spreadsheet analysis
    │   │   ├── integration_tax_summary.json # Aggregated median and total metrics per provider
    │   │   ├── measured_metrics.csv         # Turns, tool calls, session length derived from transcripts
    │   │   ├── trial_corrections.csv        # Per-trial corrections (raw rows left unchanged)
    │   │   └── phase1-scans/                # Raw machine scanner outputs (modal, e2b, etc.)
    │   │
    │   ├── visuals/                         # High-resolution publication figures
    │   │   ├── visual1_master_leaderboard_table.png
    │   │   ├── visual2_frontdoor_vs_reality_scatter.png
    │   │   ├── visual3_challenge_progression_linegraph.png
    │   │   ├── visual4_integration_tax_leaderboard.png
    │   │   └── visual5_provider_challenge_heatmap.png
    │   │
    │   ├── harness/                         # Evaluation scripts & per-trial solutions
    │   │   ├── calculate_tax.py             # Computes Integration Tax from run logs
    │   │   ├── generate_visuals.py          # Generates publication graphics with embedded badges
    │   │   ├── measure_transcripts.py       # Derives measured metrics from transcripts
    │   │   └── solutions/                   # Per-provider PROMPT.txt, solution.py, verify.py, run_log.json
    │   │
    │
    ├── state-of-agent-readiness-2026/       # Foundational 100-Platform Ecosystem Audit
    │   ├── README.md                        # Abstract and headline numbers (recomputed from data)
    │   ├── ERRATA.md                        # Every PDF-vs-data disagreement; licence flag
    │   ├── reports/
    │   │   └── STATE_OF_AGENT_READINESS_2026.pdf # 24-page PDF as originally published (1.1 MB)
    │   └── data/
    │       ├── full-scores.csv              # 100 Platforms × 10 Benchmarks score matrix (source of truth)
    │       └── research-dataset.json        # Simulated traversal records for all 100 platforms
    │
    ├── state-of-agent-readiness-2026-edition-2/ # PLANNED (paused): design only, no data
    ├── the-silent-wall/                     # PLANNED: protocol being finalised, no results
    ├── production-mcp-reliability-crisis/   # PLANNED: protocol being finalised, no results
    └── beyond-self-reporting-execution-gap/ # PLANNED (paused): design only, no data
```

---

## Quickstart: Reproducing Sandboxes Edition 1

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/glintbase/research.git
cd research/benchmarks/sandboxes-edition-1

python3 -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
pip install matplotlib seaborn pandas pillow requests
```

### 2. Inspect Raw Empirical Data

```python
import pandas as pd
df = pd.read_csv("data/benchmark_master.csv")
print(df.groupby("provider")[["total_tokens", "steps_count", "wall_time_seconds"]].median())  # column is "provider" (corrected 2026-10-12)
```

### 3. Recalculate Integration Tax ($IT$)

```bash
python harness/calculate_tax.py
```

### 4. Regenerate Visuals

```bash
python harness/generate_visuals.py
```

All 5 publication graphics will be rendered directly to `visuals/`. (The values are hard-coded in the script and reflect the original publication, not the 2026-10-12 corrections.)

### 5. Derive Measured Metrics from the Transcripts

```bash
python harness/measure_transcripts.py   # writes data/measured_metrics.csv (standard library only)
```

### 6. (Optional) Re-run a Trial and Its Verifier

Running `solution.py` / `verify.py` under `harness/solutions/<provider>/<trial>/` creates real sandboxes on your own account. It needs `python-dotenv`, the provider SDK, and credentials in a `.env` file (see `.env.example`). The SDK versions below are the ones listed in `reports/METHODOLOGY.md` §3:

```bash
pip install python-dotenv requests
pip install modal==1.6.1          # Modal
pip install e2b==1.0.5            # E2B
pip install boat-sdk==1.5.0       # boat.dev
pip install vercel-sandbox==0.7.0 # Vercel Sandbox (imported as vercel.sandbox)
pip install daytona==0.222.0      # Daytona
```

The corrected `verify.py` exits non-zero when sandboxes are still running after the solution finishes. The Trial 6 verifiers also require a real unittest or pytest summary.

---

## The Integration Tax Formula

$$\text{Integration Tax (IT)} = \left[ 0.40 \times \left(\frac{\text{Tokens}_{\text{med}}}{\text{Min Tokens}}\right) + 0.40 \times \left(\frac{\text{Steps}_{\text{med}}}{\text{Min Steps}}\right) + 0.20 \times \left(\frac{\text{Time}_{\text{med}}}{\text{Min Time}}\right) \right] \times \text{Penalty}$$

- **Minima Baseline**:
  - $\text{Min Tokens} = 1,865$ (E2B)
  - $\text{Min Steps} = 3.0$ (Modal & boat.dev)
  - $\text{Min Time} = 19.5\text{s}$ (Modal)
- **Penalty Multiplier**:
  $$\text{Penalty} = 1.0 + \frac{100 - \text{Pass Rate}}{50} \quad (\text{when Pass Rate } < 100\%)$$

> **Caveat (2026-10-12):** the token, step and time inputs to this formula were self-reported by the agent, and prompts differed by provider. Treat the resulting ranking as indicative, not as a controlled comparison. See the Sandboxes Edition 1 [`ERRATA.md`](benchmarks/sandboxes-edition-1/ERRATA.md).

---

## Citation

If you use Glintbase benchmarks, datasets, or methodologies in your academic research or industry engineering reports, please cite us:

### BibTeX: Sandboxes Edition 1 (October 2026)

```bibtex
@techreport{glintbase2026sandboxes,
  title = {The Glintbase Integration Index: Sandboxes Edition 1 — Empirical Benchmark on Cloud Code Sandboxes for Autonomous AI Coding Agents},
  author = {{Glintbase Research \& Developer Infrastructure Labs}},
  institution = {Glintbase},
  year = {2026},
  month = {October},
  type = {Empirical Benchmark Report},
  url = {https://glintbase.dev/research},
  note = {Evaluating Modal, E2B, boat.dev, Vercel Sandbox, and Daytona across 119 scans and 30 live agent trials}
}
```

### BibTeX: State of Agent Readiness 2026 (August 2026)

```bibtex
@techreport{glintbase2026ars,
  title = {State of Agent Readiness 2026: Global Benchmark Report on Developer Infrastructure Accessibility for Autonomous AI Coding Agents},
  author = {{Glintbase Research \& Developer Infrastructure Labs}},
  institution = {Glintbase},
  year = {2026},
  month = {August},
  type = {Benchmark Research Report},
  url = {https://glintbase.dev/research},
  note = {N=100 platforms, 1,000 simulated Pathfinder traversals; see ERRATA.md}
}
```

---

## License & Ethics Statement

- **Code & Harnesses**: [Apache License 2.0](LICENSE) covers the code in this repository (harness scripts, verifiers, solution code).
- **Research Reports, Datasets, Transcripts & Prompts**: © 2026 Glintbase. All rights reserved. You may read, cite and quote them with attribution; redistribution or republication requires written permission (research@glintbase.dev). This replaces the earlier CC-BY 4.0 statement (changed 2026-10-12) and the MIT note in the ARS 2026 PDF Appendix B.
- **Independence Disclosure**: Glintbase maintains zero affiliate compensation or preferential ranking deals with any evaluated infrastructure vendor. All evaluation trials are conducted in deterministic, isolated environments using standard customer tiers.

For questions, corrections, or vendor re-scan requests, reach out to **research@glintbase.dev** or open an issue.
