from functools import wraps

from flask import Blueprint, current_app, redirect, session, url_for

from db import DBManager

bp = Blueprint("auth", __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user") is None:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


@bp.route("/auth/login")
def login():
    oauth = current_app.config["GITHUB_OAUTH"]
    redirect_uri = url_for("auth.authorize", _external=True)
    return oauth.authorize_redirect(redirect_uri)


@bp.route("/auth/callback")
def authorize():
    oauth = current_app.config["GITHUB_OAUTH"]

    oauth.authorize_access_token()
    session["user"] = oauth.get("user").json()

    db = DBManager(current_app.config["DB_FILE"])
    db.add_user(
        session["user"]["name"],
        session["user"]["email"],
        session["user"]["login"],
    )

    return redirect(url_for("index"))


@bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))
