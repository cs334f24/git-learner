from functools import wraps

from flask import Blueprint, current_app, redirect, render_template, session, url_for

bp = Blueprint("auth", __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user") is None:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


@bp.route("/login")
def login_page():
    user = session.get("user")
    if user:
        return redirect(url_for("index"))
    return render_template("login.html", user=user)


@bp.route("/auth/login")
def login():
    oauth = current_app.config["GITHUB_OAUTH"]
    redirect_uri = url_for("auth.authorize", _external=True)
    return oauth.authorize_redirect(redirect_uri)


@bp.route("/auth/callback")
def authorize():
    oauth = current_app.config["GITHUB_OAUTH"]
    token = oauth.authorize_access_token()
    user = oauth.get("user").json()
    session["user"] = user
    return redirect(url_for("index"))


@bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))
