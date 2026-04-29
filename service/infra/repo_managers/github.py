import base64
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
        credentials = base64.b64encode(f"x-access-token:{self._token}".encode()).decode()
        try:
            subprocess.run([
                "git", "-c", f"http.extraHeader=Authorization: Basic {credentials}",
                "clone", "--branch", branch, "--single-branch", repo_url, str(dest),
            ],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode(errors="replace").strip().replace(credentials, "***")
            raise RuntimeError(f"git clone failed (exit {e.returncode}): {stderr}") from None
