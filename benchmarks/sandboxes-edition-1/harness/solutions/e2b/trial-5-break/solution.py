import os
import sys
from dotenv import load_dotenv
from e2b import Sandbox, CommandExitException

def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("E2B_API_KEY")

    # 1. Initialize E2B sandbox
    sandbox = Sandbox.create(api_key=api_key)
    try:
        # 1. Intentionally trigger an error inside the sandbox (e.g. running '1 / 0' to cause ZeroDivisionError)
        # 2. Catch or read the error message and print: 'CAUGHT_ERROR: <error_details>'
        try:
            res = sandbox.commands.run("python3 -c '1 / 0'")
            if res.exit_code != 0:
                print(f"CAUGHT_ERROR: {res.stderr.strip()}")
        except CommandExitException as e:
            err_msg = e.stderr.strip() if e.stderr else str(e)
            print(f"CAUGHT_ERROR: {err_msg}")
        except Exception as e:
            print(f"CAUGHT_ERROR: {e}")

        # 3. Verify that the sandbox is still responsive by executing a subsequent probe that prints 'HEALTHY-RECOVERY-77'
        recovery_res = sandbox.commands.run("python3 -c \"print('HEALTHY-RECOVERY-77')\"")
        print(recovery_res.stdout.strip())

    finally:
        # 4. Delete/close the sandbox cleanly
        sandbox.kill()

if __name__ == "__main__":
    main()
