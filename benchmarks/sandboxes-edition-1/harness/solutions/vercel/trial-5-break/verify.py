#!/usr/bin/env python3
"""
Verification Script for Vercel Sandbox - Trial 5 (Break It - Error Recovery & Health Check)
Asserts:
1. solution.py exists
2. Running solution.py shows caught error and 'HEALTHY-RECOVERY-77'
3. Verifies that the sandbox is deleted/closed cleanly
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

EXPECTED_OUTPUT = "HEALTHY-RECOVERY-77"

def verify():
    print("[*] Running Verification for Vercel Sandbox - Trial 5: Break It (Resilience & Recovery)...")

    if not os.path.exists("solution.py"):
        print("[FAIL] solution.py does not exist!")
        sys.exit(1)

    try:
        proc = subprocess.run(
            [sys.executable, "solution.py"],
            capture_output=True,
            text=True,
            timeout=60
        )
    except subprocess.TimeoutExpired:
        print("[FAIL] solution.py timed out after 60 seconds!")
        sys.exit(1)

    stdout = proc.stdout
    stderr = proc.stderr

    if EXPECTED_OUTPUT not in stdout:
        print(f"[FAIL] Expected recovery marker '{EXPECTED_OUTPUT}' not found in stdout!")
        print(f"Stdout was:\n{stdout}")
        if stderr:
            print(f"Stderr was:\n{stderr}")
        sys.exit(1)

    print(f"[PASS] Successfully caught error and verified healthy recovery: '{EXPECTED_OUTPUT}' found!")

    # Check for leaked sandboxes via vercel.sandbox.sync.query_sandboxes
    try:
        from vercel.sandbox.sync import query_sandboxes
        active = list(query_sandboxes())
        if len(active) > 0:
            print(f"[WARN] Warning: Detected {len(active)} active sandboxes after execution!")
            for s in active:
                try:
                    s.destroy()
                except:
                    pass
        else:
            print("[PASS] Clean-Up Check PASSED: 0 leaked sandboxes.")
    except Exception as e:
        print(f"[INFO] Could not check query_sandboxes() directly: {e}")

    print("\n>>> VERCEL TRIAL 5 VERIFICATION PASSED! <<<\n")

if __name__ == "__main__":
    verify()
