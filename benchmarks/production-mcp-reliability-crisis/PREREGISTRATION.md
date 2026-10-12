# Pre-registration — Remote MCP Server Reliability (2026)

> **Status:** Frozen 2026-10-12 by local commit, before round 1. A 25-endpoint pilot (`round_pilot`) ran before freezing to test the harness; it is excluded from all results.
> Any change after freezing is listed under *Deviations* with date and reason.
> **Authors:** Glintbase Research · **Contact:** research@glintbase.dev

## 1. Research questions (descriptive; no directional hypotheses)

- **RQ1:** What share of remote MCP endpoints listed in the official MCP Registry are reachable and answer the MCP protocol?
- **RQ2:** Among endpoints that complete a handshake, which protocol era and version do they speak (modern `2026-07-28` per-request metadata vs. legacy `initialize`-based revisions)?
- **RQ3:** Among auth-gated endpoints, what share present a challenge an agent can follow: a `Bearer` `WWW-Authenticate` challenge **and** valid RFC 9728 protected-resource metadata?
- **RQ4:** Among endpoints that list tools anonymously, what share declare strict input schemas, safety annotations (`readOnlyHint`, `destructiveHint`) and descriptions?
- **RQ5:** What share return an in-channel error (JSON-RPC `error` or `result.isError: true`) when asked to call a tool that doesn't exist?
- **RQ6:** How stable is each endpoint's classification between two rounds? *(See Deviation 1: rounds run back-to-back, so this is reported as re-test reliability.)*

## 2. Population and sampling

- **Source:** official MCP Registry, `GET https://registry.modelcontextprotocol.io/v0/servers?version=latest`, fully paginated. Raw pages are archived in `data/frame/registry_snapshot/`.
- **Unit:** one remote endpoint (`server.remotes[].url`) of a server whose registry metadata says `status: "active"` and `isLatest: true`.
- **De-duplication:** by normalised URL (lower-case scheme and host; no query, fragment or trailing slash). The endpoint is probed at its **registered URL as written**.
- **Exclusions (counted and reported):**
  - URLs containing template variables (`{…}`);
  - invalid URLs;
  - non-HTTPS URLs;
  - hosts resolving to private, loopback, link-local or reserved addresses;
  - hosts in `optout.txt`.
- **Frame actually built (2026-10-12):**
  - 42,176 registry entries; 41,660 latest active servers;
  - 26,619 servers with remotes, giving 27,282 remote entries;
  - 283 excluded as templated and 634 duplicate URLs merged;
  - **26,365 frame endpoints** (`frame_sha256 ae90e534…`).
- **Sample:** if the frame has ≤ 5,000 endpoints, all are probed. Otherwise a simple random sample of **3,000** is drawn with `random.Random(20261012)`. The frame and sample are fixed by SHA-256 in `data/frame/*_meta.json`.
- **Other registries** (Smithery, Glama) are **not** included: Smithery needs an API key and Glama has no documented list API. This is a stated limitation.

## 3. Procedure

The harness is `harness/probe.py`, version recorded in each output. It is a dual-era client that follows the backward-compatibility procedure in MCP `2026-07-28` (Streamable HTTP §Backward Compatibility; Versioning §Backward Compatibility with Initialization-Based Versions).

| Step | Request | Condition |
|---|---|---|
| 1 | `POST server/discover`, with `MCP-Protocol-Version: 2026-07-28`, `Mcp-Method` and `_meta` (`protocolVersion`, `clientInfo`, `clientCapabilities`) | always |
| 2–3 | modern `tools/list`; modern `tools/call` on the non-existent tool `__glintbase_probe_nonexistent_tool__` | if step 1 shows a modern-only server: a `supportedVersions` result, or error code −32020/−32021 *(corrected by Deviation 2)* |
| 2 | legacy `initialize` (`protocolVersion: 2025-11-25`; retried once with `2025-03-26` if rejected with a JSON-RPC error) | otherwise |
| 3–5 | `notifications/initialized`, `tools/list`, canary `tools/call`, with `Mcp-Session-Id` and `MCP-Protocol-Version` where the negotiated revision defines them | if `initialize` returned a result |
| 6 | `GET` with `Accept: text/event-stream`, waiting ≤ 5 s for the HTTP+SSE `endpoint` event | if `initialize` got no JSON-RPC answer |
| 7–8 | `GET` the RFC 9728 protected-resource metadata: the URL from `WWW-Authenticate resource_metadata`, then `/.well-known/oauth-protected-resource{path}`, then the root | if any step returned 401 (or 403 with `WWW-Authenticate`) |

- **At most 8 requests per endpoint.** No real tool is called. No security payloads are sent.
- **Timeouts and pacing:** 10 s per request (5 s for the SSE detect step). Global concurrency 8, and **one endpoint per host at a time**. Up to 3 redirects are followed, and redirects to private addresses are refused.
- **Identity:** `User-Agent: GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot; research@glintbase.dev)`; MCP `clientInfo.name: GlintbaseResearch`.
- **Vantage point:** a single residential connection (the researcher's workstation); the public IP and ASN are recorded in `data/run_notes.md` at run time.

## 4. Outcome classification (`harness/classify.py`)

Exactly one primary status per endpoint, assigned in this order:

| Status | Rule |
|---|---|
| `excluded` | opt-out or private address at probe time |
| `unreachable` | every protocol request failed below HTTP (DNS, connect, TLS, timeout) |
| `auth_compliant` | 401 with a `Bearer` challenge **and** valid protected-resource metadata (`resource` string + non-empty `authorization_servers`) |
| `auth_noncompliant` | 401, or 403 + `WWW-Authenticate`, without that |
| `ok` | handshake succeeded (a `server/discover` or `initialize` result) **and** `tools/list` returned a `tools` array |
| `handshake_only` | handshake succeeded; `tools/list` did not |
| `modern_rejected` | modern error code, but no successful result |
| `legacy_sse` | HTTP+SSE `endpoint` event received (deprecated transport; not probed further) |
| `jsonrpc_error` | answered with JSON-RPC but rejected `initialize` in both versions |
| `payment_required` | HTTP 402 on the protocol requests (paid or disabled deployment) |
| `server_error` | 5xx or 429 on the protocol requests |
| `not_mcp` | anything else |

Secondary fields:
- era and protocol version;
- `supportedVersions`;
- capabilities and whether a session was issued;
- handshake latency;
- tool count and whether `tools/list` was paginated (**only the first page is analysed**);
- the share of tools with a strict schema (object `inputSchema` whose every property declares `type`/`enum`/`const`/`anyOf`/`oneOf`/`allOf`/`$ref`);
- the share of tools declaring `readOnlyHint` or `destructiveHint` as booleans, and the share with descriptions;
- whether the canary error came back in-channel, and its HTTP status;
- for auth-gated endpoints: whether the challenge is Bearer and whether the metadata is valid.

## 5. Rounds, validation, analysis

- **Round 1:** the full sample. **Round 2:** the same sample, same harness, at least 6 hours later on the same day (RQ6; a one-day study schedule). Headline numbers come from round 1.
- **Validation gate (before any number is published):**
  - draw 30 endpoints, stratified across primary statuses with seed `20261012`;
  - a reviewer re-checks each independently by hand (curl, following the spec) and from the raw logs;
  - **≥ 90% agreement is required.** Otherwise the classifier is fixed, all rounds are re-classified (or re-probed if the probe was at fault), and validation is repeated on a fresh draw.
- **Analysis (`harness/compute_stats.py`):** proportions with Wilson 95% intervals; RQ1 also broken down by registry transport type; RQ6 as percentage agreement and Cohen's κ. Denominators are always stated. No inferential tests are planned.
- **Host clustering:** some hosts publish hundreds of registry endpoints (pilot: one host had 276 of the first ~12k). Endpoint-level shares are the primary result. A **host-weighted sensitivity view** (each host counts once: the mean of within-host shares) is always reported next to them, along with the number of distinct hosts and the largest per-host count.
- **Era detail:** modern servers whose `supportedVersions` also list legacy revisions are reported as **dual-era**.
- **Reporting rules:**
  - every number in the report comes from `data/summary.json`;
  - per-endpoint published data contains derived fields only (`data/round_*.jsonl`); raw logs with body snippets (`data/raw/`) are not published;
  - no per-server "worst offender" lists.

## 6. Ethics

- Protocol and metadata requests only, with an honest identity and contact, an opt-out list (`optout.txt`, honoured within 24 h), per-host serialisation, and small volumes (≤ 8 requests per endpoint per round).
- Incidental security-relevant observations are reported privately to the maintainer (90-day window) and only in aggregate in the report.

## 7. Known limitations

- **One registry only:** listings are unvetted.
- **Short re-test interval:** ≥ 6 hours, so stability over days or weeks is not measured.
- **Single vantage point and two time points.**
- **First page of `tools/list` only.**
- **Deprecated HTTP+SSE servers** are detected but not handshaken.
- **Some "failures" may be deliberate:** for example, a server that requires headers declared in its registry entry (`declares_headers` is recorded in the frame).

## Deviations

1. **2026-10-12, before round 2 started. Re-test interval shortened from ≥ 6 h to immediately after round 1 finishes.**
   - **Reason:** the study timeline was compressed to one day at the researcher's request.
   - **Consequence:** RQ6 is reported as **re-test reliability** (agreement between two back-to-back rounds, under ~1 h apart), not as same-day stability of servers. It mainly measures the repeatability of the probe and very short-term flakiness. No other part of the protocol changes.

2. **2026-10-12, after round 1, before any analysis. Era-detection rule corrected; both rounds re-run in full.**
   - **What was wrong:** §3 treated `404` + JSON-RPC `-32601` on `server/discover` as a sign of a modern server. But MCP `2026-07-28` (Versioning §Protocol Version Negotiation) requires modern servers to implement `server/discover`, so that response identifies a **non-modern** server. The rule also stopped on `-32022` (UnsupportedProtocolVersion), where the spec tells a dual-era client to retry with a supported version.
   - **Fix:**
     - only a `DiscoverResult` or a `-32020`/`-32021` error marks a server as modern-only;
     - `404`/`-32601` and `-32022` now fall back to the legacy `initialize` handshake;
     - fixture tests were added for both cases.
   - **Impact found in round 1:** 271 endpoints (262 on one host) returned `404`/`-32601` and 2 returned `-32022`. All were classified `modern_rejected` without the legacy handshake being tried.
   - **Action:** the round-1 results and the partial round 2 (449 endpoints) were archived as discarded (`data/raw/_discarded/`), and both rounds were re-run in full on the same sample with the corrected harness. No result from the discarded runs was analysed.
