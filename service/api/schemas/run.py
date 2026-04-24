from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class RunRequest(BaseModel):
    project_id: UUID
    title: str
    description: str
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]


class RunResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    model_config = {"from_attributes": True}
