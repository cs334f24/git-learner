import os

from dotenv import load_dotenv
from github import Github

from modules.create_repo import get_github


def simp_get_github():
    load_dotenv()
    org_name = os.environ["GITHUB_ORGANIZATION"]
    app_id = int(os.environ["GITHUB_APP_ID"])
    with open(os.environ["GITHUB_PRIVATE_KEY_PATH"]) as f:
        private_key = f.read()
    return get_github(private_key, app_id, org_name)


def delete_repo(github: Github, org_name: str, name: str):
    org = github.get_organization(org_name)
    repo = org.get_repo(name)
    repo.delete()
