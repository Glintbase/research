# Trial 5: Break It (Resilience & Error Recovery on E2B)

## Objective
The agent must:
1. Initialize an E2B sandbox.
2. Trigger an intentional runtime error (e.g. `1 / 0`).
3. Handle and print the caught error.
4. Execute a subsequent healthy command that prints `HEALTHY-RECOVERY-77`.
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
