import os

from dotenv import load_dotenv

load_dotenv()
ORG_NAME = "cs334f24"
APP_ID = int(os.environ["GITHUB_APP_ID"])
PRIVATE_KEY_PATH = os.environ["GITHUB_PRIVATE_KEY_PATH"]
with open(PRIVATE_KEY_PATH) as f:
    PRIVATE_KEY = f.read()

