from github import Github
from github.Repository import Repository

from modules import Module, create_repo
from modules.steps import CheckResult, Step


class AddReadme(Step):
    def __init__(self): ...
    def action(self, repo: Repository):
        repo.create_file(
            "README.md",
            "Initialize repository",
            """# README

Welcome to git-learner!""",
        )

    def check(self, repo: Repository) -> CheckResult:
        if repo.get_readme():
            return CheckResult.GOOD
        else:
            return CheckResult.UNRECOVERABLE

    def instructions(self, repo: Repository) -> str:
        return """"Welcome to Git Learner!

This is an introductory step, meant exclusively for testing"""


class DummyStep(Step):
    def __init__(self, text: str):
        self.text = text

    def action(self, repo: Repository):
        return

    def check(self, repo: Repository) -> CheckResult:
        return CheckResult.GOOD

    def instructions(self, repo: Repository) -> str:
        return f"Instructions: {self.text}"


def initialzier(github: Github):
    return create_repo(github, "cs334f24")


steps = []

steps.append(AddReadme())
steps.extend(DummyStep(f"this step does nothing: {i}") for i in range(5))


module = Module("basic module", initialzier, steps)
