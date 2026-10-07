import os
from dotenv import load_dotenv
import modal

# Load environment variables / Modal credentials
load_dotenv()

# Reference or lookup the Modal app
app = modal.App.lookup('glint-modal-app', create_if_missing=True)

sb = None
try:
    # Create remote sandbox with polars installed
    image = modal.Image.debian_slim().pip_install('polars')
    sb = modal.Sandbox.create(
        'python3',
        '-c',
        'import polars as pl; print(f"SUM:{pl.Series([10, 20, 30]).sum()}")',
        app=app,
        image=image,
    )
    # Wait for completion
    sb.wait()
    # Print stdout
    stdout = sb.stdout.read()
    print(stdout)
finally:
    if sb is not None:
        try:
            sb.terminate()
        except Exception:
            pass
