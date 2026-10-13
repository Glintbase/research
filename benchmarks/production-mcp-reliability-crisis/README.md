# Remote MCP Server Reliability

> **Status**: Data collected 2026-10-12/13. Draft report in [`reports/REPORT.md`](reports/REPORT.md); not yet published. Protocol and deviations: [`PREREGISTRATION.md`](PREREGISTRATION.md).
> **Authors**: Glintbase Research
> *(Folder name retained for link stability; the study title is neutral until data exists.)*

---

## Research Question

Among publicly listed **remote** Model Context Protocol servers, how often do the protocol basics an agent depends on actually work — handshake (including the `2026-07-28` revision and earlier revisions), anonymous discovery or a standards-compliant auth challenge, and in-channel error signalling?

## Population

Remote (HTTP) servers listed in the official MCP Registry (`registry.modelcontextprotocol.io`), Smithery, and Glama, de-duplicated by endpoint URL. Servers that only run locally (stdio) cannot be probed and are counted separately, not as failures. The sampling frame and snapshot date are recorded before probing.

## What the Probe Does — and Does Not Do

**Does (metadata and protocol only):**
1. Handshake with the current and previous protocol revisions.
2. `tools/list` (plus `prompts/list` / `resources/list` where advertised); record schema shape and annotations.
3. Call a deliberately non-existent tool to check that errors come back as JSON-RPC errors or `isError: true`.
4. For auth-gated servers: record whether a `WWW-Authenticate` challenge and OAuth protected-resource metadata are present.

**Does not:**
- Call real tools by default. An optional read-only call is limited to zero-argument tools the server itself annotates `readOnlyHint: true`.
- Send any SSRF, injection, or other security payloads. This is a reliability census, not a security test.

Any security issue noticed incidentally is reported privately to the maintainer first (90-day disclosure window) and is never published as a per-server list.

## Directory Layout (populated as the study runs)

- `harness/` — registry ingestion and batch probe runner
- `data/` — sampling frame snapshot, per-endpoint probe results
- `reports/` — whitepaper (written only after analysis)

## Running the harness

```bash
cd harness
pip install -r requirements.txt
python test_probe.py                          # fixture servers; must print ALL PASSED
python build_frame.py crawl                   # snapshot the official MCP Registry (resumable)
python build_frame.py frame                   # frame.csv + exclusion counts
python build_frame.py sample --n 3000 --seed 20261012
python probe.py --sample ../data/frame/sample.csv --round 1
python classify.py --round 1
python compute_stats.py --round 2 --retest 3 --sensitivity-exclude-host gateway.pipeworx.io
python figures.py                             # reports/figures/*.png from data/summary.json
```

See [`PREREGISTRATION.md`](PREREGISTRATION.md) for the frozen protocol and [`../../BOT.md`](../../BOT.md) for what the probe does and how to opt out.
