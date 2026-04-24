from uuid import UUID

from pydantic import BaseModel


class ProjectRequest(BaseModel):
    name: str
    repo_path: str
    default_branch: str


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    repo_path: str
    default_branch: str

    model_config = {"from_attributes": True}
