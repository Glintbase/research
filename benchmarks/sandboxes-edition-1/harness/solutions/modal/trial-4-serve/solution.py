import os
import time
from dotenv import load_dotenv
import modal
import requests

# Read MODAL credentials from .env or environment variables
load_dotenv()

# Reference an app using modal.App.lookup
app = modal.App.lookup('glint-modal-app', create_if_missing=True)

server_code = '''import http.server, socketserver
class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"GLINT-SERVER-OK")
with socketserver.TCPServer(("", 8000), H) as s:
    s.serve_forever()
'''

sb = None
try:
    # 1. Start HTTP server inside sandbox
    sb = modal.Sandbox.create('python3', '-c', server_code, encrypted_ports=[8000], app=app)

    # 2. Obtain external public URL for port 8000
    tunnels = sb.tunnels(timeout=60)
    url = tunnels[8000].url

    # 3. Wait 2 seconds, then send HTTP GET request to url
    time.sleep(2)
    resp = requests.get(url)
    print(resp.text)
finally:
    # 4. Cleanly terminate the sandbox in finally block
    if sb is not None:
        try:
            sb.terminate()
        except Exception:
            pass
