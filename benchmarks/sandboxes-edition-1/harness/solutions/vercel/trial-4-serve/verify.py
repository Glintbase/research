#!/usr/bin/env python3
"""
Verification Script for Vercel Sandbox - Trial 4 (Serve It - Ingress Networking)
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
    print("[*] Running Verification for Vercel Sandbox - Trial 4: Serve It (Ingress Networking)...")

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

    # Correction (2026-10-12): remaining sandboxes now FAIL the leak check (non-zero exit)
    # before cleanup. Previously they were deleted with only a warning and the trial still passed.
    leak_failed = False
    # Check for leaked sandboxes via vercel.sandbox.sync.query_sandboxes
    try:
        from vercel.sandbox.sync import query_sandboxes
        active = list(query_sandboxes())
        if len(active) > 0:
            print(f"[FAIL] Leak check FAILED: {len(active)} sandbox(es) still active after execution. Cleaning up after reporting.")
            leak_failed = True
            for s in active:
                try:
                    s.destroy()
                except:
                    pass
        else:
            print("[PASS] Clean-Up Check PASSED: 0 leaked sandboxes.")
    except Exception as e:
        print(f"[FAIL] Leak check could not run (query_sandboxes() raised): {e}")
        leak_failed = True

    if leak_failed:
        print("\n>>> VERCEL TRIAL 4 VERIFICATION FAILED (leak check) <<<\n")
        sys.exit(1)

    print("\n>>> VERCEL TRIAL 4 VERIFICATION PASSED! <<<\n")

if __name__ == "__main__":
    verify()
