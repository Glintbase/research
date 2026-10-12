# Summary — round pilot

Sample endpoints: 25 · analysed: 25 · excluded: {}

## RQ1 Primary status

| Status | Share |
|---|---|
| ok | 56.0% (14/25; 95% CI 37.1–73.3) |
| handshake_only | 0.0% (0/25; 95% CI 0.0–13.3) |
| auth_compliant | 28.0% (7/25; 95% CI 14.3–47.6) |
| auth_noncompliant | 8.0% (2/25; 95% CI 2.2–25.0) |
| modern_rejected | 0.0% (0/25; 95% CI 0.0–13.3) |
| legacy_sse | 0.0% (0/25; 95% CI 0.0–13.3) |
| jsonrpc_error | 0.0% (0/25; 95% CI 0.0–13.3) |
| payment_required | 8.0% (2/25; 95% CI 2.2–25.0) |
| server_error | 0.0% (0/25; 95% CI 0.0–13.3) |
| not_mcp | 0.0% (0/25; 95% CI 0.0–13.3) |
| unreachable | 0.0% (0/25; 95% CI 0.0–13.3) |

Hosts: 24 (max 2 endpoints on one host). Host-weighted shares: ok 58.3%, auth_compliant 29.2%, auth_noncompliant 8.3%, payment_required 4.2%

- Reachable: 100.0% (25/25; 95% CI 86.7–100.0)
- Speaks MCP (any protocol answer or MCP auth challenge): 92.0% (23/25; 95% CI 75.0–97.8)

## RQ2 Protocol era

Completed handshakes: 14
- Modern (2026-07-28) support: 35.7% (5/14; 95% CI 16.3–61.2)
- Dual-era (modern + legacy) among modern: 60.0% (3/5; 95% CI 23.1–88.2)
- Legacy negotiated versions: 2025-11-25: 88.9% (8/9; 95% CI 56.5–98.0), 2025-06-18: 11.1% (1/9; 95% CI 2.0–43.5)
- Legacy servers issuing sessions: 22.2% (2/9; 95% CI 6.3–54.7)
- Median handshake latency: 507.0 ms

## RQ3 Auth

- Auth-gated endpoints: 36.0% (9/25; 95% CI 20.2–55.5)
- Compliant challenge (Bearer + RFC 9728 metadata): 77.8% (7/9; 95% CI 45.3–93.7)
- Bearer challenge present: 88.9% (8/9; 95% CI 56.5–98.0)
- Valid protected-resource metadata: 77.8% (7/9; 95% CI 45.3–93.7)

## RQ4 Tools (among `ok` endpoints)

- `ok` endpoints: 14
- Zero tools listed: 0.0% (0/14; 95% CI 0.0–21.5)
- Median tool count: 6.5
- All tools strictly typed: 100.0% (14/14; 95% CI 78.5–100.0)
- Any readOnlyHint declared: 85.7% (12/14; 95% CI 60.1–96.0)
- Any destructiveHint declared: 85.7% (12/14; 95% CI 60.1–96.0)
- All tools described: 100.0% (14/14; 95% CI 78.5–100.0)

## RQ5 In-channel errors

- Canary answered over HTTP: 14
- Error returned in-channel: 100.0% (14/14; 95% CI 78.5–100.0)

