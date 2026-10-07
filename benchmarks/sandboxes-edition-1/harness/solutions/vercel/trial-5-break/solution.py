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
        print("Error: Missing required Vercel credentials (VERCEL_TOKEN, VERCEL_PROJECT_ID, VERCEL_TEAM_ID)", file=sys.stderr)
        sys.exit(1)

    # Create remote Vercel Sandbox
    sandbox = create_sandbox()
    try:
        # 1 & 2: Intentionally trigger an error inside the sandbox and catch/read error message
        try:
            sandbox.run_process("python3", ["-c", "1 / 0"], capture_output=True, check=True)
        except Exception as err:
            stderr_msg = getattr(err, "stderr", None)
            err_msg = stderr_msg.strip() if stderr_msg else str(err)
            print(f"CAUGHT_ERROR: {err_msg}")

        # 3. Verify that the sandbox is still responsive by executing a subsequent probe that prints 'HEALTHY-RECOVERY-77'
        recovery_res = sandbox.run_process("python3", ["-c", "print('HEALTHY-RECOVERY-77')"], capture_output=True, check=True)
        if recovery_res.stdout:
            print(recovery_res.stdout.strip())
    finally:
        # 4. Delete/close the sandbox cleanly in a finally block
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
