import os
from dotenv import load_dotenv
import boat_sdk

# Load credentials from .env or environment
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

    # Execute command inside sandbox
    cmd = boat_sdk.exec_command(api, sb_id, "echo GLINT-BOAT-9103")
    stdout_text = cmd.actual_instance.stdout if hasattr(cmd, 'actual_instance') else str(cmd)
    print(stdout_text.strip())
finally:
    # Cleanly delete sandbox
    if sb_id is not None:
        try:
            boat_sdk.stop_and_remove(api, sb_id, delete=True)
        except Exception as e:
            print(f"Error removing sandbox: {e}")
