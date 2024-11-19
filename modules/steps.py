from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum

import wonderwords
from github import Github
from github.Repository import Repository


class CheckResult(Enum):
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
    def check(self, repo: Repository) -> CheckResult:
        pass


def create_repo(github: Github, org_name: str) -> Repository | None:
    r = wonderwords.RandomWord()
    adjective: str = r.word(include_parts_of_speech=["adjective"])
    noun: str = r.word(include_parts_of_speech=["noun"])
    repo_name = adjective + "-" + noun

    org = github.get_organization(org_name)
    return org.create_repo(f"{org_name}/{repo_name}")


class Module:
    def __init__(
        self,
        name: str,
        initializer: Callable[[], Repository],
        steps: list[Step],
    ):
        self.name = name
        self.steps = steps
        self.initializer = initializer

    def create(self) -> Repository:
        return self.initializer()

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
        repo_name: str,
        org_name: str,
        module: Module,
        current_step: int = 0,
    ):
        """
        Raises:
            ValueError: current_step is not a valid value (too large or too small
        """
        if not 0 < current_step < len(module):
            raise ValueError("Invalid current step")

        self.user = user
        self.repo_name = repo_name
        self.current_step = current_step
        self.module = module
        self.github = github
        self.repo = self.github.get_repo(f"{org_name}/{repo_name}")

    def can_continue(self) -> bool:
        """Return if the current step passes it's check"""
        return self.module[self.current_step].check(self.repo) == CheckResult.GOOD

    def next(self):
        step = self.module[self.current_step]
        check_result = step.check(self.repo)
        match check_result:
            case CheckResult.GOOD:
                self.current_step += 1
                step = self.module[self.current_step]
                step.action(self.repo)
                self.text = step.instructions(self.repo)
                self.toast = ""
            case CheckResult.USER_ERROR:
                # TODO: pass some error message to user
                self.toast = "you goofed"
                pass
            case CheckResult.RECOVERABLE:
                # TODO: use recovery strategy
                self.toast = "we goofed, and we're fixing it"
                pass
            case CheckResult.UNRECOVERABLE:
                self.toast = "we REALLY goofed, and we can't fix it!"
                raise Exception("Unrecoverable Error Occured!")

    def cleanup(self):
        """Delete the repository associated with this module"""
        self.repo.delete()
