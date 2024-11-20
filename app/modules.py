import markdown
from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    session,
    url_for,
)

from db.create import DBManager
from discover import basic
from modules.steps import CheckResult, Module, Session

from .app import github_client
from .auth import login_required

bp = Blueprint("modules", __name__)

MODULES: dict[str, Module] = {"basic module": basic.module}


@bp.route("/modules")
@login_required
def modules_home():
    db = DBManager(current_app.config["DB_FILE"])
    modules = db.modules.get()
    return render_template("modules_home.html", modules=modules)


@bp.route("/modules/<module_name>")
@login_required
def module_page(module_name: str):
    db = DBManager(current_app.config["DB_FILE"])
    module = db.modules.get(module_name)
    if not module:
        return f"Module {module_name} does not exist!", 404

    github = session["user"]["login"]

    session_info = db.sessions.get(github, module_name)
    if session_info:
        org_name = current_app.config["GITHUB_ORGANIZATION"]
        repo_url = f"https://github.com/{org_name}/" + session_info["repo"]
        return render_template(
            "module.html", module=module, session=session_info, repo_url=repo_url
        )

    return render_template("module.html", module=module)


@bp.get("/modules/<module_name>/new")
@login_required
def new_session(module_name: str):
    db = DBManager(current_app.config["DB_FILE"])
    module_info = db.modules.get(module_name)
    if not module_info or module_name not in MODULES:
        return f"Module {module_name} does not exist!", 404

    github = github_client.get_client()
    gh_user = session["user"]["login"]
    org_name = current_app.config["GITHUB_ORGANIZATION"]
    module = MODULES[module_name]

    # delete old session
    session_info = db.sessions.get(gh_user, module_name)
    if session_info:
        Session(
            github, gh_user, org_name, module, repo_name=session_info["repo"]
        ).cleanup()
        db.sessions.delete(gh_user, module_name)

    # create new session
    session_ = Session(github, gh_user, org_name, module)
    session_created = db.sessions.create_from_session(session_)
    if session_created:
        return redirect(
            url_for("modules.module_step", module_name=module_name, module_step=1)
        )

    return "An error occured while creating a session", 500


@bp.post("/modules/<module_name>/step/<int:module_step>")
@login_required
def module_step_check(module_name: str, module_step: int):
    db = DBManager(current_app.config["DB_FILE"])
    module_info = db.modules.get(module_name)
    assert not isinstance(module_info, list)

    if not module_info:
        return f"Module {module_name} does not exist!", 404
    if not 0 < module_step <= module_info["total_steps"]:
        return f"Step {module_step} does not exist!", 404

    gh_user = session["user"]["login"]
    session_info = db.sessions.get(gh_user, module_name)
    if not session_info:
        return f"No session found for {gh_user} in {module_name}", 404

    module = MODULES[module_name]
    session_ = Session(
        github_client.get_client(),
        gh_user,
        current_app.config["GITHUB_ORGANIZATION"],
        module,
        session_info["repo"],
        session_info["current_step"],
    )

    response: dict[str, int | str] = {"step": module_step - 1}
    result, response["message"] = module[module_step - 1].check(session_.repo)
    match result:
        case CheckResult.GOOD:
            response["status"] = "GOOD"
        case CheckResult.RECOVERABLE:
            response["status"] = "RECOVERABLE"
        case CheckResult.UNRECOVERABLE:
            response["status"] = "UNRECOVERABLE"
        case CheckResult.USER_ERROR:
            response["status"] = "USER_ERROR"

    return response


@bp.get("/modules/<module_name>/step/<int:module_step>")
@login_required
def module_step(module_name: str, module_step: int):
    db = DBManager(current_app.config["DB_FILE"])
    module_info = db.modules.get(module_name)
    assert not isinstance(module_info, list)

    if not module_info:
        return f"Module {module_name} does not exist!", 404
    if not 0 < module_step <= module_info["total_steps"]:
        return f"Step {module_step} does not exist!", 404

    gh_user = session["user"]["login"]
    session_info = db.sessions.get(gh_user, module_name)
    assert session_info

    module = MODULES[module_name]

    session_ = Session(
        github_client.get_client(),
        gh_user,
        current_app.config["GITHUB_ORGANIZATION"],
        module,
        session_info["repo"],
        session_info["current_step"],
    )
    instructions = module[module_step - 1].instructions(session_.repo)
    parsed_instructions = markdown.markdown(
        instructions, extensions=["fenced_code", "codehilite"]
    )

    # if factory := MODULES.get(module_name):
    #     m = factory(github, org_name, module_step, session_["repo"])
    #
    #     m.act()
    #     if m.can_continue():
    #         m.next()
    #     new_step = min(m.step_done + 1, len(m.steps) - 1) if m.step_done else m.step
    #     db.sessions.update(gh_user, module_name, new_step)

    # else:
    #     return f"Module {module_name} is not implemented yet"

    return render_template(
        "module_step.html",
        module_info=module_info,
        module_step=module_step,
        step_instructions=parsed_instructions,
    )


@bp.post("/modules/<module_name>/step/<int:module_step>/next")
@login_required
def module_step_next(module_name: str, module_step: int):
    return ""


@bp.get("/modules/<module_name>/progress")
@login_required
def module_progress(module_name: str):
    db = DBManager(current_app.config["DB_FILE"])
    gh_user = session["user"]["login"]
    progress = db.sessions.progress(gh_user, module_name)

    if progress is None:
        return "Could not find user's progress on session", 404

    return progress
