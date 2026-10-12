#!/usr/bin/env python3
"""
Verification Script for Modal Sandbox - Trial 3 (Remember Me - State Persistence)
Asserts:
1. solution.py exists
2. Running solution.py outputs 'STATE-PERSIST-991'
3. Verifies that the sandbox is deleted/closed cleanly
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

EXPECTED_OUTPUT = "STATE-PERSIST-991"

def verify():
    print("[*] Running Verification for Modal Sandbox - Trial 3: Remember Me...")

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

    print(f"[PASS] Successfully verified persistence: '{EXPECTED_OUTPUT}' retrieved from state.txt!")

    # Correction (2026-10-12): remaining sandboxes now FAIL the leak check (non-zero exit)
    # before cleanup. Previously they were deleted with only a warning and the trial still passed.
    leak_failed = False
    # Check for leaked sandboxes via modal client
    try:
        import modal
        app = modal.App.lookup("glint-modal-app", create_if_missing=True)
        active = list(modal.Sandbox.list(app_id=app.app_id))
        if len(active) > 0:
            print(f"[FAIL] Leak check FAILED: {len(active)} sandbox(es) still active after execution. Cleaning up after reporting.")
            leak_failed = True
            for s in active:
                try:
                    s.terminate()
                except:
                    pass
        else:
            print("[PASS] Clean-Up Check PASSED: 0 leaked sandboxes.")
    except Exception as e:
        print(f"[FAIL] Leak check could not run (modal.Sandbox.list() raised): {e}")
        leak_failed = True

    if leak_failed:
        print("\n>>> MODAL TRIAL 3 VERIFICATION FAILED (leak check) <<<\n")
        sys.exit(1)

    print("\n>>> MODAL TRIAL 3 VERIFICATION PASSED! <<<\n")

if __name__ == "__main__":
    verify()
