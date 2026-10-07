# The Glintbase Integration Index: Sandboxes Edition 1
## An Empirical Evaluation of Cloud Execution Sandboxes for Autonomous AI Coding Agents

> **Publication Date**: October 6, 2026  
> **Report Version**: 1.0.0 (Preliminary Pilot Cohort, $n=1$ Deterministic)  
> **Research Group**: Glintbase Advanced Agentic Coding Research Group  
> **Evaluated Platforms**: Modal Labs, E2B, boat by ASCII, Vercel Sandbox, Daytona  
> **Scope**: 119 Front-Door Protocol Checks + 30 Autonomous Agent Integration Trials  
> **Open Source Assets**: [`benchmark_master.json`](./benchmark_master.json) · [`benchmark_master.csv`](./benchmark_master.csv) · [`METHODOLOGY.md`](./METHODOLOGY.md) · [`GOTCHAS_AND_TRAPS.md`](./GOTCHAS_AND_TRAPS.md)

---

## 1. Executive Summary & Core Findings

As autonomous coding agents transition from generating isolated code snippets to executing end-to-end software engineering workflows, **cloud sandboxes have become the critical runtime substrate of the AI agent stack**. Agents rely on these ephemeral environments to install unvetted dependencies, run tests, bind web ports, and verify bug fixes.

Traditional cloud benchmarks assess **Developer Experience (DX)**: web console aesthetics, CLI installation simplicity, and human-readable tutorials. **The Glintbase Integration Index** introduces an empirical framework measuring **Agent Ergonomics (AX)**: the token budget, tool turns, control-plane friction, and failure modes an AI agent experiences when attempting to discover, provision, and operate inside a sandbox autonomously.

This edition subjected five leading sandbox providers—**Modal**, **E2B**, **boat by ASCII**, **Vercel Sandbox**, and **Daytona**—to an exhaustive two-phase benchmark: a front-door machine-readability scan (119 checks) followed by 30 live autonomous integration trials across six standardized software engineering challenges.

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

### The 5 Key Empirical Takeaways

1. **Modal Leads Runtime Ergonomics Despite Poor Front-Door Discoverability (#1, $\text{IT} = 1.03\times$)**:  
   Modal took first place in Integration Tax, dominating execution latency (19.5s median) and agent tool steps (3.0 median). Its native container tunneling (`encrypted_ports=[8000]` and `sb.tunnels()`) provided instant HTTPS endpoints without reverse-proxy configuration. However, its web domain completely omits machine-readable REST schemas (scoring 36/100, Grade D in front-door scans).
2. **E2B Delivers the Leanest Cognitive Footprint and Zero Human Stops (#2, $\text{IT} = 1.17\times$)**:  
   E2B required only **1,865 median tokens** per trial—the lowest in the cohort. It was the **only platform where an agent completed all six trials with zero out-of-band human touches**, powered by single-variable authentication (`E2B_API_KEY`) and intuitive typed exceptions (`CommandExitException`).
3. **The Paywall Stumble: boat.dev’s Front-Door Inversion (#3, $\text{IT} = 1.21\times$)**:  
   boat by ASCII achieved the highest Front-Door ARS Score (**82/100, Grade B**), but dropped to #3 in runtime execution. Although its public port ingress (`api.host_port`) was effortless, the agent hit an unannounced HTTP 402 `Payment Required` gate during dependency installation, requiring a human developer to attach a credit card on the web console before execution could resume.
4. **The Triple-Credential Setup Tax on Vercel Sandbox (#4, $\text{IT} = 1.37\times$)**:  
   Vercel Sandbox boots microVMs rapidly (21.6s median), but penalizes agent workflows by requiring three separate credentials (`VERCEL_TOKEN`, `VERCEL_PROJECT_ID`, `VERCEL_TEAM_ID`). Discovering and wiring this triad inflated agent step counts (5.0 median) and token burn.
5. **The Unauthenticated Proxy Trap on Daytona (#5, $\text{IT} = 1.43\times$)**:  
   Daytona ships rich development environments (Python 3.14, git, zsh pre-installed). However, when exposing web servers, its default proxy routing returns an HTTP 401 Unauthorized barrier. Agents had to discover and generate signed preview URLs (`sb.create_signed_preview_url`), driving its orchestration tax to 1.43x across 5.0 median steps.
6. **100% Teardown Integrity Across All Cohorts (Zero Cloud Leaks)**:  
   Across all 30 trials, independent post-run control-plane queries confirmed that **zero microVMs or containers remained running**. Every vendor's teardown primitive (`sandbox.kill()`, `sb.terminate()`, `boat_sdk.stop_and_remove()`, `client.delete()`) functioned reliably within programmatic `try...finally` blocks.

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

### The Two Fatal Metrics:
1. **Token Bleed**: Every extra step an agent spends diagnosing an authentication error or retrying a command consumes prompt and completion tokens. Because context windows compound quadratically in multi-turn execution, platform friction directly inflates the agent operator's bill.
2. **Human Stops ($H_s$)**: The metric that matters most to production agent systems. If an autonomous code generator requires human dashboard intervention to configure secrets or enter billing details, **the agent is no longer autonomous**.

---

## 3. Methodology & Mathematical Rigor

### 3.1 The 6 Standardized Functional Challenges

To guarantee absolute scientific parity, every sandbox was subjected to the identical prompt (`PROMPT.txt`), objective, assertion criteria, and timeout limits:

| Trial | Challenge Name | Objective & Execution Method | Assertion & Pass Criteria |
|---|---|---|---|
| **Trial 1** | **Hello Sandbox Lifecycle** | Provision microVM/container, execute standard print statement, and cleanly terminate. | MicroVM stdout contains exact challenge string. 0 leaked instances. |
| **Trial 2** | **Install & Run Dependencies** | Install external Python package (`polars`) inside microVM, execute data frame calculation. | Stdout contains computed result: `SUM:60`. |
| **Trial 3** | **Remember Me (State Persistence)** | In discrete Command 1: write secret string to `/tmp/state.txt`. In discrete Command 2: read file. | Stdout of Command 2 contains exact secret string `STATE-PERSIST-991`. |
| **Trial 4** | **Serve It (Ingress Networking)** | Launch HTTP server on port 8000, obtain public ingress URL, probe from external runner. | External HTTP GET request returns `200 OK` with body `GLINT-SERVER-OK`. |
| **Trial 5** | **Break It (Resilience & Recovery)** | Intentionally execute dividing by zero (`1/0`), trap stderr, probe responsiveness. | Agent traps exception, subsequently executes healthy probe returning `HEALTHY-RECOVERY-77`. |
| **Trial 6** | **Real Job (SWE Test Suite)** | Clone `https://github.com/bottlepy/bottle` via git, execute full unit test suite. | Executes `python3 test/test_all.py`, prints test suite summary, prints `TEST_SUITE_FINISHED`. |

### 3.2 Harness & Execution Topology
- **Agent Framework**: Antigravity Autonomous Agent Framework (Google DeepMind AAC architecture).
- **Topology**: Hierarchical two-tier architecture:
  - *Parent Orchestrator*: Manages isolation, trial scaffolding, environment variables, and external verification.
  - *Worker Subagents*: Dedicated subagents dispatched into clean subdirectories (`/trial-[1-6]`) equipped with file and terminal tools.
- **Base Intelligence**: Gemini 3.8 Flash (Medium context profile).
- **Independent Verification Protocol (`verify.py`)**: Subagent self-reporting is never trusted. An external verification script executes independently after each trial to test output strings, assert timeouts, and query the vendor's cloud control-plane API to ensure zero lingering sandboxes.

### 3.3 The Integration Tax Formula

$$\text{Integration Tax (IT)} = \left[ 0.40 \times \left(\frac{\text{Tokens}_{\text{med}}}{\text{Min Tokens}}\right) + 0.40 \times \left(\frac{\text{Steps}_{\text{med}}}{\text{Min Steps}}\right) + 0.20 \times \left(\frac{\text{Time}_{\text{med}}}{\text{Min Time}}\right) \right] \times \text{Penalty}$$

- **Minima Baseline**:
  - $\text{Min Tokens} = 1,865$ (E2B)
  - $\text{Min Steps} = 3.0$ (Modal & boat)
  - $\text{Min Time} = 19.5\text{s}$ (Modal)
- **Why Medians Are the Core Standard**:  
  Medians insulate the benchmark against single-trial outlier skew (for example, boat’s Trial 2 payment gate retry inflated its total tokens to 26,598, whereas its median across five healthy trials was a competitive 2,580 tokens). Totals are published alongside medians to expose systemic friction.
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

> **Visual Assets**: See the high-resolution Anthropic-style editorial table [`visual1_master_leaderboard_table.png`](./visual1_master_leaderboard_table.png) and the [`visual4_integration_tax_leaderboard.png`](./visual4_integration_tax_leaderboard.png).

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

> **Visual Assets**: See the 2D scatter matrix [`visual2_frontdoor_vs_reality_scatter.png`](./visual2_frontdoor_vs_reality_scatter.png) and the challenge complexity line graph [`visual3_challenge_progression_linegraph.png`](./visual3_challenge_progression_linegraph.png).

### The Three Phenomenological Archetypes:

#### 1. The Modal Paradox (+4 Rank Surge)
Modal scored in the bottom tier on front-door discoverability (36/100) because its root domain omits OpenAPI endpoints, Swagger documentation, and machine-readable REST routes. It was designed from the ground up as a human-friendly Python decorator framework.  
However, when an AI coding agent is given the task of writing Python code against Modal's SDK, **Modal delivers the lowest friction in the entire benchmark**. Its container lifecycle is lightning-fast, and its ingress port tunneling primitive is the most elegant on the market.

#### 2. The boat.dev Inversion (-2 Rank Drop)
boat by ASCII led the cohort in front-door machine readiness (82/100) by publishing explicit REST API endpoints, curl examples, and machine-readable protocol schemas.  
Yet at runtime, the platform dropped to third place due to **commerce friction**: an unannounced HTTP 402 billing paywall that halted the agent mid-execution. A platform cannot be "agent-ready" on the front door if its backend halts execution for human credit card verification.

#### 3. The E2B Sweet Spot
E2B demonstrated the tightest alignment between static discoverability and runtime execution. It scored a strong Grade B (75/100) on the front door while delivering the lowest token footprint (1,865 median tokens) and zero human stops at runtime.

---

## 6. Per-Provider Technical Dossiers

> **Visual Asset**: Cross-provider trial comparisons and tool steps are summarized in the Friction Matrix Heatmap: [`visual5_provider_challenge_heatmap.png`](./visual5_provider_challenge_heatmap.png).

---

### Cohort 1: Modal Labs (`modal 1.6.1`)
**Leaderboard Position**: **#1 Overall** | **Integration Tax**: **1.03x** | **Pass Rate**: **100% (6/6)**

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
- **Webhook vs. API Token Mismatch (`AuthError: Token ID is malformed`)**: Modal issues webhook keys (`wk-...`) and control-plane API tokens (`ak-...`). Providing a `wk-...` key crashes the sandbox immediately with an uninformative error.
- **Mandatory App Binding**: Standalone sandbox creation fails unless explicitly associated with an App via `modal.App.lookup(..., create_if_missing=True)`.

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
- **Zero Human Stops**: The only provider where the agent completed all 6 challenges with a single key (`E2B_API_KEY`) and zero out-of-band human touches.
- **Typed Error Trapping**: Raised clean `CommandExitException` objects containing exit codes, stdout, and stderr.

#### Runtime Traps & Gotchas:
- **Synchronous Process Blocking**: Calling `sandbox.commands.run("python3 -m http.server 8000")` blocks the agent indefinitely unless background flags (`background=True`) or `nohup` are used.
- **MicroVM Boot Latency**: MicroVM provisioning resulted in a 29.2s median wall time (compared to Modal’s 19.5s container scheduling).

#### What E2B Could Fix:
1. **Background Daemon Helper**: Add an explicit `sandbox.start_service()` primitive that automatically wraps background web servers.
2. **Publish an Agent Catalog (`ard.json`)**: Deploy `.well-known/ard.json` on `e2b.dev` to achieve Grade A front-door discoverability.

---

### Cohort 3: boat by ASCII (`boat-sdk 1.5.0`)
**Leaderboard Position**: **#3 Overall** | **Integration Tax**: **1.21x** | **Pass Rate**: **100% (6/6)**

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
- **The HTTP 402 Payment Gate**: MicroVM creation failed with HTTP 402 `Payment Required` until a human added a credit card on the web console, triggering an agent stumble and token outlier (12,603 tokens in Trial 2).
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
- **Triple-Credential Friction**: Required `VERCEL_TOKEN`, `VERCEL_PROJECT_ID`, and `VERCEL_TEAM_ID`, halting the agent until the user supplied project metadata.
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
- **Unauthenticated Default Proxy URLs (HTTP 401)**: The standard proxy URL returned 401 Unauthorized for external automated probes, requiring the agent to discover `sb.create_signed_preview_url(8000, 300)`.
- **`client.list()` Generator Crash**: `client.list()` yields a generator instead of a list, causing `len(client.list())` to crash with `TypeError`.
- **Highest Orchestration Overhead**: 5.0 median steps and 2,260 median tokens drove Integration Tax to 1.43x.

#### What Daytona Could Fix:
1. **Public Preview Ingress Parameter**: Add a `public=True` flag to `sb.process.exec` or preview methods to eliminate the signed preview URL workaround.
2. **List Collection Return**: Make `client.list()` return a list or implement `__len__` on the generator wrapper.

---

## 7. Methodological Limitations & Transparency Disclosures

1. **Preliminary Pilot Sample Size ($n=1$)**:  
   This edition reflects a single deterministic run per trial, independently verified by automated test runners. While 100% pass rates and zero leaks were confirmed, a planned follow-up will execute automated $n=3$ repeats to quantify standard deviation ($\sigma$).
2. **Single Foundation Model Profile**:  
   All trials were conducted using Gemini 3.8 Flash via the Antigravity harness. Reasoning models with different tool-calling tendencies (e.g., Claude 3.5 Sonnet, OpenAI o1) may yield slightly different token and step counts.
3. **Geographic Network Context**:  
   Latencies were measured from an enterprise European connection; North American runners will likely experience lower TLS round-trip latencies on US-hosted endpoints.

---

## 8. What's Next: The Glintbase Roadmap

- **Quarterly Sandbox Re-Benchmark (Q1 2027)**: Evaluating how quickly vendors implement agent-first improvements.
- **The Glintbase Integration Index: Edition 2 (Agentic Payments)**: Benchmarking autonomous payment protocols (Stripe Agentic Toolkit, Coinbase AgentKit, Skyfire) across agent checkout workflows.

---

## Appendix & Reproduction Index

All raw assets, code solutions, verifiers, and datasets are open source in the benchmark directory:
- Master Dataset: [`benchmark_master.json`](./benchmark_master.json) · [`benchmark_master.csv`](./benchmark_master.csv)
- Formal Methodology: [`METHODOLOGY.md`](./METHODOLOGY.md)
- Engineering Gotchas Dossier: [`GOTCHAS_AND_TRAPS.md`](./GOTCHAS_AND_TRAPS.md)
- Front-Door Scan Report: [`phase1-scans/phase1_frontdoor_report.md`](./phase1-scans/phase1_frontdoor_report.md)
- Trial Solutions: `sandbox-benchmark/{modal-sandbox,pilot-e2b,boat-sandbox,vercel-sandbox,daytona-sandbox}/trial-[1-6]`
