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

    # 1. Run a command that creates and writes the secret code 'STATE-PERSIST-991' to a file named /tmp/state.txt
    print("Writing secret to /tmp/state.txt...")
    write_res = sb.process.exec("echo 'STATE-PERSIST-991' > /tmp/state.txt")
    print(f"Write exit code: {getattr(write_res, 'exit_code', 0)}")

    # 2. In a separate, subsequent command execution on the same sandbox, read /tmp/state.txt and print its contents
    print("Reading /tmp/state.txt...")
    read_res = sb.process.exec("cat /tmp/state.txt")

    # 3. Print the second command's output (must contain 'STATE-PERSIST-991')
    output = read_res.result if hasattr(read_res, "result") else str(read_res)
    print(output.strip())

finally:
    # 4. Cleanly delete the sandbox using client.delete(sb) in a finally block
    if sb is not None:
        print("Deleting sandbox...")
        client.delete(sb)
        print("Sandbox deleted.")
