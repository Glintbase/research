# Summary — round 2 + retest 3

Sample endpoints: 3000 · analysed: 3000 · excluded: {}

## RQ1 Primary status

| Status | Share |
|---|---|
| ok | 56.9% (1708/3000; 95% CI 55.2–58.7) |
| handshake_only | 0.4% (11/3000; 95% CI 0.2–0.7) |
| auth_compliant | 24.2% (726/3000; 95% CI 22.7–25.8) |
| auth_noncompliant | 5.1% (152/3000; 95% CI 4.3–5.9) |
| modern_rejected | 0.0% (1/3000; 95% CI 0.0–0.2) |
| legacy_sse | 0.5% (15/3000; 95% CI 0.3–0.8) |
| jsonrpc_error | 0.5% (16/3000; 95% CI 0.3–0.9) |
| payment_required | 2.1% (64/3000; 95% CI 1.7–2.7) |
| server_error | 1.4% (43/3000; 95% CI 1.1–1.9) |
| not_mcp | 4.1% (122/3000; 95% CI 3.4–4.8) |
| unreachable | 4.7% (142/3000; 95% CI 4.0–5.6) |

Hosts: 2245 (max 261 endpoints on one host). Host-weighted shares: ok 48.1%, handshake_only 0.2%, auth_compliant 30.5%, auth_noncompliant 6.4%, legacy_sse 0.6%, jsonrpc_error 0.6%, payment_required 1.2%, server_error 1.8%, not_mcp 4.3%, unreachable 6.2%

- Reachable: 95.3% (2858/3000; 95% CI 94.4–96.0)
- Speaks MCP (any protocol answer or MCP auth challenge): 87.1% (2613/3000; 95% CI 85.9–88.3)

## RQ2 Protocol era

Completed handshakes: 1772
- Modern (2026-07-28) support: 13.3% (235/1772; 95% CI 11.8–14.9)
- Dual-era (modern + legacy) among modern: 25.1% (59/235; 95% CI 20.0–31.0)
- Legacy negotiated versions: 2025-11-25: 50.0% (768/1537; 95% CI 47.5–52.5), 2025-03-26: 32.2% (495/1537; 95% CI 29.9–34.6), 2025-06-18: 12.2% (188/1537; 95% CI 10.7–14.0), 2024-11-05: 4.7% (72/1537; 95% CI 3.7–5.9), 2026-07-28: 0.9% (14/1537; 95% CI 0.5–1.5)
- Legacy servers issuing sessions: 17.1% (263/1537; 95% CI 15.3–19.1)
- Median handshake latency: 418.0 ms

## RQ3 Auth

- Auth-gated endpoints: 29.3% (878/3000; 95% CI 27.7–30.9)
- Compliant challenge (Bearer + RFC 9728 metadata): 82.7% (726/878; 95% CI 80.0–85.0)
- Bearer challenge present: 88.2% (774/878; 95% CI 85.8–90.1)
- Valid protected-resource metadata: 84.6% (743/878; 95% CI 82.1–86.9)

## RQ4 Tools (among `ok` endpoints)

- `ok` endpoints: 1708
- Zero tools listed: 0.1% (2/1708; 95% CI 0.0–0.4)
- Median tool count: 9.0
- All tools strictly typed: 98.7% (1683/1706; 95% CI 98.0–99.1)
- Any readOnlyHint declared: 56.7% (967/1706; 95% CI 54.3–59.0)
- Any destructiveHint declared: 50.5% (861/1706; 95% CI 48.1–52.8)
- All tools described: 100.0% (1706/1706; 95% CI 99.8–100.0)

## RQ5 In-channel errors

- Canary answered over HTTP: 1773
- Error returned in-channel: 75.1% (1331/1773; 95% CI 73.0–77.0)

## RQ6 Re-test reliability (back-to-back rounds; see Deviation 1)

- Paired endpoints: 3000
- Same primary status: 93.4% (2801/3000; 95% CI 92.4–94.2)
- Cohen's κ: 0.895

Excluding sha256:54b786edf0f9: same status 99.6% (2796/2806; 95% CI 99.3–99.8), κ 0.994

