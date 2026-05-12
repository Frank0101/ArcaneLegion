import base64
import subprocess
from unittest.mock import patch

import pytest

from infra.repo_managers.github import GitHubRepoManager

_TOKEN = "mytoken"
_CREDENTIALS = base64.b64encode(f"x-access-token:{_TOKEN}".encode()).decode()
_REPO_URL = "https://github.com/org/repo"


@pytest.mark.parametrize("url,expected", [
    ("https://github.com/org/repo", True),
    ("https://gitlab.com/org/repo", False),
])
def test_can_handle(url: str, expected: bool) -> None:
    assert GitHubRepoManager(None).can_handle(url) is expected


def test_clone_raises_when_token_is_none() -> None:
    with pytest.raises(ValueError, match="GITHUB_TOKEN"):
        GitHubRepoManager(None).clone(_REPO_URL, "main", "/workspace")


def test_clone_calls_git_with_auth_header() -> None:
    with patch("subprocess.run") as mock_run:
        GitHubRepoManager(_TOKEN).clone(_REPO_URL, "main", "/workspace")

    mock_run.assert_called_once_with(
        [
            "git", "-c", f"http.extraHeader=Authorization: Basic {_CREDENTIALS}",
            "clone", "--branch", "main", "--single-branch", _REPO_URL, "/workspace",
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def test_clone_failure_raises_runtime_error() -> None:
    failure = subprocess.CalledProcessError(128, [], stderr="remote: Repository not found")
    with patch("subprocess.run", side_effect=failure):
        with pytest.raises(RuntimeError, match="git clone failed"):
            GitHubRepoManager(_TOKEN).clone(_REPO_URL, "main", "/workspace")


@pytest.mark.parametrize("secret", [_TOKEN, _CREDENTIALS])
def test_clone_failure_does_not_expose_secret(secret: str) -> None:
    failure = subprocess.CalledProcessError(
        128, [], stderr=f"fatal: auth failed with {secret}")
    with patch("subprocess.run", side_effect=failure):
        with pytest.raises(RuntimeError) as exception_info:
            GitHubRepoManager(_TOKEN).clone(_REPO_URL, "main", "/workspace")

    error = exception_info.value
    assert "fatal: auth failed with ***" in str(error)
    assert secret not in str(error)
    assert error.__cause__ is None
