from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Optional
from uuid import UUID


class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


@dataclass
class Run:
    id: UUID
    project_id: UUID
    title: str
    description: str
    status: RunStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]


@dataclass
class ActionResult:
    output: str
    approved: Optional[bool] = None


@dataclass
class Agent:
    name: str
    action: Callable[["ExecutionResult"], ActionResult]
    next: Optional["Agent"] = None


@dataclass
class ExecutionResult:
    action_results: dict[str, ActionResult]
