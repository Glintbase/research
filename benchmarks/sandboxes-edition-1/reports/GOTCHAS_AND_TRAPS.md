# Research Dossier: Runtime Gotchas, Traps & Failure Modes (Sandboxes Edition 1)

> **Document Version**: 1.0.0 (Empirical Field Notes)  
> **Source**: 30 Autonomous Agent Execution Transcripts across Modal, E2B, boat by ASCII, Vercel, and Daytona  
> **Audience**: AI Agent Engineers, Platform Architects, and Sandbox Founders

---

## Executive Summary: The Anatomy of an Agent Trap

Human developers read documentation, notice missing environment variables, navigate web consoles, and adapt to breaking changes intuitively. 

When an autonomous AI agent encounters unexpected control-plane friction:
1. It burns 1,000 to 5,000 tokens reading stack traces and retrying alternative SDK calls.
2. It risks entering non-deterministic hallucination loops.
3. If an unannounced credential or payment barrier appears, execution halts completely (**Human Stop**).

This dossier catalogs the exact gotchas, error messages, and workarounds discovered across all 30 benchmark runs.

> [!WARNING]
> **Correction (2026-10-12).** We checked every quoted error against the 30 published transcripts. Only one of the traps below appears in them: boat's PEP 668 `externally-managed-environment` error (Trap 3.2). Traps 1.1, 1.2, 2.1, 3.1, 4.1, 5.1 and 5.2 are **not captured in the published transcripts**. They are labelled as such below and must not be cited as observed results of this benchmark. No transcript records a human stop. The prompts for several providers already contained the fix (for example Modal's `App.lookup`, Daytona's `create_signed_preview_url`, and Vercel's three credential names). See [`../ERRATA.md`](../ERRATA.md) (E1, E2, E5).

---

## 1. Modal Labs (`modal 1.6.1`)

### Trap 1.1: Webhook Key vs. API Token Mismatch
> *Not captured in the published transcripts (Correction 2026-10-12). Modal Trial 1 succeeded on its first run, and no "malformed" error appears in any Modal transcript.*

- **Exact Error**: `modal.exception.AuthError: Token ID is malformed`
- **Root Cause**: Modal issues two primary credential types in its console:
  - Webhook/Proxy Keys: prefixed with `wk-...` (secret `ws-...`).
  - Control-Plane API Tokens: prefixed with `ak-...` (secret `as-...`).
  When an agent is handed webhook credentials (common in gateway integrations), `modal.Sandbox.create` immediately crashes with an uninformative "Token ID is malformed" error.
- **Human Stop Trigger**: Human developer had to log into `modal.com/settings/tokens` and generate an explicit `ak-...` token.
- **Vendor Recommendation**: Provide descriptive error messaging: `"Token ID 'wk-...' is a webhook token. Control-plane sandbox operations require an API Token starting with 'ak-...'."`

### Trap 1.2: The Mandatory App Binding Prerequisite
> *Not captured in the published transcripts (Correction 2026-10-12). Every Modal `PROMPT.txt` supplied the `modal.App.lookup(..., create_if_missing=True)` call.*

- **Exact Error**: `ValueError: Sandboxes must be associated with an App`
- **Root Cause**: Unlike E2B or Daytona where `Sandbox.create()` is a standalone call, Modal requires every sandbox to live inside an App context.
- **The Agent Solution**:
  ```python
  app = modal.App.lookup("glint-modal-app", create_if_missing=True)
  sb = modal.Sandbox.create("python3", "-c", "...", app=app)
  ```

### What Modal Did Best:
- **Tunnels**: Port exposure via `encrypted_ports=[8000]` and `sb.tunnels()[8000].url` yielded zero-config, authenticated HTTPS URLs instantly.

---

## 2. E2B (`e2b 1.0.5`)

### Trap 2.1: Background Daemons via Synchronous Commands
> *Not captured in the published transcripts (Correction 2026-10-12). The E2B Trial 4 solution used `background=True` from the start, and no hang or timeout is recorded.*

- **Symptom**: Calling `sandbox.commands.run("python3 -m http.server 8000")` hangs indefinitely because the command runner blocks until stdout terminates.
- **The Agent Solution**:
  ```python
  # Must use background=True or nohup
  sandbox.commands.run("nohup python3 -m http.server 8000 > /tmp/srv.log 2>&1 &")
  ```

### What E2B Did Best:
- **Zero Human Stops**: E2B was the **only** provider in the benchmark where an agent successfully completed all 6 challenges with a single environment variable (`E2B_API_KEY`) and zero out-of-band human touches. *(Correction 2026-10-12: not unique. No provider's transcripts record a human stop.)*
- **Lowest Token Burn**: Required just 1,865 median tokens—a testament to its clean SDK declarations and intuitive typed exceptions (`CommandExitException`). *(Correction 2026-10-12: the token figure is self-reported by the agent. E2B has the highest median of transcript-measured model turns, ERRATA E3.)*

---

## 3. boat by ASCII (`boat-sdk 1.5.0`)

### Trap 3.1: The Unannounced Credit Card Paywall
> *Not captured in the published transcripts (Correction 2026-10-12). No boat transcript contains an HTTP 402 or "Payment Required", and the Trial 2 transcript has a single user turn, so no human intervention is recorded. The failure that is recorded in Trial 2 is Trap 3.2. The 12,603-token figure is the agent's self-report.*

- **Exact Error**: `HTTP 402 Payment Required: Please attach payment method to continue`
- **Root Cause**: An active API key (`boat_...`) generated on the platform is rejected at the microVM provisioning stage unless a valid credit card is stored on `boat.dev/dashboard?tab=billing`.
- **Human Stop Trigger**: The agent was completely blocked during Trial 2 until the human entered credit card details on the web dashboard.
- **Token Impact**: Outlier token spike (12,603 tokens) as the subagent diagnosed the 402 response and attempted retries.
- **Vendor Recommendation**: Allow a minimal free tier credit ($5) on initial API key generation without requiring a hard card barrier for automated evaluations.

### Trap 3.2: Debian/Ubuntu PEP 668 Managed Environment
> *Captured: `transcripts/boat/trial-2-install` records this error and the agent's recovery.*

- **Exact Error**: `error: externally-managed-environment: This environment is externally managed`
- **Root Cause**: The base Linux container enforces PEP 668, preventing raw `pip install polars`.
- **The Agent Solution**:
  ```python
  boat_sdk.exec_command(api, sb_id, "pip install --break-system-packages polars")
  ```

### What boat Did Best:
- **Port Ingress**: `api.host_port(sb_id, boat_sdk.HostPortRequest(port=8000, public=True))` returned clean public URLs on `*.on.boat.dev` in a single API call.

---

## 4. Vercel Sandbox (`vercel-sandbox 0.7.0`)

### Trap 4.1: The Triple-Credential Discovery Barrier
> *Not captured in the published transcripts (Correction 2026-10-12). The three-credential requirement is real, but no `Missing teamId or projectId` error and no request to the human are recorded. The Trial 1 prompt named all three variables, and the agent read them from `.env`.*

- **Exact Error**: `VercelAPIError: Missing teamId or projectId parameter`
- **Root Cause**: While E2B, Daytona, and boat require a single API key, Vercel requires three distinct secrets:
  1. `VERCEL_TOKEN` (Personal or Team Access Token)
  2. `VERCEL_PROJECT_ID` (e.g., `prj_...`)
  3. `VERCEL_TEAM_ID` (e.g., `team_...`)
- **Human Stop Trigger**: The agent had to stop and ask the human for project and team IDs.
- **Vendor Recommendation**: Provide a default personal workspace fallback when `projectId` and `teamId` are omitted in standalone sandbox creation.

### What Vercel Did Best:
- **Fast MicroVM Provisioning**: Provisioned microVMs with high speed (21.6s median end-to-end command latency).
- **Automated SSL Routes**: Ports exposed via `create_sandbox(ports=[8000])` automatically populated `sandbox.routes` with clean SSL domains.

---

## 5. Daytona (`daytona 0.222.0`)

### Trap 5.1: The Unauthenticated Proxy 401 Challenge
> *Not captured in the published transcripts (Correction 2026-10-12). No HTTP 401 appears in any Daytona transcript, and the Trial 4 prompt named `sb.create_signed_preview_url(8000, 300)`, so the agent did not have to discover it. The private-by-default preview behaviour is documented by Daytona; it was not observed here.*

- **Exact Error**: `HTTP 401 Unauthorized` on preview domain `https://8000-*-daytonaproxy01.eu`
- **Root Cause**: When an HTTP server is started inside Daytona, the default proxy URL generated is protected by Daytona dashboard user authentication cookies. Direct programmatic HTTP requests from external tools receive 401.
- **The Agent Solution**:
  The agent had to discover the signed URL method:
  ```python
  signed_url = sb.create_signed_preview_url(8000, 300)
  res = requests.get(signed_url.url) # Bypasses 401
  ```
- **Vendor Recommendation**: Document `create_signed_preview_url` prominently in agent code snippets.

### Trap 5.2: `client.list()` Generator Crash
> *Not captured in the published transcripts (Correction 2026-10-12). The published verifiers already wrap the call as `list(client.list())`.*

### Trap 5.3 (added 2026-10-12): Asynchronous Delete Leaves a Listed Sandbox
- **Observed**: `transcripts/daytona/trial-4-serve`, step 71. The first `verify.py` run printed `[WARN] Warning: Detected 1 active sandboxes after execution!` right after `client.delete(sb)`. The verifier then deleted the sandbox itself and reported PASSED.
- **The Agent Solution**: `client.delete(sb, wait=True)`. The re-run reported 0 leaked sandboxes.
- **Why it matters**: the published verifier hid this. It is the only leftover sandbox recorded in the transcripts.
- **Exact Error**: `TypeError: object of type 'generator' has no len()`
- **Root Cause**: Calling `len(client.list())` during cleanup verification crashed because `Daytona.list()` yields a generator instead of returning a list or collection.
- **Fix**: Wrapped call in `list(client.list())`.

### What Daytona Did Best:
- **Full Dev Environment**: Sandboxes arrived with Python 3.14, git, and zsh pre-installed, making complex real-world SWE tasks (`bottlepy` test suite) effortless once running.

---

## Summary: Control-Plane Friction Matrix

> *Correction (2026-10-12): in this matrix, the boat "Card Gate (402)" and the Daytona "Default 401" are not captured in the published transcripts. The "Teardown Leak Rate" column is **not verifiable**, because the published verifier deleted leftover sandboxes and still passed (Daytona Trial 4 had one). See ERRATA E2 and E5.*

| Provider | Credentials Required | Hard Paywalls | Ingress Friction | PEP 668 Issues | Teardown Leak Rate |
|---|:---:|:---:|:---:|:---:|:---:|
| **E2B** | 1 (`api_key`) | None | None | No | **0% (Clean)** |
| **Modal** | 2 (`ak-...` / `as-...`) | None | None | No | **0% (Clean)** |
| **boat** | 1 (`access_token`) | **Card Gate (402)** | None | **Yes** | **0% (Clean)** |
| **Vercel** | **3 (Token, Prj, Team)** | None | Route extraction | No | **0% (Clean)** |
| **Daytona** | 1 (`api_key`) | None | **Default 401 (Signed URL required)** | No | **0% (Clean)** |
