from abc import abstractmethod
from pathlib import Path

from domain.run.repo_manager import AbstractRepoManager


class AbstractRepoManagerStrategy(AbstractRepoManager):
    @staticmethod
    @abstractmethod
    def can_handle(repo_url: str) -> bool: ...


class RepoManagerStrategy(AbstractRepoManager):
    def __init__(self, managers: list[AbstractRepoManagerStrategy]) -> None:
        self._managers = managers

    def clone(self, repo_url: str, branch: str, dest: Path) -> None:
        for manager in self._managers:
            if manager.can_handle(repo_url):
                manager.clone(repo_url, branch, dest)
                return
        raise ValueError(f"No manager available for {repo_url}")
