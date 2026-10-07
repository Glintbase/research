import os
from dotenv import load_dotenv
import modal

# Load environment variables / Modal credentials
load_dotenv()

# Reference or lookup the Modal app
app = modal.App.lookup('glint-modal-app', create_if_missing=True)

sb = None
try:
    # Create remote sandbox
    sb = modal.Sandbox.create('python3', '-c', 'print("GLINT-MODAL-5821")', app=app)
    # Wait for completion
    sb.wait()
    # Print stdout
    print(sb.stdout.read().strip())
finally:
    if sb is not None:
        try:
            sb.terminate()
        except Exception:
            pass
