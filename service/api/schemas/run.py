from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from domain.run.models import RunStatus


class RunRequest(BaseModel):
    project_id: UUID
    title: str
    description: str


class RunResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str
    status: RunStatus
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None

    model_config = {"from_attributes": True}
