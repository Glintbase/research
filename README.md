<div align="center">

# Glintbase Research & Systems Intelligence Lab
### Empirical Benchmarks, Datasets, and Evaluation Suites for Autonomous AI Coding Agents

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Data License: CC-BY 4.0](https://img.shields.io/badge/Data%20License-CC--BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Benchmarks: 2 Active](https://img.shields.io/badge/Benchmarks-2%20Published-crimson.svg)](https://glintbase.dev/research)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://python.org)

[Explore Interactive Research Hub](https://glintbase.dev/research) • [Sandboxes Edition 1](benchmarks/sandboxes-edition-1) • [ARS 2026 Report](benchmarks/state-of-agent-readiness-2026) • [Citation](#citation)

</div>

---

## Overview

Welcome to the canonical research repository for **Glintbase**. This repository hosts the open-source evaluation harnesses, canonical datasets, mathematical models, high-resolution visual assets, and whitepapers developed by the Glintbase Research & Systems Intelligence Lab.

Our mission is to establish rigorous, empirical, and reproducible standards for **Agent Experience (AX)** and machine-operable developer infrastructure. We do not rely on vendor marketing claims, synthetic prompt vanity benchmarks, or front-door documentation; we deploy live, autonomous AI coding agents to measure real execution friction, token bleed, and runtime gotchas.

---

## Published Benchmark Editions

| Edition | Title | Scope | Date | Deliverables |
|---|---|---|---|---|
| **Edition 2 (Latest)** | [**The Glintbase Integration Index: Sandboxes Edition 1**](benchmarks/sandboxes-edition-1) | 5 Cloud Sandboxes (Modal, E2B, boat.dev, Vercel, Daytona) | October 2026 | 30 Live Agent Trials • 119 Scans • 5 Figures • Gotchas Dossier |
| **Edition 1** | [**State of Agent Readiness 2026 (ARS 2026)**](benchmarks/state-of-agent-readiness-2026) | Global Audit of 100 Developer Platforms across 10 Cohorts | August 2026 | 24-Page PDF • 1,000 Pathfinder Scans • 450 Agent Runs • $433k Token Tax |

---

## Repository Structure

```
glintbase-research/
├── README.md                                # Canonical research index and reproduction guide
├── LICENSE                                  # Apache 2.0 License
├── CITATION.cff                             # Machine-readable citation metadata
├── .gitignore
│
└── benchmarks/
    ├── sandboxes-edition-1/                 # The Glintbase Integration Index: Cloud Sandboxes
    │   ├── README.md                        # Summary, leaderboard table, and reproduction steps
    │   ├── .env.example                     # Environment key template (zero secrets)
    │   │
    │   ├── reports/
    │   │   ├── REPORT_SANDBOXES_EDITION_1.md# Canonical publication whitepaper
    │   │   ├── METHODOLOGY.md               # Mathematical formulation of Integration Tax (IT)
    │   │   └── GOTCHAS_AND_TRAPS.md         # Runtime trap stack traces and workarounds
    │   │
    │   ├── data/
    │   │   ├── benchmark_master.json        # Canonical 30-trial results with tokens & steps
    │   │   ├── benchmark_master.csv         # Tabular dataset for pandas / R / spreadsheet analysis
    │   │   ├── integration_tax_summary.json # Aggregated median and total metrics per provider
    │   │   └── phase1-scans/                # Raw machine scanner outputs (modal, e2b, etc.)
    │   │
    │   ├── visuals/                         # High-resolution Anthropic-styled figures
    │   │   ├── visual1_master_leaderboard_table.png
    │   │   ├── visual2_frontdoor_vs_reality_scatter.png
    │   │   ├── visual3_challenge_progression_linegraph.png
    │   │   ├── visual4_integration_tax_leaderboard.png
    │   │   └── visual5_provider_challenge_heatmap.png
    │   │
    │   ├── harness/                         # Evaluation scripts & runner templates
    │   │   ├── calculate_tax.py             # Computes Integration Tax from run logs
    │   │   ├── generate_visuals.py          # Generates publication graphics with embedded badges
    │   │   ├── templates/                   # Standardized prompt instructions for trials 1-6
    │   │   └── solutions/                   # Per-provider trial solutions (Modal, E2B, boat, etc.)
    │   │
    │   └── distribution/
    │       └── DISTRIBUTION_KIT_3DAY_LAUNCH.md # Launch sequences, thread copy, and carousel script
    │
    └── state-of-agent-readiness-2026/       # Foundational 100-Platform Ecosystem Audit
        ├── README.md                        # Abstract, cohort breakdown, and findings
        ├── reports/
        │   └── STATE_OF_AGENT_READINESS_2026.pdf # Full 24-page PDF whitepaper (1.1 MB)
        └── data/
            ├── full-scores.csv              # 100 Platforms × 10 Benchmarks score matrix
            └── research-dataset.json        # Deep metadata and traversal logs for all 100 platforms
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
print(df.groupby("platform")[["total_tokens", "steps_count", "wall_time_seconds"]].median())
```

### 3. Recalculate Integration Tax ($IT$)

```bash
python harness/calculate_tax.py
```

### 4. Regenerate Visuals

```bash
python harness/generate_visuals.py
```

All 5 publication graphics will be rendered directly to `visuals/`.

---

## The Integration Tax Formula

$$\text{Integration Tax (IT)} = \left[ 0.40 \times \left(\frac{\text{Tokens}_{\text{med}}}{\text{Min Tokens}}\right) + 0.40 \times \left(\frac{\text{Steps}_{\text{med}}}{\text{Min Steps}}\right) + 0.20 \times \left(\frac{\text{Time}_{\text{med}}}{\text{Min Time}}\right) \right] \times \text{Penalty}$$

- **Minima Baseline**:
  - $\text{Min Tokens} = 1,865$ (E2B)
  - $\text{Min Steps} = 3.0$ (Modal & boat.dev)
  - $\text{Min Time} = 19.5\text{s}$ (Modal)
- **Penalty Multiplier**:
  $$\text{Penalty} = 1.0 + \frac{100 - \text{Pass Rate}}{50} \quad (\text{when Pass Rate } < 100\%)$$

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
  note = {N=100 platforms, 1,000 Pathfinder scans, 450 live harness evaluations}
}
```

---

## License & Ethics Statement

- **Code & Harnesses**: Licensed under [Apache License 2.0](LICENSE).
- **Benchmark Datasets & Reports**: Licensed under [Creative Commons Attribution 4.0 International (CC-BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
- **Independence Disclosure**: Glintbase maintains zero affiliate compensation or preferential ranking deals with any evaluated infrastructure vendor. All evaluation trials are conducted in deterministic, isolated environments using standard customer tiers.

For questions, corrections, or vendor re-scan requests, reach out to **research@glintbase.dev** or open an issue.
