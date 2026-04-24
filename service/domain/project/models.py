from dataclasses import dataclass
from uuid import UUID


@dataclass
class Project:
    id: UUID
    name: str
    repo_path: str
    default_branch: str
