from module_core.steps import Module

from .basic import module as basic_module
from .clone_commit_update_push import module as push_after_update_module

active_modules: dict[str, Module] = {
    "basic module": basic_module,
    "push-after-update": push_after_update_module,
}

__all__ = ["basic_module", "active_modules"]
