import os
import sys
from dotenv import load_dotenv
from e2b import Sandbox

def main():
    load_dotenv()
    api_key = os.getenv("E2B_API_KEY")

    # Create E2B sandbox
    sandbox = Sandbox.create(api_key=api_key)
    try:
        # Execute a Python script inside the sandbox that prints GLINT-HELLO-8492
        result = sandbox.commands.run("python3 -c \"print('GLINT-HELLO-8492')\"")
        print(result.stdout.strip())
    finally:
        # Delete / close the sandbox cleanly
        sandbox.kill()

if __name__ == "__main__":
    main()
