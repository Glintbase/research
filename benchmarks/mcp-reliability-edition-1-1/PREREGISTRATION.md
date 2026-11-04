# Pre-registration — Remote MCP Server Reliability, Edition 1.1 (4-week re-probe)

> **Status:** Frozen 2026-11-04 by commit on branch `research/l1-web-week`, before any request of this study was sent.
> Any change after freezing is listed under *Deviations* with date and reason.
> **Authors:** Glintbase Research · **Contact:** research@glintbase.dev
> **Parent study:** [Remote MCP Server Reliability (Edition 1)](../production-mcp-reliability-crisis/PREREGISTRATION.md). Everything not restated here follows Edition 1's pre-registration.
> **Programme:** `GLINTBASE_RESEARCH_PROGRAM_NOV2026.md` §5 E2 (internal).

## 1. Research questions (descriptive; no directional hypotheses)

- **RQ1 (change):** For the same 3,000 endpoints, did primary status, protocol era (modern `2026-07-28` vs legacy `initialize`), in-channel error signalling and auth compliance change between Edition 1 (2026-10-12) and now?
- **RQ2 (new features):** Among endpoints that complete a handshake, what share declare MCP extensions, and which? What share declare the Skills extension (`io.modelcontextprotocol/skills`) and answer `skills/list`?
- **RQ3 (Server Cards):** What share serve a Server Card at `<mcp-url>/server-card`, and what share of those pass the v1 required fields?
- **RQ4 (tool metadata):** Among endpoints that list tools anonymously, what share of tools carry any `annotations` object, and how large are tool input schemas (bytes per tool)?
- **RQ5 (re-test):** How stable is each endpoint's primary status between two rounds at least 20 h apart?

## 2. Sample

- **Paired sample:** the Edition 1 seeded sample, unchanged: `../production-mcp-reliability-crisis/data/frame/sample.csv`, 3,000 endpoints, drawn with `random.Random(20261012)` from the 2026-10-12 registry frame. Endpoints are probed at the same URL as in Edition 1.
- **No fresh-registry arm in this edition.** The programme's optional "fresh registry snapshot, reported separately" is dropped from this week to keep the probe schedule within the 7-day window and the network isolated (see §4). This is stated as a limitation.
- **Exclusions:** as Edition 1 (opt-out list, private addresses at probe time), counted and reported.

## 3. Procedure

- **Core probe:** Edition 1's `harness/probe.py` (harness 1.0.0), **imported and run unchanged** by `harness/probe_e11.py`: same steps, same order, same headers, identity, timeouts (10 s), global concurrency 8, one endpoint per host at a time, ≤ 3 redirects, private-address refusal. The only `tools/call` is Edition 1's non-existent canary `__glintbase_probe_nonexistent_tool__`. **No real tool is called.**
- **Metadata additions** (harness 1.1.0), after the core steps of an endpoint, kept in separate records so Edition 1's classifier receives identical input:
  1. *No new request:* extensions declared in `capabilities.extensions` of the `server/discover` result (modern) or `initialize` result (legacy) — per the Skills extension spec (`modelcontextprotocol/ext-skills`, `specification/beta/skills.mdx`, read 2026-11-04: servers declare `extensions["io.modelcontextprotocol/skills"]`).
  2. *No new request:* from the first page of `tools/list`: tools with a non-empty `annotations` object; tools with `outputSchema`; tools with `title`; compact UTF-8 JSON size of each `inputSchema`.
  3. *New request, conditional:* `skills/list` — **only** where the skills extension is declared **and** the handshake succeeded; sent in the endpoint's negotiated era (modern headers + `_meta`, or legacy with session ID and `MCP-Protocol-Version`).
  4. *New request:* `GET <mcp-url>/server-card` with `Accept: application/mcp-server-card+json, application/json;q=0.9` (the default hosted location in `modelcontextprotocol/ext-server-card` `docs/discovery.md`, as implemented in Glintbase's scanner). Skipped when every core request failed below HTTP.
- **Request cap:** additions are sent only while the endpoint's total stays **≤ 8 requests** (the Edition 1 cap); a skipped addition is recorded as `budget`.
- **Vantage point:** the researcher's workstation (same residential connection as Edition 1 unless the run notes say otherwise); public IP/ASN recorded in `data/run_notes.md` at round start.
- **Isolation:** no other study's traffic from this lane runs during an MCP round (Edition 1 Deviation 3). A per-minute connectivity log runs alongside each round (`data/connectivity_*.txt`). Traffic from other Glintbase lanes on the same connection can't be ruled out; any overlap noticed is recorded in the run notes.

## 4. Rounds

- **Round 1:** 2026-11-04 (programme Day 0/1). **Round 2:** the same sample and harness, started **≥ 20 h** after round 1 finished.
- **Headline:** round 1. Round 2 is the re-test (RQ5). Edition 1's comparison round is its published headline round (`round_2.jsonl`, 2026-10-12 17:24–17:53Z).
- **Interval to Edition 1:** about 3.5 weeks (programme §10.6), not 4.

## 5. Classification and measures

- **Primary status:** Edition 1's `classify.py`, unchanged, applied to the core step records.
- **New fields (`harness/classify_e11.py`):** `extensions[]`, `declares_skills`, `skills_list_ok` (result with a `skills` array), `skill_count`, `server_card_status`, `server_card_json`, `server_card_valid_v1` (`$schema` containing "server-card", non-empty `name`, `version`, `description` — the v1 required fields used by Glintbase's scanner), `pct_tools_annotated`, `pct_tools_output_schema`, `schema_bytes_median`, `schema_bytes_max`, `schema_bytes_total`.

## 6. Analysis (`harness/compute_stats.py`; every published number comes from `data/summary.json`)

- Proportions with **Wilson 95% intervals**, denominators always stated.
- **RQ1 (paired, Edition 1 headline round vs this round 1), McNemar's exact test** on each binary outcome among endpoints classified (not excluded) in both:
  - `ok` (handshake + tools listed);
  - modern era (`era == "modern"`) among endpoints with a handshake in both rounds;
  - `error_in_channel` among endpoints with a canary answer in both rounds;
  - `auth_compliant` among endpoints `auth_*` in both rounds.
  Discordant counts are reported. Also a full status transition table.
- **RQ2–RQ4:** shares with Wilson CIs among `ok` endpoints (and among all handshaken endpoints for extensions); schema bytes as median / p90 / max per tool and per endpoint.
- **RQ5:** percentage agreement and Cohen's κ between round 1 and round 2 primary status.
- **Host clustering:** as Edition 1 — endpoint-level shares are primary; a host-weighted view, number of distinct hosts and largest per-host count are reported alongside.
- **Comparison with Kin Lane's probe** (44 of 1,450 endpoints on `2026-07-28`; vendor post, labelled "vendor") is descriptive only; different frames and dates.

## 7. Validation gate

- 30 endpoints drawn with seed `20261104`, stratified across round-1 primary statuses (and including every endpoint that declares skills or serves a card, up to 6 of the 30).
- Each is re-checked by an independent sequential client written for the check (Node `fetch`, following the spec by hand) plus the raw logs; recorded in `data/validation.csv` with agreement on primary status and on the new fields.
- **≥ 90% agreement** on primary status and on `server_card_valid_v1` / `declares_skills` is required; otherwise fix, re-classify (or re-probe), and re-validate on a fresh draw.
- Sign-off: the founder (sole reviewer) spot-checks 5 of the 30 and signs with name, date and scope (queued in `REVIEW_QUEUE.md`). Publication waits for it.

## 8. Ethics

As Edition 1: protocol and metadata only, honest identity, opt-out honoured, ≤ 8 requests per endpoint per round, no real tool calls, no security payloads, no per-server "worst offender" lists. Incidental security observations go privately to the maintainer (90-day window). Named vendors in the report get a 7-day right of reply before publication.

## 9. What this can't claim

Same as Edition 1 (one registry, unvetted listings, first page of `tools/list` only, single vantage point), plus: a ~3.5-week interval is not a trend; a declared extension says nothing about whether skills are useful; Server Cards may also be published via an AI Catalog, which this study doesn't fetch, so card prevalence is a lower bound.

## Deviations

*(none yet)*
