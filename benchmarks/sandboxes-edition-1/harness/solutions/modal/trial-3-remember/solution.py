import os
from dotenv import load_dotenv
import modal

# Load environment variables / Modal credentials
load_dotenv()

# Reference or lookup the Modal app
app = modal.App.lookup('glint-modal-app', create_if_missing=True)

sb = None
try:
    # 1. Create a running sandbox
    sb = modal.Sandbox.create('sleep', '300', app=app)

    # 2. First command execution: write secret code to /tmp/state.txt
    p1 = sb.exec('sh', '-c', 'echo STATE-PERSIST-991 > /tmp/state.txt')
    p1.wait()

    # 3. Subsequent command execution on the same sandbox: read /tmp/state.txt and print contents
    p2 = sb.exec('cat', '/tmp/state.txt')
    p2.wait()
    print(p2.stdout.read().strip())
finally:
    # 4. Cleanly terminate sandbox
    if sb is not None:
        try:
            sb.terminate()
        except Exception:
            pass
