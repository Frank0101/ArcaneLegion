from datetime import datetime
from typing import Optional
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
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    model_config = {"from_attributes": True}
