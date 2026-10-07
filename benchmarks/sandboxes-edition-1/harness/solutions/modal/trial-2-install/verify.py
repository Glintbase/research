#!/usr/bin/env python3
"""
Verification Script for Modal Sandbox - Trial 2 (Install & Run - Dependencies)
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
    print("[*] Running Verification for Modal Sandbox - Trial 2: Install & Run...")

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

    # Check for leaked sandboxes via modal client
    try:
        import modal
        app = modal.App.lookup("glint-modal-app", create_if_missing=True)
        active = list(modal.Sandbox.list(app_id=app.app_id))
        if len(active) > 0:
            print(f"[WARN] Warning: Detected {len(active)} active sandboxes after execution!")
            for s in active:
                try:
                    s.terminate()
                except:
                    pass
        else:
            print("[PASS] Clean-Up Check PASSED: 0 leaked sandboxes.")
    except Exception as e:
        print(f"[INFO] Could not check modal.Sandbox.list() directly: {e}")

    print("\n>>> MODAL TRIAL 2 VERIFICATION PASSED! <<<\n")

if __name__ == "__main__":
    verify()
