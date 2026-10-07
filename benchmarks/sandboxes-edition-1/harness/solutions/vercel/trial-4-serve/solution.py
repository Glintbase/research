import os
import sys
import time
import ssl
import urllib.request
from dotenv import load_dotenv
from vercel.sandbox.sync import create_sandbox


SERVER_CODE = """from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(b"GLINT-SERVER-OK")))
        self.end_headers()
        self.wfile.write(b"GLINT-SERVER-OK")

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    server.serve_forever()
"""


def main():
    # Read VERCEL credentials from .env or environment variables
    load_dotenv()

    token = os.getenv("VERCEL_TOKEN")
    project_id = os.getenv("VERCEL_PROJECT_ID")
    team_id = os.getenv("VERCEL_TEAM_ID")

    if not (token and project_id and team_id):
        print(
            "Error: Missing required Vercel credentials (VERCEL_TOKEN, VERCEL_PROJECT_ID, VERCEL_TEAM_ID)",
            file=sys.stderr,
        )
        sys.exit(1)

    # 1. Create a Vercel Sandbox with port 8000 exposed
    sandbox = create_sandbox(ports=[8000])

    try:
        # 2. Find the external route/URL for port 8000 using sandbox.routes
        matching_routes = [r.url for r in sandbox.routes if r.port == 8000]
        if not matching_routes:
            raise RuntimeError("No route found for port 8000 in sandbox.routes")

        route_url = matching_routes[0]
        if not route_url.startswith("http://") and not route_url.startswith("https://"):
            route_url = f"https://{route_url}"

        # 3. Start a simple HTTP server inside the sandbox on port 8000
        # Write server script and launch it with create_process
        try:
            sandbox.fs.write_text("server.py", SERVER_CODE)
            sandbox.create_process("python3", ["server.py"])
        except Exception:
            sandbox.create_process("python3", ["-c", SERVER_CODE])

        # 4. Wait a few seconds for the server to be ready, then send HTTP GET request
        response_text = None
        deadline = time.time() + 45
        last_error = None

        while time.time() < deadline:
            time.sleep(1)
            for verify_ssl in (True, False):
                try:
                    req = urllib.request.Request(
                        route_url,
                        headers={"User-Agent": "Mozilla/5.0"},
                    )
                    ctx = (
                        ssl.create_default_context()
                        if verify_ssl
                        else ssl._create_unverified_context()
                    )
                    with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
                        body = resp.read().decode("utf-8")
                        if "GLINT-SERVER-OK" in body:
                            response_text = body
                            break
                except Exception as err:
                    last_error = err

            if response_text:
                break

        if response_text is None:
            raise RuntimeError(
                f"Failed to receive GLINT-SERVER-OK from {route_url}. Last error: {last_error}"
            )

        # 5. Print the response text confirming it contains 'GLINT-SERVER-OK'
        print(response_text.strip())

    finally:
        # 6. Cleanly stop and destroy the sandbox in a finally block
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
