# Errata & Corrections: Sandboxes Edition 1

> **Correction date**: 2026-10-12
> **Scope**: `REPORT_SANDBOXES_EDITION_1.md`, `METHODOLOGY.md`, `GOTCHAS_AND_TRAPS.md`, `DAYTONA_AGENT_EXECUTION_TRACE.md`, this folder's `README.md`, `distribution/DISTRIBUTION_KIT_3DAY_LAUNCH.md`, and the `verify.py` harness files.
> **Method**: Every correction below was checked against the files published in this folder. No benchmark was re-run and no new trial data was produced. Where the evidence cannot settle a question, we say so.

The original documents remain in place. Each corrected passage carries an inline `Correction (2026-10-12)` note pointing here.

---

## Which source is authoritative

The published numbers came from four places that disagree with each other:

| Source | Who wrote it | Human stops (Modal / E2B / boat / Vercel / Daytona) | Stumbles (same order) |
|---|---|---|---|
| `transcripts/*/*/transcript.jsonl` | Recorded by the agent runtime during the trial | **0 / 0 / 0 / 0 / 0** (each of the 30 transcripts has exactly one user turn, and every prompt ends "Do not ask questions") | not counted in the transcripts |
| `harness/solutions/*/*/run_log.json` | Written by the agent at the end of each trial | 0 / 0 / 0 / 0 / 0 | 0 / 0 / 1 / 0 / 0 |
| `data/integration_tax_summary.json` | Generated from the run logs | 0 / 0 / 0 / 0 / 0 | 0 / 0 / 1 / 0 / 0 |
| `data/benchmark_master.csv` / `.json`, report, README | Edited by hand after the runs | 1 / 0 / 1 / 1 / 0 | 0 / 0 / 1 / 0 / 1 |

**From now on, the transcripts are the authoritative record.** Where a published claim is not supported by a transcript, it has been labelled or corrected. The raw rows in `data/benchmark_master.*` were left unchanged so the original publication can still be audited. Corrected values are listed in [`data/trial_corrections.csv`](data/trial_corrections.csv).

**Corrected counts**
- **Human stops: 0 for every provider.** The published counts were Modal 1, boat 1, Vercel 1. No transcript records a human intervention. If any setup work happened outside the transcripts (for example creating credentials or adding a card), it was not recorded, so it cannot be verified.
- **Stumbles: boat 1, all others 0, as recorded in the run logs.** The published Daytona stumble (HTTP 401) has no transcript evidence and is corrected to 0. The only in-band failure recorded in Daytona Trial 4 is a leftover sandbox caused by an asynchronous delete (E5), not a 401. The boat stumble is real. Its cause was a `pip` `externally-managed-environment` (PEP 668) error in Trial 2, not an HTTP 402. We did not recount stumbles from the transcripts. The transcripts show more in-band failures than the published counts include, for example a missing `test/test_all.py` in Trial 6 on boat, Daytona, E2B and Vercel.

---

## E1. Prompts were not identical across providers (R-03)

The report said every sandbox got "the identical prompt (`PROMPT.txt`)". **That was not true.** All 30 `harness/solutions/*/*/PROMPT.txt` files differ:

- **Modal and boat prompts spell out the exact API calls.** Modal prompts give `modal.App.lookup(..., create_if_missing=True)`, `encrypted_ports=[8000]`, `sb.tunnels()` and `sb.terminate()`. boat prompts give the client setup, `api.create(...)`, `api.host_port(...)` and the full `nohup` server command.
- **E2B and Vercel prompts are mostly plain language.** They give a few method hints, such as `sandbox.get_host(8000)` for E2B and `ports=[8000]` / `sandbox.routes` for Vercel. The Vercel Trial 1 prompt names all three credential variables.
- **The Daytona prompts name the client constructor.** The Trial 4 prompt names `sb.create_signed_preview_url(8000, 300)`.

Some providers got prompts that already contained the working calls, so the steps, tokens and Integration Tax ranking is **not a controlled comparison**. Read it as indicative only.

## E2. Traps described without transcript evidence (R-04)

We searched all 30 transcripts for each error string the documents quote.

| Claimed trap | Evidence in published transcripts | Status |
|---|---|---|
| boat: `HTTP 402 Payment Required` card gate (Trial 2) | No transcript contains "402" as an HTTP status or "Payment Required" | **Not captured in the published transcripts.** Removed from headline and summary claims. |
| boat: PEP 668 `externally-managed-environment` (Trial 2) | Present in `transcripts/boat/trial-2-install` | Captured |
| Modal: `AuthError: Token ID is malformed` with `wk-` keys | No transcript contains "malformed". Modal Trial 1 succeeded on its first run. | **Not captured in the published transcripts** |
| Modal: `Sandboxes must be associated with an App` | Error not present. Every Modal prompt already gave the `App.lookup` call. | **Not captured** (the fix was supplied in the prompt) |
| Vercel: `Missing teamId or projectId`, human asked for IDs | Error not present. The Trial 1 prompt names `VERCEL_TOKEN`, `VERCEL_PROJECT_ID` and `VERCEL_TEAM_ID`, and the agent read them from `.env`. | **Not captured.** The three-credential requirement is real (it appears in the SDK and the prompt). The "human stop" is not. |
| Daytona: HTTP 401 on the default preview URL | No HTTP 401 in any Daytona transcript (the only "401" matches are inside the marker `GLINT-DAYTONA-4019`). The Trial 4 prompt named `create_signed_preview_url`. | **Not captured.** Daytona Trial 4 had 0 stumbles, matching `DAYTONA_AGENT_EXECUTION_TRACE.md`. |
| Daytona: `TypeError: object of type 'generator' has no len()` | Not present | **Not captured** |
| E2B: blocking `commands.run` for a server | No hang or timeout recorded. The agent used `background=True` from the start. | **Not captured** |

## E3. Tokens, steps and wall time were self-reported (R-05)

The `tokens`, `steps_count` and `wall_time_seconds` fields in every `run_log.json`, and so in `data/benchmark_master.*` and the Integration Tax, were **typed in by the agent itself** at the end of each trial. The harness did not measure them. The transcripts show the agent reading earlier trials' `run_log.json` files just before writing its own values. For example, `transcripts/e2b/trial-6-real-job` steps 23–53 read the Trial 4 and Trial 5 logs and then write Trial 6. Some values were carried over or modelled on earlier trials rather than measured. The transcripts contain no token-usage fields, so token counts cannot be checked.

`harness/measure_transcripts.py` derives what the transcripts can support and writes [`data/measured_metrics.csv`](data/measured_metrics.csv):

| Provider | Self-reported median steps | Measured median model turns | Measured median tool calls | Measured median session length |
|---|---:|---:|---:|---:|
| Modal | 3.0 | 12.5 | 9.5 | 187 s |
| E2B | 3.5 | 28.0 | 26.5 | 303 s |
| boat | 3.0 | 18.5 | 17.0 | 328 s |
| Vercel | 5.0 | 27.5 | 25.5 | 403 s |
| Daytona | 5.0 | 22.0 | 20.0 | 486 s |

The measured counts are 3 to 8 times the self-reported "steps", and they rank the providers differently. On measured turns, E2B goes from the fewest steps to the most. Session length covers the whole agent session, including waits on background tasks, so it is not the `python solution.py` latency defined in METHODOLOGY §5.6. The two columns are not expected to match.

## E4. Trial 6 pass rate: 30/30 corrected to 28/30 (R-06)

- `test/test_all.py` **does not exist** in the current `bottlepy/bottle` repository. The boat, Daytona, E2B and Vercel transcripts all record `can't open file '.../test/test_all.py': [Errno 2] No such file or directory`.
- The Modal and boat `solution.py` files print `TEST_SUITE_FINISHED` **whatever happens**. The Modal run printed only the marker, with no test output. The boat run printed the missing-file error and then the marker.
- The Modal, E2B, Vercel and Daytona `verify.py` files also passed if the words `passed` or `ok` appeared anywhere in stdout. The boat verifier checked only for the marker.

| Provider | Trial 6 evidence in transcript | Published | Corrected |
|---|---|---|---|
| Modal | Marker only, no test output | Pass | **Not passed** (no evidence any test ran) |
| boat | `test_all.py` missing, then marker | Pass | **Not passed** |
| E2B | `pytest`: `363 passed` | Pass | Pass |
| Vercel | Agent-written discovery runner: `Ran 363 tests ... OK` | Pass | Pass (with the caveat that the agent wrote the runner) |
| Daytona | Agent-written discovery runner: `Ran 373 tests ... OK (skipped=1)` | Pass | Pass (same caveat) |

**Overall pass rate: 100% (30/30) → 93.3% (28/30).** By provider: Modal 100% → 83.3% (5/6), boat 100% → 83.3% (5/6), others unchanged.

Applying the published penalty formula (`1 + (100 − pass rate)/50` = 1.333) to the unchanged, self-reported medians gives:

| Provider | Published IT (rank) | Corrected IT (rank) |
|---|---|---|
| E2B | 1.17x (#2) | 1.17x (#1) |
| Vercel | 1.37x (#4) | 1.37x (#2, 1.367) |
| Modal | 1.03x (#1) | 1.37x (#3, 1.375) |
| Daytona | 1.43x (#5) | 1.43x (#4) |
| boat | 1.21x (#3) | 1.61x (#5) |

These corrected figures still rest on self-reported medians (E3) and non-identical prompts (E1). They are not a new ranking. The visuals in `visuals/` show the original numbers and were not regenerated.

**Verifier fix.** All five `harness/solutions/*/trial-6-real-job/verify.py` files now need the `TEST_SUITE_FINISHED` marker **and** a real test summary: a unittest `Ran N tests ...` (N > 0) followed by `OK`, or a pytest `N passed` with no failures or errors. Checked against the outputs in the transcripts, the new check rejects the Modal and boat runs and accepts the E2B, Vercel and Daytona runs.

## E5. "0 leaked sandboxes" could not have been detected (R-07)

Every published `verify.py` handled leftover sandboxes like this:
1. If any sandboxes were still listed after the run, it printed a `[WARN]`, **deleted them, and still reported the trial as passed**.
2. If the listing call raised an error, it printed `[INFO]` and still passed.

So a passing `verify.py` could not tell us anything about leaks. The claims "0 leaked sandboxes" and "100% clean teardown" are **not supported by the published verifier**. They are now marked "not verifiable".

The transcripts show this happening once. In `transcripts/daytona/trial-4-serve` (step 71), the first `verify.py` run printed `[WARN] Warning: Detected 1 active sandboxes after execution!`, deleted that sandbox, and then printed `VERIFICATION PASSED`. The cause was an asynchronous `client.delete(sb)`. The agent changed it to `delete(..., wait=True)`, and the re-run reported 0 leaks. The trial was recorded as "0 leaks, 0 stumbles". Under the corrected verifier, that first run would have failed. No other transcript records a leak warning, but any leak that was cleaned up silently in an unrecorded verifier run cannot be ruled out.

**Verifier fix.** All 30 `verify.py` files now print `[FAIL] Leak check FAILED` and exit non-zero when sandboxes remain. They still clean up after reporting so billing stops. A leak check that cannot run now also fails instead of passing silently.

## E6. Per-trial tables vs. the CSV (R-12)

The per-provider scorecards in the report disagree with `data/benchmark_master.csv` in two rows:

| Row | Report table | CSV / run_log |
|---|---|---|
| boat Trial 3 tokens | 2,760 | 4,745 |
| Vercel Trial 1 tokens / steps | 2,100 / 5 | 1,700 / 3 |

The medians and totals in the leaderboards match the CSV, not the per-trial tables. The boat total of 26,598 tokens is the **sum of all six boat trials** in the CSV. It is not the cost of the Trial 2 retry, which the agent reported as 12,603 tokens. The boat median (2,580) is across all six trials, not "five healthy trials".

## E7. Front-door ARS scores in the folder README (R-13)

The README leaderboard listed Front-Door ARS as Modal 89, E2B 31, boat 82, Vercel 58, Daytona 54. The Phase 1 scans in `data/phase1-scans/*.json` (`score` field) and the report give **Modal 36, E2B 75, boat 82, Vercel 69, Daytona 48**. The README now uses the scan values. Scores from *State of Agent Readiness 2026* (for example E2B 31, Modal 47, Vercel 67 in that dataset) come from a different scanner and a different scale and must not be mixed with these.

## E8. Other corrections (R-14 to R-17)

- **"The 5 Key Empirical Takeaways"** listed six items. The heading now says six.
- **Broken relative links** in the report (`./benchmark_master.json`, `./visual*.png`, `./phase1-scans/phase1_frontdoor_report.md`, `sandbox-benchmark/...`) now point to `../data/`, `../visuals/`, `../data/phase1-scans/` and `../harness/solutions/`. `phase1_frontdoor_report.md` was never published, so the link points to the raw scan JSON instead.
- **Paths in the dataset.** `solution_file` and `verify_file` in `data/benchmark_master.*` use pre-publication folder names (`modal-sandbox/`, `pilot-e2b/`, …). The published files are under `harness/solutions/{modal,e2b,boat,vercel,daytona}/`. Every `transcript_uri` in `benchmark_master.json` contains `None/None` (the CSV has the correct URIs). The raw rows were left unchanged.
- **Contact email**: `research@glintbase.com` → `research@glintbase.dev`.
- **Daytona trace, Trial 6**: the trace said the suite "ran all 182 unit tests in 1.48 seconds". The transcript shows `Ran 373 tests in 0.194s, OK (skipped=1)`. The trace also said Modal and boat "executed through the direct path specified in their prompts". In fact neither ran any tests (E4).
- **Daytona trace, tokens**: the trace said tokens were "measured and reported by the Antigravity agent runtime". They were self-reported by the agent (E3).

## E9. Distribution kit corrections (R-17)

The launch kit has been annotated. Main factual errors:
- **26,598 tokens** was presented as the cost of the boat payment-gate retry loop. It is boat's total across all six trials, and the 402 gate itself is not captured (E2, E6).
- **Daytona signed URL**: the kit said the method was "not explicit in the agent's prompt context" and gave the call as `create_signed_preview_url(port=8000, duration=300)`. The Trial 4 prompt named the method. The call used was `sb.create_signed_preview_url(8000, 300)`, and the second parameter is `expires_in_seconds`. No 401 loop is recorded.
- **Vercel "OIDC token"**: the trials used `VERCEL_TOKEN` (an access token), `VERCEL_PROJECT_ID` and `VERCEL_TEAM_ID`. `VERCEL_OIDC_TOKEN` appears only in SDK source code the agent read. No "SDK throws on OIDC" error and no human stop are recorded.
- **"We probed process tables, checked container runtimes, and monitored dangling network listeners"**: the verifier only called each provider's sandbox-listing API, and it could not report leaks (E5).
- The **100% pass rate**, **zero human stops for E2B only**, **$35 in 90 seconds** and **"pytest" on every provider** claims are not supported by the data. Only E2B ran `pytest`.

## E10. Redactions (R-01 / R-02)

Live-looking Modal credentials (`MODAL_TOKEN_ID=wk-…`, `MODAL_TOKEN_SECRET=ws-…`) appeared in 16 transcript files under `transcripts/` and `harness/solutions/` (Daytona Trials 2 and 5, E2B Trial 5 and Vercel Trial 1, in both `.jsonl` and `.md`, in both copies). They have been replaced with `[REDACTED]`. A `git status` listing of an unrelated private repository in `boat/trial-6-real-job` (`transcript.jsonl` and `transcript_readable.md`, both copies) has been replaced with `[redacted: unrelated private repository listing]`. Redaction in the working tree does not remove the values from git history. Key rotation and a history purge are being handled separately.
