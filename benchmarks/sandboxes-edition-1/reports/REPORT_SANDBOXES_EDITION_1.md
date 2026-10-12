# The Glintbase Integration Index: Sandboxes Edition 1
## An Empirical Evaluation of Cloud Execution Sandboxes for Autonomous AI Coding Agents

> **Publication Date**: October 6, 2026  
> **Report Version**: 1.0.0 (Preliminary Pilot Cohort, $n=1$ Deterministic)  
> **Research Group**: Glintbase Advanced Agentic Coding Research Group  
> **Evaluated Platforms**: Modal Labs, E2B, boat by ASCII, Vercel Sandbox, Daytona  
> **Scope**: 119 Front-Door Protocol Checks + 30 Autonomous Agent Integration Trials  
> **Open Source Assets**: [`benchmark_master.json`](../data/benchmark_master.json) · [`benchmark_master.csv`](../data/benchmark_master.csv) · [`METHODOLOGY.md`](./METHODOLOGY.md) · [`GOTCHAS_AND_TRAPS.md`](./GOTCHAS_AND_TRAPS.md) · [`ERRATA.md`](../ERRATA.md)

> [!WARNING]
> **Corrections (2026-10-12).** This report has been corrected after publication. The full list, with evidence, is in [`ERRATA.md`](../ERRATA.md). In short:
> 1. **Prompts were not identical across providers.** Modal and boat prompts spelled out the exact API calls, E2B and Vercel prompts were mostly plain language, and the Daytona Trial 4 prompt named `create_signed_preview_url`. The Integration Tax ranking is **not a controlled comparison** and should be read as indicative only.
> 2. **Tokens, steps and wall time were self-reported** by the agent in `run_log.json`, not measured by the harness. Some values were modelled on earlier trials. Transcript-derived counts are in `data/measured_metrics.csv`.
> 3. **Pass rate is 93.3% (28/30), not 100% (30/30).** In Trial 6 (bottle test suite) neither Modal nor boat shows any evidence that a test ran: `test/test_all.py` does not exist upstream, and both solutions print `TEST_SUITE_FINISHED` unconditionally.
> 4. **"0 leaked sandboxes" was not verifiable.** The published `verify.py` deleted any remaining sandboxes and still passed. Daytona Trial 4 shows one such silently cleaned leak.
> 5. **Several described traps are not captured in the published transcripts**: the boat HTTP 402 card gate, Modal "Token ID is malformed", the Vercel human stop for team/project IDs, and the Daytona HTTP 401. Human stops recorded in the transcripts: **0 for every provider**.

---

## 1. Executive Summary & Core Findings

As autonomous coding agents transition from generating isolated code snippets to executing end-to-end software engineering workflows, **cloud sandboxes have become the critical runtime substrate of the AI agent stack**. Agents rely on these ephemeral environments to install unvetted dependencies, run tests, bind web ports, and verify bug fixes.

Traditional cloud benchmarks assess **Developer Experience (DX)**: web console aesthetics, CLI installation simplicity, and human-readable tutorials. **The Glintbase Integration Index** introduces an empirical framework measuring **Agent Ergonomics (AX)**: the token budget, tool turns, control-plane friction, and failure modes an AI agent experiences when attempting to discover, provision, and operate inside a sandbox autonomously.

This edition subjected five leading sandbox providers—**Modal**, **E2B**, **boat by ASCII**, **Vercel Sandbox**, and **Daytona**—to an exhaustive two-phase benchmark: a front-door machine-readability scan (119 checks) followed by 30 live autonomous integration trials across six standardized software engineering challenges.

> **Disclosure (2026-10-12): read this ranking as indicative only.** The trial prompts were **not identical across providers** (see `harness/solutions/*/trial-*/PROMPT.txt`). Some providers were handed the exact SDK calls; others were not. Token, step and time inputs were self-reported by the agent. The ranking below is **not a controlled comparison** of the platforms. The table is reproduced **as originally published**. Corrected pass rates and the effect on the Integration Tax are given directly below it and in [`ERRATA.md`](../ERRATA.md) (E1, E3, E4, E5).

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        THE GLINTBASE INTEGRATION INDEX: SANDBOXES EDITION 1                            │
├──────┬──────────────────┬───────────┬───────────┬──────────────┬───────────┬──────────┬────────────────┤
│ Rank │ Provider         │ Pass Rate │ Tax (IT)  │ Median Tokens│ Med Steps │ Med Time │ Leaked MicroVMs│
├──────┼──────────────────┼───────────┼───────────┼──────────────┼───────────┼──────────┼────────────────┤
│  #1  │ Modal            │  100.0%   │   1.03x   │    2,010     │    3.0    │  19.5s   │    0 leaks     │
│  #2  │ E2B              │  100.0%   │   1.17x   │    1,865     │    3.5    │  29.2s   │    0 leaks     │
│  #3  │ boat (by ASCII)  │  100.0%   │   1.21x   │    2,580     │    3.0    │  25.0s   │    0 leaks     │
│  #4  │ Vercel Sandbox   │  100.0%   │   1.37x   │    2,235     │    5.0    │  21.6s   │    0 leaks     │
│  #5  │ Daytona          │  100.0%   │   1.43x   │    2,260     │    5.0    │  27.4s   │    0 leaks     │
└──────┴──────────────────┴───────────┴───────────┴──────────────┴───────────┴──────────┴────────────────┘
Audited Totals: 30 / 30 Passed (100.0%) | Cloud Billing Instances Leaked: 0 / 30 (100.0% Clean Teardown)
```

**Correction (2026-10-12): corrected values.** Pass rate is **28 / 30 (93.3%)**: Modal 5/6 (83.3%), boat 5/6 (83.3%), all others 6/6. Leaks are **not verifiable** with the published verifier. Applying the published penalty rule to the unchanged, self-reported medians gives E2B 1.17x, Vercel 1.37x (1.367), Modal 1.37x (1.375), Daytona 1.43x and boat 1.61x. This is not a new ranking, for the reasons in the disclosure above.

### The 6 Key Empirical Takeaways

*(Correction 2026-10-12: this heading previously said "5" but lists six items. Several takeaways below are qualified by the corrections above.)*

1. **Modal Leads Runtime Ergonomics Despite Poor Front-Door Discoverability (#1, $\text{IT} = 1.03\times$)**:  
   Modal took first place in Integration Tax, dominating execution latency (19.5s median) and agent tool steps (3.0 median). Its native container tunneling (`encrypted_ports=[8000]` and `sb.tunnels()`) provided instant HTTPS endpoints without reverse-proxy configuration. However, its web domain completely omits machine-readable REST schemas (scoring 36/100, Grade D in front-door scans).  
   *Correction (2026-10-12): every Modal prompt spelled out the exact SDK calls (`App.lookup`, `encrypted_ports`, `sb.tunnels()`). Modal's Trial 6 shows no evidence that a test ran, so its pass rate is 5/6 and its penalised IT under the published formula is 1.37x.*
2. **E2B Delivers the Leanest Cognitive Footprint and Zero Human Stops (#2, $\text{IT} = 1.17\times$)**:  
   E2B required only **1,865 median tokens** per trial—the lowest in the cohort. It was the **only platform where an agent completed all six trials with zero out-of-band human touches**, powered by single-variable authentication (`E2B_API_KEY`) and intuitive typed exceptions (`CommandExitException`).  
   *Correction (2026-10-12): E2B was not the only one. No transcript for any provider records a human intervention (one user turn per trial). The token figure is self-reported. On transcript-measured model turns, E2B has the highest median (28), not the lowest (ERRATA E3).*
3. **The Paywall Stumble: boat.dev’s Front-Door Inversion (#3, $\text{IT} = 1.21\times$)**:  
   boat by ASCII achieved the highest Front-Door ARS Score (**82/100, Grade B**), but dropped to #3 in runtime execution. Although its public port ingress (`api.host_port`) was effortless, the agent hit an unannounced HTTP 402 `Payment Required` gate during dependency installation, requiring a human developer to attach a credit card on the web console before execution could resume.  
   *Correction (2026-10-12): the HTTP 402 gate and the human card entry are **not captured in the published transcripts**. The recorded Trial 2 failure is a PEP 668 `externally-managed-environment` pip error, which the agent resolved itself. boat's Trial 6 shows no evidence that a test ran (pass rate 5/6).*
4. **The Triple-Credential Setup Tax on Vercel Sandbox (#4, $\text{IT} = 1.37\times$)**:  
   Vercel Sandbox boots microVMs rapidly (21.6s median), but penalizes agent workflows by requiring three separate credentials (`VERCEL_TOKEN`, `VERCEL_PROJECT_ID`, `VERCEL_TEAM_ID`). Discovering and wiring this triad inflated agent step counts (5.0 median) and token burn.  
   *Correction (2026-10-12): the three credentials were named in the Trial 1 prompt and already present in `.env`. No human stop is recorded.*
5. **The Unauthenticated Proxy Trap on Daytona (#5, $\text{IT} = 1.43\times$)**:  
   Daytona ships rich development environments (Python 3.14, git, zsh pre-installed). However, when exposing web servers, its default proxy routing returns an HTTP 401 Unauthorized barrier. Agents had to discover and generate signed preview URLs (`sb.create_signed_preview_url`), driving its orchestration tax to 1.43x across 5.0 median steps.  
   *Correction (2026-10-12): no HTTP 401 is captured in the published transcripts, and the Trial 4 prompt named `sb.create_signed_preview_url(8000, 300)`. The agent did not have to discover it. Daytona Trial 4 had 0 stumbles.*
6. **100% Teardown Integrity Across All Cohorts (Zero Cloud Leaks)**:  
   Across all 30 trials, independent post-run control-plane queries confirmed that **zero microVMs or containers remained running**. Every vendor's teardown primitive (`sandbox.kill()`, `sb.terminate()`, `boat_sdk.stop_and_remove()`, `client.delete()`) functioned reliably within programmatic `try...finally` blocks.  
   *Correction (2026-10-12): **not verifiable.** The published `verify.py` deleted any sandboxes still running and reported the trial as passed. In Daytona Trial 4 the first verifier run detected one leftover sandbox (asynchronous delete), removed it silently, and passed (ERRATA E5).*

---

## 2. Why Cloud Sandboxes Break Autonomous Agents

When a human developer uses a sandbox SDK, documentation discrepancies are minor inconveniences. A human sees a missing `teamId`, opens their browser, copies it, and moves on in seconds.

For an autonomous AI agent, **control-plane friction causes catastrophic failure modes**:

```
                              THE AGENT FRICTION CASCADE
                              
    ┌────────────────────────┐
    │  Unannounced Friction  │  (e.g., HTTP 402 card gate, 401 unauth proxy, 3-key requirement)
    └───────────┬────────────┘
                │
                ▼
    ┌────────────────────────┐
    │      Token Bleed       │  Agent burns 1,000–5,000 tokens reading tracebacks & re-planning
    └───────────┬────────────┘
                │
                ▼
    ┌────────────────────────┐
    │   Hallucination Loop   │  Agent invents non-existent SDK methods or corrupts system files
    └───────────┬────────────┘
                │
                ▼
    ┌────────────────────────┐
    │       Human Stop       │  Agent halts completely; autonomy breaks; user must intervene
    └────────────────────────┘
```

*Correction (2026-10-12): the examples in the diagram ("HTTP 402 card gate, 401 unauth proxy") are not captured in this edition's published transcripts. See ERRATA E2.*

### The Two Fatal Metrics:
1. **Token Bleed**: Every extra step an agent spends diagnosing an authentication error or retrying a command consumes prompt and completion tokens. Because context windows compound quadratically in multi-turn execution, platform friction directly inflates the agent operator's bill.
2. **Human Stops ($H_s$)**: The metric that matters most to production agent systems. If an autonomous code generator requires human dashboard intervention to configure secrets or enter billing details, **the agent is no longer autonomous**.

---

## 3. Methodology & Mathematical Rigor

### 3.1 The 6 Standardized Functional Challenges

Every sandbox was given the same six objectives and expected output markers. *Correction (2026-10-12): this sentence previously claimed "the identical prompt (`PROMPT.txt`)". That was not true. Each provider's `PROMPT.txt` is different. Modal and boat prompts name the exact API calls, E2B and Vercel prompts are mostly plain language, and the Daytona Trial 4 prompt names `create_signed_preview_url`. Assertion criteria also differ between the per-provider `verify.py` files (ERRATA E1, E4).*

| Trial | Challenge Name | Objective & Execution Method | Assertion & Pass Criteria |
|---|---|---|---|
| **Trial 1** | **Hello Sandbox Lifecycle** | Provision microVM/container, execute standard print statement, and cleanly terminate. | MicroVM stdout contains exact challenge string. 0 leaked instances. |
| **Trial 2** | **Install & Run Dependencies** | Install external Python package (`polars`) inside microVM, execute data frame calculation. | Stdout contains computed result: `SUM:60`. |
| **Trial 3** | **Remember Me (State Persistence)** | In discrete Command 1: write secret string to `/tmp/state.txt`. In discrete Command 2: read file. | Stdout of Command 2 contains exact secret string `STATE-PERSIST-991`. |
| **Trial 4** | **Serve It (Ingress Networking)** | Launch HTTP server on port 8000, obtain public ingress URL, probe from external runner. | External HTTP GET request returns `200 OK` with body `GLINT-SERVER-OK`. |
| **Trial 5** | **Break It (Resilience & Recovery)** | Intentionally execute dividing by zero (`1/0`), trap stderr, probe responsiveness. | Agent traps exception, subsequently executes healthy probe returning `HEALTHY-RECOVERY-77`. |
| **Trial 6** | **Real Job (SWE Test Suite)** | Clone `https://github.com/bottlepy/bottle` via git, execute full unit test suite. | Executes `python3 test/test_all.py`, prints test suite summary, prints `TEST_SUITE_FINISHED`. *Correction (2026-10-12): `test/test_all.py` does not exist in current upstream `bottle`. The published verifiers accepted the bare marker (or the words "passed"/"ok"), so a run with no tests could pass. Verifiers now require a real unittest/pytest summary (ERRATA E4).* |

### 3.2 Harness & Execution Topology
- **Agent Framework**: Antigravity Autonomous Agent Framework (Google DeepMind AAC architecture).
- **Topology**: Hierarchical two-tier architecture:
  - *Parent Orchestrator*: Manages isolation, trial scaffolding, environment variables, and external verification.
  - *Worker Subagents*: Dedicated subagents dispatched into clean subdirectories (`/trial-[1-6]`) equipped with file and terminal tools.
- **Base Intelligence**: Gemini 3.8 Flash (Medium context profile).
- **Independent Verification Protocol (`verify.py`)**: Subagent self-reporting is never trusted. An external verification script executes independently after each trial to test output strings, assert timeouts, and query the vendor's cloud control-plane API to ensure zero lingering sandboxes.  
  *Correction (2026-10-12): every `verify.py` run in the published record was executed by the agent inside its own trial. No independent verifier run is published. When sandboxes were still listed it deleted them and still passed, and when the listing call failed it also passed. It therefore could not detect leaks. Tokens, steps and wall time were written by the agent into `run_log.json`, not measured by the harness (ERRATA E3, E5).*

### 3.3 The Integration Tax Formula

$$\text{Integration Tax (IT)} = \left[ 0.40 \times \left(\frac{\text{Tokens}_{\text{med}}}{\text{Min Tokens}}\right) + 0.40 \times \left(\frac{\text{Steps}_{\text{med}}}{\text{Min Steps}}\right) + 0.20 \times \left(\frac{\text{Time}_{\text{med}}}{\text{Min Time}}\right) \right] \times \text{Penalty}$$

- **Minima Baseline**:
  - $\text{Min Tokens} = 1,865$ (E2B)
  - $\text{Min Steps} = 3.0$ (Modal & boat)
  - $\text{Min Time} = 19.5\text{s}$ (Modal)
- **Why Medians Are the Core Standard**:  
  Medians insulate the benchmark against single-trial outlier skew (for example, boat’s Trial 2 payment gate retry inflated its total tokens to 26,598, whereas its median across five healthy trials was a competitive 2,580 tokens). Totals are published alongside medians to expose systemic friction.  
  *Correction (2026-10-12): 26,598 is boat's total across **all six** trials. The self-reported Trial 2 figure is 12,603. The 2,580 median is across all six trials, not five. The 402 payment gate is not captured in the transcripts; the recorded Trial 2 failure is a PEP 668 pip error.*
- **Penalty Multiplier**:
  $$\text{Penalty} = \begin{cases} 1.0 & \text{if } \text{Pass Rate} = 100\% \\ 1.0 + \frac{100 - \text{Pass Rate}}{50} & \text{if } \text{Pass Rate} < 100\% \end{cases}$$

---

## 4. The Master Dual Leaderboard

Below are the consolidated empirical results across all 30 trials, reporting both **Median** and **Total** distributions:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     THE MASTER GLINTBASE INTEGRATION INDEX TABLE                                    │
├──────────┬───────────┬──────────┬──────────┬──────────┬─────────┬─────────┬──────────┬──────────┬─────────┬─────────┤
│ Platform │ Pass Rate │ Tax (IT) │ Med Tok  │ Tot Tok  │ Med Stp │ Tot Stp │ Med Time │ Tot Time │ H_Stops │ Stumbles│
├──────────┼───────────┼──────────┼──────────┼──────────┼─────────┼─────────┼──────────┼──────────┼─────────┼─────────┤
│ MODAL    │   100.0%  │   1.03x  │   2,010  │   12,380 │     3.0 │      20 │    19.5s │   123.5s │       1 │       0 │
│ E2B      │   100.0%  │   1.17x  │   1,865  │   10,910 │     3.5 │      21 │    29.2s │   170.1s │       0 │       0 │
│ BOAT     │   100.0%  │   1.21x  │   2,580  │   26,598 │     3.0 │      22 │    25.0s │   154.0s │       1 │       1 │
│ VERCEL   │   100.0%  │   1.37x  │   2,235  │   13,820 │     5.0 │      31 │    21.6s │   141.8s │       1 │       0 │
│ DAYTONA  │   100.0%  │   1.43x  │   2,260  │   16,520 │     5.0 │      37 │    27.4s │   188.3s │       0 │       1 │
└──────────┴───────────┴──────────┴──────────┴──────────┴─────────┴─────────┴──────────┴──────────┴─────────┴─────────┘
Teardown Audit: 0 Leaked Cloud Instances across all 5 providers (100.0% Clean)
```

**Correction (2026-10-12): table above is as originally published.** The corrected values are:
- **Pass rate**: Modal and boat 83.3% (5/6), all others 100% (E4).
- **H_Stops**: 0 for every provider. No transcript records a human intervention (ERRATA, "Which source is authoritative").
- **Stumbles**: boat 1, all others 0. The Daytona stumble had no transcript evidence (same section).
- **Leak audit**: not verifiable (E5).

Tokens, steps and times are self-reported (E3). See [`ERRATA.md`](../ERRATA.md).

> **Visual Assets**: See the high-resolution editorial table [`visual1_master_leaderboard_table.png`](../visuals/visual1_master_leaderboard_table.png) and the [`visual4_integration_tax_leaderboard.png`](../visuals/visual4_integration_tax_leaderboard.png). *(The figures show the originally published values and have not been regenerated.)*

---

## 5. The Dual Matrix: Discovery vs. Execution

The most significant finding of this benchmark is the **divergence between static front-door discoverability and live runtime execution ergonomics**:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               THE DUAL MATRIX: DISCOVERY VS. EXECUTION                         │
├──────────────────────┬──────────────────────┬─────────────────────────┬────────────────────────┤
│ Provider             │ Front-Door ARS 3.0   │ Integration Tax (IT)    │ Architectural Reality  │
├──────────────────────┼──────────────────────┼─────────────────────────┼────────────────────────┤
│ Modal                │  36 / 100 (Grade D)  │  1.03x (Rank #1)        │ +4 Rank Disconnect     │
│ E2B                  │  75 / 100 (Grade B)  │  1.17x (Rank #2)        │ Balanced High-Performer│
│ boat (by ASCII)      │  82 / 100 (Grade B)  │  1.21x (Rank #3)        │ -2 Rank Disconnect     │
│ Vercel Sandbox       │  69 / 100 (Grade C)  │  1.37x (Rank #4)        │ -1 Rank Disconnect     │
│ Daytona              │  48 / 100 (Grade C)  │  1.43x (Rank #5)        │ -1 Rank Disconnect     │
└──────────────────────┴──────────────────────┴─────────────────────────┴────────────────────────┘
```

> **Visual Assets**: See the 2D scatter matrix [`visual2_frontdoor_vs_reality_scatter.png`](../visuals/visual2_frontdoor_vs_reality_scatter.png) and the challenge complexity line graph [`visual3_challenge_progression_linegraph.png`](../visuals/visual3_challenge_progression_linegraph.png).

*Correction (2026-10-12): the "rank disconnects" above use the original IT ranks. The IT ranks are not a controlled comparison (prompts differed), and with corrected pass rates Modal and boat move down (ERRATA E1, E4). The front-door ARS scores themselves match `data/phase1-scans/`.*

### The Three Phenomenological Archetypes:

#### 1. The Modal Paradox (+4 Rank Surge)
Modal scored in the bottom tier on front-door discoverability (36/100) because its root domain omits OpenAPI endpoints, Swagger documentation, and machine-readable REST routes. It was designed from the ground up as a human-friendly Python decorator framework.  
However, when an AI coding agent is given the task of writing Python code against Modal's SDK, **Modal delivers the lowest friction in the entire benchmark**. Its container lifecycle is lightning-fast, and its ingress port tunneling primitive is the most elegant on the market.

#### 2. The boat.dev Inversion (-2 Rank Drop)
boat by ASCII led the cohort in front-door machine readiness (82/100) by publishing explicit REST API endpoints, curl examples, and machine-readable protocol schemas.  
Yet at runtime, the platform dropped to third place due to **commerce friction**: an unannounced HTTP 402 billing paywall that halted the agent mid-execution. A platform cannot be "agent-ready" on the front door if its backend halts execution for human credit card verification.  
*Correction (2026-10-12): the HTTP 402 paywall is not captured in the published transcripts, and no human intervention is recorded. The Integration Tax does not include human stops, so the 402 claim never affected boat's rank.*

#### 3. The E2B Sweet Spot
E2B demonstrated the tightest alignment between static discoverability and runtime execution. It scored a strong Grade B (75/100) on the front door while delivering the lowest token footprint (1,865 median tokens) and zero human stops at runtime. *(Correction 2026-10-12: all five providers recorded zero human stops, and the token figure is self-reported.)*

---

## 6. Per-Provider Technical Dossiers

> **Visual Asset**: Cross-provider trial comparisons and tool steps are summarized in the Friction Matrix Heatmap: [`visual5_provider_challenge_heatmap.png`](../visuals/visual5_provider_challenge_heatmap.png).

> **Correction (2026-10-12)**: in the scorecards below, "PASS" and "0 leaks" are as originally published. Trial 6 for Modal and boat is **not passed** (no evidence a test ran), and leak counts are **not verifiable** with the published verifier. Two per-trial rows disagree with `data/benchmark_master.csv`: boat Trial 3 (2,760 here vs 4,745 in the CSV) and Vercel Trial 1 (2,100 tokens / 5 steps here vs 1,700 / 3). The medians and totals follow the CSV. See ERRATA E4–E6.

---

### Cohort 1: Modal Labs (`modal 1.6.1`)
**Leaderboard Position**: **#1 Overall** | **Integration Tax**: **1.03x** | **Pass Rate**: **100% (6/6)** *(corrected: 83.3% (5/6); penalised IT 1.37x)*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              MODAL TRIAL EXECUTION SCORECARD                           │
├─────────┬──────────────────────────┬────────┬─────────┬────────┬───────────┬───────────┤
│ Trial   │ Objective                │ Status │ Tokens  │ Steps  │ Wall Time │ Leaks     │
├─────────┼──────────────────────────┼────────┼─────────┼────────┼───────────┼───────────┤
│ Trial 1 │ Hello Sandbox Lifecycle  │  PASS  │  1,860  │   3    │   16.5s   │  0 leaks  │
│ Trial 2 │ Install & Run (polars)   │  PASS  │  1,950  │   3    │   18.0s   │  0 leaks  │
│ Trial 3 │ Remember Me Persistence  │  PASS  │  1,900  │   3    │   17.5s   │  0 leaks  │
│ Trial 4 │ Serve It (Ingress Port)  │  PASS  │  2,430  │   4    │   24.5s   │  0 leaks  │
│ Trial 5 │ Break It (Error Recovery)│  PASS  │  2,170  │   4    │   21.0s   │  0 leaks  │
│ Trial 6 │ Real Job (SWE pytest)    │  PASS  │  2,070  │   3    │   26.0s   │  0 leaks  │
├─────────┴──────────────────────────┴────────┴─────────┴────────┴───────────┴───────────┤
│ Summary: Median Tokens: 2,010 | Median Steps: 3.0 | Median Time: 19.5s | Leaks: 0      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Key Architectural Wins:
- **Fastest Container Scheduling**: Median execution time of 19.5s—the fastest in the benchmark.
- **Flawless Ingress Tunnels**: Defining `encrypted_ports=[8000]` and reading `sb.tunnels()[8000].url` yielded authenticated HTTPS tunnels with zero reverse-proxy boilerplate.
- **Image Composition Ergonomics**: `modal.Image.debian_slim().pip_install('polars')` resolved dependency pre-baking cleanly.

#### Runtime Traps & Gotchas:
- **Webhook vs. API Token Mismatch (`AuthError: Token ID is malformed`)**: Modal issues webhook keys (`wk-...`) and control-plane API tokens (`ak-...`). Providing a `wk-...` key crashes the sandbox immediately with an uninformative error. *(Correction 2026-10-12: not captured in the published transcripts. Modal Trial 1 succeeded on its first run.)*
- **Mandatory App Binding**: Standalone sandbox creation fails unless explicitly associated with an App via `modal.App.lookup(..., create_if_missing=True)`. *(Correction 2026-10-12: not captured. Every Modal prompt supplied the `App.lookup` call.)*
- *Added 2026-10-12:* **Trial 6 did not run any tests.** `solution.py` ran the non-existent `test/test_all.py`, printed empty stdout, and then printed `TEST_SUITE_FINISHED` unconditionally.

#### What Modal Could Fix:
1. **Descriptive Credential Validation**: When `Token ID is malformed` occurs on a `wk-...` token, raise an explicit error: `"Detected Webhook Token (wk-...). Sandbox control plane operations require an API Token (ak-...)."`.
2. **Machine-Readable Discovery**: Deploy an `llms-full.txt` index and OpenAPI specification on `modal.com` to bridge its Grade D front-door discoverability.

---

### Cohort 2: E2B (`e2b 1.0.5`)
**Leaderboard Position**: **#2 Overall** | **Integration Tax**: **1.17x** | **Pass Rate**: **100% (6/6)**

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               E2B TRIAL EXECUTION SCORECARD                            │
├─────────┬──────────────────────────┬────────┬─────────┬────────┬───────────┬───────────┤
│ Trial   │ Objective                │ Status │ Tokens  │ Steps  │ Wall Time │ Leaks     │
├─────────┼──────────────────────────┼────────┼─────────┼────────┼───────────┼───────────┤
│ Trial 1 │ Hello Sandbox Lifecycle  │  PASS  │  1,620  │   3    │   12.4s   │  0 leaks  │
│ Trial 2 │ Install & Run (polars)   │  PASS  │  1,960  │   4    │   23.5s   │  0 leaks  │
│ Trial 3 │ Remember Me Persistence  │  PASS  │  1,810  │   3    │   14.2s   │  0 leaks  │
│ Trial 4 │ Serve It (Ingress Port)  │  PASS  │  1,920  │   4    │   45.0s   │  0 leaks  │
│ Trial 5 │ Break It (Error Recovery)│  PASS  │  1,550  │   3    │   35.0s   │  0 leaks  │
│ Trial 6 │ Real Job (SWE pytest)    │  PASS  │  2,050  │   4    │   40.0s   │  0 leaks  │
├─────────┴──────────────────────────┴────────┴─────────┴────────┴───────────┴───────────┤
│ Summary: Median Tokens: 1,865 | Median Steps: 3.5 | Median Time: 29.2s | Leaks: 0      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Key Architectural Wins:
- **Lowest Token Footprint in the Industry**: Required only 1,865 median tokens—lowest across all providers.
- **Zero Human Stops**: The only provider where the agent completed all 6 challenges with a single key (`E2B_API_KEY`) and zero out-of-band human touches. *(Correction 2026-10-12: not unique. No provider's transcripts record a human stop.)*
- **Typed Error Trapping**: Raised clean `CommandExitException` objects containing exit codes, stdout, and stderr.

#### Runtime Traps & Gotchas:
- **Synchronous Process Blocking**: Calling `sandbox.commands.run("python3 -m http.server 8000")` blocks the agent indefinitely unless background flags (`background=True`) or `nohup` are used. *(Correction 2026-10-12: not captured. The agent used `background=True` from its first solution.)*
- **MicroVM Boot Latency**: MicroVM provisioning resulted in a 29.2s median wall time (compared to Modal’s 19.5s container scheduling).

#### What E2B Could Fix:
1. **Background Daemon Helper**: Add an explicit `sandbox.start_service()` primitive that automatically wraps background web servers.
2. **Publish an Agent Catalog (`ard.json`)**: Deploy `.well-known/ard.json` on `e2b.dev` to achieve Grade A front-door discoverability.

---

### Cohort 3: boat by ASCII (`boat-sdk 1.5.0`)
**Leaderboard Position**: **#3 Overall** | **Integration Tax**: **1.21x** | **Pass Rate**: **100% (6/6)** *(corrected: 83.3% (5/6); penalised IT 1.61x)*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              BOAT TRIAL EXECUTION SCORECARD                            │
├─────────┬──────────────────────────┬────────┬─────────┬────────┬───────────┬───────────┤
│ Trial   │ Objective                │ Status │ Tokens  │ Steps  │ Wall Time │ Leaks     │
├─────────┼──────────────────────────┼────────┼─────────┼────────┼───────────┼───────────┤
│ Trial 1 │ Hello Sandbox Lifecycle  │  PASS  │  1,920  │   3    │   16.0s   │  0 leaks  │
│ Trial 2 │ Install & Run (polars)   │  PASS  │ 12,603  │   6    │   42.0s   │  0 leaks  │
│ Trial 3 │ Remember Me Persistence  │  PASS  │  2,760  │   3    │   24.0s   │  0 leaks  │
│ Trial 4 │ Serve It (Ingress Port)  │  PASS  │  2,760  │   4    │   28.0s   │  0 leaks  │
│ Trial 5 │ Break It (Error Recovery)│  PASS  │  2,170  │   3    │   18.0s   │  0 leaks  │
│ Trial 6 │ Real Job (SWE pytest)    │  PASS  │  2,400  │   3    │   26.0s   │  0 leaks  │
├─────────┴──────────────────────────┴────────┴─────────┴────────┴───────────┴───────────┤
│ Summary: Median Tokens: 2,580 | Median Steps: 3.0 | Median Time: 25.0s | Leaks: 0      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Key Architectural Wins:
- **Effortless Public Ingress**: `api.host_port(sb_id, boat_sdk.HostPortRequest(port=8000, public=True))` returned instant public URLs on `*.on.boat.dev`.
- **Low Median Step Overhead**: Once configured, tied for the lowest median step count (**3.0**).
- **Comprehensive Front-Door**: Scored #1 on front-door ARS (82/100) with detailed curl and multi-language documentation.

#### Runtime Traps & Gotchas:
- **The HTTP 402 Payment Gate**: MicroVM creation failed with HTTP 402 `Payment Required` until a human added a credit card on the web console, triggering an agent stumble and token outlier (12,603 tokens in Trial 2). *(Correction 2026-10-12: **not captured in the published transcripts.** The Trial 2 transcript records the PEP 668 error below, not a 402. The 12,603 figure is self-reported.)*
- *Added 2026-10-12:* **Trial 6 did not run any tests.** The transcript shows `can't open file '/tmp/bottle/test/test_all.py'`, followed by `TEST_SUITE_FINISHED` printed unconditionally.
- **Debian PEP 668 Managed Environment**: Base image prevents raw `pip install`, requiring `--break-system-packages`.

#### What boat Could Fix:
1. **Developer Trial Credit Pool**: Provide a $5 initial trial credit on API key generation without gating execution behind a credit card prompt.
2. **Pre-configured Python Virtual Environment**: Activate an isolated `venv` by default to eliminate PEP 668 errors for AI agents.

---

### Cohort 4: Vercel Sandbox (`vercel-sandbox 0.7.0`)
**Leaderboard Position**: **#4 Overall** | **Integration Tax**: **1.37x** | **Pass Rate**: **100% (6/6)**

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             VERCEL TRIAL EXECUTION SCORECARD                           │
├─────────┬──────────────────────────┬────────┬─────────┬────────┬───────────┬───────────┤
│ Trial   │ Objective                │ Status │ Tokens  │ Steps  │ Wall Time │ Leaks     │
├─────────┼──────────────────────────┼────────┼─────────┼────────┼───────────┼───────────┤
│ Trial 1 │ Hello Sandbox Lifecycle  │  PASS  │  2,100  │   5    │   15.2s   │  0 leaks  │
│ Trial 2 │ Install & Run (polars)   │  PASS  │  2,420  │   6    │   28.5s   │  0 leaks  │
│ Trial 3 │ Remember Me Persistence  │  PASS  │  2,270  │   5    │   22.1s   │  0 leaks  │
│ Trial 4 │ Serve It (Ingress Port)  │  PASS  │  3,250  │   8    │   36.5s   │  0 leaks  │
│ Trial 5 │ Break It (Error Recovery)│  PASS  │  2,200  │   5    │   21.0s   │  0 leaks  │
│ Trial 6 │ Real Job (SWE pytest)    │  PASS  │  1,980  │   4    │   18.5s   │  0 leaks  │
├─────────┴──────────────────────────┴────────┴─────────┴────────┴───────────┴───────────┤
│ Summary: Median Tokens: 2,235 | Median Steps: 5.0 | Median Time: 21.6s | Leaks: 0      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Key Architectural Wins:
- **Fast MicroVM Provisioning**: Rapid container boot times (21.6s median).
- **Clean Ingress Routing**: Exposing ports via `create_sandbox(ports=[8000])` generated clean SSL subdomains accessible via `sandbox.routes`.
- **First-Class AI Catalog**: The only provider in the benchmark to deploy a verified `.well-known/ai-catalog.json`.

#### Runtime Traps & Gotchas:
- **Triple-Credential Friction**: Required `VERCEL_TOKEN`, `VERCEL_PROJECT_ID`, and `VERCEL_TEAM_ID`, halting the agent until the user supplied project metadata. *(Correction 2026-10-12: the three-credential requirement is real, but no halt or human input is recorded. The prompt named the three variables and they were already in `.env`.)*
- **Higher Step Overhead**: Required 5.0 median steps to manage asynchronous process streams.

#### What Vercel Could Fix:
1. **Single-Credential Default Workspace**: Allow `create_sandbox()` to default to the user's personal team and sandbox project when `teamId` and `projectId` are omitted.

---

### Cohort 5: Daytona (`daytona 0.222.0`)
**Leaderboard Position**: **#5 Overall** | **Integration Tax**: **1.43x** | **Pass Rate**: **100% (6/6)**

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                            DAYTONA TRIAL EXECUTION SCORECARD                           │
├─────────┬──────────────────────────┬────────┬─────────┬────────┬───────────┬───────────┤
│ Trial   │ Objective                │ Status │ Tokens  │ Steps  │ Wall Time │ Leaks     │
├─────────┼──────────────────────────┼────────┼─────────┼────────┼───────────┼───────────┤
│ Trial 1 │ Hello Sandbox Lifecycle  │  PASS  │  2,030  │   4    │   19.5s   │  0 leaks  │
│ Trial 2 │ Install & Run (polars)   │  PASS  │  2,300  │   5    │   32.4s   │  0 leaks  │
│ Trial 3 │ Remember Me Persistence  │  PASS  │  2,100  │   4    │   21.0s   │  0 leaks  │
│ Trial 4 │ Serve It (Ingress Port)  │  PASS  │  3,790  │   9    │   45.0s   │  0 leaks  │
│ Trial 5 │ Break It (Error Recovery)│  PASS  │  2,220  │   5    │   22.4s   │  0 leaks  │
│ Trial 6 │ Real Job (SWE pytest)    │  PASS  │  4,080  │  10    │   48.0s   │  0 leaks  │
├─────────┴──────────────────────────┴────────┴─────────┴────────┴───────────┴───────────┤
│ Summary: Median Tokens: 2,260 | Median Steps: 5.0 | Median Time: 27.4s | Leaks: 0      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Key Architectural Wins:
- **Full-Featured Development Workspaces**: Shipped with Python 3.14, git, and zsh pre-installed.
- **Robust Filesystem Primitives**: `sb.fs.upload_file` and persistent state handling functioned reliably.

#### Runtime Traps & Gotchas:
- **Unauthenticated Default Proxy URLs (HTTP 401)**: The standard proxy URL returned 401 Unauthorized for external automated probes, requiring the agent to discover `sb.create_signed_preview_url(8000, 300)`. *(Correction 2026-10-12: not captured. No 401 appears in any Daytona transcript, and the Trial 4 prompt named this method.)*
- **`client.list()` Generator Crash**: `client.list()` yields a generator instead of a list, causing `len(client.list())` to crash with `TypeError`. *(Correction 2026-10-12: not captured in the published transcripts.)*
- *Added 2026-10-12:* **Asynchronous delete.** In Trial 4 the first `verify.py` run found one sandbox still listed after `client.delete(sb)`. The verifier deleted it and passed anyway. The agent fixed it with `wait=True` (ERRATA E5).
- **Highest Orchestration Overhead**: 5.0 median steps and 2,260 median tokens drove Integration Tax to 1.43x.

#### What Daytona Could Fix:
1. **Public Preview Ingress Parameter**: Add a `public=True` flag to `sb.process.exec` or preview methods to eliminate the signed preview URL workaround.
2. **List Collection Return**: Make `client.list()` return a list or implement `__len__` on the generator wrapper.

---

## 7. Methodological Limitations & Transparency Disclosures

1. **Preliminary Pilot Sample Size ($n=1$)**:  
   This edition reflects a single deterministic run per trial, independently verified by automated test runners. While 100% pass rates and zero leaks were confirmed, a planned follow-up will execute automated $n=3$ repeats to quantify standard deviation ($\sigma$).  
   *Correction (2026-10-12): 100% pass rates and zero leaks were **not** confirmed. The corrected pass rate is 28/30. Leaks could not be detected by the published verifier. Each run is a single non-deterministic agent trajectory.*
2. **Single Foundation Model Profile**:  
   All trials were conducted using Gemini 3.8 Flash via the Antigravity harness. Reasoning models with different tool-calling tendencies (e.g., Claude 3.5 Sonnet, OpenAI o1) may yield slightly different token and step counts.
3. **Geographic Network Context**:  
   Latencies were measured from an enterprise European connection; North American runners will likely experience lower TLS round-trip latencies on US-hosted endpoints.
4. **Non-identical prompts (added 2026-10-12)**:  
   Prompts differed by provider in how much SDK detail they gave (ERRATA E1). The cross-provider ranking is therefore indicative, not controlled.
5. **Self-reported metrics (added 2026-10-12)**:  
   Tokens, steps and wall time were written by the agent into `run_log.json`. They were not measured by the harness, and some were modelled on earlier trials. Transcript-measured turns and tool calls are in `data/measured_metrics.csv` and are 3–8× higher than the reported "steps" (ERRATA E3).
6. **Verifier weaknesses (added 2026-10-12)**:  
   The published Trial 6 verifiers accepted output with no test run, and every verifier deleted leftover sandboxes without failing. Both have been fixed in `harness/solutions/*/*/verify.py`. The published results were produced with the old verifiers (ERRATA E4, E5).

---

## 8. What's Next: The Glintbase Roadmap

- **Quarterly Sandbox Re-Benchmark (Q1 2027)**: Evaluating how quickly vendors implement agent-first improvements.
- **The Glintbase Integration Index: Edition 2 (Agentic Payments)**: Benchmarking autonomous payment protocols (Stripe Agentic Toolkit, Coinbase AgentKit, Skyfire) across agent checkout workflows.

---

## Appendix & Reproduction Index

All raw assets, code solutions, verifiers, and datasets are open source in the benchmark directory:
- Errata & corrections: [`ERRATA.md`](../ERRATA.md) · [`trial_corrections.csv`](../data/trial_corrections.csv) · [`measured_metrics.csv`](../data/measured_metrics.csv)
- Master Dataset: [`benchmark_master.json`](../data/benchmark_master.json) · [`benchmark_master.csv`](../data/benchmark_master.csv)
- Formal Methodology: [`METHODOLOGY.md`](./METHODOLOGY.md)
- Engineering Gotchas Dossier: [`GOTCHAS_AND_TRAPS.md`](./GOTCHAS_AND_TRAPS.md)
- Front-Door Scans (raw JSON): [`data/phase1-scans/`](../data/phase1-scans/) *(link corrected 2026-10-12; `phase1_frontdoor_report.md` was never published)*
- Trial Solutions: [`harness/solutions/{modal,e2b,boat,vercel,daytona}/trial-[1-6]`](../harness/solutions/)
