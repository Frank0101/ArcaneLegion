from abc import ABC, abstractmethod


class AbstractRepoManager(ABC):
    @abstractmethod
    def clone(self, repo_url: str, branch: str, workspace: str) -> None: ...
