import time

from flask import Flask
from github import Auth, Github, GithubIntegration

from db.create import DBManager
from modules import active_modules


class FlaskGithub:
    """A Flask extension that manages a GitHub app's acces token"""

    def __init__(self, app: Flask | None = None):
        self.github = None
        self.token = None
        self.token_expires = 0
        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        app_id = app.config["GITHUB_APP_ID"]
        self.org_name = app.config["GITHUB_ORGANIZATION"]
        private_key = app.config["GITHUB_PRIVATE_KEY"]

        self.auth = Auth.AppAuth(app_id, private_key)

        self.refresh_token()

    def refresh_token(self):
        gi = GithubIntegration(auth=self.auth)
        installation = gi.get_org_installation(self.org_name)
        access_token = gi.get_access_token(installation.id)
        self.token = access_token.token
        self.token_expires = access_token.expires_at.timestamp()

        self.github = Github(self.token)

    def get_client(self):
        if time.time() > self.token_expires - 60:
            self.refresh_token()
        assert self.github
        return self.github


class FlaskGitLearner:
    """A Flask extension for discovery of git-learner modules"""

    def __init__(self, app: Flask | None = None):
        self.active_modules = active_modules
        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        db = DBManager(app.config["DB_FILE"])
        for module_name, module in self.active_modules.items():
            db.modules.add(
                {"name": module_name, "total_steps": len(module), "base_repo": None}
            )
