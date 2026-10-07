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
        # 1. Run a command that creates and writes the secret code 'STATE-PERSIST-991' to /tmp/state.txt
        write_res = sandbox.run_process("sh", ["-c", "printf 'STATE-PERSIST-991' > /tmp/state.txt"], capture_output=True)
        if write_res.returncode != 0:
            # Fallback to python3 if sh isn't standard in the container
            write_res = sandbox.run_process("python3", ["-c", "with open('/tmp/state.txt', 'w') as f: f.write('STATE-PERSIST-991')"], capture_output=True)

        # 2. In a separate, subsequent command execution on the same sandbox, read /tmp/state.txt and print its contents
        read_res = sandbox.run_process("cat", ["/tmp/state.txt"], capture_output=True)
        if read_res.returncode != 0:
            read_res = sandbox.run_process("python3", ["-c", "with open('/tmp/state.txt') as f: print(f.read())"], capture_output=True)

        # Print the second command's output
        if read_res.stdout:
            print(read_res.stdout.strip())
        elif read_res.stderr:
            print(f"Error reading file: {read_res.stderr}", file=sys.stderr)
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
