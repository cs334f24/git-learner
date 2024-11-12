from flask import Blueprint

from .auth import login_required

bp = Blueprint("modules", __name__)


@login_required
@bp.route("/module/<module_id>")
def module_home(module_id: str):
    print("loading module:", module_id)
    return f"<h1>Loading Module {module_id} ...</h1>"


@login_required
@bp.route("/module/<module_id>/step/<int:module_step>")
def module_setp(module_id: str, module_step: int):
    print(f"On Module {module_id} step {module_step}")
    return f"<h1>Module {module_id}</h1><h2>Step {module_step}</h2>"
