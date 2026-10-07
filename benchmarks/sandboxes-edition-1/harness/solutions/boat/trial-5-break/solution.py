import os
from dotenv import load_dotenv
import boat_sdk

# Read BOAT credentials from .env or environment variables
load_dotenv()
key = os.getenv("BOAT_API_KEY")

if not key:
    raise ValueError("BOAT_API_KEY is not set.")

# Configure API client
config = boat_sdk.Configuration(access_token=key)
api = boat_sdk.BoatApi(boat_sdk.ApiClient(config))

sb_id = None
try:
    # Create remote Boat Sandbox
    res = api.create(create_sandbox_request=boat_sdk.CreateSandboxRequest())
    sb_id = res.sandbox.id
    boat_sdk.wait_until_ready(api, sb_id, timeout_seconds=60)

    # 1. Intentionally trigger an error inside the sandbox (e.g. execute python3 -c "1/0")
    # 2. Catch/read the error message and print: 'CAUGHT_ERROR: <error_details>'
    try:
        cmd_err = boat_sdk.exec_command(api, sb_id, 'python3 -c "1/0"')
        err_output = ""
        if hasattr(cmd_err, "actual_instance"):
            err_output = cmd_err.actual_instance.stderr or cmd_err.actual_instance.stdout
        else:
            err_output = getattr(cmd_err, "stderr", str(cmd_err))
        print(f"CAUGHT_ERROR: {err_output.strip()}")
    except Exception as e:
        print(f"CAUGHT_ERROR: {e}")

    # 3. Verify that the sandbox is still responsive by executing a subsequent probe that prints 'HEALTHY-RECOVERY-77'
    probe = boat_sdk.exec_command(api, sb_id, "echo HEALTHY-RECOVERY-77")
    probe_out = probe.actual_instance.stdout if hasattr(probe, "actual_instance") else str(probe)
    print(probe_out.strip())

finally:
    # 4. Cleanly delete the sandbox using boat_sdk.stop_and_remove(api, sb_id, delete=True) in a finally block
    if sb_id is not None:
        try:
            boat_sdk.stop_and_remove(api, sb_id, delete=True)
        except Exception as e:
            print(f"Error removing sandbox: {e}")
