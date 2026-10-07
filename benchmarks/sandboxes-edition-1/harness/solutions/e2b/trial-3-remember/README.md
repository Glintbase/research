# Trial 3: Remember Me (State Persistence on E2B)

## Objective
The agent must:
1. Initialize an E2B sandbox.
2. In command 1, write `STATE-PERSIST-991` to `/tmp/state.txt`.
3. In a separate, subsequent command execution on the same sandbox, read and print `/tmp/state.txt`.
4. Return the output and cleanly close the sandbox.

## Instructions
1. Copy `.env.example` to `.env` and set `E2B_API_KEY`.
2. Open this folder in Codex Desktop.
3. Paste the contents of `PROMPT.txt` into Codex.
4. Once Codex finishes, run:
   ```bash
   python verify.py
   ```
5. Fill in token stats and time in `run_log.json`.
