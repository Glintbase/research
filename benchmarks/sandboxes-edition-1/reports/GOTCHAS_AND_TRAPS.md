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

---

## 1. Modal Labs (`modal 1.6.1`)

### Trap 1.1: Webhook Key vs. API Token Mismatch
- **Exact Error**: `modal.exception.AuthError: Token ID is malformed`
- **Root Cause**: Modal issues two primary credential types in its console:
  - Webhook/Proxy Keys: prefixed with `wk-...` (secret `ws-...`).
  - Control-Plane API Tokens: prefixed with `ak-...` (secret `as-...`).
  When an agent is handed webhook credentials (common in gateway integrations), `modal.Sandbox.create` immediately crashes with an uninformative "Token ID is malformed" error.
- **Human Stop Trigger**: Human developer had to log into `modal.com/settings/tokens` and generate an explicit `ak-...` token.
- **Vendor Recommendation**: Provide descriptive error messaging: `"Token ID 'wk-...' is a webhook token. Control-plane sandbox operations require an API Token starting with 'ak-...'."`

### Trap 1.2: The Mandatory App Binding Prerequisite
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
- **Symptom**: Calling `sandbox.commands.run("python3 -m http.server 8000")` hangs indefinitely because the command runner blocks until stdout terminates.
- **The Agent Solution**:
  ```python
  # Must use background=True or nohup
  sandbox.commands.run("nohup python3 -m http.server 8000 > /tmp/srv.log 2>&1 &")
  ```

### What E2B Did Best:
- **Zero Human Stops**: E2B was the **only** provider in the benchmark where an agent successfully completed all 6 challenges with a single environment variable (`E2B_API_KEY`) and zero out-of-band human touches.
- **Lowest Token Burn**: Required just 1,865 median tokens—a testament to its clean SDK declarations and intuitive typed exceptions (`CommandExitException`).

---

## 3. boat by ASCII (`boat-sdk 1.5.0`)

### Trap 3.1: The Unannounced Credit Card Paywall
- **Exact Error**: `HTTP 402 Payment Required: Please attach payment method to continue`
- **Root Cause**: An active API key (`boat_...`) generated on the platform is rejected at the microVM provisioning stage unless a valid credit card is stored on `boat.dev/dashboard?tab=billing`.
- **Human Stop Trigger**: The agent was completely blocked during Trial 2 until the human entered credit card details on the web dashboard.
- **Token Impact**: Outlier token spike (12,603 tokens) as the subagent diagnosed the 402 response and attempted retries.
- **Vendor Recommendation**: Allow a minimal free tier credit ($5) on initial API key generation without requiring a hard card barrier for automated evaluations.

### Trap 3.2: Debian/Ubuntu PEP 668 Managed Environment
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
- **Exact Error**: `TypeError: object of type 'generator' has no len()`
- **Root Cause**: Calling `len(client.list())` during cleanup verification crashed because `Daytona.list()` yields a generator instead of returning a list or collection.
- **Fix**: Wrapped call in `list(client.list())`.

### What Daytona Did Best:
- **Full Dev Environment**: Sandboxes arrived with Python 3.14, git, and zsh pre-installed, making complex real-world SWE tasks (`bottlepy` test suite) effortless once running.

---

## Summary: Control-Plane Friction Matrix

| Provider | Credentials Required | Hard Paywalls | Ingress Friction | PEP 668 Issues | Teardown Leak Rate |
|---|:---:|:---:|:---:|:---:|:---:|
| **E2B** | 1 (`api_key`) | None | None | No | **0% (Clean)** |
| **Modal** | 2 (`ak-...` / `as-...`) | None | None | No | **0% (Clean)** |
| **boat** | 1 (`access_token`) | **Card Gate (402)** | None | **Yes** | **0% (Clean)** |
| **Vercel** | **3 (Token, Prj, Team)** | None | Route extraction | No | **0% (Clean)** |
| **Daytona** | 1 (`api_key`) | None | **Default 401 (Signed URL required)** | No | **0% (Clean)** |
