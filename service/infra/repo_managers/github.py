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

        # Pass the token as an HTTP header instead of embedding it in the URL,
        # and wrap in try/except to prevent CalledProcessError.cmd from leaking
        # the token into logs or tracebacks.
        try:
            subprocess.run([
                "git", "-c", f"http.extraheader=Authorization: Bearer {self._token}",
                "clone", "--branch", branch, "--single-branch", repo_url, str(dest),
            ],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"git clone failed (exit {e.returncode})") from None
