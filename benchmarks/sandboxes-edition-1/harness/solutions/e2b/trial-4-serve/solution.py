import os
import sys
import time
import requests
from dotenv import load_dotenv
from e2b import Sandbox

# Read E2B_API_KEY from .env or environment variable
load_dotenv()
api_key = os.getenv("E2B_API_KEY")

SERVER_SCRIPT = """from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'GLINT-SERVER-OK')

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8000), Handler)
    server.serve_forever()
"""

def main():
    # 1. Initialize an E2B sandbox
    sandbox = Sandbox.create(api_key=api_key)
    try:
        # Write server script and launch it in the background on port 8000
        sandbox.files.write("/tmp/server.py", SERVER_SCRIPT)
        sandbox.commands.run("python3 /tmp/server.py", background=True)

        # 2. Get host address for port 8000
        host = sandbox.get_host(8000)

        target_urls = [f"https://{host}", f"http://{host}"]
        response_text = None

        # Poll until the server responds
        start_time = time.time()
        while time.time() - start_time < 30:
            for url in target_urls:
                try:
                    res = requests.get(url, timeout=5)
                    if res.status_code == 200 and "GLINT-SERVER-OK" in res.text:
                        response_text = res.text
                        break
                except Exception:
                    pass
            if response_text:
                break
            time.sleep(1)

        if not response_text:
            raise RuntimeError(f"Failed to reach server on {host} within timeout")

        # 3. Print the HTTP response text confirming it contains 'GLINT-SERVER-OK'
        print(response_text)
    finally:
        # 4. Delete/close the sandbox cleanly
        sandbox.kill()

if __name__ == "__main__":
    main()
