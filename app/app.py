from authlib.integrations.flask_client import OAuth
from flask import Flask, render_template


def create_app() -> Flask:
    app = Flask(__name__)

    oauth = OAuth(app)

    oauth.register(
        name="github",
        client_id="",
        client_secret="",
        access_token_url="",
        authorize_url="",
    )

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login")
    def login():
        return ""

    @app.route("/authorize")
    def authorize():
        return ""

    @app.route("/logout")
    def logout():
        return ""

    return app


if __name__ == "__main__":
    create_app().run(port=8080)
