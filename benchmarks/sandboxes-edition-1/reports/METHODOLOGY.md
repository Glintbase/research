# Methodology Specification — The Glintbase Integration Index (Sandboxes Edition 1)

> **Document Version**: 1.0.0 (Audit-Grade Specification)  
> **Evaluation Subject**: Cloud Code Sandboxes for Autonomous AI Coding Agents  
> **Evaluation Window**: October 5–6, 2026  
> **Harness Topology**: Antigravity AI Agent Pair-Programming Architecture (DeepMind AAC)  
> **Sample Size**: Preliminary Pilot Cohort ($n=1$ Deterministic with Independent External Verification)

---

## 1. Objective & Hypothesis

Traditional cloud benchmarks measure human developer experience (DX): dashboard aesthetic, CLI ease of installation, and documentation readability. 

**The Glintbase Integration Index** measures **Agent Ergonomics (AX)**:
- How much token budget does an autonomous AI agent burn to discover, authenticate, and execute code?
- How many cognitive tool turns (steps) does the agent require?
- Does the platform trap the agent in unauthenticated proxies, malformed token schemes, or unannounced billing paywalls?
- Does the microVM cleanly terminate, or does it leak dangling instances onto the developer's cloud bill?

---

## 2. Test Harness & Execution Topology

### 2.1 Harness Architecture
- **Framework**: Antigravity Autonomous Agent Framework.
- **Agent Topology**: Two-tier hierarchical model:
  1. **Parent Orchestrator**: Manages trial scheduling, secret scoping, and independent test verification.
  2. **Worker Subagents**: Isolated execution agents operating in dedicated directory sandboxes (`/trial-[1-6]`). Subagents have access to file read/write, terminal execution, and process inspection tools.
- **Underlying Intelligence**: Gemini 3.8 Flash (Medium context profile).
- **Prompting Protocol**: Zero-shot standard prompt (`PROMPT.txt`) provided in each trial directory with objective and expected output marker. No proprietary vendor tips or hints are injected unless explicitly required by API specs.

### 2.2 Host Environment
- **Host OS**: Windows 11 Enterprise (x86_64).
- **Python Runtime**: Python 3.12.6.
- **Secret Isolation**: All credentials loaded strictly via local `.env` files (gitignored).

---

## 3. Evaluated Providers & SDK Versions

Each provider was evaluated using its official Python SDK current as of October 6, 2026:

| Provider | Canonical Organization | SDK Package | Tested Version | Auth Prerequisite |
|---|---|---|---|---|
| **Modal** | Modal Labs, Inc. | `modal` | `1.6.1` | API Token (`ak-...` / `as-...`) + App lookup |
| **E2B** | E2B (YC W24) | `e2b` | `1.0.5` | Single API Key (`E2B_API_KEY`) |
| **boat** | ASCII Inc. | `boat-sdk` | `1.5.0` | API Key (`BOAT_API_KEY`) + Card on file |
| **Vercel Sandbox** | Vercel Inc. | `vercel-sandbox` | `0.7.0` | 3 Keys: `TOKEN`, `PROJECT_ID`, `TEAM_ID` |
| **Daytona** | Daytona Platforms, Inc. | `daytona` | `0.222.0` | Single API Key (`DAYTONA_API_KEY`) |

---

## 4. The 6 Standardized Empirical Challenges

Every provider was subjected to identical functional objectives across 6 isolated trials:

```
┌─────────┬─────────────────────────────────────┬─────────────────────────────────────────────────────────────┐
│ Trial   │ Challenge Name                      │ Verification Assertion                                      │
├─────────┼─────────────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ Trial 1 │ Hello Sandbox Lifecycle             │ MicroVM creates, runs `print(...)`, outputs exact marker.   │
│ Trial 2 │ Install & Run Dependencies          │ MicroVM installs `polars`, computes Series sum: `SUM:60`.   │
│ Trial 3 │ Remember Me (State Persistence)     │ Write `/tmp/state.txt`, verify read in discrete command.    │
│ Trial 4 │ Serve It (Ingress Networking)       │ Bind port 8000, query external URL for `GLINT-SERVER-OK`.   │
│ Trial 5 │ Break It (Resilience & Recovery)    │ Trigger `1/0`, trap error, probe healthy recovery marker.   │
│ Trial 6 │ Real Job (SWE Test Suite)           │ Clone `bottlepy/bottle` via git, execute `test/test_all.py`.│
└─────────┴─────────────────────────────────────┴─────────────────────────────────────────────────────────────┘
```

### 4.1 Independent Verification Protocol (`verify.py`)
No trial is marked passed based on subagent self-reporting. 
An independent verifier script (`verify.py`) executes outside the agent loop to confirm:
1. `solution.py` exists and executes deterministically.
2. The stdout/stderr contains the exact expected challenge output.
3. The vendor's control-plane API is queried to verify that **zero active sandboxes** remain in the account.

---

## 5. Metric Definitions & Mathematical Formulation

### 5.1 Integration Tax ($\text{IT}$)
Integration Tax measures the compounded overhead an agent incurs compared to the ideal theoretical minimum across the cohort:

$$\text{IT} = \left[ 0.40 \times \left(\frac{\text{Tokens}_{\text{med}}}{\text{Min Tokens}}\right) + 0.40 \times \left(\frac{\text{Steps}_{\text{med}}}{\text{Min Steps}}\right) + 0.20 \times \left(\frac{\text{Time}_{\text{med}}}{\text{Min Time}}\right) \right] \times \text{Penalty}$$

- **Weight Rationale**: Tokens (40%) and Steps (40%) reflect direct LLM billing cost and compounding reasoning error risks. Wall Time (20%) reflects user-perceived turnaround latency.
- **Normalization Baseline**:
  - $\text{Min Tokens} = 1,865$ (E2B)
  - $\text{Min Steps} = 3.0$ (Modal & boat)
  - $\text{Min Time} = 19.5\text{s}$ (Modal)
- **Aggregation Rule**: We calculate $\text{IT}$ using **median** values across the 6 trials. Medians prevent single-trial outliers (such as an external pip network delay or initial card gate) from disproportionately skewing a platform's structural ranking. Totals and ranges are reported alongside medians for full transparency.

### 5.2 Penalty Multiplier
$$\text{Penalty} = \begin{cases} 1.0 & \text{if } \text{Pass Rate} = 100\% \\ 1.0 + \frac{100 - \text{Pass Rate}}{50} & \text{if } \text{Pass Rate} < 100\% \end{cases}$$
*(A 0% pass rate receives a $3.0\times$ penalty multiplier).*

### 5.3 Human Stops ($H_s$)
A **Human Stop** is defined as an event where an autonomous agent cannot complete the trial without out-of-band human intervention.
- *Modal*: Human required to replace webhook key with API token.
- *Vercel*: Human required to inspect project dashboard to discover Project ID and Team ID.
- *boat*: Human required to enter credit card on billing dashboard after HTTP 402 rejection.
- *Daytona / E2B*: 0 human stops.

### 5.4 Stumbles
A **Stumble** is defined as an in-band failure that the agent successfully diagnosed, recovered from, and resolved without human intervention (e.g., catching a 401 unauthenticated domain and switching to a signed URL).

### 5.5 Zero-Leak Teardown Audit
Following every trial execution, `verify.py` invokes the vendor's listing endpoint (`client.list()`, `api.sandboxes()`, etc.). If any sandbox remains in a running or paused state after execution, it is flagged as a leaked instance.

### 5.6 End-to-End Command Latency
Wall-clock seconds elapsed from the launch of `python solution.py` to process exit. Includes network round-trip, TLS negotiation, container/microVM scheduling, command execution, and clean teardown.

---

## 6. Sample Size & Limitations Disclosure

- **Preliminary Pilot Cohort ($n=1$)**: This benchmark represents a single deterministic execution pass per trial, independently validated by post-hoc test runners.
- **Single Model Family**: All trials were executed using Gemini 3.8 Flash via the Antigravity harness. Different reasoning models (e.g., Claude 3.5 Sonnet, OpenAI o1) may exhibit differing tool call trajectories.
- **Regional Latency**: Network latencies were measured from an enterprise European connection; US-based runners may observe slightly different raw latencies.
