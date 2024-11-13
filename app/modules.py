from flask import Blueprint, current_app, redirect, render_template, session, url_for

from db.create import DBManager
from modules.create_repo import get_github, test_module

from .auth import login_required

bp = Blueprint("modules", __name__)

MODULES = {"test_module": test_module}


@bp.route("/modules")
def modules_home():
    db = DBManager(current_app.config["DB_FILE"])
    modules = db.get_modules()
    return render_template("modules_home.html", modules=modules)


@login_required
@bp.route("/modules/<module_name>")
def module_page(module_name: str):
    db = DBManager(current_app.config["DB_FILE"])
    module = db.get_module(module_name)
    if not module:
        return f"Module {module_name} does not exist!", 404

    user = session.get("user")
    github = user["login"]
    session_ = db.get_session(github, module_name)
    return render_template("module.html", module=module, session=session_)


@login_required
@bp.get("/modules/<module_name>/new")
def new_session(module_name: str):
    db = DBManager(current_app.config["DB_FILE"])
    module = db.get_module(module_name)
    if not module:
        return f"Module {module_name} does not exist!", 404

    gh_user = session["user"]["login"]
    db.delete_session(gh_user, module_name)
    session_created = db.create_session(gh_user, module_name)
    if session_created:
        return redirect(
            url_for("modules.module_step", module_name=module_name, module_step=0)
        )

    return "An error occured while creating a session", 500


@login_required
@bp.get("/modules/<module_name>/step/<int:module_step>")
def module_step(module_name: str, module_step: int):
    db = DBManager(current_app.config["DB_FILE"])
    module = db.get_module(module_name)
    if not module:
        return f"Module {module_name} does not exist!", 404
    if module_step > module["total_steps"]:
        return f"Step {module_step} does not exist!", 404

    gh_user = session["user"]["login"]
    session_ = db.get_session(gh_user, module_name)

    if factory := MODULES.get(module_name):
        private_key = current_app.config["GITHUB_PRIVATE_KEY"]
        org_name = current_app.config["GITHUB_ORGANIZATION"]
        app_id = current_app.config["GITHUB_APP_ID"]

        github = get_github(private_key, app_id, org_name)
        m = factory(github, org_name, module_step, session_["repo"])

        m.act()
        if m.can_continue():
            m.next()
        new_step = min(m.step_done + 1, len(m.steps) - 1) if m.step_done else m.step
        db.update_session(m.data["repo_name"], gh_user, new_step)
    else:
        return f"Module {module_name} is not implemented yet"

    return render_template("module_step.html", module=module, module_step=module_step)
