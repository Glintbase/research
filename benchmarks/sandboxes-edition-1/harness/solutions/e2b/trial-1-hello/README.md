# Trial 1: Hello Sandbox (E2B)

## Objective
The agent must:
1. Initialize an E2B sandbox.
2. Execute a Python script inside the sandbox that outputs `GLINT-HELLO-8492`.
3. Read the output.
4. Cleanly terminate/destroy the sandbox.

## Instructions
1. Copy `.env.example` to `.env` and set `E2B_API_KEY`.
2. Open this folder in Codex Desktop.
3. Paste the contents of `PROMPT.txt` into Codex.
4. Once Codex finishes, run:
   ```bash
   python verify.py
   ```
5. Fill in token stats and time in `run_log.json`.
