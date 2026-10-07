import os
import time
import requests
from dotenv import load_dotenv
import boat_sdk

# Load BOAT credentials from .env or environment variables
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

    # 1. Start HTTP server listening on port 8000
    srv_cmd = "nohup python3 -c 'import http.server, socketserver; h = http.server.SimpleHTTPRequestHandler; h.do_GET = lambda self: (self.send_response(200), self.end_headers(), self.wfile.write(b\"GLINT-SERVER-OK\")); socketserver.TCPServer((\"\", 8000), h).serve_forever()' > /tmp/srv.log 2>&1 &"
    boat_sdk.exec_command(api, sb_id, srv_cmd)

    # 2. Obtain the public URL for port 8000
    port_res = api.host_port(sb_id, boat_sdk.HostPortRequest(port=8000, public=True))
    url = port_res.url

    # 3. Wait 3 seconds, then send an HTTP GET request to url
    time.sleep(3)
    response_text = ""
    for attempt in range(5):
        try:
            resp = requests.get(url, timeout=15)
            response_text = resp.text
            if resp.status_code == 200 and "GLINT-SERVER-OK" in response_text:
                break
        except Exception as e:
            if attempt == 4:
                raise
        time.sleep(2)

    print(response_text)
finally:
    # 4. Cleanly delete the sandbox in a finally block
    if sb_id is not None:
        try:
            boat_sdk.stop_and_remove(api, sb_id, delete=True)
        except Exception as e:
            print(f"Error removing sandbox: {e}")
