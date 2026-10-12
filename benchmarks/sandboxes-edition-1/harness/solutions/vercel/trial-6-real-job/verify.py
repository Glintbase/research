#!/usr/bin/env python3
"""
Verification Script for Vercel Sandbox - Trial 6 (Real Job - Git Clone & Test Execution)
Asserts:
1. solution.py exists
2. Running solution.py finishes and outputs 'TEST_SUITE_FINISHED' or test pass summary
3. Verifies that the sandbox is deleted/closed cleanly
"""

import os
import sys
import subprocess
import re
from dotenv import load_dotenv

load_dotenv()


def real_test_run_signal(text):
    """Correction (2026-10-12): require evidence that a real test suite ran and passed.

    Accepts either a unittest summary ("Ran N tests in ..." with N > 0 followed by an
    "OK" line) or a pytest summary ("N passed" with no failures or errors). The old
    check passed on the bare marker, or on the substrings "passed"/"ok" anywhere in
    stdout, which matched even when test/test_all.py did not exist.
    """
    ran = re.search(r"^Ran (\d+) tests? in ", text, re.M)
    if ran and int(ran.group(1)) > 0 and re.search(r"^OK\b", text[ran.end():], re.M):
        return True
    summary = re.search(r"=+ (.*\b(\d+) passed\b.*) =+", text)
    if summary and int(summary.group(2)) > 0 and not re.search(r"\b\d+ (failed|errors?)\b", summary.group(1)):
        return True
    return False

EXPECTED_OUTPUT = "TEST_SUITE_FINISHED"

def verify():
    print("[*] Running Verification for Vercel Sandbox - Trial 6: Real Job (SWE Test Execution)...")

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

    combined = stdout + "\n" + (stderr or "")
    if EXPECTED_OUTPUT not in stdout or not real_test_run_signal(combined):
        print(f"[FAIL] No evidence of a real, passing test run (need '{EXPECTED_OUTPUT}' plus a unittest 'Ran N tests ... OK' or pytest 'N passed' summary)!")
        print(f"Stdout was:\n{stdout}")
        if stderr:
            print(f"Stderr was:\n{stderr}")
        sys.exit(1)

    print(f"[PASS] Test suite ran and passed (real test-run summary found).")

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
        print("\n>>> VERCEL TRIAL 6 VERIFICATION FAILED (leak check) <<<\n")
        sys.exit(1)

    print("\n>>> VERCEL TRIAL 6 VERIFICATION PASSED! <<<\n")

if __name__ == "__main__":
    verify()
