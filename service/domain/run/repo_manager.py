from abc import ABC, abstractmethod
from pathlib import Path


class AbstractRepoManager(ABC):
    @abstractmethod
    def clone(self, repo_url: str, branch: str, dest: Path) -> None: ...
