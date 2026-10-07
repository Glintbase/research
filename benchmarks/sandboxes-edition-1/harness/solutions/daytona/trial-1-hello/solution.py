import os
from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig

# Read DAYTONA credentials from .env or environment variables (DAYTONA_API_KEY)
load_dotenv()

api_key = os.environ.get("DAYTONA_API_KEY")
if not api_key:
    raise ValueError("DAYTONA_API_KEY not found in environment or .env")

# Create a remote Daytona Sandbox using client = Daytona(DaytonaConfig(api_key=key)) and sb = client.create()
client = Daytona(DaytonaConfig(api_key=api_key))
sb = None

try:
    print("Creating Daytona sandbox...")
    sb = client.create()
    print("Sandbox created successfully.")

    # Execute a Python command inside the sandbox using sb.process.exec(...) that prints the exact code: GLINT-DAYTONA-4019
    response = sb.process.exec("python3 -c \"print('GLINT-DAYTONA-4019')\"")
    output = response.result if hasattr(response, 'result') else str(response)
    print(output.strip())
finally:
    # Cleanly delete/close the sandbox using client.delete(sb) in a finally block
    if sb is not None:
        print("Deleting sandbox...")
        client.delete(sb)
        print("Sandbox deleted.")
