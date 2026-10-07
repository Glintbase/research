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

    # Create remote Vercel Sandbox using create_sandbox()
    sandbox = create_sandbox()
    try:
        # Execute Python code inside the sandbox that prints the secret code
        result = sandbox.run_process("python3", ["-c", "print('GLINT-VERCEL-1092')"], capture_output=True)
        if result.stdout:
            print(result.stdout.strip())
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
