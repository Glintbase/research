# Trial 4: Serve It (Ingress Networking on E2B)

## Objective
The agent must:
1. Initialize an E2B sandbox.
2. Launch an HTTP server on port 8000 inside the sandbox returning `GLINT-SERVER-OK` at `/`.
3. Reach the port externally (e.g. via `sandbox.get_host(8000)`) and fetch the response.
4. Output the confirmation and cleanly close the sandbox.

## Instructions
1. Copy `.env.example` to `.env` and set `E2B_API_KEY`.
2. Open this folder in Codex Desktop.
3. Paste the contents of `PROMPT.txt` into Codex.
4. Once Codex finishes, run:
   ```bash
   python verify.py
   ```
5. Fill in token stats and time in `run_log.json`.
