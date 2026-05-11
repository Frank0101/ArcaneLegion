import pytest

from infra.repo_manager_strategy import AbstractRepoManagerAdapter, RepoManagerStrategy


class _MatchingManager(AbstractRepoManagerAdapter):
    def __init__(self) -> None:
        self.called = False

    @staticmethod
    def can_handle(repo_url: str) -> bool:
        return True

    def clone(self, repo_url: str, branch: str, workspace: str) -> None:
        self.called = True


class _NonMatchingManager(AbstractRepoManagerAdapter):
    @staticmethod
    def can_handle(repo_url: str) -> bool:
        return False

    def clone(self, repo_url: str, branch: str, workspace: str) -> None:
        raise AssertionError("should not be called")


def test_clone_delegates_to_matching_manager() -> None:
    manager = _MatchingManager()

    RepoManagerStrategy([manager]).clone("https://example.com/repo", "main", "/workspace")

    assert manager.called is True


def test_clone_raises_when_no_manager_matches() -> None:
    with pytest.raises(ValueError, match="https://example.com/repo"):
        RepoManagerStrategy([_NonMatchingManager()]).clone("https://example.com/repo", "main", "/workspace")
