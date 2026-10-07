import os
import sys
from dotenv import load_dotenv
from e2b import Sandbox

def main():
    load_dotenv()
    api_key = os.getenv("E2B_API_KEY")

    # Create E2B sandbox
    sandbox = Sandbox.create(api_key=api_key)
    try:
        # 1. Clone repository
        clone_res = sandbox.commands.run("git clone --depth 1 https://github.com/bottlepy/bottle")
        if clone_res.exit_code != 0:
            print(f"Clone error: {clone_res.stderr}", file=sys.stderr)
            sys.exit(1)

        # 2. Install pytest inside sandbox and run the test suite
        install_res = sandbox.commands.run("pip install --quiet pytest")
        if install_res.exit_code != 0:
            print(f"Install error: {install_res.stderr}", file=sys.stderr)
            sys.exit(1)

        test_res = sandbox.commands.run("cd bottle && pytest")
        if test_res.stdout:
            print(test_res.stdout.strip())
        if test_res.stderr:
            print(test_res.stderr.strip(), file=sys.stderr)

        # 3. Print the final summary of the test run containing 'TEST_SUITE_FINISHED'
        print("TEST_SUITE_FINISHED")
    finally:
        # 4. Delete/close the sandbox cleanly
        sandbox.kill()

if __name__ == "__main__":
    main()
