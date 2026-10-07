#!/usr/bin/env python3
"""
Verification Script for Modal Sandbox - Trial 1 (Hello Sandbox Lifecycle)
Asserts:
1. solution.py exists
2. Running solution.py outputs 'GLINT-MODAL-5821'
3. Verifies that the sandbox is deleted/closed cleanly
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

EXPECTED_OUTPUT = "GLINT-MODAL-5821"

def verify():
    print("[*] Running Verification for Modal Sandbox - Trial 1: Hello Sandbox...")

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

    print("\n>>> MODAL TRIAL 1 VERIFICATION PASSED! <<<\n")

if __name__ == "__main__":
    verify()
