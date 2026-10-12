#!/usr/bin/env python3
"""
Verification Script for Daytona Sandbox - Trial 2 (Install & Run - Dependencies)
Asserts:
1. solution.py exists
2. Running solution.py outputs 'SUM:60'
3. Verifies that the sandbox is deleted/closed cleanly
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

EXPECTED_OUTPUT = "SUM:60"

def verify():
    print("[*] Running Verification for Daytona Sandbox - Trial 2: Install & Run...")

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
        print(f"[FAIL] Expected computation output '{EXPECTED_OUTPUT}' not found in stdout!")
        print(f"Stdout was:\n{stdout}")
        if stderr:
            print(f"Stderr was:\n{stderr}")
        sys.exit(1)

    print(f"[PASS] Found computed result '{EXPECTED_OUTPUT}' in execution output!")

    # Correction (2026-10-12): remaining sandboxes now FAIL the leak check (non-zero exit)
    # before cleanup. Previously they were deleted with only a warning and the trial still passed.
    leak_failed = False
    # Check for leaked sandboxes via Daytona client
    try:
        from daytona import Daytona, DaytonaConfig
        key = os.getenv("DAYTONA_API_KEY")
        client = Daytona(DaytonaConfig(api_key=key))
        active = list(client.list())
        if len(active) > 0:
            print(f"[FAIL] Leak check FAILED: {len(active)} sandbox(es) still active after execution. Cleaning up after reporting.")
            leak_failed = True
            for s in active:
                try:
                    client.delete(s)
                except:
                    pass
        else:
            print("[PASS] Clean-Up Check PASSED: 0 leaked sandboxes.")
    except Exception as e:
        print(f"[FAIL] Leak check could not run (client.list() raised): {e}")
        leak_failed = True

    if leak_failed:
        print("\n>>> DAYTONA TRIAL 2 VERIFICATION FAILED (leak check) <<<\n")
        sys.exit(1)

    print("\n>>> DAYTONA TRIAL 2 VERIFICATION PASSED! <<<\n")

if __name__ == "__main__":
    verify()
