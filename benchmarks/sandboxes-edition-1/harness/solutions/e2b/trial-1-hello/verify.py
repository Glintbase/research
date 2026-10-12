#!/usr/bin/env python3
"""
Verification Script for Trial 1 (Hello Sandbox)
Asserts:
1. solution.py exists
2. Running solution.py outputs GLINT-HELLO-8492
3. Verifies that the sandbox is deleted/closed cleanly
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

EXPECTED_SECRET = "GLINT-HELLO-8492"

def verify():
    print("[*] Running Verification for Trial 1: Hello Sandbox...")

    if not os.path.exists("solution.py"):
        print("[FAIL] solution.py does not exist!")
        sys.exit(1)

    # Execute solution.py
    try:
        proc = subprocess.run(
            [sys.executable, "solution.py"],
            capture_output=True,
            text=True,
            timeout=45
        )
    except subprocess.TimeoutExpired:
        print("[FAIL] solution.py timed out after 45 seconds!")
        sys.exit(1)

    stdout = proc.stdout
    stderr = proc.stderr

    if EXPECTED_SECRET not in stdout:
        print(f"[FAIL] Expected secret '{EXPECTED_SECRET}' not found in stdout!")
        print(f"Stdout was:\n{stdout}")
        if stderr:
            print(f"Stderr was:\n{stderr}")
        sys.exit(1)

    print(f"[PASS] Found secret '{EXPECTED_SECRET}' in execution output!")

    # Correction (2026-10-12): remaining sandboxes now FAIL the leak check (non-zero exit)
    # before cleanup. Previously they were deleted with only a warning and the trial still passed.
    leak_failed = False
    # Check for leaked sandboxes via e2b if available
    try:
        from e2b import Sandbox
        p = Sandbox.list()
        active = p.next_items() if hasattr(p, 'next_items') else []
        if len(active) > 0:
            print(f"[FAIL] Leak check FAILED: {len(active)} sandbox(es) still active after execution. Cleaning up after reporting.")
            leak_failed = True
            for s in active:
                try:
                    s.kill()
                except:
                    pass
        else:
            print("[PASS] Clean-Up Check PASSED: 0 leaked sandboxes.")
    except Exception as e:
        print(f"[FAIL] Leak check could not run (e2b.Sandbox.list() raised): {e}")
        leak_failed = True

    if leak_failed:
        print("\n>>> TRIAL 1 VERIFICATION FAILED (leak check) <<<\n")
        sys.exit(1)

    print("\n>>> TRIAL 1 VERIFICATION PASSED! <<<\n")

if __name__ == "__main__":
    verify()
