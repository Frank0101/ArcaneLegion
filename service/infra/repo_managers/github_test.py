from pathlib import Path
from unittest.mock import patch

import pytest

from infra.repo_managers.github import GitHubRepoManager


@pytest.mark.parametrize("url,expected", [
    ("https://github.com/org/repo", True),
    ("https://gitlab.com/org/repo", False),
])
def test_can_handle(url: str, expected: bool) -> None:
    assert GitHubRepoManager(None).can_handle(url) is expected


def test_clone_raises_when_token_is_none(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="GITHUB_TOKEN"):
        GitHubRepoManager(None).clone("https://github.com/org/repo", "main", tmp_path)


def test_clone_calls_git_clone_with_authenticated_url(tmp_path: Path) -> None:
    with patch("subprocess.run") as mock_run:
        GitHubRepoManager("mytoken").clone("https://github.com/org/repo", "main", tmp_path)

    mock_run.assert_called_once_with(
        ["git", "clone", "--branch", "main", "--single-branch",
         "https://mytoken@github.com/org/repo", str(tmp_path)],
        check=True,
        capture_output=True,
    )
