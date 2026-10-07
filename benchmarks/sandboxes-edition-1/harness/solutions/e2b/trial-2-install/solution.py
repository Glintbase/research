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
        # Install the Python package 'polars'
        install_res = sandbox.commands.run("pip install polars")
        if install_res.exit_code != 0:
            print(f"Error installing polars: {install_res.stderr}", file=sys.stderr)
            sys.exit(1)

        # Execute script that calculates and prints the sum using polars
        script = (
            "import polars as pl\n"
            "print(f\"SUM:{pl.Series([10, 20, 30]).sum()}\")\n"
        )
        sandbox.files.write("test_polars.py", script)
        result = sandbox.commands.run("python3 test_polars.py")

        # Print the script's output
        print(result.stdout.strip())
    finally:
        # Delete / close the sandbox cleanly
        sandbox.kill()

if __name__ == "__main__":
    main()
