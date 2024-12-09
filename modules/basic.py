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

    def check(self, repo: Repository, user: str ) -> tuple[CheckResult, str]:
        return CheckResult.GOOD, ""

    def instructions(self, repo: Repository) -> str:
        name = repo.name
        url = repo.html_url

        return f"""

## Welcome to Git Learner!
---

### This module will guide you through the basics of the Git Learner tool.

The Git Learner tool is designed to help you learn the basics of git and GitHub by guiding you through a series of steps.

Our tool is able to interact with the GitHub API to create repositories, push commits, and more! 
This mean we are able to create a repository for you to work with. like this one 
```{url}```

---
#### Before you can access the repository, you will need to accept the invitation to join the organization. To do this, follow the steps below:
* Click on the link above to access the repository.
* Click on the "Join" button to accept the invitation to join the organization.
* Once you have accepted the invitation, you will be able to access the repository and complete the steps in this module!

---
#### You can proceed to the next step once you have accepted the invitation to join the organization. 

"""
    
class DummyStep(Step):
    def instructions(self, repo: Repository) -> str:
        
        return """
## Working with Git Learner
---

While working in Git Learner, you will encounter certain steps that will not let you proceed until you have correctly completed the task.

For example, this step is a dummy step that does not require any action from you to proceed so if you click the check it will display a "Good" result.

If you were to not complete the task correctly, you would receive a status explaining what you need to do to proceed.

To complete this step, click the Next button below.




"""

    def action(self, repo: Repository):
        pass

    def check(self, repo: Repository, user: str) -> tuple[CheckResult, str]:
        return CheckResult.GOOD, ""




class EndStep(Step):
    def instructions(self, repo: Repository) -> str:
        return "You have completed this module!"

    def action(self, repo: Repository):
        pass

    def check(self, repo: Repository, user: str) -> tuple[CheckResult, str]:
        return CheckResult.GOOD, ""

def initialzier(github: Github):
    return create_repo(github, "cs334f24")


steps: list[Step] = []

steps.append(AddReadme())
steps.append(DummyStep())
steps.append(EndStep())


module = Module("basic module", initialzier, steps)
