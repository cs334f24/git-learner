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
from module_core import CheckResult, Session
from module_core.steps import UnrecoverableRepoStateException
from modules import active_modules as ACTIVE_MODULES

from .app import github_client, gitlearner
from .auth import login_required

bp = Blueprint("modules", __name__)


@bp.route("/modules")
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
            "module.html", module=module, session_info=session_info, repo_url=repo_url
        )

    return render_template("module.html", module=module)


@bp.get("/modules/<module_name>/new")
@login_required
def new_session(module_name: str):
    db = DBManager(current_app.config["DB_FILE"])
    module_info = db.modules.get(module_name)
    if not module_info or module_name not in ACTIVE_MODULES:
        return f"Module {module_name} does not exist!", 404

    github = github_client.get_client()
    gh_user = session["user"]["login"]
    org_name = current_app.config["GITHUB_ORGANIZATION"]
    module = ACTIVE_MODULES[module_name]

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
        session_.module[0].action(session_.repo)
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

    module = ACTIVE_MODULES[module_name]
    session_ = Session(
        github_client.get_client(),
        gh_user,
        current_app.config["GITHUB_ORGANIZATION"],
        module,
        session_info["repo"],
        module_step,
    )

    response: dict[str, int | str] = {"step": module_step}
    result, response["message"] = module[module_step - 1].check(session_.repo, gh_user)
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

    module = ACTIVE_MODULES[module_name]

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

    org_name = current_app.config["GITHUB_ORGANIZATION"]

    return render_template(
        "module_step.html",
        module_info=module_info,
        module_step=module_step,
        repo_url=f"https://github.com/{org_name}/{session_info['repo']}",
        session_info=session_info,
        step_instructions=parsed_instructions,
    )


@bp.post("/modules/<module_name>/step/<int:module_step>/next")
@login_required
def module_step_next(module_name: str, module_step: int):
    db = DBManager(current_app.config["DB_FILE"])
    module_info = db.modules.get(module_name)
    assert not isinstance(module_info, list)

    if not 0 < module_step + 1 <= module_info["total_steps"]:
        return f"No next step {module_step + 1}!", 404

    gh_user = session["user"]["login"]
    session_info = db.sessions.get(gh_user, module_name)
    if not session_info:
        return f"No session for {gh_user} in module {module_name}", 404

    if session_info["current_step"] != module_step:
        return (
            f"Currently on step {session_info['current_step']},"
            + "not {module_step}. Cannot go to next from here",
            400,
        )

    module = gitlearner.active_modules[module_name]

    session_ = Session(
        github_client.get_client(),
        gh_user,
        current_app.config["GITHUB_ORGANIZATION"],
        module,
        session_info["repo"],
        session_info["current_step"],
    )

    try:
        can_continue = session_.next()
    except UnrecoverableRepoStateException as e:
        return {"toast": str(e), "status": "Unrecoverable"}

    if can_continue:
        next_step = session_.current_step
        db.sessions.update(gh_user, module_name, next_step)
        return {
            "url": url_for(
                "modules.module_step",
                module_name=module_name,
                module_step=next_step,
            )
        }

    return {"toast": session_.toast, "status": "Recoverable"}


@bp.get("/modules/<module_name>/progress")
@login_required
def module_progress(module_name: str):
    db = DBManager(current_app.config["DB_FILE"])
    gh_user = session["user"]["login"]
    progress = db.sessions.progress(gh_user, module_name)

    if progress is None:
        return "Could not find user's progress on session", 404

    return progress
