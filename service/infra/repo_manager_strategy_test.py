from pathlib import Path

import pytest

from infra.repo_manager_strategy import AbstractRepoManagerStrategy, RepoManagerStrategy


class _MatchingManager(AbstractRepoManagerStrategy):
    def __init__(self) -> None:
        self.called = False

    @staticmethod
    def can_handle(repo_url: str) -> bool:
        return True

    def clone(self, repo_url: str, branch: str, dest: Path) -> None:
        self.called = True


class _NonMatchingManager(AbstractRepoManagerStrategy):
    @staticmethod
    def can_handle(repo_url: str) -> bool:
        return False

    def clone(self, repo_url: str, branch: str, dest: Path) -> None:
        raise AssertionError("should not be called")


def test_clone_delegates_to_matching_manager(tmp_path: Path) -> None:
    manager = _MatchingManager()

    RepoManagerStrategy([manager]).clone("https://example.com/repo", "main", tmp_path)

    assert manager.called is True


def test_clone_raises_when_no_manager_matches(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="https://example.com/repo"):
        RepoManagerStrategy([_NonMatchingManager()]).clone("https://example.com/repo", "main", tmp_path)
