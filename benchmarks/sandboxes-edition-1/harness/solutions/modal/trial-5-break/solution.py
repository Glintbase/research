import os
from dotenv import load_dotenv
import modal

# Read MODAL credentials from .env or environment variables
load_dotenv()

# Reference an app using modal.App.lookup
app = modal.App.lookup('glint-modal-app', create_if_missing=True)

sb = None
try:
    # 1. Create a running sandbox
    sb = modal.Sandbox.create('sleep', '300', app=app)

    # 2. Intentionally trigger an error inside the sandbox
    p1 = sb.exec('python3', '-c', '1 / 0')
    p1.wait()

    # 3. Read the error output from p1.stderr.read() and print: 'CAUGHT_ERROR: <error_details>'
    err_output = p1.stderr.read().strip()
    print(f"CAUGHT_ERROR: {err_output}")

    # 4. Verify that the sandbox is still responsive by executing a subsequent probe that prints 'HEALTHY-RECOVERY-77'
    p2 = sb.exec('echo', 'HEALTHY-RECOVERY-77')
    p2.wait()
    print(p2.stdout.read().strip())
finally:
    # 5. Cleanly terminate the sandbox using sb.terminate() in a finally block
    if sb is not None:
        try:
            sb.terminate()
        except Exception:
            pass
