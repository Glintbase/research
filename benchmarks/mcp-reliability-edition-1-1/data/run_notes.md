# Run notes — Edition 1.1

- Pre-registration frozen: commit 3ddbc9e (2026-11-04), pushed to origin/research/l1-web-week before round 1
- Vantage point: researcher workstation, residential connection — 105.112.205.10, AS36873 Airtel Networks Limited NG (same ASN as Edition 1)
- Round 1 started: 2026-11-04T06:41Z (connectivity log: data/connectivity_round1.txt)
- Workstation idle-slept 06:50–20:14Z (Deviation 1); round 1 first pass finished 2026-11-04T20:56:31Z
- Deviation 1 re-probe: 272 endpoints (8 in flight across the sleep, 264 started 20:14–20:16Z) archived to raw/_discarded/round_1_sleep/ and re-probed 20:56–21:00:56Z
- **Round 1 finished: 2026-11-04T21:00:56Z.** Round 2 may start from 2026-11-05T17:01Z (≥ 20 h)
- Validation (30 endpoints, seed 20261104, independent Node checker, 1 sequential connection): 21:01–21:08Z
  - checker v1 had a bug (labelled -32020 rejections as handshake_only); its output is kept as validation_check_v1_checker_bug.json; fixed and re-run in full
  - result: primary status 28/30 (93.3%), server_card_valid_v1 29/30, declares_skills 30/30; both disagreements are server-side changes (see validation.csv). Gate (≥ 90%) passed, pending founder spot-check of 5.
- Other lanes: L3 reported degraded network to E2B from this host on Nov 4; it may have run E2B traffic during round 1's second session.
