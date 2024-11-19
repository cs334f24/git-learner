import wonderwords
from github import Auth, Github, GithubException, GithubIntegration
from github.Repository import Repository

from .defs import GithubStep, Module, StepData


def get_github(private_key, app_id: int | str, org_name: str) -> Github:
    """Create an object to interact with the github api as an app

    Args:
        app_id: the github app id
        org_name: the organization the github act should act as

    Returns:
        Github Object
    """
    auth = Auth.AppAuth(app_id, private_key)
    gi = GithubIntegration(auth=auth)
    installation = gi.get_org_installation(org_name)
    return installation.get_github_for_installation()


class CreateRepo(GithubStep):
    def __init__(self, github: Github, org_name: str):
        super().__init__(github, org_name)
        r = wonderwords.RandomWord()
        adjective: str = r.word(include_parts_of_speech=["adjective"])
        noun: str = r.word(include_parts_of_speech=["noun"])
        self.name = adjective + "-" + noun

    def act(self, data: StepData) -> StepData:
        result = data.copy() if data else {}
        self.repo = self.org.create_repo(self.name)
        result["repo_name"] = self.name
        result["repo_url"] = self.repo.url
        result["repo"] = self.repo
        return result

    def check(self, data: StepData):
        try:
            self.org.get_repo(self.name)
            return True, ""
        except GithubException as e:
            if e.status == 404:
                return False, "Repository not created"
            return False, f"something went wrong, {str(e)}"

    def output(self, data: StepData) -> str:
        return data.get("repo_url", "")


class AddReadme(GithubStep):
    def __init__(self, github: Github, org_name: str):
        super().__init__(github, org_name)

    def act(self, data: StepData) -> StepData:
        result = data.copy() if data else {}
        self.get_repo(data)
        self.repo.create_file(
            "README.md",
            "Initialize repository",
            """# README

Welcome to git-learner!""",
        )
        return result

    def check(self, data: StepData):
        self.get_repo(data)
        try:
            self.repo.get_readme()
            return True, ""
        except Exception as e:
            return False, f"something went wrong, {str(e)}"

    def output(self, data: StepData) -> str:
        return ""


class AddRandomFile(GithubStep):
    def __init__(self, github: Github, org_name: str):
        super().__init__(github, org_name)

    def act(self, data: StepData) -> StepData:
        result = data.copy() if data else {}
        self.get_repo(data)

        r = wonderwords.RandomWord()
        filename = r.word() + ".txt"
        content = r.random_words(20)

        self.repo.create_file(
            filename,
            "Add random words",
            "\n".join(content),
        )
        return result

    def check(self, data: StepData):
        self.get_repo(data)
        return True, ""

    def output(self, data: StepData) -> str:
        return ""


class CreateRepoFromTemplate(CreateRepo):
    def __init__(self, github: Github, org_name: str, template: Repository):
        super().__init__(github, org_name)
        self.template = template

    def act(self, data: StepData) -> StepData:
        result = data.copy() if data else {}
        self.repo = self.org.create_repo_from_template(self.name, self.template)
        result["repo_name"] = self.name
        result["repo_url"] = self.repo.url
        result["repo"] = self.repo
        return result


def example_module(private_key_path: str, org_name: str = "cs334f24") -> Module:
    github = get_github(private_key_path, 1055842, org_name)
    steps = []
    steps.append(CreateRepo(github, org_name))
    steps.append(AddReadme(github, org_name))
    return Module("example_module", steps)


def test_module(
    github: Github, org_name: str, current_step: int = 0, repo: str = ""
) -> Module:
    if current_step != 0 and not repo:
        raise ValueError("Need repository url if not starting from the beginning")

    steps = []
    steps.append(CreateRepo(github, org_name))
    steps.append(AddReadme(github, org_name))
    steps.append(AddRandomFile(github, org_name))
    init_data = {"repo_name": repo} if repo else {}

    return Module("test_module", steps, init_step=current_step, init_data=init_data)
