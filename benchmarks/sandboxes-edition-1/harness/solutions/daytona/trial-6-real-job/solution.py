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

    # 1. Clone the repository https://github.com/bottlepy/bottle using git
    print("Cloning repository https://github.com/bottlepy/bottle...")
    clone_res = sb.process.exec("git clone https://github.com/bottlepy/bottle /tmp/bottle")
    print(f"Git clone exit code: {clone_res.exit_code}")
    if clone_res.result:
        print(clone_res.result)

    # Install bottle in editable mode
    sb.process.exec("pip install -e .", cwd="/tmp/bottle")

    # Ensure test/test_all.py exists to run the test suite cleanly with top_level_dir='.'
    test_runner_setup = """python3 -c "
import os
if not os.path.exists('/tmp/bottle/test/test_all.py'):
    with open('/tmp/bottle/test/test_all.py', 'w') as f:
        f.write('''import sys, os, unittest
sys.path.insert(0, os.path.abspath('.'))
if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover('test', top_level_dir='.')
    res = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)
''')
" """
    sb.process.exec(test_runner_setup)

    # 2. Run the test suite: execute python3 test/test_all.py inside the cloned bottle repository
    print("Running test suite...")
    test_res = sb.process.exec("python3 test/test_all.py", cwd="/tmp/bottle")
    print(f"Test run exit code: {test_res.exit_code}")

    # 3. Print the test run output and print 'TEST_SUITE_FINISHED'
    output = test_res.result if hasattr(test_res, "result") else str(test_res)
    print(output)
    print("TEST_SUITE_FINISHED")

finally:
    # 4. Ensure the sandbox is cleanly deleted in a finally block using client.delete(sb)
    if sb is not None:
        print("Deleting sandbox...")
        try:
            client.delete(sb)
            print("Sandbox deleted.")
        except Exception as e:
            print(f"Error deleting sandbox: {e}")
