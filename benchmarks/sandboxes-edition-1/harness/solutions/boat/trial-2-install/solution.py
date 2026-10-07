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
    # Create a remote Boat Sandbox
    res = api.create(create_sandbox_request=boat_sdk.CreateSandboxRequest(env={"PIP_BREAK_SYSTEM_PACKAGES": "1"}))
    sb_id = res.sandbox.id
    boat_sdk.wait_until_ready(api, sb_id, timeout_seconds=60)

    # Ensure pip permits installation in system environment
    boat_sdk.exec_command(api, sb_id, "pip config set global.break-system-packages true")

    # 1. Install polars
    boat_sdk.exec_command(api, sb_id, "pip install polars", timeout_seconds=120)

    # 2. Execute a Python script that calculates
    cmd = boat_sdk.exec_command(api, sb_id, "python3 -c \"import polars as pl; print(f'SUM:{pl.Series([10, 20, 30]).sum()}')\"")
    stdout_text = cmd.actual_instance.stdout if hasattr(cmd, 'actual_instance') else str(cmd)
    print(stdout_text.strip())
finally:
    # 3. Cleanly delete the sandbox
    if sb_id is not None:
        try:
            boat_sdk.stop_and_remove(api, sb_id, delete=True)
        except Exception as e:
            print(f"Error removing sandbox: {e}")
