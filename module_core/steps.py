from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum

import wonderwords
from github import Github
from github.Repository import Repository


class CheckResult(Enum):
    """ The result of a Step's check"""
    USER_ERROR = "User Error"
    RECOVERABLE = "recoverable"
    GOOD = "Good"
    UNRECOVERABLE = "unrecoverable"


class Step(ABC):
    @abstractmethod
    def instructions(self, repo: Repository) -> str:
        pass

    @abstractmethod
    def action(self, repo: Repository):
        pass

    @abstractmethod
    def check(self, repo: Repository) -> tuple[CheckResult, str]:
        pass


def create_repo(github: Github, org_name: str) -> Repository:
    """Create a repository under an organization with a random adjective-noun name

    Params:
        github: an authenticated Github object to interact with the GitHub API
        org_name: the organization which the repo should be created under
    """
    r = wonderwords.RandomWord()
    adjective: str = r.word(include_parts_of_speech=["adjective"])
    noun: str = r.word(include_parts_of_speech=["noun"])
    repo_name = adjective + "-" + noun

    org = github.get_organization(org_name)
    return org.create_repo(f"{repo_name}")


def create_repo_from_template(github: Github, template: Repository, org_name: str):
    """Copies a template repository into a new repository under an organization

    Params:
        github: an authenticated Github object to interact with the GitHub API
        template: a repository object for the reposity to use as a template
        org_name: the organization which the repo should be created under
    """
    r = wonderwords.RandomWord()
    adjective: str = r.word(include_parts_of_speech=["adjective"])
    noun: str = r.word(include_parts_of_speech=["noun"])
    repo_name = adjective + "-" + noun

    org = github.get_organization(org_name)
    return org.create_repo_from_template(repo_name, template)


class Module:
    def __init__(
        self,
        name: str,
        initializer: Callable[[Github], Repository],
        steps: list[Step],
    ):
        self.name = name
        self.steps = steps
        self.initializer = initializer

    def create(self, github: Github) -> Repository:
        return self.initializer(github)

    def __len__(self):
        return len(self.steps)

    def __getitem__(self, index):
        if not isinstance(index, int):
            raise ValueError(f"Expected integer index, recieved {type(index)}")

        return self.steps[index]


class Session:
    def __init__(
        self,
        github: Github,
        user: str,
        org_name: str,
        module: Module,
        repo_name: str | None = None,
        current_step: int = 0,
    ):
        """
        Raises:
            ValueError: current_step is not a valid value (too large or too small
        """
        if not 0 <= current_step < len(module) - 1:
            raise ValueError("Invalid current step")

        self.user = user
        self.current_step = current_step
        self.module = module
        self.github = github

        # create repo if no repo_name is passed
        if not repo_name:
            self.repo = module.create(self.github)
            self.repo_name = self.repo.name
        else:
            self.repo_name = repo_name
            self.repo = self.github.get_repo(f"{org_name}/{repo_name}")

    def instructions(self) -> str:
        """Return the instructions for the current step"""
        return self.module[self.current_step].instructions(self.repo)

    def check(self) -> bool:
        """Return if the current step passes it's check"""
        return self.module[self.current_step].check(self.repo) == CheckResult.GOOD

    def next(self) -> bool:
        step = self.module[self.current_step]
        check_result, self.toast = step.check(self.repo)
        match check_result:
            case CheckResult.GOOD:
                self.current_step += 1
                step = self.module[self.current_step]
                step.action(self.repo)
                self.text = step.instructions(self.repo)
                return True
            case CheckResult.USER_ERROR:
                # TODO: pass some error message to user
                return False
            case CheckResult.RECOVERABLE:
                # TODO: use recovery strategy
                return False
            case CheckResult.UNRECOVERABLE:
                raise Exception("Unrecoverable Error Occured!")

    def cleanup(self):
        """Delete the repository associated with this module"""
        self.repo.delete()
