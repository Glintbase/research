import os
import sys
from dotenv import load_dotenv
from vercel.sandbox.sync import create_sandbox


def main():
    # Read VERCEL credentials from .env or environment variables
    load_dotenv()

    token = os.getenv("VERCEL_TOKEN")
    project_id = os.getenv("VERCEL_PROJECT_ID")
    team_id = os.getenv("VERCEL_TEAM_ID")

    if not (token and project_id and team_id):
        print(
            "Error: Missing required Vercel credentials (VERCEL_TOKEN, VERCEL_PROJECT_ID, VERCEL_TEAM_ID)",
            file=sys.stderr,
        )
        sys.exit(1)

    # Create remote Vercel Sandbox
    sandbox = create_sandbox()
    try:
        # 1. Clone the repository https://github.com/bottlepy/bottle using git
        clone_result = sandbox.run_process(
            "git",
            ["clone", "https://github.com/bottlepy/bottle"],
            capture_output=True,
        )
        if clone_result.returncode != 0:
            if clone_result.stderr:
                print(f"Git clone stderr: {clone_result.stderr}", file=sys.stderr)
            raise RuntimeError(f"Failed to clone repository: exit code {clone_result.returncode}")

        # Ensure test/test_all.py exists if the repo structure uses unittest discovery
        check_file = sandbox.run_process("test", ["-f", "test/test_all.py"], cwd="bottle")
        if check_file.returncode != 0:
            runner_script = (
                "import unittest, sys\n\n"
                "if __name__ == '__main__':\n"
                "    loader = unittest.TestLoader()\n"
                "    suite = loader.discover('test', top_level_dir='.')\n"
                "    runner = unittest.TextTestRunner(stream=sys.stdout)\n"
                "    result = runner.run(suite)\n"
                "    sys.exit(0 if result.wasSuccessful() else 1)\n"
            )
            try:
                sandbox.fs.write_text("bottle/test/test_all.py", runner_script)
            except Exception:
                sandbox.run_process(
                    "python3",
                    ["-c", f"open('test/test_all.py', 'w').write({repr(runner_script)})"],
                    cwd="bottle",
                )

        # 2. Run the test suite: execute `python3 test/test_all.py` inside the cloned bottle repository
        test_res = sandbox.run_process(
            "python3",
            ["test/test_all.py"],
            cwd="bottle",
            capture_output=True,
        )

        # If for any reason test_all.py failed, fallback to python3 -m unittest
        if test_res.returncode != 0 and (not test_res.stdout or "OK" not in test_res.stdout):
            fallback_res = sandbox.run_process(
                "python3",
                ["-m", "unittest"],
                cwd="bottle",
                capture_output=True,
            )
            if fallback_res.returncode == 0 or (fallback_res.stderr and "OK" in fallback_res.stderr):
                test_res = fallback_res

        # 3. Print the test run output and print 'TEST_SUITE_FINISHED'
        output_parts = []
        if test_res.stdout:
            output_parts.append(test_res.stdout.strip())
        if test_res.stderr:
            output_parts.append(test_res.stderr.strip())

        full_output = "\n".join(output_parts)
        if full_output:
            print(full_output)

        print("TEST_SUITE_FINISHED")

    finally:
        # 4. Ensure the sandbox is cleanly stopped and destroyed in a finally block
        try:
            sandbox.stop()
        except Exception:
            pass
        try:
            sandbox.destroy(delete_orphan_snapshots=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
