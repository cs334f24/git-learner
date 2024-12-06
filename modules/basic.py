from github import Github, GithubException
from github.Repository import Repository

from module_core import CheckResult, Module, Step, create_repo


class AddReadme(Step):
    def __init__(self): ...
    def action(self, repo: Repository):
        repo.create_file(
            "README.md",
            "Initialize repository",
            """# README

Welcome to git-learner!""",
        )

    def check(self, repo: Repository) -> tuple[CheckResult, str]:
        return CheckResult.GOOD, ""

    def instructions(self, repo: Repository) -> str:
        return """
## Welcome to Git Learner!

This is an introductory step meant exclusively for testing

* here is
* a bulleted
* list

```bash
mkdir testing
cd a_code_block
```

here is some syntax highlighted python code
```python
name = input("What is your name?")
if name:
    print(f"Hello {name}!")
else:
    print("Hello World!")
```
"""


class DummyStep(Step):
    def __init__(self, text: str):
        self.text = text

    def action(self, repo: Repository):
        return

    def check(self, repo: Repository) -> tuple[CheckResult, str]:
        return CheckResult.GOOD, ""

    def instructions(self, repo: Repository) -> str:
        return f"Instructions: {self.text}"


def initialzier(github: Github):
    return create_repo(github, "cs334f24")


steps: list[Step] = []

steps.append(AddReadme())
steps.extend(DummyStep(f"this step does nothing: {i}") for i in range(5))


module = Module("basic module", initialzier, steps)
