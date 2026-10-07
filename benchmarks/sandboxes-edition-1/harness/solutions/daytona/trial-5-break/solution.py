import os
import sys
from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig

# Load credentials from .env or environment variables
load_dotenv()

api_key = os.getenv("DAYTONA_API_KEY")
if not api_key:
    raise ValueError("DAYTONA_API_KEY not found in environment or .env")

client = Daytona(DaytonaConfig(api_key=api_key))
sb = None

try:
    print("Creating Daytona sandbox...")
    sb = client.create()
    print("Sandbox created successfully.")

    # 1. Intentionally trigger an error inside the sandbox
    print("Triggering intentional error inside sandbox...")
    try:
        res = sb.process.exec("python3 -c '1/0'")
        if res.exit_code != 0:
            error_details = res.result.strip() if res.result else f"Non-zero exit code: {res.exit_code}"
            print(f"CAUGHT_ERROR: {error_details}")
        else:
            print(f"CAUGHT_ERROR: Command exited with 0 unexpectedly: {res.result}")
    except Exception as e:
        print(f"CAUGHT_ERROR: {e}")

    # 3. Verify that the sandbox is still responsive by executing a subsequent probe
    print("Verifying sandbox responsiveness with probe...")
    probe_res = sb.process.exec("echo HEALTHY-RECOVERY-77")
    output = probe_res.result if hasattr(probe_res, "result") else str(probe_res)
    print(output.strip())

finally:
    # 4. Cleanly delete/close the sandbox using client.delete(sb) in a finally block
    if sb is not None:
        print("Deleting sandbox cleanly...")
        try:
            client.delete(sb)
            print("Sandbox deleted.")
        except Exception as e:
            print(f"Error deleting sandbox: {e}")
