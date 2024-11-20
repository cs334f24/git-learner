import os
import time

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, render_template, session
from github import Auth, Github, GithubIntegration


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


oauth = OAuth()
github_client = FlaskGithub()


def create_app() -> Flask:
    app = Flask(__name__)

    load_dotenv()
    app.secret_key = os.getenv("FLASK_SECRET")

    app.config.from_mapping(
        GITHUB_CLIENT_ID=os.getenv("GITHUB_CLIENT_ID"),
        GITHUB_CLIENT_SECRET=os.getenv("GITHUB_CLIENT_SECRET"),
        DB_FILE="data.sqlite3",
        GITHUB_APP_ID=int(os.environ["GITHUB_APP_ID"]),
        GITHUB_ORGANIZATION=os.getenv("GITHUB_ORGANIZATION"),
    )

    with open(os.environ["GITHUB_PRIVATE_KEY_PATH"]) as f:
        app.config["GITHUB_PRIVATE_KEY"] = f.read()

    oauth.init_app(app)
    github_client.init_app(app)

    github_oauth = oauth.register(
        name="github",
        client_id=app.config["GITHUB_CLIENT_ID"],
        client_secret=app.config["GITHUB_CLIENT_SECRET"],
        authorize_url="https://github.com/login/oauth/authorize",
        authorize_params=None,
        access_token_url="https://github.com/login/oauth/access_token",
        access_token_params=None,
        client_kwargs={"scope": "user:email"},
        api_base_url="https://api.github.com/",
    )
    assert github_oauth

    app.config["GITHUB_OAUTH"] = github_oauth

    @app.route("/")
    def index():
        user = session.get("user")
        if user:
            return render_template(
                "index.html",
                signed_in=True,
                user=user,
            )
        return render_template("index.html", signed_in=False)

    from .auth import bp as auth_bp

    app.register_blueprint(auth_bp)

    from .modules import bp as modules_bp

    app.register_blueprint(modules_bp)

    return app
