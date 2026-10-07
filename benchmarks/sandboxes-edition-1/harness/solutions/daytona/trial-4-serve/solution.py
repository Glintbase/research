import os
import time
import requests
from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig

# Read DAYTONA credentials from .env or environment variables
load_dotenv()

api_key = os.environ.get("DAYTONA_API_KEY")
if not api_key:
    raise ValueError("DAYTONA_API_KEY not found in environment or .env")

client = Daytona(DaytonaConfig(api_key=api_key))
sb = None

server_script = """import http.server
import socketserver

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'GLINT-SERVER-OK')

    def log_message(self, format, *args):
        pass

with ReusableTCPServer(('0.0.0.0', 8000), Handler) as httpd:
    httpd.serve_forever()
"""

try:
    print("Creating Daytona sandbox...")
    sb = client.create()
    print("Sandbox created successfully.")

    # 1. Start an HTTP server listening on port 8000 inside the sandbox
    print("Uploading server script to /tmp/server.py...")
    sb.fs.upload_file(server_script.encode("utf-8"), "/tmp/server.py")

    print("Starting HTTP server in background on port 8000...")
    sb.process.exec("bash -c 'nohup python3 /tmp/server.py > /tmp/srv.log 2>&1 &'")

    # 2. Obtain a public preview URL for port 8000
    print("Obtaining signed preview URL for port 8000...")
    signed = sb.create_signed_preview_url(8000, 300)
    preview_url = signed.url
    print(f"Preview URL: {preview_url}")

    # 3. Wait 2-3 seconds for the server to be ready, then send HTTP GET request
    time.sleep(3)

    response_text = ""
    for attempt in range(10):
        try:
            res = requests.get(preview_url, timeout=10)
            if res.status_code == 200 and "GLINT-SERVER-OK" in res.text:
                response_text = res.text
                break
            else:
                print(f"Attempt {attempt + 1}: status {res.status_code}, body: {res.text}")
        except Exception as e:
            print(f"Attempt {attempt + 1} request error: {e}")
        time.sleep(1)

    if not response_text and 'res' in locals():
        response_text = res.text

    print("Response body:")
    print(response_text.strip())

finally:
    # 4. Cleanly delete the sandbox using client.delete(sb) in a finally block
    if sb is not None:
        print("Deleting sandbox...")
        client.delete(sb, wait=True)
        print("Sandbox deleted.")
