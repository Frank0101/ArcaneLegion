import subprocess
from pathlib import Path

from infra.repo_manager_strategy import AbstractRepoManagerStrategy


class GitHubRepoManager(AbstractRepoManagerStrategy):
    def __init__(self, token: str | None) -> None:
        self._token = token

    @staticmethod
    def can_handle(repo_url: str) -> bool:
        return "github.com" in repo_url

    def clone(self, repo_url: str, branch: str, dest: Path) -> None:
        if self._token is None:
            raise ValueError("GITHUB_TOKEN is not configured")
        authenticated_url = repo_url.replace("https://", f"https://{self._token}@")
        subprocess.run(
            ["git", "clone", "--branch", branch, "--single-branch", authenticated_url, str(dest)],
            check=True,
            capture_output=True,
        )
