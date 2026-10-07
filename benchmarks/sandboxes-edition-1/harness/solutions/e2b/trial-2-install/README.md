# Trial 2: Install & Run (E2B)

## Objective
The agent must:
1. Initialize an E2B sandbox.
2. Install a dependency (`polars`) inside the sandbox.
3. Run a Python script utilizing `polars` that calculates and outputs `SUM:60`.
4. Read the output and cleanly close the sandbox.

## Instructions
1. Copy `.env.example` to `.env` and set `E2B_API_KEY`.
2. Open this folder in Codex Desktop.
3. Paste the contents of `PROMPT.txt` into Codex.
4. Once Codex finishes, run:
   ```bash
   python verify.py
   ```
5. Fill in token stats and time in `run_log.json`.
