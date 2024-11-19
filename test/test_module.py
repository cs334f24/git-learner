import os

import pytest
from dotenv import load_dotenv
from github import Github, GithubException
from github.Repository import Repository

from modules.create_repo import get_github
from modules.steps import create_repo

load_dotenv()
ORG_NAME = "cs334f24"
APP_ID = int(os.environ["GITHUB_APP_ID"])
PRIVATE_KEY_PATH = os.environ["GITHUB_PRIVATE_KEY_PATH"]
with open(PRIVATE_KEY_PATH) as f:
    PRIVATE_KEY = f.read()


@pytest.fixture
def github():
    g = get_github(PRIVATE_KEY, APP_ID, ORG_NAME)
    yield g
    g.close()


@pytest.fixture
def repo(github: Github):
    repository = create_repo(github, ORG_NAME)
    assert repository
    yield repository
    repository.delete()


def test_create_delete_repo(github: Github):
    repo = create_repo(github, ORG_NAME)
    assert repo
    repo_name = repo.name
    retrv = github.get_repo(f"{ORG_NAME}/{repo_name}")
    assert retrv.url == repo.url

    repo.delete()
    with pytest.raises(GithubException):
        github.get_repo(f"{ORG_NAME}/{repo_name}")
