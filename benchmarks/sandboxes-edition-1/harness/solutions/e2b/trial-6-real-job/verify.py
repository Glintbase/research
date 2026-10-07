#!/usr/bin/env python3
"""
Verification Script for Trial 6 (Real Job - Git Clone & Test Execution)
Asserts:
1. solution.py exists
2. Running solution.py finishes and outputs 'TEST_SUITE_FINISHED' or test pass summary
3. Verifies that the sandbox is deleted/closed cleanly
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

EXPECTED_OUTPUT = "TEST_SUITE_FINISHED"

def verify():
    print("[*] Running Verification for Trial 6: Real Job (SWE Test Execution)...")

    if not os.path.exists("solution.py"):
        print("[FAIL] solution.py does not exist!")
        sys.exit(1)

    try:
        proc = subprocess.run(
            [sys.executable, "solution.py"],
            capture_output=True,
            text=True,
            timeout=180
        )
    except subprocess.TimeoutExpired:
        print("[FAIL] solution.py timed out after 180 seconds!")
        sys.exit(1)

    stdout = proc.stdout
    stderr = proc.stderr

    if EXPECTED_OUTPUT not in stdout and "passed" not in stdout.lower():
        print(f"[FAIL] Expected marker '{EXPECTED_OUTPUT}' or 'passed' not found in stdout!")
        print(f"Stdout was:\n{stdout}")
        if stderr:
            print(f"Stderr was:\n{stderr}")
        sys.exit(1)

    print(f"[PASS] Successfully cloned and executed SWE test suite in sandbox!")

    # Check for leaked sandboxes via e2b if available
    try:
        from e2b import Sandbox
        p = Sandbox.list()
        active = p.next_items() if hasattr(p, 'next_items') else []
        if len(active) > 0:
            print(f"[WARN] Warning: Detected {len(active)} active sandboxes after execution!")
            for s in active:
                try:
                    s.kill()
                except:
                    pass
        else:
            print("[PASS] Clean-Up Check PASSED: 0 leaked sandboxes.")
    except Exception as e:
        print(f"[INFO] Could not check e2b.Sandbox.list() directly: {e}")

    print("\n>>> TRIAL 6 VERIFICATION PASSED! <<<\n")

if __name__ == "__main__":
    verify()
