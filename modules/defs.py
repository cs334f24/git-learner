from abc import ABC, abstractmethod
from typing import Any

from github import Github, Repository

StepData = dict[str, Any]


class Step(ABC):
    @abstractmethod
    def act(self, data: StepData) -> StepData:
        """Have the Git Learner system perform a step's action"""
        pass

    @abstractmethod
    def check(self, data: StepData) -> tuple[bool, str]:
        """Have the Git Learner system check a step"""
        pass

    @abstractmethod
    def output(self, data: StepData) -> str:
        """Return a string that represents the current state of a step"""
        pass


class GithubStep(Step):
    def __init__(self, github: Github, org_name: str):
        self.github = github
        self.org = self.github.get_organization(org_name)

    def get_repo(self, data: StepData):
        """Set step's repository, making an api request if necessary"""
        if hasattr(self, "repo"):
            return
        if "repo" in data:
            self.repo: Repository.Repository = data["repo"]
        else:
            self.repo = self.org.get_repo(data["repo_name"])


class Module:
    def __init__(
        self,
        name: str,
        steps: list[Step],
        init_data: StepData | None = None,
        init_step: int = 0,
    ):
        self.name = name
        self.steps = steps
        self.step = init_step
        self.data = init_data or {}

    @property
    def progress(self):
        return self.step, len(self.steps)

    def __iter__(self):
        yield from self.steps

    def __len__(self):
        return len(self.steps)

    def __getitem__(self, index):
        if not isinstance(index, int):
            raise ValueError(f"Expected integer index, recieved {type(index)}")

        if not 0 <= index < len(self.steps):
            raise IndexError(
                f"No step with index {index} from module with {len(self.steps)} steps"
            )

        return self.steps[index]

    def act(self):
        data = self[self.step].act(self.data)
        self.data.update(data)

    def can_continue(self) -> bool:
        self.step_done, _ = self[self.step].check(self.data)
        return self.step_done

    def next(self) -> bool:
        if self.step_done and self.step + 1 < len(self):
            self.step += 1
            self.step_done = False
            return True
        return False
