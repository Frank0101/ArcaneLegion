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
    success: Optional[bool] = None


@dataclass
class Agent:
    name: str
    action: Callable[[], ActionResult]
    next: Optional["Agent"] = None


@dataclass
class ExecutionResult:
    action_results: dict[str, ActionResult]

    @property
    def success(self) -> bool:
        return not any(r.success is False for r in self.action_results.values())

    @property
    def error_message(self) -> Optional[str]:
        failures = [ar.output for ar in self.action_results.values() if ar.success is False]
        return failures[0] if failures else None
