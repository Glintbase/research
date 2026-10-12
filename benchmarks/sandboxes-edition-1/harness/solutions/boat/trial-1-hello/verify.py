#!/usr/bin/env python3
"""
Verification Script for Boat Sandbox - Trial 1 (Hello Sandbox Lifecycle)
Asserts:
1. solution.py exists
2. Running solution.py outputs 'GLINT-BOAT-9103'
3. Verifies that the sandbox is deleted/closed cleanly
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

EXPECTED_OUTPUT = "GLINT-BOAT-9103"

def verify():
    print("[*] Running Verification for Boat Sandbox - Trial 1: Hello Sandbox...")

    if not os.path.exists("solution.py"):
        print("[FAIL] solution.py does not exist!")
        sys.exit(1)

    try:
        proc = subprocess.run(
            [sys.executable, "solution.py"],
            capture_output=True,
            text=True,
            timeout=90
        )
    except subprocess.TimeoutExpired:
        print("[FAIL] solution.py timed out after 90 seconds!")
        sys.exit(1)

    stdout = proc.stdout
    stderr = proc.stderr

    if EXPECTED_OUTPUT not in stdout:
        print(f"[FAIL] Expected secret '{EXPECTED_OUTPUT}' not found in stdout!")
        print(f"Stdout was:\n{stdout}")
        if stderr:
            print(f"Stderr was:\n{stderr}")
        sys.exit(1)

    print(f"[PASS] Successfully verified output '{EXPECTED_OUTPUT}' in solution output!")

    # Correction (2026-10-12): remaining sandboxes now FAIL the leak check (non-zero exit)
    # before cleanup. Previously they were deleted with only a warning and the trial still passed.
    leak_failed = False
    # Check for leaked sandboxes via boat client
    try:
        import boat_sdk
        key = os.getenv("BOAT_API_KEY")
        api = boat_sdk.BoatApi(boat_sdk.ApiClient(boat_sdk.Configuration(access_token=key)))
        active = api.sandboxes().sandboxes
        if len(active) > 0:
            print(f"[FAIL] Leak check FAILED: {len(active)} sandbox(es) still active after execution. Cleaning up after reporting.")
            leak_failed = True
            for s in active:
                try:
                    boat_sdk.stop_and_remove(api, s.id, delete=True)
                except:
                    pass
        else:
            print("[PASS] Clean-Up Check PASSED: 0 leaked sandboxes.")
    except Exception as e:
        print(f"[FAIL] Leak check could not run (boat_sdk sandboxes list raised): {e}")
        leak_failed = True

    if leak_failed:
        print("\n>>> BOAT TRIAL 1 VERIFICATION FAILED (leak check) <<<\n")
        sys.exit(1)

    print("\n>>> BOAT TRIAL 1 VERIFICATION PASSED! <<<\n")

if __name__ == "__main__":
    verify()
