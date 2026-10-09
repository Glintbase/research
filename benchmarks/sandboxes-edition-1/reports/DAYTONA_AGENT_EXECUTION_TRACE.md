# Daytona Cloud Sandbox — Comprehensive Autonomous Agent Trace
**Benchmark**: Glintbase Sandboxes Benchmark (Edition 1)  
**Provider**: Daytona  
**SDK Evaluated**: `daytona 0.222.0` (Python SDK)  
**Autonomous Agent**: Gemini 3.8 Flash (Medium Profile)  
**Harness**: Antigravity Autonomous Coding Harness (zero human in-the-loop intervention)  
**Date of Run**: October 6, 2026  
**Final Status**: **100% Pass Rate (6/6 Trials Passed)** | **0 Leaked MicroVMs** | **Integration Tax: 1.43×** | **Rank: #5 Overall**

---

## 1. Executive Summary & Benchmark Overview

This document provides the full, reproduction-grade trace of Daytona's evaluation during Edition 1 of the Glintbase Sandboxes Benchmark. Daytona was tested alongside Modal Labs, E2B, boat by ASCII, and Vercel Sandbox across six standardized engineering challenges designed to evaluate how AI coding agents autonomously discover, orchestrate, persist state in, and teardown remote sandboxes.

### Master Scorecard

| Trial ID | Challenge Name | Outcome | Prompt Tokens | Completion Tokens | Total Tokens | Steps | Wall Time | Stumbles | Leaks |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `trial-1-hello` | Hello Sandbox Lifecycle | **PASS** | 1,540 | 490 | 2,030 | 4 | 19.5s | 0 | 0 |
| `trial-2-install` | Install & Run (`polars`) | **PASS** | 1,720 | 580 | 2,300 | 5 | 32.4s | 0 | 0 |
| `trial-3-remember`| State Persistence (`/tmp`) | **PASS** | 1,590 | 510 | 2,100 | 4 | 21.0s | 0 | 0 |
| `trial-4-serve` | Ingress Networking & Ports | **PASS** | 2,850 | 940 | 3,790 | 9 | 45.0s | 1 | 0 |
| `trial-5-break` | Error Resilience & Recovery | **PASS** | 1,680 | 540 | 2,220 | 5 | 22.4s | 0 | 0 |
| `trial-6-real-job`| Real Job (`bottlepy` Tests)| **PASS** | 3,100 | 980 | 4,080 | 10 | 48.0s | 0 | 0 |
| **Totals / Medians**| **Full Test Battery** | **100% (6/6)**| **12,480** | **4,040** | **16,520** | **5.0 med** | **27.4s med**| **1** | **0 leaks** |

---

## 2. Deep-Dive Trial-by-Trial Traces

---

### Trial 1: Hello Sandbox Lifecycle (`trial-1-hello`)
- **Objective**: Provision a Daytona sandbox via Python SDK, execute `python3 -c "print('GLINT-DAYTONA-4019')"`, assert exact output, and delete sandbox cleanly.
- **Tokens**: 1,540 Prompt / 490 Completion / 2,030 Total
- **Steps**: 4
- **Wall Time**: 19.5 seconds
- **Pass / Fail**: PASS (Zero stumbles, zero leaks)

#### Autonomous Agent Solution (`solution.py`):
```python
import os
from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig

# Read DAYTONA credentials from .env or environment variables (DAYTONA_API_KEY)
load_dotenv()

api_key = os.environ.get("DAYTONA_API_KEY")
if not api_key:
    raise ValueError("DAYTONA_API_KEY not found in environment or .env")

# Create remote Daytona Sandbox
client = Daytona(DaytonaConfig(api_key=api_key))
sb = None

try:
    print("Creating Daytona sandbox...")
    sb = client.create()
    print("Sandbox created successfully.")

    # Execute Python command inside sandbox
    response = sb.process.exec("python3 -c \"print('GLINT-DAYTONA-4019')\"")
    output = response.result if hasattr(response, 'result') else str(response)
    print(output.strip())
finally:
    # Cleanly delete/close sandbox in finally block
    if sb is not None:
        print("Deleting sandbox...")
        client.delete(sb)
        print("Sandbox deleted.")
```

#### Execution Output:
```
Creating Daytona sandbox...
Sandbox created successfully.
GLINT-DAYTONA-4019
Deleting sandbox...
Sandbox deleted.
```

---

### Trial 2: Install & Run Dependencies (`trial-2-install`)
- **Objective**: In a fresh sandbox, install `polars` via pip, run computation `import polars as pl; print(f"SUM:{pl.Series([10, 20, 30]).sum()}")`, assert `SUM:60`, and teardown.
- **Tokens**: 1,720 Prompt / 580 Completion / 2,300 Total
- **Steps**: 5
- **Wall Time**: 32.4 seconds
- **Pass / Fail**: PASS (Zero stumbles, zero leaks)

#### Autonomous Agent Solution (`solution.py`):
```python
import os
from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig

load_dotenv()

api_key = os.environ.get("DAYTONA_API_KEY")
if not api_key:
    raise ValueError("DAYTONA_API_KEY not found in environment or .env")

client = Daytona(DaytonaConfig(api_key=api_key))
sb = None

try:
    print("Creating Daytona sandbox...")
    sb = client.create()
    print("Sandbox created successfully.")

    # 1. Install Python package 'polars'
    print("Installing polars...")
    install_res = sb.process.exec("pip install polars")
    if install_res.exit_code != 0:
        install_res = sb.process.exec("python3 -m pip install polars")
    print(f"Install exit code: {install_res.exit_code}")

    # 2. Execute computation
    python_cmd = 'python3 -c "import polars as pl; print(f\\"SUM:{pl.Series([10, 20, 30]).sum()}\\")"'
    res = sb.process.exec(python_cmd)

    # 3. Print output
    output = res.result if hasattr(res, "result") else str(res)
    print(output.strip())

finally:
    if sb is not None:
        print("Deleting sandbox...")
        client.delete(sb)
        print("Sandbox deleted.")
```

#### Execution Output:
```
Creating Daytona sandbox...
Sandbox created successfully.
Installing polars...
Install exit code: 0
SUM:60
Deleting sandbox...
Sandbox deleted.
```

---

### Trial 3: State Persistence Across Independent Invocations (`trial-3-remember`)
- **Objective**: Write secret code `STATE-PERSIST-991` to `/tmp/state.txt` in invocation #1. In an isolated, subsequent invocation #2, read `/tmp/state.txt` and verify contents, proving container filesystem persistence between commands.
- **Tokens**: 1,590 Prompt / 510 Completion / 2,100 Total
- **Steps**: 4
- **Wall Time**: 21.0 seconds
- **Pass / Fail**: PASS (Zero stumbles, zero leaks)

#### Autonomous Agent Solution (`solution.py`):
```python
import os
from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig

load_dotenv()

api_key = os.environ.get("DAYTONA_API_KEY")
if not api_key:
    raise ValueError("DAYTONA_API_KEY not found in environment or .env")

client = Daytona(DaytonaConfig(api_key=api_key))
sb = None

try:
    print("Creating Daytona sandbox...")
    sb = client.create()
    print("Sandbox created successfully.")

    # Command 1: Write secret
    print("Writing secret to /tmp/state.txt...")
    write_res = sb.process.exec("echo 'STATE-PERSIST-991' > /tmp/state.txt")
    print(f"Write exit code: {getattr(write_res, 'exit_code', 0)}")

    # Command 2: Read secret in subsequent exec
    print("Reading /tmp/state.txt...")
    read_res = sb.process.exec("cat /tmp/state.txt")

    output = read_res.result if hasattr(read_res, "result") else str(read_res)
    print(output.strip())

finally:
    if sb is not None:
        print("Deleting sandbox...")
        client.delete(sb)
        print("Sandbox deleted.")
```

#### Execution Output:
```
Creating Daytona sandbox...
Sandbox created successfully.
Writing secret to /tmp/state.txt...
Write exit code: 0
Reading /tmp/state.txt...
STATE-PERSIST-991
Deleting sandbox...
Sandbox deleted.
```

---

### Trial 4: Ingress Networking & Server Expose (`trial-4-serve`)
- **Objective**: Start an HTTP server on port 8000 returning `GLINT-SERVER-OK`, expose port to the public internet, send external HTTP GET request from host machine, and verify response body.
- **Tokens**: 2,850 Prompt / 940 Completion / 3,790 Total
- **Steps**: 9
- **Wall Time**: 45.0 seconds
- **Pass / Fail**: PASS (1 Stumble resolved autonomously)
- **The Stumble (Trap 5.1)**:  
  Default workspace port proxying on Daytona (`https://8000-*-daytonaproxy01.eu`) returned `HTTP 401 Unauthorized` because the proxy gateway protects workspace ports with dashboard session cookies. The agent inspected the SDK, discovered `sb.create_signed_preview_url(8000, 300)`, generated a signed tokenized link, and successfully reached the server with HTTP 200.

#### Autonomous Agent Solution (`solution.py`):
```python
import os
import time
import requests
from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig

load_dotenv()

api_key = os.environ.get("DAYTONA_API_KEY")
if not api_key:
    raise ValueError("DAYTONA_API_KEY not found in environment or .env")

client = Daytona(DaytonaConfig(api_key=api_key))
sb = None

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

try:
    print("Creating Daytona sandbox...")
    sb = client.create()
    print("Sandbox created successfully.")

    # 1. Upload server script via fs primitive
    print("Uploading server script to /tmp/server.py...")
    sb.fs.upload_file(server_script.encode("utf-8"), "/tmp/server.py")

    # 2. Run HTTP server in background
    print("Starting HTTP server in background on port 8000...")
    sb.process.exec("bash -c 'nohup python3 /tmp/server.py > /tmp/srv.log 2>&1 &'")

    # 3. Obtain signed preview URL to bypass 401 Unauthorized barrier
    print("Obtaining signed preview URL for port 8000...")
    signed = sb.create_signed_preview_url(8000, 300)
    preview_url = signed.url
    print(f"Preview URL: {preview_url}")

    # 4. Probe external ingress
    time.sleep(3)
    response_text = ""
    for attempt in range(10):
        try:
            res = requests.get(preview_url, timeout=10)
            if res.status_code == 200 and "GLINT-SERVER-OK" in res.text:
                response_text = res.text
                break
        except Exception as e:
            print(f"Attempt {attempt + 1} request error: {e}")
        time.sleep(1)

    print("Response body:")
    print(response_text.strip())

finally:
    if sb is not None:
        print("Deleting sandbox...")
        client.delete(sb, wait=True)
        print("Sandbox deleted.")
```

#### Execution Output:
```
Creating Daytona sandbox...
Sandbox created successfully.
Uploading server script to /tmp/server.py...
Starting HTTP server in background on port 8000...
Obtaining signed preview URL for port 8000...
Preview URL: https://8000-work-10023-daytonaproxy01.eu/dtn_preview?token=...
Response body:
GLINT-SERVER-OK
Deleting sandbox...
Sandbox deleted.
```

---

### Trial 5: Error Resilience & Recovery (`trial-5-break`)
- **Objective**: Intentionally trigger a crash (`1 / 0`), verify the SDK cleanly captures non-zero return code and stderr without killing the session, and verify the sandbox recovers to execute subsequent health probe (`echo HEALTHY-RECOVERY-77`).
- **Tokens**: 1,680 Prompt / 540 Completion / 2,220 Total
- **Steps**: 5
- **Wall Time**: 22.4 seconds
- **Pass / Fail**: PASS (Zero stumbles, zero leaks)

#### Autonomous Agent Solution (`solution.py`):
```python
import os
import sys
from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig

load_dotenv()

api_key = os.getenv("DAYTONA_API_KEY")
if not api_key:
    raise ValueError("DAYTONA_API_KEY not found in environment or .env")

client = Daytona(DaytonaConfig(api_key=api_key))
sb = None

try:
    print("Creating Daytona sandbox...")
    sb = client.create()
    print("Sandbox created successfully.")

    # 1. Intentionally trigger runtime error
    print("Triggering intentional error inside sandbox...")
    res = sb.process.exec("python3 -c '1/0'")
    if res.exit_code != 0:
        error_details = res.result.strip() if res.result else f"Non-zero exit code: {res.exit_code}"
        print(f"CAUGHT_ERROR: {error_details}")

    # 2. Verify sandbox responsiveness with probe
    print("Verifying sandbox responsiveness with probe...")
    probe_res = sb.process.exec("echo HEALTHY-RECOVERY-77")
    output = probe_res.result if hasattr(probe_res, "result") else str(probe_res)
    print(output.strip())

finally:
    if sb is not None:
        print("Deleting sandbox cleanly...")
        try:
            client.delete(sb)
            print("Sandbox deleted.")
        except Exception as e:
            print(f"Error deleting sandbox: {e}")
```

#### Execution Output:
```
Creating Daytona sandbox...
Sandbox created successfully.
Triggering intentional error inside sandbox...
CAUGHT_ERROR: ZeroDivisionError: division by zero
Verifying sandbox responsiveness with probe...
HEALTHY-RECOVERY-77
Deleting sandbox cleanly...
Sandbox deleted.
```

---

### Trial 6: Real-World SWE Workflow (`trial-6-real-job`)
- **Objective**: Clone open-source git repository (`bottlepy/bottle`), run test discovery (`python3 test/test_all.py`), assert complete test suite execution, and verify clean teardown with zero orphaned compute.
- **Tokens**: 3,100 Prompt / 980 Completion / 4,080 Total
- **Steps**: 10
- **Wall Time**: 48.0 seconds
- **Pass / Fail**: PASS (Zero stumbles, zero leaks)
- **Architectural Note**: Daytona was the **only platform** that had `git` installed and working out-of-the-box without requiring `apt-get install` or custom Dockerfile/Image layers.

#### Autonomous Agent Solution (`solution.py`):
```python
import os
from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig

load_dotenv()

api_key = os.environ.get("DAYTONA_API_KEY")
if not api_key:
    raise ValueError("DAYTONA_API_KEY not found in environment or .env")

client = Daytona(DaytonaConfig(api_key=api_key))
sb = None

try:
    print("Creating Daytona sandbox...")
    sb = client.create()
    print("Sandbox created successfully.")

    # 1. Clone repository via pre-installed git
    print("Cloning repository https://github.com/bottlepy/bottle...")
    clone_res = sb.process.exec("git clone https://github.com/bottlepy/bottle /tmp/bottle")
    print(f"Git clone exit code: {clone_res.exit_code}")

    # Install bottle in editable mode
    sb.process.exec("pip install -e .", cwd="/tmp/bottle")

    # Ensure test runner exists
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

    # 2. Run test suite
    print("Running test suite...")
    test_res = sb.process.exec("python3 test/test_all.py", cwd="/tmp/bottle")
    print(f"Test run exit code: {test_res.exit_code}")

    output = test_res.result if hasattr(test_res, "result") else str(test_res)
    print(output)
    print("TEST_SUITE_FINISHED")

finally:
    if sb is not None:
        print("Deleting sandbox...")
        try:
            client.delete(sb)
            print("Sandbox deleted.")
        except Exception as e:
            print(f"Error deleting sandbox: {e}")
```

#### Execution Output:
```
Creating Daytona sandbox...
Sandbox created successfully.
Cloning repository https://github.com/bottlepy/bottle...
Git clone exit code: 0
Running test suite...
Test run exit code: 0
Ran 182 tests in 1.482s
OK
TEST_SUITE_FINISHED
Deleting sandbox...
Sandbox deleted.
```

---

## 3. What Impressed the Autonomous Agent

1. **Rich Developer Base Image Out-of-the-Box**:
   - Python 3.14, git, and zsh were already pre-installed.
   - For real-world coding agents, this eliminates the step of running `apt update && apt install -y git`, which failed or required complex container builders on several other sandbox runtimes.
2. **Single-Credential Simplicity**:
   - Only `DAYTONA_API_KEY` is required.
   - In contrast, Vercel requires 3 secrets (`VERCEL_TOKEN`, `VERCEL_PROJECT_ID`, `VERCEL_TEAM_ID`), and Modal requires paired tokens (`MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`).
3. **Flawless Teardown & Zero Compute Leaks**:
   - Over all 6 automated runs, Daytona achieved a **0% leak rate**. Every sandbox was cleanly terminated and removed from the account.
4. **Clean Filesystem Primitives**:
   - `sb.fs.upload_file(data, path)` allowed binary and script injection without needing shell `base64 -d` hacks.

---

## 4. Friction Points & Actionable Recommendations for Daytona

### 1. Ingress 401 Trap (Public vs. Dashboard Preview)
- **Friction**: The default preview URL created for exposed ports requires Daytona web session cookies, returning `HTTP 401 Unauthorized` to any external API client or automated test probe.
- **Agent Stumble**: The agent had to spend extra tokens and steps discovering `sb.create_signed_preview_url(8000, 300)`.
- **Recommendation**:
  - Add a parameter directly to preview methods, e.g. `sb.preview(8000, public=True)`.
  - Highlight `create_signed_preview_url` prominently in agent code examples and machine-readable surfaces (`/llms.txt`).

### 2. `client.list()` Generator Return Type
- **Friction**: Calling `len(client.list())` in cleanup scripts threw `TypeError: object of type 'generator' has no len()`.
- **Recommendation**: Return a sized list or collection, or implement `__len__` on the iterable wrapper.

### 3. Front-Door Machine Discovery (ARS 3.0 Score: 48/100 Grade C)
- While Daytona's **runtime performance** was 100% robust, its **documentation and machine-readable surfaces** lacked an `/llms.txt`, formal OpenAPI schema, and clear SDK tool manifests. This caused initial discovery token bloat, contributing to its 1.43× Integration Tax.

---

## 5. Artifact & Log References (Canonical GitHub Repository)

All raw transcripts, step-by-step readable logs, solution code, and verification scripts are tracked directly in the public [Glintbase Research Repository](https://github.com/Glintbase/research) and are completely portable for external engineering teams:

### GitHub Research Repository Links
| Challenge | Readable Markdown Trace (Formatted) | Raw JSONL Transcript | Solution Script | Verification Script | Run Metadata |
|---|---|---|---|---|---|
| **Trial 1 (Hello)** | [Trace](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/transcripts/daytona/trial-1-hello/transcript_readable.md) | [JSONL](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/transcripts/daytona/trial-1-hello/transcript.jsonl) | [Solution](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-1-hello/solution.py) | [Verify](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-1-hello/verify.py) | [run_log.json](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-1-hello/run_log.json) |
| **Trial 2 (Install)** | [Trace](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/transcripts/daytona/trial-2-install/transcript_readable.md) | [JSONL](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/transcripts/daytona/trial-2-install/transcript.jsonl) | [Solution](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-2-install/solution.py) | [Verify](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-2-install/verify.py) | [run_log.json](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-2-install/run_log.json) |
| **Trial 3 (Remember)** | [Trace](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/transcripts/daytona/trial-3-remember/transcript_readable.md) | [JSONL](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/transcripts/daytona/trial-3-remember/transcript.jsonl) | [Solution](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-3-remember/solution.py) | [Verify](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-3-remember/verify.py) | [run_log.json](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-3-remember/run_log.json) |
| **Trial 4 (Serve)** | [Trace](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/transcripts/daytona/trial-4-serve/transcript_readable.md) | [JSONL](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/transcripts/daytona/trial-4-serve/transcript.jsonl) | [Solution](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-4-serve/solution.py) | [Verify](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-4-serve/verify.py) | [run_log.json](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-4-serve/run_log.json) |
| **Trial 5 (Break)** | [Trace](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/transcripts/daytona/trial-5-break/transcript_readable.md) | [JSONL](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/transcripts/daytona/trial-5-break/transcript.jsonl) | [Solution](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-5-break/solution.py) | [Verify](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-5-break/verify.py) | [run_log.json](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-5-break/run_log.json) |
| **Trial 6 (Real Job)** | [Trace](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/transcripts/daytona/trial-6-real-job/transcript_readable.md) | [JSONL](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/transcripts/daytona/trial-6-real-job/transcript.jsonl) | [Solution](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-6-real-job/solution.py) | [Verify](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-6-real-job/verify.py) | [run_log.json](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/harness/solutions/daytona/trial-6-real-job/run_log.json) |

### Complete Benchmark Suite
- Entire Transcripts Directory: [github.com/Glintbase/research/tree/main/benchmarks/sandboxes-edition-1/transcripts/](https://github.com/Glintbase/research/tree/main/benchmarks/sandboxes-edition-1/transcripts/)
- Master Benchmark Dataset: [github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/data/benchmark_master.json](https://github.com/Glintbase/research/blob/main/benchmarks/sandboxes-edition-1/data/benchmark_master.json)


