import wonderwords
from github import Github, GithubException
from github.Commit import Commit
from github.Repository import Repository

from module_core import CheckResult, Module, Step, create_repo


class CloneStep(Step):
    def __init__(self): ...
    def action(self, repo: Repository):
        repo.create_file(
            "README.md",
            "Add README",
            """# README

It is good practice to include a README.md file within your repository.

## Contributors

- Contributor1
                """,
        )
        repo.create_file("favorite_colors.txt", "Create favorite colors file", "red")

    def check(self, repo: Repository) -> tuple[CheckResult, str]:
        return CheckResult.GOOD, ""

    def instructions(self, repo: Repository) -> str:
        name = repo.name
        url = repo.ssh_url
        return f"""
## Cloning the Repo

The first step to working with a git repo is creating a local copy.
This is done by using `clone` on repo. The repo you clone is called `origin`.

To get started, open a terminal and navigate to where you would like to store your copy of the repo.

```bash
git clone {url}
cd {name}
```

You have now created a local copy of {name}.
When you have work (commits) you want to someone else to have, you `push` them to `origin`.

To check the url of `origin`, you can run the following command:

```bash
git remote -v
```
In the next step you will create local changes and push them to `origin`.
"""


class PushNoConflict(Step):
    def __init__(self):
        self.previous_commit: dict[str, Commit] = {}

    def action(self, repo: Repository):
        # self.previous_commit[repo.name] = repo.get_commits()[0]
        pass

    def check(self, repo: Repository):
        commits = repo.get_commits()

        commit: Commit = commits[0]

        if repo.name not in self.previous_commit:
            try:
                self.previous_commit[repo.name] = commits[1]
            except IndexError:
                self.previous_commit[repo.name] = commits[0]

        has_new_commit = self.previous_commit[repo.name].sha != commit.sha

        if not has_new_commit:
            return CheckResult.USER_ERROR, "No new commit pushed"

        return CheckResult.GOOD, str(commit)

    def instructions(self, repo: Repository) -> str:
        return """
## Adding Changes Locally

Changes to a repo are stored in `commits`.
You can check if you have any uncommited changes by running the command `git status` in your terminal.

Let's start by editting the `README.md` in your terminal.

```bash
nano README.md
```

Add your name to the list of contributors.
Make sure to save the file before exiting your editor.

Run `git status` again.
You should now see uncommited changes in `README.md`.

## Staging Changes

You can stage changed files to be commited by running `git add` along with their path.
So, to stage `README.md` you should run the following.

```bash
git add README.md
```
Now that you have staged changes, you can create a commit.

## Committing Changes Locally

Staged changes are commited using `git commit`.
Running the command below

```bash
git commit
```

You editor (likely nano) should open.
The first line of the file is used as commit message, and the rest of the file is used as the body.

After you save the file the commit is created.
Run `git status` again to see that you are one commit locally that `origin` does not.

## Pushing To `origin`

To push local commits to a remote repository you can use the command `git push`.
It is best practice to specify which remote to push to.
For this repository you can run the command below

```bash
git push origin
```
"""


class PushAfterUpdate(Step):
    def __init__(self):
        self.previous_commit: dict[str, Commit] = {}

    def action(self, repo: Repository):
        r = wonderwords.RandomWord()
        words = r.random_words(10, include_parts_of_speech=["nouns"])
        repo.create_file("random_words.txt", "Add random words", "\n".join(words))
        self.previous_commit[repo.name] = repo.get_commits()[0]

    def check(self, repo: Repository) -> tuple[CheckResult, str]:
        commits = repo.get_commits()

        commit = commits[0]

        if repo.name not in self.previous_commit:
            try:
                self.previous_commit[repo.name] = commits[1]
            except IndexError:
                self.previous_commit[repo.name] = commits[0]

        has_new_commit = self.previous_commit[repo.name].sha != commit.sha

        if not has_new_commit:
            return CheckResult.USER_ERROR, "No new commit pushed"

        return CheckResult.GOOD, "All good!"

    def instructions(self, repo: Repository) -> str:
        return """
This step goes over how to handle the remote repository having non-conflicting changes.

## Adding more changes

Start by adding your favorite color to `favorite_colors.txt`.
After you have added your color, stage then commit the file.
The `-m` flag can be used with commit to specify a commit message without opening a text editor.

```bash
git add favorite_colors.txt
git commit -m "Add a favorite color"
```

Not try to push using `git push origin`.
You should see a message in your terminal about your local repo not being up to date.
To resolve this, you will need to pull the remote changes.

### Pulling Non-Conflicting Remote Updates

Another user has pushed changes before you!
Changes are downloaded from a remote repository using `git pull`.

To download the changes from `origin` you can run

```bash
git pull origin
```

To resolve the changes you will need to create a merge commit.
Since there are no conflicting changes, git can do this automically.

Now that your repo is up to date with origin, you are ready to push.

### Pushing Changes

To push your updated repository to, use `git push origin`.
"""


class EndStep(Step):
    def instructions(self, repo: Repository) -> str:
        return "You have completed this module!"

    def action(self, repo: Repository):
        pass

    def check(self, repo: Repository) -> tuple[CheckResult, str]:
        return CheckResult.GOOD, ""


def initializer(github: Github):
    return create_repo(github, "cs334f24")


steps: list[Step] = []

steps.append(CloneStep())
steps.append(PushNoConflict())
steps.append(PushAfterUpdate())
steps.append(EndStep())

module = Module("push-after-update", initializer, steps)
