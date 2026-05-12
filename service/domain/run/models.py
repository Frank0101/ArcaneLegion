from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class AgentRole(str, Enum):
    planner = "planner"
    coder = "coder"
    reviewer = "reviewer"


@dataclass
class Run:
    id: UUID
    project_id: UUID
    title: str
    description: str
    status: RunStatus
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None


@dataclass
class ActionResult:
    prompt: str
    output: str
    approved: bool | None = None


@dataclass
class Agent:
    role: AgentRole
    action: Callable[["ExecutionResult"], ActionResult]
    next: "Agent | None" = None


@dataclass
class ExecutionResult:
    action_results: dict[AgentRole, ActionResult]
