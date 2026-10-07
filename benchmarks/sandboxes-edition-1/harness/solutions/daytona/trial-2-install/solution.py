import os
from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig

# Read DAYTONA credentials from .env or environment variables
load_dotenv()

api_key = os.environ.get("DAYTONA_API_KEY")
if not api_key:
    raise ValueError("DAYTONA_API_KEY not found in environment or .env")

client = Daytona(DaytonaConfig(api_key=api_key))
sb = None

try:
    print("Creating Daytona sandbox...")
    sb = client.create()
    print("Sandbox created successfully.")

    # 1. Install the Python package 'polars'
    print("Installing polars...")
    install_res = sb.process.exec("pip install polars")
    if install_res.exit_code != 0:
        # Fallback to python3 -m pip install polars
        install_res = sb.process.exec("python3 -m pip install polars")
    print(f"Install exit code: {install_res.exit_code}")

    # 2. Execute a Python script inside the sandbox that calculates and prints:
    # import polars as pl
    # print(f"SUM:{pl.Series([10, 20, 30]).sum()}")
    python_cmd = 'python3 -c "import polars as pl; print(f\\"SUM:{pl.Series([10, 20, 30]).sum()}\\")"'
    res = sb.process.exec(python_cmd)

    # 3. Print the script's output (must contain 'SUM:60')
    output = res.result if hasattr(res, "result") else str(res)
    print(output.strip())

finally:
    # 4. Cleanly delete the sandbox using client.delete(sb) in a finally block
    if sb is not None:
        print("Deleting sandbox...")
        client.delete(sb)
        print("Sandbox deleted.")
