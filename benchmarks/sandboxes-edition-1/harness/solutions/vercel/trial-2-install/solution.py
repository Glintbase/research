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

    sandbox = create_sandbox()
    try:
        # Install the Python package 'polars'
        install_res = sandbox.run_process("python3", ["-m", "pip", "install", "polars"], capture_output=True)
        if install_res.returncode != 0:
            # Fallback to pip install if python3 -m pip had issues
            install_res = sandbox.run_process("pip", ["install", "polars"], capture_output=True)

        # Execute script inside the sandbox
        script = 'import polars as pl\nprint(f"SUM:{pl.Series([10, 20, 30]).sum()}")'
        result = sandbox.run_process("python3", ["-c", script], capture_output=True)
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr and result.returncode != 0:
            print(result.stderr, file=sys.stderr)
    finally:
        # Cleanly delete/close the sandbox
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
