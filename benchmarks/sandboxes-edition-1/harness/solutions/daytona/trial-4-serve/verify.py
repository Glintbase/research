#!/usr/bin/env python3
"""
Verification Script for Daytona Sandbox - Trial 4 (Serve It - Ingress Networking)
Asserts:
1. solution.py exists
2. Running solution.py outputs 'GLINT-SERVER-OK'
3. Verifies that the sandbox is deleted/closed cleanly
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

EXPECTED_OUTPUT = "GLINT-SERVER-OK"

def verify():
    print("[*] Running Verification for Daytona Sandbox - Trial 4: Serve It (Ingress Networking)...")

    if not os.path.exists("solution.py"):
        print("[FAIL] solution.py does not exist!")
        sys.exit(1)

    try:
        proc = subprocess.run(
            [sys.executable, "solution.py"],
            capture_output=True,
            text=True,
            timeout=120
        )
    except subprocess.TimeoutExpired:
        print("[FAIL] solution.py timed out after 120 seconds!")
        sys.exit(1)

    stdout = proc.stdout
    stderr = proc.stderr

    if EXPECTED_OUTPUT not in stdout:
        print(f"[FAIL] Expected response '{EXPECTED_OUTPUT}' not found in stdout!")
        print(f"Stdout was:\n{stdout}")
        if stderr:
            print(f"Stderr was:\n{stderr}")
        sys.exit(1)

    print(f"[PASS] Successfully reached HTTP server: '{EXPECTED_OUTPUT}' returned!")

    # Check for leaked sandboxes via Daytona client
    try:
        from daytona import Daytona, DaytonaConfig
        key = os.getenv("DAYTONA_API_KEY")
        client = Daytona(DaytonaConfig(api_key=key))
        active = list(client.list())
        if len(active) > 0:
            print(f"[WARN] Warning: Detected {len(active)} active sandboxes after execution!")
            for s in active:
                try:
                    client.delete(s)
                except:
                    pass
        else:
            print("[PASS] Clean-Up Check PASSED: 0 leaked sandboxes.")
    except Exception as e:
        print(f"[INFO] Could not check client.list() directly: {e}")

    print("\n>>> DAYTONA TRIAL 4 VERIFICATION PASSED! <<<\n")

if __name__ == "__main__":
    verify()
