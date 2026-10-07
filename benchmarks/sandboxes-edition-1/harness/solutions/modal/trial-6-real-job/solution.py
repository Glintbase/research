import os
import sys
from dotenv import load_dotenv
import modal

# Load credentials from .env or environment variables
load_dotenv()

app = modal.App.lookup('glint-modal-app', create_if_missing=True)

image = modal.Image.debian_slim().apt_install('git')
sb = modal.Sandbox.create('sleep', '300', app=app, image=image)

try:
    p1 = sb.exec('git', 'clone', 'https://github.com/bottlepy/bottle', '/tmp/bottle')
    p1.wait()
    p2 = sb.exec('python3', 'test/test_all.py', workdir='/tmp/bottle')
    p2.wait()
    print(p2.stdout.read())
    print('TEST_SUITE_FINISHED')
finally:
    sb.terminate()
