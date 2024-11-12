import os

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, session, url_for


def create_app() -> Flask:
    app = Flask(__name__)

    load_dotenv()
    app.secret_key = os.getenv("FLASK_SECRET")

    app.config.from_mapping(
        GITHUB_CLIENT_ID=os.getenv("GITHUB_CLIENT_ID"),
        GITHUB_CLIENT_SECRET=os.getenv("GITHUB_CLIENT_SECRET"),
    )

    oauth = OAuth(app)

    github = oauth.register(
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
    assert github

    @app.route("/")
    def index():
        user = session.get("user")
        if user:
            user_data = {
                "name": user["name"],
                "login": user["login"],
                "avatar_url": user["avatar_url"],
                "github_url": user["html_url"],
            }
            return render_template(
                "index.html", title="Git Learner", signed_in=True, **user_data
            )
        return render_template("index.html", title="Git Learner", signed_in=False)

    @app.route("/auth/login")
    def login():
        redirect_uri = url_for("authorize", _external=True)
        return github.authorize_redirect(redirect_uri)
        # return github.authorize_redirect(redirect_uri)

    @app.route("/auth/callback")
    def authorize():
        token = github.authorize_access_token()
        user = github.get("user").json()
        session["user"] = user
        return redirect(url_for("index"))

    @app.route("/logout")
    def logout():
        session.pop("user", None)
        return redirect(url_for("index"))

    return app


if __name__ == "__main__":
    create_app().run(port=8080, debug=True)
