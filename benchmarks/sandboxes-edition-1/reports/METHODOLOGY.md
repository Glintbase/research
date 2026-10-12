# Methodology Specification — The Glintbase Integration Index (Sandboxes Edition 1)

> **Document Version**: 1.0.0 (Audit-Grade Specification)  
> **Evaluation Subject**: Cloud Code Sandboxes for Autonomous AI Coding Agents  
> **Evaluation Window**: October 5–6, 2026  
> **Harness Topology**: Antigravity AI Agent Pair-Programming Architecture (DeepMind AAC)  
> **Sample Size**: Preliminary Pilot Cohort ($n=1$ Deterministic with Independent External Verification)

> [!WARNING]
> **Corrections (2026-10-12)**: see [`../ERRATA.md`](../ERRATA.md).
> - **Prompts were not identical across providers.** Modal and boat prompts name the exact API calls, E2B and Vercel prompts are mostly plain language, and the Daytona Trial 4 prompt names `create_signed_preview_url`. The Integration Tax ranking is **not a controlled comparison** and is indicative only.
> - **Tokens, steps and wall time are self-reported.** The agent wrote them into `run_log.json` at the end of each trial; the harness did not measure them. Some values were modelled on earlier trials' logs. `harness/measure_transcripts.py` derives turns, tool calls and session length from the transcripts into `data/measured_metrics.csv`. No token counts exist in the transcripts.
> - **The published `verify.py` could not detect leaks**, and the Trial 6 verifiers accepted output with no test run. Both have been fixed. The corrected pass rate is 28/30.

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
  *Correction (2026-10-12): the prompts were not standard across providers. The Modal and boat prompts include the exact SDK calls needed (for example `modal.App.lookup(...)`, `sb.tunnels()`, `api.host_port(...)`). E2B and Vercel prompts are mostly plain language with a few method hints. The Daytona prompts name the client constructor, and Trial 4 names `sb.create_signed_preview_url(8000, 300)`. The level of help differed by provider.*

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

Every provider was subjected to the same functional objectives across 6 isolated trials. *(Correction 2026-10-12: the objectives were shared; the prompt wording and level of SDK detail were not.)*

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

*Correction (2026-10-12):*
- *Every verifier run in the published transcripts was executed by the agent inside its own trial loop. No separate harness run is published.*
- *Item 3 did not work as described. When sandboxes were still listed, the published `verify.py` printed a warning, deleted them and still passed. If the listing call failed, it also passed. It could not detect a leak.*
- *For Trial 6, the Modal, E2B, Vercel and Daytona verifiers also passed on the words "passed" or "ok" anywhere in stdout, and the boat verifier on the bare marker. Modal and boat print the marker unconditionally, and their runs show no test execution.*
- *All 30 `verify.py` files now fail (non-zero exit) when sandboxes remain or the leak check cannot run. The Trial 6 verifiers require a real unittest `Ran N tests … OK` or pytest `N passed` summary. See ERRATA E4 and E5.*

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
- **Input provenance (Correction 2026-10-12)**: the token, step and time inputs are agent self-reports from `run_log.json`, not harness measurements (ERRATA E3). Transcript-measured model turns per trial are 3–8× the reported steps and rank providers differently.
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

*Correction (2026-10-12): none of the three human stops above is recorded in the published transcripts. Each of the 30 transcripts has a single user turn, and every prompt ends "Do not ask questions". The agent-written `run_log.json` files and `data/integration_tax_summary.json` also record 0 human stops. The 1/1/1 values exist only in the hand-edited `benchmark_master.*`, report and README. **The transcripts are the authoritative source: 0 human stops for every provider.** Setup work outside the recorded trials, if any, cannot be verified. The Integration Tax formula does not use human stops, so the ranking is unaffected.*

### 5.4 Stumbles
A **Stumble** is defined as an in-band failure that the agent successfully diagnosed, recovered from, and resolved without human intervention (e.g., catching a 401 unauthenticated domain and switching to a signed URL).

*Correction (2026-10-12): the example given (a 401 on Daytona) is not captured in any transcript, and the published Daytona stumble is corrected to 0. The run-log counts (boat 1, others 0) stand. The boat stumble was a PEP 668 pip error, not an HTTP 402. Published stumble counts were not systematically coded from the transcripts and undercount the in-band failures the transcripts show.*

### 5.5 Zero-Leak Teardown Audit
Following every trial execution, `verify.py` invokes the vendor's listing endpoint (`client.list()`, `api.sandboxes()`, etc.). If any sandbox remains in a running or paused state after execution, it is flagged as a leaked instance.  
*Correction (2026-10-12): in the published verifier a remaining sandbox was only warned about, then deleted, and the trial still passed. This happened in Daytona Trial 4. The published "0 leaks" values are therefore not verifiable. The verifier now exits non-zero in this case.*

### 5.6 End-to-End Command Latency
Wall-clock seconds elapsed from the launch of `python solution.py` to process exit. Includes network round-trip, TLS negotiation, container/microVM scheduling, command execution, and clean teardown.  
*Correction (2026-10-12): the published values were reported by the agent, not timed by the harness (ERRATA E3).*

---

## 6. Sample Size & Limitations Disclosure

- **Preliminary Pilot Cohort ($n=1$)**: This benchmark represents a single deterministic execution pass per trial, independently validated by post-hoc test runners. *(Correction 2026-10-12: agent runs are not deterministic, and no post-hoc verifier runs separate from the agent's own are published.)*
- **Non-identical prompts and self-reported metrics (added 2026-10-12)**: see the warning at the top of this document.
- **Single Model Family**: All trials were executed using Gemini 3.8 Flash via the Antigravity harness. Different reasoning models (e.g., Claude 3.5 Sonnet, OpenAI o1) may exhibit differing tool call trajectories.
- **Regional Latency**: Network latencies were measured from an enterprise European connection; US-based runners may observe slightly different raw latencies.
