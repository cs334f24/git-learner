from flask import Blueprint, render_template

from .auth import login_required

bp = Blueprint("modules", __name__)

@bp.route("/modules")
def modules_home():
    modules = [
        {"id": i, "name": f"Module {i+1}", "step": 2 * i, "total_steps": 3 * i + 1}
        for i in range(5)
    ]
    return render_template('modules_home.html', modules=modules)

@login_required
@bp.route("/modules/<module_id>")
def module_page(module_id: str):
    print("loading module:", module_id)
    return f"<h1>Loading Module {module_id} ...</h1>"


@login_required
@bp.route("/modules/<module_id>/step/<int:module_step>")
def module_setp(module_id: str, module_step: int):
    print(f"On Module {module_id} step {module_step}")
    return f"<h1>Module {module_id}</h1><h2>Step {module_step}</h2>"
