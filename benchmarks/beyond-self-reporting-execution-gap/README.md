# Beyond Self-Reporting: Claimed vs. Verified Completion in Integration Tasks

> **Status**: **Paused** (2026-10-12) at design stage, pending budget for ~900 agent runs. No data has been collected and no results exist.
> **Authors**: Glintbase Research

---

## Background

WebPageBench (Emelyanov et al., arXiv:2609.35026) verifies web-agent tasks from instrumented event logs. On its leaderboard of 24 model–harness pairs, the gap between what agents declare finished and what the log confirms **reaches** 41 points; one configuration declared every task finished while satisfying the conditions on 59%. That is the largest gap observed, not an average.

## Research Question

Does a comparable claimed-vs-verified gap appear in **developer integration work** (calling APIs, handling webhooks, mutating databases), how large is it per model and harness, and what failure modes produce it?

## Design (summary)

| Element | Plan |
|---|---|
| Testbed | Instrumented mock services (REST API, webhook receiver, database) that log every request and state change |
| Tasks | ~50 integration tasks with machine-checkable success conditions, written and frozen before any run |
| Agents | Current frontier models (e.g. Claude Opus 5.5 / Sonnet 5.5, current GPT and Gemini releases) in at least two harnesses |
| Repetitions | 3 per task per configuration |
| Primary outcome | Claimed completion rate − verified completion rate, per configuration, with 95% CIs |
| Failure taxonomy | Coded by two independent raters from transcripts + event logs; agreement reported (Cohen's κ) |

The size of the gap depends heavily on testbed design, so task specs, error behaviours, and success conditions are published alongside the results.

## Directory Layout (populated as the study runs)

- `harness/` — testbed services, task specs, runner, verifiers
- `data/` — per-run claimed vs. verified outcomes, coded failure modes
- `reports/` — whitepaper (written only after analysis)
