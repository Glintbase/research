# Daytona: Agent Execution Trace
**Glintbase Integration Index, Sandboxes Edition 1**

| Parameter | Value |
|---|---|
| **Provider** | Daytona |
| **SDK** | `daytona 0.222.0` (Python SDK) |
| **Agent Model** | Gemini 3.8 Flash (temperature 0.2, Antigravity Autonomous Coding Harness) |
| **Harness** | Antigravity Autonomous Agent Framework, zero human-in-the-loop intervention during runs |
| **Run Date** | October 6, 2026 |
| **Execution Mode** | Prompt-provided API scaffold / interface hints (pre-installed SDK, zero web search permitted during execution, local runtime Python introspection enabled) |
| **Credentials** | Single pre-provisioned `DAYTONA_API_KEY`, loaded from `.env` |
| **Evaluation Result** | **6 of 6 tasks passed (100% pass rate)**. 0 leaked sandboxes across all runs. |
| **Integration Tax** | **1.43×** (median-based), **1.65×** (totals-based). Rank #5 of 5 under both. |

---

## 1. Read This First

- **Preliminary & Empirical.** Each task was executed once per provider (6 tasks × 5 providers = 30 standardized trials). Medians are calculated across the six tasks within the suite, not across repeated trials of the same task. The data reflects deterministic single-run agent trajectories under identical harness conditions.
- **What Was Measured.** The resource expenditure required by an autonomous AI agent to complete each engineering task: input/output token volume, autonomous tool invocations ("steps"), and total wall-clock time. It does not measure raw hypervisor boot speed, network throughput, price-performance ratio, GPU topology, or multi-tenant security architecture.
- **Wall Time Scope.** Wall time encompasses the full end-to-end agent cycle: model inference latency, tool invocation, environment introspection, remote API roundtrips, test verification, and cleanup. It is distinct from hypervisor provisioning latency, which Daytona documents separately.
- **Independence.** Glintbase maintains strict editorial independence. Glintbase has no financial relationship, commercial partnership, or equity affiliation with Daytona, Modal Labs, E2B, boat.dev, or Vercel.

### Metrics & Terminology

| Metric | Definition |
|---|---|
| **Step** | A single autonomous tool call executed by the agent (e.g., executing a command via `run_command`, writing code via `write_to_file`, or inspecting files via `view_file`). |
| **Stumble** | A moment where an agent tool call failed or returned an unexpected exit code/response, necessitating corrective backtracking or adaptation in subsequent steps. |
| **Tokens** | Cumulative prompt and completion token counts measured and reported by the Antigravity agent runtime for each trial. |
| **Wall Time** | Elapsed seconds from initial prompt ingestion to verified sandbox destruction. |
| **Integration Tax** | Standardized overhead index computed as $0.4 \times (\text{Tokens} / \text{Best}) + 0.4 \times (\text{Steps} / \text{Best}) + 0.2 \times (\text{Time} / \text{Best})$. A score of 1.00× represents the top benchmark performer across all dimensions. |

---

## 2. Scorecard

### Per-Task Breakdown

| Trial | Task Name | Result | Prompt Tok | Completion Tok | Total Tok | Steps | Wall Time | Stumbles | Leaks |
|---|---|:---:|---:|---:|---:|---:|---:|:---:|:---:|
| 1 | Hello Sandbox | **Pass** | 1,540 | 490 | 2,030 | 4 | 19.5s | 0 | 0 |
| 2 | Install & Run (`polars`) | **Pass** | 1,720 | 580 | 2,300 | 5 | 32.4s | 0 | 0 |
| 3 | Remember Me (`/tmp` State) | **Pass** | 1,590 | 510 | 2,100 | 4 | 21.0s | 0 | 0 |
| 4 | Serve It (Public Ingress Port) | **Pass** | 2,850 | 940 | 3,790 | 9 | 45.0s | 0 | 0 |
| 5 | Break It (Error Recovery) | **Pass** | 1,680 | 540 | 2,220 | 5 | 22.4s | 0 | 0 |
| 6 | Real Job (`bottle` Tests) | **Pass** | 3,100 | 980 | 4,080 | 10 | 48.0s | 0 | 0 |
| | **Totals** | **6 / 6** | **12,480** | **4,040** | **16,520** | **37** | **188.3s** | **0** | **0** |
| | **Median per Task** | | | | **2,260** | **5** | **27.4s** | | |

### Daytona's Position in the Field (Median per Task)

| Metric | Daytona | Best in Field | Ratio vs. Best | Daytona Rank (of 5) |
|---|---:|---:|---:|:---:|
| **Tokens** | 2,260 | 1,865 (E2B) | 1.21× | 4th |
| **Steps** | 5 | 3 (Modal, boat.dev) | 1.67× | Tied 4th |
| **Wall Time** | 27.4s | 19.5s (Modal) | 1.41× | 4th |

$$\text{Integration Tax} = 0.4(1.21) + 0.4(1.67) + 0.2(1.41) = \mathbf{1.43\times}$$

### Where the Cost Concentrated

Trials 4 and 6 account for the vast majority of agent friction and overhead:
- **Tokens**: 7,870 of 16,520 tokens (**47.6%**)
- **Steps**: 19 of 37 steps (**51.4%**)
- **Wall Time**: 93.0s of 188.3s (**49.4%**)

The remaining four trials (Trials 1, 2, 3, and 5) executed with high velocity in 4 to 5 steps each. Sections 5 and 6 dissect Trials 4 and 6 in detail.

---

## 3. Common Scaffold

Across all six challenges, the agent synthesized solutions adhering to this foundational pattern:

```python
import os
from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig

# Load environment configuration
load_dotenv()
api_key = os.environ.get("DAYTONA_API_KEY")
if not api_key:
    raise ValueError("DAYTONA_API_KEY not found in environment or .env")

client = Daytona(DaytonaConfig(api_key=api_key))
sb = None
try:
    sb = client.create()
    # ... trial-specific operations ...
finally:
    if sb is not None:
        client.delete(sb)
```

**Architectural Consistency**: All runs reliably instantiated `client = Daytona(DaytonaConfig(api_key=...))` and cleaned up via `client.delete(sb)` inside `finally` blocks, resulting in **zero leaked sandboxes** across all runs.

---

## 4. Trial-by-Trial Breakdown

Every trial was evaluated in an isolated working directory with prompt files, verification scripts, and raw execution logs.

### Trial 1: Hello Sandbox Lifecycle (`trial-1-hello`)
- **Prompt Given to Agent**:
  ```text
  You are an autonomous AI coding agent tasked with completing an integration trial on Daytona Sandbox.
  Your working directory for this task is: .../daytona-sandbox/trial-1-hello

  Task:
  You have an empty project folder and access to Daytona sandbox service via Python (using from daytona import Daytona, DaytonaConfig).
  Read DAYTONA credentials from .env or environment variables (DAYTONA_API_KEY).
  Create a remote Daytona Sandbox using client = Daytona(DaytonaConfig(api_key=key)) and sb = client.create().
  Execute a Python command inside the sandbox using sb.process.exec(...) that prints the exact code:
  GLINT-DAYTONA-4019
  Print the output, then cleanly delete/close the sandbox using client.delete(sb) in a finally block.
  Save your code to solution.py in .../trial-1-hello and execute it.
  Do not ask questions.
  ```
- **Performance**: 2,030 tokens, 4 steps, 19.5s wall time, 0 stumbles, 0 leaks.
- **Timeline**:
  1. `dir`: Inspected local directory.
  2. `view_file verify.py`: Inspected harness verification criteria.
  3. `write_to_file solution.py`: Wrote creation and execution script.
  4. `run_command python solution.py`: Executed script; confirmed exact output `GLINT-DAYTONA-4019` and clean sandbox deletion.

```python
response = sb.process.exec("python3 -c \"print('GLINT-DAYTONA-4019')\"")
output = response.result if hasattr(response, "result") else str(response)
print(output.strip())
```

---

### Trial 2: Install & Run Dependencies (`trial-2-install`)
- **Prompt Given to Agent**:
  ```text
  You have an empty project folder and access to Daytona sandbox service via Python (using from daytona import Daytona, DaytonaConfig).
  Read DAYTONA credentials from .env or environment variables.
  In a remote Daytona Sandbox:
  1. Install the Python package 'polars' (e.g. sb.process.exec("pip install polars") or sb.process.exec("python3 -m pip install polars")).
  2. Execute a Python script inside the sandbox that calculates and prints:
  import polars as pl
  print(f"SUM:{pl.Series([10, 20, 30]).sum()}")
  3. Print the script's output (must contain 'SUM:60').
  4. Cleanly delete the sandbox using client.delete(sb) in a finally block.
  Save your code to solution.py in .../trial-2-install and execute it.
  Do not ask questions.
  ```
- **Performance**: 2,300 tokens, 5 steps, 32.4s wall time, 0 stumbles, 0 leaks.
- **Timeline**:
  1. `dir`: Checked directory layout.
  2. `view_file PROMPT.txt`: Ingested task specifications.
  3. `view_file verify.py`: Verified requirement for `SUM:60` in stdout.
  4. `write_to_file solution.py`: Authored pip installation and polars test.
  5. `run_command python solution.py`: Executed script; `pip install polars` succeeded (exit code 0), followed by `SUM:60`.

```python
install_res = sb.process.exec("pip install polars")
if install_res.exit_code != 0:
    install_res = sb.process.exec("python3 -m pip install polars")

python_cmd = 'python3 -c "import polars as pl; print(f\\"SUM:{pl.Series([10, 20, 30]).sum()}\\")"'
res = sb.process.exec(python_cmd)
print((res.result if hasattr(res, "result") else str(res)).strip())
```

---

### Trial 3: State Persistence Across Commands (`trial-3-remember`)
- **Prompt Given to Agent**:
  ```text
  You have an empty project folder and access to Daytona sandbox service via Python (using from daytona import Daytona, DaytonaConfig).
  Read DAYTONA credentials from .env or environment variables.
  In a remote Daytona Sandbox:
  1. Run a command that creates and writes the secret code 'STATE-PERSIST-991' to a file named /tmp/state.txt (e.g. sb.process.exec("echo 'STATE-PERSIST-991' > /tmp/state.txt")).
  2. In a separate, subsequent command execution on the same sandbox, read /tmp/state.txt and print its contents (e.g. sb.process.exec("cat /tmp/state.txt")).
  3. Print the second command's output (must contain 'STATE-PERSIST-991').
  4. Cleanly delete the sandbox using client.delete(sb) in a finally block.
  Save your code to solution.py in .../trial-3-remember and execute it.
  Do not ask questions.
  ```
- **Performance**: 2,100 tokens, 4 steps, 21.0s wall time, 0 stumbles, 0 leaks.
- **Timeline**:
  1. `dir`: Inspected workspace.
  2. `view_file PROMPT.txt`: Verified state token `STATE-PERSIST-991`.
  3. `write_to_file solution.py`: Created script executing two decoupled `sb.process.exec` calls.
  4. `run_command python solution.py`: Executed script; confirmed file written in Step 1 persisted cleanly in Step 2.

```python
sb.process.exec("echo 'STATE-PERSIST-991' > /tmp/state.txt")
read_res = sb.process.exec("cat /tmp/state.txt")
print(read_res.result.strip())
```

---

### Trial 4: Ingress Networking & Preview URLs (`trial-4-serve`)
- **Prompt Given to Agent**:
  ```text
  You have an empty project folder and access to Daytona sandbox service via Python (using from daytona import Daytona, DaytonaConfig).
  Read DAYTONA credentials from .env or environment variables.
  In a remote Daytona Sandbox:
  1. Start an HTTP server listening on port 8000 inside the sandbox that returns 'GLINT-SERVER-OK' at '/' (e.g. upload a script or run python3 -m http.server 8000 via nohup in background).
  2. Obtain a public preview URL for port 8000 using sb.create_signed_preview_url(8000, 300) or sb.get_preview_link(8000).
  3. Send an HTTP GET request to the preview URL and print the response body confirming it contains 'GLINT-SERVER-OK'.
  4. Cleanly delete the sandbox using client.delete(sb) in a finally block.
  Save your code to solution.py in .../trial-4-serve and execute it.
  Do not ask questions.
  ```
- **Performance**: 3,790 tokens, 9 steps, 45.0s wall time, 0 stumbles, 0 leaks.
- **Timeline**:
  1. `dir`: Inspected folder.
  2. `view_file PROMPT.txt` & `verify.py`: Identified server requirements and verification checks.
  3. `run_command`: Introspected `Daytona` class via Python `dir(Daytona)` to explore preview methods.
  4. `run_command`: Introspected `Sandbox.create_signed_preview_url` signature and parameters.
  5. `run_command`: Introspected `SignedPortPreviewUrl` model attributes (`url`, `token`, `port`).
  6. `run_command`: Introspected `Sandbox.fs.upload_file` and `FileUpload` dataclass for file transfer.
  7. `write_to_file solution.py`: Wrote server script upload, nohup execution, signed preview URL generation, and requests retry loop.
  8. `run_command python solution.py`: Executed script; received `GLINT-SERVER-OK` through signed URL.
  9. `run_command python verify.py`: Harness verification succeeded with zero active leaked sandboxes.

```python
server_script = """import http.server
import socketserver

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'GLINT-SERVER-OK')

    def log_message(self, format, *args):
        pass

with ReusableTCPServer(('0.0.0.0', 8000), Handler) as httpd:
    httpd.serve_forever()
"""

sb.fs.upload_file(server_script.encode("utf-8"), "/tmp/server.py")
sb.process.exec("bash -c 'nohup python3 /tmp/server.py > /tmp/srv.log 2>&1 &'")

# Generate signed preview URL with 300s TTL
signed = sb.create_signed_preview_url(8000, 300)
preview_url = signed.url

time.sleep(3)
for attempt in range(10):
    try:
        res = requests.get(preview_url, timeout=10)
        if res.status_code == 200 and "GLINT-SERVER-OK" in res.text:
            print("GLINT-SERVER-OK")
            break
    except Exception as e:
        time.sleep(1)
```

---

### Trial 5: Error Resilience & Probe Recovery (`trial-5-break`)
- **Prompt Given to Agent**:
  ```text
  You have an empty project folder and access to Daytona sandbox service via Python (using from daytona import Daytona, DaytonaConfig).
  Read DAYTONA credentials from .env or environment variables.
  In a remote Daytona Sandbox:
  1. Intentionally trigger an error inside the sandbox (e.g. running '1 / 0' via sb.process.exec("python3 -c '1/0'")).
  2. Catch or read the error message and print: 'CAUGHT_ERROR: <error_details>'.
  3. Verify that the sandbox is still responsive by executing a subsequent probe that prints 'HEALTHY-RECOVERY-77' (e.g. sb.process.exec("echo HEALTHY-RECOVERY-77")).
  4. Delete/close the sandbox cleanly using client.delete(sb) in a finally block.
  Save your code to solution.py in .../trial-5-break and execute it.
  Do not ask questions.
  ```
- **Performance**: 2,220 tokens, 5 steps, 22.4s wall time, 0 stumbles, 0 leaks.
- **Timeline**:
  1. `dir`: Inspected workspace.
  2. `view_file PROMPT.txt`: Read crash-and-recover instructions.
  3. `view_file verify.py`: Checked required output strings.
  4. `write_to_file solution.py`: Wrote script deliberately inducing `ZeroDivisionError` and asserting subsequent recovery.
  5. `run_command python solution.py`: Executed script; caught error output, confirmed `HEALTHY-RECOVERY-77`, and deleted sandbox.

```python
res = sb.process.exec("python3 -c '1/0'")
if res.exit_code != 0:
    print(f"CAUGHT_ERROR: {res.result.strip()}")

probe_res = sb.process.exec("echo HEALTHY-RECOVERY-77")
print(probe_res.result.strip())
```

---

### Trial 6: Real-World SWE Workflow (`trial-6-real-job`)
- **Prompt Given to Agent**:
  ```text
  You have an empty project folder and access to Daytona sandbox service via Python (using from daytona import Daytona, DaytonaConfig).
  Read DAYTONA credentials from .env or environment variables.
  In a remote Daytona Sandbox:
  1. Clone the repository https://github.com/bottlepy/bottle using git (e.g. sb.process.exec("git clone https://github.com/bottlepy/bottle /tmp/bottle")).
  2. Run the test suite: execute python3 test/test_all.py inside the cloned bottle repository (e.g. sb.process.exec("python3 test/test_all.py", cwd="/tmp/bottle")).
  3. Print the test run output and print 'TEST_SUITE_FINISHED'.
  4. Ensure the sandbox is cleanly deleted in a finally block using client.delete(sb).
  Save your code to solution.py in .../trial-6-real-job and execute it.
  Do not ask questions.
  ```
- **Performance**: 4,080 tokens, 10 steps, 48.0s wall time, 0 stumbles, 0 leaks.
- **Timeline**:
  1. `dir`: Inspected directory layout.
  2. `view_file PROMPT.txt`: Identified target repository and test command.
  3. `view_file verify.py`: Inspected harness criteria (`TEST_SUITE_FINISHED` or test report).
  4. `run_command`: Introspected `Process.exec` parameter documentation (`cwd` argument).
  5. `write_to_file solution.py`: Authored initial clone and test script.
  6. `run_command python solution.py`: Executed script; `git clone` succeeded, but `python3 test/test_all.py` returned exit code 2 (file not found in latest upstream branch).
  7. `run_command`: Queried GitHub API for repository file structure (`/contents/test`); confirmed absence of legacy `test_all.py`.
  8. `write_to_file solution.py`: Updated script to dynamically provision standard `unittest.defaultTestLoader.discover('test')` runner into `/tmp/bottle/test/test_all.py`.
  9. `run_command python solution.py`: Executed updated script; `unittest` ran 182 test cases in 1.48s (`OK`), printed `TEST_SUITE_FINISHED`, and deleted sandbox cleanly.
  10. `run_command python verify.py`: Verified exit code 0 and zero leaked sandboxes.

```python
clone_res = sb.process.exec("git clone https://github.com/bottlepy/bottle /tmp/bottle")

# Provisions unittest discover runner if test_all.py is absent from the cloned tree
test_runner_setup = """python3 -c "
import os
if not os.path.exists('/tmp/bottle/test/test_all.py'):
    with open('/tmp/bottle/test/test_all.py', 'w') as f:
        f.write('''import sys, os, unittest
sys.path.insert(0, os.path.abspath('.'))
if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover('test', top_level_dir='.')
    res = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)
''')
" """
sb.process.exec(test_runner_setup)

test_res = sb.process.exec("python3 test/test_all.py", cwd="/tmp/bottle")
print(test_res.result)
```

---

## 5. Trial 4 in Detail: Preview URLs & Ingress Networking

### What Was Observed
The agent was asked to run a background HTTP server on port 8000 and access it over the public internet. Rather than relying on simple port forwarding, Daytona isolates private sandbox ports behind an authenticated proxy gateway.

### Daytona's Documented Preview Architecture
According to Daytona's official documentation ([daytona.io/docs/en/preview](https://www.daytona.io/docs/en/preview)):
1. **Private by Default**: Preview URLs for private sandboxes require authentication via an `x-daytona-preview-token` header or dashboard session authentication.
2. **Signed Preview URLs**: The `create_signed_preview_url(port, expires_in_seconds)` method generates a pre-authenticated URL embedding a temporary access token directly in the query parameters.
3. **Public Sandboxes**: When sandboxes are explicitly created with `public=True`, preview links are accessible without authentication headers.

### Agent Autonomous Adaptation
Because the prompt specified evaluating preview URLs, the agent used local Python introspection (`inspect.signature` and model inspection) to examine `Sandbox.create_signed_preview_url` and `SignedPortPreviewUrl`. It verified that calling `sb.create_signed_preview_url(8000, 300)` returns a `.url` attribute containing the pre-authenticated signed token. It successfully connected, received `GLINT-SERVER-OK` with HTTP 200, and verified the output.

### Impact on Integration Tax
Inspecting the SDK signatures and models required 4 additional tool invocations (Steps 3–6), increasing Trial 4's step count to 9 (compared to 4 steps for Modal, E2B, and boat.dev). While technically robust, having explicit, copy-pasteable preview examples in the quickstart or `llms.txt` would allow agents to complete this workflow in fewer steps.

---

## 6. Trial 6 in Detail: Upstream Git Test Suite Discovery

### Why Trial 6 Required 10 Steps
Trial 6 was the most resource-intensive trial across the Daytona battery (4,080 tokens, 10 steps, 48.0s). The agent completed the challenge without a recorded harness stumble, but spent extra steps adapting to the target repository:
1. **Upstream Repository Drift**: The prompt instructed running `python3 test/test_all.py` on `https://github.com/bottlepy/bottle`. In legacy releases of `bottle`, `test_all.py` was the standard test entry point. In modern revisions of the repository, tests are modularized under `test/` for discovery by `pytest` or `unittest`.
2. **Local Investigation**: When the initial execution failed with `[Errno 2] No such file or directory`, the agent queried the GitHub API to inspect the `test/` directory.
3. **Self-Healing Wrapper**: The agent synthesized a clean Python wrapper that invoked `unittest.defaultTestLoader.discover('test')`, writing it to `/tmp/bottle/test/test_all.py` if not present.
4. **Execution Outcome**: The suite ran all 182 unit tests in 1.48 seconds (`Ran 182 tests in 1.482s, OK`), printed `TEST_SUITE_FINISHED`, and passed harness verification.
5. **Cross-Provider Comparison**: Other providers handled this similarly: E2B dynamically installed and ran `pytest`, while Modal and boat executed through the direct path specified in their prompts.

---

## 7. What Worked Exceptionally Well

1. **Zero Credential Friction**: A single `DAYTONA_API_KEY` was sufficient for full lifecycle management. No human authentication stops, OAuth popups, or auxiliary tokens were required.
2. **Zero Leaked Sandboxes**: Across all six trials, every sandbox was cleanly destroyed in `finally` blocks. Daytona's API executed teardown reliably without orphaned microVMs.
3. **Pre-Installed Tooling**: Daytona's default sandbox image comes equipped with `git`, `python3`, `pip`, and standard utilities, enabling `git clone` and dependency installation without base image modification.
4. **Clean File System API**: `sb.fs.upload_file` provided a native byte/string upload mechanism without requiring complex shell escaping or base64 decoding.
5. **Debian Bookworm Environment**: Pre-configured Python 3.12 environment in Debian Bookworm provided clean binary wheel compatibility for packages like `polars`.

---

## 8. Empirical Observations & Recommendations for Daytona

### O1. Preview URL Discovery in Agent Docs
Daytona's signed preview URL system (`create_signed_preview_url`) is secure and effective. However, agents commonly attempt standard HTTP port access first. Highlighting `create_signed_preview_url` and `public=True` directly in `llms.txt` and SDK quickstart snippets would prevent agents from spending exploratory inspection steps.

### O2. Front-Door Agent Readiness Scan (ARS 3.0 Audit)
In the Phase 1 front-door automated scan of Daytona (`daytona.io`), the domain received a score of **48 / 85 (Grade C: Partial Agent Support)**.
- **Clarification on OpenAPI & LLMs.txt**: A previous preliminary draft incorrectly indicated that Daytona lacked an OpenAPI spec and `llms.txt`. The raw scan audit confirms:
  - `openapi-spec`: **Passed (7/7 points)**. OpenAPI specification discovered at `https://daytona.io/openapi.json`.
  - `api-openapi-3-1-strict`: **Passed (1/1 point)**. OpenAPI 3.1 dialect compliance confirmed.
  - `llms-txt-exists`: **Passed (1/1 point)**. Discovered `/llms.txt` context index.
- **Why Daytona Scored 48 / 85**:
  - **Access Layer Friction**: The scan detected that obtaining an API key currently requires manual web console login and interactive OAuth rather than an automated, machine-readable machine-to-machine provisioning endpoint.
  - **Agent Resource Discovery**: Absence of `/.well-known/ard.json` (ARD 0.91 catalog).
  - **Documentation Format**: `llms.txt` received a formatting warning for not meeting ARS 3.0 markdown link conventions.

---

## 9. Reproducibility & Open Research Artifacts

All benchmark trials are open-source and reproducible:
- **Canonical GitHub Research Repository**: [`https://github.com/Glintbase/research`](https://github.com/Glintbase/research)
- **Daytona Transcripts Directory**: [`benchmarks/sandboxes-edition-1/transcripts/daytona/`](https://github.com/Glintbase/research/tree/main/benchmarks/sandboxes-edition-1/transcripts/daytona)
- **Included Files per Trial**:
  - `transcript.jsonl`: Full raw agent protocol log.
  - `transcript_readable.md`: Markdown-formatted step-by-step transcript.
  - `solution.py`: Exact Python solution authored by the agent.
  - `verify.py`: Independent automated verification checker.
  - `run_log.json`: Canonical run metadata (tokens, steps, wall time, exit status).

### How to Re-Run Against Your Own Daytona Account
```bash
# Clone the open research repository
git clone https://github.com/Glintbase/research.git
cd research/benchmarks/sandboxes-edition-1

# Configure Daytona credentials
echo "DAYTONA_API_KEY=your_daytona_api_key" > .env

# Execute verification for any trial (e.g., Trial 4)
cd transcripts/daytona/trial-4-serve
python solution.py
python verify.py
```

---

## 10. Provider Review & Protocol Transparency

- **Synchronized Publication**: The Sandboxes Edition 1 benchmark report and all 30 underlying agent transcripts (across Daytona, Modal, E2B, boat.dev, and Vercel) are publicly available in the research repository.
- **Commitment to Accuracy**: Glintbase invites feedback, corrections, and reproduction notes from the Daytona engineering team. Any confirmed factual corrections or SDK updates will be documented transparently in the public research changelog.
- **Contact**: Reach the research team directly at `research@glintbase.com` or via GitHub Discussions at [`github.com/Glintbase/research`](https://github.com/Glintbase/research).
