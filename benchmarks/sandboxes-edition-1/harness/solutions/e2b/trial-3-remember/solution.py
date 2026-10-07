import os
from dotenv import load_dotenv
from e2b import Sandbox

# Read E2B_API_KEY from .env or environment variable
load_dotenv()
api_key = os.getenv("E2B_API_KEY")

def main():
    # Create an E2B sandbox
    sandbox = Sandbox.create(api_key=api_key)
    try:
        # 1. Run a command that creates and writes the secret code 'STATE-PERSIST-991' to a file named /tmp/state.txt
        sandbox.commands.run("echo 'STATE-PERSIST-991' > /tmp/state.txt")

        # 2. In a separate, subsequent command execution on the same sandbox, read /tmp/state.txt and print its contents
        result = sandbox.commands.run("cat /tmp/state.txt")
        print(result.stdout.strip())
    finally:
        # Cleanly close and delete the sandbox
        sandbox.kill()

if __name__ == "__main__":
    main()
