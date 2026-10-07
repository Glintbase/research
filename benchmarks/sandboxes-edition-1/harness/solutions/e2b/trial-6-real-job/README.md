# Trial 6: Real Job (SWE Workload on E2B)

## Objective
The agent must:
1. Initialize an E2B sandbox.
2. Clone `https://github.com/bottlepy/bottle`.
3. Install pytest or run `python test/test_all.py` inside the sandbox.
4. Output the final test status containing `TEST_SUITE_FINISHED` or test pass summary.
5. Cleanly close the sandbox.

## Instructions
1. Copy `.env.example` to `.env` and set `E2B_API_KEY`.
2. Open this folder in Codex Desktop.
3. Paste the contents of `PROMPT.txt` into Codex.
4. Once Codex finishes, run:
   ```bash
   python verify.py
   ```
5. Fill in token stats and time in `run_log.json`.
