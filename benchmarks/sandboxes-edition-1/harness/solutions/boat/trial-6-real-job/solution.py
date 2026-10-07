import os
from dotenv import load_dotenv
import boat_sdk

load_dotenv()
key = os.getenv("BOAT_API_KEY")
if not key:
    raise ValueError("BOAT_API_KEY not found in environment or .env")

config = boat_sdk.Configuration(access_token=key)
api = boat_sdk.BoatApi(boat_sdk.ApiClient(config))

sb_id = None
try:
    res = api.create(create_sandbox_request=boat_sdk.CreateSandboxRequest())
    sb_id = res.sandbox.id
    boat_sdk.wait_until_ready(api, sb_id, timeout_seconds=60)

    # 1. Clone repository
    boat_sdk.exec_command(api, sb_id, "git clone https://github.com/bottlepy/bottle /tmp/bottle", timeout_seconds=120)

    # 2. Run test suite
    cmd = boat_sdk.exec_command(api, sb_id, "cd /tmp/bottle && python3 test/test_all.py", timeout_seconds=120)

    # 3. Print test output
    output = getattr(cmd, "stdout", None) or getattr(getattr(cmd, "actual_instance", None), "stdout", "") or ""
    stderr = getattr(cmd, "stderr", None) or getattr(getattr(cmd, "actual_instance", None), "stderr", "") or ""
    if output:
        print(output)
    if stderr:
        print(stderr)

    print("TEST_SUITE_FINISHED")
finally:
    if sb_id:
        try:
            boat_sdk.stop_and_remove(api, sb_id, delete=True)
        except Exception as e:
            print(f"Error cleaning up sandbox {sb_id}: {e}")
